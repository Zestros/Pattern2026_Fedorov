from abc import ABC



class abstract_manager(ABC):
    """
    Абстрактный класс для реализации загрузки и обработки данных
    """

    # Полный путь к файлу
    _file_name: str = ""
    # Флаг. Загрузка и обработка данных завершена успешно
    _is_loaded: bool = False
    # Сырые данные
    _data: dict | None = None

    def load(self, name: str = "") -> None:
        """
        Загрузка данных
        """
        pass



    def convert(self) -> bool:
        """
        Обработать загруженные данные
        """
        return False

    def is_loaded(self) -> bool:
        return self._is_loaded
