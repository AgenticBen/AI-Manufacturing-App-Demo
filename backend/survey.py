"""Comprehensive customer intake. Examples are fictional, not design verification.
Values remain source evidence; only supported fixture inputs drive the estimator.
"""
from copy import deepcopy
from .fixtures import SCENARIOS,source

UNKNOWN='Unknown — requires customer / engineering confirmation'
# key | question | common prepared example; scenario overrides are below.
SECTIONS=[
('project','Project, stakeholders & decision process', '''project_reference|What is the project / RFQ reference?|DEMO-RFQ-2026-09
application_goal|What problem should the hopper solve?|Provide a stationary buffer above an existing downstream process
success_criteria|How will the customer judge success?|Controlled gravity discharge, reviewed interface, accessible inspection and agreed acceptance checks
project_type|New installation, replacement or expansion?|New hopper connected to existing equipment
customer_relationship|New or returning customer?|New fictional customer
site_location|Where will the equipment operate?|Fictional Iowa customer facility; exact address not collected
request_owner|Who owns the requirements and clarifications?|Fictional purchasing role
technical_reviewer|Who approves the mechanical interface and material choices?|Customer engineering role and shop engineer
operations_reviewer|Who confirms operating and cleaning needs?|Customer operations role
budget_approver|Who approves budget and purchase order?|Customer purchasing manager role
revision_reference|Which requirement / drawing revision governs?|Initial RFQ; drawing approval required before release
approval_process|What approvals are needed before manufacture?|Customer scope confirmation, engineering review, PM timeline confirmation and Ops release'''),
('product','Handled product & test evidence', '''handled_product|What product and grades will be handled?|Dry bulk product; exact grade to be confirmed
product_variability|What alternate products or seasonal variations occur?|Single stated product; substitutions require a new review
bulk_density|Loose bulk density and test method (kg/m³)?|Unknown — obtain measured loose bulk density
packed_density|Compacted bulk density (kg/m³)?|Unknown — confirm worst-case stored density
particle_size|Particle size distribution, fines and maximum lump (mm)?|Unknown — obtain representative sample / sieve analysis
particle_shape|Particle shape and fragility?|Unknown — confirm breakage tolerance and sharp particles
moisture_range|Minimum / normal / maximum moisture (% by mass)?|Unknown — measure product and seasonal extremes
product_temperature|Product temperature range (°C)?|Ambient product stated; numerical limits unconfirmed
angle_of_repose|Measured angle of repose and test conditions (degrees)?|Unknown — sample test required; not a hopper wall angle
wall_friction|Wall friction / flow-function test available?|Unknown — no validated flow test supplied
abrasiveness|Abrasiveness and expected wear life?|Unknown — confirm sample and service conditions
corrosiveness|Chemical compatibility, salts or corrosive contaminants?|Unknown — obtain composition and compatibility evidence
hygroscopicity|Hygroscopicity, caking or moisture sensitivity?|Unknown — confirm storage and moisture behavior
cohesion|Known bridging, rat-holing or compaction history?|Unknown — ask operations and review flow testing
contamination|Foreign objects, tramp metal or contaminants?|Unknown — define upstream screening and rejection policy
product_sds|Product SDS, technical data and sample references?|Not supplied; request current customer-selected documents'''),
('capacity','Capacity, throughput & operating cycle', '''nominal_capacity|Required nominal hopper volume (m³)?|Unknown
usable_capacity|Required working / usable volume and freeboard (m³ / %)?|Unknown — usable volume must be separately confirmed
maximum_payload|Maximum stored mass and overload case (kg)?|Unknown — requires validated density and structural review
throughput|Required normal / peak discharge rate (kg/h)?|Unknown — match downstream process demand
batch_size|Typical / maximum batch size (kg or m³)?|Unknown — operations to confirm
fill_rate|Incoming fill rate and peak surge (kg/h)?|Unknown — upstream equipment data required
fill_frequency|How often is the hopper filled?|Intermittent batch operation; exact cycle unconfirmed
operating_hours|Operating hours per day and days per week?|One-shift planning assumption; customer to confirm
duty_cycle|Continuous or intermittent duty; starts per hour?|Intermittent; detailed cycle unconfirmed
residence_time|Maximum residence / hold time (hours)?|Unknown — confirm product degradation or caking limits
turn_down|Required minimum controllable flow or turndown?|Manual isolation; metering performance not promised
future_expansion|Future capacity increase or alternate use?|No future expansion included in the prepared scope'''),
('geometry','Envelope, geometry & mechanical interfaces', '''installation_envelope|Maximum length × width × height (mm)?|Unknown — site survey and approved layout required
hopper_geometry|Required shape and geometry constraints?|Stationary hopper concept; final geometry requires engineering
inlet_size|Fill opening size, shape and flange (mm)?|Unknown — confirm upstream fill interface
inlet_position|Inlet centerline, offset and orientation (mm / degrees)?|Unknown — dimensioned layout required
outlet_size|Outlet clear opening and flange specification (mm)?|Unknown
outlet_elevation|Discharge elevation above finished floor (mm)?|Unknown — site measurement required
bolt_pattern|Bolt pattern, hole size, flange thickness and standard (mm)?|Unknown — customer interface drawing required
adapter_scope|Is a custom transition / adapter required?|Drawing-controlled interface; verify scope
wall_angle|Required wall angle and flow-test basis (degrees)?|Unknown — engineer selects from product flow evidence
wall_thickness|Plate thickness / gauge by panel (mm)?|Unknown — engineer determines from loads and fabrication rules
upstream_interface|Which upstream equipment connects, and who owns it?|Existing customer fill equipment; excluded from shop supply
upstream_loads|Upstream static / impact / vibration loads (N / kN)?|Unknown — equipment supplier data required
downstream_interface|Which downstream equipment connects?|Existing customer process equipment; remains outside quote scope
downstream_loads|Downstream reactions, misalignment and thermal movement?|Unknown — interface load envelope required
access_clearance|Maintenance access and removal envelope (mm)?|Unknown — review with site operations
layout_reference|Dimensioned layout / drawing numbers and revisions?|Illustrative drawings only; customer-approved dimensions required'''),
('construction','Construction, finishes & fabrication', '''construction_material|Specified contact material / grade?|Unknown
noncontact_material|Frame and non-contact material / grade?|Engineer-reviewed frame material per prepared design
surface_finish|Contact surface finish / roughness requirement (Ra µm)?|Not specified — confirm before fabrication
external_finish|External paint, galvanizing or passivation requirements?|Finish follows prepared material selection; coating specification pending
coating_system|Coating chemistry, thickness and color (µm / RAL)?|Unknown — obtain customer-approved finish specification
weld_standard|Weld standard, quality level and weld map?|Unknown — qualified engineer / welding coordinator to define
weld_finish|Continuous welds, flush grinding or crevice limits?|Unknown — hygiene and product requirements to determine
weld_inspection|Visual / NDT method, extent and acceptance criteria?|Unknown — agree inspection plan before release
material_certificates|Material traceability / mill certificates required?|Customer to confirm certificate level and retention
fabrication_tolerance|Dimensional, flatness and alignment tolerances (mm)?|Unknown — approved drawings to specify
seal_material|Seal / gasket material and compatibility evidence?|Prepared seal candidate; exact compatibility requires review
fastener_standard|Fastener grade, finish, size and locking method?|Drawing-controlled; prepared M8 allowance is not a released specification
wear_protection|Replaceable wear liners or sacrificial parts?|Not included; confirm abrasion and wear-life requirements
cover_design|Cover, lid, inspection hatch and weather sealing?|Unknown
structural_frame|Support frame, mounting and anchorage arrangement?|Unknown
lifting_points|Lifting / handling points and certified lift requirements?|Unknown — engineered handling plan required'''),
('discharge','Discharge, gate & flow aids', '''discharge_method|Gravity, screw, belt, rotary valve or other discharge?|Gravity discharge only in the prepared scope
gate_type|Gate type and isolation function?|Manual gate; no rated metering performance claimed
gate_actuation|Manual / pneumatic / electric actuation?|Manual; powered actuators excluded
gate_fail_state|Required fail-safe position and lockout provisions?|Not applicable to manual actuator; lockout details require review
leakage_limit|Permitted product / dust leakage?|Unknown — define acceptance criteria
flow_aids|Vibrators, air pads, agitators or other flow aids?|Excluded; need requires additional engineering scope
blocked_flow|How should bridging or blocked discharge be handled?|Operator procedure to be reviewed; no unsafe access assumed
cleanout_access|Cleanout / service opening and access arrangements?|Reviewed access required; no entry procedure approved
foreign_body_control|Screens, magnets or metal detection required?|Excluded; customer confirms upstream controls
feeding_accuracy|Required dosing accuracy and test basis (%)?|Not included; hopper is not a weighing / dosing system'''),
('site','Site, environmental conditions & utilities', '''installation_environment|Indoor / outdoor and exposure details?|Unknown
ambient_temperature|Ambient minimum / maximum (°C)?|Unknown — customer provides design extremes
relative_humidity|Humidity range / condensation exposure (% RH)?|Unknown — do not infer from city or geography
rain_snow_ice|Rain, snow, ice, washdown or flood exposure?|Unknown — explicit site conditions required
wind_seismic|Wind / seismic design criteria and governing code?|Unknown — site-specific structural review required
floor_foundation|Floor / foundation capacity and anchorage details?|Customer scope; engineer must verify imposed loads
corrosive_atmosphere|Salt, fertilizer, chemical vapor or corrosive atmosphere?|Unknown — customer to identify exposures
site_access|Door, aisle, crane and rigging access (mm / kg)?|Unknown — confirm delivery and installation route
height_constraints|Headroom, overhead services and lifting restrictions?|Unknown — measured site layout required
electrical_supply|Voltage, phase, frequency and available power?|No powered equipment included; future utilities unconfirmed
compressed_air|Air pressure, quality and capacity (bar / L/min)?|Not required by manual scope; confirm if options added
water_drainage|Cleaning water and drainage availability?|Unknown — operations to confirm
installation_owner|Who installs, anchors and connects the hopper?|Customer-appointed installer; installation excluded
commissioning_owner|Who commissions and trains operators?|Customer and qualified installer; scope to be agreed'''),
('safety','Safety, dust & regulatory review', '''dust_hazard|Combustible / respirable dust assessment available?|Unknown — customer hazard assessment and representative testing required
kst_st|Measured Kst / St class with report reference (bar·m/s)?|Unknown — no sample-specific test result supplied
pmax_mie|Pmax, minimum ignition energy and test references?|Unknown — qualified specialist to determine required testing
oxidizer_status|Oxidizer or reactive-material classification?|Unknown — verify current SDS; oxidizers need specialist review
hazardous_area|Hazardous-area / electrical classification?|Unknown — customer and qualified specialist must establish
explosion_protection|Vent, suppression or isolation design responsibility?|Outside prepared scope; specialist hazard review determines needs
dust_collection|Dust extraction interface and performance requirements?|Unknown — customer / specialist system scope
exposure_limits|Worker exposure controls and industrial hygiene evidence?|Unknown — site-specific assessment required
static_grounding|Bonding, grounding and static control requirements?|Unknown — qualified design review required
machine_guarding|Moving parts, pinch points and access guards?|Manual gate pinch points and interfaces require risk review
access_safety|Platforms, ladders, fall protection or confined-space issues?|No platform / entry system included; site review required
lockout_tagout|Isolation, lockout and maintenance responsibilities?|Customer-approved procedure required before operation
applicable_standards|Which codes, standards and jurisdiction apply?|Unknown — engineer identifies applicable requirements; no certification implied
permits_certification|Permits, third-party inspection or certification required?|Unknown — customer / engineer to identify
risk_acceptance|Who signs off unresolved safety / feasibility conditions?|Qualified engineer and responsible customer role; cannot be priced away'''),
('cleaning','Cleaning, hygiene & product changeover', '''cleaning_method|Dry brush, vacuum, wet wash or CIP?|Unknown
cleaning_frequency|Frequency and allowable downtime?|Unknown — customer cleaning procedure required
cleaning_chemistry|Agent, concentration, pH and SDS reference?|Unknown — material and seal compatibility review required
cleaning_temperature|Cleaning temperature / pressure (°C / bar)?|Unknown — procedure limits required
drying_method|Drying method and residual moisture acceptance?|Unknown — confirm before returning to service
hygienic_design|Food / feed contact, hygienic or sanitary design requirements?|No certification asserted; customer to define applicable obligations
allergen_crosscontact|Allergen / cross-contamination controls required?|Unknown — product and site hazard review required
changeover|Product changeover sequence and acceptance criteria?|Single prepared product; changes require review
residue_limit|Maximum residue and cleanliness validation method?|Unknown — customer defines measurable acceptance
inspection_access|How are contact surfaces inspected and accessed?|Customer / engineer to confirm safe access without unsupported entry'''),
('controls','Instrumentation, controls & integration', '''level_detection|High / low level sensors or viewing indicators?|Excluded; optional requirement to be reviewed
weighing_system|Load cells, weighing accuracy and calibration?|Excluded from prepared scope
control_interface|PLC, local controls, I/O and communications?|No controls supplied in manual scope
interlocks|Upstream / downstream permissives and interlocks?|Customer system responsibility; interface review required
emergency_stop|Emergency-stop integration and safety architecture?|No powered controls included; site risk assessment governs
cable_routing|Cable trays, penetrations and protection rating?|Not applicable to base manual scope
alarms|Required alarms and operator notifications?|Not included; define if powered options are requested
remote_monitoring|Data logging, remote access or cybersecurity needs?|No connected device or remote access in base scope'''),
('quality','Inspection, testing & acceptance', '''inspection_plan|Required inspection and test plan / hold points?|Drawing review, dimensional inspection and final document review proposed
factory_test|Factory acceptance test method and witness requirements?|Dry functional gate check proposed; customer to agree criteria
site_test|Site acceptance test and performance demonstration?|Customer / installer scope to be agreed
performance_acceptance|Measurable throughput / flow / leakage acceptance criteria?|Unknown — cannot warrant performance without agreed tests
load_test|Proof-load / structural validation requirements?|Unknown — qualified engineer to specify; no test load assumed
surface_inspection|Coating, finish and weld acceptance criteria?|Unknown — specification required
customer_witness|Customer inspection, notice period and attendance?|Not requested; confirm before scheduling
nonconformance|Deviation approval and nonconformance process?|Written engineering / customer disposition before release
traceability|Serial numbering and component traceability?|Shop job / assembly ID proposed; customer format to confirm
acceptance_signoff|Who signs the completed acceptance record?|Customer technical representative and shop quality role'''),
('delivery','Schedule, shipping & site handoff', '''quote_due|Quote due date and urgency?|Customer to confirm; no guaranteed turnaround
required_on_site|Required on-site date and installation window?|Not committed; requested date recorded separately
schedule_flexibility|Which milestones can move and by how much?|Unknown — customer priority discussion required
drawing_turnaround|Customer drawing approval turnaround (business days)?|Unknown — conditional schedule depends on approval
split_delivery|Partial shipments or batch release allowed?|Customer to confirm; no split delivery assumed
shipping_method|Carrier, shipment mode and responsibility?|Freight excluded; arrange separately
shipping_dimensions|Shipping envelope, weight and road restrictions?|Unknown until reviewed design / shipping plan
packaging|Crating, wrapping, corrosion protection and storage duration?|Prepared packaging allowance; detailed specification pending
loading_unloading|Who supplies loading, rigging and unloading equipment?|Customer / carrier responsibilities to be agreed
transport_risk|Transit damage inspection and claims process?|Customer and carrier to agree before dispatch
storage_conditions|Site storage duration and weather protection?|Unknown — confirm protection before shipment
pm_handoff|Project-system job setup and handoff owner?|PM receives approved BOM, build plan and conditions after acceptance'''),
('commercial','Commercial scope, options & risk tolerance', '''budget_range|Budget range / currency and approval status?|USD; customer budget not supplied
price_basis|Fixed price, allowance, budget estimate or time-and-materials?|Prepared estimate pending explicit review; no automatic commercial commitment
payment_terms|Deposit, milestones and final payment?|Prepared terms: 50% deposit; balance before dispatch
quote_validity|Required price-validity period (days)?|Prepared quote validity: 14 days
freight_tax|Freight, tax and duties inclusions / exclusions?|Freight and tax excluded; no tax determination
scope_exclusions|Customer-supplied items and exclusions?|Foundations, anchors, powered downstream equipment, installation, certification and production release
warranty|Warranty expectations and exclusions?|Not specified; agree written commercial terms
spares|Startup / recommended spares and service support?|Not included; customer to request
insurance_tolerance|Insurance preference and responsibility split?|Discuss project policy versus minimal cover; premium TBD, no policy quoted
change_control|How are requirement changes approved and priced?|Written revision and downstream re-review before commitment
purchase_order|PO requirements, vendor onboarding and release conditions?|Customer PO and reviewed scope required; no real purchase in demo
cancellation|Cancellation, suspension and restocking expectations?|Not specified; agree written terms'''),
('documents','Documents, evidence & unresolved questions', '''customer_drawings|Customer drawings / CAD file references and revisions?|Not supplied at initial intake; request dimensioned interface drawing
photos_scan|Site photographs, scan or survey reference?|Not supplied; customer-selected evidence only
material_test_reports|Density, flow and dust-test report references?|Not supplied; no verified sample test claimed
engineering_reports|Structural, load or hazard report references?|Pending qualified engineering review
cleaning_procedure|Cleaning procedure / compatibility report reference?|Not supplied at initial intake
vendor_datasheets|Approved supplier / component datasheet references?|Prepared fictional supplier offers; exact product review required
required_deliverables|Required drawing, manual, certificate and spare-parts documents?|Quote, reviewed drawings, BOM, manufacturing plan and agreed inspection record
open_questions|What must be clarified before baseline approval?|Scenario-specific clarification plus unresolved engineering evidence
assumptions_to_confirm|Which assumptions need explicit customer confirmation?|All prepared values are fictional examples; unknowns are not approvals
customer_confirmation|Has the customer confirmed this requirements revision?|No — explicit simulated summary send and human review remain separate''')]

