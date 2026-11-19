from abc import ABC, abstractmethod
from Src.Dtos.filter_dto import filter_dto

class abstract_prototype(ABC):
    __data:list =[]

    def __init__(self, data:list):
        super().__init__()
        pass