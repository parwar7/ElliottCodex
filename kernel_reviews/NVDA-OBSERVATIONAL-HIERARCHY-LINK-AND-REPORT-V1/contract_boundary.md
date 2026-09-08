# Observational link contract — implemented, not Kernel ancestry

Classification: PROJECT_ANALYSIS_INFRASTRUCTURE. No new Elliott source proposition or methodology behavior. This implements only the observation-link portion of the prior aggregate-extremum proposal. Its prohibition on insertion into Kernel ancestry remains binding.

`link_observations(parent, role_index, child, start, end, *, max_pairings, cache=None)` consumes exact single-result public-factory Normal Impulse evaluations and two original `ExtremumOccurrenceEvidence` objects. Both occurrences must retain that exact parent and proposed role, the same aggregate and finer snapshots, and their respective start/end sides. The child must retain its own issued subject and five-slot binding on that exact finer observation object. Content-equal snapshots and matching IDs do not substitute for identity.

The factory returns an immutable `ObservationalHierarchyLink`. It stores original references, pairing budget, every pairing, relationship, limitations, P004-rejected flag and a non-rejected observational-link flag. A weak issuance registry pins nested references and represented link content; existing public result/occurrence validators validate their deep issuance guards on every validation. Failed validation does not refresh any evidence. Pickle/copy cannot restore live identity. This is in-process fail-closed mutation detection, not protection against arbitrary hostile Python rewriting private module state.

Pairing uses all Cartesian pairs of exact high/high or low/low occurrences in the approved civil/session envelopes. Each match denotes a half-open bar interval, not an instant. Impossible reverse order is explicitly rejected as a pairing; overlapping intervals remain unresolved. No intrabar order is chosen.

- BOUNDARY_SUPPORTED_PROPOSED_REFINEMENT: original child first/last observation bars and fields correspond to both paired parent-boundary occurrences. Still no complete subdivision, orthodox endpoint, completion or family proof.
- INTERIOR_OBSERVATION: both boundary occurrences exist and child envelopes are conservatively contained between them; either endpoint may itself correspond to that exact occurrence. Does not cover both boundaries and supplies no classification of the unexamined portions.
- AMBIGUOUS_ALTERNATIVE_PAIRINGS: paired classifications differ. Retain every pair; do not choose the convenient occurrence.
- MISSING_BOUNDARY_EVIDENCE: either boundary has no exact observed match. Individual occurrence records distinguish unavailable history from supplied rows with no match. Temporal overlap alone is insufficient. July's 190.01/190.02 is not normalized.
- OUTSIDE_SUPPORTED_REGION or UNRESOLVED_BOUNDARY_OVERLAP_OR_CROSSING: not a supported contained link. This is no Elliott invalidity.
- INCOMPATIBLE_METADATA / UNAVAILABLE_INTERVAL_EVIDENCE retain unavailable compatibility or envelope evidence without substituting a convention.

Unknown adjustment semantics, nonsynchronous captures, revisions, forming bars and incomplete/holiday/early-close coverage remain explicit in occurrence limitations. A match unique in supplied rows is not globally unique. Supported means conditional support in this immutable supplied snapshot only, not permanent endpoint/completion authority.

P004 rejected parent or child excludes that link from non-rejected proposed paths independently of P005. A rejected independent child does not reject the parent or validate siblings. The child's own original P004/P005 results remain attached only to it.

`validate_observational_graph(tuple_of_links, *, max_links)` checks every link and rejects cycles on exact live evaluation identities. It preserves repeated contextual links and uses iterative topological validation. It never rewrites `OrderedChildBinding`, recursive composition, family requirements or certifications. All serialized exports are informational; replay reconstructs live objects through public factories.

Explicit experiment limits were written in search_plan.json before evaluation: 27 existing hypotheses, at most 160 links, 256 pairings/link and 4096 total. All pair counts are preflighted, no silent truncation. Only M1/M2 role 5 and JULY:1D:S0 roles 1–5 are link parents; all previously selected strictly finer independent hypotheses are attempted without outcome selection. No additional candidate search, data refresh, history expansion or Kernel recursion.

Original implementation files and historical baselines remain unchanged. No protected policy amendment is needed or applied. Inventories remain 11/7/0/0; P006, Flat/Triangle, terminal/base-case and legacy-analyze limitations remain unchanged.
