from dotenv import load_dotenv
from framework.abstractions.abstract_request import RequestContextProvider
from framework.di.static_provider import InternalProvider
from framework.logger.providers import get_logger
from quart import Quart

from routes.carriers import carrier_bp
from routes.health import health_bp
from routes.labels import label_bp
from routes.rates import rates_bp
from routes.shipment import shipment_bp
from routes.address import address_bp
from utilities.provider import ContainerProvider

load_dotenv()

logger = get_logger(__name__)

# Insufficient funds code
# 0x00560101

app = Quart(__name__)

app.register_blueprint(health_bp)
app.register_blueprint(shipment_bp)
app.register_blueprint(carrier_bp)
app.register_blueprint(rates_bp)
app.register_blueprint(label_bp)
app.register_blueprint(address_bp)

provider = ContainerProvider.initialize_provider()


@app.before_serving
async def startup():
    RequestContextProvider.initialize_provider(
        app=app)


if __name__ == '__main__':
    app.run(debug=True, port='5088')
