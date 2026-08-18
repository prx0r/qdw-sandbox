# Proposed QDW semantic-core patch

This patch is intentionally separate from the current QDW repository so it can be reviewed rather than silently mutating a proven schema.

Current QDW already has `WorldStore -> PainFinder/StackOracle -> Opportunity -> Idea -> Product`. The missing bridge for LifeGit and human reality sensing is a typed temporal/private semantic layer.

Apply conceptually after `0002_global.sql`:

- `spaces`: privacy/trust boundary.
- `ontology_terms`: controlled predicates/types instead of arbitrary relationship strings.
- `object_edges`: universal typed edges across QDW object families.
- `semantic_objects`: questions/ideas/discoveries/decisions/etc; distinct from QDW ProductHypotheses.
- `events` and `states`: temporal reality.
- `tensions`: canonical problem/state discrepancy; replaces `problem_key` as durable identity.
- `threads`: longitudinal arcs across events/objects.
- `evidence_links`: universal provenance.
- `requirements/fulfillments/human_submissions`: HumanOracle/ResolutionBroker foundation.
- `data_grants`: consent and scoped rights for LifeGit-derived sensing.
- `report_definitions/report_runs/share_packages`: Wrapped/CareerGit as projections, not new truth stores.

Do **not** delete current `pain_clusters` or `ideas` immediately. Migrate them as projections/compatibility views while the new layer is proven by E2E fixtures.
