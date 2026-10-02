# 4 — Pièce et pièce après-marché (déduction eurocode)

- **Déclencheur** : clic utilisateur sur une pièce de la catégorie.
- **Code** : `onSelectPiece()` → `getSelectedPieceAm()`/`getPieceAm()` (`agent_widget_dialog.js`).
- **Route** : `POST /getPieceAm` (`main.py::getPieceAm`) → pièces après-marché correspondantes sur X'Glass.
- **Déduction eurocode** : un clic sur une pièce après-marché (`onSelectPieceAM()`), carte « Équivalence AM » ou ligne « Autres marques AM », renseigne `state.baseEurocode` (état widget, pas encore un champ Odoo) avec les 5 premiers caractères de sa référence. Le changement de base relance la recherche VSF. Sans pièce après-marché, le champ reste à saisir à la main.
- **Affichage d'une pièce après-marché** : libellé, fournisseur, référence, validité (« A partir de », « Jusqu'à » ou « De … à … », comme X'Glass) et description. La description reprend la remarque de X'Glass (ex. « 5Ptes ») devant la description, sauf si elle vaut « - ». Le prix n'est affiché que s'il est connu.

Aucun champ Odoo lu ou écrit à cette étape — uniquement de l'état widget local, qui alimentera l'écriture à la confirmation ([6](06-confirmation-crm-lead.md)/[7](07-confirmation-sale-order.md)).

La confirmation mémorise `piece.id`, `piece.pieceOe.id` et l'identifiant de la
pièce après-marché sélectionnée. À la réouverture, la pièce mémorisée est affichée
seule ; « Afficher les autres » réaffiche toutes les pièces. La base Eurocode enregistrée
est restaurée telle quelle, y compris lorsqu'elle a été saisie à la main ; la pièce
après-marché restaurée ne la remplace pas (R12, 2026-10-02). Une pièce choisie dans « Autres
marques AM » est mémorisée de la même façon ; à la réouverture, elle n'est pas
re-sélectionnée (la restauration ne cherche que dans « Équivalence AM »), mais la base
enregistrée reste affichée. Un second clic sur la pièce sélectionnée annule la sélection et
efface la base Eurocode ainsi que la recherche VSF.

## Autres marques AM (encart X'Glass « AUTRE AM », R11)

Sous la pièce sélectionnée, l'encart « Autres marques AM » est toujours présent, replié par
défaut. Il reprend l'encart « AUTRE AM » de X'Glass, rattaché à la famille de la pièce
(élément X'Glass, ex. PARE-BRISE) et non à la pièce : il donne des références après-marché
même quand « Équivalence AM » est vide.

- **Déclencheur** : dépliage de l'encart (`onToggleAutresAm()` → `loadAutresAm()`).
- **Route** : `POST /getPieceAm` sans `pieceId` : X'Glass est interrogé par `idElementSit`.
- **Cache** : la liste est gardée par véhicule et famille pendant la vie de la dialog. Replier,
  déplier ou changer de pièce dans la même famille ne relance pas d'appel. En cas d'erreur, rien
  n'est gardé : replier puis déplier relance l'appel. Une reconnexion aux portails vide le
  cache.
- **Contenu** : toutes les lignes renvoyées par X'Glass, dans son ordre, doublons de fournisseurs
  compris. Une famille sans entrée affiche « Aucune autre référence après-marché. ».
- **Présentation** : une ligne compacte par référence, comme X'Glass : fournisseur au-dessus de
  la référence à gauche ; libellé, « Validité : … » et « Description : … » à droite ; prix en
  bout de ligne seulement s'il est connu. Un séparateur sépare les lignes. Les cartes
  « Équivalence AM » restent des cartes sur deux colonnes.
- **Clic sur une ligne** : même effet qu'une carte « Équivalence AM » (sélection, base Eurocode,
  recherche VSF). Vérifier qu'une seule base Eurocode ressort de la liste reste à la charge de
  l'utilisateur.

Suivant : [5 — Recherche VSF par eurocode](05-recherche-vsf-eurocode.md).
