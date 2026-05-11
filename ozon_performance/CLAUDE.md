# CLAUDE.md — Ozon Performance

## Setup

```bash
pip install -r requirements.txt
```

Учётные данные — в `.env` (скопировать из `.env.example`):
```
OZON_CLIENT_ID=...
OZON_CLIENT_SECRET=...
```

`OzonPerformanceClient` читает из env vars или принимает явно в конструкторе.

## Запуск

```bash
jupyter notebook ozon_performance_demo.ipynb
```

Быстрая проверка из REPL:
```python
from ozon_performance import get_campaign_dict
df = get_campaign_dict()
print(df.shape)
```

## Архитектура

Единый файл: `ozon_performance.py`.

**`OzonPerformanceClient`** — внутренний HTTP-клиент:
- OAuth 2.0 `client_credentials`; токен — **POST** `/api/client/token` с JSON-телом; обновляется за 60 сек до истечения (TTL 1800 сек)
- `_fetch_all_campaigns()` → `GET /api/client/campaign`, envelope key `list`
- `_submit_report()` → `POST /api/client/statistics`, возвращает UUID
- `_poll_uuid()` → `GET /api/client/statistics/{UUID}` каждые 7 сек (макс. 40 попыток ≈ 5 мин)
- `_download_report_bytes()` → `GET /api/client/statistics/report?UUID=...` → bytes (CSV или ZIP)
- `_extract_csvs()` → разбирает ZIP или одиночный CSV
- 429: экспоненциальный backoff, макс. 5 повторов, старт 10 сек

**Публичные функции** (все возвращают `pd.DataFrame`):

| Функция | Тип | API endpoint |
|---------|-----|--------------|
| `get_campaign_dict()` | Справочник | `GET /api/client/campaign` |
| `get_campaigns_daily_stat(date_from, date_to)` | Статистика | `POST /api/client/statistics` |
| `get_ads_daily_stat(date_from, date_to)` | Статистика | уточнить |
| `get_reach_campaigns_daily_stat(global_start_date, date_from, date_to)` | Охват | `POST /api/client/statistics` groupBy=NO_GROUP_BY |
| `get_reach_ads_daily_stat(global_start_date, date_from, date_to)` | Охват | уточнить |
| `get_video_ads_daily_stat(date_from, date_to)` | Статистика | уточнить (предположительно `/api/client/statistics/video`) |

**Семантика охвата:**
`reach` — кумулятивный показатель (уникальные пользователи за период, нельзя суммировать по дням).
Для каждого дня D запрашивается период [global_start_date, D] с groupBy=NO_GROUP_BY.
`increment` вычисляется локально через `groupby().diff()`.

**Порядок запросов статистики:**
Статистика запрашивается по 1 дню за раз (dateFrom == dateTo), BATCH_SIZE кампаний на запрос.
Охват — [global_start_date, D], groupBy=NO_GROUP_BY.

## Лимиты API

- Макс. **10 кампаний** на запрос → `BATCH_SIZE = 10`
- Макс. **3 одновременные** задачи → `MAX_CONCURRENT = 3`
- Макс. **1000 скачиваний** отчётов в сутки
- Макс. **100 000 запросов** в сутки

## Кодировка (Windows)

`ozon_performance.py` перенастраивает `sys.stdout/stderr` на UTF-8 при импорте.
Не удалять — на Windows default cp1251 ломает вывод кириллицы.

## Open Questions (уточнить реальными запросами)

См. полный список в `info/00_api_methods.md` → раздел "Open Questions".
Ключевые:
1. HTTP-метод токена: GET с JSON-телом или POST?
2. Кодировка и разделитель CSV
3. Точные названия колонок CSV
4. Endpoint для статистики по объявлениям (ad-level)
5. Endpoint видео-статистики

## Структура файлов

```
ozon_performance.py          # библиотека-клиент
ozon_performance_demo.ipynb  # демо-ноутбук
info/00_api_methods.md       # сводка методов API
info/01_functions_implemented.md  # реестр реализованных функций
specs/                       # спецификации функций
plans/                       # планы реализации
tests/                       # pytest unit-тесты (с моками)
smoke_tests/                 # smoke-тесты на реальном API (требуют .env)
raw_data/                    # CSV-результаты успешных вызовов всех публичных функций
```

## Воркфлоу реализации функций

Каждая функция реализуется по циклу:
1. Создать spec → `specs/NN_spec_имя.md`
2. Утвердить spec
3. Создать plan → `plans/NN_plan_имя.md`
4. Утвердить plan
5. Реализовать
6. Smoke-тест → `smoke_tests/test_имя.py`
7. Показать `df.head(5)` + shape + columns
8. Обновить `info/01_functions_implemented.md`
