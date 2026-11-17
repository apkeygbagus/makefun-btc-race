# Hunter-Zero cbBTC mean-reversion bot for make.fun "Race a BTC trading bot
# live for 24 hours" (agent-fun/bars-replay/v1, Python, stdlib only).
#
# Strategy (designed and swept on the kit's published 24h dev window):
# selective long-only mean reversion against a 240-bar simple moving average.
#
#   - The dev window is a choppy, range-bound day: every trend/momentum
#     variant swept (EMA crosses, Donchian breakouts, momentum thresholds)
#     lost money on it after the ~26 bps full-size round-trip cost, while a
#     deep-dip mean-reversion plateau (entries 50-70 bps below the mean,
#     exits 25-35 bps above it) was positive across the whole plateau.
#   - Entry:  close <= SMA240 - 60 bps, the bar is bouncing (close >= the
#     previous close, so we do not catch a still-falling knife), and the dip
#     is not a crash (close > SMA240 - 250 bps). Full size: all cash, capped
#     by the hello caps' weight room.
#   - Exit:   close >= SMA240 + 30 bps (reversion complete), or a stop-loss
#     90 bps under the entry close, or the crash guard (close <= SMA240 -
#     250 bps), or a 720-bar (12 h) time stop.
#   - All decisions are integer arithmetic on the bar closes: no floats, no
#     clock, no randomness, no files, no network -- two runs on the same
#     data produce byte-identical orders.
#
# The wire protocol is the kit's own shim, vendored byte-for-byte at
# vendor/makefun_bars.py; this file only decides the orders.

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
SMA_BARS = 240          # 4 hours of 1-minute bars
ENTRY_BPS = 60          # buy a dip at least this far below the SMA
EXIT_BPS = 30           # sell once this far above the SMA
STOP_BPS = 90           # sell this far under the entry close
CRASH_BPS = 250         # never enter, and bail out, this far below the SMA
TIME_STOP_BARS = 720    # sell after 12 hours in a trade that went nowhere
MAX_SLIPPAGE_BPS = 100  # fills must land within 1% of the latest close

# Per-symbol strategy state.
_closes = []            # every close seen, oldest first (ints, price scale)
_window_sum = 0         # sum of the last SMA_BARS closes
_entry_close = None     # close of the bar that decided the current entry
_entry_seq = None       # seq of that bar


def _sma():
    """The SMA of the last SMA_BARS closes, or None until enough history."""
    if len(_closes) < SMA_BARS:
        return None
    return _window_sum // SMA_BARS


def on_batch(state, batch):
    global _entry_close, _entry_seq, _window_sum

    # Record this batch's bar for our symbol, if it carries one.
    bar = None
    for b in batch["bars"]:
        if b["symbol"] == SYMBOL:
            bar = b
    if bar is not None:
        close = int(bar["c"])
        _closes.append(close)
        _window_sum += close
        if len(_closes) > SMA_BARS:
            _window_sum -= _closes[-SMA_BARS - 1]

    if state.warming_up or bar is None:
        return []

    sma = _sma()
    if sma is None:
        return []
    close = _closes[-1]
    prev_close = _closes[-2]
    # Deviation from the SMA in bps, signed, integer-truncated toward zero
    # via floor on the scaled ratio (exact comparisons below use products).
    holding = SYMBOL in state.positions and state.positions[SYMBOL].qty > 0

    if holding:
        if _entry_close is None:
            # Position we do not remember entering (cannot happen in one
            # run); anchor the stop at the position's average cost price is
            # not available, so anchor at the current close.
            _entry_close = close
            _entry_seq = state.seq
        dev_exit = close * 10000 >= sma * (10000 + EXIT_BPS)
        crash = close * 10000 <= sma * (10000 - CRASH_BPS)
        stopped = close * 10000 <= _entry_close * (10000 - STOP_BPS)
        timed_out = _entry_seq is not None and state.seq - _entry_seq >= TIME_STOP_BARS
        if dev_exit or crash or stopped or timed_out:
            qty = state.positions[SYMBOL].qty
            _entry_close = None
            _entry_seq = None
            return [{"side": "sell", "symbol": SYMBOL, "qty": qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []

    # Flat: look for a deep, stabilising dip that is not a crash.
    dip = close * 10000 <= sma * (10000 - ENTRY_BPS)
    not_crash = close * 10000 > sma * (10000 - CRASH_BPS)
    bouncing = close >= prev_close
    if dip and not_crash and bouncing:
        spend = state.cash
        room = state.weight_room(SYMBOL)
        if room is not None and room < spend:
            spend = room
        min_notional = int(state.hello["fees"]["min_notional_quote_units"])
        if spend >= min_notional and spend > 0:
            _entry_close = close
            _entry_seq = state.seq
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": spend,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


if __name__ == "__main__":
    makefun_bars.run(on_batch)
