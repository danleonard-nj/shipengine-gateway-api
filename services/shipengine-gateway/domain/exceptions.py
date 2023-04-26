

class InvalidOriginException(Exception):
    def __init__(self) -> None:
        super().__init__(
            'Either a shipper ID or an origin address is required')


class ShipmentNotFoundException(Exception):
    def __init__(self, shipment_id: str, *args: object) -> None:
        super().__init__(
            f"No shipment with the ID '{shipment_id}' exists")


class ShipEngineClientException(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(
            f"Failed to reach ShipEngine client: {message}")


class ShipmentLabelException(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message)