OVERRIDES={
 'seed':{'customer_relationship':'Returning fictional client; prior jobs H-101 and H-102','fill_frequency':'Prepared example: two to four batch fills per shift; customer confirmation needed','cleaning_method':'Dry cleaning only; no washdown per stated request','cleaning_chemistry':'No wet-cleaning chemistry in stated scope','rain_snow_ice':'Customer states dry indoor service; no rain or washdown','adapter_scope':'Custom adapter to existing conveyor; customer drawing C-101 R1 required','customer_drawings':'Prepared response C-101 R1 available after explicit clarification review','open_questions':SCENARIOS['seed']['clarification']},
 'grain':{'fill_frequency':'Prepared example: intermittent seasonal batches; peak schedule unconfirmed','cleaning_method':'Dry cleaning proposed; customer procedure unconfirmed','rain_snow_ice':'Customer explicitly states outdoor rain exposure; snow / ice design criteria unknown','external_finish':'Galvanized candidate; outside coating lead time is reviewed separately','schedule_flexibility':'Seasonal installation window; exact dates require customer confirmation','engineering_reports':'Prepared E-202 R1 demonstration load envelope; actual site loads need engineering','open_questions':SCENARIOS['grain']['clarification']},
 'feed':{'cleaning_method':'Intermittent wet cleaning per customer-defined procedure','cleaning_chemistry':'Neutral detergent in prepared CS-3 response; concentration and temperature still need limits','cleaning_procedure':'Prepared customer cleaning sheet CS-3 available after explicit clarification review','rain_snow_ice':'Intermittent wet cleaning stated; other exposure conditions unconfirmed','allergen_crosscontact':'Customer must identify feed ingredients and cross-contact controls; no hygienic certification implied','open_questions':SCENARIOS['feed']['clarification']}}

