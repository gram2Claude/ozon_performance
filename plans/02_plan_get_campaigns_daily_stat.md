# Plan: get_campaigns_daily_stat

## Контекст

На основании спецификации `specs/02_spec_get_campaigns_daily_stat.md`.

## Изменения в `ozon_performance.py`

### 1. Новые константы

Нет — `CAMPAIGN_STAT_COLUMNS` уже есть в скаффолде.

### 2. Новые приватные методы

- `_parse_stat_csv(data: bytes, campaign_id: str) -> list[dict]`
  - Определяет кодировку (пробует `utf-8-sig` → `utf-8` → `cp1251`)
  - Читает CSV с разделителем `,`
  - Маппит колонки CSV → `date`, `views`, `clicks`, `costs_nds`
  - Первый вызов: печатает имена колонок CSV в stdout для фиксации в `00_api_methods.md`
  - Возвращает список dict с полями `date`, `campaign_id`, `views`, `clicks`, `costs_nds`

### 3. Новая публичная функция

- `get_campaigns_daily_stat(date_from, date_to)`:
  1. `_fetch_all_campaigns()` → список campaign_id (конвертировать в `str`)
  2. Для каждого дня D в `_date_range(date_from, date_to)`:
     - Для каждого батча ≤ `BATCH_SIZE` кампаний:
       - `_submit_report(batch, D, D, group_by="DATE")` → UUID
       - `_poll_uuid(uuid)`
       - `_download_report_bytes(uuid)` → bytes
       - `_extract_csvs(bytes)` → список CSV
       - Для каждого CSV: `_parse_stat_csv(csv_bytes, campaign_id)` → rows
  3. `pd.DataFrame(все_rows).reindex(columns=CAMPAIGN_STAT_COLUMNS)`

### 4. Изменения в существующем коде

- `get_campaigns_daily_stat()` — заменить `raise NotImplementedError` на реализацию
- Обновить docstring модуля

## Порядок реализации

1. Реализовать `_parse_stat_csv()` — включая авто-определение кодировки и вывод колонок при первом вызове
2. Реализовать `get_campaigns_daily_stat()`
3. Обновить docstring модуля
4. Создать `smoke_tests/test_get_campaigns_daily_stat.py`
5. Запустить smoke-тест (период: `TEST_START_DATE`–`TEST_END_DATE` из `.env`)
6. Зафиксировать колонки CSV в `info/00_api_methods.md` (open questions #3–5)
7. Показать `df.head(5)` из сохранённого CSV + shape + columns
8. Обновить `info/01_functions_implemented.md`

## Проверка

- [ ] `get_campaigns_daily_stat("2026-04-24", "2026-04-25")` возвращает DataFrame с колонками `["date", "campaign_id", "views", "clicks", "costs_nds"]`
- [ ] `date` в формате `YYYY-MM-DD`
- [ ] `campaign_id` — string без NaN
- [ ] `costs_nds >= 0` для всех строк
- [ ] При отсутствии данных — пустой DataFrame с правильными колонками
- [ ] `get_campaign_dict()` продолжает работать без изменений
