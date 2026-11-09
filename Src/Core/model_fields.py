from inspect import getattr_static

from Src.Core.exception import arguments_exception


def set_public_fields(instance: object, fields: dict[str, object]) -> None:
    """Присваивает публичные поля, вызывая сеттеры свойств модели."""
    for name, value in fields.items():
        if not isinstance(name, str) or name.startswith("_"):
            raise arguments_exception("fields", "Ожидаются публичные именованные поля")
        descriptor = getattr_static(type(instance), name, None)
        if callable(descriptor):
            raise arguments_exception(name, "Нельзя заменять метод значением поля")
        if isinstance(descriptor, property) and descriptor.fset is None:
            raise arguments_exception(name, "Неизвестное поле только для чтения")
        setattr(instance, name, value)
