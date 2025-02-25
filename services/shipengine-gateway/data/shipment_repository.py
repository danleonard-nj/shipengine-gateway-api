from framework.mongo.mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient


class ShipmentRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database='ShipEngine',
            collection='Shipment')

    async def get_shipments(
        self,
        page_size: int,
        page_number: int,
        cancelled: bool = False
    ):
        skip_count = (page_number - 1) * page_size  # Calculate how many documents to skip

        return await (
            self.collection
            .find({'shipment_status': {'$ne': 'Canceled'}} if not cancelled else {})
            .sort('created_date', -1)  # Sort by sync_date in descending order
            .skip(skip_count)
            .limit(page_size)
            .to_list(length=None)
        )

    async def bulk_insert_shipments(
        self,
        shipments: list
    ):
        result = await self.collection.insert_many(shipments)
        return result.inserted_ids

    async def get_shipments_count(
        self,
        cancelled: bool = False
    ) -> int:
        return await self.collection.count_documents({
            'shipment_status': {'$ne': 'Canceled'}
        } if not cancelled else {})

    async def get_all_shipments(
        self
    ):
        return await self.collection.find().to_list(length=None)

    async def get_most_recent_shipment(self):
        return await self.collection.find_one(
            sort=[("sync_date", -1)]
        )
