from dataclasses import dataclass
from typing import List, Union, Dict, Optional
from typing import Any, Dict
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union, get_args, get_origin

from framework.logger.providers import get_logger
from framework.serialization import Serializable
from models.carrier import Carrier
from models.mapping import mapped_value, shipment_status_mapping
from utilities.utils import ValidatableDataclass

logger = get_logger(__name__)


@dataclass
class ShipmentAddress(ValidatableDataclass, Serializable):
    name: str
    company_name: Optional[str]
    address_one: str
    city_locality: str
    state_province: str
    zip_code: str
    country_code: str
    phone: Optional[str]

    def __post_init__(
        self
    ):
        # Run the generic empty value checks from the base class.
        super().__post_init__()
        # Additional custom validation: enforce that country_code is exactly 2 letters.
        if isinstance(self.country_code, str) and len(self.country_code) != 2:
            raise ValueError("Field 'country_code' must be exactly 2 letters.")

    @staticmethod
    def from_data(
        data: dict[str, Any]
    ) -> "ShipmentAddress":
        return ShipmentAddress(
            name=data.get('name'),
            company_name=data.get('company_name'),
            address_one=data.get('address_line1') or data.get('address_one'),
            city_locality=data.get('city_locality'),
            state_province=data.get('state_province'),
            zip_code=data.get('postal_code') or data.get('zip_code'),
            country_code=data.get('country_code'),
            phone=data.get('phone')
        )

    def to_shipengine_address(
        self
    ) -> dict[str, str]:
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

    def to_dict(
        self
    ) -> dict[str, str]:
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


@dataclass
class ShipmentPackage(ValidatableDataclass, Serializable):
    weight: Union[int, float]
    length: Union[int, float]
    width: Union[int, float]
    height: Union[int, float]
    insured_value: Optional[Union[int, float]]

    @staticmethod
    def from_data(
        data: Dict[str, Any] = None,
        **kwargs
    ) -> "ShipmentPackage":
        if data is None:
            data = kwargs

        weight = (
            data.get('weight')
            if isinstance(data.get('weight'), (int, float))
            else data.get('weight').get('value')
        )

        # Dimensions
        length = (
            data.get('length')
            if isinstance(data.get('length'), (int, float))
            else data.get('dimensions', {}).get('length')
        )
        width = (
            data.get('width')
            if isinstance(data.get('width'), (int, float))
            else data.get('dimensions', {}).get('width')
        )
        height = (
            data.get('height')
            if isinstance(data.get('height'), (int, float))
            else data.get('dimensions', {}).get('height')
        )

        insured_value = (
            data.get('insured_value')
            if isinstance(data.get('insured_value'), (int, float))
            else data.get('insured_value').get('amount')
        )

        return ShipmentPackage(
            weight=weight,
            length=length,
            width=width,
            height=height,
            insured_value=insured_value
        )

    @staticmethod
    def from_entity(
        data: dict
    ):
        return ShipmentPackage(
            weight=data.get('weight'),
            length=data.get('length'),
            width=data.get('width'),
            height=data.get('height'),
            insured_value=data.get('insured_value')
        )

    def to_shipengine_package(
        self
    ) -> Dict[str, Any]:
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

    def to_dict(
        self
    ) -> Dict[str, Union[int, float]]:
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


# Assuming these are defined elsewhere:
# from your_module import Serializable, ShipmentPackage, ShipmentAddress, Carrier, parse_packages, mapped_value, shipment_status_mapping, logger


