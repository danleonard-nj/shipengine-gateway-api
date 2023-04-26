from framework.abstractions.abstract_request import RequestContextProvider
from framework.auth.azure import AzureAd
from framework.auth.configuration import AzureAdConfiguration
from framework.clients.cache_client import CacheClientAsync
from framework.configuration.configuration import Configuration
from framework.di.service_collection import ServiceCollection
from framework.di.static_provider import ProviderBase
from httpx import AsyncClient
from quart import Quart, request

from clients.shipengine_client import ShipEngineClient
from services.carrier_service import CarrierService
from services.label_service import LabelService
from services.mapper_service import MapperService
from services.rate_service import RateService
from services.shipment_service import ShipmentService


class AdRole:
    ShipEngineRead = 'ShipEngine.Read'
    ShipEngineWrite = 'ShipEngine.Write'


def configure_http_client(container):
    return AsyncClient(timeout=None)


def configure_azure_ad(container):
    configuration = container.resolve(Configuration)

    # Hook the Azure AD auth config into the service
    # configuration
    ad_auth: AzureAdConfiguration = configuration.ad_auth
    azure_ad = AzureAd(
        tenant=ad_auth.tenant_id,
        audiences=ad_auth.audiences,
        issuer=ad_auth.issuer)

    azure_ad.add_authorization_policy(
        name='read',
        func=lambda t: AdRole.ShipEngineRead in t.get('roles'))

    azure_ad.add_authorization_policy(
        name='write',
        func=lambda t: AdRole.ShipEngineWrite in t.get('roles'))

    return azure_ad


class ContainerProvider(ProviderBase):
    @classmethod
    def configure_container(cls):
        descriptors = ServiceCollection()

        descriptors.add_singleton(Configuration)
        descriptors.add_singleton(CacheClientAsync)

        descriptors.add_singleton(
            dependency_type=AsyncClient,
            factory=configure_http_client)

        descriptors.add_singleton(
            dependency_type=AzureAd,
            factory=configure_azure_ad)

        descriptors.add_singleton(MapperService)
        descriptors.add_singleton(ShipEngineClient)
        descriptors.add_singleton(CarrierService)

        descriptors.add_transient(LabelService)
        descriptors.add_transient(RateService)
        descriptors.add_transient(ShipmentService)

        return descriptors
