from typing import Dict

from framework.serialization import Serializable


class GetShipmentRequest(Serializable):
    def __init__(
        self,
        request: Dict
    ):
        self.shipengine_model = request.args.get('shipengine_model') == 'true'
        self.page_number = request.args.get('page_number') or 1
        self.page_size = request.args.get('page_size') or 25
