from framework.logger.providers import get_logger
from framework.rest.blueprints.meta import MetaBlueprint
from quart import request
from services.rate_service import RateService

logger = get_logger(__name__)
rates_bp = MetaBlueprint('rates_bp', __name__)


@rates_bp.configure('/api/rates', methods=['POST'], auth_scheme='read')
async def get_rates(container):
    rate_service: RateService = container.resolve(
        RateService)

    data = await request.get_json()
    response = await rate_service.get_rates(
        shipment=data)

    return response


@rates_bp.configure('/api/rates/estimate', methods=['POST'], auth_scheme='read')
async def get_estimate(container):
    rate_service: RateService = container.resolve(
        RateService)

    data = await request.get_json()
    response = await rate_service.get_estimate(
        shipment=data)

    return response
