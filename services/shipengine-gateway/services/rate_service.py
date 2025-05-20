import asyncio
from typing import Optional


from clients.shipengine_client import ShipEngineClient
from constants.cache import CacheKey
from framework.clients.cache_client import CacheClientAsync
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from models.rate import convert_to_shipengine_rates_payload, transform_to_estimate_response_shape
from models.requests import RateEstimateRequest
from services.carrier_service import CarrierService
from pydantic import BaseModel

from services.shipment_service import ShipmentService


logger = get_logger(__name__)


def to_rate_error(error: dict):
    class RateError(BaseModel):
        error_code: Optional[str]
        error_source: Optional[str]
        error_type: Optional[str]
        message: Optional[str]

    return RateError(
        error_code=error.get('error_code'),
        error_source=error.get('error_source'),
        error_type=error.get('error_type'),
        message=error.get('message')
    ).model_dump()


class RateService:
    def __init__(
        self,
        carrier_service: CarrierService,
        shipengine_client: ShipEngineClient,
        cache_client: CacheClientAsync,
        shipment_service: ShipmentService
    ):
        ArgumentNullException.if_none(carrier_service, 'carrier_service')
        ArgumentNullException.if_none(shipengine_client, 'shipengine_client')
        ArgumentNullException.if_none(cache_client, 'cache_client')
        ArgumentNullException.if_none(shipment_service, 'shipment_service')

        self._client = shipengine_client
        self._carrier_service = carrier_service
        self._cache_client = cache_client
        self._shipment_service = shipment_service

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

    async def get_rates(
        self,
        rate_request: dict
    ) -> dict:

        available_carriers = await self._get_carriers()
        available_carriers = [
            carrier.get('carrier_id') for carrier in available_carriers
        ]

        downstream_request = convert_to_shipengine_rates_payload(
            raw=rate_request,
            carrier_ids=available_carriers
        )

        rates = await self._client.get_rates(
            rate_request=downstream_request.to_dict()
        )

        # Keeping the shape the same as the one in the estimate for the frontend
        result = transform_to_estimate_response_shape(
            rate_response=rates
        )

        # This creates a new shipment in the system that we have to wipe
        await self._shipment_service.cancel_shipment(
            shipment_id=rates.get('shipment_id')
        )

        return result

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
