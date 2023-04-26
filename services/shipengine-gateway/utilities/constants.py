
class Environment:
    DEVELOPMENT = 'Development'
    PRODUCTION = 'Production'
    ENV = 'FLASK_ENV'


class ConfigurationSource:
    DEVELOPMENT = 'config.dev.json'
    PRODUCTION = 'config.json'


class ConfigurationKey:
    DIAGNOSTIC_RESPONSE_ENABLED = 'diagnostic_response_enabled'
    CORS = 'cors'
    CORS_HEADERS = 'headers'
    CORS_ORIGIN = 'origin'
    TELEMETRY_ROLE_NAME = 'role_name'
    SECURITY_IDENTITY_URL = 'identity_url'
    SECURITY_IDENTITY_CLIENT_ID = 'client_id'
    SECURITY_IDENTITY_CLIENT_SECRET = 'client_secret'
    SECURITY_IDENTITY_CLIENT_GRANT_TYPE = 'grant_type'
    SECURITY_IDENTITY_CLIENT_SCOPE = 'client_scope'
    SECURITY_IDENTITY_CLIENT_NAME = 'name'
    SECURITY_IDENTITY_CLIENTS = 'clients'


class TelemtryKey:
    SQLALCHEMY_QUERY = 'sqlalchemy.query'
    APP_INSIGHTS_ROLE_KEY = 'ai.cloud.role'
