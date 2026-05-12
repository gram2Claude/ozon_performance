# Plan: get_campaign_dict

## Контекст

На основании спецификации `specs/01_spec_get_campaign_dict.md`.

## Изменения в `ozon_performance.py`

Изменений не требуется — функция полностью реализована в скаффолде:
- `CAMPAIGN_DICT_COLUMNS` — есть
- `OzonPerformanceClient._fetch_all_campaigns()` — реализован
- `get_campaign_dict()` — реализован (не стаб)

## Порядок реализации

1. Установить зависимости: `pip install -r requirements.txt`
2. Запросить у пользователя `CLIENT_ID` и `CLIENT_SECRET` → вписать в `.env`
3. Запросить тестовые даты `TEST_START_DATE`, `TEST_END_DATE`, `TEST_GLOBAL_START_DATE` → вписать в `.env`
4. Создать `smoke_tests/test_get_campaign_dict.py`
5. Запустить smoke-тест
6. Показать `df.head(5)`, `df.shape`, `df.columns`
7. Зафиксировать результат в `info/01_functions_implemented.md`

## Проверка

- [ ] `get_campaign_dict()` возвращает DataFrame с колонками `["campaign_id", "campaign_name"]`
- [ ] `campaign_id` без дублей и без NaN
- [ ] `df.shape[0] > 0` — есть реальные кампании
- [ ] Пагинация: проверить, нет ли `next_page` / `offset` в ответе API
