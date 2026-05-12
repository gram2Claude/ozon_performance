# Plan: `get_reach_ads_daily_stat`

На основании спецификации `specs/05_spec_get_reach_ads_daily_stat.md`.

## Изменения в `ozon_performance.py`

### 1. Константа `ADS_REACH_COLUMNS`
Добавлена колонка `platform` (между `ad_name` и `reach`).

### 2. Новый парсер `_parse_reach_ads_csv`
Парсит CSV groupBy=NO_GROUP_BY, возвращает ad-level строки.
Одна строка = (ad_id, platform). Пропускает «Всего», «Корректировка», пустые ad_id.

### 3. Публичная функция `get_reach_ads_daily_stat`
Заменяет `raise NotImplementedError`. Тот же паттерн что функция 4:
- Общий кэш `reach_{global_start_date}_{cid}_{day}.csv`
- increment по группе (campaign_id, ad_id, platform)
- Фильтр: только строки с reach > 0

### 4. Изменения в существующем коде
Нет — `_evict_stale_reach_cache`, `_unpack_and_cache_report` переиспользуются без изменений.

## Порядок реализации (выполнено)

1. ✅ Обновить `ADS_REACH_COLUMNS` — добавить `platform`
2. ✅ Добавить `_parse_reach_ads_csv` после `_parse_reach_csv`
3. ✅ Реализовать `get_reach_ads_daily_stat` вместо `NotImplementedError`
4. ✅ Создать smoke-тест `smoke_tests/test_get_reach_ads_daily_stat.py`
5. Запустить smoke-тест, показать результат из CSV
6. Обновить `info/01_functions_implemented.md`
