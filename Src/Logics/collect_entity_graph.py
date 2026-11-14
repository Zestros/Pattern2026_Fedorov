from collections.abc import Iterable

from Src.Core.entity_model import entity_model


def collect_entity_graph(roots: Iterable[entity_model]) -> tuple[entity_model, ...]:
    """Дополняет исходный набор связанными сущностями, сохраняя общие экземпляры."""
    entities = list(roots)
    visited = {id(entity) for entity in entities}
    pending = list(reversed(entities))
    while pending:
        entity = pending.pop()
        children = []
        for _, target in entity.references():
            if id(target) not in visited:
                visited.add(id(target))
                entities.append(target)
                children.append(target)
        pending.extend(reversed(children))
    return tuple(entities)
