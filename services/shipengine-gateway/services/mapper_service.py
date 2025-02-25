from framework.logger.providers import get_logger

from services.carrier_service import CarrierService

logger = get_logger(__name__)


class MappingKey:
    CarrierServiceCode = 'carrier-service-code'
    Carrier = 'carrier'


class MapperService:
    def __init__(
        self,
        carrier_service: CarrierService
    ):
        self._carrier_service = carrier_service
        self._mapping = dict()

    async def get_carrier_service_code_mapping(
        self
    ):
        if self._mapping.get(MappingKey.CarrierServiceCode) is None:
            logger.info(
                f'Initializing mapping: {MappingKey.CarrierServiceCode}')
            await self._create_carrier_service_code_mapping()
        return self._mapping[MappingKey.CarrierServiceCode]

    async def get_carrier_mapping(
        self
    ):
        if self._mapping.get(MappingKey.Carrier) is None:
            logger.info(
                f'Initializing mapping: {MappingKey.Carrier}')
            await self._create_carrier_mapping()
        return self._mapping[MappingKey.Carrier]

    async def _create_carrier_mapping(
        self
    ):
        logger.info('Building carrier mapping')

        mapping = dict()
        carriers = await self._carrier_service.get_carrier_models()

        for carrier in carriers:
            mapping[carrier.carrier_id] = carrier

        self._mapping[MappingKey.Carrier] = mapping

    async def _create_carrier_service_code_mapping(
        self
    ) -> None:
        logger.info(f'Building carrier service code mapping')

        mapping = dict()
        carriers = await self._carrier_service.get_carrier_models()

        for carrier in carriers:
            logger.info(f'Mapping carrier: {carrier}')

            for service_code in carrier.services:
                logger.info(
                    f'Mapping service code: {service_code.service_code} -> {service_code.name}')
                mapping[service_code.service_code] = service_code.name

        self._mapping[MappingKey.CarrierServiceCode] = mapping
