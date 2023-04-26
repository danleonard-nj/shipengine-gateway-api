import pytest
from api_base import ApiTest
from app import app


class CarrierTests(ApiTest):
    async def test_get_service_codes(self):
        result = await self.send_request(
            method='GET',
            endpoint='/api/carriers/services')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)

    async def test_get_balances(self):
        result = await self.send_request(
            method='GET',
            endpoint='/api/carriers/balances')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)
