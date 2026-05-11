# Spec for get_campaigns_daily_stat

## Summary

Публичная функция в `ozon_performance.py`, возвращающая дневную статистику по всем рекламным кампаниям аккаунта — показы, клики, расходы — за заданный период.

## Functional Requirements

### 1. Сигнатура функции

```python
def get_campaigns_daily_stat(
    date_from: str,  # YYYY-MM-DD — начало периода
    date_to: str,    # YYYY-MM-DD — конец периода
) -> pd.DataFrame:
```

### 2. Алгоритм

Асинхронный паттерн:

1. Получить список всех campaign_id через `_fetch_all_campaigns()` (внутренний вызов, не публичный `get_campaign_dict()`).
2. Для каждого дня D в [date_from, date_to]:
   - Для каждого батча campaign_id (≤ `BATCH_SIZE` = 10):
     - `POST /api/client/statistics` с телом:
       ```json
       {
         "campaigns": ["id1", "id2", ...],
         "dateFrom": "YYYY-MM-DD",
         "dateTo": "YYYY-MM-DD",
         "groupBy": "DATE"
       }
       ```
     - Дождаться UUID → poll до `state == OK` → скачать отчёт
     - Разобрать CSV / ZIP→CSV → добавить строки в аккумулятор
3. Конкатенировать все строки → DataFrame → вернуть с фиксированными колонками `CAMPAIGN_STAT_COLUMNS`.

**Пейсинг:** между submit-запросами ≥ `MIN_SUBMIT_INTERVAL_SEC` сек. Не более `MAX_CONCURRENT` одновременных UUID.

**campaign_id передаётся строкой** (`str(id)`) — API принимает только string, хотя `GET /api/client/campaign` возвращает integer.

### 3. Возвращаемый DataFrame

| Колонка | Тип | Источник в CSV | Описание |
|---------|-----|----------------|----------|
| `date` | string (YYYY-MM-DD) | `Дата` (DD.MM.YYYY) | Дата статистики |
| `campaign_id` | string | имя CSV-файла или колонка в CSV | ID кампании |
| `views` | Int64 | `Показы` | Показы рекламы |
| `clicks` | Int64 | `Клики` | Клики по рекламе |
| `money_spent` | float | `Расход` | Расход в рублях |

> ⚠️ Точные имена колонок CSV — уточнить первым реальным запросом. Разделитель `,` подтверждён. Источник `campaign_id` (имя файла ZIP или колонка) — определить при первом скачивании.

### 4. Изменения в `ozon_performance.py`

- `CAMPAIGN_STAT_COLUMNS` — уже есть в скаффолде
- `_submit_report()`, `_poll_uuid()`, `_download_report_bytes()`, `_extract_csvs()` — уже реализованы
- Добавить приватный метод `_parse_stat_csv(data: bytes, campaign_id: str) -> list[dict]` — парсит один CSV-файл в список строк
- Реализовать `get_campaigns_daily_stat()` вместо `raise NotImplementedError`
- Обновить docstring модуля

## Ограничения API

| Ограничение | Значение | Реализация |
|-------------|----------|------------|
| Кампаний в одном запросе | макс **10** | `BATCH_SIZE = 10` |
| Одновременных задач | макс **3** | `MAX_CONCURRENT`, `_wait_for_free_slot()` |
| Скачиваний отчётов в сутки | макс **1000** | не enforced в коде |
| Burst rate limit | недокументирован | `MIN_SUBMIT_INTERVAL_SEC = 3` |

**Поведение при 429:** экспоненциальный backoff, старт `RATE_LIMIT_BASE_SEC` = 10 сек, удвоение, макс `RATE_LIMIT_RETRY_MAX` = 5 повторов.

## Possible Edge Cases

- `campaign_id` в ZIP — имя файла содержит ID кампании (предположительно `{id}.csv`). Если нет — искать колонку в CSV.
- CSV без строк данных за день — кампания не показывалась. Пропускаем, не добавляем строку.
- `date_from == date_to` — один день, валидно.
- Большой период (30+ дней × 88 кампаний) — много запросов. `tqdm` для прогресса.
- Числа в CSV с запятой как десятичным разделителем (`«25833,00»`) — `_parse_num()` уже обрабатывает.
- Дата в CSV в формате `DD.MM.YYYY` — `_parse_date_str()` уже обрабатывает.

## Acceptance Criteria

- [ ] `get_campaigns_daily_stat("2026-04-24", "2026-04-25")` возвращает DataFrame с колонками `["date", "campaign_id", "views", "clicks", "money_spent"]`
- [ ] Одна строка на кампанию × день (только кампании с ненулевой активностью)
- [ ] `date` в формате `YYYY-MM-DD`
- [ ] `money_spent >= 0` для всех строк
- [ ] `campaign_id` — string без NaN
- [ ] При отсутствии данных — пустой DataFrame с правильными колонками
- [ ] Не превышается `MAX_CONCURRENT` одновременных UUID
- [ ] `get_campaign_dict()` продолжает работать без изменений

## Подтверждённые решения

- **Разделитель CSV:** `,`
- **Кодировка CSV:** определить автоматически при первом скачивании (попробовать `utf-8-sig`, затем `utf-8`, затем `cp1251`)
- **Источник `campaign_id`:** определить при первом скачивании — проверить имя файла в ZIP и колонки в CSV
- **Поле статуса polling:** определить при первом реальном запросе (попробовать `state`, затем `status`)

## Open Questions

- Точные имена колонок CSV: `Показы` / `Клики` / `Расход` — уточнить первым реальным скачиванием отчёта.