# Rich fictional customer answers: goals/operating descriptions, never certified capabilities.
EXAMPLE_DETAILS={
 'operating_hours':'Prepared customer plan: 8 hours/day, 5 days/week; seasonal overtime by separate agreement',
 'duty_cycle':'Intermittent batch loading and gravity drawdown; planned 4–8 cycles per shift',
 'residence_time':'Customer target: empty by end of shift; overnight hold only with reviewed storage procedure',
 'product_variability':'One nominated product per hopper; customer approval required before changing product or grade',
 'foreign_body_control':'Customer retains upstream screening; screen specification and maintenance remain customer responsibilities',
 'turn_down':'Manual gate used for isolation; downstream conveyor controls rate, no calibrated turndown guarantee requested',
 'future_expansion':'No larger future payload requested; reserve layout space only, subject to site drawing',
 'inlet_position':'Customer preference: centered vertical fill; final offsets follow the signed interface layout',
 'upstream_interface':'Customer-owned bag / bulk transfer equipment; no load may be transferred without an approved interface design',
 'layout_reference':'Prepared layout request L-01 R0; fabrication must wait for a dimensioned approved revision',
 'gate_type':'Hand-operated slide gate for start/stop isolation; lockable handle requested for maintenance review',
 'blocked_flow':'Stop feed, isolate connected equipment and follow an approved maintenance procedure; no worker entry assumed',
 'feeding_accuracy':'No dosing tolerance requested; downstream customer equipment performs metering',
 'changeover':'Single product in prepared scope; isolate and clean before any separately reviewed product change',
 'inspection_access':'Customer asks for external visual access to outlet and contact surfaces; detailed access design unapproved',
 'inspection_plan':'Customer requests dimensional and visual weld checks before finish, gate function after assembly and final photo record',
 'factory_test':'Customer requests five unloaded manual gate cycles plus dimensional checks; test acceptance criteria to be signed',
 'customer_witness':'Customer accepts remote review of final photographs for this example; request 2 business days notice of hold point',
 'nonconformance':'Shop records deviation, stops affected work and seeks written engineer / customer disposition',
 'traceability':'Assembly serial and job number on nameplate; link material certificates and final inspection to that job record',
 'acceptance_signoff':'Customer technical role signs documented acceptance; purchasing confirms commercial receipt separately',
 'quote_due':'Prepared customer request: budgetary response within 3 business days after clarifications; not a shop promise',
 'drawing_turnaround':'Prepared customer planning allowance: 2 business days to review each drawing issue',
 'split_delivery':'Customer preference: complete assemblies delivered together; partial shipment needs written agreement',
 'shipping_method':'Customer-arranged flatbed / enclosed freight as agreed after final envelope and mass are known; freight excluded',
 'packaging':'Customer asks for protected flanges, secured gate, wrapped loose parts and a packing list; final crate design unapproved',
 'loading_unloading':'Shop loads by agreed lift plan; customer provides suitable unloading equipment and site rigging team',
 'transport_risk':'Customer records condition on arrival, photographs damage and raises carrier exceptions before receipt signoff',
 'storage_conditions':'Customer plans covered short-term storage under two weeks; drying and corrosion protection remain subject to finish review',
 'budget_range':'USD; customer asks for a base-scope price and separately identified options, no approved budget ceiling supplied',
 'spares':'Customer requests an optional spare gate-seal kit and fastener list; not included in base quote',
 'change_control':'Sales records change request and price/schedule impact; customer and engineer approve a new revision before affected work',
 'purchase_order':'Fictional purchasing team issues PO referencing quote revision and approved drawings; no actual order in demo',
 'required_deliverables':'Dimensioned general arrangement, interface drawing, BOM, manufacturing plan, inspection checklist, material records where agreed and maintenance notes',
 'photos_scan':'Prepared evidence request: front/side site photos, outlet interface close-up and clearance sketch; no actual site photos supplied',
 'request_owner':'Fictional purchasing coordinator role; requests one bundled clarification email',
 'technical_reviewer':'Customer mechanical engineer role confirms interface; shop engineer owns fabrication design review',
 'operations_reviewer':'Customer shift supervisor role confirms fill/discharge cycle, access and cleaning procedure',
 'approval_process':'Sales confirms requirements → engineer approves design → PM confirms sequence → Ops clears release → purchasing reviews acceptance recheck'
}

