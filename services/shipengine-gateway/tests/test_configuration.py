

import unittest

from framework.configuration.configuration import Configuration

from utilities.provider import ContainerProvider


class ConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        container = ContainerProvider.get_container()
        self.configuration = container.resolve(Configuration)

    def test_redis_configuration(self):
        self.assertIsNotNone(self.configuration.redis)
        self.assertIsNotNone(self.configuration.redis.get('host'))
        self.assertIsNotNone(self.configuration.redis.get('port'))

    def test_shipengine_configuration(self):
        self.assertIsNotNone(self.configuration.shipengine)
        self.assertIsNotNone(self.configuration.shipengine.get('base_url'))
        self.assertIsNotNone(self.configuration.shipengine.get('api_key'))

    def test_azure_ad_configuration(self):
        self.assertIsNotNone(self.configuration.auth)
        self.assertIsNotNone(self.configuration.auth.get('tenant_id'))
        self.assertIsNotNone(self.configuration.auth.get('audiences'))
        self.assertIsNotNone(self.configuration.auth.get('issuer'))
        self.assertIsNotNone(self.configuration.auth.get('identity_url'))
