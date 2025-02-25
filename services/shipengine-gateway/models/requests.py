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
        self.cancelled = request.args.get('cancelled', 'false') == 'true'


class RateEstimateRequest(Serializable):
    def __init__(self, shipment: dict, carrier_ids):
        self.carrier_ids = carrier_ids

        # Extract origin details
        origin = shipment.get('origin', {})
        self.from_country_code = origin.get('country_code')
        self.from_postal_code = origin.get('zip_code')
        self.from_city_locality = origin.get('city_locality')
        self.from_state_province = origin.get('state_province')

        # Extract destination details
        destination = shipment.get('destination', {})
        self.to_country_code = destination.get('country_code')
        self.to_postal_code = destination.get('zip_code')
        self.to_city_locality = destination.get('city_locality')
        self.to_state_province = destination.get('state_province')

        # Set weight and dimensions
        self.weight = {
            'value': shipment.get('total_weight'),
            'unit': 'pound'
        }
        self.dimensions = {
            'unit': 'inch',
            'length': shipment.get('length'),
            'width': shipment.get('width'),
            'height': shipment.get('height')
        }
