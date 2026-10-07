# 4 — Pièce et pièce après-marché (déduction eurocode)

- **Déclencheur** : clic utilisateur sur une pièce de la catégorie, ou clic sur une ligne d'un encart « Autres marques AM » (sans pièce sélectionnée, voir [plus bas](#autres-marques-am-par-famille-encart-xglass-autre-am-r11-et-r19)).
- **Code** : `onSelectPiece()` → `getSelectedPieceAm()`/`getPieceAm()` (`agent_widget_dialog.js`).
- **Route** : `POST /getPieceAm` (`main.py::getPieceAm`) → pièces après-marché correspondantes sur X'Glass.
- **Déduction eurocode** : un clic sur une pièce après-marché (`onSelectPieceAM()`), carte « Équivalence AM » ou ligne « Autres marques AM » d'une famille quelconque, renseigne `state.baseEurocode` (état widget, pas encore un champ Odoo) avec les 5 premiers caractères de sa référence. Le changement de base relance la recherche VSF sur le devis ; sur l'opportunité (lot E1), le dialog s'arrête à la base. Sans pièce après-marché, le champ reste à saisir à la main.
- **Affichage d'une pièce après-marché** : libellé, fournisseur, référence, validité (« A partir de », « Jusqu'à » ou « De … à … », comme X'Glass) et description. La description reprend la remarque de X'Glass (ex. « 5Ptes ») devant la description, sauf si elle vaut « - ». Le prix n'est affiché que s'il est connu.

Aucun champ Odoo lu ou écrit à cette étape — uniquement de l'état widget local, qui alimentera l'écriture à la confirmation ([6](06-confirmation-crm-lead.md)/[7](07-confirmation-sale-order.md)).

