# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -r ozon_performance/requirements.txt
# dev (pytest, ruff):
pip install -r ozon_performance/requirements-dev.txt
```

Credentials in `ozon_performance/.env` (copy from `ozon_performance/.env.example`):
```
OZON_CLIENT_ID=...
OZON_CLIENT_SECRET=...
TEST_START_DATE=YYYY-MM-DD
TEST_END_DATE=YYYY-MM-DD
```

## Запуск

Быстрая проверка из REPL (из `ozon_performance/`):
```python
import sys; sys.path.insert(0, ".")
from ozon_performance import get_campaign_dict
df = get_campaign_dict()
print(df.shape)
```

Smoke-тесты (реальный API, требуют `.env`):
```bash
python ozon_performance/smoke_tests/test_get_campaign_dict.py
python ozon_performance/smoke_tests/test_get_campaigns_daily_stat.py
python ozon_performance/smoke_tests/test_get_ads_daily_stat.py
```

Unit-тесты (моки):
```bash
pytest tests/
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
1. Endpoint для видео-статистики (`get_video_ads_daily_stat`) — предположительно `/api/client/statistics/video`
2. Endpoint для охвата на уровне объявлений (`get_reach_ads_daily_stat`)

## Структура файлов

```
CLAUDE.md                    # этот файл
info/                        # сводки API и реестр функций
specs/                       # спецификации функций (NN_spec_имя.md)
plans/                       # планы реализации (NN_plan_имя.md)
tests/                       # pytest unit-тесты (с моками)
manual_forms/                # заполненные вручную анкеты проекта
auto_generated/              # автогенерируемые файлы (шаблоны)
test/                        # шаблоны для новых проектов (не тесты)

ozon_performance/
  ozon_performance.py        # единственный файл библиотеки
  requirements.txt
  requirements-dev.txt
  .env / .env.example
  smoke_tests/               # smoke-тесты (реальный API)
  raw_data/                  # CSV-результаты; raw_data/raw_files/ — кэш сырых CSV
```

## Воркфлоу реализации функций

Каждая функция реализуется по циклу:
1. Создать spec → `specs/NN_spec_имя.md`
2. Утвердить spec
3. Создать plan → `plans/NN_plan_имя.md`
4. Утвердить plan
5. Реализовать в `ozon_performance/ozon_performance.py`
6. Smoke-тест → `ozon_performance/smoke_tests/test_имя.py`
7. Показать `df.head(5).to_markdown(index=False)` + shape + columns
8. Обновить `info/01_functions_implemented.md`

**После создания плана — ждать явного утверждения пользователя.** Не начинать реализацию после утверждения спека — это два отдельных шага.

**Smoke-тесты запускаются Claude самостоятельно** после реализации — без ожидания команды от пользователя.
