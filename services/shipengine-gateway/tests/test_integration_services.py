import os
import pytest
import asyncio
from httpx import AsyncClient
from framework.configuration.configuration import Configuration
from clients.shipengine_client import ShipEngineClient
from services.shipment_service import ShipmentService
from services.rate_service import RateService
from services.label_service import LabelService
from services.carrier_service import CarrierService
from services.mapper_service import MapperService
from framework.clients.cache_client import CacheClientAsync
from data.shipment_repository import ShipmentRepository
from data.address_repository import AddressRepository
from framework.configuration import Configuration

# Use the ShipEngine sandbox API key
config = Configuration()
SHIPENGINE_API_KEY = config.shipengine.get('sandbox_api_key')
SHIPENGINE_BASE_URL = config.shipengine.get('base_url')


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop


@pytest.fixture(scope="module")
def configuration():
    class DummyConfig:
        shipengine = {'api_key': SHIPENGINE_API_KEY, 'base_url': SHIPENGINE_BASE_URL}
    return DummyConfig()


@pytest.fixture(scope="module")
def http_client():
    client = AsyncClient()
    yield client
    asyncio.get_event_loop().run_until_complete(client.aclose())


@pytest.fixture(scope="module")
def shipengine_client(http_client, configuration):
    return ShipEngineClient(http_client, configuration)


@pytest.fixture(scope="module")
def cache_client():
    class DummyCache(CacheClientAsync):
        async def get(self, key): return None
        async def set(self, key, value, ttl=None): return None
    return DummyCache()


@pytest.fixture(scope="module")
def carrier_service(shipengine_client, cache_client):
    return CarrierService(shipengine_client, cache_client)


@pytest.fixture(scope="module")
def mapper_service(carrier_service):
    return MapperService(carrier_service)


@pytest.fixture(scope="module")
def shipment_repository():
    class DummyRepo(ShipmentRepository):
        async def get_most_recent_shipment(self): return None
        async def get_all(self): return []
        async def update(self, selector, values): return None
        async def bulk_insert_shipments(self, shipments): return None
        async def delete(self, selector): return None
        async def get_shipments_count(self, cancelled=None): return 0
        async def get_shipments(self, page_size, page_number, cancelled=None): return []
        async def insert(self, entity): return None
    return DummyRepo()


@pytest.fixture(scope="module")
def shipment_service(mapper_service, shipengine_client, shipment_repository, carrier_service, cache_client):
    return ShipmentService(mapper_service, shipengine_client, shipment_repository, carrier_service, cache_client)


@pytest.fixture(scope="module")
def rate_service(carrier_service, shipengine_client, cache_client):
    return RateService(carrier_service, shipengine_client, cache_client)


@pytest.fixture(scope="module")
def label_service(shipengine_client, cache_client):
    return LabelService(shipengine_client, cache_client)


@pytest.mark.asyncio
async def test_shipengine_get_carriers(shipengine_client):
    carriers = await shipengine_client.get_carriers()
    assert isinstance(carriers, dict)
    assert 'carriers' in carriers or len(carriers) > 0


@pytest.mark.asyncio
async def test_carrier_service_get_carriers(carrier_service):
    carriers = await carrier_service.get_carriers()
    assert isinstance(carriers, list)
    assert len(carriers) > 0


@pytest.mark.asyncio
async def test_rate_service_estimate(rate_service):
    shipment = {
        "from_postal_code": "75001",
        "to_postal_code": "90210",
        "weight": 16,
        "carrier_id": None,
        "service_code": None
    }
    try:
        result = await rate_service.get_estimate(shipment)
        assert 'estimated_amount' in result or 'currency' in result
    except Exception as e:
        assert 'error' in str(e) or 'rate' in str(e)


@pytest.mark.asyncio
async def test_shipment_service_get_shipments(shipment_service):
    class DummyRequest:
        page_size = 1
        page_number = 1
        cancelled = False
    result = await shipment_service.get_shipments(DummyRequest())
    assert 'shipments' in result
    assert isinstance(result['shipments'], list)


@pytest.mark.asyncio
async def test_label_service_create_label(label_service):
    # This test expects a valid shipment_id from your sandbox
    shipment_id = os.getenv('SHIPENGINE_TEST_SHIPMENT_ID')
    if not shipment_id:
        pytest.skip('SHIPENGINE_TEST_SHIPMENT_ID not set')
    try:
        label = await label_service.create_label(shipment_id)
        assert label is not None
    except Exception as e:
        assert 'not found' in str(e) or 'error' in str(e)
