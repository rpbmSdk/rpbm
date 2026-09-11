"""Génère le guide client PDF et son texte Markdown, sans aucun accès Odoo.

Exécution depuis la racine : python Jobs/rpbm_agent_stock/documentation/generer_guide.py
Dépendances : reportlab, Pillow. Les captures sont conservées sans retouche.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import re
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

HERE=Path(__file__).resolve().parent
OUT=HERE/'Guide_client_RPBM_logistique_et_assistant.pdf'
FONT=Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Guide',str(FONT/'arial.ttf')))
pdfmetrics.registerFont(TTFont('Guide-Bold',str(FONT/'arialbd.ttf')))
pdfmetrics.registerFont(TTFont('Guide-Italic',str(FONT/'ariali.ttf')))
pdfmetrics.registerFontFamily('Guide',normal='Guide',bold='Guide-Bold',italic='Guide-Italic')
NAVY=colors.HexColor('#163747'); TEAL=colors.HexColor('#007E87'); INK=colors.HexColor('#233944')
MUTED=colors.HexColor('#5E737D'); PALE=colors.HexColor('#EDF5F5'); GOLD=colors.HexColor('#D69A32')
W,H=595.276,841.89
BODY_W=W-84
styles={
 'body':ParagraphStyle('body',fontName='Guide',fontSize=10.4,leading=15.2,textColor=INK,spaceAfter=9),
 'lead':ParagraphStyle('lead',fontName='Guide',fontSize=12,leading=17,textColor=MUTED,spaceAfter=17),
 'title':ParagraphStyle('title',fontName='Guide-Bold',fontSize=24,leading=28,textColor=NAVY,spaceAfter=13),
 'h2':ParagraphStyle('h2',fontName='Guide-Bold',fontSize=13.5,leading=18,textColor=TEAL,spaceBefore=10,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Guide',fontSize=8.2,leading=11.2,textColor=MUTED,spaceAfter=8),
 'cell':ParagraphStyle('cell',fontName='Guide',fontSize=9.3,leading=13,textColor=INK),
 'th':ParagraphStyle('th',fontName='Guide-Bold',fontSize=9.2,leading=13,textColor=colors.white),
 'cover':ParagraphStyle('cover',fontName='Guide-Bold',fontSize=34,leading=39,textColor=NAVY,spaceAfter=20),
}
story=[]; md=[]; section=0

def rich(s):
    s=escape(s)
    return re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s).replace('\n','<br/>')
def para(s,style='body'):
    return Paragraph(rich(s),styles[style])
def P(s,style='body'):
    story.append(para(s,style));md.extend([('# ' if style in ['title','cover'] else '')+s,''])
def H2(s):
    story.append(para(s,'h2'));md.extend(['## '+s,''])
def Page(title,lead):
    global section
    if story: story.append(PageBreak())
    section+=1
    P(f'{section:02d}  /  RPBM - GUIDE CLIENT','small')
    P(title,'title');P(lead,'lead')
    md.extend(['---',''])
def Bullet(s):
    story.append(Paragraph('•  '+rich(s),styles['body']));md.extend(['- '+s,''])
def Box(title,s,warning=False):
    t=Table([[para(title,'h2')],[para(s)]],colWidths=[BODY_W-22])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#FFF5E1') if warning else PALE),('BOX',(0,0),(-1,-1),.6,GOLD if warning else TEAL),('LEFTPADDING',(0,0),(-1,-1),11),('RIGHTPADDING',(0,0),(-1,-1),11),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.extend([t,Spacer(1,12)]);md.extend(['> **'+title+'**  ', '> '+s,''])
def T(headers,rows,widths):
    cells=[[para(x,'th') for x in headers]]+[[para(str(x),'cell') for x in row] for row in rows]
    table=Table(cells,colWidths=[BODY_W*x for x in widths],hAlign='LEFT',repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,-1),(-1,-1),.5,TEAL)]))
    story.extend([table,Spacer(1,12)])
    md.extend(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |'])
    md.extend('| '+' | '.join(str(x).replace('\n','<br>') for x in row)+' |' for row in rows);md.append('')

class Diagram(Flowable):
    def __init__(self,labels,caption=''):
        Flowable.__init__(self);self.labels=labels;self.width=BODY_W;self.height=90;self.caption=caption
    def draw(self):
        c=self.canv;n=len(self.labels);gap=18;bw=(BODY_W-(n-1)*gap)/n
        for i,label in enumerate(self.labels):
            x=i*(bw+gap);c.setFillColor(PALE);c.setStrokeColor(TEAL);c.roundRect(x,30,bw,53,7,stroke=1,fill=1)
            p=para(label,'cell');_,ph=p.wrap(bw-14,60);p.drawOn(c,x+7,30+(53-ph)/2)
            if i<n-1:
                c.setStrokeColor(TEAL);c.setFillColor(TEAL);c.line(x+bw+3,56,x+bw+gap-3,56)
                path=c.beginPath();path.moveTo(x+bw+gap-3,56);path.lineTo(x+bw+gap-8,59);path.lineTo(x+bw+gap-8,53);path.close();c.drawPath(path,fill=1,stroke=0)
        if self.caption:
            p=para(self.caption,'small');p.wrap(BODY_W,30);p.drawOn(c,0,7)
def Flow(labels,caption=''):
    story.append(Diagram(labels,caption));md.extend([' → '.join(labels),caption,''])

class SiteMap(Flowable):
    def __init__(self):
        Flowable.__init__(self);self.width=BODY_W;self.height=253
    def draw(self):
        c=self.canv
        c.setFillColor(PALE);c.setStrokeColor(TEAL);c.roundRect(0,73,BODY_W,170,9,fill=1,stroke=1)
        c.setFillColor(NAVY);c.setFont('Guide-Bold',12);c.drawString(15,222,'RPBM / Stock : les réserves des sites fixes')
        for x,y,w,title,desc in [(15,101,222,'Dépôts','Dépôt 1 + ses racks\nDépôt 2 + ses racks'),(254,154,241,'Galleria','Stock du comptoir Galleria'),(254,89,241,'Genipa','Stock du comptoir Genipa')]:
            c.setFillColor(colors.white);c.setStrokeColor(colors.HexColor('#B5D5D6'));c.roundRect(x,y,w,55 if title!='Dépôts' else 108,6,fill=1,stroke=1)
            p=para('**'+title+'**\n'+desc,'cell');_,ph=p.wrap(w-22,100);p.drawOn(c,x+11,y+(55 if title!='Dépôts' else 108)-ph-10)
        for x,w,title,desc in [(0,246,'RPBM / Camion','Pièces chargées pour les interventions'),(264,247,'RPBM / A controler','Pièces à examiner, hors circuit normal')]:
            c.setFillColor(colors.HexColor('#FFF5E1'));c.setStrokeColor(GOLD);c.roundRect(x,6,w,54,6,fill=1,stroke=1)
            p=para('**'+title+'**\n'+desc,'cell');_,ph=p.wrap(w-20,52);p.drawOn(c,x+10,54-ph)

class Screenshot(Flowable):
    def __init__(self,name,crop,height):
        Flowable.__init__(self);self.path=HERE/'captures'/name;self.crop=crop;self.width=BODY_W;self.height=height
    def draw(self):
        c=self.canv;img=ImageReader(str(self.path));iw,ih=img.getSize();x,y,w,h=self.crop or (0,0,iw,ih)
        scale=min(BODY_W/w,self.height/h);dw=w*scale;dh=h*scale
        c.saveState();p=c.beginPath();p.rect(0,self.height-dh,dw,dh);c.clipPath(p,stroke=0)
        c.drawImage(img,-x*scale,self.height-(ih-y)*scale,width=iw*scale,height=ih*scale)
        c.restoreState();c.setStrokeColor(colors.HexColor('#CAD8DD'));c.rect(0,self.height-dh,dw,dh,stroke=1,fill=0)
def Shot(name,crop,height,caption):
    if (HERE/'captures'/name).exists(): story.extend([Screenshot(name,crop,height),Spacer(1,6)]);P(caption,'small');md.extend([f'![{caption}](captures/{name})',''])

# Couverture
P('RPBM  /  PROJET ODOO','small');story.append(Spacer(1,42))
P('Une pièce,\nun parcours clair.','cover')
P('Nouvelle organisation logistique\net assistant véhicule & pièces','lead')
story.append(Spacer(1,17))
Flow(['Identifier la pièce','Choisir le lieu de remise','Préparer et livrer'])
story.append(Spacer(1,15))
P('Document de validation et guide d’utilisation','h2')
P('Ce guide explique comment le module **rpbm_agent** aide à préparer un devis, et comment Odoo organise ensuite les achats, les déplacements de pièces et la remise au client.')
Box('Le geste indispensable du vendeur','Choisir le **transporteur / mode de remise** sur chaque vente : Galleria, Genipa ou Camion. Ce choix détermine le parcours logistique.')
P('Édition du 11 septembre 2026 · Préproduction RPBM','small')
P('Organisation déployée pour essais. La validation du client et les essais restant à réaliser sont regroupés en fin de document. Ce guide ne vaut pas autorisation de démarrage en production.','small')
T(['Pour décider','Pour travailler'],[['Organisation et circuits : pages 2 à 7','Assistant véhicule : pages 9 à 12'],['Reprise du stock : page 8','Résultats et validation : pages 13 et 14']],[.5,.5])

Page('Ce que le projet change','Une même chaîne relie la recherche de la pièce, la vente et le mouvement physique.')
T(['Jusqu’ici, selon la procédure existante','Avec l’organisation proposée'],[
 ['Ventes dans Odoo ; entrées et sorties principalement suivies dans des tableaux.','Un article et ses mouvements sont suivis dans Odoo, avec un emplacement d’origine et une destination.'],
 ['Les couleurs du tableau signalent vendu, réservé ou cassé.','Une réservation, une livraison ou une mise au rebut matérialise chaque situation.'],
 ['Le rapprochement entre ventes et sorties demande un contrôle régulier.','Les documents liés à la vente rendent visible ce qui reste à acheter, transférer ou remettre.']],[.48,.52])
H2('Deux briques qui se complètent')
P('**L’assistant véhicule** recherche un véhicule et les pièces correspondantes dans X’Glass, puis les articles chez VSF. Il peut retrouver ou créer une fiche article et ajouter une ligne au devis.')
P('**La gestion du stock** utilise les articles Odoo et le lieu de remise choisi sur la vente pour organiser les achats et déplacements nécessaires.')
Box('Un prix ou un article trouvé ne réserve pas une pièce','La présence d’un article dans l’assistant ne signifie pas qu’il est disponible chez RPBM. L’ajout au devis ne fait pas sortir le stock. Les mouvements sont traités dans l’application Inventaire.')
H2('La mise en place, vue côté client')
Flow(['1. Installer\nl’assistant','2. Organiser\nles lieux','3. Reprendre\nle catalogue','4. Compter\net tester'])
P('L’équipe de déploiement prépare l’installation et les accès fournisseurs. Les utilisateurs valident les parcours, les lieux physiques et les règles de travail. La reprise des quantités initiales reste une étape séparée.','small')

Page('Un entrepôt Odoo, cinq sites','Les bâtiments restent distincts. Odoo les représente comme des zones d’une même organisation RPBM.')
story.append(SiteMap());md.extend(['RPBM / Stock : Dépôts (Dépôt 1, Dépôt 2), Galleria, Genipa.','RPBM / Camion et RPBM / A controler sont hors de Stock.',''])
H2('Ce que cette séparation permet')
Bullet('**Galleria** sert ses ventes avec son stock, puis avec celui des deux dépôts. Elle ne prélève pas automatiquement à Genipa.')
Bullet('**Genipa** suit la même règle avec son propre comptoir et les deux dépôts.')
Bullet('Le **Camion** est chargé à partir des sites fixes. Une pièce déjà dans le camion ne peut pas être réservée automatiquement par une vente au comptoir.')
Bullet('La zone **A controler** reste hors du circuit de réservation normal. **CASSE** sert à enregistrer les pièces mises au rebut, avec leur origine.')
Box('Le lieu réel reste à renseigner','Le rack est la case physique où se trouve la pièce. Cette préproduction contient **179 emplacements au Dépôt 1 et 255 au Dépôt 2**. Deux fiches portent le nom **R101 au Dépôt 1** : faire lever cette ambiguïté avant le comptage initial.')

Page('Vendeur : choisir le bon circuit','Sur la vente, le champ « Transporteur / mode de remise » est placé sous le client.')
Shot('01-transporteur.png',(25,460,725,220),165,'Capture de préproduction, cadrée sur le champ : choix du mode de remise, 11/09/2026.')
T(['Choix à sélectionner','Conséquence'],[
 ['Retrait / pose Galleria','Pièce remise ou posée à Galleria.'],
 ['Retrait / pose Genipa','Pièce remise ou posée à Genipa.'],
 ['Pose sur site (Camion)','Chargement du camion, puis pose chez le client.']],[.46,.54])
P('**1.** Renseigner le client et les articles. **2.** Choisir le mode de remise convenu. **3.** Enregistrer le devis. **4.** Vérifier le choix avant de confirmer la vente.')
Box('Champ rétabli en préproduction ; à reprendre au déploiement','Le champ était absent des vues de vente inspectées. Il a été ajouté et sa sauvegarde a été vérifiée sur le devis de démonstration. Le vendeur doit le renseigner : **aucun blocage automatique des ventes sans transporteur n’a été ajouté**.',True)
P('Ne pas choisir l’ancien « Frais de livraison gratuit » pour ces trois circuits : il n’a aucune route associée. Une règle choisie exceptionnellement sur une ligne peut aussi prendre le dessus sur le transporteur ; faire contrôler ces exceptions par le référent.','small')
P('Après confirmation, demander au référent de corriger le circuit si nécessaire : changer simplement le libellé ne suffit pas à refaire les documents déjà créés. Les prix de remise sont actuellement à 0 € ; le tarif de pose à domicile reste à confirmer.','small')

Page('Remettre la pièce au comptoir','Le même fonctionnement s’applique à Galleria et à Genipa. Les exemples ci-dessous utilisent Galleria.')
H2('Cas 1 · La pièce est disponible à Galleria')
Flow(['Galleria','Client'],'Un bon de livraison Galleria. La quantité doit être réellement disponible, hors réservations existantes.')
P('À la confirmation de la vente, Odoo prépare la livraison depuis Galleria. L’équipe remet ou pose la pièce, renseigne la quantité réellement traitée et valide le bon correspondant.')
H2('Cas 2 · La pièce est dans un dépôt')
Flow(['Dépôt 1 ou 2','Galleria','Client'],'Un transfert vers Galleria, puis une livraison au client.')
P('Le préparateur ouvre le transfert **Dépôts → Galleria**, contrôle le rack d’origine et déplace la pièce. Il valide le transfert lorsque le déplacement est effectué. Le comptoir traite ensuite la livraison client.')
H2('Cas 3 · Il faut commander la pièce')
Flow(['Fournisseur','Dépôt 2','Galleria','Client'],'Une demande de prix, puis trois documents de stock après confirmation de l’achat.')
P('Si aucune quantité suffisante n’est disponible dans les lieux autorisés, Odoo peut préparer une demande de prix. L’acheteur vérifie le fournisseur, le prix et le délai, puis passe la commande selon la procédure habituelle. L’achat doit être possible pour cet article.')
Box('Lire les lignes pour savoir où prélever','Le transfert automatique porte le nom **Dépôts → Galleria**, que la pièce vienne du Dépôt 1 ou du Dépôt 2. Le dépôt et le rack réels figurent dans les lignes de préparation. Le nom seul ne suffit pas.')

Page('Préparer une pose chez le client','Le chargement et la pose sont deux événements différents, chacun avec son document.')
Flow(['Sites fixes\nDépôts / comptoirs','Camion\nPièces chargées','Client\nPièces posées'])
T(['Moment','Action de l’équipe'],[
 ['Avant le départ','Ouvrir « Chargement camion ». Contrôler les pièces et les racks d’origine. Réserver manuellement au moment de préparer le chargement.'],
 ['Chargement effectué','Renseigner les quantités réellement embarquées et valider le chargement. Les pièces sont désormais localisées dans le camion.'],
 ['Après l’intervention','Ouvrir « Pose sur site ». Renseigner et valider uniquement les quantités réellement remises ou posées.'],
 ['Pièce non posée','La quantité restante reste à traiter. Organiser son retour vers le bon comptoir ou dépôt et enregistrer ce déplacement.']],[.27,.73])
H2('Une pièce oubliée dans le camion doit rester visible')
P('Un reliquat est simplement **ce qui reste à faire**. Les opérations camion conservent automatiquement ce reste lorsque tout n’a pas été traité. Ne pas déclarer une pose terminée pour une pièce encore embarquée.')
Box('Le stock déjà embarqué ne sert pas de réserve générale','Chaque nouvelle vente « Pose sur site (Camion) » déclenche une étape de chargement. La réutilisation d’une pièce restée dans le camion doit être organisée par le référent ; elle ne doit pas être supposée automatique.',True)
P('Le circuit et les réservations manuelles sont configurés. Les essais complets de chargement, pose partielle, retour et réutilisation restent à réaliser avec l’équipe avant démarrage.','small')

Page('Les autres mouvements du quotidien','Chaque déplacement réel doit laisser une trace dans le bon document Odoo.')
T(['Situation','Marche à suivre'],[
 ['Réception fournisseur habituelle','L’achat automatique vise le Dépôt 2. Vérifier « Livrer à » sur l’achat avant confirmation. À réception, contrôler la référence et la quantité reçue.'],
 ['Rangement au dépôt','Choisir le rack réel dans les opérations détaillées ou enregistrer le rangement vers ce rack. Aucun rack de réception précis n’est imposé automatiquement.'],
 ['Dépôt 1 ↔ Dépôt 2, comptoir ↔ dépôt, Galleria ↔ Genipa','Dans Inventaire, créer un transfert avec le type correspondant à l’origine et à la destination. Contrôler les lieux, saisir les quantités, puis valider une fois le déplacement réalisé.'],
 ['Retour du camion','Choisir le retour Camion → site réellement destinataire. La quantité redevient disponible dans ce site après traitement.'],
 ['Pièce cassée','Enregistrer une mise au rebut vers CASSE depuis le lieu réel de la casse, y compris le camion. Ne pas simuler une livraison client.'],
 ['Retour fournisseur','Partir de la réception concernée et utiliser le retour. Contrôler le fournisseur, l’origine et la quantité. Le retour de stock et l’éventuel avoir restent deux sujets à traiter.']],[.29,.71])
Box('Livraison fournisseur directement au comptoir : essai à terminer','L’acheteur peut choisir « Réception Galleria » ou « Réception Genipa » avant de confirmer l’achat. Mais un transfert vers ce comptoir peut déjà avoir été généré. **Faire contrôler la chaîne par le référent** : le traitement de ce transfert devenu inutile n’est pas encore validé en situation réelle.',True)
P('Ne pas annuler un document lié à l’aveugle : cela peut affecter les mouvements suivants. Le fournisseur doit recevoir la bonne adresse par le canal de commande habituel ; vérifier le document imprimé si celui-ci est utilisé.','small')

Page('Reprendre un stock fiable','Le catalogue décrit les articles. Le stock initial indique combien de pièces se trouvent réellement à chaque endroit.')
T(['Déjà réalisé selon le compte rendu du 11/09','Encore nécessaire avant démarrage'],[
 ['Import du catalogue : 3 229 références, 15 catégories et 30 fournisseurs issus du fichier de préparation.','Fournir et approuver un relevé daté : référence, quantité, lieu exact et état de chaque pièce.'],
 ['43 références douteuses exclues du catalogue importé.','Les corriger séparément si elles doivent être utilisées ; ne pas les recréer à l’aveugle.'],
 ['Réorganisation des dépôts en préservant leurs racks existants.','Rapprocher les pièces physiques des emplacements et résoudre les cas inconnus.'],
 ['Prix fournisseurs et coûts importés ; certains coûts restent à revoir.','Faire valider les prix de vente et les coûts manquants avant utilisation commerciale.']],[.5,.5])
H2('Comment préparer la bascule')
Bullet('Fixer une date de comptage et une période pendant laquelle les mouvements sont arrêtés ou relevés séparément.')
Bullet('Compter les pièces dans les dépôts, les comptoirs et le camion. Distinguer celles réservées, cassées ou à contrôler.')
Bullet('Faire approuver les écarts, intégrer les quantités, puis contrôler quelques références de chaque site dans Odoo.')
Bullet('Choisir la date à laquelle Odoo devient la référence des mouvements et désigner les personnes chargées du suivi.')
Box('Ne pas reprendre les anciennes couleurs comme des quantités fiables','Les couleurs vendu / réservé / cassé du tableau ne sont pas conservées dans l’export CSV. Le modèle de fichier de stock initial est volontairement vide. L’import du catalogue ne prouve donc pas la reprise du stock physique.',True)
P('Les volumes du catalogue ci-dessus viennent du dernier compte rendu d’import ; ils n’ont pas été recomptés article par article pour ce guide. Les quantités présentes en préproduction ne constituent pas un inventaire de démarrage.','small')

Page('Ouvrir l’assistant véhicule','L’assistant est le bouton du module rpbm_agent. Il est accessible depuis une opportunité ou depuis son devis lié.')
Shot('02-acces-assistant.png',(25,1055,735,180),125,'Capture de préproduction, cadrée sur l’onglet « Véhicule (X’Glass) » et le bouton « Assistant véhicule ».')
H2('Le parcours conseillé')
Bullet('Ouvrir le dossier client dans le CRM et vérifier le client concerné.')
Bullet('Utiliser l’assistant dans ce dossier, ou ouvrir le devis associé à cette opportunité.')
Bullet('Sur le devis, ouvrir l’onglet **Véhicule (X’Glass)**, puis cliquer sur **Assistant véhicule**.')
Box('L’onglet est absent sur un devis indépendant','Le devis doit être lié à une opportunité. L’absence de cet onglet sur un devis sans opportunité est un comportement prévu du module. Repartir du dossier CRM ou faire vérifier le lien.')
H2('La connexion aux fournisseurs doit être prête')
P('L’ouverture de la fenêtre lance la connexion à X’Glass et VSF. L’équipe de déploiement doit avoir configuré les accès aux deux portails. Les utilisateurs ne doivent pas copier de mot de passe dans le dossier client.')
Box('État constaté pendant la préparation du guide','Lors de la préparation, les quatre paramètres de connexion n’étaient pas encore présents sur la préproduction et l’ouverture est restée sur la connexion. Ils ont depuis été configurés ; l’authentification complète et les recherches sur les portails restent à rejouer.',True)
P('Un seul utilisateur peut employer l’assistant à la fois avec les accès partagés actuels. Fermer la fenêtre après utilisation pour libérer la place.','small')

Page('Identifier le véhicule et la pièce','Parcours prévu par le module ; à vérifier sur les portails une fois les accès configurés.')
Flow(['1. Véhicule','2. Catégorie','3. Pièce','4. Article VSF'])
T(['Étape dans la fenêtre','Ce que vous faites et contrôlez'],[
 ['1. Véhicule','Saisir ou vérifier l’immatriculation, puis cliquer sur « Rechercher ». Le premier résultat peut être sélectionné automatiquement : vérifier le modèle et la version.'],
 ['Choix du véhicule','Choisir le bon véhicule. Si une alerte signale un conducteur différent du client, vérifier le dossier avant de poursuivre. « Voir » permet de consulter une fiche existante.'],
 ['2. Catégorie','Afficher les catégories du véhicule avec « Rechercher les Catégories », puis choisir le vitrage concerné. Vérifier aussi le champ « Pièce concernée », qui influence le calcul de pose existant.'],
 ['3. Pièce','Comparer les pièces proposées et sélectionner celle qui convient. Vérifier les caractéristiques et les éventuelles variantes avant de poursuivre.'],
 ['4. Article VSF','Une base Eurocode, c’est-à-dire le début de la référence vitrage, peut être proposée. La vérifier ; si nécessaire la saisir, puis utiliser « Rechercher sur VSF ».']],[.28,.72])
H2('La sélection automatique ne remplace pas votre contrôle')
P('Le véhicule, une catégorie ou le début de référence peuvent être repris du dossier ou déduits par l’assistant. Vérifier la compatibilité avec le véhicule réel : vitrage, options, capteurs, dimensions et accessoires nécessaires.')
Box('Aucun résultat ?','Vérifier d’abord l’immatriculation et le choix du véhicule. Pour la recherche article, vérifier la référence. Une panne du portail et une recherche sans résultat sont deux situations différentes : ne pas conclure trop vite que la pièce n’existe pas.')

Page('Choisir un article et l’ajouter au devis','Le choix d’une référence VSF et son ajout au devis sont deux actions distinctes.')
Flow(['Sélectionner\nl’article VSF','Retrouver ou créer\nla fiche Odoo','Ajouter au devis'])
T(['Ce qui est affiché','Ce que cela signifie'],[
 ['Prix / Coût','Informations fournies par le parcours VSF. Vérifier ensuite le prix final de la ligne de devis, calculé avec les règles commerciales existantes.'],
 ['En stock / Indisponible','Disponibilité présentée par VSF. **Ce n’est pas le stock physique RPBM** ni une promesse de délai de réception.'],
 ['Voir le produit','Une fiche Odoo a été retrouvée. L’assistant indique le critère utilisé : référence, Eurocode ou nom. Vérifier qu’il s’agit bien du même article.'],
 ['Créer le produit','Aucune fiche correspondante n’a été trouvée. Créer la fiche seulement après vérification ; cela ne crée aucune quantité en stock.'],
 ['Ajouter au devis','Ajoute une ligne de quantité 1. Contrôler la quantité, la référence, la description et le prix dans le devis.'],
 ['Articles suggérés','Les accessoires ne sont pas ajoutés automatiquement. Sélectionner et ajouter séparément ceux qui sont nécessaires.']],[.27,.73])
P('Cliquer sur une image pour l’agrandir lorsque cette possibilité est proposée. Le lien **Fiche technique** permet de consulter les détails de l’article.')
Box('Éviter les doublons dans le devis','« Article déjà présent dans le devis » signifie qu’une ligne existe déjà. « Retirer du devis » n’est disponible que pour une ligne ajoutée par cette fenêtre pendant la session en cours. Une ligne existante se corrige dans le devis.')
P('Sur une opportunité CRM, la confirmation prépare les informations du dossier. L’ajout de lignes décrit ici concerne le widget ouvert depuis une vente.','small')

Page('Enregistrer et reprendre son travail','Les boutons de la fenêtre assistant ne confirment pas la commande client.')
T(['Bouton','Effet attendu'],[
 ['Confirmer, dans l’assistant','Reporte les informations sélectionnées dans le formulaire. Il reste à enregistrer ce formulaire.'],
 ['Confirmer et enregistrer','Reporte les informations puis enregistre le dossier ou le devis.'],
 ['Annuler ou fermer la fenêtre','Quitte la recherche. Ne pas l’utiliser comme une annulation générale : une fiche créée ou une ligne déjà ajoutée peut nécessiter un contrôle séparé.'],
 ['Confirmer, sur la vente','Valide commercialement la vente et peut déclencher les documents logistiques. Vérifier les articles et le transporteur avant ce clic.']],[.34,.66])
H2('Les contrôles de fin de saisie')
P('Vérifier le client, le véhicule, la pièce concernée et la référence complète. Relire les lignes ajoutées, les quantités et les prix. Choisir le transporteur / mode de remise et enregistrer le devis.')
H2('Si l’assistant ne répond pas comme prévu')
T(['Message ou situation','Réflexe'],[
 ['Assistant utilisé par une autre personne','Attendre qu’elle termine et ferme sa fenêtre. Éviter les connexions concurrentes aux portails partagés.'],
 ['Session expirée / Reconnecter','Utiliser « Reconnecter » si proposé. Vérifier le contexte restauré avant de poursuivre.'],
 ['Connexion bloquée ou refusée','Faire vérifier les accès et la disponibilité des portails par le référent. Ne pas multiplier les créations ou les confirmations.'],
 ['Onglet ou bouton introuvable','Vérifier l’opportunité liée, l’installation du module et les droits du compte utilisateur.']],[.40,.60])
P('Le verrou d’utilisation expire après 15 minutes sans activité prévue par le module. Une panne du portail ou du réseau peut demander une intervention ; attendre ne corrige pas un problème d’accès.','small')

Page('Ce qui a été vérifié','Les résultats ci-dessous concernent la préproduction contrôlée le 11 septembre 2026.')
T(['Contrôle','Résultat et portée'],[
 ['Module rpbm_agent','Version 17.0.260730.6 observée sur la cible lors du contrôle ; la version source actuelle est 17.0.260911.1. Bouton visible sur un devis lié à une opportunité.'],
 ['Organisation logistique','Un entrepôt RPBM ; trois routes métier, 34 types d’opération, six règles métier et une règle de rangement vers le Dépôt 2.'],
 ['Contrôle structurel rejoué','53 entrées : **50 conformes, 2 observations, 1 essai non réalisé**. Aucune anomalie ou alerte parmi les contrôles exécutés.'],
 ['Transporteur sur la vente','Champ rétabli, liste des choix vérifiée dans Chrome et valeur Galleria sauvegardée puis relue sur le devis de démonstration.'],
 ['Essais du dernier commit','T1 : livraison Galleria générée avec stock au comptoir. T3 : en rupture, achat préparé vers le Dépôt 2, transfert et livraison en attente. Résultats issus du compte rendu du lancement précédent.'],
 ['Recherche X’Glass et VSF','Les paramètres ont été configurés après ce contrôle ; l’authentification et la recherche de bout en bout restent à valider.']],[.30,.70])
Box('La recette logistique n’est pas encore complète','Les tests T1 et T3 n’ont pas validé physiquement une réception, un transfert ou une livraison. Les cas Genipa, camion, retour, casse, réception directe au comptoir et quantités partielles restent à éprouver avec les utilisateurs.',True)
P('La présence des routes ne garantit pas tous les cas particuliers : disponibilité insuffisante, autres réservations, article nouvellement créé ou absence de fournisseur. Le référent doit vérifier l’achat automatique pour les articles concernés.','small')
P('Les anciennes routes et l’ancien mode gratuit sont encore présents. Les résultats du contrôle structurel ne valent pas validation de leur usage.','small')

Page('Validation du client et démarrage','À compléter ensemble, en distinguant l’accord sur l’organisation et l’autorisation de démarrage.')
T(['Décision à consigner','Accord / réserve / responsable'],[
 ['Accepter les cinq sites regroupés dans un entrepôt Odoo, avec le camion à part.','________________________________'],
 ['Accepter le stock séparé des comptoirs, les dépôts communs et les transferts automatiques regroupés.','________________________________'],
 ['Organiser le choix du transporteur sur toutes les ventes et le traitement des oublis.','________________________________'],
 ['Nommer les personnes qui achètent, réceptionnent, rangent, transfèrent, livrent et traitent les écarts.','________________________________'],
 ['Valider le tarif « Pose à domicile », actuellement à 0 €, et le traitement des exceptions.','________________________________'],
 ['Fixer le comptage initial, le traitement des pièces à contrôler et la date de bascule.','________________________________']],[.64,.36])
H2('Conditions à lever avant utilisation réelle')
P('Rejouer et valider les accès X’Glass/VSF ; réaliser les cas métier restants ; vérifier les droits avec un vendeur et un magasinier ; intégrer puis contrôler le stock initial ; reprendre la visibilité du transporteur sur la cible de production.')
P('**Décision :** accord sur l’organisation / accord avec réserves / à revoir\n**Nom et fonction :** __________________________________________\n**Date et signature :** _________________________________________')
P('Un accord sur l’organisation n’efface pas les réserves de recette. Le lancement opérationnel fera l’objet d’une décision distincte une fois les conditions levées.','small')
H2('Origine du document')
P('Sources : commit de recette 08b6b1d et commit de configuration rpbm_agent e6c7364 du dépôt RPBM ; compte rendu « module et architecture » du 11/09/2026 ; dossier Gestion Stock ; code et documentation fonctionnelle de rpbm_agent ; lectures MCP et captures Chrome du 11/09/2026. Les anciens documents de cadrage sont interprétés avec les amendements du dernier compte rendu.','small')
P('Préproduction : rpbm-pre-prod-37860002.dev.odoo.com. Les notes de vérification, captures et sources reproductibles de cette édition se trouvent dans Jobs/rpbm_agent_stock/documentation.','small')

class NumberedCanvas(canvas.Canvas):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw);self.saved=[]
    def showPage(self):
        self.saved.append(dict(self.__dict__));self._startPage()
    def save(self):
        total=len(self.saved)
        for state in self.saved:
            self.__dict__.update(state)
            self.setStrokeColor(colors.HexColor('#D7E3E6'));self.line(42,45,W-42,45)
            self.setFillColor(MUTED);self.setFont('Guide',8)
            self.drawString(42,31,'RPBM · Logistique & assistant véhicule · 11 septembre 2026')
            self.drawRightString(W-42,31,f'{self._pageNumber} / {total}')
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

def header(c,doc):
    c.saveState();c.setFillColor(TEAL);c.rect(0,H-9,W,9,stroke=0,fill=1)
    if doc.page>1:
        c.setFont('Guide-Bold',8);c.setFillColor(MUTED);c.drawRightString(W-42,H-30,'PRÉPRODUCTION · DOCUMENT À VALIDER')
    c.restoreState()

doc=SimpleDocTemplate(str(OUT),pagesize=(W,H),leftMargin=42,rightMargin=42,topMargin=48,bottomMargin=62,title='RPBM - Guide client logistique et assistant véhicule',author='RPBM / Paradigme',subject='Validation de l’organisation logistique et utilisation de rpbm_agent')
doc.build(story,onFirstPage=header,onLaterPages=header,canvasmaker=NumberedCanvas)
(HERE/'guide-client.md').write_text('\n'.join(md),encoding='utf-8')
print(OUT)
