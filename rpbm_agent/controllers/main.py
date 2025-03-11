
from odoo.http import Controller, request, route
import logging

from . import vsf
from . import xglass

_logger = logging.getLogger(__name__)

vsfAgent = vsf.VSFAgent()
xglassAgent = xglass.XGLASS()

class AgentController(Controller):

    @route('/rpbm_agent_auth', auth='user', methods=['POST'])
    def rpbm_agent_auth(self):
        _logger.info("rpbm_agent_auth")
        xglassAgent.auth()
        vsfAgent.auth()
        _logger.info("rpbm_agent_auth done")
        return 
    
    @route('/rpbm_agent_close', auth='user', methods=['POST'])
    def rpbm_agent_close(self):
        _logger.info("rpbm_agent_close")
        xglassAgent.close()
        # vsfAgent.close()
        _logger.info("rpbm_agent_close done")
        return
    
    @route('/searchImmatriculation', auth='user', methods=['POST'])
    def searchImmatriculation(self,immatriculation: str):
        _logger.info(f"searchImmatriculation {immatriculation}")
        vehicules = xglassAgent.searchVehiculeImmat(immatriculation)
        return [vehicule.__dict__ for vehicule in vehicules]

