# Spec: `get_reach_campaigns_daily_stat`

**Статус:** черновик  
**Функция:** `get_reach_campaigns_daily_stat`  
**Файл:** `ozon_performance/ozon_performance.py`

---

## 1. Назначение

Возвращает накопительный охват (уникальные пользователи) по рекламным кампаниям с ежедневным инкрементом.

`reach` — кумулятивный показатель: нельзя суммировать по дням.  
Для каждого дня D запрашивается период **[global_start_date, D]** с `groupBy=NO_GROUP_BY`.  
`increment` вычисляется локально: `reach[D] - reach[D-1]`.

---

## 2. Сигнатура

```python
def get_reach_campaigns_daily_stat(
    global_start_date: str,           # YYYY-MM-DD — начало накопительного периода
    date_from: str,                   # YYYY-MM-DD — первый день результирующего диапазона
    date_to: str,                     # YYYY-MM-DD — последний день результирующего диапазона
    raw_cache_dir: str | Path | None = None,
) -> pd.DataFrame:
```

**Ограничения:**
- `global_start_date <= date_from <= date_to`

---

## 3. Выходной DataFrame

Колонки: `CAMPAIGN_REACH_COLUMNS = ["date", "campaign_id", "reach", "increment"]`

| Колонка | Тип pandas | Источник | Описание |
|---------|-----------|----------|----------|
| `date` | object (string YYYY-MM-DD) | параметр D цикла | Дата |
| `campaign_id` | object (string) | из контекста батча | ID кампании |
| `reach` | float64 | `Охват` из CSV | Охват [global_start_date, D] |
| `increment` | float64 | `reach.diff()` | Прирост охвата за день D |

---

## 4. Алгоритм

```
Шаг 1. Получить campaign_ids — GET /api/client/campaign
Шаг 2. Для каждого дня D в [date_from, date_to]:
   Для каждого батча из 10 кампаний:
     - Проверить кэш: reach_{global_start_date}_{cid}_{D}.csv
     - Если нет в кэше:
         UUID = POST /api/client/statistics
                  {campaigns: batch, dateFrom: global_start_date, dateTo: D, groupBy: NO_GROUP_BY}
         poll UUID → download → распаковать ZIP/CSV → сохранить в кэш
     - Парсить: _parse_reach_csv(csv_bytes, campaign_id) → {campaign_id, reach}
Шаг 3. Собрать строки: {date: D, campaign_id, reach}
Шаг 4. Вычислить increment:
   df.sort_values(["campaign_id", "date"])
   df["increment"] = df.groupby("campaign_id")["reach"].diff().fillna(df["reach"])
Шаг 5. Вернуть df[CAMPAIGN_REACH_COLUMNS]
```

---

## 5. Кэш

Ключ отличается от кэша функций 2/3:

```
reach_{global_start_date}_{campaign_id}_{day}.csv
```

Не пересекается с `raw_{date_from}_{date_to}_{cid}_{day}.csv`.  
Инвалидация: файлы с другим `global_start_date` удаляются при запуске.

---

## 6. Парсер `_parse_reach_csv`

### CSV с `groupBy=NO_GROUP_BY` — ожидаемый формат

⚠️ Формат **не подтверждён** реальным запросом. Ожидаемая структура:

```
;Рекламная кампания № {id}, {name}, период {date_from}-{date_to}
ID баннера;Название;Платформа;Показы;Клики;CTR (%);Охват;...
{id};{name};...;{reach};...
Всего;...
```

Отличие от groupBy=DATE: **нет колонки `День`**.

### Стратегия парсера:

1. Найти строку заголовка: ищем строку с `Охват` (не `День;`)
2. Взять `Охват` из строки **`Всего`** (campaign-level итог, уникальные пользователи дедуплицированы API)
3. Если `Всего` нет и единственная строка данных — взять её
4. Если `Всего` нет и строк данных > 1 — логировать warning, вернуть `None`

> Reach нельзя суммировать по ad-level строкам: пользователи пересекаются между объявлениями.
> Строка `Всего` = дедуплицированный campaign-level охват за период.

---

## 7. Пример результата

| date | campaign_id | reach | increment |
|------|-------------|-------|-----------|
| 2025-01-01 | 123456 | 5000.0 | 5000.0 |
| 2025-01-02 | 123456 | 7200.0 | 2200.0 |
| 2025-01-03 | 123456 | 8100.0 | 900.0 |

---

## 8. Открытые вопросы

1. Структура CSV при `groupBy=NO_GROUP_BY`: есть ли колонка `День`?
2. Ad-level или campaign-level строки в ответе?
3. Название колонки reach: `Охват` (как в groupBy=DATE)?
4. Что делать если reach для дня отсутствует (нет данных по кампании)?

→ Ответы получить в smoke-тесте: выводить `reader.fieldnames` и первые строки.
