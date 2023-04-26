from framework.logger.providers import get_logger

logger = get_logger(__name__)


def get_expected_type_string(_type):
    if isinstance(_type, tuple):
        return ', '.join([x.__name__ for x in _type])
    else:
        return _type.__name__


class FieldTypeException(Exception):
    def __init__(self, message):
        super().__init__(message)


class FieldValueException(Exception):
    def __init__(self, message):
        super().__init__(message)


class Field:
    def __init__(self, name, value, required=False, _type=None):
        self.name = name
        self.value = value

        if _type and not isinstance(_type, (tuple, type)):
            raise Exception("'_type' must be either a tuple or a type")
        self._type = _type

        self.required = required

    @staticmethod
    def validate_fields(obj):
        for prop in obj.__dict__:
            if isinstance(obj.__dict__[prop], Field):
                field = obj.__dict__[prop]
                if field.required and not field.value:
                    raise FieldValueException(
                        f"No value provided for required field '{field.name}'")

                if field._type:
                    if not isinstance(field.value, field._type) and not (not field.required and field.value is None):
                        raise FieldTypeException(
                            f"Received type '{type(field.value).__name__}' but expected type '{get_expected_type_string(field._type)}' for field '{field.name}'")


class FieldClass:
    def create_backing_fields(self):
        '''
        Creates backing attributes for field objects to preserve the metadata (type,
        required state, etc) while exposing the original attributes as normal values

        self.id = Field(name='id', value='123') -> self.field__id with self.id = '123'
        '''

        obj = self.__dict__.copy()
        for key in self.__dict__:
            if isinstance(self.__dict__[key], Field):
                # logger.info(f'Creating backing metadata for field {key}')

                field: Field = self.__dict__[key]
                field_key = f'field__{key}'
                obj[field_key] = field
                obj[field.name] = field.value

        self.__dict__.update(obj)
        # logger.info(self.__dict__)

    def validate(self):
        Field.validate_fields(self)

    def get_attributes(self):
        return [x for x in self.__dict__ if '__' not in x]
