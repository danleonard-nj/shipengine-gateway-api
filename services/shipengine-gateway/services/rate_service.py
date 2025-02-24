import asyncio
from typing import Optional

from clients.shipengine_client import ShipEngineClient
from constants.cache import CacheKey
from deprecated import deprecated
from framework.clients.cache_client import CacheClientAsync
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from models.rate import Rate, ShipmentRate
from models.requests import RateEstimateRequest
from services.carrier_service import CarrierService

logger = get_logger(__name__)


def to_rate_error(error: dict):
    return {
        "error_code": error.get('error_code'),
        "error_source": error.get('error_source'),
        "error_type": error.get('error_type'),
        "message": error.get('message')
    }


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

        self._client = shipengine_client
        self._carrier_service = carrier_service
        self._cache_client = cache_client

    async def get_estimate(
        self,
        shipment: dict,
        carrier_ids: Optional[list[str] | str] = None
    ):
        logger.info('Get shipment estimate')

        cache_key = CacheKey.get_estimate(shipment)
        cached = await self._cache_client.get_json(
            key=cache_key)

        if cached is not None:
            logger.info('Returning cached estimate')
            return cached

        if carrier_ids is None:
            logger.info('No carrier IDs provided, fetching all carriers')
            carriers = await self._get_carriers()
            carrier_ids = [carrier.get('carrier_id') for carrier in carriers]
        elif isinstance(carrier_ids, str):
            carrier_ids = [carrier_ids.strip()]
        elif isinstance(carrier_ids, list):
            carrier_ids = [carrier.strip() for carrier in carrier_ids]
        else:
            raise ValueError('Invalid carrier IDs provided')

        request = RateEstimateRequest(
            shipment=shipment,
            carrier_ids=carrier_ids)

        data = request.to_dict()

        rates = await self._client.estimate_shipment(
            shipment=data)

        # Cache the estimate for 60 seconds
        asyncio.create_task(
            self._cache_client.set_json(
                key=cache_key,
                value=rates,
                ttl=60
            )
        )

        return rates

    @deprecated
    async def get_rates(
        self,
        shipment: dict
    ) -> dict:
        logger.info('Get shipment rates')

        # TODO: Just cache the IDs here instead of the entire carrier list?
        logger.info('Fetching carrier list')
        carriers = await self._get_carriers()

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
        rates = await self._client.get_rates(
            shipment=rate_request)

        rate_response = rates.get('rate_response')
        rate_details = rate_response.get('rates')

        carrier_rate_errors = {
            error.get('carrier_id'): to_rate_error(error)
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

    async def _get_carriers(
        self
    ):
        cache_key = CacheKey.get_carrier_list()
        logger.info(f'Fetch carriers @ key: {cache_key}')

        cached_carriers = await self._cache_client.get_json(
            key=cache_key)

        if cached_carriers is not None:
            logger.info('Returning cached carrier list')
            return cached_carriers

        logger.info(f'Fetching carriers from carrier service')
        carriers = await self._carrier_service.get_carriers()

        # Cache async for one week
        asyncio.create_task(self._cache_client.set_json(
            key=cache_key,
            value=carriers,
            ttl=60))

        return carriers