@dataclass
class Shipment(ValidatableDataclass, Serializable):
    shipment_id: str
    # Cases where a carrier is not selected
    carrier_id: Optional[str]
    created_date: Union[str, datetime]
    packages: List[ShipmentPackage]
    return_address: ShipmentAddress
    # Cases where a carrier / service code is not selected
    service_code: Optional[str]
    ship_date: str
    origin: ShipmentAddress
    destination: ShipmentAddress
    shipment_status: str
    total_weight: float
    sync_date: Union[str, datetime]
    # Mapped on post init
    carrier_name: Optional[str] = ""         # Computed field, defaults to empty
    service_code_name: Optional[str] = ""    # Computed field, defaults to empty

    @staticmethod
    def _get_mapped_service_code(
        service_code: Optional[str],
        mapping: Dict
    ) -> str:
        if service_code is None:
            return 'n/a'
        # Return the mapped service code (as a string, not as a list)
        return mapping.get(service_code, 'n/a')

    @staticmethod
    def _get_mapped_carrier(
        carrier_id: str,
        mapping: Dict
    ) -> str:
        # mapped_carrier = mapped_value(mapping=mapping, value=carrier_id)
        mapped_carrier = mapping.get(carrier_id, 'n/a')
        if isinstance(mapped_carrier, dict):
            return mapped_carrier.get('name', 'n/a')
        if isinstance(mapped_carrier, Carrier):
            return mapped_carrier.name
        return 'n/a'

    @classmethod
    def from_data(
        cls,
        data: dict,
        service_code_mapping: Optional[Dict] = None,
        carrier_mapping: Optional[Dict] = None
    ) -> 'Shipment':
        return_address = ShipmentAddress.from_data(data=data.get('return_to'))
        origin = ShipmentAddress.from_data(data=data.get('ship_from'))
        destination = ShipmentAddress.from_data(data=data.get('ship_to'))
        packages = parse_packages(data.get('packages', []))

        service_code = data.get('service_code')
        carrier_id = data.get('carrier_id')
        shipment_status = shipment_status_mapping.get(data.get('shipment_status', 'n/a'), 'n/a')
        total_weight = data.get('total_weight', dict()).get('value', 0.0)

        service_code_name = (cls._get_mapped_service_code(service_code, service_code_mapping)
                             if service_code_mapping else "")
        carrier_name = (cls._get_mapped_carrier(carrier_id, carrier_mapping)
                        if carrier_mapping else "")

        return Shipment(
            shipment_id=data.get('shipment_id'),
            carrier_id=carrier_id,
            created_date=data.get('created_at'),
            packages=packages,
            return_address=return_address,
            service_code=service_code,
            ship_date=data.get('ship_date'),
            origin=origin,
            destination=destination,
            shipment_status=shipment_status,
            total_weight=total_weight,
            sync_date=data.get('sync_date'),
            service_code_name=service_code_name,
            carrier_name=carrier_name,
        )

    @classmethod
    def from_entity(
        cls,
        data: dict,
        service_code_mapping: Optional[Dict] = None,
        carrier_mapping: Optional[Dict] = None
    ) -> 'Shipment':
        return_address = ShipmentAddress.from_data(data=data.get('return_address'))
        origin = ShipmentAddress.from_data(data=data.get('origin'))
        destination = ShipmentAddress.from_data(data=data.get('destination'))

        packages = []
        for package in data.get('packages', []):
            model = ShipmentPackage.from_entity(data=package)
            packages.append(model)

        shipment_id = data.get('shipment_id')
        carrier_id = data.get('carrier_id')
        service_code = data.get('service_code')
        shipment_status = data.get('shipment_status')
        total_weight = data.get('total_weight')
        created_date = data.get('created_date')
        ship_date = data.get('ship_date')
        sync_date = data.get('sync_date')

        service_code_name = (cls._get_mapped_service_code(service_code, service_code_mapping)
                             if service_code_mapping else "")
        carrier_name = (cls._get_mapped_carrier(carrier_id, carrier_mapping)
                        if carrier_mapping else "")

        return Shipment(
            shipment_id=shipment_id,
            carrier_id=carrier_id,
            created_date=created_date,
            packages=packages,
            return_address=return_address,
            service_code=service_code,
            ship_date=ship_date,
            origin=origin,
            destination=destination,
            shipment_status=shipment_status,
            total_weight=total_weight,
            sync_date=sync_date,
            service_code_name=service_code_name,
            carrier_name=carrier_name,
        )

    def get_selector(self) -> dict:
        return {'shipment_id': self.shipment_id}

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

    def to_dict(self) -> Dict:
        # If carrier_name is a Carrier instance, get its 'carrier' attribute; otherwise use it directly.
        carrier_name_value = (
            self.carrier_name.carrier if isinstance(self.carrier_name, Carrier)
            else self.carrier_name
        )
        return {
            'id': self.shipment_id,
            'carrier_id': self.carrier_id,
            'carrier_name': carrier_name_value,
            'created_date': self.created_date,
            'packages': [package.to_dict() for package in self.packages],
            'return_address': self.return_address.to_dict(),
            'service_code': self.service_code,
            'service_code_name': self.service_code_name,
            'ship_date': self.ship_date,
            'origin': self.origin.to_dict(),
            'destination': self.destination.to_dict(),
            'shipment_status': self.shipment_status,
            'total_weight': self.total_weight,
        }

    def to_entity(self) -> dict:
        # If carrier_name is a Carrier instance, use its 'name' attribute.
        carrier_name_value = (
            self.carrier_name.name if isinstance(self.carrier_name, Carrier)
            else self.carrier_name
        )
        return {
            'shipment_id': self.shipment_id,
            'carrier_id': self.carrier_id,
            'carrier_name': carrier_name_value,
            'created_date': self.created_date,
            'packages': [package.to_dict() for package in self.packages],
            'return_address': self.return_address.to_dict(),
            'service_code': self.service_code,
            'service_code_name': self.service_code_name,
            'ship_date': self.ship_date,
            'origin': self.origin.to_dict(),
            'destination': self.destination.to_dict(),
            'shipment_status': self.shipment_status,
            'total_weight': self.total_weight,
            'sync_date': datetime.now(timezone.utc)
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
        origin = ShipmentAddress.from_data(
            data=self.origin)
        destination = ShipmentAddress.from_data(
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

    # @deprecated
    # def to_json(self):
    #     origin = ShipmentAddress(
    #         data=self.origin)
    #     destination = ShipmentAddress(
    #         data=self.destination)

    #     # TODO: Simplify the mapping here
    #     package = ShipmentPackage.from_data({
    #         'dimensions': self.dimensions,
    #         'insured_value': {
    #             'amount': self.insured_value
    #         },
    #         'weight': {
    #             'value': self.weight
    #         }
    #     })

    #     model = {
    #         'carrier_id': self.carrier_id,
    #         'service_code': self.service_code,
    #         'ship_from': origin.to_shipengine_address(),
    #         'ship_to': destination.to_shipengine_address(),
    #         'insurance_provider': self.insurance_provider,
    #         'packages': [package.to_shipengine_package()]
    #     }

    #     result = {
    #         'shipments': [model]
    #     }

    #     logger.info('Shipment create model')
    #     logger.info(result)

    #     return result
