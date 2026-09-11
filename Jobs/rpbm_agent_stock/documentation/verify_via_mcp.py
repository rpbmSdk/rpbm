"""Rejoue le contrôle structurel existant en lecture seule via MCP."""
import contextlib
import io
from pathlib import Path
from inspect_live import CONN, call, read, save
from common import Odoo
import verify_structural

class ReadOnlyMCP(Odoo):
    def __init__(self):
        self.url=CONN['url']; self.profile=CONN['profile']; self.commit=False
    def search_read(self,model,domain,fields,limit=0):
        return read(model,domain,fields,limit=limit or 1000)
    def search_count(self,model,domain):
        rows=read(model,domain,['id'],limit=1000)
        assert len(rows)<1000, 'Comptage tronqué interdit'
        return len(rows)
    def execute(self,*args,**kwargs):
        raise RuntimeError('Appel direct interdit dans cet adaptateur MCP')

if __name__=='__main__':
    buffer=io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result=verify_structural.phase_check(ReadOnlyMCP(),None)
    save('structural_results',verify_structural.RESULTS)
    Path(__file__).with_name('controle-structurel-2026-09-11.txt').write_text(buffer.getvalue(),encoding='utf8')
    print(buffer.getvalue())
    raise SystemExit(result)
