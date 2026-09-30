create table public.arc_shop_rules(id uuid primary key default gen_random_uuid(),session_id uuid not null references public.arc_sessions(id),rule_key text not null,version integer not null,body jsonb not null,created_at timestamptz not null default now(),unique(session_id,rule_key,version));
alter table public.arc_shop_rules enable row level security;
create policy server_only_deny_clients on public.arc_shop_rules for all to anon,authenticated using(false) with check(false);
revoke all on public.arc_shop_rules from public,anon,authenticated;
alter table public.arc_lots add column acquired_at timestamptz;
update public.arc_lots l set acquired_at=s.created_at-interval '120 days' from public.arc_sessions s where s.id=l.session_id;
create or replace function arc_private.arc_rpc(p_key text, p_session text, p_op text, p_data jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
 bucket_count integer;
 sid uuid; q public.arc_quotes; l public.arc_lots; r jsonb; x jsonb; avail numeric;
 qty numeric; prior jsonb; rid uuid; qid uuid;
begin
 if not exists(select 1 from arc_private.server_keys where digest=encode(extensions.digest(p_key,'sha256'),'hex')) then
   raise exception 'unauthorized' using errcode='28000';
 end if;
 if p_op='mcp_resolve' then
   select jsonb_build_object('quote_id',a.id,'session_hash',b.token_hash) into r from public.arc_quotes a join public.arc_sessions b on b.id=a.session_id where a.body->>'mcp_token_hash'=p_data->>'token_hash' and b.expires_at>now();
   if r is null then raise exception 'invalid MCP capability' using errcode='28000'; end if;
   return r;
 end if;
 if p_op='session' then
   if length(p_session)<>64 then raise exception 'invalid session'; end if;
   if not exists(select 1 from public.arc_sessions where token_hash=p_session) and p_data->>'ip_hash' is not null then
     insert into arc_private.session_limits(ip_hash,bucket,count) values(p_data->>'ip_hash',date_trunc('hour',now()),1) on conflict(ip_hash,bucket) do update set count=arc_private.session_limits.count+1 returning count into bucket_count;
     if bucket_count>20 then raise exception 'Demo session creation limit reached; try again next hour'; end if;
   end if;
   insert into public.arc_sessions(token_hash) values(p_session) on conflict(token_hash) do nothing;
 end if;
 select id into sid from public.arc_sessions where token_hash=p_session and expires_at>now();
 if sid is null then raise exception 'session expired' using errcode='28000'; end if;
 if p_op='session' then
   insert into public.arc_lots(session_id,item,on_hand,unit_cost) values
     (sid,'FASTENER',5,0.10),(sid,'GATE-200',2,185),(sid,'FRAME-CS',1,240)
   on conflict(session_id,item) do nothing;
   update public.arc_lots set acquired_at=(select created_at from public.arc_sessions where id=sid)-interval '120 days' where session_id=sid and acquired_at is null;
   return (select jsonb_build_object('id',id,'created_at',created_at,'expires_at',expires_at) from public.arc_sessions where id=sid);
 elsif p_op='session_info' then
   return (select jsonb_build_object('id',id,'created_at',created_at,'expires_at',expires_at) from public.arc_sessions where id=sid);
 elsif p_op='rules' then
   return coalesce((select jsonb_agg(to_jsonb(r)) from (select distinct on(rule_key) id,rule_key,version,body,created_at from public.arc_shop_rules where session_id=sid order by rule_key,version desc) r),'[]');
 elsif p_op='list' then
   return coalesce((select jsonb_agg(jsonb_build_object('id',id,'version',version,'body',body) order by created_at desc) from public.arc_quotes where session_id=sid),'[]');
 elsif p_op='create' then
   if (select count(*) from public.arc_quotes where session_id=sid)>40 then raise exception 'session quote limit'; end if;
   insert into public.arc_quotes(id,session_id,event_key,body) values((p_data->>'id')::uuid,sid,p_data->>'event_key',p_data->'body') on conflict(session_id,event_key) do nothing;
   select * into q from public.arc_quotes where session_id=sid and event_key=p_data->>'event_key';
   return jsonb_build_object('id',q.id,'version',q.version,'body',q.body);
 elsif p_op='inventory' then
   return coalesce((select jsonb_agg(jsonb_build_object('id',a.id,'item',a.item,'on_hand',a.on_hand::text,'unit_cost',a.unit_cost::text,'acquired_at',a.acquired_at,'available',(a.on_hand-coalesce((select sum(b.quantity) from public.arc_reservations b where b.lot_id=a.id and (b.status='committed' or (b.status='held' and b.expires_at>now()))),0))::text)) from public.arc_lots a where a.session_id=sid and a.usable),'[]');
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
 if p_data->'shop_rule' is not null and p_data->'shop_rule'<>'null'::jsonb then
   if length(p_data->'shop_rule'->>'reason')<5 or length(p_data->'shop_rule'->>'statement')<5 then raise exception 'Shop rule requires statement and reason'; end if;
   perform id from public.arc_sessions where id=sid for update;
   insert into public.arc_shop_rules(session_id,rule_key,version,body) select sid,p_data->'shop_rule'->>'key',coalesce(max(version),0)+1,p_data->'shop_rule' from public.arc_shop_rules where session_id=sid and rule_key=p_data->'shop_rule'->>'key';
 end if;
 update public.arc_quotes set body=p_data->'body',version=version+1,updated_at=now() where id=q.id returning * into q;
 insert into public.arc_events(session_id,quote_id,kind,body) values(sid,q.id,coalesce(p_data->>'kind','updated'),jsonb_build_object('event_key',p_data->>'event_key','version',q.version,'detail',p_data->'detail'));
 return jsonb_build_object('id',q.id,'version',q.version,'body',q.body);
end; $$;

