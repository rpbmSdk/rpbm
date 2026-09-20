# Jeu de test — Assistant véhicule RPBM

Jeu de données destiné à rejouer les parcours du module `rpbm_agent` sur une
instance de test. Les valeurs marquées **observée** proviennent des scénarios
et fixtures déjà présents dans le dépôt. Les valeurs **synthétiques** ne
doivent être utilisées qu'avec un mock des portails ou avec des enregistrements
de test explicitement préparés.

## Données de référence

| Élément | Valeur | Statut | Usage |
|---|---|---|---|
| Plaque véhicule | `DS808DZ` | Observée | Recherche X'Glass nominale ; véhicule de test historique |
| Identifiant véhicule X'Glass | `397899` | Observée | Tests techniques de sélection véhicule |
| Base Eurocode | `6539R` | Observée | Recherche VSF nominale |
| Article VSF principal | `6539RGSH5RD` | Observée | Article avec stock et fiche détaillée |
| Article VSF principal alternatif | `6571AGRCHIMVZ` | Observée | Création/synchronisation produit |
| Suggestion VSF | `6571AGRCIMVZ` | Observée | Vérification des suggestions liées |
| Suggestion accessoire | `PP-COLLE310` | Observée | Article suggéré disponible ou indisponible |
| Plaque sans résultat | `ZZ-TEST-00` | Synthétique | Scénario de recherche vide ; nécessite un mock ou une donnée X'Glass dédiée |
| Base sans résultat | `ZZZZZ` | Synthétique | Scénario VSF vide ; nécessite un mock ou une donnée VSF dédiée |

Les valeurs observées ne garantissent pas que les portails externes les
retourneront encore dans le futur. Avant une recette live, contrôler la réponse
réelle de X'Glass et de VSF.

## Scénarios CRM / Opportunité

### CRM-01 — Parcours nominal complet

Préparer une opportunité de test avec la plaque `DS808DZ`, puis ouvrir le
widget et exécuter :

1. rechercher la plaque ;
2. sélectionner le véhicule `397899` ou le candidat correspondant ;
3. sélectionner le calque `PARE-BRISE` ;
4. sélectionner une pièce OE puis une pièce après-marché ;
5. vérifier ou saisir la base `6539R` ;
6. sélectionner l'article `6539RGSH5RD` ;
7. utiliser **Confirmer**, puis enregistrer le formulaire nativement.

Résultats attendus :

- le véhicule Fleet est créé ou retrouvé puis lié par `rpbm_vehicle_id` ;
- la catégorie X'Glass et la pièce concernée sont visibles ;
- la base Eurocode est `6539R` ;
- l'article sélectionné est mémorisé sans modifier de prix ;
- les champs VIN/date MEC/historiques sont complétés uniquement lorsqu'une
  valeur fiable est disponible ;
- aucune erreur `RPC_ERROR` et aucune écriture tarifaire inattendue.

### CRM-02 — Confirmation avec sauvegarde immédiate

Reprendre CRM-01 sur une nouvelle opportunité et utiliser **Confirmer et
enregistrer**.

Résultats attendus : les mêmes valeurs sont envoyées que dans CRM-01, mais
elles sont persistées immédiatement. Une validation Odoo standard doit rester
active si un autre champ requis manque.

### CRM-03 — Réouverture et restauration des sélections

Sur une opportunité ayant déjà les valeurs de CRM-01, fermer puis rouvrir le
widget.

Résultats attendus :

- `DS808DZ` est préremplie ;
- le véhicule et la catégorie sont restaurés ;
- la pièce OE et la pièce après-marché sont restaurées si leurs identifiants
  sont encore présents ;
- `6539R` reste restaurée même sans article VSF sélectionné ;
- les résultats VSF peuvent être relancés sans repartir d'un état incohérent.

### CRM-04 — Recherche vide et saisie manuelle

Avec la plaque synthétique `ZZ-TEST-00`, vérifier le comportement d'une
recherche sans résultat. Puis utiliser une plaque de test retournant au moins
un véhicule et saisir manuellement `6539R` sans sélectionner de pièce AM.

