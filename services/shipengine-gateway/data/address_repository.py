from framework.mongo.mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient


class AddressRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database='ShipEngine',
            collection='AddressBook')

    async def get_addresses(
        self,
        page_size: int,
        page_number: int
    ):
        skip_count = (page_number - 1) * page_size
        result = await (
            self.collection
            .find()
            .sort('created_date', -1)  # Sort by sync_date in descending order
            .skip(skip_count)
            .limit(page_size)
            .to_list(length=None)
        )

        mod = []
        for item in result:
            item['_id'] = str(item['_id'])
            mod.append(item)
        return mod

    async def insert_address(
        self,
        address: dict
    ):
        result = await self.collection.insert_one(address)
        return {'_id': str(result.inserted_id)} | address

    async def get_address(
        self,
        address_id: str
    ):
        return await self.collection.find_one({'address_id': address_id})

    async def update_address(
        self,
        address_id: str,
        address: dict
    ):
        result = await self.collection.update_one(
            {'_id': address_id},
            {'$set': address}
        )

    async def set_default_address(
        self,
        address_id: str
    ):
        # Set all other addresses to not default
        await self.collection.update_many(
            {'is_default': True, 'address_id': {'$ne': address_id}},
            {'$set': {'is_default': False}}
        )

        # Set the specified address to default
        result = await self.collection.update_one(
            {'address_id': address_id},
            {'$set': {'is_default': True}}
        )
        return result

    async def get_default_address(
        self
    ):
        return await self.collection.find_one({'is_default': True})

    async def delete_address(
        self,
        address_id: str
    ):
        result = await self.collection.delete_one({'address_id': address_id})
        return {'deleted_count': result.deleted_count}
