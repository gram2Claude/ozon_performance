# Plan: `get_video_ads_daily_stat`

На основании спецификации `specs/06_spec_get_video_ads_daily_stat.md`.

## Изменения в `ozon_performance.py`

### 1. Константа `VIDEO_ADS_COLUMNS`
Уже обновлена — `reach` удалён (строка 107). Менять не нужно.

### 2. Новый парсер `_parse_video_ads_csv`
После `_parse_ads_csv`. Читает VIDEO_BANNER CSV:
- Заголовок ищется по `День;`
- Пропускает `Всего`, `Корректировка` (нет даты), пустые `ad_id`
- Колонки: `Показы`, `Видимые показы`, `Клики`, `Досмотры по квартилям 25/50/75/100%`, `Просмотры со звуком`, `Расход, ₽`

### 3. Публичная функция `get_video_ads_daily_stat`
Заменяет `raise NotImplementedError`. Паттерн идентичен `get_ads_daily_stat`:
- `_fetch_all_campaigns()` → фильтр `advObjectType == "VIDEO_BANNER"`
- Общий кэш `raw_{date_from}_{date_to}_{cid}_{day}.csv`
- `_parse_video_ads_csv` вместо `_parse_ads_csv`
- `tqdm` прогресс-бар

### 4. Изменения в существующем коде
Нет — все хелперы переиспользуются без изменений.

## Порядок реализации

1. ✅ Обновить `VIDEO_ADS_COLUMNS` — удалить `reach`
2. Добавить `_parse_video_ads_csv` после `_parse_ads_csv`
3. Реализовать `get_video_ads_daily_stat` вместо `NotImplementedError`
4. Создать smoke-тест `smoke_tests/test_get_video_ads_daily_stat.py`
5. Запустить smoke-тест, показать результат из CSV
6. Обновить `info/01_functions_implemented.md`
