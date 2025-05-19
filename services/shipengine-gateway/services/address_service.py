import uuid
from attr import dataclass
from data.address_repository import AddressRepository
from framework.logger.providers import get_logger
from framework.configuration import Configuration
import httpx
from framework.serialization import Serializable
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
        return AddressModel(
            address_id=data.get('_id'),
            name=data.get('name'),
            street=data.get('street'),
            city=data.get('city'),
            state=data.get('state'),
            postal_code=data.get('postal_code'),
            country=data.get('country'),
            is_default=data.get('is_default', False)
        )


class AddressService:
    def __init__(
        self,
        address_repository: AddressRepository,
        configuration: Configuration
    ):
        self._address_repository = address_repository
        # TODO: Replace this
        self._maps_key = None

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

    async def insert_address(
        self,
        address: dict
    ):
        name = address.get('name')
        if not name:
            raise Exception("Address name is required")

        exists = await self._address_repository.get({
            'name': name}) is not None

        if exists:
            raise Exception(f"Address with the name '{name} already exists")

        model = AddressModel.from_dict(address)
        model.address_id = str(uuid.uuid4())

        result = await self._address_repository.insert_address(
            address=model.to_dict()
        )

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
        return await self._address_repository.update_address(
            address_id=address_id,
            address=address
        )

    async def set_default_address(
        self,
        address_id: str
    ):
        address = await self._address_repository.get_address(
            address_id=address_id
        )

        if not address:
            raise Exception(f"Address with the ID '{address_id}' does not exist")

        return await self._address_repository.set_default_address(
            address_id=address_id
        )

    async def get_default_address(
        self
    ):
        return await self._address_repository.get_default_address()

    async def validate_address(
        self,
        address: dict
    ):
        # Validate the address using
        async with httpx.AsyncClient() as client:
            params = {
                "address": address.get("street", ""),
                "components": f"locality:{address.get('city','')}|administrative_area:{address.get('state','')}|country:{address.get('country','')}",
                "key": self._maps_key
            }
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=params
            )
            data = response.json()
            if data.get("status") == "OK":
                standardized = data["results"][0]["formatted_address"]
                return {"is_valid": True, "standardized_address": standardized}
            else:
                return {"is_valid": False, "error": data.get("status")}