La confirmation mémorise `piece.id`, `piece.pieceOe.id` et l'identifiant de la
pièce après-marché sélectionnée. Depuis le lot E1.1, pour une pièce déjà mémorisée à l'ouverture, ces identifiants ne sont réécrits
que si la sélection a été retrouvée à la restauration, ou remplacée ou retirée par une action
explicite (clic sur une pièce ou une pièce après-marché, sur une **autre** catégorie ou un **autre**
véhicule, recherche d'immatriculation **réussie**) ; sinon la valeur mémorisée est conservée, y compris
une pièce introuvable ou encore en cours de chargement. La liste des actions est en
[6](06-confirmation-crm-lead.md#pièce-mémorisée-lot-e11). À la réouverture, la pièce mémorisée est affichée
seule ; « Afficher les autres » réaffiche toutes les pièces. La base Eurocode enregistrée
est restaurée telle quelle, y compris lorsqu'elle a été saisie à la main ; la pièce
après-marché restaurée ne la remplace pas (R12, 2026-10-02). Une pièce choisie dans « Autres
marques AM » est mémorisée de la même façon ; à la réouverture, elle n'est pas
re-sélectionnée (la restauration ne cherche que dans « Équivalence AM »), mais la base
enregistrée reste affichée et son identifiant reste conservé tant qu'aucune action explicite ne
remplace ou ne retire la sélection (lot E1.1). Un second clic sur la pièce sélectionnée annule la sélection et
efface la base Eurocode ainsi que la recherche VSF.

Une ligne « Autres marques AM » choisie **sans pièce sélectionnée** est mémorisée à la
confirmation avec la base Eurocode ; les identifiants de pièce X'Glass et de pièce OE ne sont pas
écrits : vides pour un dossier neuf, inchangés sinon (lot E1.1). À la réouverture, la
section VSF (« 5. Article VSF » sur le devis, « 4. Base Eurocode » sur l'opportunité) et les
encarts de toutes les familles sont affichés sans cartes de pièces (contexte restauré), la base
enregistrée reste affichée et aucune recherche automatique ne démarre. Sur le devis, depuis le lot E2,
la recherche VSF part dès l'ouverture sur la base enregistrée, sans X'Glass ; les encarts de familles
n'apparaissent qu'après « Charger X'Glass ».

## Autres marques AM par famille (encart X'Glass AUTRE AM, R11 et R19)

À la fin de **chaque famille** X'Glass affichée (voir [3 — groupes et familles](03-categorie-xglass.md#pièces-de-la-catégorie-groupes-et-familles-r20-lot-d-build-a)),
l'encart « Autres marques AM » est toujours présent, replié par défaut, **même sans pièce
sélectionnée** (lot D, build A, décision du 2026-10-05 ; avant, il n'apparaissait que sous la
pièce sélectionnée). Il reprend l'encart « AUTRE AM » de X'Glass, rattaché à la famille
(élément X'Glass, ex. PARE-BRISE) et non à la pièce : il donne des références après-marché
même quand « Équivalence AM » est vide. « Équivalence AM » reste sous la pièce sélectionnée.

- **Déclencheur** : dépliage de l'encart d'une famille (`onToggleAutresAm()` → `loadAutresAm()`).
  Chaque famille a son propre état ouvert ou replié ; en ouvrir une ne déplie pas les autres.
- **Route** : `POST /getPieceAm` sans `pieceId` : X'Glass est interrogé par `idElementSit`.
  Aucun appel à l'ouverture du widget : une famille jamais dépliée ne coûte aucune requête.
- **Cache** : la liste est gardée par véhicule et famille pendant la vie de la dialog. Replier,
  déplier ou changer de pièce dans la même famille ne relance pas d'appel ; sélectionner ou
  désélectionner une pièce ne change plus l'état ouvert d'un encart. En cas d'erreur, rien
  n'est gardé (l'encart reste ouvert et vide, avec la notification d'erreur) : replier puis
  déplier relance l'appel. Une reconnexion aux portails vide le
  cache et replie les encarts ; ils se rechargent au prochain dépliage.
- **Contenu** : toutes les lignes renvoyées par X'Glass, dans son ordre, doublons de fournisseurs
  compris. Une famille sans entrée affiche « Aucune autre référence après-marché. ».
- **Présentation** : une ligne compacte par référence, comme X'Glass : fournisseur au-dessus de
  la référence à gauche ; libellé, « Validité : … » et « Description : … » à droite ; prix en
  bout de ligne seulement s'il est connu. Un séparateur sépare les lignes. Les cartes
  « Équivalence AM » restent des cartes sur deux colonnes.
- **Clic sur une ligne, dans toute famille** : même effet qu'une carte « Équivalence AM »
  (sélection, base Eurocode = 5 premiers caractères de la référence, recherche VSF sur le devis),
  **avec ou sans pièce sélectionnée**. Sans pièce, la section VSF apparaît dès ce clic (voir
  ci-dessous). Vérifier qu'une seule base Eurocode ressort de la liste reste à la charge
  de l'utilisateur.

**Risque assumé (décision du 2026-10-05).** Le clic remplit toujours la base, quelle que soit
la famille. Pour les familles complémentaires (cale, joint, nécessaire de collage,
rétroviseur), la référence AM n'est pas forcément un eurocode de vitrage : la base déduite peut
être peu pertinente pour la recherche VSF. Hypothèse, non vérifiée (non observée à la recette
du 2026-10-05 : les familles complémentaires testées ne renvoient aucune ligne). À confirmer sur
des lignes réelles ; le comportement sera reconsidéré si elles donnent une base trompeuse.

### Section « Article VSF » sans pièce sélectionnée

La section VSF est visible dès qu'une pièce, une pièce après-marché ou un contexte restauré
existe. Sur le devis, c'est « 5. Article VSF » (étape [5](05-recherche-vsf-eurocode.md)) : cliquer
sur une ligne « Autres marques AM » sans avoir choisi de pièce renseigne la base et lance la
recherche VSF. Au lot D, une base restaurée seule ne lançait **aucune** recherche (R12 : la
recherche automatique exigeait une pièce ou une pièce AM sélectionnée) ; **depuis le lot E2, sur le
devis, la recherche part dès qu'il y a une base**, y compris au montage et sans X'Glass (voir
[7](07-confirmation-sale-order.md#devis-sans-xglass-lot-e2)). Sur l'opportunité (lot E1),
la section se réduit à « 4. Base Eurocode » : le champ base et le lien « Ouvrir dans un nouvel
onglet », sans tableau, sans bouton « Rechercher sur VSF » et sans recherche automatique ; le clic
sur une ligne renseigne la base, rien de plus.

- Sur un devis, la section « 4. Main d'œuvre » suit la pièce sélectionnée ou, tant que X'Glass n'est
  pas chargé, la main-d'œuvre enregistrée de la pièce mémorisée (correctif du 2026-10-07, voir
  [7](07-confirmation-sale-order.md#main-dœuvre-enregistrée-correctif-du-2026-10-07)) : sans pièce
  sélectionnée ni main-d'œuvre enregistrée, seule « 5. Article VSF » s'affiche, comme pour une base
  restaurée seule.
- Cas limite : lorsque « Afficher les autres » est actif, une ligne d'une autre famille que celle
  de la pièce sélectionnée remplace la pièce après-marché et la base, la pièce OE restant
  sélectionnée. À la confirmation, la pièce après-marché mémorisée peut donc venir d'une
  autre famille que la pièce OE ; aucun contrôle n'est prévu (question ouverte, voir le
  document de travail local (non suivi, lot D du 2026-10-05)).
- Après un clic AM sans pièce, sélectionner une pièce réinitialise les données dépendantes de la
  sélection précédente, base Eurocode comprise (comportement de `clearSelectedPiece()`, inchangé).
- Cas limite du lot E1, **levé par le lot E2** : une opportunité sans pièce OE, avec seulement une
  ligne « Autres marques AM » et une base, ouvrait le devis (« Créer un devis », voir
  [6](06-confirmation-crm-lead.md)) sans recherche VSF automatique, faute de pièce ou de pièce AM
  sélectionnée (R12) ; la recherche part maintenant à l'ouverture.

Lot D, build A (`17.0.261005.1`) : recette réussie le 2026-10-05 sur le build `ab31793`.

Suivant : [5 — Recherche VSF par eurocode](05-recherche-vsf-eurocode.md).
