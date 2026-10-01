# UML-диаграммы менеджеров
Обозначения: `+` — публичный член, `#` — защищённый, `-` — приватный; `$` — член класса. Свойства Python показаны как атрибуты. Стрелка с треугольником означает наследование, пунктирная — зависимость, пустой ромб — хранение ссылок на объекты без исключительного владения ими.

## Менеджер настроек

```mermaid
classDiagram
    direction TB
    class abstract_manager {
        <<abstract>>
        #str _file_name
        #bool _is_loaded
        #dict _data
        +load(name) None
        +convert() bool
        +is_loaded() bool
    }
    class setting_manager {
        <<Singleton>>
        +setting_manager instance$
        -str __default_file_name$
        -settings_model __settings
        +__new__(cls) setting_manager
        +load(file_name) None
        +convert() bool
        +settings_model settings
    }
    class settings_model {
        +company_model company
        +str boss_name
        +str account_name
        +bool first_start
    }
    class company_model {
        +str name
        +str inn
        +str bik
        +str account
        +str ownership_form
    }
    class validator {
        +validate(value, type_, len_, field) bool$
    }
    class operation_exception {
        <<exception>>
    }

    abstract_manager <|-- setting_manager
    setting_manager "1" --> "0..1" settings_model : settings
    settings_model "1" --> "0..1" company_model : company
    setting_manager ..> company_model : создаёт при convert
    setting_manager ..> validator : проверяет имя файла
    settings_model ..> validator : проверяет свойства
    setting_manager ..> operation_exception : выбрасывает при ошибке
```

`load()` читает JSON в `_data`, затем вызывает `convert()`. Метод `convert()` создаёт организацию и настройки, включая `first_start`, и публикует модель только после успешного заполнения. До первого успешного преобразования настройки могут отсутствовать.

## Менеджер хранилища

```mermaid
classDiagram
    direction TB
    class abstract_manager {
        <<abstract>>
        #str _file_name
        #bool _is_loaded
        #dict _data
        +load(name) None
        +convert() bool
        +is_loaded() bool
    }
    class storage_manager {
        <<Singleton>>
        -storage_manager __instance$
        -bool __initialized
        -settings_model __settings
        -list~warehouse_model~ __warehouses
        -list~unit_model~ __units
        -list~item_model~ __items
        -list~group_model~ __groups
        +__new__(cls, settings) storage_manager
        +__init__(settings) None
        +convert() bool
        -__add_model(value, expected_type, collection) None
        +add_warehouse(value) None
        +add_unit(value) None
        +add_item(value) None
        +add_group(value) None
        +tuple~warehouse_model~ warehouses
        +tuple~unit_model~ units
        +tuple~item_model~ items
        +tuple~group_model~ groups
    }
    class settings_model {
        +bool first_start
    }
    class warehouse_model {
        +str name
    }
    class group_model {
        +str name
    }
    class unit_model {
        +str name
        +float coefficient
        +unit_model base_unit
    }
    class item_model {
        +str name
        +str full_name
        +group_model group
        +unit_model unit
    }
    class arguments_exception {
        <<exception>>
    }
    class operation_exception {
        <<exception>>
    }

    abstract_manager <|-- storage_manager
    storage_manager "1" --> "1" settings_model : настройки
    storage_manager "1" o-- "0..*" warehouse_model : warehouses
    storage_manager "1" o-- "0..*" unit_model : units
    storage_manager "1" o-- "0..*" item_model : items
    storage_manager "1" o-- "0..*" group_model : groups
    item_model "0..*" --> "1" group_model : group
    item_model "0..*" --> "1" unit_model : unit
    unit_model "0..*" --> "1" unit_model : base_unit
    storage_manager ..> arguments_exception : неверный аргумент или дубликат
    storage_manager ..> operation_exception : ошибка подготовки
```

Для читаемости у доменных моделей показаны только связанные с хранилищем свойства, включая унаследованное `name`. Все четыре модели также имеют унаследованный `unique_code`. Тип `coefficient` в коде — `int | float`; в диаграмме он сокращён до `float`. Коллекции возвращаются как кортежи произвольной длины.

### Первый старт и повторные обращения

- Конструктор принимает готовую `settings_model` и вызывает `convert()` при первой инициализации.
- При `first_start = True` создаются группа «Бакалея», грамм, килограмм с коэффициентом 1000, «Основной склад» и номенклатура «Мука». Мука ссылается на общую группу и килограмм; грамм ссылается на себя как базовую единицу.
- При `first_start = False` коллекции остаются пустыми, подготовка завершается успешно.
- Повторное создание Singleton сохраняет данные. Повторный `convert()` после успешной подготовки возвращает `True` без пересоздания объектов.
- Методы добавления проверяют тип и совпадение `unique_code` среди всех четырёх коллекций. Для номенклатуры проверяется регистрация группы и единицы; для производной единицы — регистрация базовой.

`abstract_manager` наследует `ABC`, но его методы пока не помечены `@abstractmethod`. Обозначение `abstract` отражает назначение базового класса. Унаследованный `load()` в `storage_manager` не переопределён и остаётся заглушкой.
