"""Интеграционные проверки HTTP-маршрутов отчётности."""
import pytest
import main
from Src.Core.report_type_enum import report_type_enum
from Src.Models.recipe_item_model import recipe_item_model


@pytest.mark.parametrize('kind', ['item', 'unit', 'recipe'])
@pytest.mark.parametrize('format_', list(report_type_enum))
def test_correct_response_get_explicit_format(kind, format_):
    """<summary>Все типы сущностей доступны во всех форматах с правильной выдачей.</summary>"""
    # Подготовка
    entity = {'item': main.storage.items[0], 'unit': main.storage.units[0],
              'recipe': next(x.recipe for x in main.storage.items if isinstance(x, recipe_item_model))}[kind]
    client = main.api.app.test_client()
    # Действие
    response = client.get(f'/api/reports/{kind}/{entity.unique_code}?format={format_.name}')
    # Проверка
    assert response.status_code == 200
    assert entity.unique_code in response.get_data(as_text=True)
    assert ('attachment' in response.headers.get('Content-Disposition', '')) == (format_.name in ('CSV', 'MARKDOWN'))
    assert response.mimetype == {'TXT':'text/plain','CSV':'text/csv','MARKDOWN':'text/markdown','XML':'application/xml','HTML':'text/html'}[format_.name]


def test_default_format_get_settings(monkeypatch):
    """<summary>Маршрут default выбирает Markdown из настроек и отдаёт файл.</summary>"""
    # Подготовка
    monkeypatch.setattr(main.settings.settings, 'response_format', report_type_enum.MARKDOWN)
    client = main.api.app.test_client()
    # Действие
    response = client.get(f'/api/reports/unit/{main.storage.units[0].unique_code}/default')
    # Проверка
    assert response.status_code == 200
    assert response.mimetype == 'text/markdown'
    assert '.md' in response.headers['Content-Disposition']


@pytest.mark.parametrize('url,status', [
    ('/api/reports/unit/missing?format=XML',404),
    ('/api/reports/unit/missing/default',404),
    ('/api/reports/wrong/missing?format=TXT',400),
    ('/api/reports/unit/missing?format=PDF',400),
    ('/api/reports/unit/missing',400),
])
def test_error_response_get_invalid_request(url,status):
    """<summary>Ошибки параметров и отсутствующий код имеют ожидаемый HTTP-статус.</summary>"""
    # Подготовка
    client = main.api.app.test_client()
    # Действие
    response = client.get(url)
    # Проверка
    assert response.status_code == status
