import requests
import dotenv

dotenv.load_dotenv()
import os
import bs4 as bs

import json
from datetime import datetime

try:
    from . import xglass_lbl 
    getLabel = xglass_lbl.getLabel
except:
    from xglass_lbl import getLabel

import logging
_logger = logging.getLogger(__name__)

XGLASS_URL = "https://portail-xglass.com"
XGLASS_LOGIN_URL = f"{XGLASS_URL}/j_spring_security_check"
XGLASS_MAIN_URL = f"{XGLASS_URL}/mainMenu.html"

# XGLASS_USER = os.getenv("XGLASS_USER")
# XGLASS_PASS = os.getenv("XGLASS_PASS")

XGLASS_searchImmat = f"{XGLASS_URL}/ajax/searchImmat.html"
LOGOUT_URL = "https://portail-xglass.com/logout.html"


class XGlassMarque():
    codeDarva:str
    codeEtai:str
    groupeMarque:dict
    id:int
    nom:str
    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        pass

class XGlassModele():
    dateDebut:str
    dateFin:str
    gamme:str
    marque:dict
    xGlassMarque:XGlassMarque
    nom:str
    serie:str

    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        self.xGlassMarque = XGlassMarque(**self.marque)
        pass
    
    def getDateDebut(self):
        return datetime.strptime(self.dateDebut, '%Y-%m-%dT%H:%M:%S')
    def getDateFin(self):
        return datetime.strptime(self.dateFin, '%Y-%m-%dT%H:%M:%S')


class XGlassVehicule():
    energie:int
    imageRef:str
    id:int
    libelleCourt:str
    modele:dict
    xGlassModele:XGlassModele
    puissanceKw:int
    portesNbr:int
    energieLibelle:str

    energieLibelle:str
    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        self.energieLibelle = getLabel(f"lbl.energie.{self.__dict__.get('energie')}")
        self.imgUrl = f"{XGLASS_URL}/images/images_modele/{self.imageRef}"
        self.xGlassModele = XGlassModele(**self.modele)



class XGlassCalque():
    id:int
    codification:str
    libelle:str
    type:str
    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)

