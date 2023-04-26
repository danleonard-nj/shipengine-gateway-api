from app import app
import unittest
from unittest.mock import Mock, patch


def get_mock_middleware(*args, **kwargs):
    auth_middleware = Mock()
    auth_middleware.validate_access_token = Mock(
        return_value=True)
    return auth_middleware


@patch('utilities.provider.configure_middleware')
class ApiTest(unittest.TestCase):
    def _get_mock_auth_headers(self):
        return {
            'Authorization': 'Bearer fake'
        }

    async def send_request(self, method, endpoint, auth=True, headers=None, json=None):
        with patch('utilities.provider.configure_azure_ad', get_mock_middleware):
            with app.test_client() as client:
                _headers = (headers or {}) | self._get_mock_auth_headers()
                return await client.open(
                    endpoint,
                    method=method,
                    headers=_headers,
                    data=json)
