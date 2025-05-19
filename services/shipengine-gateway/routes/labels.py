from framework.logger.providers import get_logger
from framework.rest.blueprints.meta import MetaBlueprint
from services.label_service import LabelService

logger = get_logger(__name__)
label_bp = MetaBlueprint('label_bp', __name__)


@label_bp.configure('/api/shipments/<shipment_id>/label', methods=['GET'], auth_scheme='read')
async def get_label(container, shipment_id: str):
    label_service: LabelService = container.resolve(
        LabelService)

    logger.info(f'Get label for shipment: {shipment_id}')
    label = await label_service.get_label(
        shipment_id=shipment_id)

    return {'label': label}


@label_bp.configure('/api/shipments/<shipment_id>/label', methods=['POST'], auth_scheme='write')
async def create_label(container, shipment_id):
    label_service: LabelService = container.resolve(
        LabelService)

    logger.info(f'Create label for shipment: {shipment_id}')

    label = await label_service.create_label(
        shipment_id=shipment_id)

    return {'label': label}


@label_bp.configure('/api/labels/<label_id>/void', methods=['PUT'], auth_scheme='write')
async def void_label(container, label_id):
    label_service: LabelService = container.resolve(
        LabelService)

    logger.info(f'Void label: {label_id}')

    result = await label_service.void_label(
        label_id=label_id)

    return {'response': result}
