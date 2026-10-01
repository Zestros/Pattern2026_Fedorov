from Src.Core.exception import arguments_exception

"""
Исключение при выполнении бизнес операции
"""  
class operation_exception(Exception):
    pass  


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
