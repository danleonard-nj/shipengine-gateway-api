from typing import Dict

from deprecated import deprecated
from framework.logger.providers import get_logger
from framework.serialization import Serializable
from models.mapping import mapped_value, shipment_status_mapping

logger = get_logger(__name__)


class Shipment(Serializable):
    def __init__(self, data, service_code_mapping=None, carrier_mapping=None):
        self.shipment_id = data.get('shipment_id')
        self.carrier_id = data.get('carrier_id')
        self.created_date = data.get('created_at')
        self.packages = self._get_packages(data.get('packages'))
        self.return_address = ShipmentAddress(
            data=data.get('return_to'))
        self.service_code = data.get('service_code'),
        self.ship_date = data.get('ship_date'),
        self.origin = ShipmentAddress(
            data=data.get('ship_from'))
        self.destination = ShipmentAddress(
            data=data.get('ship_to'))
        self.shipment_status = shipment_status_mapping.get(
            data.get('shipment_status'))
        self.total_weight = data.get('total_weight').get('value')

        if service_code_mapping is not None:
            self._map_service_codes(
                mapping=service_code_mapping)
        if carrier_mapping is not None:
            self._map_carrier(
                mapping=carrier_mapping)

    def _map_service_codes(self, mapping):
        logger.info('Mapping service code names')
        self.service_code_name = [
            mapped_value(mapping=mapping,
                         value=service_code)
            for service_code in self.service_code]

    def _map_carrier(self, mapping):
        self.carrier_name = mapped_value(
            mapping=mapping,
            value=self.carrier_id).name

    def _get_packages(self, package_data):
        return [
            ShipmentPackage(data=package)
            for package in package_data
        ]

    def to_shipengine_shipment(self) -> dict:
        return {
            'shipment_id': self.shipment_id,
            'carrier_id': self.carrier_id,
            'created_at': self.created_date,
            'packages': [package.to_shipengine_package() for package in self.packages],
            'return_to': self.return_address,
            'service_code': self.service_code,
            'ship_date': self.ship_date,
            'ship_from': self.origin.to_shipengine_address(),
            'ship_to': self.destination.to_shipengine_address(),
            'shipment_status': self.shipment_status,
            'total_weight': {
                'unit': 'ounce',
                'value': float(self.total_weight)
            }
        }

    @deprecated
    def to_json(
        self
    ) -> Dict:
        return {
            'id': self.shipment_id,
            'carrier_id': self.carrier_id,
            'carrier_name': self.carrier_name,
            'created_date': self.created_date,
            'packages': [package.to_json() for package in self.packages],
            'return_address': self.return_address.to_json(),
            'service_code': self.service_code,
            'service_code_name': self.service_code_name,
            'ship_date': self.ship_date,
            'origin': self.origin.to_json(),
            'destination': self.destination.to_json(),
            'shipment_status': self.shipment_status,
            'total_weight': self.total_weight,
        }

    def to_dict(
        self
    ) -> Dict:
        return self.to_json()


class CreateShipment(Serializable):
    def __init__(self, data):
        self.shipper_id = data.get('shipper_id')
        self.origin = data.get('origin')
        self.destination = data.get('destination')
        self.dimensions = data.get('dimensions')
        self.weight = data.get('weight')
        self.insured_value = data.get('insured_value')
        self.service_code = data.get('service_code')
        self.insurance_provider = data.get('insurance_provider')

    def to_dict(self):
        return self.to_json()

    @deprecated
    def to_json(self):
        origin = ShipmentAddress(
            data=self.origin)
        destination = ShipmentAddress(
            data=self.destination)

        # TODO: Simplify the mapping here
        package = ShipmentPackage({
            'dimensions': self.dimensions,
            'insured_value': {
                'amount': self.insured_value
            },
            'weight': {
                'value': self.weight
            }
        })

        model = {
            'service_code': self.service_code,
            'ship_from': origin.to_shipengine_address(),
            'ship_to': destination.to_shipengine_address(),
            'insurance_provider': self.insurance_provider,
            'packages': [package.to_shipengine_package()]
        }

        result = {
            'shipments': [model]
        }

        logger.info('Shipment create model')
        logger.info(result)

        return result


class ShipmentAddress(Serializable):
    def __init__(self, data):
        self.name = data.get('name')
        self.company_name = data.get('company_name')
        self.address_one = data.get('address_line1') or data.get('address_one')
        self.city_locality = data.get('city_locality')
        self.state_province = data.get('state_province')
        self.zip_code = data.get('postal_code') or data.get('zip_code')
        self.country_code = data.get('country_code')
        self.phone = data.get('phone')

    def to_shipengine_address(self):
        return {
            'name': self.name,
            'company_name': self.company_name,
            'address_line1': self.address_one,
            'city_locality': self.city_locality,
            'state_province': self.state_province,
            'postal_code': self.zip_code,
            'country_code': self.country_code,
            'phone': self.phone
        }

    def to_dict(self):
        return self.to_json()

    @deprecated
    def to_json(self):
        return {
            'name': self.name,
            'company_name': self.company_name,
            'address_one': self.address_one,
            'city_locality': self.city_locality,
            'state_province': self.state_province,
            'zip_code': self.zip_code,
            'country_code': self.country_code,
            'phone': self.phone
        }


class ShipmentPackage(Serializable):
    def __init__(self, data=None, **kwargs):
        if data is None:
            data = kwargs

        self.weight = data.get('weight') if isinstance(
            data.get('weight'), int) else data.get('weight').get('value')

        self.length = data.get('length') if isinstance(
            data.get('length'), int) else data.get('dimensions').get('length')
        self.width = data.get('width') if isinstance(
            data.get('width'), int) else data.get('dimensions').get('width')
        self.height = data.get('height') if isinstance(
            data.get('height'), int) else data.get('dimensions').get('height')

        self.insured_value = data.get('insured_value') if isinstance(
            data.get('height'), int) else data.get('insured_value').get('amount')

    def to_shipengine_package(self):
        return {
            'weight': {
                'value': int(self.weight),
                'unit': 'pound'
            },
            'dimensions': {
                'length': int(self.length),
                'width': int(self.width),
                'height': int(self.height),
                'unit': 'inch'
            },
            'insured_value': {
                'amount': float(self.insured_value),
                'currency': 'usd'
            }
        }

    def __str__(self):
        return self.to_json()

    def to_dict(self):
        return self.to_json()

    @deprecated
    def to_json(self):
        return {
            'weight': self.weight,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'insured_value': self.insured_value
        }
