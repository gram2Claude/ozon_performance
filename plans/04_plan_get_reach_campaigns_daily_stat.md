# Plan: `get_reach_campaigns_daily_stat`

**Статус:** черновик  
**Spec:** `specs/04_spec_get_reach_campaigns_daily_stat.md`  
**Файл реализации:** `ozon_performance/ozon_performance.py`

---

## Шаги реализации

### Шаг 1 — Вспомогательная функция `_evict_stale_reach_cache`

Аналог `_evict_stale_raw_cache`, но для reach-кэша.

```python
def _evict_stale_reach_cache(cache_dir: Path, global_start_date: str) -> None:
    prefix = f"reach_{global_start_date}_"
    for f in cache_dir.glob("reach_*"):
        if not f.name.startswith(prefix):
            f.unlink()
```

---

### Шаг 2 — Парсер `_parse_reach_csv`

```python
def _parse_reach_csv(data: bytes, campaign_id: str) -> float | None:
    """Парсит CSV groupBy=NO_GROUP_BY, возвращает суммарный Охват кампании."""
    text = _decode_csv(data)
    lines = text.splitlines()

    # Найти строку заголовка: содержит "Охват" (не "День;" — его нет при NO_GROUP_BY)
    header_idx = None
    for i, line in enumerate(lines):
        if "Охват" in line and not line.startswith(";"):
            header_idx = i
            break
    if header_idx is None:
        logger.warning("reach CSV [%s]: заголовок с 'Охват' не найден", campaign_id)
        return None

    csv_text = "\n".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
    rows = list(reader)

    # Логировать колонки при первом вызове (аналог _STAT_CSV_COLUMNS_LOGGED)
    logger.info("Колонки reach CSV: %s", reader.fieldnames)

    # Reach нельзя суммировать по строкам — уникальные пользователи пересекаются.
    # Строка "Всего" содержит дедуплицированный campaign-level охват → берём её.
    # Если "Всего" нет (одна кампания без итоговой строки) — берём единственную строку данных.
    totals_row_reach: float | None = None
    data_rows_reach: list[float] = []

    for row in rows:
        first_val = str(next(iter(row.values()), "")).strip()
        val = _parse_num(row.get("Охват"))
        if first_val in ("Всего", "Итого", "Total"):
            totals_row_reach = val
        elif first_val and val is not None:
            data_rows_reach.append(val)

    if totals_row_reach is not None:
        return totals_row_reach
    if len(data_rows_reach) == 1:
        return data_rows_reach[0]
    if data_rows_reach:
        logger.warning(
            "reach CSV [%s]: нет строки 'Всего', %d строк данных — reach неизвестен",
            campaign_id, len(data_rows_reach),
        )
    return None
```

**Логика:** строка `Всего` = дедуплицированный campaign-level reach (уникальные пользователи уже учтены API). Суммировать ad-level строки нельзя — пользователи пересекаются между объявлениями.

---

### Шаг 3 — Публичная функция `get_reach_campaigns_daily_stat`

Размещается **после** `get_ads_daily_stat` в файле, **вместо** текущего `raise NotImplementedError`.

