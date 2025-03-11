
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
        _logger.info("rpbm_agent_auth")
        xglassAgent.auth()
        vsfAgent.auth()
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
        vehicules = xglassAgent.searchVehiculeImmat(immatriculation)
        return [vehicule.__dict__ for vehicule in vehicules]

    @route('/getPlanche', auth='user', type='json')
    def getPlanche(self,vehiculeId:int):
        _logger.info(f"getPlanche {vehiculeId}")
        planche = xglassAgent.selectVehicule(str(vehiculeId))
        return planche.__dict__
    
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
                    pieces.append(piece)
        return pieces
