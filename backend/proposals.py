"""Strict stage proposal payloads. External narrative never becomes authoritative arithmetic."""
from pydantic import BaseModel,ConfigDict,Field
from typing import Literal,Optional

class Strict(BaseModel):model_config=ConfigDict(extra='forbid')
class Candidate(Strict):
    field:str=Field(min_length=1,max_length=100)
    value:str=Field(max_length=3000)
    unit:Optional[str]=None
    status:Literal['stated','inferred','unknown','conflicting','confirmed']
    source_refs:list[str]
class Clarification(Strict):
    issue:str
    owner:Literal['customer','internal']
    blocker:bool
    question:str
class Intake(Strict):
    candidate_fields:list[Candidate]=Field(min_length=1)
    customer_match:str
    attachment_status:Literal['ready','missing','unreadable','not_applicable']
    missing_inputs:list[str]
class Requirements(Strict):
    requirements:list[Candidate]=Field(min_length=1)
    conflicts:list[str]
    clarification_items:list[Clarification]
    assumptions:list[str]
    baseline_proposal:str
class BomLine(Strict):
    item:str
    specification:str
    quantity_per_assembly:str
    unit:Literal['ea','kg','m','sheet']
    drawing_ref:str
    source_refs:list[str]
class Engineering(Strict):
    configuration:dict[str,str]
    bom_lines:list[BomLine]=Field(min_length=1)
    drawing_refs:list[str]=Field(min_length=1)
    compatibility_checks:list[str]=Field(min_length=1)
    deviations:list[str]
class Operation(Strict):
    sequence:int=Field(ge=1)
    dependencies:list[str]
    work_center:str
    setup_basis:str
    run_basis:str
    rate_refs:list[str]=Field(min_length=1)
    evidence_refs:list[str]=Field(min_length=1)
class Manufacturing(Strict):
    operations:list[Operation]=Field(min_length=1)
    outside_services:list[str]
    capability_gaps:list[str]
class Attempt(Strict):
    source:str
    outcome:Literal['retrieved','unavailable','price_absent','synthetic_fixture']
    note:str
class Sourcing(Strict):
    offer_refs:list[str]=Field(min_length=1)
    sourcing_attempts:list[Attempt]
    make_buy_proposals:list[str]
    inquiry_proposals:list[str]
    cost_input_refs:list[str]=Field(min_length=1)
    calculation_run_id:str
class Risk(Strict):
    first_pass_artifact:str
    reconciled_findings:list[str]
    duplicates:list[str]
    proposed_dispositions:list[str]
    allowance_input_refs:list[str]
class Pricing(Strict):
    calculation_run_id:str
    terms_proposal:dict[str,str]
    approval_exceptions:list[str]
    customer_visible_summary:str
class Release(Strict):
    package_draft_ref:str
    included_artifacts:list[str]
    consistency_checks:list[str]=Field(min_length=1)
    release_blockers:list[str]
MODELS=[Intake,Requirements,Engineering,Manufacturing,Sourcing,Risk,Pricing,Release]

def validate(stage,output,source_ids,calculation_ids):
    parsed=MODELS[stage].model_validate(output).model_dump()
    def refs(v,key=''):
        if isinstance(v,dict):
            for k,value in v.items():refs(value,k)
        elif isinstance(v,list):
            if key in ('source_refs','evidence_refs','drawing_refs','offer_refs','rate_refs','cost_input_refs','allowance_input_refs','included_artifacts'):
                if not set(v)<=source_ids:raise ValueError('Foreign or missing source/artifact reference')
            else:
                for child in v:refs(child)
        elif key in ('drawing_ref',) and v not in source_ids:raise ValueError('Foreign drawing reference')
        elif key=='calculation_run_id' and v not in calculation_ids:raise ValueError('Foreign calculation reference')
    refs(parsed)
    return parsed
