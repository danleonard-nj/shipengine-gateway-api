from framework.logger.providers import get_logger
from framework.rest.blueprints.meta import MetaBlueprint

from services.carrier_service import CarrierService

logger = get_logger(__name__)
carrier_bp = MetaBlueprint('carrier_bp', __name__)


@carrier_bp.configure('/api/carriers', methods=['GET'], auth_scheme='read')
async def get_carriers(container):
    carrier_service: CarrierService = container.resolve(
        CarrierService)

    response = await carrier_service.get_carriers()
    return {'carriers': response}


@carrier_bp.configure('/api/carriers/balances', methods=['GET'], auth_scheme='read')
async def get_balances(container):
    carrier_service: CarrierService = container.resolve(
        CarrierService)

    response = await carrier_service.get_balances()
    return response


@carrier_bp.configure('/api/carriers/services', methods=['GET'], auth_scheme='read')
async def get_service_codes(container):
    carrier_service: CarrierService = container.resolve(
        CarrierService)

    response = await carrier_service.get_service_codes()
    return response
