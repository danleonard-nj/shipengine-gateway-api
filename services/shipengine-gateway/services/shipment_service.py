import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict

from clients.shipengine_client import ShipEngineClient
from data.shipment_repository import ShipmentRepository
from framework.clients.cache_client import CacheClientAsync
from framework.concurrency import TaskCollection
from framework.crypto.hashing import sha256
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from framework.serialization.utilities import serialize
from models.requests import GetShipmentRequest
from models.shipment import CreateShipment, Shipment
from services.mapper_service import MapperService
from utilities.utils import first_or_default

logger = get_logger(__name__)


class ShipmentService:
    def __init__(
        self,
        mapper_service: MapperService,
        shipengine_client: ShipEngineClient,
        shipment_repository: ShipmentRepository,
        cache_client: CacheClientAsync
    ):
        ArgumentNullException.if_none(mapper_service, 'mapper_service')
        ArgumentNullException.if_none(shipengine_client, 'shipengine_client')
        ArgumentNullException.if_none(shipment_repository, 'shipment_repository')
        ArgumentNullException.if_none(cache_client, 'cache_client')

        self._mapper_service = mapper_service
        self._shipengine_client = shipengine_client
        self._repository = shipment_repository
        self.__cache_client = cache_client

    async def cancel_shipment(
        self,
        shipment_id: str
    ) -> Dict:
        logger.info(f'Cancel shipment: {shipment_id}')

        ArgumentNullException.if_none_or_whitespace(shipment_id, 'shipment_id')

        await self._shipengine_client.cancel_shipment(
            shipment_id=shipment_id)

        return {
            'deleted': True
        }

    async def is_last_sync_over_one_hour_ago(
        self
    ) -> bool:
        most_recent_shipment = await self._repository.get_most_recent_shipment()
        if not most_recent_shipment or 'sync_date' not in most_recent_shipment:
            return True

        last_sync_date = most_recent_shipment['sync_date']
        if isinstance(last_sync_date, str):
            last_sync_date = datetime.fromisoformat(last_sync_date)

        one_hour_ago = datetime.now() - timedelta(hours=1)
        return last_sync_date < one_hour_ago

    async def sync_shipments(
        self,
        page_size: int = 50
    ):
        logger.info('Syncing shipments to the database')

        # Fetch the first page to get the total number of pages
        response = await self._shipengine_client.get_shipments(
            page_number=1,
            page_size=page_size)

        total_pages = response.get('pages', 1)
        fetched_shipments = response.get('shipments', [])

        # Fetch remaining pages concurrently
        tasks = [
            self._shipengine_client.get_shipments(
                page_number=page,
                page_size=page_size)
            for page in range(2, total_pages + 1)
        ]

        responses = await asyncio.gather(*tasks)

        # Collect shipments from all pages
        for resp in responses:
            fetched_shipments.extend(resp.get('shipments', []))

        # Fetch existing shipments from the database
        existing_shipments = await self._repository.get_all()

        # The 'shipment_id' property on the ShipEngine model is named 'id' in the database
        existing_shipments_dict = {
            shipment['id']: shipment
            for shipment
            in existing_shipments
        }

        # Prepare mappings
        service_code_mapping = await self._mapper_service.get_carrier_service_code_mapping()
        carrier_mapping = await self._mapper_service.get_carrier_mapping()

        # Track changes
        added_shipments = []
        updated_shipments = []
        removed_shipments = []

        def hash_shipment(shipment):
            j = json.dumps(shipment, sort_keys=True, default=str)
            return sha256(j)

        # Process fetched shipments
        for shipment in fetched_shipments:
            shipment_id = shipment['shipment_id']
            if shipment_id in existing_shipments_dict:
                # Update existing shipment (remove it from the dict to track removes later)
                existing_shipment = existing_shipments_dict.pop(shipment_id)

                existing = Shipment.from_data(
                    data=existing_shipment,
                    service_code_mapping=service_code_mapping,
                    carrier_mapping=carrier_mapping)

                current = Shipment.from_data(
                    data=shipment,
                    service_code_mapping=service_code_mapping,
                    carrier_mapping=carrier_mapping)

                # Check if the shipment has changed
                if hash_shipment(existing.to_dict()) != hash_shipment(current.to_dict()):
                    updated_shipments.append(current)
            else:
                # Add new shipment
                new = Shipment.from_data(
                    data=shipment,
                    service_code_mapping=service_code_mapping,
                    carrier_mapping=carrier_mapping)

                added_shipments.append(new)

        # Remaining shipments in existing_shipments_dict are removed
        removed_shipments = list(existing_shipments_dict.values())

        # Apply changes to the database
        to_insert = [shipment.to_entity() for shipment in added_shipments]
        await self._repository.bulk_insert_shipments(to_insert)

        for shipment in updated_shipments:
            logger.info(f'Updating shipment: {shipment.shipment_id} in the database')
            # Update the existing shipment in the database
            await self._repository.update(
                selector=shipment.get_selector(),
                values=shipment.to_dict()
            )

        for shipment in removed_shipments:
            # Delete the removed shipment from the database
            await self._repository.delete(
                selector=dict('shipment_id', shipment['shipment_id']))

        logger.info(f'Sync complete: {len(added_shipments)} added, {len(updated_shipments)} updated, {len(removed_shipments)} removed')

        return {
            'added': len(added_shipments),
            'updated': len(updated_shipments),
            'removed': len(removed_shipments)
        }

    async def get_shipments(
        self,
        request: GetShipmentRequest
    ) -> Dict:
        logger.info('Get shipments from ShipEngine client')

        page_size = int(request.page_size)
        page_number = int(request.page_number)

        is_sync_required = await self.is_last_sync_over_one_hour_ago()

        if is_sync_required:
            logger.info('Syncing shipments to the database')
            await self.sync_shipments()

        # Fetch shipments and document count from the database
        shipments, total_shipment_count = await TaskCollection(
            self._repository.get_shipments(
                page_size=page_size,
                page_number=page_number),
            self._repository.get_shipments_count()
        ).run()

        service_code_mapping = await self._mapper_service.get_carrier_service_code_mapping()
        carrier_mapping = await self._mapper_service.get_carrier_mapping()

        parsed = [Shipment.from_entity(
            data=shipment,
            service_code_mapping=service_code_mapping,
            carrier_mapping=carrier_mapping)
            for shipment in shipments]

        # Get the total number of pages by dividing the document count by the page size
        total_pages = total_shipment_count // page_size + (1 if total_shipment_count % page_size > 0 else 0)

        return {
            'shipments': [shipment.to_dict() for shipment in parsed],
            'page_number': page_number,
            'total_pages': total_pages,
            'result_count': total_shipment_count
        }

    async def create_shipment(
        self,
        data: Dict
    ) -> Dict:
        shipment = CreateShipment(
            data=data)

        shipment_data = shipment.to_json()

        result = await self._shipengine_client.create_shipment(
            data=shipment_data)

        created = first_or_default(result.get('shipments'))
        logger.info(f'Response: {serialize(created)}')

        if not created:
            raise Exception('No response content returned from client')

        logger.info('Parsing created shipment model')
        created_shipment = Shipment(
            data=created)

        return {
            'shipment_id': created_shipment.shipment_id
        }

    async def update_shipment(
        self,
        data: Dict
    ) -> Dict:
        shipment = CreateShipment(
            data=data)

        shipment_data = shipment.to_json()

        result = await self._shipengine_client.create_shipment(
            data=shipment_data)

        created = first_or_default(result.get('shipments'))
        logger.info(f'Response: {serialize(created)}')

        if not created:
            raise Exception('No response content returned from client')

        logger.info('Parsing created shipment model')
        created_shipment = Shipment(
            data=created)

        return {
            'shipment_id': created_shipment.shipment_id
        }

    async def get_shipment(
        self,
        shipment_id: str
    ):
        logger.info(f'Get shipment: {shipment_id}')
        shipment = await self._shipengine_client.get_shipment(
            shipment_id=shipment_id)

        logger.info(f'Fetching carrier mapping')
        service_code_mapping = await self._mapper_service.get_carrier_service_code_mapping()
        carrier_mapping = await self._mapper_service.get_carrier_mapping()

        result = Shipment(
            data=shipment,
            service_code_mapping=service_code_mapping,
            carrier_mapping=carrier_mapping)

        return result.to_dict()
