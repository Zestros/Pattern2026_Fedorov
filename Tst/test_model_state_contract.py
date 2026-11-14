"""Проверки устойчивости контракта моделей к изменению кода и формата JSON."""

import pytest

from Src.Core.exception import arguments_exception
from Src.Logics.Restore.restore_factory import restore_factory
from Src.Logics.convert_factory import convert_factory
from Src.Logics.reference_restore import reference_restore
from Src.Models.group_model import group_model


class labeled_group_model(group_model):
    """Тестовая группа с полями конструктора и унаследованным сеттером name."""

    def __init__(self, name: str, label: str) -> None:
        """Сохраняет обязательную метку, которую нельзя менять после создания."""
        super().__init__(name)
        self.__label = label
        self.__note = ""

    @property
    def label(self) -> str:
        """Возвращает метку конструктора."""
        return self.__label

    @property
    def note(self) -> str:
        """Возвращает необязательную заметку."""
        return self.__note

    @note.setter
    def note(self, value: str) -> None:
        """Проверяет тип заметки при присваивании."""
        if not isinstance(value, str):
            raise arguments_exception("note", "Ожидается текст заметки")
        self.__note = value


def test_discovered_fields_reference_restore_new_registered_model(monkeypatch):
    """<summary>После регистрации типа маппинг сам находит поля конструктора и свойства с сеттерами.</summary>"""
    monkeypatch.setattr(restore_factory, "_restore_factory__instance", None)
    restore_factory().add_model(labeled_group_model)
    source = labeled_group_model("Бакалея", "Продукты")
    source.note = "Основная группа"
    data = convert_factory().create(source).convert(source)

    restored = reference_restore().restore(data)

    assert type(restored) is labeled_group_model
    assert restored.unique_code == source.unique_code
    assert restored.name == source.name
    assert restored.label == source.label
    assert restored.note == source.note
    data["value"]["$fields"]["note"] = 42
    with pytest.raises(arguments_exception, match="Ожидается текст заметки"):
        reference_restore().restore(data)


def test_preserved_model_reference_restore_new_computed_property(monkeypatch):
    """<summary>Новое вычисляемое свойство не читается при сохранении и не мешает загрузке.</summary>"""
    def computed_label(instance):
        """Имитирует свойство, которое нельзя читать вне контекста приложения."""
        raise AssertionError("Вычисляемое свойство не входит в сохраняемое состояние")

    monkeypatch.setattr(group_model, "label", property(computed_label), raising=False)
    source = group_model("Бакалея")
    source.temporary_note = "Не сохранять"
    data = convert_factory().create(source).convert(source)
    restored = reference_restore().restore(data)
    assert set(data["value"]["$fields"]) == {"unique_code", "name"}
    assert restored.name == source.name
    assert restored.unique_code == source.unique_code
    assert not hasattr(restored, "temporary_note")


@pytest.mark.parametrize("field", ["unexpected_field", "apply_fields", "type", "_private"])
def test_arguments_exception_reference_restore_unknown_field(field):
    """<summary>Необъявленные поля, методы и метаданные нельзя присвоить модели через JSON.</summary>"""
    source = group_model("Бакалея")
    data = convert_factory().create(source).convert(source)
    data["value"]["$fields"][field] = "unexpected"
    with pytest.raises(arguments_exception):
        reference_restore().restore(data)


def test_unchanged_model_from_fields_rejected_field():
    """<summary>Фабричный метод отклоняет неизвестное поле до изменения переданного экземпляра.</summary>"""
    source = group_model("Исходное имя")
    code = source.unique_code
    with pytest.raises(arguments_exception):
        group_model.from_fields({"name": "Новое имя", "unknown": 1}, instance=source)
    assert source.name == "Исходное имя"
    assert source.unique_code == code


def test_arguments_exception_reference_restore_short_model_type():
    """<summary>Короткое имя модели отклоняется: формат требует полное имя класса.</summary>"""
    source = group_model("Бакалея")
    data = convert_factory().create(source).convert(source)
    data["value"]["$type"] = "group_model"
    with pytest.raises(arguments_exception, match="Неизвестный тип: group_model"):
        reference_restore().restore(data)


def test_preserved_optional_field_from_fields_missing_value(monkeypatch):
    """<summary>Новое свойство с сеттером и начальным значением совместимо со старым JSON.</summary>"""
    def get_note(instance):
        """Возвращает начальное значение для ранее сохранённых моделей."""
        return getattr(instance, "_note", "")

    def set_note(instance, value):
        """Сохраняет значение нового свойства."""
        instance._note = value

    source = group_model("Бакалея")
    data = convert_factory().create(source).convert(source)
    monkeypatch.setattr(group_model, "note", property(get_note, set_note), raising=False)
    restored = reference_restore().restore(data)
    assert restored.name == source.name
    assert restored.note == ""
    assert convert_factory().create(restored).convert(restored)["value"]["$fields"]["note"] == ""
