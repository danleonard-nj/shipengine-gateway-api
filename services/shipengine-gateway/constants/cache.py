

class CacheKey:
    CARRIER_LIST = 'shipengine-carrier-list'

    @classmethod
    def get_carrier_list():
        return 'shipengine-carrier-list'

    @classmethod
    def get_carrier_service_codes():
        return 'shipengine-carrier-service-code-list'