class XGlassPlanche():
    id:int
    calques:list[dict]
    xGlassCalques : list[XGlassCalque]

    def __init__(self, id:int, calques:list[XGlassCalque], **kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        self.id = id
        self.calques = calques
        self.xGlassCalques = [XGlassCalque(**c) for c in calques]

class XGlassPieceOeCaracteristiqueType:
        id:int
        libelle:str
        ordre:int
        code:str
        def __init__(self,**kwargs):
            for key, value in kwargs.items():
                setattr(self,key,value)
        

class XGlassPieceOeCaracteristique():
    
    codearcauto:str
    id:int
    ordre:int
    type:dict
    xGlassPieceOeCaracteristiqueType:XGlassPieceOeCaracteristiqueType
    
    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        self.xGlassPieceOeCaracteristiqueType = XGlassPieceOeCaracteristiqueType(**self.type)
        pass

class XGlassPieceOe():
    caracteristiques:list[dict]
    
    xGlassPieceOeCaracteristique:list[XGlassPieceOeCaracteristique]
    couleur:str
    descriptionTechnique:str
    libelle:str
    libelleComplementaire:str
    libellePrincipal:str
    matiere:str
    origine:str
    
    id:int
    prix:float
    reference:str
    referenceClean:str
    referencetrim0:str

    eurocode:str

    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        self.xGlassPieceOeCaracteristique = [XGlassPieceOeCaracteristique(**c) for c in self.caracteristiques]
        self.eurocode = kwargs.get('reference')

class XGlassPieceTempsActivite():
    code:str
    id:int
    libelle:str
    nature:str
    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        pass

class XGlassPieceTempsOperationTempsIntervention():
    code:str
    id:int
    libelleCourt:str
    libelleLong:str
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        pass
        
class XGlassPieceTempsOperationTempsTypeOperationTemps():
    id:int
    libelle:str
    typeOperation:str
    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        pass


class XGlassPieceTempsOperationTemps():
    id:int
    idMarque:int
    intervention:dict
    xGlassPieceTempsOperationTempsIntervention:XGlassPieceTempsOperationTempsIntervention
    reference:str
    sequence:int
    typeOperationTemps:dict
    xGlassPieceTempsOperationTempsTypeOperationTemps:XGlassPieceTempsOperationTempsTypeOperationTemps
    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        self.xGlassPieceTempsOperationTempsIntervention = XGlassPieceTempsOperationTempsIntervention(**self.intervention)
        self.xGlassPieceTempsOperationTempsTypeOperationTemps = XGlassPieceTempsOperationTempsTypeOperationTemps(**self.typeOperationTemps)
        pass

class XGlassPieceTemps():
    id:int
    activite:dict
    xGlassPieceTempsActivite:XGlassPieceTempsActivite
    operationTemps:dict
    taux:float
    temps:float
    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        self.xGlassPieceTempsActivite = XGlassPieceTempsActivite(**self.activite)

class XGlassPiece():
    id:int
    eurocode:str
    containsPiecesAm:bool
    # filterPieceByVin:bool
    pieceOe:dict
    xGlassPieceOe:XGlassPieceOe

    tempsList:list[dict]
    xGlassPieceTemps:list[XGlassPieceTemps]

    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        
        self.id = self.pieceOe.get('id')
        self.xGlassPieceOe = XGlassPieceOe(**self.pieceOe)
        self.eurocode = self.xGlassPieceOe.eurocode

        self.xGlassPieceTemps = [XGlassPieceTemps(**t) for t in self.tempsList]

class XGlassPieceAm():
    id:int
    eurocode:str
    pieceAm:dict
    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        self.eurocode = self.pieceAm.get('reference')
        self.id = self.pieceAm.get('id')

class XGlassElement():
    pieces : list[XGlassPiece]
    libelle:str
    withPiecesAm:bool
    elementSitId:str
    def __init__(self,**kwargs):
        for key, value in kwargs.items():
            setattr(self,key,value)
        self.pieces = [XGlassPiece(**p) for p in self.listPieceOeView]
        self.libelle = self.elementSitLibelle



class XGLASS:
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Host": "portail-xglass.com",
        "Origin": "https://portail-xglass.com",
    }

    def __init__(self):
        self.session = requests.Session()
        self.initRecherche = False
        self.selectedVehiculePage = None
        # self.auth()

    def get(self, url):
        return self.session.get(url)

    def post(self, url, data: dict = {}, **kwargs):
        return self.session.post(url, data=data)

    def auth(self, XGLASS_USER:str, XGLASS_PASS:str):
        self.get(XGLASS_URL)
        JSESSIONID = self.session.cookies.get_dict().get("JSESSIONID")
        payload = {
            "j_username": XGLASS_USER,
            "j_password": XGLASS_PASS,
            "spring-security-redirect": "/mainMenu.html",
        }

        def meta_auth():
            return self.post(
                XGLASS_LOGIN_URL,
                data=payload,
                verify=False,
                allow_redirects=False,
            )
        _logger.info('First login')
        r = meta_auth()
        _logger.info(f'res return url {r.request.url}')

        if r.request.url != XGLASS_MAIN_URL:
            self.close()
            _logger.info('Second login')
            # _logger.info(f'res return url {r.request.url}')
            r = meta_auth()
            _logger.info(f'res return url {r.request.url}')
        if r.request.url != XGLASS_MAIN_URL:
            raise Exception("Login failed")
        return

    def close(self):
        r = self.get(LOGOUT_URL)
        if self.login_form(r):
            print("Logout success")
        self.session.close()

    def login_form(self, r: requests.Response):
        login_form = bs.BeautifulSoup(r.text, "html.parser")
        if login_form.find("form"):
            return True
        return False

    def ensure_logged(self, r: requests.Response):
        if self.login_form(r):
            self.session.close()
            raise Exception("Login failed")

    def setInitRecherche(self):
        r = self.get("https://portail-xglass.com/initRechercheVehicule.html")
        self.ensure_logged(r)
        self.initRecherche = True

    def searchImmat(self, immatriculation: str = "DS808DZ") -> dict:
        if not self.initRecherche:
            self.setInitRecherche()
        r = self.post(
            XGLASS_searchImmat,
            data={"selectionsCriteres.immatriculation": immatriculation},
        )
        return r.json()
    
    def searchVehiculeImmat(self, immatriculation: str = "DS808DZ") -> list[XGlassVehicule]:
        data = self.searchImmat(immatriculation)
        print(data)
        _logger.info(data)
        listeDeVariantes = data.get('regroupementVariantes')[0].get('listeDeVariante')
        return [XGlassVehicule(**v) for v in listeDeVariantes]

    
    def getSelectedVehiculePage(self, idVehicule: str='397899'):
        r = self.post(
            "https://portail-xglass.com/selectVehicule.html",
            data={"sessionScopedBean.infoSelectionVehicule.variante.id": idVehicule},
        )
        self.selectedVehiculePage = bs.BeautifulSoup(r.text, "html.parser")
        return self.selectedVehiculePage
    
    def getVehiculeMeta(self, idVehicule: str='397899'):
        # r = self.post(
        #     "https://portail-xglass.com/selectVehicule.html",
        #     data={"sessionScopedBean.infoSelectionVehicule.variante.id": idVehicule},
        # )
        page = self.selectedVehiculePage if self.selectedVehiculePage else self.getSelectedVehiculePage(idVehicule)
        scripts = page.find_all("script",src=False)
        def extract_line_value(line, key):
            if key in line:
                line = line.replace(key, "").replace(':', "").replace(',', "").replace("'", '')
                return line.strip()
            return None

        keys = ['vin', 'cnit', 'dateMec']
        data = {}

        for script in scripts:
            try:
                lines = script.text.splitlines()
                for line in lines:
                    for key in keys:
                        value = extract_line_value(line, key)
                        if value:
                            data[key] = value
                            # break
                print(data)
                return data
            except Exception as e :
                print(e)
                pass
    
    def selectVehicule(self, idVehicule: str='397899'):
        # r = self.post(
        #     "https://portail-xglass.com/selectVehicule.html",
        #     data={"sessionScopedBean.infoSelectionVehicule.variante.id": idVehicule},
        # )
        # page = bs.BeautifulSoup(r.text, "html.parser")
        # page = self.selectedVehiculePage if self.selectedVehiculePage else self.getSelectedVehiculePage(idVehicule)
        page = self.getSelectedVehiculePage(idVehicule)
        scripts = page.find_all("script",src=False)
        for script in scripts:
            try:
                if "planche =" in script.text:
                    lines = script.text.splitlines()
                    for line in lines:
                        if "planche =" in line:
                            raw = line.split("planche = ")[1]
                            raw = raw.replace(";", "")
                            return json.loads(raw)
            except:
                pass
        return {}

    def getPlancheData(self, vehicule: XGlassVehicule):
        raw = self.selectVehicule(vehicule.id)
        # calques = raw.get("calques")
        # data = {}
        # if calques:
        #     data['calques'] = [XGlassCalque(**c) for c in calques]
        # data['id'] = raw.get('id')
        return XGlassPlanche(**raw)

    def affichagePieces(self, planche:XGlassPlanche, calque:XGlassCalque)->requests.Response:
        return self.get(f'https://portail-xglass.com/affichagePieces.html?planche.id={planche.id}&calque.id={calque.id}&filtrageVinButtonClickedForDevisRapide=true')

    def getPieceData(self, planche:XGlassPlanche, calque:XGlassCalque)->dict:
        html = self.affichagePieces(planche, calque).text
        page = bs.BeautifulSoup(html, "html.parser")
        scripts = page.find_all("script",src=False)
        lines : list[str] = []
        for script in scripts:
            try:
                if "var elementSitMapData =" in script.text:
                    lines = script.text.splitlines()
                    break
            except:
                pass
        for line in lines:
            if "var elementSitMapData =" in line:
                raw = line.split("var elementSitMapData = ")[1]
                raw = raw.replace(";", "")
                return json.loads(raw)[0]
        raise Exception("Piece not found")

    def getPieces(self, planche:XGlassPlanche, calque:XGlassCalque):
        data = self.getPieceData(planche, calque)
        self.elements_principaux = [XGlassElement(**p) for p in data.get('ELEMENTSIT_PRINCIPAUX')]
        self.elements_complementaires = [XGlassElement(**p) for p in data.get('ELEMENTSIT_COMPLEMENTAIRES')]

    def getPiecesData (self, plancheId:int, calqueId:int):
        html = self.get(f'https://portail-xglass.com/affichagePieces.html?planche.id={plancheId}&calque.id={calqueId}&filtrageVinButtonClickedForDevisRapide=true').text
        page = bs.BeautifulSoup(html, "html.parser")
        scripts = page.find_all("script",src=False)
        lines : list[str] = []
        for script in scripts:
            try:
                if "var elementSitMapData =" in script.text:
                    lines = script.text.splitlines()
                    break
            except:
                pass
        for line in lines:
            if "var elementSitMapData =" in line:
                raw = line.split("var elementSitMapData = ")[1]
                raw = raw.replace(";", "")
                return json.loads(raw)[0]
        raise Exception("Piece not found")
    
    def findSelectionsPiecesAmView(self, element:XGlassElement, piece:XGlassPiece = None):
        URL = 'https://portail-xglass.com/ajax/findSelectionsPiecesAmView.html'
        data = {
            'withPiecesAm':element.withPiecesAm,
            'idDevis':''
        }
        if piece:
            data['idPieceOe'] = piece.id
        else:
            data['idElementSit'] = element.elementSitId

        r = self.post(
            URL,
            data=data,
        )
        return r
    
    def getPieceAm(self, element:XGlassElement, piece:XGlassPiece=None):
        r = self.findSelectionsPiecesAmView(element, piece)
        data = r.json()
        return [XGlassPieceAm(**p) for p in data.get('selectionsPiecesAmView')]

if __name__ == "__main__":
    from pprint import pprint

    xglass = XGLASS()
    r = xglass.auth()
    try:
        vehicules = xglass.searchVehiculeImmat()
        vehicule = vehicules[0]
        pprint(vehicule.__dict__)
        planche = xglass.getPlancheData(vehicule)
        pare_brise = [c for c in planche.calques if c.libelle == "PARE-BRISE"][0]
        xglass.affichagePieces(planche, pare_brise)
    except Exception as e:
        print(e)

    xglass.close()
