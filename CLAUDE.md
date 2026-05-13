# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -r ozon_performance/requirements.txt
# dev (pytest, ruff):
pip install -r ozon_performance/requirements-dev.txt
# для генерации PDF ТЗ (`generate_tz_pdf.py`):
pip install fpdf2
```

`fpdf2` намеренно не включён в `requirements.txt` — он нужен только для разовой
генерации PDF ТЗ, не для runtime библиотеки.

Credentials in `ozon_performance/.env` (copy from `ozon_performance/.env.example`):
```
CLIENT_ID=...
CLIENT_SECRET=...
TEST_GLOBAL_START_DATE=YYYY-MM-DD   # начало накопительного периода для reach-функций
TEST_START_DATE=YYYY-MM-DD
TEST_END_DATE=YYYY-MM-DD
```

**Имена env-переменных credentials — без префикса модуля/API.** Используем
`CLIENT_ID` / `CLIENT_SECRET` (OAuth) или `API_KEY` (статический ключ). Не
`OZON_CLIENT_ID`, не `{MODULE}_CLIENT_ID` — правило из шаблона
`test/01_PROJECT_STRUCTURE.md`. При генерации новых функций/демо/ТЗ держать
эту конвенцию.

**Важно:** в smoke-тестах reach-функций параметр `global_start_date` берётся из
`TEST_GLOBAL_START_DATE` (НЕ из `TEST_START_DATE`). Передача `TEST_START_DATE`
вместо `TEST_GLOBAL_START_DATE` даст охват за 1 день вместо накопительного — числа будут неверные.

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
python ozon_performance/smoke_tests/test_get_reach_campaigns_daily_stat.py
python ozon_performance/smoke_tests/test_get_reach_ads_daily_stat.py
python ozon_performance/smoke_tests/test_get_video_ads_daily_stat.py
```

Unit-тесты (моки): папка `tests/` зарезервирована, но сейчас пуста —
верификация всех 6 функций идёт через `smoke_tests/` на реальном API.
Когда появятся pytest-моки, запуск будет `pytest tests/`.

Генерация ТЗ для внешнего разработчика (PHP):
```bash
python generate_tz_pdf.py   # → TZ_ozon_performance_PHP.pdf в корне репо
```
Содержательный source-of-truth для PDF: `specs/TZ_ozon_performance_PHP.md`.
При правках держать оба файла в синхроне.

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
| `get_campaigns_daily_stat(date_from, date_to)` | Статистика | `POST /api/client/statistics` groupBy=DATE |
| `get_ads_daily_stat(date_from, date_to)` | Статистика | `POST /api/client/statistics` groupBy=DATE |
| `get_reach_campaigns_daily_stat(global_start_date, date_from, date_to)` | Охват | `POST /api/client/statistics` groupBy=NO_GROUP_BY |
| `get_reach_ads_daily_stat(global_start_date, date_from, date_to)` | Охват | `POST /api/client/statistics` groupBy=NO_GROUP_BY |
| `get_video_ads_daily_stat(date_from, date_to)` | Статистика | `POST /api/client/statistics` groupBy=DATE, только VIDEO_BANNER |

**Семантика охвата:**
`reach` — кумулятивный показатель (уникальные пользователи за период, нельзя суммировать по дням).
Для каждого дня D запрашивается период [global_start_date, D] с groupBy=NO_GROUP_BY.
`increment` вычисляется локально через `groupby().diff()`, для первого дня — `fillna(reach)`
(инвариант: `increment[D=date_from] == reach`, не NaN).

- `get_reach_campaigns_daily_stat` — берёт строку «Всего» из CSV (campaign-level, API-дедуплицированный)
- `get_reach_ads_daily_stat` — берёт ad-level строки (одна на платформу) и **суммирует reach по платформам**
  через `groupby(["date", "campaign_id", "ad_id", "ad_name"])["reach"].sum()`. Поле `platform` в выходе отсутствует.

**Порядок запросов статистики:**
Статистика запрашивается по 1 дню за раз (dateFrom == dateTo), BATCH_SIZE кампаний на запрос.
Охват — [global_start_date, D], groupBy=NO_GROUP_BY.

## Обогащение DataFrame (соглашение проекта)

Каждая публичная функция, перед `df.reindex(columns=...)`, обогащает результат
фиксированным набором константных и вычисляемых полей. Это часть контракта всех
функций — менять/удалять только синхронно во всех шести.

**Константы (все функции):** `account_id = 1`, `source_type_id = 9` — примеры,
заменяемые при интеграции. Колонки итоговых DataFrame заданы константами
`CAMPAIGN_DICT_COLUMNS`, `CAMPAIGN_STAT_COLUMNS`, `ADS_STAT_COLUMNS`,
`CAMPAIGN_REACH_COLUMNS`, `ADS_REACH_COLUMNS`, `VIDEO_ADS_COLUMNS` в начале
`ozon_performance.py`.

**Справочник** (`get_campaign_dict`): дополнительно `product_id = 1`,
`product_name = "prod_test"`, `camp_type = "camp_test"`,
`camp_category = "cat_test"`, `owner_id = 1`.

**Функции с расходами** (`get_campaigns_daily_stat`, `get_ads_daily_stat`,
`get_video_ads_daily_stat`):
- `costs_without_nds = costs_nds / 1.22` (НДС 22%)
- `ak = 0.5` (агентская комиссия 50%, константа)
- `costs_nds_ak = costs_nds * 1.5`
- `costs_without_nds_ak = costs_without_nds * 1.5`

**Составные ключи:**
- `id_key_camp = "1_" + campaign_id` — во всех функциях
- `id_key_ad = id_key_camp + "_" + ad_id` — **только для ad-level**
  (`get_ads_daily_stat`, `get_reach_ads_daily_stat`, `get_video_ads_daily_stat`)

