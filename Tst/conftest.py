"""Общие настройки тестовых моделей графа."""

import pytest


@pytest.fixture
def declare_fields(monkeypatch):
    """Временно расширяет контракт модели полями тестового графа."""
    def declare(model_type, *names):
        """Объявляет дополнительные поля и значения для незаполненных экземпляров."""
        own = model_type.__dict__.get("state_fields", ())
        monkeypatch.setattr(model_type, "state_fields", (*own, *names))
        for name in names:
            monkeypatch.setattr(model_type, name, None, raising=False)
    return declare