def schema():
    return [{'id':id,'title':title,'fields':[{'id':line.split('|')[0],'question':line.split('|')[1]} for line in text.splitlines()]} for id,title,text in SECTIONS]

def defaults(sid):
    if sid not in SCENARIOS:return {f['id']:'' for sec in schema() for f in sec['fields']}
    values={line.split('|')[0]:line.split('|')[2] for _,_,text in SECTIONS for line in text.splitlines()}
    s=SCENARIOS[sid]
    values.update(handled_product=s['handled'],nominal_capacity=s['capacity'],construction_material=s['material'],outlet_size=s['outlet'],cover_design=s['cover'],structural_frame=s['frame'],installation_environment=s['environment'],site_location=s['city']+' · fictional facility; exact site not supplied')
    values.update(EXAMPLE_DETAILS)
    from .calculations import dec,number
    density={'seed':'650','grain':'720','feed':'550'}[sid];volume={'seed':'3','grain':'8','feed':'5'}[sid]
    values.update(
        bulk_density='Prepared customer planning estimate: '+density+' kg/m³; no sample test supplied, engineering must confirm',
        usable_capacity='Prepared working-volume target: '+number(dec(volume)*dec('0.9'))+' m³ with 10% planning freeboard; final geometry unverified',
        maximum_payload='Planning full-volume product mass: '+number(dec(volume)*dec(density))+' kg, calculated in Python from assumed density; not a rated structural load',
        throughput={'seed':'Customer target: 2,000 kg/h normal, 3,000 kg/h peak; no validated flow performance','grain':'Customer target: 6,000 kg/h normal, 8,000 kg/h peak; confirm downstream conveyor limit','feed':'Customer target: 2,500 kg/h normal, 4,000 kg/h peak; blend flowability untested'}[sid],
        batch_size={'seed':'Customer planning batch: 1,000 kg; peak surge to be confirmed','grain':'Customer planning batch: 4,000 kg; seasonal surge to be confirmed','feed':'Customer planning batch: 1,500 kg; blend-to-blend variation to be confirmed'}[sid],
        fill_rate={'seed':'Prepared customer target: 4,000 kg/h; upstream rating unverified','grain':'Prepared customer target: 10,000 kg/h; upstream rating unverified','feed':'Prepared customer target: 5,000 kg/h; upstream rating unverified'}[sid],
        installation_envelope={'seed':'Customer layout target: 2,200 × 2,200 × 3,600 mm maximum; site survey pending','grain':'Customer layout target: 3,200 × 3,200 × 4,800 mm maximum; site survey pending','feed':'Customer layout target: 2,600 × 2,600 × 4,200 mm maximum; site survey pending'}[sid],
        outlet_elevation={'seed':'Customer target: 1,200 mm above finished floor; conveyor interface must confirm','grain':'Customer target: 1,500 mm above finished floor; layout must confirm','feed':'Customer target: 1,300 mm above finished floor; downstream interface must confirm'}[sid],
        access_clearance='Customer planning target: 900 mm clear service aisle on one side; actual safe access requires site review',
        site_access='Customer requests delivery as a completed assembly if access permits; doorway and lift envelope still need measurement',
        cleaning_frequency={'seed':'Prepared operations plan: dry inspection at each shift end; isolate before cleaning','grain':'Prepared operations plan: inspect between seasonal batches and before shutdown; procedure unapproved','feed':'Prepared operations plan: clean between designated product campaigns; chemistry and validation still require review'}[sid])
    values.update(OVERRIDES[sid]);return values

