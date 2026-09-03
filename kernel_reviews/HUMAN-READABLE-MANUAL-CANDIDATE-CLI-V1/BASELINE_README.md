# HUMAN-READABLE-MANUAL-CANDIDATE-CLI-V1

This additive logical baseline records `PROJECT_ANALYSIS_INFRASTRUCTURE` and
`PROJECT_OPERATIONAL_POLICY`. It adds no Elliott methodology behavior or
source authority.

The `elliott-manual-candidate` console entrypoint and
`python -m elliott_runtime.manual_candidate_cli` accept one bounded UTF-8 JSON
file. The file is limited to 1 MiB, duplicate keys and non-finite JSON tokens
are rejected, all objects use closed field sets, and every enum token must
match an existing public token exactly.

The human-readable adapter constructs only existing untrusted
`AnalyzedWaveSubject`, ordered-child, manual-fact, and
`BoundedManualChartAnalysisRequest` objects. It supports the six existing
manual fact forms and preserves their explicit order. It does not accept or
deserialize certificates, observations, operational resolutions, existing
bindings, validators, constructors, results, summaries, or other authority.

Execution delegates exactly to
`MethodologyKernel.analyze_bounded_manual_chart`. Runtime imports only the
approved Methodology Kernel package root. The CLI contains no methodology
dispatch, validator invocation, certificate issuance, network/process/browser
capability, output-file writer, market interpretation, discovery, inference,
ranking, alert, or trading behavior.

Successful output is a non-authoritative JSON diagnostic snapshot written to
standard output. It copies exact scalar status tokens and reasons from the
validated bounded result, reports all ten coverage records, explicitly records
`reviewed_is_valid: false`, and cannot be loaded back through the input schema.
Errors are fail-closed machine-readable JSON on standard error with exit code
2. No durable or serialized methodology authority is created.

The examples demonstrate one reviewed P004 declaration and one explicitly
selected cardinality violation that remains unresolved without a genuine
certificate. They are demonstrations, not analysis recommendations or source
authority.

All existing methodology, certificate, bounded-analysis, and legacy API
semantics remain unchanged.
