

class CacheKey:
    CARRIER_LIST = 'shipengine-carrier-list'

    @staticmethod
    def get_carrier_list():
        return 'shipengine-carrier-list'

    @staticmethod
    def get_carrier_service_codes():
        return 'shipengine-carrier-service-code-list'
