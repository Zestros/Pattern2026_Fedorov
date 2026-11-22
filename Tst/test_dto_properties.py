"""Модульные проверки свойств DTO и HTTP-декоратора."""
import pytest
from Src.Core.exception import arguments_exception
from Src.Core.filter_operator_enum import filter_operator_enum
from Src.Core.sort_direction_enum import sort_direction_enum
from Src.Dtos.filter_dto import filter_dto
from Src.Dtos.filter_item_dto import filter_item_dto
from Src.Dtos.report_data_dto import report_data_dto
from Src.Dtos.report_field_dto import report_field_dto
from Src.Dtos.report_row_dto import report_row_dto
from Src.Dtos.report_result_dto import report_result_dto
from Src.Dtos.sort_item_dto import sort_item_dto
from Src.Dtos.turnover_row_dto import turnover_row_dto
from Src.Logics.csv_report import csv_report
from Src.Logics.dto_serializer import dto_serializer
from Src.Api.http_report import http_report


def test_read_only_properties_report_data_snapshot():
    """<summary>DTO копирует коллекции и предоставляет только читаемые свойства.</summary>"""
    # Подготовка
    values = [1, None]
    # Действие
    data = report_data_dto('Тест', (('Поле', 2),), ('A', 'B'), (values,))
    values[0] = 99
    # Проверка
    assert data.fields[0].name == 'Поле'
    assert data.fields[0].value == '2'
    assert data.rows[0].values == ('1', '')
    with pytest.raises(AttributeError):
        data.title = 'Другое'


@pytest.mark.parametrize('create', [
    lambda: report_field_dto('Поле', 1),
    lambda: report_row_dto((1,)),
    lambda: report_result_dto(1, 'text/plain', 'txt'),
])
def test_rejected_properties_dto_wrong_types(create):
    """<summary>Некорректные типы полей DTO отклоняются при создании.</summary>"""
    # Подготовка: конструктор передаётся параметром.
    # Действие и Проверка
    with pytest.raises(arguments_exception):
        create()


def test_attachment_http_report_delegated_csv():
    """<summary>HTTP-декоратор сохраняет результат CSV и выставляет заголовки файла.</summary>"""
    # Подготовка
    report = http_report(csv_report())
    data = report_data_dto('Тест', (('Поле', 'Значение'),))
    # Действие
    result = report.build(data)
    response = report.make_report_response(result)
    # Проверка
    assert response.data == result.content
    assert response.mimetype == 'text/csv'
    assert 'attachment' in response.headers['Content-Disposition']
    assert 'report.csv' in response.headers['Content-Disposition']


@pytest.mark.parametrize('dto, property_name', [
    (report_field_dto('Поле', ''), 'name'),
    (report_field_dto('Поле', ''), 'value'),
    (report_row_dto(('',)), 'values'),
    (report_data_dto('', ()), 'fields'),
    (report_data_dto('', ()), 'columns'),
    (report_data_dto('', ()), 'rows'),
    (report_result_dto('', 'text/plain', 'txt'), 'content'),
    (report_result_dto('', 'text/plain', 'txt'), 'media_type'),
    (report_result_dto('', 'text/plain', 'txt'), 'file_extension'),
    (report_result_dto('', 'text/plain', 'txt'), 'download'),
])
def test_rejected_assignment_dto_read_only(dto, property_name):
    """<summary>Закрытые методы установки не открывают публичное изменение свойств.</summary>"""
    # Подготовка
    previous = getattr(dto, property_name)
    # Действие и Проверка
    with pytest.raises(AttributeError):
        setattr(dto, property_name, None)
    assert getattr(dto, property_name) == previous


@pytest.mark.parametrize('fields, columns, rows', [
    (None, (), ()),
    ((('Имя',),), (), ()),
    ((), 'Колонка', ()),
    ((), ('Колонка',), ('строка',)),
    ((), ('Колонка',), ((1, 2),)),
])
def test_rejected_structure_report_data_invalid_table(fields, columns, rows):
    """<summary>Неверная структура полей или таблицы вызывает предметную ошибку.</summary>"""
    # Подготовка: некорректная структура передана параметрами.
    # Действие и Проверка
    with pytest.raises(arguments_exception):
        report_data_dto('', fields, columns, rows)


