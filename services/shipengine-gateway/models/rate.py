from pydantic import BaseModel
from typing import List, Optional
from framework.serialization import Serializable


class Address(BaseModel):
    name: str
    phone: str
    company_name: Optional[str] = ""
    address_line1: str
    city_locality: str
    state_province: str
    postal_code: str
    country_code: str
    address_residential_indicator: str = "no"


class Weight(BaseModel):
    value: float
    unit: str = "pound"


class InsuredValue(BaseModel):
    currency: str = "usd"
    amount: float


class Package(BaseModel):
    package_code: str = "package"
    weight: Weight
    insured_value: Optional[InsuredValue] = None


class Shipment(BaseModel):
    validate_address: str = "no_validation"
    ship_to: Address
    ship_from: Address
    packages: List[Package]


class RateOptions(BaseModel):
    carrier_ids: List[str]


class ShipEngineRateRequest(BaseModel, Serializable):
    rate_options: RateOptions
    shipment: Shipment

    def to_dict(self):
        return self.model_dump()


def convert_to_shipengine_rates_payload(raw: dict, carrier_ids: list[str]) -> ShipEngineRateRequest:
    destination = raw["destination"]
    origin = raw["origin"]

    ship_to = Address(
        name=destination["name"],
        phone=destination["phone"],
        company_name=destination.get("company_name") or "",
        address_line1=destination["address_one"],
        city_locality=destination["city_locality"],
        state_province=destination["state_province"],
        postal_code=destination["zip_code"],
        country_code=destination["country_code"]
    )

    ship_from = Address(
        name=origin["name"],
        phone=origin["phone"],
        company_name=origin.get("company_name") or "",
        address_line1=origin["address_one"],
        city_locality=origin["city_locality"],
        state_province=origin["state_province"],
        postal_code=origin["zip_code"],
        country_code=origin["country_code"]
    )

    package = Package(
        weight=Weight(value=raw["total_weight"]),
        insured_value=InsuredValue(amount=200)
    )

    carrier_ids = carrier_ids or []

    return ShipEngineRateRequest(
        rate_options=RateOptions(carrier_ids=carrier_ids),
        shipment=Shipment(
            ship_to=ship_to,
            ship_from=ship_from,
            packages=[package]
        )
    )


def transform_to_estimate_response_shape(rate_response: dict) -> list[dict]:
    rates = rate_response.get("rate_response", {}).get("rates", [])
    transformed = []

    carrier_friendly_name = rate.get("carrier_friendly_name")
    if rate.get('carrier_id') == 'se-485981':
        carrier_friendly_name = "UPS (Billed Thru Ship Engine)"

    for rate in rates:
        transformed.append({
            "carrier_code": rate.get("carrier_code"),
            "carrier_delivery_days": rate.get("carrier_delivery_days"),
            "carrier_friendly_name": carrier_friendly_name,
            "carrier_id": rate.get("carrier_id"),
            "carrier_nickname": rate.get("carrier_nickname"),
            "confirmation_amount": rate.get("confirmation_amount"),
            "delivery_days": rate.get("delivery_days"),
            "display_scheme": rate.get("display_scheme"),
            "error_messages": rate.get("error_messages", []),
            "estimated_delivery_date": rate.get("estimated_delivery_date"),
            "guaranteed_service": rate.get("guaranteed_service"),
            "insurance_amount": rate.get("insurance_amount"),
            "negotiated_rate": rate.get("negotiated_rate"),
            "other_amount": rate.get("other_amount"),
            "package_type": rate.get("package_type"),
            "rate_details": rate.get("rate_details", []),
            "rate_type": "check",
            "requested_comparison_amount": rate.get("requested_comparison_amount"),
            "service_code": rate.get("service_code"),
            "service_type": rate.get("service_type"),
            "ship_date": rate.get("ship_date"),
            "shipping_amount": rate.get("shipping_amount"),
            "trackable": rate.get("trackable"),
            "validation_status": "unknown",  # override
            "warning_messages": rate.get("warning_messages", []),
            "zone": rate.get("zone"),
        })

    return transformed
