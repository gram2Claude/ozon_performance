# Plan: `get_reach_ads_daily_stat`

На основании спецификации `specs/05_spec_get_reach_ads_daily_stat.md`.

## Изменения в `ozon_performance.py`

### 1. Константа `ADS_REACH_COLUMNS`
Колонки: `["date", "campaign_id", "ad_id", "ad_name", "reach", "increment"]` — без `platform`.

### 2. Парсер `_parse_reach_ads_csv`
Парсит CSV groupBy=NO_GROUP_BY, возвращает ad-level строки.
Одна строка = (ad_id, ad_name, reach). Пропускает «Всего», «Корректировка», пустые ad_id.

### 3. Публичная функция `get_reach_ads_daily_stat`
- Общий кэш `reach_{global_start_date}_{cid}_{day}.csv`
- После сбора строк: `groupby(["date", "campaign_id", "ad_id", "ad_name"])["reach"].sum()` — суммируем по платформам
- increment по группе (campaign_id, ad_id)
- Фильтр: только строки с reach > 0

### 4. Изменения в существующем коде
Нет — `_evict_stale_reach_cache`, `_unpack_and_cache_report` переиспользуются без изменений.

## Порядок реализации (выполнено)

1. ✅ `ADS_REACH_COLUMNS` — без `platform`
2. ✅ `_parse_reach_ads_csv` — без поля `platform`
3. ✅ `get_reach_ads_daily_stat` — groupby sum по платформам, increment по (campaign_id, ad_id)
4. ✅ Smoke-тест `smoke_tests/test_get_reach_ads_daily_stat.py`
5. ✅ CSV обновлён
6. ✅ `info/01_functions_implemented.md` обновлён
