# Plan: get_ads_daily_stat

<!-- 
Имя файла: plans/03_plan_get_ads_daily_stat.md
-->

## Контекст

На основании спецификации `specs/03_spec_get_ads_daily_stat.md`.

Функция использует тот же API-эндпоинт и ту же инфраструктуру кэша, что `get_campaigns_daily_stat`.
Единственное отличие — парсер не агрегирует строки до уровня кампании.

## Изменения в `ozon_performance/ozon_performance.py`

### 1. Новые константы

`ADS_STAT_COLUMNS` — уже объявлена в скаффолде как `raise NotImplementedError`. Заменить на:
```python
ADS_STAT_COLUMNS = ["date", "campaign_id", "ad_id", "ad_name", "views", "clicks", "costs_nds"]
```

### 2. Новый приватный метод

`_parse_ads_csv(data: bytes, campaign_id: str) -> list[dict]`

Как `_parse_stat_csv`, но без агрегации:
- Декодировать через `_decode_csv()`
- Пропустить первую строку (метаданные)
- Найти строку заголовка по `День;`
- Для каждой строки данных:
  - `date = _parse_date_str(row["День"])` — если `None`, пропустить (`Корректировка`)
  - Пропустить строку `Всего` / `Итого`
  - Пропустить если `ad_id` пустой
  - Вернуть dict с полями `date`, `campaign_id`, `ad_id`, `ad_name`, `views`, `clicks`, `costs_nds`

Маппинг колонок CSV → поля:
| CSV | поле |
|-----|------|
| `День` | `date` |
| `ID баннера` | `ad_id` |
| `Название` | `ad_name` |
| `Показы` | `views` |
| `Клики` | `clicks` |
| `Расход, ₽, с НДС` | `costs_nds` |

### 3. Публичная функция

`get_ads_daily_stat(date_from, date_to, raw_cache_dir=None)` — заменить `raise NotImplementedError`.

Алгоритм идентичен `get_campaigns_daily_stat` за исключением вызова парсера:
- Вместо `_parse_stat_csv(csv_bytes, cid)` вызывать `_parse_ads_csv(csv_bytes, cid)`
- Кэш-файлы те же (`raw_{date_from}_{date_to}_{cid}_{day}.csv`) — общий с функцией 2

### 4. Изменения в существующем коде

Нет. `_evict_stale_raw_cache`, `_unpack_and_cache_report`, `_submit_report`, `_poll_uuid`,
`_download_report_bytes` — используются без изменений.

## Порядок реализации

1. Заменить заглушку `ADS_STAT_COLUMNS` на реальный список колонок
2. Реализовать `_parse_ads_csv()`
3. Реализовать `get_ads_daily_stat()` (копия `get_campaigns_daily_stat` с заменой парсера)
4. Обновить docstring модуля
5. Smoke-тест → `ozon_performance/smoke_tests/test_get_ads_daily_stat.py`

## Проверка

- [ ] Возвращает DataFrame с колонками `ADS_STAT_COLUMNS`
- [ ] Одна строка на объявление × день (нет агрегации)
- [ ] `campaign_id` и `ad_id` — string без NaN
- [ ] При тех же датах что `get_campaigns_daily_stat` — кэш переиспользуется (0 API-запросов)
- [ ] `get_campaign_dict()` и `get_campaigns_daily_stat()` работают без изменений
