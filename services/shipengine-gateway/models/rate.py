from typing import Dict, List

from deprecated import deprecated
from framework.logger.providers import get_logger
from framework.serialization import Serializable
from domain.exceptions import InvalidOriginException
from models.shipment import ShipmentAddress, ShipmentPackage
from services.fields import Field, FieldClass
from framework.exceptions.nulls import ArgumentNullException
from framework.validators.nulls import none_or_whitespace

logger = get_logger(__name__)


class Rate:
    def __init__(
        self,
        rate,
        errors_by_carrier
    ):
        self.rate = rate
        self.errors = errors_by_carrier

    def to_rate_carrier(
        self
    ) -> Dict:
        return {
            'carrier_id': self.rate.get('carrier_id'),
            'carrier_code': self.rate.get('carrier_code'),
            'carrier_name': self.rate.get('carrier_friendly_name'),
            'service_type': self.rate.get('service_type'),
            'service_code': self.rate.get('service_code'),
            'package_type': self.rate.get('package_type')
        }

    def to_rate_cost(
        self
    ):
        logger.info(f'Mapping to rate cost: {self.rate}')

        # Get the costs for the carrier quote
        confirmation_amount = self.rate.get(
            'confirmation_amount', dict()).get('amount') or 0

        insurance_amount = self.rate.get(
            'insurance_amount', dict()).get('amount') or 0

        other_amount = self.rate.get(
            'other_amount', dict()).get('amount') or 0

        shipping_amount = self.rate.get(
            'shipping_amount', dict()).get('amount') or 0

        total_amount = round((confirmation_amount
                              + insurance_amount
                              + other_amount
                              + shipping_amount), 2)

        logger.info(f'Total calculated amount: {total_amount}')

        return {
            'confirmation_amount': confirmation_amount,
            'insurance_amount': insurance_amount,
            'other_amount': other_amount,
            'shipping_amount': shipping_amount,
            'total_amount': total_amount
        }

    def to_rate_validation(self):
        carrier_id = self.rate.get('carrier_id')
        return {
            'status': self.rate.get('validation_status'),
            'warnings': self.rate.get('warning_messages'),
            'error': self.errors.get(carrier_id)
        }

    def to_rate(
        self
    ):
        return {
            'rate_id': self.rate.get('rate_id'),
            'ship_date': self.rate.get('ship_date'),
            'delivery_date': self.rate.get('estimated_delivery_date'),
            'transit_time': self.rate.get('delivery_days'),
            'validation': self.to_rate_validation(),
            'carrier': self.to_rate_carrier(),
            'cost': self.to_rate_cost()
        }