**Семантика `costs_nds`:** название = «расход С НДС», но **источник зависит
от типа отчёта**:
- BANNER (`get_campaigns_daily_stat`, `get_ads_daily_stat`) — поле API
  «Расход, ₽, с НДС»
- VIDEO_BANNER (`get_video_ads_daily_stat`) — поле API «Расход, ₽» (БЕЗ НДС);
  название колонки в этом случае вводит в заблуждение, фактически там сумма
  без НДС — задокументировано в `info/01_functions_implemented.md`.

**Кэш сырых CSV (`raw_data/raw_files/`):**
- Префикс `raw_{date_from}_{date_to}_{cid}_{day}.csv` — статистика (groupBy=DATE),
  разделяется между `get_campaigns_daily_stat` / `get_ads_daily_stat` / `get_video_ads_daily_stat`
- Префикс `reach_{global_start_date}_{cid}_{day}.csv` — охват (groupBy=NO_GROUP_BY),
  разделяется между `get_reach_campaigns_daily_stat` / `get_reach_ads_daily_stat`
- При смене дат `_evict_stale_*_cache()` удаляет файлы с несоответствующим префиксом

## Лимиты API

- Макс. **10 кампаний** на запрос → `BATCH_SIZE = 10`
- Макс. **3 одновременные** задачи → `MAX_CONCURRENT = 3`
- Макс. **1000 скачиваний** отчётов в сутки
- Макс. **100 000 запросов** в сутки

## Кодировки

Две разные кодировки в проекте — не путать:

1. **Консоль (`sys.stdout/stderr`)** — UTF-8.
   `ozon_performance.py` перенастраивает её при импорте; на Windows default cp1251 ломает вывод кириллицы.
2. **CSV от Ozon API** — **cp1251**. Декодируется через `_decode_csv()` перед парсингом.
   Результирующие CSV в `raw_data/` сохраняются с `encoding="cp1251", errors="replace"` —
   без `errors="replace"` pandas молча пишет UTF-8, Excel на Windows открывает с кракозябрами.

## Open Questions

Все 6 функций реализованы. Открытых вопросов по endpoints нет.
Актуальный список: `info/00_api_methods.md` → раздел "Open Questions".

## Структура файлов

```
CLAUDE.md                          # этот файл
generate_tz_pdf.py                 # генератор PDF ТЗ из шаблона
TZ_ozon_performance_PHP.pdf        # результат генерации (артефакт)
info/                              # сводки API и реестр функций
  00_api_methods.md                # сводка endpoints
  01_functions_implemented.md      # реестр реализованных функций
specs/                             # спецификации функций (NN_spec_имя.md)
  TZ_ozon_performance_PHP.md       # source-of-truth ТЗ для PHP-портирования
plans/                             # планы реализации (NN_plan_имя.md)
tests/                             # зарезервировано под pytest unit-тесты с моками (пока пусто)
manual_forms/                      # заполненные вручную анкеты проекта
auto_generated/                    # автогенерируемые файлы (шаблоны)
test/                              # шаблоны для инициализации новых проектов (не тесты)
  00_README.md                     # порядок шагов 0–5 нового проекта
  01_PROJECT_STRUCTURE.md          # шаг 0: структура папок
  manual_forms/                    # шаблоны анкет (02_*, 02b_*, 02c_*, 03_*)
  auto_generated/                  # шаблоны скаффолда (04_client.py, 05_CLAUDE.md, 06_demo.ipynb)
  spec_templates/                  # шаблон spec + HOW_TO
  plan_templates/                  # шаблон plan + HOW_TO
  tz_templates/                    # шаблон ТЗ (10_*, 11_*) + HOW_TO
  09_SPEC_template_system.md       # мета-спецификация всей шаблонной системы

ozon_performance/
  ozon_performance.py              # единственный файл библиотеки
  requirements.txt
  requirements-dev.txt
  .env / .env.example
  smoke_tests/                     # smoke-тесты (реальный API)
  raw_data/                        # итоговые CSV-результаты функций
    raw_files/                     # кэш сырых CSV от API (raw_*, reach_*)
```

**Двойной folder `test/` vs `tests/`** — намеренно: `tests/` зарезервирована
под pytest unit-тесты с моками (сейчас пуста); `test/` — шаблоны для
инициализации **новых** проектов (не запускается pytest'ом).

## Отношения с шаблонной системой (`test/`)

Этот репозиторий — **готовый инстанс** шаблонного воркфлоу из `test/`
(см. `test/00_README.md`, шаги 0–5: инициализация структуры → анкета
проекта → сводка API → скаффолд → цикл реализации функций → ТЗ).
Шаги 0–4 уже выполнены: все 6 функций реализованы, ТЗ сгенерировано.

Когда пользователь говорит «инициализируй структуру», «сгенерируй демо»
и т.п., **по умолчанию это про работу внутри текущего проекта**, а не про
создание нового. Шаблоны из `test/` трогать только если пользователь явно
просит изменить сам шаблон (для будущих проектов).

Источники правды:
- `info/00_api_methods.md` — сводка endpoints Ozon Performance (приоритет над интернетом)
- `info/01_functions_implemented.md` — реестр реализованных функций
- `specs/TZ_ozon_performance_PHP.md` — source-of-truth для PDF ТЗ

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

## Воркфлоу генерации ТЗ

ТЗ — крупный deliverable, требует согласования перед генерацией:
1. Предложить структуру ТЗ (разделы, что войдёт) → ждать утверждения
2. Показать ключевые решения (какие функции, примеры, рекомендации) → ждать утверждения
3. Генерировать Markdown + PDF

**Не начинать генерацию ТЗ без явного утверждения структуры.**
