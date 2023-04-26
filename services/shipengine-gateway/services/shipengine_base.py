from clients.shipengine_client import ShipEngineClient

from framework.logger.providers import get_logger

logger = get_logger(__name__)


class ShipEngineBase:
    def __init__(
        self,

    ):
        self.__client: ShipEngineClient = container.resolve(ShipEngineClient)
