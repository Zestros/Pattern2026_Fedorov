"""Модульные проверки свойств DTO и HTTP-декоратора."""
import pytest
from Src.Core.exception import arguments_exception
from Src.Dtos.report_data_dto import report_data_dto
from Src.Dtos.report_field_dto import report_field_dto
from Src.Dtos.report_row_dto import report_row_dto
from Src.Dtos.report_result_dto import report_result_dto
from Src.Logics.csv_report import csv_report
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
