from datetime import datetime
from typing import Dict

from deprecated import deprecated
from framework.logger.providers import get_logger
from framework.serialization import Serializable
from models.carrier import Carrier
from models.mapping import mapped_value, shipment_status_mapping

logger = get_logger(__name__)


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
    def __init__(
        self,
        weight: int | float,
        length: int | float,
        width: int | float,
        height: int | float,
        insured_value: int | float,
    ):
        self.weight = weight
        self.length = length
        self.width = width
        self.height = height
        self.insured_value = insured_value

    @staticmethod
    def from_data(
        data=None,
        **kwargs
    ):
        if data is None:
            data = kwargs

        weight = data.get('weight') if isinstance(
            data.get('weight'), int) else data.get('weight').get('value')

        length = data.get('length') if isinstance(
            data.get('length'), int) else data.get('dimensions', dict()).get('length')
        width = data.get('width') if isinstance(
            data.get('width'), int) else data.get('dimensions', dict()).get('width')
        height = data.get('height') if isinstance(
            data.get('height'), int) else data.get('dimensions', dict()).get('height')

        insured_value = data.get('insured_value') if isinstance(
            data.get('height'), int) else data.get('insured_value').get('amount')

        return ShipmentPackage(
            weight=weight,
            length=length,
            width=width,
            height=height,
            insured_value=insured_value
        )

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
        return self.to_dict()

    def to_dict(self):
        return {
            'weight': self.weight,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'insured_value': self.insured_value
        }


def parse_packages(package_data):
    return [
        ShipmentPackage.from_data(data=package)
        for package in package_data
    ]


class Shipment(Serializable):
    def __init__(
        self,
        shipment_id: str,
        carrier_id: str,
        created_date: str | datetime,
        packages: list[ShipmentPackage],
        return_address: ShipmentAddress,
        service_code: str,
        ship_date: str,
        origin: ShipmentAddress,
        destination: ShipmentAddress,
        shipment_status: str,
        total_weight: float,
        sync_date: str | datetime,
        service_code_mapping: dict = None,
        carrier_mapping: dict = None
    ):
        self.shipment_id = shipment_id
        self.carrier_id = carrier_id
        self.created_date = created_date
        self.packages = packages
        self.return_address = return_address
        self.service_code = service_code
        self.ship_date = ship_date
        self.origin = origin
        self.destination = destination
        self.shipment_status = shipment_status
        self.total_weight = total_weight
        self.sync_date = sync_date

        self.carrier_name = ''
        self.service_code_name = ''

        if service_code_mapping is not None:
            self.service_code_name = self._get_mapped_service_code(
                mapping=service_code_mapping)
        if carrier_mapping is not None:
            self.carrier_name = self._get_mapped_carrier(
                mapping=carrier_mapping)

    @staticmethod
    def from_data(
        data: dict,
        service_code_mapping: dict = None,
        carrier_mapping: dict = None
    ):
        return_address = ShipmentAddress(
            data=data.get('return_to'))

        origin = ShipmentAddress(
            data=data.get('ship_from'))
        destination = ShipmentAddress(
            data=data.get('ship_to'))

        packages = parse_packages(
            data.get('packages', []))

        return Shipment(
            shipment_id=data.get('shipment_id'),
            carrier_id=data.get('carrier_id'),
            created_date=data.get('created_at'),
            packages=packages,
            return_address=return_address,
            service_code=data.get('service_code'),
            ship_date=data.get('ship_date'),
            origin=origin,
            destination=destination,
            shipment_status=shipment_status_mapping.get(
                data.get('shipment_status')),
            total_weight=data.get('total_weight').get('value'),
            sync_date=data.get('sync_date'),
            service_code_mapping=service_code_mapping,
            carrier_mapping=carrier_mapping
        )

    @staticmethod
    def from_entity(
        data: dict,
        service_code_mapping: dict = None,
        carrier_mapping: dict = None
    ) -> 'Shipment':
        return_address = ShipmentAddress(
            data=data.get('return_address'))

        origin = ShipmentAddress(
            data=data.get('origin'))
        destination = ShipmentAddress(
            data=data.get('destination'))

        packages = []
        for package in data.get('packages', []):
            model = ShipmentPackage(
                weight=package.get('weight'),
                length=package.get('length'),
                width=package.get('width'),
                height=package.get('height'),
                insured_value=package.get('insured_value')
            )
            packages.append(model)

        shipment = Shipment(
            shipment_id=data.get('shipment_id'),
            carrier_id=data.get('carrier_id'),
            created_date=data.get('created_date'),
            packages=packages,
            return_address=return_address,
            service_code=data.get('service_code'),
            ship_date=data.get('ship_date'),
            origin=origin,
            destination=destination,
            shipment_status=data.get('shipment_status'),
            total_weight=data.get('total_weight'),
            sync_date=data.get('sync_date'),
            service_code_mapping=service_code_mapping,
            carrier_mapping=carrier_mapping
        )

        return shipment

    def _get_mapped_service_code(self, mapping):
        if self.service_code is None:
            logger.info(f'Service code is None: {self.to_dict()}')
            return 'n/a'

        return [mapping.get(self.service_code, 'n/a')]

    def _get_mapped_carrier(self, mapping):
        mapped_carrier = mapped_value(
            mapping=mapping,
            value=self.carrier_id)

        if isinstance(mapped_carrier, dict):
            return mapped_carrier.get('name', 'n/a')
        if isinstance(mapped_carrier, Carrier):
            return mapped_carrier.name
        else:
            return 'n/a'

    def get_selector(
        self
    ) -> dict:
        return {
            'shipment_id': self.shipment_id
        }

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

    def to_dict(
        self
    ) -> Dict:

        return {
            'id': self.shipment_id,
            'carrier_id': self.carrier_id,
            'carrier_name': self.carrier_name.carrier if isinstance(
                self.carrier_name, Carrier) else self.carrier_name,
            'created_date': self.created_date,
            'packages': [package.to_dict() for package in self.packages],
            'return_address': self.return_address.to_json(),
            'service_code': self.service_code,
            'service_code_name': self.service_code_name,
            'ship_date': self.ship_date,
            'origin': self.origin.to_json(),
            'destination': self.destination.to_json(),
            'shipment_status': self.shipment_status,
            'total_weight': self.total_weight,
        }

    def to_entity(
        self
    ) -> dict:
        carrier_name = self.carrier_name.name if isinstance(
            self.carrier_name, Carrier) else self.carrier_name

        return {
            'shipment_id': self.shipment_id,
            'carrier_id': self.carrier_id,
            'carrier_name': carrier_name,
            'created_date': self.created_date,
            'packages': [package.to_dict() for package in self.packages],
            'return_address': self.return_address.to_json(),
            'service_code': self.service_code,
            'service_code_name': self.service_code_name,
            'ship_date': self.ship_date,
            'origin': self.origin.to_json(),
            'destination': self.destination.to_json(),
            'shipment_status': self.shipment_status,
            'total_weight': self.total_weight,
            'sync_date': datetime.now()
        }


class CreateShipment(Serializable):
    def __init__(self, data):
        self.carrier_id = data.get('carrier_id')
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
        package = ShipmentPackage.from_data({
            'dimensions': self.dimensions,
            'insured_value': {
                'amount': self.insured_value
            },
            'weight': {
                'value': self.weight
            }
        })

        model = {
            'carrier_id': self.carrier_id,
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
