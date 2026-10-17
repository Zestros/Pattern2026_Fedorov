"""Модульные проверки контрактов подготовки и представления отчёта."""

import pytest

from Src.Core.exception import arguments_exception
from Src.Dtos.report_data_dto import report_data_dto
from Src.Logics.text_report import text_report


def test_rejected_report_data_dto_mismatched_row():
    """<summary>Строка без значения для объявленного столбца отклоняется.</summary>"""
    # Подготовка
    # Действие и Проверка
    with pytest.raises(arguments_exception):
        report_data_dto("Отчёт", (), ("Код", "Название"), (("123",),))


def test_correct_text_report_build_fields_without_table():
    """<summary>Поля выводятся без таблицы; API получает текст и его MIME-тип.</summary>"""
    # Подготовка
    # Действие
    data = report_data_dto("Единица измерения", (("Название", "грамм"),))
    result = text_report().build(data)
    # Проверка
    assert result.content == "Единица измерения\nНазвание: грамм"
    assert result.media_type == "text/plain"
    assert result.file_extension == "txt"
    assert result.download is False
