from framework.logger.providers import get_logger
from framework.rest.blueprints.meta import MetaBlueprint
from models.requests import GetShipmentRequest
from quart import request
from services.shipment_service import ShipmentService

logger = get_logger(__name__)
shipment_bp = MetaBlueprint('shipment_bp', __name__)


def _get_shipment_service(container):
    return container.resolve(ShipmentService)


@shipment_bp.configure('/api/shipment', methods=['GET'], auth_scheme='read')
async def get_shipments(container):
    shipment_service = _get_shipment_service(container)

    shipment_request = GetShipmentRequest.from_request(request)

    logger.info(f'Get shipments: {shipment_request.__dict__}')

    shipments = await shipment_service.get_shipments(
        request=shipment_request)

    return shipments


@shipment_bp.configure('/api/shipment/<shipment_id>', methods=['GET'], auth_scheme='read')
async def get_shipment(container, shipment_id):
    shipment_service = _get_shipment_service(container)

    shipment = await shipment_service.get_shipment(
        shipment_id=shipment_id)

    return shipment


@shipment_bp.configure('/api/shipment', methods=['POST'], auth_scheme='write')
async def post_shipment(container):
    shipment_service = _get_shipment_service(container)

    _content = await request.get_json()

    if not _content:
        raise Exception('Request body cannot be null')

    result = await shipment_service.create_shipment(
        data=_content)

    return result


@shipment_bp.configure('/api/shipment/<shipment_id>/cancel', methods=['PUT'], auth_scheme='write')
async def cancel_shipment(container, shipment_id: str):
    shipment_service = _get_shipment_service(container)

    return await shipment_service.cancel_shipment(
        shipment_id=shipment_id)
