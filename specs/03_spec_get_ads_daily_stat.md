# Spec for get_ads_daily_stat

## Summary

Публичная функция в `ozon_performance.py`, возвращающая дневную статистику на уровне объявлений (баннеров) — показы, клики, расходы — за заданный период.

В отличие от `get_campaigns_daily_stat`, данные **не агрегируются** до уровня кампании — возвращается одна строка на объявление × день.

## Functional Requirements

### 1. Сигнатура функции

```python
def get_ads_daily_stat(
    date_from: str,  # YYYY-MM-DD — начало периода
    date_to: str,    # YYYY-MM-DD — конец периода
) -> pd.DataFrame:
```

### 2. Алгоритм

Асинхронный паттерн — идентичен `get_campaigns_daily_stat`, кроме шага парсинга:

1. Получить список всех campaign_id через `_fetch_all_campaigns()`.
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
     - Poll UUID → скачать → распаковать CSV
     - Разобрать CSV **без агрегации** — одна строка на объявление
3. Конкатенировать → DataFrame → вернуть с колонками `ADS_STAT_COLUMNS`.

**Пейсинг и кэш:** те же константы и `raw_cache_dir` параметр, что в функции 2.

**Переиспользование кэша:** если `get_campaigns_daily_stat` уже была вызвана с теми же датами и тем же `raw_cache_dir`, файлы `raw_data/raw_files/raw_{date_from}_{date_to}_{hash}.bin` уже существуют — `get_ads_daily_stat` читает их напрямую без API-запросов.

**Очистка кэша:** при старте `_evict_stale_raw_cache()` удаляет `raw_*.bin` файлы с датами, отличными от текущего запроса.

### 3. Возвращаемый DataFrame

| Колонка | Тип | Источник в CSV | Описание |
|---------|-----|----------------|----------|
| `date` | string (YYYY-MM-DD) | `День` (DD.MM.YYYY) | Дата |
| `campaign_id` | string | передаётся в парсер | ID кампании |
| `ad_id` | string | `ID баннера` | ID объявления/баннера |
| `ad_name` | string | `Название` | Название объявления |
| `views` | float | `Показы` | Показы |
| `clicks` | float | `Клики` | Клики |
| `money_spent` | float | `Расход, ₽, с НДС` | Расход с НДС |

### 4. Изменения в `ozon_performance.py`

- `ADS_STAT_COLUMNS` — уже есть в скаффолде
- Добавить приватный метод `_parse_ads_csv(data: bytes, campaign_id: str) -> list[dict]` — как `_parse_stat_csv`, но без агрегации (возвращает строки уровня объявления, пропускает `Всего`/`Корректировка`)
- Реализовать `get_ads_daily_stat()` вместо `raise NotImplementedError`
- Обновить docstring модуля

## Ограничения API

| Ограничение | Значение | Реализация |
|-------------|----------|------------|
| Кампаний в одном запросе | макс **10** | `BATCH_SIZE = 10` |
| Одновременных задач | макс **3** | `MAX_CONCURRENT`, `_wait_for_free_slot()` |
| Скачиваний отчётов в сутки | макс **1000** | не enforced в коде |
| Burst rate limit | недокументирован | `MIN_SUBMIT_INTERVAL_SEC = 3` |

## Possible Edge Cases

- Кампания без объявлений за день — CSV содержит только строку `Всего` с нулями → функция возвращает пустые строки для этой кампании (нормально).
- Строка `Корректировка` — нет даты, пропускается через `_parse_date_str`.
- `ad_id` отсутствует в строке — строка пропускается (`dropna(subset=["ad_id"])`).
- Формат CSV тот же что в функции 2 (подтверждён): UTF-8 BOM, разделитель `;`, колонки `День;ID баннера;Название;...`.

## Acceptance Criteria

- [ ] `get_ads_daily_stat("2026-04-24", "2026-04-25")` возвращает DataFrame с колонками `["date", "campaign_id", "ad_id", "ad_name", "views", "clicks", "money_spent"]`
- [ ] Одна строка на объявление × день (не агрегировано до кампании)
- [ ] `date` в формате `YYYY-MM-DD`
- [ ] `campaign_id` и `ad_id` — string без NaN
- [ ] При отсутствии данных — пустой DataFrame с правильными колонками
- [ ] `get_campaign_dict()` и `get_campaigns_daily_stat()` работают без изменений

## Open Questions

- Колонки CSV могут отличаться для кампаний типа SKU / SEARCH_PROMO — проверить реальным запросом (для BANNER уже подтверждено).
