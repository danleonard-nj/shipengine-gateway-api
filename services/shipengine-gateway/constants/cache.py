import json
from framework.crypto.hashing import sha256


class CacheKey:
    CARRIER_LIST = 'shipengine-carrier-list'

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
