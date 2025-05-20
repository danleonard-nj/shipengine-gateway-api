import uuid
from attr import dataclass
from data.address_repository import AddressRepository
from framework.logger.providers import get_logger
from framework.configuration import Configuration
from httpx import AsyncClient
from framework.serialization import Serializable
from framework.clients.cache_client import CacheClientAsync
from constants.cache import CacheKey

logger = get_logger(__name__)


@dataclass
class AddressModel(Serializable):
    address_id: str
    name: str
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    is_default: bool

    @staticmethod
    def from_dict(data: dict):
        # Accepts both '_id' and 'address_id', prioritizing 'address_id' if present
        address_id = data.get('address_id') or data.get('_id')
        return AddressModel(
            address_id=address_id,
            name=data.get('name'),
            street=data.get('street'),
            city=data.get('city'),
            state=data.get('state'),
            postal_code=data.get('postal_code'),
            country=data.get('country'),
            is_default=data.get('is_default', False)
        )

    def to_dict(self):
        # Only serialize address_id, not _id
        return {
            'address_id': self.address_id,
            'name': self.name,
            'street': self.street,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'is_default': self.is_default
        }


class AddressService:
    def __init__(
        self,
        address_repository: AddressRepository,
        http_client: AsyncClient,
        configuration: Configuration,
        cache_client: CacheClientAsync
    ):
        self._address_repository = address_repository
        self._maps_key = configuration.google.get('google_maps_key')
        self._http_client = http_client
        self._cache_client = cache_client

    async def get_addresses(
        self,
        page_size: int,
        page_number: int
    ):
        logger.info(f"Fetching addresses with page_size: {page_size}, page_number: {page_number}")

        result = await self._address_repository.get_addresses(
            page_size=page_size,
            page_number=page_number
        )

        if len([x for x in result if x.get('is_default')]) > 1:
            raise Exception(f"Multiple addresses currently set to default: {[x.get('name') for x in result if x.get('is_default')]}")

        return result

    async def _bust_address_cache(self):
        await self._cache_client.delete(CacheKey.get_address_list())
        await self._cache_client.delete(CacheKey.get_default_address())

    async def insert_address(
        self,
        address: dict
    ):
        name = address.get('name')
        if not name:
            raise Exception("Address name is required")
        street = address.get('street')
        city = address.get('city')
        state = address.get('state')
        postal_code = address.get('postal_code')
        country = address.get('country')
        # Additional validation logic
        if not street:
            raise Exception("Street is required")
        if not city:
            raise Exception("City is required")
        if not state:
            raise Exception("State is required")
        if not postal_code:
            raise Exception("Postal code is required")
        if not country:
            raise Exception("Country is required")

        exists = await self._address_repository.get({
            'name': name}) is not None

        if exists:
            raise Exception(f"Address with the name '{name}' already exists")

        model = AddressModel.from_dict(address)
        model.address_id = str(uuid.uuid4())

        result = await self._address_repository.insert_address(
            address=model.to_dict()
        )
        await self._bust_address_cache()
        if model.is_default:
            logger.info(f"Setting address '{model.name}' as default")
            await self.set_default_address(
                address_id=model.address_id)
        return model.to_dict()

    async def get_address(
        self,
        address_id: str
    ):
        return await self._address_repository.get_address(
            address_id=address_id
        )

    async def update_address(
        self,
        address_id: str,
        address: dict
    ):
        # Simplified validation logic for update
        required_fields = ['name', 'street', 'city', 'state', 'postal_code', 'country']
        for field in required_fields:
            if field in address and not address[field]:
                raise Exception(f"{field.replace('_', ' ').capitalize()} is required")
        result = await self._address_repository.update_address(
            address_id=address_id,
            address=address
        )
        await self._bust_address_cache()
        # If is_default is being set, ensure only one default
        if address.get('is_default'):
            await self.set_default_address(address_id=address_id)
        return result

    async def set_default_address(
        self,
        address_id: str
    ):
        address = await self._address_repository.get_address(
            address_id=address_id
        )
        if not address:
            raise Exception(f"Address with the ID '{address_id}' does not exist")
        result = await self._address_repository.set_default_address(
            address_id=address_id
        )
        await self._bust_address_cache()
        return result

    async def get_default_address(
        self
    ):
        return await self._address_repository.get_default_address()

    async def validate_address(
        self,
        address: dict
    ):
        if not self._maps_key:
            raise Exception("Google Maps API key is not configured")

        params = {
            "address": f"{address.get('street', '')}, {address.get('city', '')}, {address.get('state', '')} {address.get('postal_code', '')}, {address.get('country', '')}",
            "key": self._maps_key
        }
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        response = await self._http_client.get(url, params=params)
        data = await response.json()

        if data.get("status") != "OK":
            raise Exception(f"Address validation failed: {data.get('status')} - {data.get('error_message', '')}")

        results = data.get("results", [])
        if not results:
            raise Exception("No results found for the provided address")

        # Optionally, extract more details if needed
        return {
            "is_valid": True,
            "formatted_address": results[0].get("formatted_address"),
            "location": results[0].get("geometry", {}).get("location", {})
        }

    async def delete_address(
        self,
        address_id: str
    ):
        address = await self._address_repository.get_address(address_id=address_id)
        if not address:
            raise Exception(f"Address with the ID '{address_id}' does not exist")
        was_default = address.get('is_default', False)
        result = await self._address_repository.delete_address(address_id=address_id)
        await self._bust_address_cache()
        # If the deleted address was default, promote another if any exist
        if was_default:
            addresses = await self._address_repository.get_addresses(page_size=1, page_number=1)
            if addresses:
                await self.set_default_address(addresses[0]['address_id'])
        return result
