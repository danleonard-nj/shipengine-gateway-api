from data.address_repository import AddressRepository
from framework.logger.providers import get_logger
from framework.configuration import Configuration
import httpx
logger = get_logger(__name__)


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

        return await self._address_repository.get_addresses(
            page_size=page_size,
            page_number=page_number
        )

    async def insert_address(
        self,
        address: dict
    ):
        if not address.get('name'):
            raise Exception("Address name is required")

        exists = await self._address_repository.get({
            'name': address.get('name')}) is not None

        if exists:
            raise Exception(f"Address with the name ' already exists")

        return await self._address_repository.insert_address(
            address=address
        )

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
