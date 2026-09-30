# Risk and uncertainty

Version 1.0 · Inherits [COMMON.md](COMMON.md).

## Inputs

Factual context/checklist for first pass; accumulated findings only for second pass. Require current revision and source references; unresolved upstream blockers remain visible.

## AI task

First-pass analysis then reconciliation. Use the authorized tools defined in the architecture document; all proposed changes remain reviewable.

## Typed output fields

first_pass_artifact, reconciled_findings[], duplicates[], proposed_dispositions[], allowance_input_refs[]

Include these fields inside the common result envelope. The build must express the final schema in runtime validators with explicit units, identifiers, optional fields and status enums. Do not use a prose document as a substitute for typed output.

## Deterministic checks and calculations

Server validates schema, current revision, evidence ownership and applicable prerequisite checks. Any quantities, costs, prices, margin, variance or schedule calculations use reviewed Python functions and persist the calculation ID. No independent AI totals.

## Human gate

Human assigns disposition/owner and resolves blockers. Exact reviewed inputs/output fingerprints are captured; changed inputs invalidate affected approval. Model/client success never satisfies this gate.

## Exceptions and completion

Never claim testing/certification; insurance not an assumed payout; retain contradictory evidence. Completion means a valid proposal and all new relevant risk findings are saved. Stage advancement requires the human decision separately.