@deprecated
class ShipmentRate(FieldClass, Serializable):
    def from_json(self, data, carrier_ids):
        self.shipper_id = Field(
            name='shipper_id',
            _type=(int, str),
            value=data.get('shipper_id'))
        self.origin = Field(
            name='origin',
            _type=dict,
            value=data.get('origin'))
        self.destination = Field(
            name='destination',
            value=data.get('destination'),
            _type=dict,
            required=True)
        self.length = Field(
            name='length',
            _type=(float, int),
            value=data.get('length'),
            required=True)
        self.width = Field(
            name='width',
            _type=(float, int),
            value=data.get('width'),
            required=True)
        self.height = Field(
            name='height',
            _type=(float, int),
            value=data.get('height'))
        self.weight = Field(
            name='weight',
            _type=(float, int),
            value=data.get('weight'),
            required=True)
        self.insured_value = Field(
            name='insured_value',
            _type=(float, int),
            value=data.get('insured_value'),
            required=True)
        self.service_code = Field(
            name='service_code',
            _type=str,
            value=data.get('service_code'),
            required=True)
        self.insurance_provider = Field(
            name='insurance_provider',
            _type=str,
            value=data.get('insurance_provider'),
            required=True)
        self.carrier_ids = Field(
            name='carrier_ids',
            _type=list,
            value=carrier_ids,
            required=True)

        self.create_backing_fields()
        return self

    def validate(self):
        logger.info('Validating shipper and origin')
        logger.info(f'Origin: {self.origin}')
        logger.info(f'Shipper: {self.shipper_id}')

        if self.shipper_id is None and self.origin is None:
            raise Exception(
                'Either a shipper ID or an origin address is required')

        super().validate()

    def to_shipment_json(self):
        origin = ShipmentAddress(self.origin)
        destination = ShipmentAddress(self.destination)

        package = ShipmentPackage(
            length=self.length,
            width=self.width,
            height=self.height,
            weight=self.weight,
            insured_value=self.insured_value)

        model = {
            'service_code': self.service_code,
            'ship_from': origin.to_shipengine_address(),
            'ship_to': destination.to_shipengine_address(),
            'insurance_provider': self.insurance_provider,
            'packages': [package.to_shipengine_package()]
        }

        return {
            'shipment': model,
            'rate_options': {
                'carrier_ids': self.carrier_ids
            }
        }

    def to_dict(
        self
    ) -> Dict:
        return self.to_json()

    @deprecated
    def to_json(self):
        result = {
            'shipments': [self.to_shipment_json()]
        }

        logger.info('Shipment create model')
        logger.info(to_json(result))

        return result


class CarrierRate(FieldClass, Serializable):
    def __init__(
        self,
        shipper_id: str,
        origin: str,
        destination: str,
        length: int,
        width: int,
        height: int,
        weight: int,
        insured_value: float,
        service_code: str,
        insurance_provider,
        carrier_ids: List[str]
    ):
        self.shipper_id = shipper_id
        self.origin = origin
        self.destination = destination
        self.length = length
        self.width = width
        self.height = height
        self.weight = weight
        self.insured_value = insured_value
        self.service_code = service_code
        self.insurance_provider = insurance_provider
        self.carrier_ids = carrier_ids

    @classmethod
    def from_json(
        self,
        data: Dict,
        carrier_ids
    ):
        ArgumentNullException.if_none(data, 'data')
        ArgumentNullException.if_none(carrier_ids, 'carrier_ids')

        return CarrierRate(
            shipper_id=data.get('shipper_id'),
            origin=data.get('origin'),
            destination=data.get('destination'),
            length=data.get('length'),
            width=data.get('width'),
            height=data.get('height'),
            weight=data.get('weight'),
            insured_value=data.get('insured_value'),
            service_code=data.get('service_code'),
            insurance_provider=data.get('insurance_provider'),
            carrier_ids=carrier_ids)

    def validate(
        self
    ):
        logger.info('Validating shipper and origin')
        logger.info(f'{self.origin} -> {self.shipper_id}')

        # Validate the shipping ID / origin is provided
        if (none_or_whitespace(self.shipper_id)
                and none_or_whitespace(self.origin)):
            logger.info(
                f'Invalid origin or shipper ID provided')
            raise InvalidOriginException()

        super().validate()

    def to_shipment_json(
        self
    ):
        origin = ShipmentAddress(self.origin)
        destination = ShipmentAddress(self.destination)

        package = ShipmentPackage(
            length=self.length,
            width=self.width,
            height=self.height,
            weight=self.weight,
            insured_value=self.insured_value)

        model = {
            'service_code': self.service_code,
            'ship_from': origin.to_shipengine_address(),
            'ship_to': destination.to_shipengine_address(),
            'insurance_provider': self.insurance_provider,
            'packages': [package.to_shipengine_package()]
        }

        return {
            'shipment': model,
            'rate_options': {
                'carrier_ids': self.carrier_ids
            }
        }

    def to_dict(
        self
    ) -> Dict:
        return self.to_json()

    @deprecated
    def to_json(self):
        result = {
            'shipments': [self.to_shipment_json()]
        }

        logger.info('Shipment create model')
        logger.info(to_json(result))

        return result
