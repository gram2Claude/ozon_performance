# Spec: `get_video_ads_daily_stat`

## Цель

Получить ежедневную статистику по видео-объявлениям (кампании типа `VIDEO_BANNER`) за заданный период. Один запрос на день, кэш CSV на диске.

## Входные параметры

```python
def get_video_ads_daily_stat(
    date_from: str,                    # YYYY-MM-DD — начало периода
    date_to: str,                      # YYYY-MM-DD — конец периода
    raw_cache_dir: str | Path | None = None,
) -> pd.DataFrame:
```

## API endpoint

- `POST /api/client/statistics` — тот же что у функций 2 и 3
- `groupBy: "DATE"` — один запрос на день
- `campaigns: [список ID видео-кампаний]` — только `advObjectType == "VIDEO_BANNER"`
- Async pattern: submit → poll → download (идентично функциям 2/3)

## Кампании

Фильтр: из `_fetch_all_campaigns()` берём только `advObjectType == "VIDEO_BANNER"`.
В аккаунте 14 таких кампаний (из 88 всего).

## Кэш CSV

Общий с функциями 2/3: `raw_{date_from}_{date_to}_{campaign_id}_{day}.csv`.
Если файл уже существует — API не вызывается, читаем с диска.

## Колонки CSV (подтверждено реальным запросом 2026-05-12)

| № | Колонка CSV | Поле DataFrame | Тип pandas |
|---|-------------|----------------|-----------|
| 0 | `День` | `date` (YYYY-MM-DD) | object |
| — | контекст батча | `campaign_id` | object |
| 1 | `ID баннера` | `ad_id` | object |
| 2 | `Название` | `ad_name` | object |
| 3 | `Показы` | `views` | float64 |
| 4 | `Видимые показы` | `viewable_views` | float64 |
| 5 | `Клики` | `clicks` | float64 |
| 9 | `Досмотры по квартилям 25%` | `quartile_25` | float64 |
| 10 | `Досмотры по квартилям 50%` | `quartile_50` | float64 |
| 11 | `Досмотры по квартилям 75%` | `quartile_75` | float64 |
| 12 | `Досмотры по квартилям 100%` | `quartile_100` | float64 |
| 17 | `Просмотры со звуком` | `views_with_sound` | float64 |
| 22 | `Расход, ₽` | `costs_nds` | float64 |

Пропускаются: `CTR`, `Доля видимых показов`, `Доля досмотров *%`, `Заказы post-click/view`, `Выручка post-click/view`.

## Поля выходного DataFrame

| Колонка | Тип pandas | Источник |
|---------|-----------|----------|
| `date` | object (YYYY-MM-DD) | `День` |
| `campaign_id` | object (string) | из контекста батча |
| `ad_id` | object (string) | `ID баннера` |
| `ad_name` | object (string) | `Название` |
| `views` | float64 | `Показы` |
| `viewable_views` | float64 | `Видимые показы` |
| `clicks` | float64 | `Клики` |
| `quartile_25` | float64 | `Досмотры по квартилям 25%` |
| `quartile_50` | float64 | `Досмотры по квартилям 50%` |
| `quartile_75` | float64 | `Досмотры по квартилям 75%` |
| `quartile_100` | float64 | `Досмотры по квартилям 100%` |
| `views_with_sound` | float64 | `Просмотры со звуком` |
| `costs_nds` | float64 | `Расход, ₽` (без НДС, в отличие от BANNER) |

## Специфика

- **`Расход, ₽`** — без НДС (у BANNER было `Расход, ₽, с НДС`)
- **Нет `platform`** — VIDEO_BANNER CSV не содержит колонку `Платформа`
- **Строки `Всего`/`Корректировка`** — пропускаются (как в функциях 2/3)
- **Пустые `ad_id`** — пропускаются
- **Результат функции 2 (`get_ads_daily_stat`)** уже кэширует VIDEO_BANNER CSV при одинаковых датах — функция 6 читает этот кэш без повторного API-запроса

## Константа VIDEO_ADS_COLUMNS

Уже определена в коде (строка 107):
```python
VIDEO_ADS_COLUMNS = [
    "date", "campaign_id", "ad_id", "ad_name",
    "views", "viewable_views", "clicks",
    "quartile_25", "quartile_50", "quartile_75", "quartile_100",
    "views_with_sound", "costs_nds",
]
```
Совпадает с реальными колонками API — менять не нужно.
