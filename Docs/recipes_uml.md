# UML-диаграммы моделей технологических карт

Диаграммы описывают текущую реализацию в `Src/Models`.
Обозначения: `+` — публичный член, `-` — приватный, `$` — статический метод.
Свойства Python показаны как атрибуты. `number` сокращает `int | float`,
`optional_number` — `int | float | None`. Треугольник обозначает наследование,
пустой ромб — хранение ссылок без исключительного владения, пунктир — зависимость.

## Продукт, карта и строка состава

```mermaid
classDiagram
    direction TB

    class abstract_model {
        +str unique_code
    }
    class entity_model {
        +str name
    }
    class item_model {
        +str full_name
        +group_model group
        +unit_model unit
        +ratio_value_model mass_ratio
        +calculate_mass(quantity, target_unit, source_unit) float
        +create_flour(group, kilogram) item_model$
        +create_water(group, kilogram, liter) item_model$
        +create_oil(group, kilogram, liter) item_model$
        +create_salt(group, kilogram) item_model$
    }
    class recipe_item_model {
        +recipe_model recipe
        +optional_number output_quantity
        +calculate_mass(quantity, target_unit, source_unit) float
        +calculate_packaging_mass(quantity, target_unit) float
        +create_dough(group, kilogram, liter) recipe_item_model$
        +create_flatbreads(dough, piece) recipe_item_model$
    }
    class recipe_model {
        +unit_model mass_unit
        +number mass_coefficient
        +tuple~recipe_ingredient_model~ ingredients
        +float gross_weight
        +float net_weight
        +float packaging_weight
        +add_ingredient(item, quantity, is_packaging) recipe_ingredient_model
        +remove_ingredient(ingredient) None
        -__check_cycles(path) None
        -__food_weight() float
    }
    class recipe_ingredient_model {
        +item_model item
        +number quantity
        +bool is_packaging
        +recipe_model recipe
    }
    class validator {
        +validate(value, type_, len_, field) bool$
        +validate_number(value, field, allow_zero) bool$
    }

    abstract_model <|-- entity_model
    entity_model <|-- item_model
    item_model <|-- recipe_item_model
    entity_model <|-- recipe_model
    abstract_model <|-- recipe_ingredient_model

    recipe_item_model "0..*" --> "1" recipe_model : recipe
    recipe_model "0..*" o-- "0..*" recipe_ingredient_model : ingredients
    recipe_ingredient_model "0..*" --> "1" item_model : item
    recipe_ingredient_model ..> recipe_model : recipe вычисляется через item
    recipe_model ..> item_model : calculate_mass
    recipe_model ..> recipe_item_model : вложенная упаковка
    recipe_model ..> validator : проверка аргументов
    recipe_ingredient_model ..> validator : проверка количества
    recipe_item_model ..> validator : проверка выхода
```

### Ответственность моделей

- **`item_model`** хранит характеристики обычного продукта и рассчитывает массу
  через перевод единиц или `mass_ratio`.
- **`recipe_item_model`** наследует номенклатуру и связывает составной продукт
  с его картой. При заданном `output_quantity` вычисляет долю нетто партии;
  без него количество означает готовую массу весового продукта.
- **`recipe_ingredient_model`** хранит количество и назначение продукта
  в конкретной карте. `item` и `is_packaging` доступны только для чтения,
  `quantity` изменяется через валидируемый сеттер. Свойство `recipe` возвращает
  карту составного продукта либо `None`, отдельная ссылка не хранится.
- **`recipe_model`** управляет составом, проверяет циклы до добавления строки
  и вычисляет итоговые массы. `add_ingredient()` создаёт и возвращает строку;
  также допускается передача готовой строки.

Один продукт может использоваться во многих строках. Текущая реализация
позволяет передать одну строку в разные карты, поэтому связь карты со строками
показана агрегацией, а не исключительным владением. Повторное добавление той же
строки в одну карту запрещено. Удаление выполняется по идентичности строки.

Ссылка `recipe_item_model.recipe` доступна только для чтения. Проверка циклов
обходит текущий путь вложенных карт: прямые и косвенные циклы запрещены,
общий полуфабрикат в разных ветках разрешён.

### Расчёт массы

Все массы карты выражаются в её `mass_unit`:

```text
Входная пищевая масса = сумма масс строк, не помеченных упаковкой
Брутто = входная пищевая масса + упаковка
Нетто = входная пищевая масса × коэффициент выхода
```

Масса пищевой строки составного продукта берётся из готового нетто вложенной
карты с учётом доли партии либо из заданного количества готового весового
продукта. Упаковка вложенных карт переносится отдельно и не умножается на
коэффициент обработки. Брутто текущей карты не является суммарным расходом
исходного сырья по всей цепочке производства.

Массы вычисляются при обращении к свойствам. Изменение количества, добавление
и удаление строк не требуют отдельного обновления сумм.

## Единицы и характеристики массы

```mermaid
classDiagram
    direction LR

    class abstract_model
    class entity_model
    class item_model {
        +unit_model unit
        +ratio_value_model mass_ratio
        +calculate_mass(quantity, target_unit, source_unit) float
    }
    class unit_model {
        +number coefficient
        +unit_model base_unit
        +convert_to(quantity, target_unit) float
    }
    class ratio_unit_model {
        +unit_model numerator_unit
        +unit_model denominator_unit
        +convert_to(value, target_unit) float
        +grams_per_milliliter(gram, milliliter) ratio_unit_model$
        +kilograms_per_liter(kilogram, liter) ratio_unit_model$
        +grams_per_piece(gram, piece) ratio_unit_model$
        +kilograms_per_piece(kilogram, piece) ratio_unit_model$
    }
    class ratio_value_model {
        +number value
        +ratio_unit_model unit
        +calculate_mass(quantity, source_unit, target_unit) float
    }

    abstract_model <|-- entity_model
    entity_model <|-- item_model
    entity_model <|-- unit_model
    abstract_model <|-- ratio_unit_model
    abstract_model <|-- ratio_value_model

    item_model "0..*" --> "1" unit_model : единица учёта
    item_model "0..*" --> "0..1" ratio_value_model : mass_ratio
    ratio_value_model "0..*" --> "1" ratio_unit_model : unit
    ratio_unit_model "0..*" --> "1" unit_model : numerator_unit
    ratio_unit_model "0..*" --> "1" unit_model : denominator_unit
    unit_model "0..*" --> "1" unit_model : base_unit
```

`mass_ratio` необязателен: для муки достаточно перевода кг в г, для воды
и масла применяется плотность, для упаковки в штуках — масса одной штуки.
Совместимость определяется базовыми единицами справочника, а не названиями.
Физический вид величины отдельно не хранится: корректную единицу массы
передаёт вызывающий код.

