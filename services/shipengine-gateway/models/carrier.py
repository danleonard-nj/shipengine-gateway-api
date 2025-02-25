from dataclasses import dataclass

from deprecated import deprecated
from framework.serialization import Serializable


class CarrierServiceModel(Serializable):
    @staticmethod
    def from_data(
        data: dict
    ):
        return CarrierServiceModel(
            service_code=data.get('service_code'),
            name=data.get('name'))

    def __init__(
        self,
        service_code: str,
        name: str
    ):
        self.service_code = service_code
        self.name = name

    def to_dict(self):
        return {
            'service_code': self.service_code,
            'name': self.name
        }


@dataclass
class Carrier(Serializable):
    carrier_id: str
    carrier_code: str
    name: str
    account_number: str
    balance: float
    services: list[CarrierServiceModel]

    @staticmethod
    def from_data(data: dict) -> "Carrier":
        return Carrier(
            carrier_id=data.get('carrier_id'),
            carrier_code=data.get('carrier_code'),
            name=data.get('friendly_name') or data.get('name'),
            account_number=data.get('account_number'),
            balance=data.get('balance'),
            services=[
                CarrierServiceModel.from_data(data=service)
                for service in data.get('services', [])
            ]
        )

    def to_dict(self) -> dict:
        return {
            'carrier_id': self.carrier_id,
            'carrier_code': self.carrier_code,
            'name': self.name,
            'account_number': self.account_number,
            'balance': self.balance,
            'services': [service.to_dict() for service in self.services]
        }
