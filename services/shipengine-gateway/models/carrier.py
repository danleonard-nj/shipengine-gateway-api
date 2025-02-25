from typing import Dict

from deprecated import deprecated
from framework.serialization import Serializable


class CarrierServiceModel(Serializable):
    def __init__(
        self,
        data: Dict
    ):
        self.service_code = data.get('service_code')
        self.name = data.get('name')

    def to_dict(self):
        return self.to_json()

    @deprecated
    def to_json(self):
        return {
            'service_code': self.service_code,
            'name': self.name
        }


class Carrier(Serializable):
    def __init__(
        self,
        data: Dict
    ):
        self.carrier_id = data.get('carrier_id')
        self.carrier_code = data.get('carrier_code')
        self.name = data.get('friendly_name')
        self.account_number = data.get('account_number')
        self.balance = data.get('balance')
        self.services = [CarrierServiceModel(data=service)
                         for service in data.get('services')
                         if data.get('services') is not None]

    def to_dict(
        self
    ) -> Dict:
        return {
            'carrier_id': self.carrier_id,
            'carrier_code': self.carrier_code,
            'name': self.name,
            'account_number': self.account_number,
            'balance': self.balance,
            'services': [x.to_json() for x
                         in self.services]
        }
