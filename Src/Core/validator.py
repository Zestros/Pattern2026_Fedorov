from Src.Core.exception import arguments_exception
import math

class operation_exception(Exception):
    """Ошибка выполнения бизнес-операции с описанием причины."""

    def __init__(self, message: str = "") -> None:
        """Передаёт сообщение базовому классу исключений."""
        super().__init__(message)


class validator:
    """
    Набор проверок данных
    """
    @staticmethod
    def validate(
        value,
        type_,
        len_: int | None = None,
        field: str = "value",
    ) -> bool:
        """Проверяет тип, непустую строку и её максимальную длину."""
        if value is None:
            raise arguments_exception(field, "Аргумент не может быть None")

        if not isinstance(value, type_):
            raise arguments_exception(
                field,
                f"Ожидается тип {type_}, получен {type(value).__name__}",
            )

        if isinstance(value, str):
            text = value.strip()

            if not text:
                raise arguments_exception(
                    field,
                    "Строка не может быть пустой",
                )

            if len_ is not None and len(text) > len_:
                raise arguments_exception(
                    field,
                    f"Длина строки не должна превышать {len_} символов",
                )

        return True

    @staticmethod
    def validate_number(
        value: int | float,
        field: str,
        allow_zero: bool = True,
    ) -> bool:
        """Проверяет тип, конечность и допустимый диапазон числа."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise arguments_exception(field, "Ожидается число")

        if isinstance(value, float) and not math.isfinite(value):
            raise arguments_exception(field, "Число должно быть конечным")

        if value < 0 or (not allow_zero and value == 0):
            raise arguments_exception(
                field,
                "Ожидается неотрицательное число"
                if allow_zero
                else "Ожидается положительное число",
            )

        return True