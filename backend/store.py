import os, hashlib, httpx
from dotenv import load_dotenv
load_dotenv()
class StoreError(Exception):
    def __init__(self, message, status=409): self.message=message; self.status=status; super().__init__(message)
class Store:
    def __init__(self):
        self.url=os.environ.get('SUPABASE_URL',''); self.key=os.environ.get('SUPABASE_PUBLISHABLE_KEY',''); self.secret=os.environ.get('ARC_BACKEND_TOKEN','')
    def call(self, token, operation, data=None):
        return self.call_hash(hashlib.sha256(token.encode()).hexdigest(), operation, data)
    def call_hash(self, session_hash, operation, data=None):
        if not self.url or not self.key or not self.secret: raise StoreError('Hosted Supabase configuration is required. No local persistence fallback.',503)
        try:
            response=httpx.post(self.url+'/rest/v1/rpc/arc_rpc',headers={'apikey':self.key,'Content-Type':'application/json'},json={'p_key':self.secret,'p_session':session_hash,'p_op':operation,'p_data':data or {}},timeout=25)
        except httpx.HTTPError: raise StoreError('Supabase could not be reached. Your action was not confirmed; retry safely.',503)
        if response.status_code>=400:
            payload=response.json(); message=payload.get('message','Persistence rejected the action')
            status=404 if payload.get('code')=='P0002' else 401 if payload.get('code')=='28000' else 409
            raise StoreError(message,status)
        return response.json()
    def save(self, token, record, kind, event_key, inventory_action=None, reserve_lines=None, detail=None, shop_rule=None):
        return self.call(token,'save',{'id':record['id'],'version':record['version'],'body':record['body'],'kind':kind,'event_key':event_key,'inventory_action':inventory_action,'reserve_lines':reserve_lines or [],'detail':detail,'shop_rule':shop_rule})
