# Registre des validations métier

Ce document centralise les décisions à obtenir du client avant toute évolution qui modifie une donnée métier, un prix ou le comportement visible du widget. Il complète la [roadmap](roadmap.md) et les [cartographies de l'instance](../../docs/cartographie/README.md).

## Mode d'emploi

- Statuts possibles : **À soumettre**, **En attente**, **Validé**, **Refusé**, **Remplacé**.
- Une réponse client doit renseigner la décision retenue, la date et la personne qui la valide.
- Aucun item signalé **bloquant prix** ne doit être codé tant qu'il n'est pas **Validé**.
- Une décision qui modifie une entrée existante est ajoutée dans la section « Historique des décisions » ; ne pas écraser l'historique.

## Décisions suivies

| ID | Lot | Décision à obtenir | Proposition préparée | Impact | Statut | Réponse / décision client | Date / validé par |
|---|---|---|---|---|---|---|---|
| VM-01 | L1.2.b | `GLACE AR` correspond-elle à « Lunette arrière » ou à une glace latérale ? | Suggérer « Lunette arrière », modifiable par l'utilisateur. | **Bloquant prix** : « Pièce concernée » pilote le forfait de pose. | Validé | `GLACE AR` → « Lunette arrière ». | 2026-07-27 / Métier RPBM |
| VM-02 | L1.2.b | Les glaces fixes et custodes relèvent-elles de « Glace Latérale » ou « Autre... » ? | Suggérer « Glace Latérale » pour `GLACE FIXE PORTE AR`, modifiable par l'utilisateur. | **Bloquant prix**. | Validé | Les glaces de porte et fixes → « Glace Latérale ». | 2026-07-27 / Métier RPBM |
| VM-03 | L1.2.b | `Autre...` suffit-il pour les calques non couverts, ou faut-il une valeur « indéterminé / à saisir » ? | Utiliser `Autre...` par défaut et laisser le choix visible/modifiable. | **Bloquant prix** ; couvre feux, phares, rétroviseurs, joints, essuie-glaces, etc. | Validé | `Autre...` est la valeur par défaut. | 2026-07-27 / Métier RPBM |
| VM-04 | L1.2.b | Le widget doit-il proposer et écrire « Pièce concernée » après validation visible de l'utilisateur ? | Oui : suggestion issue du calque X'Glass, jamais une écriture silencieuse ; conserver en parallèle le libellé X'Glass exact. | **Bloquant prix**. | Validé | Suggestion visible et modifiable avant confirmation. | 2026-07-27 / Métier RPBM |
| VM-05 | L1.3 | À quel moment les champs Eurocode/VSF doivent-ils être alimentés : dès la Piste/Opportunité, ou seulement depuis le devis ? | Écrire dès qu'un article VSF est explicitement sélectionné ; la donnée est ensuite disponible sur le devis lié via les champs `related`. | Processus commercial et qualité de données. | Validé | Depuis le devis seulement (décision du 2026-10-05, voir VD-02). Réponse précédente (2026-07-27) : l'article sélectionné est recherché/créé comme produit ; pas d'écriture CRM supplémentaire demandée. | 2026-10-05 / Stanley SERIN (tient lieu de réponse du client) ; 2026-07-27 / Métier RPBM |
| VM-06 | L1.3 | Quel champ porte la référence constructeur VSF ? | Cibler `crm.lead.x_studio_field_MNzfJ` (« Code Constructeur »), pas `x_studio_field_e6OAd` (« Autre Référence »). | Cohérence avec l'usage historique ; 3 411 valeurs contre 43. | Remplacé | Référence conservée sur le produit créé, pas sur `crm.lead`. | 2026-07-27 / Métier RPBM |
| VM-07 | L1.3 | Le prix `prixVenteRPBM` de VSF doit-il alimenter « VSF - Prix VIT » ? Que couvrent `JT1`/`JT2`/`JT3` ? | Ne rien écrire dans `VIT` tant que la source et le périmètre des joints ne sont pas confirmés. | **Bloquant prix** : `VIT` entre dans le prix facturé au client. | Validé | Ne jamais alimenter `VIT`, `JT1`, `JT2` ou `JT3`. | 2026-07-27 / Métier RPBM |
| VM-08 | L1.3 | Faut-il créer un miroir `related` du code constructeur sur `sale.order` ? | Ne l'écrire que sur l'opportunité tant que le besoin devis n'est pas confirmé. | Parité Piste/Devis, sans impact tarifaire connu. | Refusé | Aucun miroir `related` supplémentaire. | 2026-07-27 / Métier RPBM |
| VM-09 | L1.4 | Que doit-il se passer pour un devis sans opportunité liée ? | Afficher un avertissement et ne pas transférer les données X'Glass ; demander de rattacher une opportunité. | Évite une écriture silencieusement perdue sur les 38 devis concernés au diagnostic. | Validé | Masquer la page du widget sur les devis sans opportunité. | 2026-07-27 / Métier RPBM |
| VM-10 | L1.6 | Quelle valeur de la pièce OE doit alimenter `sale.order.line.x_studio_prix_x_glass` ? | Utiliser le prix X'Glass de la pièce sélectionnée, puis laisser l'automatisation « Tarif x glass » calculer `price_unit`. | **Bloquant prix** : l'automatisation applique `prix X'Glass × 1,5`. | Validé | Utiliser `articleVsf.prixVenteRPBM`, jamais le prix de pièce OE. | 2026-07-27 / Métier RPBM |
| VM-11 | L4 | Le coefficient de `× 1,085` utilisé pour le prix de pose correspond-il à une TVA réduite ou à une marge ? | Documenter sa signification, son propriétaire et les conditions où il s'applique avant toute refonte. | **Bloquant refonte prix**. | À soumettre | — | — |
| VM-12 | L4 | Pour une pièce « À trouver », le prix VSF peut-il rester le prix de référence par défaut ? | Conserver provisoirement ce comportement jusqu'à décision contraire. | **Bloquant refonte prix** ; influence le prix proposé. | À soumettre | — | — |

## Historique des décisions

| ID | Décision | Date | Validé par | Source |
|---|---|---|---|---|
| VD-01 | Le `product.supplierinfo` créé depuis VSF utilise `prixVenteRPBM` comme prix d'achat RPBM ; `prixHT` est le prix public VSF et ne doit pas le remplacer. | 2026-07-24 | Métier RPBM | [L1.5 de la roadmap](roadmap.md#l15) |
| VD-02 | Précise VM-05 : l'Eurocode complet, la désignation, le stock et la référence constructeur de l'article VSF principal (`rpbm_eurocode`, `rpbm_vsf_designation`, `rpbm_vsf_stock`, `rpbm_constructor_reference`) ne sont plus écrits depuis l'opportunité, dont la fenêtre ne cherche plus d'article VSF et s'arrête à la base Eurocode ; seul le devis les désigne. Ils restent visibles et modifiables à la main dans le formulaire. | 2026-10-05 | Stanley SERIN (tient lieu de réponse du client, qui pourra l'infirmer) | [6 — Confirmation sur Piste/Opportunité](fonctionnel/workflow/06-confirmation-crm-lead.md#créer-un-devis-lot-e1) |
| VD-03 | Rattachement d'un article VSF à un produit Odoo : le code VSF (`rpbm_eurocode`) d'abord ; la référence interne et le nom exact, ce dernier seulement s'il est unique, ne servent que pour un produit sans eurocode ; un produit qui porte l'eurocode d'un autre article n'est jamais retenu. Remplace l'ordre « référence interne, eurocode, nom ». | 2026-10-05 | Stanley SERIN (tient lieu de réponse du client, qui pourra l'infirmer) | [9 — Création du produit](fonctionnel/workflow/09-creation-produit.md) |
| VD-04 | Nouveau champ « libellé de la pièce X'Glass » (`rpbm_xglass_piece_label`, « Pièce X'Glass sélectionnée ») : le widget l'écrit avec les identifiants de pièce, et le devis l'affiche dans l'encart « Dossier » quand il s'ouvre sans X'Glass (lot E2). Sans équivalent Studio ni migration. | 2026-10-06 | Stanley SERIN (tient lieu de réponse du client, qui pourra l'infirmer) | [champs de l'opportunité](technique/champs/crm-lead.md) |
| VD-05 | Le verrou de session ne protège plus que X'Glass : plusieurs vendeurs peuvent utiliser VSF en même temps (la trace T1 du 2026-10-06 montre que VSF accepte plusieurs sessions sur le même compte). Précise la contrainte d'un seul utilisateur à la fois, qui ne vaut que pour X'Glass. | 2026-10-06 | Stanley SERIN (tient lieu de réponse du client, qui pourra l'infirmer) | [Concurrence — verrou de session](technique/configuration.md#concurrence--verrou-de-session) |

## Références

- [Mapping calques X'Glass → Pièce concernée](../../docs/cartographie/calques-mapping.md)
- [Cascade de prix des pistes](../../docs/cartographie/prix-devis/champs-crm-lead.md)
- [Automatisations Studio](../../docs/cartographie/automatisations.md)
- [Roadmap L1 et L4](roadmap.md)
