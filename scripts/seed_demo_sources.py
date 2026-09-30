"""Generate an additive migration from versioned fictional source seeds."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.demo.catalog import seed_databases
sql='''create table if not exists public.arc_demo_databases (id text primary key, body jsonb not null);
alter table public.arc_demo_databases enable row level security;
revoke all on public.arc_demo_databases from anon, authenticated;
grant select on public.arc_demo_databases to anon, authenticated;
drop policy if exists demo_read on public.arc_demo_databases;
create policy demo_read on public.arc_demo_databases for select to anon, authenticated using (true);
'''
for d in seed_databases():
 sql+="insert into public.arc_demo_databases(id,body) values ('"+d['id']+"','"+json.dumps(d).replace("'","''")+"'::jsonb) on conflict(id) do update set body=excluded.body;\n"
Path('supabase/migrations/20260930100000_demo_sources.sql').write_text(sql)
print('Generated 13 fictional source databases')
