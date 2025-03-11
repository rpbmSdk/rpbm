
from odoo.http import Controller, request, route
import logging

from vsf import VSFAgent
from xglass import XGLASS

_logger = logging.getLogger(__name__)

vsfAgent = VSFAgent()
xglassAgent = XGLASS()

class AgentController(Controller):

    def create_XGlassAgent(self):
        return XGLASS()
    
    def create_VSFAgent(self):
        return VSFAgent()
    
    @route('/searchImmatriculation', auth='user', methods=['POST'])
    def searchImmatriculation(self,immatriculation: str):
        agent = self.create_XGlassAgent()
        res = agent.searchVehiculeImmat(immatriculation)

