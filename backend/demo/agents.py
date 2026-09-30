"""Agent registry: stable IDs connect playbooks, source permissions and workflow outputs."""
AGENTS=[
('intake','Intake agent',0,['D11'],['request-packet'],'Gather transcript, emails and survey. Separate handled product from construction material. Preserve unknowns.'),
('crm-check','CRM check agent',0,['D10'],['request-packet'],'Match the fictional client by exact scenario identity. Tag returning/new and link past jobs; never infer a real account.'),
('company-research','Company research agent',1,['D10','D11','D12'],['client-document'],'For new clients only, draft background from supplied public-page evidence. With no verified page, mark background fictional/unverified. Do not invent public citations.'),
('material-check','Material check agent',1,['D9','D11'],['material-review'],'Match the material and preserve uncertainty. Treat report ranges as reference summaries, not design values. Ammonium nitrate requires specialist engineering; do not propose a standard hopper.'),
('material-research','Material research agent',1,['D9','D11'],['material-review'],'Only when material is missing, draft a pending-review library entry with sources and unknowns. Human approval is required before publication.'),
('conversation-synthesizer','Conversation synthesizer agent',1,['D11','D12','D9'],['client-document','clarification-email'],'Fill the requirements template from source lines, list only unresolved gaps, bundle clarification questions and material decisions. Preserve version history when answers arrive.'),
('anchor-job','Anchor job agent',2,['D6','D4'],['anchor-comparison'],'Use Python similarity scoring for historical jobs. Explain differences in quantity, material, tolerance and quoted/actual hours. Reject all if unsuitable.'),
('design','Design agent',2,['D7','D12','D9'],['concept-design'],'Propose a labeled AI concept from template, requirements, material review and anchor. A concept is not a released engineering drawing.'),
('bom','BOM agent',2,['D5','D12'],['bom'],'Produce complete part/spec/material/per-assembly quantity/total quantity/drawing references. Python extends quantities. Do not assign stock, buy or custom sourcing here.'),
('manufacturing','Manufacturing agent',3,['D8','D5'],['manufacturing-plan'],'Propose build order legs, cone, body, gate, finish, inspect and machines. Retain feature-based route choices and engineer edits.'),
('labor','Labor agent',3,['D3','D4'],['manufacturing-plan'],'Call Python estimator for setup, run, rates and totals. Compare each task estimate with historical actuals and disclose modeled uncertainty.'),
('supervisor','Supervisor agent',4,['D1','D2','D3','D5'],['working-cost','completed-cost'],'Dispatch each BOM line by stock, full assembly, individual part or custom quote; scope each sub-agent to necessary sources. Merge outputs and route QA failures back to the responsible agent.'),
('inventory','Inventory agent',4,['D1'],['working-cost'],'Read available stock, stock number, quantity and acquisition lot cost. Propose holds only; the salesperson explicitly reserves inventory.'),
('full-component','Full-component agent',4,['D2'],['working-cost'],'Look up gate assemblies and components. Return product URL, pack units, price basis and lead time. Demo lookup is prepared; invented prices must say demo price · not taken from this page.'),
('individual-parts','Individual-parts agent',4,['D1','D2'],['working-cost'],'Use Python net buy quantities after current holds; check fasteners, plate and seals, pack sizes and item background. Record exact evidence, never invent a captured price.'),
('custom-quote','Custom-quote agent',4,['D2','D12'],['working-cost'],'Draft supplier RFQ for drawing-controlled custom adapter. Mark awaiting supplier quote. Prepared estimate is not a firm offer. No email may be sent by this agent.'),
('cost-qa','Cost QA agent',4,['D1','D2','D3'],['completed-cost'],'Check every cost line for supporting evidence, link target, currency, units, pack size, current quantity and price date. Return failed line IDs to supervisor; one prepared QA loop is shown honestly.'),
('master-risk','Master risk agent',5,['D9','D12','D2','D4'],['master-risk'],'First review facts without prior conclusions, then reconcile. Cover handling, indoor/outdoor heat/moisture, transport damage, supply and lead time. Insurance amounts remain placeholders; never invent premiums.'),
('quote-drafting','Quote drafting agent',7,['D6','D12'],['customer-quote'],'Draft from approved requirements, completed cost and pricing decision, using won quote style. Customer package excludes internal costs, margin and risk notes.'),
('release-qa','Release QA agent',7,['D6','D12'],['release-qa'],'Check attachments, current revision, exact approved price and absence of internal data. Ops final check and salesperson send remain explicit separate actions.'),
('post-acceptance','Post-acceptance recheck agent',8,['D1','D2'],['post-acceptance','purchase-list','pm-handoff'],'Rerun purchasing lookups only for items not covered by stock. Python compares new cost with fixed accepted price; create buy-only list and handoff for human review.'),
('completion-extraction','Completion extraction agent',9,['D4'],[],'Future described step only: after fulfillment propose quoted/actual task hours, variance and lessons for D4. Human validates before saving; never claim this ran in the demo.')]

def agent_records():
 from pathlib import Path
 records=[]
 common=Path('backend/playbooks/COMMON.md').read_text()
 for id,name,stage,dbs,outputs,task in AGENTS:
  records.append(dict(id=id,name=name,stage=stage,databases=dbs,outputs=outputs,version='2.0',tools=['get_quote_context','read_source','lookup_catalog_and_history','calculate_quote','calculate_schedule','submit_stage_proposal'],output_fields=['proposed_output','evidence_refs','assumptions','missing_inputs','risk_findings','calculation_run_ids','errors'],human_check='Assigned reviewer checks exact inputs, output and evidence; approval is separate.',text=Path('backend/playbooks/agent-'+id+'.md').read_text(),common=common))
 return records
