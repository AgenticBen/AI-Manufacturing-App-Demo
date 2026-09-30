# Request intake

Version 1.0 · Inherits [COMMON.md](COMMON.md).

## Inputs

Saved ready sources and request identity. Require current revision and source references; unresolved upstream blockers remain visible.

## AI task

Source extraction and customer matching proposals. Use the authorized tools defined in the architecture document; all proposed changes remain reviewable.

## Typed output fields

candidate_fields[{field,value,unit,status,source_refs}], customer_match, attachment_status, missing_inputs

Include these fields inside the common result envelope. The build must express the final schema in runtime validators with explicit units, identifiers, optional fields and status enums. Do not use a prose document as a substitute for typed output.

## Deterministic checks and calculations

Server validates schema, current revision, evidence ownership and applicable prerequisite checks. Any quantities, costs, prices, margin, variance or schedule calculations use reviewed Python functions and persist the calculation ID. No independent AI totals.

## Human gate

Employee verifies source identity and extracted facts. Exact reviewed inputs/output fingerprints are captured; changed inputs invalidate affected approval. Model/client success never satisfies this gate.

## Exceptions and completion

No source ready → no extraction; preserve confirmed fields; unknown/unreadable stays explicit. Completion means a valid proposal and all new relevant risk findings are saved. Stage advancement requires the human decision separately.
