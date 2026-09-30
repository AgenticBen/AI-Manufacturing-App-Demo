"""Read-only public, fictional demo sources persisted in Supabase."""
import httpx
from .store import StoreError

def read_databases(store, id=None):
    try:
        r=httpx.get(store.url+'/rest/v1/arc_demo_databases',headers={'apikey':store.key},params={'select':'body',**({'id':'eq.'+id} if id else {})},timeout=20)
        r.raise_for_status()
        values=[x['body'] for x in r.json()]
    except (httpx.HTTPError,ValueError,KeyError):
        raise StoreError('Demo source library is unavailable. Please retry.',503)
    if id:
        if not values:raise StoreError('Database not found',404)
        return values[0]
    return sorted(values,key=lambda x:int(x['id'][1:]))
