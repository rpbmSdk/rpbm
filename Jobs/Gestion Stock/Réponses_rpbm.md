# Réponses

## 2026-07-23
En entrepôts, on a galleria et genipa en entrepôts principaux, il y a aussi des entrepôts déportés : 
- De R101 à RXX : Dépôt 1
- De RXX à RYY : Dépôt 2
- JXX/TXX : Dépôt 2
Créer un emplacement par Référence
Entrepôt Camion
Penser à voir comment seront réapprovisionnés les articles depuis les dépôts déportés vers les entrepôts principaux.
Pour le Coût on utilise la colonne Prix RV, Pour le prix de vente, il faudra regarder les formules utilisées dans Odoo
Les clients hors assurances sont sensé payer un acompte de 40% du prix de vente, le reste est payé lors de l'installation. Pour les clients assurances, le paiement se fait après l'installation, mais il faudra vérifier si le client a un acompte à payer ou pas.

## 2026-08-05

**Répartition des racks entre dépôts déportés** (remplace la formulation « R101 à RXX » du 23/07) :
- `R101` à `R336` : Dépôt 1
- `R401` à `R937` : Dépôt 2
- `J…` : Dépôt 2
- `T…` : Dépôt 2

Les bornes tombent exactement sur la frontière réelle des blocs (`R3xx` s'arrête à 336, `R4xx`
commence à 401). Couverture : 497 des 568 valeurs `PLACE` distinctes, soit 489 emplacements
après fusion des variantes de casse — 109 en Dépôt 1, 380 en Dépôt 2.

**Emplacements ambigus : ignorés pour l'instant.** Les cellules multi-racks (`R108 - R109`,
`R303 / R324`…), les libellés non codifiés (`Tringle`, `Rack Plafond`, `JDESSUS`, `Palette
Savon`…), les statuts (`PERDU`, `NON TROUVE`, `Vendu ?`…) et les valeurs désignant un entrepôt
sans emplacement précis (`GALLERIA`, `Dépôt 2`…) restent sous `A controler`, à rattacher à la
main plus tard. 49 emplacements concernés, listés par la phase `locations`.

**Valorisation des stocks** : on part sur le plus simple — coût **standard** (prix standard) et
valorisation d'inventaire **manuelle**. Ce sont les valeurs par défaut d'Odoo 17, aucun compte
comptable à paramétrer. AVCO a été écartée : Odoo réécrit `standard_price` à chaque réception
entrante, ce qui écraserait le `PRIX RV` importé.

**Fret** : supposé déjà inclus dans `PRIX RV` — à confirmer avant l'écriture des coûts.

**Fournisseur VSF** : `VSF Centre` et `VSF Ouest` désignent tous deux le partenaire existant
`res.partner` id **5708**, celui que `rpbm_agent.vsf_partner_id` référence. Aucun second
partenaire VSF n'est créé.

**Prix fournisseurs sans `date_start`** : datés au jour de l'import. Les produits qui portent
déjà un tarif VSF actif ne reçoivent pas de seconde ligne — sinon la synchronisation du module
se bloque définitivement sur ce produit.

**Champs `categ_id` et `standard_price` du widget** : le widget continue de ne pas les
renseigner sur les produits qu'il crée à la volée. C'est au client de les compléter.

## 2026-08-05 (bis)

Réponses aux questions Q1, Q2, Q3, Q8, Q9 du document d'import
([archive](archive/questions-import-articles-2026-07-30.md)).

**Q1 — module `rpbm_agent`** : oui, il sera un **prérequis** à l'implémentation du stock. Sa
visibilité pour les équipes est acceptée.

**Q2 — historique du fichier Excel** : on ne conserve **rien**. Le fichier sert uniquement à créer
les articles, les prix fournisseurs VSF, les références d'emplacements, etc. Ni champs Studio
d'audit, ni note interne, ni note au chatter.

**Q3 — valorisation** : question retournée — « est-ce qu'on peut simplement écrire le coût dans
`standard_price` sans mettre en place de méthode de valorisation ? » **Oui.** `standard` +
`manual_periodic` sont les valeurs par défaut d'Odoo 17 (l'`ir.default` est posé par
`stock_account/data/stock_account_data.xml`) : ne rien paramétrer produit exactement cette
configuration, sans aucun compte comptable. Et comme la phase coûts tourne avant tout stock,
`_change_standard_price` (`stock_account/models/product.py:268`) sort sur `quantity_svl <= 0` :
ni couche de valorisation, ni écriture comptable.

**Q5 / Q6 / Q7 / Q10** : déjà répondues le 2026-08-05, ces questions n'auraient pas dû être
reposées. Le fret est confirmé inclus dans `PRIX RV`, sans réserve.

**Q8 — consommables** : tous les articles importés sont définis comme **stockables**.

**Q9 — 43 références à l'eurocode douteux** : **pas d'import**. Elles sont exclues du catalogue
migré plutôt qu'importées hors synchronisation.