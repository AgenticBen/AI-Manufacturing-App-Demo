import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.demo.agents import agent_records
rows=agent_records()
body=dict(id='D13',title='Agent instructions',home='Supabase (real)',view='playbooks',version='2.0',status='Exact versioned playbooks stored in Supabase; saved outputs are Prepared example.',path='backend/playbooks/',note='Single seed source: backend/playbooks. No real recorded run exists yet.',rows=[dict(line=i+1,**r) for i,r in enumerate(rows)])
Path('supabase/migrations/20260930101000_agent_playbooks.sql').write_text("update public.arc_demo_databases set body='"+json.dumps(body).replace("'","''")+"'::jsonb where id='D13';\n")
