
import asyncio
from datetime import datetime

from clients.shipengine_client import ShipEngineClient
from constants.cache import CacheKey
from dateutil import parser
from domain.exceptions import ShipmentLabelException, ShipmentNotFoundException
from framework.clients.cache_client import CacheClientAsync
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from framework.serialization.utilities import serialize
from models.label import Label
from utilities.utils import first_or_default

logger = get_logger(__name__)


class LabelService:
    def __init__(
        self,
        shipengine_client: ShipEngineClient,
        cache_client: CacheClientAsync
    ):
        self._client = shipengine_client
        self._cache_client = cache_client

    async def create_label(
        self,
        shipment_id: str
    ):
        ArgumentNullException.if_none_or_empty(shipment_id, 'shipment_id')

        # TODO: Handle 'out of funds' more gracefully, catch it and maybe auto-fund

        logger.info(f'Create label from shipment: {shipment_id}')

        # Fetch the shipment and update the ship date if it's not current.  The API
        # doesn't provide any capabilities to do this on the fly when requesting the
        # label, so if the ship date is in the past it'll just error out
        shipment = await self._client.get_shipment(
            shipment_id=shipment_id)

        # If the shipment we're requesting a label for doesn't exist
        if shipment is None:
            raise ShipmentNotFoundException(
                shipment_id=shipment_id)

        # Parse the shipment date
        shipment_date = shipment.get('ship_date')
        ship_date = parser.parse(shipment_date)
        logger.info(f'Ship date: {ship_date.isoformat()}')

        # Update the ship date if it's in the past as this
        # will fail shipengine validation
        now = datetime.now()
        if ship_date.date() != now.date():
            logger.info(f'Updating ship date to {now.date()}')

            # Update the ship date on the shipment request
            shipment['ship_date'] = now.date().isoformat()

            logger.info(f'Sending shipment update call')
            update_response = await self._client.update_shipment(
                shipment_id=shipment_id,
                data=shipment)

            logger.info(f'Update response: {serialize(update_response)}')

        # Create the shipment label
        label = await self._client.create_label(
            shipment_id=shipment_id)

        # Handle errors in the event we fail to create
        # the label
        errors = label.get('errors', list())

        if len(errors) > 0:
            logger.info(f'Failed to create label: {errors}')

            # Get the list of error messages returned by
            # shipengine to surface in exception message
            error_messages = [x.get('message') for x in errors]

            raise Exception(f'Error: {error_messages}')

        model = Label.from_data(data=label)

        return model.to_dict()

    async def get_label(
        self,
        shipment_id: str
    ) -> dict:
        ArgumentNullException.if_none_or_whitespace(shipment_id, 'shipment_id')

        logger.info(f'Get label for shipment: {shipment_id}')

        cache_key = CacheKey.get_label(shipment_id=shipment_id)

        # Check the cache for the label
        cached = await self._cache_client.get_json(
            key=cache_key)

        if cached is not None:
            logger.info(f'Label found in cache for shipment ID: {shipment_id}')

            return Label.from_dict(data=cached).to_dict()

        # Fetch the label from shipengine
        label_response = await self._client.get_label(
            shipment_id=shipment_id)

        # If we get an invalid response from shipengine
        if label_response is None:
            raise ShipmentLabelException(
                f'Failed to fech labels for shipment: {shipment_id}')

        shipment_labels = label_response.get('labels', [])
        label = first_or_default(shipment_labels)

        # If a shipment has no label created for it return
        # none
        if label is None:
            return dict(label=None)

        data = Label.from_data(data=label).to_dict()

        # Cache the label
        asyncio.create_task(
            self._cache_client.set_json(
                key=cache_key,
                value=data,
                ttl=60 * 24
            )
        )

        return data
