import asyncio
from typing import Dict

from framework.clients.cache_client import CacheClientAsync
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger

from clients.shipengine_client import ShipEngineClient
from constants.cache import CacheKey
from models.rate import Rate, ShipmentRate
from services.carrier_service import CarrierService

logger = get_logger(__name__)


class RateService:
    def __init__(
        self,
        carrier_service: CarrierService,
        shipengine_client: ShipEngineClient,
        cache_client: CacheClientAsync
    ):
        ArgumentNullException.if_none(carrier_service, 'carrier_service')
        ArgumentNullException.if_none(shipengine_client, 'shipengine_client')
        ArgumentNullException.if_none(cache_client, 'cache_client')

        self.__client = shipengine_client
        self.__carrier_service = carrier_service
        self.__cache_client = cache_client

    async def get_rates(
        self,
        shipment: Dict
    ) -> Dict:
        logger.info('Get shipment rates')

        # TODO: Just cache the IDs here instead of the entire carrier list?
        logger.info('Fetching carrier list')
        carriers = await self.__get_carriers()

        # Get a list of all distinct carrier IDs to get
        # quotes for
        carrier_ids = [
            x.get('carrier_id')
            for x in carriers
        ]

        logger.info(f'Carrier IDs to run rate against: {carrier_ids}')

        model = ShipmentRate().from_json(
            data=shipment,
            carrier_ids=carrier_ids)
        model.validate()

        rate_request = model.to_shipment_json()
        rates = await self.__client.get_rates(
            shipment=rate_request)

        rate_response = rates.get('rate_response')
        rate_details = rate_response.get('rates')

        carrier_rate_errors = {
            error.get('carrier_id'): self.to_rate_error(error)
            for error in rate_response.get('errors')
        }

        results = [
            Rate(rate, carrier_rate_errors).to_rate()
            for rate in rate_details
        ]

        carrier_rates = {}
        for rate in results:
            carrier_id = rate.get('carrier').get('carrier_id')
            if carrier_rates.get(carrier_id) is None:
                carrier_rates[carrier_id] = []

            carrier_rate = carrier_rates[carrier_id]
            carrier_rate.append(rate)
            carrier_rates[carrier_id] = carrier_rate

        return {
            'quotes': carrier_rates,
            'errors': carrier_rate_errors
        }

    def to_rate_error(
        self,
        error: Dict
    ) -> Dict:
        return {
            "error_code": error.get('error_code'),
            "error_source": error.get('error_source'),
            "error_type": error.get('error_type'),
            "message": error.get('message')
        }

    async def __get_carriers(
        self
    ):
        cache_key = CacheKey.get_carrier_list()
        logger.info(f'Fetch carriers @ key: {cache_key}')

        cached_carriers = await self.__cache_client.get_json(
            key=cache_key)

        if cached_carriers is not None:
            logger.info('Returning cached carrier list')
            return cached_carriers

        logger.info(f'Fetching carriers from carrier service')
        carriers = await self.__carrier_service.get_carriers()

        # Cache async for one week
        asyncio.create_task(self.__cache_client.set_json(
            key=cache_key,
            value=carriers,
            ttl=60))

        return carriers
