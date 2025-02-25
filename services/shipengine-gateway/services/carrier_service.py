import asyncio
from typing import Dict, List

from framework.clients.cache_client import CacheClientAsync
from framework.logger.providers import get_logger

from clients.shipengine_client import ShipEngineClient
from constants.cache import CacheKey
from models.carrier import Carrier, CarrierServiceModel

logger = get_logger(__name__)

SERVICE_CODE_TTL_MINUTES = 60 * 24 * 7


class CarrierService:
    def __init__(
        self,
        shipengine_client: ShipEngineClient,
        cache_client: CacheClientAsync
    ):
        self.__client = shipengine_client
        self._cache_client = cache_client

    async def get_carrier_models(
        self
    ) -> List[Carrier]:
        logger.info('Parsing carrier models from carrier repsonse')
        carriers = await self._get_carriers()

        return [
            Carrier(data=carrier)
            for carrier in carriers
        ]

    async def get_carriers(
        self
    ) -> Dict:
        logger.info('Get carrier list from ShipEngine')

        carriers = await self._get_carriers()

        models = [
            Carrier(data=carrier)
            for carrier in carriers
        ]

        return [model.to_json() for model in models]

    async def get_carrier_ids(
        self
    ) -> Dict:
        logger.info('Get carrier list from ShipEngine')

        carriers = await self._get_carriers()

        models = [
            Carrier(data=carrier)
            for carrier in carriers
        ]

        return [model.carrier_id for model in models]

    async def get_service_codes(
        self
    ) -> Dict:
        logger.info(f'Fetching carrier list')

        results = await self.__get_service_codes()

        return {
            'service_codes': results
        }

    async def __get_service_codes(
        self
    ) -> Dict:

        key = CacheKey.get_carrier_service_codes()

        cached_codes = await self._cache_client.get_json(
            key=key)

        if cached_codes is not None:
            logger.info('Returning cached carrier service codes')

        logger.info('Calculating carrier service codes')

        service_codes = await self.__parse_carrier_service_codes()

        asyncio.create_task(self._cache_client.set_json(
            key=key,
            value=service_codes,
            ttl=60
        ))

    async def __parse_carrier_service_codes(
        self
    ):
        carriers = await self._get_carriers()

        results = []
        for carrier in carriers:
            services = carrier.get('services', [])

            if services is not None and any(services):
                logger.info(f'Parsing carrier service model: {carrier}')
                for service in services:
                    model = CarrierServiceModel(data=service)
                    results.append(model.to_json())

        return results

    # def __parse_carriers_response(
    #     self,
    #     carriers
    # ):
    #     if not carriers:
    #         raise Exception(f'Failed to fetch carriers from ShipEngine')

    #     results = []
    #     for carrier in carriers:
    #         model = Carrier(data=carrier)
    #         results.append(model.to_json())

    #     return {
    #         'carriers': results
    #     }

    async def get_balances(
        self
    ):
        logger.info('Get carrier balances')

        response = await self.__client.get_carriers()
        carriers = response.get('carriers')

        results = []
        for carrier in carriers:
            model = Carrier(data=carrier)

            results.append({
                'carrier_id': model.carrier_id,
                'carrier_code': model.carrier_code,
                'carrier_name': model.name,
                'balance': model.balance
            })

        return {
            'balances': results
        }

    async def _get_carriers(
        self
    ) -> List[Dict]:
        cached_carriers = await self._cache_client.get_json(
            key=CacheKey.CARRIER_LIST)

        if cached_carriers is not None:
            logger.info('Returning carriers from cache')
            return cached_carriers

        logger.info(f'Fetching carriers from client')
        response = await self.__client.get_carriers()
        carriers = response.get('carriers')

        await self._cache_client.set_json(
            key=CacheKey.CARRIER_LIST,
            value=carriers,
            ttl=60 * 24 * 7)

        return carriers
