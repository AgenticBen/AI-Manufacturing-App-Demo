-- Server-only RPC. Public roles have no table access; RLS is deny-by-default.
create schema if not exists arc_private;
revoke all on schema arc_private from public, anon, authenticated;
create table arc_private.server_keys (digest text primary key);
create table public.arc_sessions (
 id uuid primary key default gen_random_uuid(), token_hash text unique not null,
 created_at timestamptz not null default now(), expires_at timestamptz not null default now()+interval '7 days'
);
create table public.arc_quotes (
 id uuid primary key, session_id uuid not null references public.arc_sessions(id),
 version integer not null default 1, body jsonb not null,
 event_key text not null, created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 unique(session_id,event_key)
);
create table public.arc_events (
 id uuid primary key default gen_random_uuid(), session_id uuid not null references public.arc_sessions(id),
 quote_id uuid references public.arc_quotes(id), kind text not null, body jsonb not null,
 created_at timestamptz not null default now()
);
create table public.arc_lots (
 id uuid primary key default gen_random_uuid(), session_id uuid not null references public.arc_sessions(id),
 item text not null, on_hand numeric not null check(on_hand>=0), unit_cost numeric not null check(unit_cost>=0),
 usable boolean not null default true, unique(session_id,item)
);
create table public.arc_reservations (
 id uuid primary key default gen_random_uuid(), session_id uuid not null references public.arc_sessions(id),
 quote_id uuid not null references public.arc_quotes(id), revision integer not null,
 lot_id uuid not null references public.arc_lots(id), quantity numeric not null check(quantity>0),
 status text not null check(status in ('held','committed','released','issued')),
 expires_at timestamptz not null, event_key text not null,
 unique(session_id,event_key,lot_id)
);
create index arc_quotes_session_idx on public.arc_quotes(session_id);
create index arc_events_quote_idx on public.arc_events(quote_id,created_at);
create index arc_events_session_idx on public.arc_events(session_id);
create index arc_reservations_quote_idx on public.arc_reservations(quote_id);
create index arc_reservations_lot_idx on public.arc_reservations(lot_id,status,expires_at);
create index arc_reservations_session_idx on public.arc_reservations(session_id);
alter table public.arc_sessions enable row level security;
alter table public.arc_quotes enable row level security;
alter table public.arc_events enable row level security;
alter table public.arc_lots enable row level security;
alter table public.arc_reservations enable row level security;
alter table arc_private.server_keys enable row level security;
revoke all on public.arc_sessions, public.arc_quotes, public.arc_events, public.arc_lots, public.arc_reservations from public,anon,authenticated;

