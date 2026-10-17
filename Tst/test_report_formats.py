"""Модульные проверки форматов, фабрики и настройки формата."""

import csv
import json
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
from xml.etree.ElementTree import fromstring

import pytest

from Src.Core.report_type_enum import report_type_enum
from Src.Core.validator import operation_exception
from Src.Dtos.report_data_dto import report_data_dto
from Src.Logics.report_factory import report_factory
from Src.Logics.settings_manager import setting_manager
from Src.Models.settings_model import settings_model


class text_collector(HTMLParser):
    """Собирает текст HTML для проверки исходных значений."""

    def __init__(self):
        """Создаёт пустую коллекцию текстовых фрагментов."""
        super().__init__()
        self.values = []

    def handle_data(self, data):
        """Сохраняет текст после декодирования HTML-сущностей."""
        self.values.append(data)


@pytest.mark.parametrize("format_", list(report_type_enum))
def test_equal_values_build_all_formats(format_):
    """<summary>Все форматы сохраняют заголовок, поля, столбцы и обе строки таблицы.</summary>"""
    # Подготовка
    # Действие
    data = report_data_dto(
        "Рецепт", (("Код", "abc"),), ("Продукт", "Масса"),
        (("Мука", 405), ("Вода", 200)),
    )
    result = report_factory(settings_model()).create(format_).build(data)
    text = result.content.decode("utf-8") if result.download else result.content
    for value in ("Рецепт", "Код", "abc", "Продукт", "Масса", "Мука", "405", "Вода", "200"):
        assert value in text
    # Проверка
    assert isinstance(result.content, bytes if format_ in (
        report_type_enum.CSV, report_type_enum.MARKDOWN,
    ) else str)
    if format_ is report_type_enum.XML:
        root = fromstring(text)
        assert [[cell.text for cell in row] for row in root.find("rows")] == [
            ["Мука", "405"], ["Вода", "200"],
        ]
    if format_ is report_type_enum.CSV:
        rows = dict(list(csv.reader(StringIO(text)))[1:])
        assert rows == {
            "title": "Рецепт", "fields[0].name": "Код", "fields[0].value": "abc",
            "columns[0]": "Продукт", "columns[1]": "Масса",
            "rows[0][0]": "Мука", "rows[0][1]": "405",
            "rows[1][0]": "Вода", "rows[1][1]": "200",
        }


@pytest.mark.parametrize("format_", list(report_type_enum))
def test_preserved_special_characters_build_formats(format_):
    """<summary>Разделители, переносы и HTML-разметка не повреждают структуру отчёта.</summary>"""
    # Подготовка
    value = '<b>Мука</b> & "соль", | *тест*\nстрока'
    # Действие и Проверка
    data = report_data_dto("", (("Поле", value),))
    result = report_factory(settings_model()).create(format_).build(data)
    if format_ is report_type_enum.CSV:
        assert dict(list(csv.reader(StringIO(result.content.decode())))[1:])["fields[0].value"] == value
    elif format_ is report_type_enum.XML:
        assert fromstring(result.content).find("fields/field").text == value
    elif format_ is report_type_enum.HTML:
        parser = text_collector()
        parser.feed(result.content)
        assert value in parser.values
        assert "<b>" not in result.content
    elif format_ is report_type_enum.MARKDOWN:
        text = result.content.decode()
        assert "\\|" in text and "\\*тест\\*" in text
        assert "&lt;b&gt;" in text and "<br>строка" in text
    else:
        assert value in result.content


@pytest.mark.parametrize("format_", list(report_type_enum))
def test_selected_format_create_default_changed_settings(format_):
    """<summary>Фабрика использует текущее значение переданной модели настроек.</summary>"""
    # Подготовка
    settings = settings_model()
    factory = report_factory(settings)
    settings.response_format = format_
    # Действие и Проверка
    assert type(factory.create_default()) is type(factory.create(format_))


@pytest.mark.parametrize("raw, expected", [
    ("CSV", report_type_enum.CSV), ("Markdown", report_type_enum.MARKDOWN),
    ("xml", report_type_enum.XML), ("TXT", report_type_enum.TXT),
    ("HTML", report_type_enum.HTML), (None, report_type_enum.TXT),
])
def test_loaded_response_format_load_json(tmp_path, monkeypatch, raw, expected):
    """<summary>Менеджер загружает формат из JSON; отсутствие поля сохраняет TXT.</summary>"""
    # Подготовка
    manager = setting_manager()
    monkeypatch.setattr(manager, "_setting_manager__settings", manager.settings)
    monkeypatch.setattr(manager, "_data", getattr(manager, "_data", None), raising=False)
    monkeypatch.setattr(manager, "_is_loaded", manager._is_loaded)
    # Действие
    data = json.loads(Path("settings.json").read_text())
    data.pop("response_format", None)
    if raw is not None:
        data["response_format"] = raw
    file = tmp_path / "settings.json"
    file.write_text(json.dumps(data))
    manager.load(str(file))
    # Проверка
    assert manager.settings.response_format is expected


@pytest.mark.parametrize("raw", ["PDF", "", 1, None])
def test_rejected_response_format_convert_invalid_value(monkeypatch, raw):
    """<summary>Неподдерживаемый или нестроковый формат даёт ошибку настройки.</summary>"""
    # Подготовка
    manager = setting_manager()
    data = json.loads(Path("settings.json").read_text())
    data["response_format"] = raw
    monkeypatch.setattr(manager, "_data", data, raising=False)
    # Действие и Проверка
    with pytest.raises(operation_exception, match="response_format"):
        manager.convert()
