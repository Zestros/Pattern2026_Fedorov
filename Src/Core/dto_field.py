from inspect import getattr_static


class dto_field:
    """Тип поля и простые правила его передачи и связывания."""
    def __init__(self, name: str, field_type: object, dto_type: type) -> None:
        """Читает правила поля из описания DTO с учётом наследования."""
        self.name = name
        self.type = field_type
        self.reference = None
        self.read_only = False
        self.optional = False
        self.has_default = hasattr(dto_type, name) and not isinstance(getattr_static(dto_type, name), property)
        for parent in reversed(dto_type.__mro__):
            self.reference = parent.__dict__.get("_references", {}).get(name, self.reference)
            self.read_only |= name in parent.__dict__.get("_read_only_fields", ())
            self.optional |= name in parent.__dict__.get("_optional_fields", ())
