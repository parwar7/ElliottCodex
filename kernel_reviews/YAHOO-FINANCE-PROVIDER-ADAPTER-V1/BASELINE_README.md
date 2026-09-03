# YAHOO-FINANCE-PROVIDER-ADAPTER-V1

This additive logical baseline records a stdlib HTTPS adapter for Yahoo Finance
chart data. It is `PROJECT_DATA_INFRASTRUCTURE`; Yahoo responses are
`UNTRUSTED_EXTERNAL_MARKET_DATA`, and normalized results use the existing
`NormalizedMarketObservations`, `SymbolIdentity`, `Timeframe`,
`DataProvenance`, and `DataQualityReport` contracts.

`YahooHistoricalDataRequest` requires an exact safe Yahoo symbol, existing
`MarketType`, supported `YahooInterval`, and explicit zero-offset UTC start/end
datetimes. Symbols are not uppercased, aliased, or heuristically rewritten. The
result maps the exact caller symbol into `SymbolIdentity.provider_symbol` and
retains the deterministic request URL in provenance.

V1 supports native requests for `1mo`, `1wk`, `1d`, `1h`, and `15m`. `4h` is
rejected as unsupported by this V1 contract and is never synthesized. The
monthly `Timeframe.resolution_seconds` value is the existing nominal 30-day
transport representation; it is not calendar or Elliott-degree authority.
Intraday results always carry `YAHOO_INTRADAY_RETENTION_LIMIT`.

The adapter uses Yahoo `quote` open/high/low/close consistently and does not mix
the separate adjusted-close series with raw quote OHLC. Corporate actions are
requested only as provider response context and are not interpreted.

The response body is capped at 64 MiB and fetched once with a 30-second default
timeout and explicit User-Agent. JSON structure, result cardinality, timestamps,
quote-array lengths, finite numeric values, and exchange timezone metadata fail
closed when malformed. Required-OHLC null rows alone are excluded, with their
zero-based raw row indices and warning retained. Values are never interpolated.
Null volume remains null and is quality metadata only.

The existing normalizer retains duplicate rows while reporting duplicate
timestamps and sorts rows chronologically. Provider metadata records raw and
normalized counts, dropped rows, missing volume, out-of-order pairs, UTC
coverage, response hash, exchange metadata, and raw-price policy. No persistent
cache or automatic retry is included.

The provider performs no pivot/swing discovery, Elliott interpretation,
candidate generation, degree inference, resampling, indicators, scenario
ranking, forecasting, or trading logic. `TIMEFRAME_IS_NOT_DEGREE` remains the
core invariant.
