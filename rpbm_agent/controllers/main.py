
from odoo.http import Controller, request, route
import logging

from . import vsf
from . import xglass

_logger = logging.getLogger(__name__)

vsfAgent = vsf.VSFAgent()
xglassAgent = xglass.XGLASS()

class AgentController(Controller):

    @route('/rpbm_agent_auth', auth='user', type='json')
    def rpbm_agent_auth(self):
        global vsfAgent
        global xglassAgent
        vsfAgent = vsf.VSFAgent()
        xglassAgent = xglass.XGLASS()
        _logger.info("rpbm_agent_auth")
        VSF_LOGIN = request.env['ir.config_parameter'].sudo().get_param('VSF_LOGIN')
        VSF_PASSWORD = request.env['ir.config_parameter'].sudo().get_param('VSF_PASSWORD')
        XGLASS_USER = request.env['ir.config_parameter'].sudo().get_param('XGLASS_USER')
        XGLASS_PASS = request.env['ir.config_parameter'].sudo().get_param('XGLASS_PASS')
        xglassAgent.close()
        xglassAgent.auth(XGLASS_USER, XGLASS_PASS)
        vsfAgent.auth(VSF_LOGIN, VSF_PASSWORD)
        _logger.info("rpbm_agent_auth done")
        return 
    
    @route('/rpbm_agent_close', auth='user', type='json')
    def rpbm_agent_close(self):
        _logger.info("rpbm_agent_close")
        xglassAgent.close()
        # vsfAgent.close()
        _logger.info("rpbm_agent_close done")
        return
    
    @route('/searchImmatriculation', auth='user', type='json')
    def searchImmatriculation(self,immatriculation: str):
        _logger.info(f"searchImmatriculation {immatriculation}")
        try:
            vehicules = xglassAgent.searchVehiculeImmat(immatriculation)
            return [vehicule.__dict__ for vehicule in vehicules]
        except Exception as e:
            _logger.warning(e)
            return []

    @route('/getOdooVehicule', auth='user', type='json')
    def getVehicule(self,immatriculation:str, vehicule:xglass.XGlassVehicule):
        """
            Permet de retourner l'ID du véhicule enregistré en BDD de Odoo, si 
            le véhicule n'existe pas, retourne False
        """
        _logger.info(f"getVehicule {vehicule}")
        vehicules = request.env['fleet.vehicle'].search([('licence_plate', '=', immatriculation)])
        if vehicules:
            if len(vehicules) > 1:
                _logger.warning(f"Plusieurs véhicules avec la même immatriculation {immatriculation}")
            vehicule = vehicules[0]
            return vehicule.id
        else:
            return False

    @route('/createVehicule', auth='user', type='json')
    def createVehicule(self,immatriculation:str, vehicule:xglass.XGlassVehicule):
        """
            Permet de créer un véhicule en BDD de Odoo
        """
        _logger.info(f"getVehicule {vehicule}")
        vehicules = request.env['fleet.vehicle'].search([('licence_plate', '=', immatriculation)])
        if vehicules:
            if len(vehicules) > 1:
                _logger.warning(f"Plusieurs véhicules avec la même immatriculation {immatriculation}")
            vehicule = vehicules[0]
        else:
            marque = request.env['fleet.vehicle.model.brand'].search([('name', '=', vehicule.xGlassModele.xGlassMarque.nom)])
            if not marque:
                marque = request.env['fleet.vehicle.model.brand'].create({
                    'name': vehicule.xGlassModele.xGlassMarque.nom
                })
            modele = request.env['fleet.vehicle.model'].search([('name', '=', vehicule.xGlassModele.nom)])
            if not modele:
                modele = request.env['fleet.vehicle.model'].create({
                    'name': vehicule.xGlassModele.nom,
                    'brand_id': marque.id
                })
            vehicule = request.env['fleet.vehicle'].create({
                'model_id': modele.id,
                'licence_plate': immatriculation,
                'description': vehicule.libelleCourt
            })
            _logger.info(f"Véhicule créé {vehicule}")

        return vehicule.id


    @route('/getPlanche', auth='user', type='json')
    def getPlanche(self,vehiculeId:int):
        _logger.info(f"getPlanche {vehiculeId}")
        planche = xglassAgent.selectVehicule(str(vehiculeId))
        return planche
    
    @route('/getPieces', auth='user', type='json')
    def getPieces(self,plancheId:int, calqueId:int):
        _logger.info(f"getPieces {plancheId} {calqueId}")
        raw = xglassAgent.getPiecesData(plancheId, calqueId)
        rawData = {
            'ELEMENTSIT_PRINCIPAUX': [xglass.XGlassElement(**element) for element in raw.get('ELEMENTSIT_PRINCIPAUX', [])],
            'ELEMENTSIT_COMPLEMENTAIRES': [xglass.XGlassElement(**element) for element in raw.get('ELEMENTSIT_COMPLEMENTAIRES', [])],
        }
        pieces = []

        for elementKey,Elements in rawData.items():
            for Element in Elements:
                for XGLasspiece in Element.pieces:
                    piece = XGLasspiece.__dict__
                    piece['elementKey'] = elementKey
                    piece['element.withPiecesAm'] = Element.withPiecesAm
                    piece['elementSitId'] = Element.elementSitId
                    pieces.append(piece)
        return pieces

    @route('/getPieceAm', auth='user', type='json')
    def getPieceAm(self,element_withPiecesAm, pieceId:int=None, elementSitId:int=None):
        _logger.info(f"getPieceAm {element_withPiecesAm} {pieceId} {elementSitId}")
        URL = 'https://portail-xglass.com/ajax/findSelectionsPiecesAmView.html'
        data = {
            'withPiecesAm':element_withPiecesAm,
            'idDevis':''
        }
        if pieceId:
            data['idPieceOe'] = pieceId
        else:
            data['idElementSit'] = elementSitId

        r = xglassAgent.post(
            URL,
            data=data,
        )
        piecesData = r.json()
        try:
            return piecesData.get('selectionsPiecesAmView',[])
        except Exception as e:
            _logger.warning(e)
            return [] 
         
    @route('/searchBaseEurocode', auth='user', type='json')
    def searchBaseEurocode(self,baseEurocode:str):
        _logger.info(f"searchBaseEurocode {baseEurocode}")
        try:
            vsfArticles = vsfAgent.searchEurocodeArticlesClient(baseEurocode)
            return [vsfArticle.__dict__ for vsfArticle in vsfArticles]
        except Exception as e:
            _logger.warning(e)
            return []