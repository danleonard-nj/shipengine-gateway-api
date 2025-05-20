from dataclasses import fields
from typing import Any, Union, get_origin, get_args


def first_or_default(_iterable):
    try:
        return _iterable[0]
    except:
        return None


class ValidatableDataclass:
    def __post_init__(self):
        for field_def in fields(self):
            value = getattr(self, field_def.name)
            self.validate_field(field_def.name, value, field_def.type)

    @staticmethod
    def is_optional(annotation: Any) -> bool:
        # Checks if the annotation is Optional[...] (i.e. Union[..., None])
        return get_origin(annotation) is Union and type(None) in get_args(annotation)

    @classmethod
    def validate_field(cls, field_name: str, value: Any, annotation: Any):
        # Check for emptiness: treat None or any container with length 0 as empty.
        if value is None:
            if not cls.is_optional(annotation):
                raise ValueError(f"Field '{field_name}' cannot be empty.")
