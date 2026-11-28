from Src.Core.abstract_observation import abstract_observation


class observer:
    __handlers: list[abstract_observation] = []

    @classmethod
    def add(cls, source: abstract_observation) -> None:
        if source not in cls.__handlers:
            cls.__handlers.append(source)

    @classmethod
    def delete(cls, source: abstract_observation) -> None:
        if source in cls.__handlers:
            cls.__handlers.remove(source)

    @classmethod
    def notify(cls) -> None:
        for handler in cls.__handlers.copy():
            handler.update()