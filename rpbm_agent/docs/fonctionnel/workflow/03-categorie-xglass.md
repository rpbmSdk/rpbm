# 3 — Catégorie X'Glass (calque)

- **Déclencheur** : clic utilisateur sur une catégorie, OU auto-sélection si le champ `categorieXglass` est déjà renseigné sur l'enregistrement au chargement de la planche (`useEffect` sur `planche`, `agent_widget_dialog.js`).
- **Code** : `onClickCalque()` (`agent_widget_dialog.js`).
- **Route** : `POST /getPieces` (`main.py::getPieces`) → liste des pièces de la catégorie.

| Champ | Modèle | Sens | Détail |
|---|---|---|---|
| `rpbm_xglass_category` | `crm.lead` / `sale.order` | **lecture** | Comparé aux `libelle` des calques chargés ; si une correspondance est trouvée, la catégorie est présélectionnée automatiquement (seule lecture de champ Odoo de toute la chaîne réactive du widget, en dehors de l'ouverture de la fenêtre) |

Aucune écriture à cette étape — la valeur n'est écrite qu'à la confirmation (voir [6](06-confirmation-crm-lead.md)/[7](07-confirmation-sale-order.md)). Détail du champ : [technique/champs/crm-lead.md](../../technique/champs/crm-lead.md) / [sale-order.md](../../technique/champs/sale-order.md).

À la réouverture, une catégorie enregistrée est affichée seule. Le bouton
« Afficher les autres » permet de revenir à la liste complète et de modifier le choix.

## Pièces de la catégorie, groupes et familles (R20, lot D build A)

Les pièces de la catégorie choisie ne sont plus aplaties dans une seule grille : elles sont
présentées comme sur le portail X'Glass, en **groupes** puis en **familles**.

| Mot | Sens | Exemple (X-Trail IV, catégorie PARE-BRISE) |
|---|---|---|
| Catégorie | Calque X'Glass, étape 2 du widget (cette page) | PARE-BRISE |
| Groupe | « Pièces principales » ou « Pièces complémentaires » | Pièces complémentaires |
| Famille | Élément X'Glass (`elementSitId`) : un lot de pièces de même nature, avec son libellé X'Glass | une famille principale + quatre complémentaires |
| Pièce | Carte de pièce OE, inchangée | `G27006RA0E` |

Le mot « catégorie » du client pour l'encart « Autres marques AM » désigne la **famille**
(décision du 2026-10-05, voir document de travail local (non suivi, lot D du 2026-10-05)).
Dans le widget, « Catégorie » reste le calque ; les bandeaux de famille portent seulement le
libellé X'Glass de la famille.

- **Ordre** : celui du portail, sans tri. Les groupes principaux précèdent les complémentaires ;
  à l'intérieur d'un groupe, familles et pièces suivent l'ordre reçu.
- **Structure affichée** : titre de groupe, bandeau de famille, cartes de la famille, puis
  l'encart « Autres marques AM » de la famille, replié (voir [4 — Pièce et pièce après-marché](04-piece-piece-am.md#autres-marques-am-par-famille-encart-xglass-autre-am-r11-et-r19)).
- **Cas observé** (véhicule X'Glass 471612 ; famille principale tracée le 2026-10-01, familles
  complémentaires relevées lors de l'exploration du 2026-10-05) : la famille principale
  (`elementSitId` 3464) porte quatre pièces OE (`RA0E`, `RA1E`, `RA3E`, `RA2E`) ; quatre
  familles complémentaires portent six pièces (cales inférieure et supérieure, joint, nécessaire
  de collage, rétroviseur ×2). L'affichage est donc 4 puis 6 cartes, soit 10, dans l'ordre du
  portail, et cinq encarts : présentation confirmée à la recette du 2026-10-05 sur le build
  `ab31793`.
- **Familles déduites des pièces** : une famille sans pièce reçue n'est pas affichée. Une pièce dont
  le groupe est inconnu est rangée dans un groupe générique « Pièces ».
- **Pièce sélectionnée** : seule sa famille reste affichée (avec le titre de son groupe) ; « Afficher les autres » rétablit
  les groupes et familles. Réouverture avec un contexte restauré sans pièce retrouvée (par
  exemple une base Eurocode saisie seule) : toutes les familles sont affichées avec leurs
  encarts, sans cartes, jusqu'à « Afficher les autres ».
- **Libellé de famille** : `/getPieces` ajoute `elementSitLibelle` à chaque pièce (clé
  supplémentaire, rien n'est retiré de la réponse). Détail technique :
  [frontend](../../technique/frontend.md#groupes-de-pièces-et-encarts-autre-am-par-famille-r19-r20) et
  [backend](../../technique/backend.md#getpieces-et-getpieceam-lot-d-build-a).
- **Autres groupes du portail** : le portail connaît d'autres groupes (hors calque, recherche
  par référence). Le widget n'affiche toujours que les principaux et les complémentaires ;
  le serveur journalise désormais les autres clés reçues pour décider plus tard s'il faut les
  afficher. Leur existence dans les réponses réelles n'est pas vérifiée (hypothèse tirée des
  libellés du portail).

Aucun champ Odoo n'est lu ni écrit pour ce regroupement : le groupe et la famille ne sont pas
mémorisés (décision par défaut, à rouvrir si le client le demande).

Lot D, build A (`17.0.261005.1`) : recette réussie le 2026-10-05 sur le build `ab31793`.

Suivant : [4 — Pièce et pièce après-marché](04-piece-piece-am.md).
