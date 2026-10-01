from Src.Core.exception import arguments_exception
from Src.Models.settings_model import settings_model
from Src.Models.group_model import group_model
from Src.Models.warehouse_model import warehouse_model
from Src.Models.item_model import item_model
from Src.Models.unit_model import unit_model
from Src.Core.abstract_manager import abstract_manager


class storage_manager(abstract_manager):
    """Хранилище в памяти приложения."""
    def __new__(cls):
        """Создаёт единственный экземпляр или возвращает существующий."""
        if not hasattr(cls, 'instance'):
            cls.instance = super(storage_manager, cls).__new__(cls)
        return cls.instance

    





    