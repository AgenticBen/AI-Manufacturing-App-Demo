from fastapi.testclient import TestClient
from backend.api import app,store
from backend.demo.catalog import seed_databases
from backend.store import StoreError
from unittest.mock import patch

client=TestClient(app)

def test_source_records_are_stable_and_complete():
    dbs=seed_databases()
    assert [d['id'] for d in dbs]==['D'+str(i) for i in range(1,14)]
    for db in dbs:
        assert db['rows'] and 'fictional' in db['status']
        assert len({r['id'] for r in db['rows']})==len(db['rows'])
        assert [r['line'] for r in db['rows']]==list(range(1,len(db['rows'])+1))
    assert len([r for r in dbs[1]['rows'] if r['real_website']])==5
    assert 'Specialist engineering required' in dbs[8]['rows'][2]['design_implications']

def test_readonly_source_endpoints():
    with patch('backend.demo_sources.read_databases',side_effect=lambda store,id=None: next(d for d in seed_databases() if d['id']==id) if id else seed_databases()):
        assert len(client.get('/api/databases').json())==13
        assert client.get('/api/databases/D3').json()['rows'][0]['hourly_rate']=='82'
        assert client.post('/api/databases/D3',headers={'X-Arc-Client':'web'},json={}).status_code==405

def test_unknown_and_unavailable_sources():
    with patch('backend.demo_sources.read_databases',side_effect=StoreError('Database not found',404)):
        assert client.get('/api/databases/D99').status_code==404
    with patch('backend.demo_sources.httpx.get',side_effect=__import__('httpx').ConnectError('offline')):
        assert client.get('/api/databases').status_code==503

def test_each_agent_has_exact_versioned_playbook():
    from backend.demo.agents import agent_records
    from pathlib import Path
    records=agent_records()
    assert len(records)==22
    for r in records:
        assert r['text']==Path('backend/playbooks/agent-'+r['id']+'.md').read_text()
        assert all(d in {'D'+str(i) for i in range(1,14)} for d in r['databases'])
        assert all(label in r['text'] for label in ['## Inputs','## Allowed databases','## Allowed tools','## Output fields','## Human check','## Failure behavior'])
    with patch('backend.demo_sources.read_databases',return_value={'rows':records}):
        assert len(client.get('/api/playbooks').json())==22
        assert client.get('/api/playbooks/intake').json()['version']=='2.0'
        assert client.get('/api/playbooks/unknown').status_code==404

def test_past_quotes_open_as_one_page_pdfs():
    from backend.document_pdf import source_record_pdf
    from pypdf import PdfReader
    from io import BytesIO
    db=next(d for d in seed_databases() if d['id']=='D6')
    for row in db['rows']:
        pdf=source_record_pdf(db,row)
        assert len(PdfReader(BytesIO(pdf)).pages)==1
    with patch('backend.demo_sources.read_databases',return_value=db):
        assert client.get('/api/databases/D6/records/D6-001/pdf').content.startswith(b'%PDF')
        assert client.get('/api/databases/D6/records/unknown/pdf').status_code==404
