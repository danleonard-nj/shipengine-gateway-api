from email.headerregistry import Address
from cv2 import add
from framework.logger.providers import get_logger
from framework.rest.blueprints.meta import MetaBlueprint

from services import address_service
from services.address_service import AddressService
from quart import request
from dataclasses import dataclass

logger = get_logger(__name__)
address_bp = MetaBlueprint('address_bp', __name__)


@dataclass
class AddressInsertRequest:
    name: str
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    is_default: bool


def has_required_fields(data, _class: 'dataclass'):
    for field in _class.__dataclass_fields__:
        if field not in data:
            return False, {'error': f'{field} is required'}
    return True, {}


@address_bp.configure('/api/address', methods=['GET'], auth_scheme='read')
async def get_addresses(container):
    address_service: AddressService = container.resolve(
        AddressService)

    page_size = request.args.get('page_size', default=10, type=int)
    page_number = request.args.get('page_number', default=1, type=int)
    if page_size < 1 or page_number < 1:
        return {'error': 'page_size and page_number must be greater than 0'}, 400
    response = await address_service.get_addresses(
        page_size=page_size,
        page_number=page_number
    )
    return {'addresses': response}


@address_bp.configure('/api/address/<address_id>', methods=['GET'], auth_scheme='read')
async def get_address(container, address_id):
    address_service: AddressService = container.resolve(
        AddressService)

    if not address_id:
        return {'error': 'Address ID is required'}, 400

    response = await address_service.get_address(
        address_id=address_id
    )
    if not response:
        return {'error': 'Address not found'}, 404

    return {'address': response}


@address_bp.configure('/api/address/<address_id>', methods=['PUT'], auth_scheme='read')
async def update_address(container, address_id):
    address_service: AddressService = container.resolve(
        AddressService)

    if not address_id:
        return {'error': 'Address ID is required'}, 400

    data = await request.get_json()

    @dataclass
    class AddressUpdateRequest:
        street: str
        city: str
        state: str
        postal_code: str
        country: str

    req = AddressUpdateRequest(
        street=data.get('street', ''),
        city=data.get('city', ''),
        state=data.get('state', ''),
        postal_code=data.get('postal_code', ''),
        country=data.get('country', ''))

    result = await address_service.update_address(
        address_id=address_id,
        address=data
    )

    return {'address': result}


@address_bp.configure('/api/address', methods=['POST'], auth_scheme='read')
async def insert_address(container):
    address_service: AddressService = container.resolve(
        AddressService)

    overwrite = request.args.get('overwrite', default=False, type=bool)

    data = await request.get_json()

    if not data:
        return {'error': 'Address data is required'}, 400

    valid, error = has_required_fields(data, AddressInsertRequest)

    if not valid:
        return error, 400

    req = AddressInsertRequest(
        name=data.get('name', ''),
        street=data.get('street', ''),
        city=data.get('city', ''),
        state=data.get('state', ''),
        postal_code=data.get('postal_code', ''),
        country=data.get('country', ''),
        is_default=data.get('is_default', False)
    )

    result = await address_service.insert_address(
        address=data
    )

    return {'address': str()}


@address_bp.configure('/api/address/<address_id>/default', methods=['PUT'], auth_scheme='read')
async def set_default_address(container, address_id):
    address_service: AddressService = container.resolve(
        AddressService)

    if not address_id:
        return {'error': 'Address ID is required'}, 400

    response = await address_service.set_default_address(
        address_id=address_id
    )

    return {'result': response}


@address_bp.configure('/api/address/<address_id>', methods=['DELETE'], auth_scheme='read')
async def delete_address(container, address_id):
    address_service: AddressService = container.resolve(
        AddressService)

    if not address_id:
        return {'error': 'Address ID is required'}, 400

    response = await address_service.delete_address(
        address_id=address_id
    )
    return {'address': response}


@address_bp.configure('/api/address/default', methods=['GET'], auth_scheme='read')
async def get_default_address(container):
    address_service: AddressService = container.resolve(
        AddressService)

    response = await address_service.get_default_address()
    return {'address': response}


@address_bp.configure('/api/address/validate', methods=['POST'], auth_scheme='read')
async def validate_address(container):
    address_service: AddressService = container.resolve(
        AddressService)

    data = await request.get_json()

    @dataclass
    class AddressValidationRequest:
        street: str
        city: str
        state: str
        postal_code: str
        country: str

    req = AddressValidationRequest(
        street=data.get('street', ''),
        city=data.get('city', ''),
        state=data.get('state', ''),
        postal_code=data.get('postal_code', ''),
        country=data.get('country', '')
    )

    response = address_service.validate_address(data)
