from Src.Core.abstract_model import  abstract_model
from Src.Models.unit_model import unit_model
from Src.Logics.storage_manager import storage_manager
import datetime

class transaction_model(abstract_model):
    __unit: unit_model = None
    __storage: storage_manager = None
    __item: item_model = None


    # +Поступление
    # -Списание

    __value: float

