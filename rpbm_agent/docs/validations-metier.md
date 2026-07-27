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
| VM-05 | L1.3 | À quel moment les champs Eurocode/VSF doivent-ils être alimentés : dès la Piste/Opportunité, ou seulement depuis le devis ? | Écrire dès qu'un article VSF est explicitement sélectionné ; la donnée est ensuite disponible sur le devis lié via les champs `related`. | Processus commercial et qualité de données. | Remplacé | L'article sélectionné est recherché/créé comme produit ; pas d'écriture CRM supplémentaire demandée. | 2026-07-27 / Métier RPBM |
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

## Références

- [Mapping calques X'Glass → Pièce concernée](../../docs/cartographie/calques-mapping.md)
- [Cascade de prix des pistes](../../docs/cartographie/prix-devis/champs-crm-lead.md)
- [Automatisations Studio](../../docs/cartographie/automatisations.md)
- [Roadmap L1 et L4](roadmap.md)
