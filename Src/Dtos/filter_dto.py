

class filter_item_dto:
    __field_name: str = ""
    __field_type: str = ""
    __value: str = ""


class filter_dto:
    __filters:list[filter_item_dto] = []
