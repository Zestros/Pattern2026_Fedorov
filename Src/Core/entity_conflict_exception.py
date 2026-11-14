from Src.Core.exception import arguments_exception


class entity_conflict_exception(arguments_exception):
    """Операция конфликтует с существующим кодом или входящими ссылками."""
