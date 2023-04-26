from api_base import ApiTest


class ShipmentTests(ApiTest):
    async def test_get_shipments(self):
        result = await self.send_request(
            method='GET',
            endpoint='/api/shipment?page_number=1&page_size=1')

        self.assertEqual(200, result.status_code)
        self.assertIsNotNone(result.json)
