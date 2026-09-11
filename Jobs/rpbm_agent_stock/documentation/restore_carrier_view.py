"""Ajout réversible du transporteur sur la préproduction explicitement désignée.

Sans --commit : lecture et aperçu. --restore désactive uniquement cette vue.
Les sauvegardes restent dans le dossier d'audit local ignoré par Git.
"""
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from inspect_live import call, read, save

NAME = 'sale.order.form.rpbm.transporteur.visible'

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit',action='store_true')
    parser.add_argument('--restore',action='store_true')
    args=parser.parse_args()
    fields=call('get_model_fields',model='sale.order',field_names=['carrier_id','locked','state'],attributes=['type','string'])
    save('carrier_field',fields)
    domain=[['name','=',NAME],['active','in',[True,False]]]
    existing=read('ir.ui.view',domain,['name','arch_db','inherit_id','priority','active'])
    assert len(existing)<=1
    arch=Path(__file__).with_name('transporteur_visible.xml').read_text(encoding='utf-8')
    values={'name':NAME,'model':'sale.order','inherit_id':1118,'priority':100,'arch_db':arch,'active':True}
    print('Cible rpbm-preprod ; une vue complémentaire ; aucune vente modifiée.')
    if not args.commit:
        print(values);raise SystemExit(0)
    save('carrier_view_before_'+datetime.now().strftime('%Y%m%d-%H%M%S'),existing)
    if args.restore:
        assert existing
        result=call('model_write',model='ir.ui.view',ids=[existing[0]['id']],values={'active':False},expected_record_count=1,confirm_write=True)
    elif existing:
        result=call('model_write',model='ir.ui.view',ids=[existing[0]['id']],values=values,expected_record_count=1,confirm_write=True)
    else:
        result=call('model_create',model='ir.ui.view',values=values,confirm_write=True)
    print(result)
    after=read('ir.ui.view',domain,['name','arch_db','inherit_id','priority','active'])
    save('carrier_view_after',after)
    assert len(after)==1 and after[0]['active']==(not args.restore)
    if not args.restore:
        def signature(text):
            return [(node.tag, dict(node.attrib), (node.text or '').strip()) for node in ET.fromstring(text).iter()]
        assert signature(after[0]['arch_db']) == signature(arch)
    print('Relecture conforme',after[0]['id'])
