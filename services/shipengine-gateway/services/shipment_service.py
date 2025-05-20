import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Dict

from clients.shipengine_client import ShipEngineClient
from data.shipment_repository import ShipmentRepository
from framework.clients.cache_client import CacheClientAsync
from framework.concurrency import TaskCollection
from framework.crypto.hashing import sha256
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace
from models.requests import GetShipmentRequest
from models.shipment import CreateShipment, Shipment
from services.carrier_service import CarrierService
from services.mapper_service import MapperService
from utilities.utils import first_or_default

logger = get_logger(__name__)


def hash_shipment(shipment):
    j = json.dumps(shipment, sort_keys=True, default=str)
    return sha256(j)


class ShipmentService:
    def __init__(
        self,
        mapper_service: MapperService,
        shipengine_client: ShipEngineClient,
        shipment_repository: ShipmentRepository,
        carrier_service: CarrierService,
        cache_client: CacheClientAsync
    ):
        ArgumentNullException.if_none(mapper_service, 'mapper_service')
        ArgumentNullException.if_none(shipengine_client, 'shipengine_client')
        ArgumentNullException.if_none(shipment_repository, 'shipment_repository')
        ArgumentNullException.if_none(cache_client, 'cache_client')

        self._mapper_service = mapper_service
        self._shipengine_client = shipengine_client
        self._carrier_service = carrier_service
        self._repository = shipment_repository
        self._cache_client = cache_client

    async def cancel_shipment(
        self,
        shipment_id: str
    ) -> Dict:
        logger.info(f'Cancel shipment: {shipment_id}')

        ArgumentNullException.if_none_or_whitespace(shipment_id, 'shipment_id')

        success = await self._shipengine_client.cancel_shipment(
            shipment_id=shipment_id)

        if not success:
            raise Exception(f'Failed to cancel shipment')

        # Update the shipment status in the database
        await self._repository.update(
            selector={'shipment_id': shipment_id},
            values={'shipment_status': 'Canceled'}
        )

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
        # if isinstance(last_sync_date, str):
        #     last_sync_date = datetime.fromisoformat(last_sync_date)
        last_sync_date = last_sync_date.replace(tzinfo=timezone.utc)

        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        logger.info(f'Last sync date: {last_sync_date}, One hour ago: {one_hour_ago}')
        logger.info(f'Current time: {datetime.now(timezone.utc)}')
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
        if total_pages > 1:
            tasks = [
                self._shipengine_client.get_shipments(
                    page_number=page,
                    page_size=page_size)
                for page in range(2, total_pages + 1)
            ]
            responses = await asyncio.gather(*tasks)
            for resp in responses:
                fetched_shipments.extend(resp.get('shipments', []))

        # Fetch existing shipments from the database
        existing_shipments = await self._repository.get_all()
        existing_shipments_dict = {
            s['shipment_id']: s for s in existing_shipments if 'shipment_id' in s
        }
        for s in existing_shipments:
            if 'shipment_id' not in s:
                logger.info(f'missing shipment ID: {s}')

        # Prepare mappings
        service_code_mapping = await self._mapper_service.get_carrier_service_code_mapping()
        carrier_mapping = await self._mapper_service.get_carrier_mapping()

        added_shipments = []
        updated_shipments = []

        # Process fetched shipments
        for shipment in fetched_shipments:
            shipment_id = shipment['shipment_id']
            if shipment_id in existing_shipments_dict:
                existing_shipment = existing_shipments_dict.pop(shipment_id)
                existing = Shipment.from_entity(
                    data=existing_shipment,
                    service_code_mapping=service_code_mapping,
                    carrier_mapping=carrier_mapping)
                current = Shipment.from_data(
                    data=shipment,
                    service_code_mapping=service_code_mapping,
                    carrier_mapping=carrier_mapping)
                if hash_shipment(existing.to_dict()) != hash_shipment(current.to_dict()):
                    logger.info(f'Updating shipment: {shipment_id} in the database')
                current.sync_date = datetime.now(timezone.utc)
                updated_shipments.append(current)
            else:
                added_shipments.append(
                    Shipment.from_data(
                        data=shipment,
                        service_code_mapping=service_code_mapping,
                        carrier_mapping=carrier_mapping)
                )

        removed_shipments = list(existing_shipments_dict.values())

        # Apply changes to the database
        if added_shipments:
            await self._repository.bulk_insert_shipments([
                s.to_entity() for s in added_shipments
            ])

        semaphore = asyncio.Semaphore(10)

        async def wrapped_update(shipment):
            async with semaphore:
                await self._repository.update(
                    selector=shipment.get_selector(),
                    values=shipment.to_entity()
                )
        tasks = [wrapped_update(s) for s in updated_shipments]
        await asyncio.gather(*tasks)

        for shipment in removed_shipments:
            await self._repository.delete(
                selector={'shipment_id': shipment['shipment_id']})

        logger.info(f'Sync complete: {len(added_shipments)} added, {len(updated_shipments)} updated, {len(removed_shipments)} removed')
        return len(fetched_shipments)

    async def get_shipments(
        self,
        request: GetShipmentRequest
    ) -> Dict:
        logger.info('Get shipments from local database (sync if needed)')

        page_size = int(request.page_size)
        page_number = int(request.page_number)
        cancelled = request.cancelled

        # Only check if sync is needed, do not always call remote API
        needs_sync = await self.is_last_sync_over_one_hour_ago()
        if needs_sync:
            logger.info('Last sync over one hour ago, triggering sync in background')
            # Trigger sync but do not await, so response is fast
            asyncio.create_task(self.sync_shipments())

        # Fetch shipments and document count from the database
        shipments = await self._repository.get_shipments(
            page_size=page_size,
            page_number=page_number,
            cancelled=cancelled)

        service_code_mapping = await self._mapper_service.get_carrier_service_code_mapping()
        carrier_mapping = await self._mapper_service.get_carrier_mapping()

        parsed = []
        for shipment in shipments:
            parsed_shipment = Shipment.from_entity(
                data=shipment,
                service_code_mapping=service_code_mapping,
                carrier_mapping=carrier_mapping)
            if parsed_shipment.carrier_name is None:
                logger.info(f"Failed to map carrier name for carrier ID: '{parsed_shipment.carrier_id}' for shipment ID: '{parsed_shipment.shipment_id}'")
            parsed.append(parsed_shipment)

        total_shipment_count = await self._repository.get_shipments_count(
            cancelled=cancelled
        )
        total_pages = total_shipment_count // page_size + (total_shipment_count % page_size > 0)

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

        carrier_ids = await self._carrier_service.get_carrier_ids()

        shipment = CreateShipment.from_data(data=data)

        if none_or_whitespace(shipment.carrier_id):
            raise Exception('Carrier ID cannot be null or empty')

        if none_or_whitespace(shipment.service_code):
            raise Exception('Service code cannot be null or empty')

        if shipment.carrier_id not in carrier_ids:
            raise Exception(f'Carrier ID {shipment.carrier_id} is not supported')

        shipment_data = shipment.to_dict()

        result = await self._shipengine_client.create_shipment(
            data=shipment_data)

        created = first_or_default(result.get('shipments'))

        if not created:
            raise Exception('No response content returned from client')

        service_code_mapping = await self._mapper_service.get_carrier_service_code_mapping()
        carrier_mapping = await self._mapper_service.get_carrier_mapping()

        logger.info('Parsing created shipment model')
        created_shipment = Shipment.from_data(
            data=created,
            service_code_mapping=service_code_mapping,
            carrier_mapping=carrier_mapping)

        await self._repository.insert(created_shipment.to_entity())

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

        result = Shipment.from_data(
            data=shipment,
            service_code_mapping=service_code_mapping,
            carrier_mapping=carrier_mapping)

        return result.to_dict()
