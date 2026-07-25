# Mapping calques X'Glass → « Pièce concernée »

Prérequis de [L1.2.b](../../rpbm_agent/docs/roadmap.md#l12) : le widget doit renseigner
`x_studio_field_eENQz` « Pièce concernée » (sélection à 4 valeurs, remplie sur 9 980 pistes,
**pilote le forfait de pose** dans la cascade de prix — cf.
[prix-devis](prix-devis/README.md)). Or il ne connaît que le **libellé du calque X'Glass**
cliqué, qui est bien plus granulaire.

## Constat sur données réelles (L0.1, HYUNDAI I20)

Une planche X'Glass réelle remonte ~25 calques. Relevé en live sur le véhicule de test
(HYUNDAI I20 I PHASE 2), tous les calques disponibles :

```
PARE-BRISE · JT/ENJOLIVEUR PARE-BRISE · GLACE AR · GLACE PORTE AV · GLACE PORTE AR ·
GLACE FIXE PORTE AR · GLACE RETROVISEUR · RETROVISEUR EXT · RETROVISEUR INTERIEUR ·
FEU AR · FEU STOP SUPPLEMENTAIRE · FEU REPETITEUR LATERAL · PHARE · PHARE AB/LP ·
ESSUIE-GLACE AV · ESSUIE-GLACE AR · MECANISME ESSUIE-GLACE · MECANISME ESSUIE-GLACE AR ·
LEVE-GLACE PORTE AV · LEVE-GLACE PORTE AR · TOIT OUVRANT · ECLAIREUR PLAQUE POLICE ·
NECESSAIRE MONTAGE · JT/LECHEUR PORTE AV · JT/LECHEUR PORTE AR
```

Les 4 valeurs cibles de `x_studio_field_eENQz` : `Pare-Brise` / `Lunette arrière` /
`Glace Latérale` / `Autre...`.

**La grande majorité des calques ne correspond à aucune des 4 valeurs** (feux, phares,
rétroviseurs, essuie-glaces, mécanismes, lève-glaces, toit ouvrant, éclaireurs, joints…).
C'est probablement la raison d'être historique du champ texte libre `x_studio_categorie_xglass` :
accepter n'importe quel libellé sans trancher ce mapping.

## Proposition de correspondance (à valider avec le métier)

Table **indicative**, à confirmer/compléter en atelier avant implémentation. Le widget doit
**suggérer** la valeur (pré-remplie, modifiable, jamais écrite en silence — cf. L1.2.b), car
une correspondance automatique fausse fausse le prix.

| Libellé calque X'Glass | → « Pièce concernée » proposée | Confiance |
|---|---|---|
| `PARE-BRISE` | Pare-Brise | haute |
| `GLACE AR` | Lunette arrière | **à valider** (« glace arrière » = lunette ?) |
| `GLACE PORTE AV`, `GLACE PORTE AR`, `GLACE FIXE PORTE AR` | Glace Latérale | moyenne |
| Tous les autres (feux, phares, rétroviseurs, essuie-glaces, mécanismes, lève-glaces, toit ouvrant, éclaireurs, joints/lécheurs, nécessaire montage…) | Autre... | par défaut |

**Questions ouvertes pour le métier :**
1. `GLACE AR` correspond-il à « Lunette arrière » ou à une glace latérale arrière ?
2. Faut-il distinguer une valeur « indéterminé / à saisir » de `Autre...`, ou `Autre...`
   suffit-il comme fourre-tout ?
3. Les glaces de custode / glaces fixes relèvent-elles de « Glace Latérale » ou « Autre... » ?
4. La liste des calques ci-dessus est celle d'**un** véhicule — d'autres modèles peuvent
   exposer des libellés non vus ici. Le défaut `Autre...` doit couvrir tout libellé inconnu
   (ne jamais laisser le champ vide).

> Cette table n'est pas figée : elle doit être élargie au fil des libellés rencontrés
> (`/getPlanche` sur des véhicules de types variés) avant d'être codée dans `utils.js`.