-- This is intentionally privileged and authenticates a high-entropy server capability,
-- then resolves an independently hashed visitor capability before touching tenant data.
-- Neither capability is exposed in static assets. No SQL or table name is caller-controlled.
create function public.arc_rpc(p_key text, p_session text, p_op text, p_data jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
 sid uuid; q public.arc_quotes; l public.arc_lots; r jsonb; x jsonb; avail numeric;
 qty numeric; prior jsonb; rid uuid; qid uuid;
begin
 if not exists(select 1 from arc_private.server_keys where digest=encode(extensions.digest(p_key,'sha256'),'hex')) then
   raise exception 'unauthorized' using errcode='28000';
 end if;
 if p_op='session' then
   if length(p_session)<>64 then raise exception 'invalid session'; end if;
   insert into public.arc_sessions(token_hash) values(p_session) on conflict(token_hash) do nothing;
 end if;
 select id into sid from public.arc_sessions where token_hash=p_session and expires_at>now();
 if sid is null then raise exception 'session expired' using errcode='28000'; end if;
 if p_op='session' then
   insert into public.arc_lots(session_id,item,on_hand,unit_cost) values
     (sid,'FASTENER',5,0.10),(sid,'GATE-200',2,185),(sid,'FRAME-CS',1,240)
   on conflict(session_id,item) do nothing;
   return jsonb_build_object('id',sid);
 elsif p_op='list' then
   return coalesce((select jsonb_agg(jsonb_build_object('id',id,'version',version,'body',body) order by created_at desc) from public.arc_quotes where session_id=sid),'[]');
 elsif p_op='create' then
   if (select count(*) from public.arc_quotes where session_id=sid)>40 then raise exception 'session quote limit'; end if;
   insert into public.arc_quotes(id,session_id,event_key,body) values((p_data->>'id')::uuid,sid,p_data->>'event_key',p_data->'body') on conflict(session_id,event_key) do nothing;
   select * into q from public.arc_quotes where session_id=sid and event_key=p_data->>'event_key';
   return jsonb_build_object('id',q.id,'version',q.version,'body',q.body);
 elsif p_op='inventory' then
   return coalesce((select jsonb_agg(jsonb_build_object('id',a.id,'item',a.item,'on_hand',a.on_hand::text,'unit_cost',a.unit_cost::text,'available',(a.on_hand-coalesce((select sum(b.quantity) from public.arc_reservations b where b.lot_id=a.id and (b.status='committed' or (b.status='held' and b.expires_at>now()))),0))::text)) from public.arc_lots a where a.session_id=sid and a.usable),'[]');
 end if;
 qid:=(p_data->>'id')::uuid;
 select * into q from public.arc_quotes where id=qid and session_id=sid for update;
 if q.id is null then raise exception 'quote not found' using errcode='P0002'; end if;
 if p_op='get' then return jsonb_build_object('id',q.id,'version',q.version,'body',q.body); end if;
 if p_op='events' then return coalesce((select jsonb_agg(jsonb_build_object('kind',kind,'body',body,'at',created_at) order by created_at) from public.arc_events where quote_id=q.id and session_id=sid),'[]'); end if;
 if p_op='allocations' then
 return coalesce((select jsonb_agg(jsonb_build_object('id',b.id,'item',a.item,'quantity',b.quantity::text,'unit_cost',a.unit_cost::text,'status',b.status,'expires_at',b.expires_at,'active',(b.status='committed' or (b.status='held' and b.expires_at>now())))) from public.arc_reservations b join public.arc_lots a on a.id=b.lot_id where b.quote_id=q.id and b.session_id=sid),'[]');
 end if;
 if p_op<>'save' then raise exception 'unsupported operation'; end if;
 -- Duplicate HTTP retries return their original successful state, before CAS.
 if p_data->>'event_key' is not null and exists(select 1 from public.arc_events where quote_id=q.id and body->>'event_key'=p_data->>'event_key') then
   return jsonb_build_object('id',q.id,'version',q.version,'body',q.body);
 end if;
 if q.version<>(p_data->>'version')::int then raise exception 'stale version' using errcode='40001'; end if;
 if p_data->>'inventory_action' in ('release','reserve','commit') then
   -- Same lock order for all bundles prevents deadlocks and protects final-stock races.
   perform id from public.arc_lots where session_id=sid order by id for update;
 end if;
 if p_data->>'inventory_action'='release' then
   update public.arc_reservations set status='released' where quote_id=q.id and status='held';
 elsif p_data->>'inventory_action'='reserve' then
   update public.arc_reservations set status='released' where quote_id=q.id and status='held';
   for x in select value from jsonb_array_elements(p_data->'reserve_lines') loop
     qty:=(x->>'quantity')::numeric;
     if qty<=0 then raise exception 'invalid reservation quantity'; end if;
     select * into l from public.arc_lots where session_id=sid and item=x->>'item' and usable;
     if l.id is null then raise exception 'lot unavailable'; end if;
     select l.on_hand-coalesce(sum(quantity),0) into avail from public.arc_reservations where lot_id=l.id and (status='committed' or (status='held' and expires_at>now()));
     if qty>avail then raise exception 'stock shortage: %',l.item using errcode='P0001'; end if;
     insert into public.arc_reservations(session_id,quote_id,revision,lot_id,quantity,status,expires_at,event_key)
     values(sid,q.id,(p_data->'body'->>'revision')::int,l.id,qty,'held',now()+interval '24 hours',p_data->>'event_key');
   end loop;
 elsif p_data->>'inventory_action'='commit' then
   if exists(select 1 from public.arc_reservations where quote_id=q.id and status='held' and expires_at<=now()) then raise exception 'expired hold: refresh allocation and cost before commitment'; end if;
   update public.arc_reservations set status='committed' where quote_id=q.id and status='held' and expires_at>now();
 end if;
 update public.arc_quotes set body=p_data->'body',version=version+1,updated_at=now() where id=q.id returning * into q;
 insert into public.arc_events(session_id,quote_id,kind,body) values(sid,q.id,coalesce(p_data->>'kind','updated'),jsonb_build_object('event_key',p_data->>'event_key','version',q.version,'detail',p_data->'detail'));
 return jsonb_build_object('id',q.id,'version',q.version,'body',q.body);
end; $$;
revoke all on function public.arc_rpc(text,text,text,jsonb) from public,anon,authenticated;
grant execute on function public.arc_rpc(text,text,text,jsonb) to anon;

