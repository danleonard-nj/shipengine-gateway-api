from api_base import ApiTest


class HealthTests(ApiTest):
    async def test_alive(self):
        result = await self.send_request(
            method='GET',
            endpoint='/api/health/alive')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)

    async def test_alive(self):
        result = await self.send_request(
            method='GET',
            endpoint='/api/health/ready')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)
