from Src.Dtos.filter_dto import filter_dto
from Src.Core.abstract_prototype import abstract_prototype

class prototype(abstract_prototype):
    __filters:filter_dto = []

    def clone(self, filtes:filter_dto):
        
        for item in filter:
            # ...
            self.__data = []
        result = prototype(self.__data)
        return result