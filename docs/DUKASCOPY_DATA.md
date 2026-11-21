# Dukascopy data — catalog and downloader

Our repo does **not** contain tick data. `data/` is ignored and never pushed. The
2026 ticks live only on this PC. To get other years or instruments, use the
Dukascopy downloader.

## Downloader

- Fork: `https://github.com/YoussefMaximous/dukascopy-node`
- Upstream: `https://github.com/Leo4815162342/dukascopy-node` (MIT)
- Instrument browser: `https://www.dukascopy-node.app/instruments`
- 1,499 instruments across forex, stocks, crypto, commodities, indices, bonds,
  CFDs and ETFs; 10 timeframes; earliest daily candles from 1973 for EUR/USD.
  Tick availability varies by instrument and year.

## Fastest path into X

Use our sync command; it drives the same downloader and writes the validated
Parquet store:

```text
python -m losslens ticks sync --symbol XAUUSD --from 2024-01-01 --to 2024-12-31
```

Our store already covers 2026-01-01 to 2026-11-20. Any other year can be added
the same way. `ticks status` shows what is stored; `ticks verify` checks it.

## Raw CSV path

```text
npx dukascopy-node -i xauusd -from 2024-01-01 -to 2024-12-31 -t tick -f csv
python -m losslens ticks import --symbol XAUUSD --file <csv> \
    --ts-col <time> --bid-col <bid> --ask-col <ask> --ts-format epoch_ms
```

Check the downloader’s output columns with `--help`; the importer needs
`ts_ms`, `bid`, `ask` and optional volumes.

## Why there is no fork full of data

A full Dukascopy history is terabytes and changes daily. GitHub cannot host it,
and our standing rule is that tick data never goes into git. The fork is the
downloader and its instrument catalog; the data is fetched on demand and stays
local.
