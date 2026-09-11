"""Crée uniquement un dossier et un devis de démonstration non confirmés."""
import argparse

from inspect_live import call, read, save

TAG='DEMO-DOC-RPBM-20260911'
if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', action='store_true', help='autoriser la création des deux documents de démonstration')
    args = parser.parse_args()
    if not args.commit:
        raise SystemExit('Aucune écriture : relancer avec --commit pour créer le jeu de démonstration.')
    assert not read('crm.lead',[['name','=',TAG]],['id'])
    partners=read('res.partner',[['id','=',1],['name','=','RPBM']],['name'],limit=2)
    assert len(partners)==1
    lead=call('model_create',model='crm.lead',values={'name':TAG,'type':'opportunity','partner_id':partners[0]['id']},confirm_write=True)['record_id']
    sale=call('model_create',model='sale.order',values={'partner_id':partners[0]['id'],'opportunity_id':lead,'client_order_ref':TAG},confirm_write=True)['record_id']
    data={'tag':TAG,'lead_id':lead,'sale_id':sale}
    save('demo_ids',data)
    print(data)
    print(read('sale.order',[['id','=',sale]],['name','state','opportunity_id','carrier_id']))
