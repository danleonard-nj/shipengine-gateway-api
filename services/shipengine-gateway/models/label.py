from typing import Dict
from deprecated import deprecated
from framework.serialization import Serializable
from models.mapping import (label_status_mapping, mapped_value,
                            tracking_status_mapping)


class Label(Serializable):
    def __init__(
        self,
        data: Dict
    ):
        self.label_id = data.get('label_id')
        self.shipment_id = data.get('shipment_id')
        self.carrier_code = data.get('carrier_code')
        self.carrier_id = data.get('carrier_id')
        self.service_code = data.get('service_code')
        self.ship_date = data.get('ship_date')
        self.created_date = data.get('created_at')
        self.insurance_cost = data.get('insurance_cost').get('amount')
        self.download_pdf = data.get('label_download').get('pdf')
        self.download_png = data.get('label_download').get('png')
        self.shipment_cost = data.get('shipment_cost').get('amount')
        self.status = mapped_value(
            mapping=label_status_mapping,
            value=data.get('status'))
        self.tracking_number = data.get('tracking_number')
        self.tracking_status = mapped_value(
            mapping=tracking_status_mapping,
            value=data.get('tracking_status'))
        self.tracking_url = self.__get_tracking_url(
            tracking_number=data.get('tracking_number'))
        self.voided = data.get('voided')
        self.voided_date = data.get('voided_at')

    def __get_tracking_url(
        self,
        tracking_number: str
    ):
        return f'https://wwwapps.ups.com/WebTracking/track?track=yes&trackNums={tracking_number}'

    def to_dict(
        self
    ) -> Dict:
        return self.to_json()

    @deprecated
    def to_json(
        self
    ) -> Dict:
        return self.__dict__