def test_serialized_assignment_filter_dto_preserves_defaults_and_presence():
    """<summary>Сеттеры фиксируют переданные правила, а пропущенное направление остаётся ASC.</summary>"""
    # Подготовка
    codec = dto_serializer()
    criteria = codec.deserialize({}, filter_dto)
    ordering = codec.deserialize({"field": "group.name"}, sort_item_dto)
    condition = filter_item_dto(field="name", operator=filter_operator_enum.LIKE, value="Мук")

    # Действие
    criteria.filters = (condition,)
    criteria.sort = (ordering,)
    implicit = codec.serialize(criteria)
    ordering.direction = sort_direction_enum.DESC

    # Проверка
    assert implicit == {
        "filters": [{"field": "name", "operator": "LIKE", "value": "Мук"}],
        "sort": [{"field": "group.name"}],
    }
    assert criteria.contains("filters") and criteria.contains("sort")
    assert codec.deserialize({"field": "name"}, sort_item_dto).direction is sort_direction_enum.ASC
    assert codec.serialize(criteria)["sort"] == [{"field": "group.name", "direction": "DESC"}]


@pytest.mark.parametrize(("target", "data", "missing"), [
    (filter_item_dto, {"operator": "EQUALS", "value": "Мука"}, "field"),
    (filter_item_dto, {"field": "name", "value": "Мука"}, "operator"),
    (filter_item_dto, {"field": "name", "operator": "LIKE"}, "value"),
    (sort_item_dto, {}, "field"),
])
def test_required_property_deserialize_dto_checks_missing_fields(target, data, missing):
    """<summary>Сериализатор требует обязательные свойства, даже если у класса есть их геттеры.</summary>"""
    # Действие и проверка
    with pytest.raises(arguments_exception, match=f"Поле: {missing}"):
        dto_serializer().deserialize(data, target)


def test_rejected_assignment_filter_dto_invalid_values_preserves_previous():
    """<summary>Сеттеры отклоняют закрытый путь, пустой текст, неверную операцию и чужой тип правила.</summary>"""
    # Подготовка
    criteria = filter_dto()
    condition = filter_item_dto(field="name", operator=filter_operator_enum.EQUALS, value="Мука")

    # Действие и проверка
    with pytest.raises(arguments_exception, match="Поле: field"):
        condition.field = "group._hidden.name"
    with pytest.raises(arguments_exception, match="Поле: value"):
        condition.value = " "
    with pytest.raises(arguments_exception, match="Поле: operator"):
        condition.operator = "LIKE"
    with pytest.raises(arguments_exception, match="Поле: sort"):
        criteria.sort = (condition,)
    assert condition.field == "name"
    assert condition.value == "Мука"
    assert condition.operator is filter_operator_enum.EQUALS
    assert criteria.sort == () and not criteria.contains("sort")


def test_validated_assignment_turnover_row_dto_distinguishes_balances_and_movements():
    """<summary>Строка ОСВ допускает отрицательные остатки, а обороты и подписи проверяются сеттерами.</summary>"""
    # Подготовка
    row = turnover_row_dto(
        warehouse_code="main", warehouse_name="Основной склад",
        item_code="flour", item_name="Мука", unit_code="gram", unit_name="грамм",
        opening=-2, receipts=1, issues=4, closing=-5,
    )

    # Действие и проверка
    with pytest.raises(arguments_exception, match="Поле: receipts"):
        row.receipts = -1
    with pytest.raises(arguments_exception, match="Поле: closing"):
        row.closing = float("inf")
    with pytest.raises(arguments_exception, match="Поле: opening"):
        row.opening = True
    with pytest.raises(arguments_exception, match="Поле: warehouse_name"):
        row.warehouse_name = ""
    assert (row.opening, row.receipts, row.closing) == (-2, 1, -5)
