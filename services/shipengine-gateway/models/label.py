from dataclasses import dataclass
from typing import Dict, Optional

from framework.serialization import Serializable
from models.mapping import label_status_mapping, tracking_status_mapping
from utilities.utils import ValidatableDataclass


def get_tracking_url(
    tracking_number: str
):
    return f'https://wwwapps.ups.com/WebTracking/track?track=yes&trackNums={tracking_number}'


@dataclass
class Label(ValidatableDataclass, Serializable):
    label_id: str
    shipment_id: str
    carrier_code: str
    carrier_id: str
    service_code: str
    ship_date: str
    created_date: str
    insurance_cost: float
    download_pdf: str
    download_png: str
    shipment_cost: float
    status: str
    tracking_number: str
    tracking_status: str
    tracking_url: str
    voided: bool
    voided_date: Optional[str]

    @staticmethod
    def from_data(data: Dict) -> "Label":
        return Label(
            label_id=data.get('label_id'),
            shipment_id=data.get('shipment_id'),
            carrier_code=data.get('carrier_code'),
            carrier_id=data.get('carrier_id'),
            service_code=data.get('service_code'),
            ship_date=data.get('ship_date'),
            created_date=data.get('created_at'),
            insurance_cost=data.get('insurance_cost').get('amount'),
            download_pdf=data.get('label_download').get('pdf'),
            download_png=data.get('label_download').get('png'),
            shipment_cost=data.get('shipment_cost').get('amount'),
            status=label_status_mapping.get(data.get('status', 'n/a'), 'n/a'),
            tracking_number=data.get('tracking_number'),
            tracking_status=tracking_status_mapping.get(data.get('tracking_status', 'n/a'), 'n/a'),
            tracking_url=get_tracking_url(tracking_number=data.get('tracking_number')),
            voided=data.get('voided'),
            voided_date=data.get('voided_at')
        )

    @staticmethod
    def from_dict(data: dict) -> "Label":
        return Label(
            label_id=data.get('label_id'),
            shipment_id=data.get('shipment_id'),
            carrier_code=data.get('carrier_code'),
            carrier_id=data.get('carrier_id'),
            service_code=data.get('service_code'),
            ship_date=data.get('ship_date'),
            created_date=data.get('created_date'),
            insurance_cost=data.get('insurance_cost'),
            download_pdf=data.get('download_pdf'),
            download_png=data.get('download_png'),
            shipment_cost=data.get('shipment_cost'),
            status=data.get('status'),
            tracking_number=data.get('tracking_number'),
            tracking_status=data.get('tracking_status'),
            tracking_url=data.get('tracking_url'),
            voided=data.get('voided'),
            voided_date=data.get('voided_date')
        )
