import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StreamableHTTPClientTransport} from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import {writeFile,mkdir} from 'node:fs/promises';
const base=process.env.TEST_BASE_URL||'http://127.0.0.1:8000';
let cookie='';const trace=[];
async function api(path,body){const r=await fetch(base+'/api'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json','X-Arc-Client':'web',...(cookie?{Cookie:cookie}:{})},body:body===undefined?undefined:JSON.stringify(body)});if(r.headers.get('set-cookie'))cookie=r.headers.get('set-cookie').split(';')[0];const d=await r.json();if(!r.ok)throw Error(JSON.stringify(d));return d;}
await api('/session',{});const catalog=await api('/catalog');const s=catalog.scenarios.seed;
let record=await api('/quotes',{scenario:'seed',description:s.description,quantity:'1',company:s.name,contact:'MCP protocol test',mode:'live_mcp',event_key:crypto.randomUUID()});
const capability=await api('/quotes/'+record.id+'/mcp-capability',{});
const client=new Client({name:'arc-official-sdk-acceptance-client',version:'1.0.0'});
await client.connect(new StreamableHTTPClientTransport(new URL(base+'/mcp'),{requestInit:{headers:{Authorization:'Bearer '+capability.token}}}));
const tools=await client.listTools();if(tools.tools.some(t=>/approve|reserve|commit|send|purchase/.test(t.name)))throw Error('Human-only tool exposed');
async function call(name,args={},expectError=false){const r=await client.callTool({name,arguments:args});trace.push({at:new Date().toISOString(),playbook_version:'1.0',classification:'scripted protocol test, not Recorded AI run',tool:name,job_id:args.job_id||null,result:r.isError?'rejected':'ok'});if(expectError){if(!r.isError)throw Error('Expected rejection');return r;}if(r.isError)throw Error(JSON.stringify(r));return JSON.parse(r.content[0].text);}
async function human(action,data={}){record=await api('/quotes/'+record.id);record=await api('/quotes/'+record.id+'/actions',{action,data,version:record.version,event_key:crypto.randomUUID()});trace.push({human_simulation:action,stage:record.body.stage});}
const candidates=ctx=>ctx.requirements.map(r=>({field:r.field,value:r.value,unit:null,status:r.status,source_refs:[r.source_id]}));
for(let stage=0;stage<8;stage++){
 if(stage===1){await human('inspect',{source_id:'clarification-seed'});await human('resolve',{confirmed:true});}
 const list=await call('list_pending_jobs');const job=list.jobs.findLast(j=>j.stage===stage&&j.state==='queued');if(!job)throw Error('No pending job '+stage);
 let lease=await call('claim_job',{job_id:job.id});
 if(stage===0){await call('report_job_failure',{job_id:job.id,lease:lease.lease,message:'Scripted transient failure to prove bounded retry.'});lease=await call('claim_job',{job_id:job.id});}
 const args={job_id:job.id,lease:lease.lease};
 if(stage===0)await call('get_quote_context',{...args,lease:'wrong-lease'},true);
 let ctx=await call('get_quote_context',args);let first;
 if(stage===0){await call('read_source',{source_id:'request-seed'});await call('read_source',{source_id:'foreign-source-id'},true);await call('lookup_catalog_and_history');await call('inspect_inventory');await call('calculate_schedule');await call('claim_job',{job_id:crypto.randomUUID()},true);await call('add_risk_finding',{...args,proposal:{title:'Scripted host flags interface inspection traceability',source_id:'drawing-seed',impact:'Inspection',owner:'Quality reviewer',blocking:false}});}
 if(stage===5){if(ctx.prior_risk_findings||ctx.risks)throw Error('Risk first pass leaked prior conclusions');first=await call('submit_stage_proposal',{...args,first_pass:true,proposal:{findings:['Validate drawing-controlled interface and procurement freshness; qualify delivery conditions.'],evidence_refs:['drawing-seed','policy-v1']}});ctx=await call('get_quote_context',args);if(!ctx.prior_risk_findings)throw Error('Reconciliation context missing');}
 const calc=stage>=4?await call('calculate_quote',args):null;
 const outputs=[
 {candidate_fields:candidates(ctx),customer_match:s.name,attachment_status:'ready',missing_inputs:[]},
 {requirements:candidates(ctx),conflicts:[],clarification_items:[],assumptions:['Synthetic demo envelope only; not manufacturing certification.'],baseline_proposal:'Confirmed customer clarification defines the estimating baseline.'},
 {configuration:{capacity:s.capacity,material:s.material,outlet:s.outlet,frame:s.frame,cover:s.cover},bom_lines:ctx.bom.map(b=>({item:b.item,specification:b.spec,quantity_per_assembly:b.per_unit,unit:b.unit,drawing_ref:b.drawing_ref,source_refs:[b.source_id]})),drawing_refs:['drawing-seed'],compatibility_checks:['Match reviewed mating opening to illustrative E-seed R1; human engineering approval remains mandatory.'],deviations:[]},
 {operations:ctx.route.map(o=>({sequence:o.sequence,dependencies:o.dependencies,work_center:o.work_center,setup_basis:o.setup_hours+' h per batch of up to '+o.batch_limit,run_basis:o.run_hours+' h per assembly',rate_refs:[o.source_id],evidence_refs:[o.source_id]})),outside_services:[],capability_gaps:[]},
 {offer_refs:ctx.bom.map(b=>b.source_id),sourcing_attempts:[{source:'Synthetic fixture catalog',outcome:'synthetic_fixture',note:'No claim of live supplier website research.'}],make_buy_proposals:ctx.bom.map(b=>b.item+': '+b.classification),inquiry_proposals:[],cost_input_refs:[...new Set(ctx.calculation.lines.flatMap(l=>l.evidence))],calculation_run_id:ctx.calculation?.id},
 {first_pass_artifact:first?.id,reconciled_findings:['Retain engineering resolution, delivery qualification and freight/tax exclusion.'],duplicates:[],proposed_dispositions:['Human must qualify commercial and schedule conditions.'],allowance_input_refs:[]},
 {calculation_run_id:ctx.calculation?.id,terms_proposal:ctx.terms,approval_exceptions:[],customer_visible_summary:'Stationary gravity-discharge hopper; approved selling price must come from the referenced Python result.'},
 {package_draft_ref:'pending-human-preview',included_artifacts:[],consistency_checks:['Scope, quantity, revision, USD and explicit exclusions match reviewed context.'],release_blockers:[]}
 ];
 const proposal={schema_version:'1.0',job_id:job.id,revision:ctx.revision,input_fingerprint:job.input_fingerprint,stage,proposed_output:outputs[stage],evidence_refs:ctx.sources.map(s=>s.id),assumptions:['Fictional demonstration; human review required.'],missing_inputs:[],risk_findings:[],calculation_run_ids:calc?[calc.calculation_run_id]:[],proposed_artifact_refs:[],errors:[]};
 if(stage===0){await call('submit_stage_proposal',{...args,proposal:{...proposal,approved:true}},true);await call('submit_stage_proposal',{...args,proposal:{...proposal,revision:999}},true);}
 await call('submit_stage_proposal',{...args,proposal});
 record=await api('/quotes/'+record.id);if(record.body.stages[stage].status!=='awaiting_review')throw Error('Model completion impersonated human approval');
 if(stage===0)await human('inspect',{source_id:'request-seed'});
 if(stage===4){for(const src of new Set(record.body.calculation.lines.flatMap(l=>l.evidence)))await human('inspect',{source_id:src});for(const l of record.body.calculation.lines)await human('verify',{line_id:l.id,confirmed:true});}
 if(stage===5){for(const r of record.body.risks)if(r.disposition==='open')await human('risk_dispose',{risk_id:r.id,disposition:'qualified'});}
 if(stage===7)await human('preview');
 await human('approve',{stage});console.log('PASS live MCP stage '+(stage+1)+' → separate simulated human gate');
}
await human('export');await human('respond',{response:'accepted'});await human('acceptance_check');await call('compare_acceptance_cost');await human('approve_procurement');
const completedQuote=record.id;
// Explicit stale-revision and foreign-quote rejection with real quote/job identities.
const other=await api('/quotes',{scenario:'seed',description:s.description,quantity:'1',contact:'Foreign quote probe',mode:'live_mcp',event_key:crypto.randomUUID()});
await call('claim_job',{job_id:other.body.jobs[0].id},true);
const secondCap=await api('/quotes/'+other.id+'/mcp-capability',{});
const otherClient=new Client({name:'arc-stale-revision-probe',version:'1.0.0'});await otherClient.connect(new StreamableHTTPClientTransport(new URL(base+'/mcp'),{requestInit:{headers:{Authorization:'Bearer '+secondCap.token}}}));
const secondLease=JSON.parse((await otherClient.callTool({name:'claim_job',arguments:{job_id:other.body.jobs[0].id}})).content[0].text);
record=await api('/quotes/'+other.id);await human('revise',{quantity:'2',material:s.material});
const stale=await otherClient.callTool({name:'get_quote_context',arguments:{job_id:secondLease.id,lease:secondLease.lease}});if(!stale.isError)throw Error('Stale revision was accepted');trace.push({test:'real stale revision after human scope change',result:'rejected'});await otherClient.close();
const called=new Set(trace.filter(x=>x.tool&&x.result==='ok').map(x=>x.tool));for(const tool of tools.tools)if(!called.has(tool.name))throw Error('Untested tool '+tool.name);

await mkdir('artifacts',{recursive:true});await writeFile('artifacts/mcp-proof.json',JSON.stringify({client:'Official @modelcontextprotocol/sdk 1.17.5',transport:'Streamable HTTP',base,quote_id:completedQuote,mode:'live_mcp',human_gates:'API test harness simulates human controls separately; no claim of actual owner approval',trace},null,2));await client.close();console.log('PASS complete MCP round trip, stale/foreign lease checks, no approval tools, preserved human gates.');
