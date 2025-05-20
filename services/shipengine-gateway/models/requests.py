from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from framework.serialization import Serializable


@dataclass
class GetShipmentRequest(Serializable):
    shipengine_model: bool
    page_number: int = 1
    page_size: int = 25
    cancelled: bool = False

    @classmethod
    def from_request(cls, request: Any) -> "GetShipmentRequest":
        return cls(
            shipengine_model=request.args.get('shipengine_model') == 'true',
            page_number=int(request.args.get('page_number') or 1),
            page_size=int(request.args.get('page_size') or 25),
            cancelled=request.args.get('cancelled', 'false') == 'true',
        )


@dataclass
class RateEstimateRequest(Serializable):
    carrier_ids: list
    from_country_code: Optional[str] = None
    from_postal_code: Optional[str] = None
    from_city_locality: Optional[str] = None
    from_state_province: Optional[str] = None
    to_country_code: Optional[str] = None
    to_postal_code: Optional[str] = None
    to_city_locality: Optional[str] = None
    to_state_province: Optional[str] = None
    weight: dict = field(default_factory=dict)
    dimensions: dict = field(default_factory=dict)

    @classmethod
    def from_shipment(cls, shipment: dict, carrier_ids: list) -> "RateEstimateRequest":
        origin = shipment.get('origin', {})
        destination = shipment.get('destination', {})
        return cls(
            carrier_ids=carrier_ids,
            from_country_code=origin.get('country_code'),
            from_postal_code=origin.get('zip_code'),
            from_city_locality=origin.get('city_locality'),
            from_state_province=origin.get('state_province'),
            to_country_code=destination.get('country_code'),
            to_postal_code=destination.get('zip_code'),
            to_city_locality=destination.get('city_locality'),
            to_state_province=destination.get('state_province'),
            weight={
                'value': shipment.get('total_weight'),
                'unit': 'pound'
            },
            dimensions={
                'unit': 'inch',
                'length': shipment.get('length'),
                'width': shipment.get('width'),
                'height': shipment.get('height')
            }
        )
