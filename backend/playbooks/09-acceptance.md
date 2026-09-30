# Post-acceptance cost and procurement

Version 1.0 · Inherits [COMMON.md](COMMON.md).

## Inputs

Accepted immutable revision, offers, allocation state. Require current revision and source references; unresolved upstream blockers remain visible.

## AI task

Refresh evidence, call variance calculator and draft requisition. Use the authorized tools defined in the architecture document; all proposed changes remain reviewable.

## Typed output fields

refresh_evidence_refs[], calculation_run_id, uncovered_purchase_lines[], allocation_summary, exceptions[]

Include these fields inside the common result envelope. The build must express the final schema in runtime validators with explicit units, identifiers, optional fields and status enums. Do not use a prose document as a substitute for typed output.

## Deterministic checks and calculations

Server validates schema, current revision, evidence ownership and applicable prerequisite checks. Any quantities, costs, prices, margin, variance or schedule calculations use reviewed Python functions and persist the calculation ID. No independent AI totals.

## Human gate

Buyer/manager confirms allocation/spend; engineer approves alternatives. Exact reviewed inputs/output fingerprints are captured; changed inputs invalidate affected approval. Model/client success never satisfies this gate.

## Exceptions and completion

No PO/payment; no accepted-price mutation; expired holds need atomic recheck. Completion means a valid proposal and all new relevant risk findings are saved. Stage advancement requires the human decision separately.
