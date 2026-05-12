# Реестр реализованных функций — Ozon Performance

---

## Функция: `get_campaign_dict`

- **Статус:** реализована
- **Дата реализации:** 2026-05-11
- **Тип:** справочник
- **Файл:** `ozon_performance/ozon_performance.py` → `get_campaign_dict()`
- **Spec:** `specs/01_spec_get_campaign_dict.md`
- **Plan:** `plans/01_plan_get_campaign_dict.md`
- **Smoke-test:** `ozon_performance/smoke_tests/test_get_campaign_dict.py`

### API-метод

- **Endpoint:** `GET /api/client/campaign`
- **Тип:** sync
- **Формат ответа:** `application/json`
- **Ссылка на сводку:** см. `info/00_api_methods.md` → раздел 3.1

### Параметры функции (Python-сигнатура)

```python
def get_campaign_dict() -> pd.DataFrame:
    ...
```

### Поля выходного DataFrame

| Колонка (итоговая) | Тип pandas | Источник (поле API) | Описание |
|--------------------|-----------|---------------------|----------|
| `campaign_id` | object (string) | `id` (integer в JSON) | Идентификатор кампании |
| `campaign_name` | object (string) | `title` (string) | Название кампании |

### Специфика / сложности реализации

- **`id` в JSON — integer**, не string. pandas хранит как int64 / object в зависимости от версии. В запросах статистики `campaigns` принимает строки — при передаче `campaign_id` нужен `str(id)`.
- **Пагинация отсутствует:** `GET /api/client/campaign` возвращает весь список за один запрос (проверено: 88 кампаний).
- **Envelope:** ответ — `{"list": [...]}`. Если API вернёт голый список (не dict) — обрабатывается через `isinstance(data, list)`.
- **Токен — POST:** endpoint `/api/client/token` принимает **POST** с JSON-телом. GET возвращает 405.

### История изменений

| Дата | Изменение | Причина |
|------|-----------|---------|
| 2026-05-11 | Первичная реализация | — |

---

## Функция: `get_campaigns_daily_stat`



- **Статус:** реализована
- **Дата реализации:** 2026-05-11
- **Тип:** статистика
- **Файл:** `ozon_performance/ozon_performance.py` → `get_campaigns_daily_stat()`
- **Spec:** `specs/02_spec_get_campaigns_daily_stat.md`
- **Plan:** `plans/02_plan_get_campaigns_daily_stat.md`
- **Smoke-test:** `ozon_performance/smoke_tests/test_get_campaigns_daily_stat.py`

### API-метод

- **Endpoint:** `POST /api/client/statistics`
- **Тип:** async (submit → poll → download)
- **Формат ответа:** CSV (1 кампания) / ZIP→CSV (N кампаний)
- **Ссылка на сводку:** см. `info/00_api_methods.md` → раздел 2.1–2.3

### Параметры функции (Python-сигнатура)

```python
def get_campaigns_daily_stat(
    date_from: str,  # YYYY-MM-DD
    date_to: str,    # YYYY-MM-DD
) -> pd.DataFrame:
```

### Поля выходного DataFrame

| Колонка | Тип pandas | Источник (поле CSV) | Описание |
|---------|-----------|---------------------|----------|
| `date` | object (string) | `День` (DD.MM.YYYY → YYYY-MM-DD) | Дата |
| `campaign_id` | object (string) | передаётся в парсер (не из CSV) | ID кампании |
| `views` | float64 | `Показы` | Показы (сумма по объявлениям за день) |
| `clicks` | float64 | `Клики` | Клики (сумма по объявлениям за день) |
| `money_spent` | float64 | `Расход, ₽, с НДС` | Расход с НДС (сумма по объявлениям) |

### Специфика / сложности реализации

- **CSV — ad-level, не campaign-level:** каждая строка = одно объявление (баннер). Агрегируем суммой по (date, campaign_id) в `_parse_stat_csv`.
- **Кодировка:** UTF-8 BOM — декодируем через `_decode_csv()` (пробует `utf-8-sig` → `utf-8` → `cp1251`).
- **Разделитель:** `;` (не `,`).
- **Строка 0 CSV:** метаданные кампании (`;Рекламная кампания № …`), пропускается — парсер ищет строку заголовков начиная с `День;`.
- **Строка `Всего`:** итоговая строка, пропускается.
- **Строка `Корректировка`:** корректировка бюджета без даты, пропускается в `_parse_date_str` (не соответствует формату DD.MM.YYYY).
- **`campaign_id`:** передаётся в `_parse_stat_csv` из контекста батча — в самом CSV не содержится напрямую.
- **Токен → POST** (подтверждено при реализации функции 1).

### История изменений

| Дата | Изменение | Причина |
|------|-----------|---------|
| 2026-05-11 | Первичная реализация | — |

---

## Функция: `get_ads_daily_stat`

