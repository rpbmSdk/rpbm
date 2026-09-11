"""Lectures documentaires via Paradigme MCP, profil local et cible vérifiés."""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import load_profile, load_env, _parse_simple_yaml, PROFILES_PATH

CONN = load_profile()
assert CONN['profile'] == 'rpbm-preprod'
assert CONN['database'] == 'rpbm-pre-prod-37860002'
# L'utilisateur désigne l'URL de branche ; le profil utilise son alias stable.
# La base est identique, aucun profil ni secret global n'est modifié.
assert CONN['url'].rstrip('/') in ['https://rpbm-pre-prod.odoo.com','https://rpbm-pre-prod-37860002.dev.odoo.com']
CONN['url'] = 'https://rpbm-pre-prod-37860002.dev.odoo.com'
ENV = load_env()
CONFIG = _parse_simple_yaml(PROFILES_PATH.read_text(encoding='utf-8'))
ENDPOINT = CONFIG.get('mcp_server_url', 'https://mcp.odoo.paradigme.io/mcp')
DATA = ROOT / '.paradigme/audits/rpbm-preprod/data/documentation-2026-09-11'

def call(name, **kw):
    args = {k:v for k,v in CONN.items() if k != 'profile'}
    args.update(kw)
    payload = {'jsonrpc':'2.0', 'id':1, 'method':'tools/call', 'params':{'name':name,'arguments':args}}
    headers = {'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
    if ENV.get('PARADIGME_MCP_API_KEY'):
        headers['Authorization'] = 'Bearer ' + ENV['PARADIGME_MCP_API_KEY']
    req = urllib.request.Request(ENDPOINT, json.dumps(payload).encode(), headers)
    with urllib.request.urlopen(req, timeout=90) as response:
        raw = response.read().decode()
    if raw.startswith('event:') or raw.startswith('data:'):
        raw = next(line[5:].strip() for line in raw.splitlines() if line.startswith('data:'))
    result = json.loads(raw)
    if result.get('error'): raise RuntimeError(result['error'])
    result = result['result']
    if result.get('isError'): raise RuntimeError(result)
    for c in result.get('content', []):
        if c.get('type') == 'text':
            try: return json.loads(c['text'])
            except ValueError: pass
    return result.get('structuredContent', result)

def records(result):
    if isinstance(result, list): return result
    rows = result.get('records', result.get('result', result.get('data', [])))
    if isinstance(rows, dict): return records(rows)
    return [dict(r.get('values', r), id=r.get('id', r.get('values', {}).get('id'))) for r in rows]

def read(model, domain, fields, limit=1000):
    return records(call('model_search_read',model=model,domain=domain,fields=fields,limit=limit))

def save(name, obj):
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / (name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__ == '__main__':
    print('Profil confirmé:',CONN['profile'], CONN['url'],CONN['transport'])
    module = read('ir.module.module', [['name','=','rpbm_agent']], ['name','state','installed_version'])
    save('module', module); print('Module:',module)
    fields = call('get_model_fields',model='ir.ui.view',field_names=['name','model','inherit_id','arch_db','priority','active','key','write_date'],attributes=['string','type'])
    save('view_fields',fields)
    views = read('ir.ui.view',[['model','=','sale.order'],['type','=','form']],['name','inherit_id','arch_db','priority','active','key','write_date'])
    save('sale_views',views)
    for v in views:
        if any(s in v['arch_db'] for s in ['carrier_id','delivery','rpbm_agent_widget']):
            print('VUE',v['id'],v['name'],'parent',v['inherit_id'],'priorité',v['priority'])
            for line in v['arch_db'].splitlines():
                if any(s in line for s in ['carrier_id','delivery','invisible']): print(line[:350])
    for model, fields in [
        ('stock.warehouse',['name','lot_stock_id']),
        ('stock.location',['name','complete_name','location_id','usage']),
        ('stock.route',['name','sale_selectable','shipping_selectable']),
        ('stock.rule',['name','route_id','location_src_id','location_dest_id','picking_type_id','procure_method']),
        ('stock.picking.type',['name','sequence_code','default_location_src_id','default_location_dest_id','reservation_method','create_backorder']),
        ('stock.putaway.rule',['location_in_id','location_out_id']),
        ('delivery.carrier',['name','route_ids','product_id','fixed_price'])]:
        rows=read(model,[],fields);save(model,rows); print(model,len(rows))