Résultats attendus : la recherche vide affiche une information exploitable,
ne crée aucun véhicule et ne lève pas d'exception non gérée. La base saisie
manuellement permet néanmoins de rechercher les articles VSF.

## Scénarios devis

### SO-01 — Devis avec opportunité

Créer un devis lié à une opportunité de test issue de CRM-01. Rejouer la
recherche `DS808DZ`, sélectionner `PARE-BRISE`, puis l'article
`6539RGSH5RD`.

Résultats attendus :

- les champs `related` du devis reflètent l'opportunité ;
- aucune seconde source indépendante n'est créée sur `sale.order` ;
- l'article peut être recherché/créé puis ajouté comme ligne de devis ;
- deux articles distincts peuvent être ajoutés sans supprimer les lignes
  préexistantes ;
- `carrier_id` reste à renseigner ou est prérempli uniquement si le lieu CRM
  fournit une correspondance déterministe.

### SO-02 — Devis sans opportunité

Créer un devis de test sans `opportunity_id`.

Résultat attendu : la page de l'assistant véhicule est masquée et aucune
écriture X'Glass, Fleet ou Eurocode n'est tentée.

### SO-03 — Création produit et doublon

Sur un devis avec opportunité, tester successivement :

- `6571AGRCHIMVZ`, absent du catalogue produit de test ;
- le même article une seconde fois ;
- la suggestion `PP-COLLE310`.

Résultats attendus :

- le premier clic crée un seul produit et sa ligne fournisseur ;
- le second clic retrouve le produit sans doublon ;
- la suggestion dispose des mêmes actions que l'article principal ;
- le retrait ne supprime qu'une ligne créée par le widget pendant la dialog.

### SO-04 — Opérations de main-d'œuvre X'Glass

Sur un devis de test avec opportunité, sélectionner une pièce qui renvoie des
opérations T1, T2 ou T3, cocher plusieurs opérations puis les ajouter.

Résultats attendus :

- une ligne de service par opération, avec quantité égale à la durée X'Glass ;
- le produit et ses taxes viennent du tarif Odoo T1/T2/T3, sans calcul Studio ;
- le rechargement du devis ne crée aucun doublon et permet de retirer seulement
  la ligne portant la provenance de l'opération ;
- une opération sans durée, identifiant ou taux reconnu reste indisponible ;
- les lignes manuelles, le champ Studio agrégé et le produit « Pose à Domicile »
  restent inchangés.

## Scénarios de robustesse

| ID | Précondition | Action | Résultat attendu |
|---|---|---|---|
| ROB-01 | Deux véhicules candidats | Changer rapidement de véhicule | Une seule planche et une seule métadonnée correspondent au véhicule finalement sélectionné |
| ROB-02 | Session X'Glass expirée | Déclencher une recherche ou une sélection | Reconnexion proposée, contexte conservé, action rejouée au plus une fois |
| ROB-03 | VIN Fleet déjà renseigné | Confirmer avec une valeur X'Glass différente | Le VIN Fleet valide n'est pas écrasé |
| ROB-04 | VIN Fleet de forme `var = <VIN>;` | Confirmer avec une valeur X'Glass valide | Le VIN malformé est nettoyé et remplacé par le VIN valide |
| ROB-05 | Article sans image ou stock | Sélectionner l'article | La carte reste utilisable, sans erreur JavaScript |
| ROB-06 | Catégorie non couverte | Sélectionner un calque comme `PHARE` ou `ESSUIE-GLACE AV` | `Autre...` est suggéré, reste modifiable et le libellé X'Glass exact est conservé |

## Preuve à consigner

Pour chaque scénario, noter séparément :

- l'instance, la base et le commit testé ;
- l'identifiant de l'opportunité/devis de test ;
- les appels réseau principaux et leur résultat ;
- les valeurs visibles avant et après sauvegarde ;
- la relecture après rechargement complet ;
- les erreurs de console ou serveur ;
- le verdict `PASS`, `FAIL` ou `BLOCKED` et sa justification.

Ne pas utiliser de données client réelles dans ce jeu de test et ne pas
consigner de secrets de portail.