- **Статус:** реализована
- **Дата реализации:** 2026-05-11
- **Тип:** статистика
- **Файл:** `ozon_performance/ozon_performance.py` → `get_ads_daily_stat()`
- **Spec:** `specs/03_spec_get_ads_daily_stat.md`
- **Plan:** `plans/03_plan_get_ads_daily_stat.md`
- **Smoke-test:** `ozon_performance/smoke_tests/test_get_ads_daily_stat.py`

### API-метод

- **Endpoint:** `POST /api/client/statistics`
- **Тип:** async (submit → poll → download)
- **Формат ответа:** CSV (1 кампания) / ZIP→CSV (N кампаний)
- **Ссылка на сводку:** см. `info/00_api_methods.md` → раздел 2.1–2.3

### Параметры функции (Python-сигнатура)

```python
def get_ads_daily_stat(
    date_from: str,       # YYYY-MM-DD
    date_to: str,         # YYYY-MM-DD
    raw_cache_dir: str | Path | None = None,
) -> pd.DataFrame:
```

### Поля выходного DataFrame

| Колонка | Тип pandas | Источник (поле CSV) | Описание |
|---------|-----------|---------------------|----------|
| `date` | object (string) | `День` (DD.MM.YYYY → YYYY-MM-DD) | Дата |
| `campaign_id` | object (string) | передаётся в парсер (не из CSV) | ID кампании |
| `ad_id` | object (string) | `ID баннера` | ID объявления/баннера |
| `ad_name` | object (string) | `Название` | Название объявления |
| `views` | float64 | `Показы` | Показы |
| `clicks` | float64 | `Клики` | Клики |
| `money_spent` | float64 | `Расход, ₽, с НДС` | Расход с НДС |

### Специфика / сложности реализации

- **Тот же endpoint что `get_campaigns_daily_stat`** — `POST /api/client/statistics` с `groupBy=DATE`. Парсер `_parse_ads_csv` не агрегирует строки — одна строка на объявление × день.
- **Общий кэш:** файлы `raw_{date_from}_{date_to}_{campaign_id}_{day}.csv` разделяются с `get_campaigns_daily_stat`. При одинаковых датах вторая функция читает кэш, API не вызывается.
- **Строка `Корректировка`:** пропускается через `_parse_date_str` (нет даты).
- **Строка `Всего`:** пропускается явно.
- **Пустой `ad_id`:** строка пропускается.

### История изменений

| Дата | Изменение | Причина |
|------|-----------|---------|
| 2026-05-11 | Первичная реализация | — |

---

## Функция: `get_reach_campaigns_daily_stat`

- **Статус:** реализована
- **Дата реализации:** 2026-05-12
- **Тип:** охват (кумулятивный)
- **Файл:** `ozon_performance/ozon_performance.py` → `get_reach_campaigns_daily_stat()`
- **Spec:** `specs/04_spec_get_reach_campaigns_daily_stat.md`
- **Plan:** `plans/04_plan_get_reach_campaigns_daily_stat.md`
- **Smoke-test:** `ozon_performance/smoke_tests/test_get_reach_campaigns_daily_stat.py`

### API-метод

- **Endpoint:** `POST /api/client/statistics`
- **Тип:** async (submit → poll → download)
- **groupBy:** `NO_GROUP_BY`
- **Формат ответа:** CSV (1 кампания) / ZIP→CSV (N кампаний)

### Параметры функции (Python-сигнатура)

```python
def get_reach_campaigns_daily_stat(
    global_start_date: str,           # YYYY-MM-DD — начало накопительного периода
    date_from: str,                   # YYYY-MM-DD — первый день результата
    date_to: str,                     # YYYY-MM-DD — последний день результата
    raw_cache_dir: str | Path | None = None,
) -> pd.DataFrame:
```

### Поля выходного DataFrame

| Колонка | Тип pandas | Источник | Описание |
|---------|-----------|----------|----------|
| `date` | object (string YYYY-MM-DD) | параметр D цикла | Дата |
| `campaign_id` | object (string) | из контекста батча | ID кампании |
| `reach` | float64 | `Охват` из строки «Всего» CSV | Охват [global_start_date, D] |
| `increment` | float64 | `reach.diff()` | Прирост охвата за день D |

### Специфика / сложности реализации

- **Один запрос на день:** для каждого D → `POST` с `dateFrom=global_start_date, dateTo=D, groupBy=NO_GROUP_BY`
- **Reach нельзя суммировать** ни по объявлениям, ни по дням — пользователи пересекаются. Берём строку «Всего» в CSV (campaign-level, API дедуплицировал).
- **Парсер `_parse_reach_csv`:** ищет заголовок по наличию `Охват`, берёт строку «Всего» → `totals_reach`. Fallback: единственная строка данных. Если строк > 1 без «Всего» — `None` + warning.
- **Отдельный кэш:** ключ `reach_{global_start_date}_{cid}_{day}.csv` — не пересекается с кэшем функций 2/3.
- **`_unpack_and_cache_report`** расширен параметром `prefix="raw"` (backward-compatible).
- **increment для первого дня:** `fillna(reach)` — первый день инкремент = reach.

### История изменений

| Дата | Изменение | Причина |
|------|-----------|---------|
| 2026-05-12 | Первичная реализация | — |
