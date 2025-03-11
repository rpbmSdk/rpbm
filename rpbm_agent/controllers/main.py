
from odoo.http import Controller, request, route
import logging

from . import vsf
from . import xglass

_logger = logging.getLogger(__name__)

vsfAgent = vsf.VSFAgent()
xglassAgent = xglass.XGLASS()

class AgentController(Controller):
    
    @route('/searchImmatriculation', auth='user', methods=['POST'])
    def searchImmatriculation(self,immatriculation: str):
        _logger.info(f"searchImmatriculation {immatriculation}")
        vehicules = xglassAgent.searchVehiculeImmat(immatriculation)
        return [vehicule.__dict__ for vehicule in vehicules]