def normalize(sid,submitted=None):
    values=defaults(sid);allowed=set(values)
    if submitted is not None:
        if not isinstance(submitted,dict) or set(submitted)-allowed:raise ValueError('Survey contains unknown field IDs')
        for key,value in submitted.items():
            if not isinstance(value,str) or len(value)>1000:raise ValueError('Survey answers must be text of at most 1,000 characters')
            values[key]=value.strip()
    return values

def requirements(values,classification='Prepared fictional example'):
    rows=[]
    for section in schema():
        for f in section['fields']:
            value=values.get(f['id'],'').strip()
            unresolved=not value or any(t in value.lower() for t in ['unknown','not supplied','not specified','unconfirmed','to confirm','pending','unverified','not a rated','must confirm','must be','required before','requires','to be agreed','not committed'])
            rows.append(dict(field=f['id'],question=f['question'],section=section['title'],value=value or 'Not supplied',status='Needs confirmation' if unresolved else 'Stated · review required',source_id='survey-submission',line=len(rows)+1,classification=classification))
    return rows

def attach(q,values,classification):
    q['survey_answers']=deepcopy(values);q['survey_requirements']=requirements(values,classification)
    content='\n'.join(f"{r['section']} | {r['question']} | {r['value']} | {r['status']}".replace('\n',' / ').replace('\r',' ') for r in q['survey_requirements'])
    item=source('survey-submission','Comprehensive customer survey',content,'survey_input','Numbered answers; '+classification)
    item['synthetic']=classification.startswith('Prepared')
    q['sources']=[s for s in q['sources'] if s['id']!='survey-submission']+[item]
    q['survey_summary']={'fields':len(values),'answered':sum(bool(v.strip()) for v in values.values()),'needs_confirmation':sum(r['status']=='Needs confirmation' for r in q['survey_requirements']),'classification':classification}
    q['requirements']=[r for r in q['requirements'] if not r.get('section')]+q['survey_requirements']


def ensure_survey(q):
    if not q.get('survey_requirements'):
        sid=q.get('scenario_id','custom')
        attach(q,normalize(sid,q.get('intake',{}).get('survey')),'Prepared supplementary example · not original customer submission' if sid in SCENARIOS else 'Customer / operator input · unverified')
