# cbBTC Race Bot — make.fun "Race a BTC trading bot live for 24 hours"

Bounty: https://make.fun/bounty/btc-race-24h-20261117-0603
Slug: `btc-race-24h-20261117-0603` · Pool $250 USDC (1st $60, 10 places) ·
**Deadline: 2026-11-17 12:03 UTC = 19:03 WIB** · Race window starts 12:18 UTC.

Status: **MVP SELESAI & LULUS DEV GATE pada pengujian lokal. BELUM DISUBMIT**
(login/daftar/submit dilarang pada tahap persiapan ini).

## Format entri (TERVERIFIKASI dari halaman bounty + kit resmi + API)

- Repo GitHub **publik**, dimiliki akun GitHub pendaftar, **dibuat setelah
  kompetisi dibuka** (dibuka 2026-11-17 06:03 UTC), lisensi OSI-approved
  (repo ini: MIT, lihat `LICENSE`).
- Bot di root repo: `main.py` (Python 3.13) — file ini. Runtime grader:
  `python3 -P -s /bot/main.py` dengan `PYTHONHASHSEED=0`.
- Protokol `agent-fun/bars-replay/v1`: JSONL di stdin/stdout — `hello` sekali,
  lalu satu `batch` per menit (bar 1 menit cbBTC dari Orca Whirlpool, harga
  integer skala 1e5), bot menjawab tepat satu `reply` per batch berisi orders.
  Order terisi di **open bar berikutnya**, fee **4 bps**, slippage **2 bps**,
  plus price impact constant-product `1 + a/D` terhadap depth bar pengisi.
- Modal kertas $1.000 USDC (1.000.000.000 quote units, skala 6). Long-only,
  maks 1 posisi, maks 16 order/reply, buy minimum 1 USDC.
- Shim protokol resmi kit disalin byte-for-byte ke `vendor/makefun_bars.py`
  (sha256 `80452b00d2eb1e9c959e73d41cda6ca726cdbe7bfa4065d48278c22eccd276ff`,
  sama dengan `sdk/makefun_bars.py` di kit). Stdlib only; tanpa network,
  wall-clock, file di luar repo, atau randomness — deterministik.
- **Dev gate:** entri hanya ikut race jika grade terakhir di dev window
  (24 jam beku yang dipublikasikan di kit, 1.440 bar) menghasilkan
  **net PnL > $0** setelah semua fee.
- **Guardrail race:** minimal 1 trade terisi dan max drawdown ≤ 25%.
- Maks **10 submission** per peserta; submission terakhir sebelum deadline
  adalah entri final. Hasil/ranking hanya dari race window 24 jam.
- Submit wajib menyertakan **transkrip sesi AI coding-agent** yang membangun
  bot (bundle dari kit CLI). Peringatan: `handed_over_places: none` — entri
  dengan transkrip "handed_over" tetap diranking tetapi **tidak dapat tempat
  berbayar**; gunakan sesi yang terekam harness sungguhan.
- Entry fee: halaman bounty tidak mencantumkan fee, dan API resmi
  `GET /api/competitions/btc-race-24h-20261117-0603/requirements`
  mengembalikan **`entry_fee: null`** → tidak ada fee yang dikenakan API
  untuk bounty ini (tetap konfirmasi ulang di layar submit).

## Strategi (main.py)

Mean-reversion selektif long-only terhadap SMA 240 bar, aritmetika integer
penuh (tanpa float):

- **Entry:** close ≤ SMA240 − 60 bps, bar memantul (close ≥ close sebelumnya),
  dan bukan crash (close > SMA240 − 250 bps). Ukuran penuh: seluruh cash,
  dibatasi `weight_room` dari caps.
- **Exit:** close ≥ SMA240 + 30 bps, atau stop-loss −90 bps dari entry,
  atau crash-guard −250 bps dari SMA, atau time-stop 720 bar (12 jam).
- `max_slippage_bps = 100` pada semua order.

Alasan pemilihan: dev window adalah hari choppy/range-bound (BTC +0,49%
net, range −0,9%…+1,6%). Sweep 28 varian trend/momentum (EMA cross,
Donchian, momentum threshold, RSI-dip-trend, breakout+EMA) **semuanya rugi**
setelah biaya round-trip ~26 bps; plateau mean-reversion (entry 50–70 bps,
exit 25–35 bps) positif di seluruh plateau-nya. Parameter yang dipilih
adalah titik tengah plateau, bukan puncak tunggal.

## Hasil tes lokal (backtest.py — harness replay lokal di folder ini)

Harness lokal memberi makan bot asli (subprocess, protokol wire sungguhan)
dengan dev window resmi dari kit dan mengisi order sesuai model RULES.txt
(fee 4 bps, slippage 2 bps, impact 1 + a/D, flatten di close terakhir):

| Window | Net PnL | Trades | Fees | Max DD | Deterministik |
|---|---|---|---|---|---|
| Dev window penuh (1.440 bar) | **+$6,29** | 4 | $1,61 | 0,88% | Ya (2 run byte-identik) |
| Paruh pertama (720 bar) | +$5,29 | 2 | — | 0,66% | Ya |
| Paruh kedua / geser 240 bar | +$1,00 | 2 | — | 0,72% | Ya |

- Dev gate lokal: **LULUS** (+$6,29 > $0). Guardrail: 4 trade ≥ 1, DD 0,88% ≤ 25%.
- Test unit shim resmi kit (`sdk/test_makefun_bars.py`): 16 tests OK.
- `grade-local` resmi kit **tidak dapat dijalankan di mesin ini**: driver
  `process` hanya mendukung bot Node 22 ("python3.13 runs only inside
  Docker") dan Docker tidak tersedia. Angka di atas berasal dari harness
  lokal yang meniru formula RULES.txt — bukan grade resmi server.

## Cara submit nanti (agent utama, setelah akun user tersedia)

1. Buat repo GitHub publik baru (setelah 06:03 UTC 17 Nov 2026) di akun user,
   isi: `main.py`, `vendor/makefun_bars.py`, `LICENSE`, README ini. Commit.
2. Unduh kit: `curl -sSL "https://make.fun/c/btc-race-24h-20261117-0603/kit" | tar xz`
3. Login/register dengan akun user (keypair Solana / GitHub sesuai akun user).
4. Buat bundle transkrip sesi pembangunan dari kit CLI (`node cli/makefun.mjs bundle`),
   lalu cek (`node cli/makefun.mjs check`).
5. Submit sebelum **12:03 UTC**:
   `node cli/makefun.mjs submit --competition btc-race-24h-20261117-0603 --repo-url <url> --commit <sha40> --title <name> --bundle <file> --keypair <file>`
6. Verifikasi dev grade entri final > $0 di leaderboard sebelum deadline;
   bila ditolak check, perbaiki dan submit ulang (maks 10x, terakhir yang dihitung).

## Asumsi / belum terverifikasi

- PnL lokal adalah aproksimasi setia (integer/Fraction mengikuti RULES.txt),
  bukan grade server; margin +$6,29 di atas gate $0 tergolong tipis —
  perbedaan kecil pada model flatten/impact server bisa menggeser angka,
  walau seluruh sub-window juga positif.
- Bot hanya memperdagangkan CBBTC (satu-satunya simbol di universe bounty ini).
- Zona waktu deadline memakai UTC dari API (12:03 UTC = 19:03 WIB).
- Tidak ada login, pendaftaran, pembayaran, atau submission yang dilakukan
  selama persiapan ini.
