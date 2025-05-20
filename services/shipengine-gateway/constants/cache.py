import json
from framework.crypto.hashing import sha256


class CacheKey:
    @staticmethod
    def get_carrier_list():
        return 'shipengine-carrier-list'

    @staticmethod
    def get_carrier_service_codes():
        return 'shipengine-carrier-service-code-list'

    @staticmethod
    def get_estimate(shipment):
        hash_key = sha256(json.dumps(shipment, sort_keys=True))
        return f'shipengine-estimate-{hash_key}'

    @staticmethod
    def get_label(shipment_id):
        return f'shipengine-label-shipment-id-{shipment_id}'

    @staticmethod
    def get_address_list():
        return 'shipengine-address-list'

    @staticmethod
    def get_default_address():
        return 'shipengine-default-address'
