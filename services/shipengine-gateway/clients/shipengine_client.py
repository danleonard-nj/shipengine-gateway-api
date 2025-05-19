from typing import Dict

from framework.configuration.configuration import Configuration
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from framework.utilities.url_utils import build_url
from httpx import AsyncClient

logger = get_logger(__name__)


class ShipEngineClient:
    def __init__(
        self,
        http_client: AsyncClient,
        configuration: Configuration
    ):
        # self.__http_client = HttpClient()

        self._http_client = http_client
        self._base_url = configuration.shipengine.get(
            'base_url')
        self._api_key = configuration.shipengine.get(
            'api_key')

    def _get_headers(
        self
    ) -> dict:
        return {
            'Content-Type': 'application/json',
            'API-Key': self._api_key
        }

    async def create_label(
        self,
        shipment_id: str
    ) -> Dict:
        ArgumentNullException.if_none_or_whitespace(shipment_id, 'shipment_id')

        logger.info(f'Create label for shipment: {shipment_id}')

        response = await self._http_client.post(
            url=f'{self._base_url}/labels/shipment/{shipment_id}',
            headers=self._get_headers())

        content = response.json()
        logger.info(f'Response status: {response.status_code}')

        return content

    async def void_label(
        self,
        label_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(label_id, 'label_id')

        logger.info(f'Void label: {label_id}')

        response = await self._http_client.put(
            url=f'{self._base_url}/labels/{label_id}/void',
            headers=self._get_headers())

        logger.info(f'Response status: {response.status_code}')

        return response

    async def get_label(
        self,
        shipment_id: str
    ) -> Dict:
        ArgumentNullException.if_none_or_whitespace(shipment_id, 'shipment_id')

        logger.info(f'Get label for shipment: {shipment_id}')

        url = build_url(
            base=f'{self._base_url}/labels',
            shipment_id=shipment_id)

        logger.info(f'Get label endpoint: {url}')

        response = await self._http_client.get(
            url=url,
            headers=self._get_headers())

        logger.info(f'Status: {response.status_code}')
        return response.json()

    async def get_shipments(
        self,
        page_number: int,
        page_size: int
    ) -> Dict:
        logger.info('Get Shipments')

        url = build_url(
            base=f'{self._base_url}/shipments',
            sort_by='created_at',
            sort_dir='desc',
            page=page_number,
            page_size=page_size)

        logger.info(f'Get shipments endpoint: {url}')

        response = await self._http_client.get(
            url=url,
            headers=self._get_headers(),
            timeout=None)

        logger.info(f'Status: {response.status_code}')
        return response.json()

    async def create_shipment(
        self,
        data: Dict
    ) -> Dict:
        ArgumentNullException.if_none_or_whitespace(data, 'data')

        logger.info(f'Create shipment request: {data}')

        response = await self._http_client.post(
            url=f'{self._base_url}/shipments',
            headers=self._get_headers(),
            json=data)

        content = response.json()

        logger.info(f'Create shipment status: {response.status_code}')

        return content

    async def update_shipment(
        self,
        shipment_id: str,
        data: Dict
    ) -> Dict:
        ArgumentNullException.if_none_or_whitespace(shipment_id, 'shipment_id')
        ArgumentNullException.if_none(data, 'data')

        logger.info(f'Update shipment: {shipment_id}')

        response = await self._http_client.put(
            url=f'{self._base_url}/shipments/{shipment_id}',
            headers=self._get_headers(),
            json=data,
            timeout=None)

        content = response.json()
        logger.info(f'Status: {response.status_code}')
        logger.info(f'Response status: {response.status_code}')

        return content

    async def get_carriers(
        self
    ) -> Dict:
        logger.info('Get carriers from client')

        response = await self._http_client.get(
            url=f'{self._base_url}/carriers',
            headers=self._get_headers(),
            timeout=None)

        content = response.json()

        logger.info(f'Get carriers status: {response.status_code}')

        return content

    async def cancel_shipment(
        self,
        shipment_id: str
    ):
        ArgumentNullException.if_none_or_whitespace(shipment_id, 'shipment_id')

        logger.info(f'Attempting to cancel shipment: {shipment_id}')

        response = await self._http_client.put(
            url=f'{self._base_url}/shipments/{shipment_id}/cancel',
            headers=self._get_headers(),
            timeout=None)

        logger.info(f'Response: {response.status_code}')

        return response.status_code == 204

    async def get_shipment(
        self,
        shipment_id: str
    ) -> Dict:
        ArgumentNullException.if_none_or_whitespace(shipment_id, 'shipment_id')

        logger.info(f'Get shipment: {shipment_id}')

        response = await self._http_client.get(
            url=f'{self._base_url}/shipments/{shipment_id}',
            headers=self._get_headers(),
            timeout=None)

        content = response.json()
        logger.info(f'Response status: {response.status_code}')

        return content or dict()

    async def get_rates(
        self,
        rate_request: Dict
    ) -> Dict:
        ArgumentNullException.if_none(rate_request, 'shipment')

        logger.info('Get rates for shipment')

        url = f'{self._base_url}/rates'

        response = await self._http_client.post(
            url=url,
            headers=self._get_headers(),
            json=rate_request,
            timeout=None
        )

        logger.info(f'Response status: {response.status_code}')

        try:
            content = response.json()
        except Exception as e:
            logger.exception(f'Error parsing JSON response from /v1/rates: {e}')
            raise

        return content or {}

    async def estimate_shipment(
        self,
        shipment: Dict
    ) -> Dict:
        ArgumentNullException.if_none(shipment, 'shipment')

        logger.info('Estimate shipment')

        response = await self._http_client.post(
            url=f'{self._base_url}/rates/estimate',
            json=shipment,
            headers=self._get_headers(),
            timeout=None)

        content = response.json()

        logger.info(f'Estimate shipment status: {response.status_code}')

        return content