```python
def get_reach_campaigns_daily_stat(
    global_start_date: str,
    date_from: str,
    date_to: str,
    raw_cache_dir: str | Path | None = None,
) -> pd.DataFrame:
    """Охват рекламных кампаний накопительным итогом по дням.

    Для каждого дня D запрашивает [global_start_date, D] с groupBy=NO_GROUP_BY.
    increment = reach[D] - reach[D-1] (diff по campaign_id).

    Возвращает DataFrame с колонками: date, campaign_id, reach, increment
    """
    client = OzonPerformanceClient()
    campaigns = client._fetch_all_campaigns()
    if not campaigns:
        return pd.DataFrame(columns=CAMPAIGN_REACH_COLUMNS)

    campaign_ids = [str(c["id"]) for c in campaigns if c.get("id") is not None]
    days = _date_range(date_from, date_to)
    all_rows: list[dict[str, Any]] = []

    cache_dir = Path(raw_cache_dir) if raw_cache_dir else None
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        _evict_stale_reach_cache(cache_dir, global_start_date)

    batches = list(_chunks(campaign_ids, BATCH_SIZE))
    total = len(days) * len(batches)
    with tqdm(total=total, desc="get_reach_campaigns_daily_stat") as pbar:
        for day in days:
            for batch in batches:
                if cache_dir:
                    cached = {
                        cid: cache_dir / f"reach_{global_start_date}_{cid}_{day}.csv"
                        for cid in batch
                    }
                    all_hit = all(f.exists() for f in cached.values())
                else:
                    all_hit = False

                if all_hit:
                    pairs = [(cf.read_bytes(), cid) for cid, cf in cached.items()]
                else:
                    uuid = client._submit_report(
                        batch, global_start_date, day, group_by="NO_GROUP_BY"
                    )
                    client._poll_uuid(uuid)
                    raw = client._download_report_bytes(uuid)
                    pairs = _unpack_and_cache_report(
                        raw, batch, day, global_start_date, day, cache_dir,
                        prefix="reach",
                    )

                for csv_bytes, cid in pairs:
                    reach = _parse_reach_csv(csv_bytes, cid)
                    if reach is not None:
                        all_rows.append({"date": day, "campaign_id": str(cid), "reach": reach})
                pbar.update(1)

    if not all_rows:
        return pd.DataFrame(columns=CAMPAIGN_REACH_COLUMNS)

    df = pd.DataFrame(all_rows)
    df = df.sort_values(["campaign_id", "date"])
    df["increment"] = df.groupby("campaign_id")["reach"].diff()
    df["increment"] = df["increment"].fillna(df["reach"])  # первый день: increment = reach
    return df.reindex(columns=CAMPAIGN_REACH_COLUMNS).reset_index(drop=True)
```

---

### Шаг 4 — Правка `_unpack_and_cache_report`

Функция нужна с поддержкой кастомного `prefix` (сейчас хардкод `raw_`).

**До:**
```python
def _unpack_and_cache_report(
    raw: bytes,
    batch: list[str],
    day: str,
    date_from: str,
    date_to: str,
    cache_dir: Path | None,
) -> list[tuple[bytes, str]]:
```

**После:**
```python
def _unpack_and_cache_report(
    raw: bytes,
    batch: list[str],
    day: str,
    date_from: str,
    date_to: str,
    cache_dir: Path | None,
    prefix: str = "raw",
) -> list[tuple[bytes, str]]:
```

Внутри — заменить `f"raw_{date_from}_{date_to}_{cid}_{day}.csv"` на `f"{prefix}_{date_from}_{date_to}_{cid}_{day}.csv"`.

---

### Шаг 5 — Smoke-тест `test_get_reach_campaigns_daily_stat.py`

```python
# ozon_performance/smoke_tests/test_get_reach_campaigns_daily_stat.py
import os, sys
sys.path.insert(0, str(__file__).rsplit("ozon_performance", 1)[0])
from dotenv import load_dotenv
load_dotenv("ozon_performance/.env")

from ozon_performance.ozon_performance import get_reach_campaigns_daily_stat

GLOBAL_START = os.environ["TEST_START_DATE"]
DATE_FROM    = os.environ["TEST_START_DATE"]
DATE_TO      = os.environ["TEST_END_DATE"]
CACHE_DIR    = "ozon_performance/raw_data/raw_files"

df = get_reach_campaigns_daily_stat(GLOBAL_START, DATE_FROM, DATE_TO, raw_cache_dir=CACHE_DIR)
print(f"shape: {df.shape}")
print(f"columns: {list(df.columns)}")
print(df.head(5).to_markdown(index=False))
```

---

### Шаг 6 — Обновить `info/01_functions_implemented.md`

Добавить запись по функции 4 (статус, endpoint, колонки, специфика).

---

## Порядок правок в файле

1. `_evict_stale_reach_cache` — после `_evict_stale_raw_cache` (~строка 499)
2. `_parse_reach_csv` — после `_parse_ads_csv` (~строка 491)
3. `_unpack_and_cache_report` — добавить `prefix="raw"` параметр (~строка 501)
4. `get_reach_campaigns_daily_stat` — заменить `raise NotImplementedError` (~строка 694)

## Риски

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| CSV NO_GROUP_BY имеет `День` в заголовке | средняя | парсер ищет строку с `Охват`, а не `День` |
| `Охват` суммируется некорректно (unique users) | средняя | логируем fieldnames + первые строки в smoke-тесте |
| Нет данных reach для части кампаний | низкая | пропускаем строки где reach is None |
| Большое кол-во запросов (N_days × N_batches) | высокая | кэш минимизирует повторные запросы |
