# Manufacturing approach

Version 1.0 · Inherits [COMMON.md](COMMON.md).

## Inputs

Approved engineering, shop capabilities and historical routes. Require current revision and source references; unresolved upstream blockers remain visible.

## AI task

Proposed estimating routing and time assumptions. Use the authorized tools defined in the architecture document; all proposed changes remain reviewable.

## Typed output fields

operations[{sequence,dependencies,work_center,setup_basis,run_basis,rate_refs,evidence_refs}], outside_services[], capability_gaps[]

Include these fields inside the common result envelope. The build must express the final schema in runtime validators with explicit units, identifiers, optional fields and status enums. Do not use a prose document as a substitute for typed output.

## Deterministic checks and calculations

Server validates schema, current revision, evidence ownership and applicable prerequisite checks. Any quantities, costs, prices, margin, variance or schedule calculations use reviewed Python functions and persist the calculation ID. No independent AI totals.

## Human gate

Estimator/engineer approves feasibility and time basis. Exact reviewed inputs/output fingerprints are captured; changed inputs invalidate affected approval. Model/client success never satisfies this gate.

## Exceptions and completion

Unknown duration remains flagged; route stays internal; no production release. Completion means a valid proposal and all new relevant risk findings are saved. Stage advancement requires the human decision separately.
