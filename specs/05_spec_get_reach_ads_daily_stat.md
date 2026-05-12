# Spec: `get_reach_ads_daily_stat`

**Статус:** черновик
**Функция:** `get_reach_ads_daily_stat`
**Файл:** `ozon_performance/ozon_performance.py`

---

## 1. Назначение

Возвращает накопительный охват (уникальные пользователи) по отдельным объявлениям с ежедневным инкрементом.

Тот же паттерн что `get_reach_campaigns_daily_stat`: для каждого дня D запрашивается `[global_start_date, D]` с `groupBy=NO_GROUP_BY`. Разница — парсим строки по объявлениям, а не строку `Всего`.

---

## 2. Сигнатура

```python
def get_reach_ads_daily_stat(
    global_start_date: str,           # YYYY-MM-DD — начало накопительного периода
    date_from: str,                   # YYYY-MM-DD — первый день результирующего диапазона
    date_to: str,                     # YYYY-MM-DD — последний день результирующего диапазона
    raw_cache_dir: str | Path | None = None,
) -> pd.DataFrame:
```

---

## 3. Выходной DataFrame

Колонки: `ADS_REACH_COLUMNS = ["date", "campaign_id", "ad_id", "ad_name", "reach", "increment"]`

| Колонка | Тип pandas | Источник | Описание |
|---------|-----------|----------|----------|
| `date` | object (string YYYY-MM-DD) | параметр D цикла | Дата |
| `campaign_id` | object (string) | из контекста батча | ID кампании |
| `ad_id` | object (string) | `ID баннера` из CSV | ID объявления |
| `ad_name` | object (string) | `Название` из CSV | Название объявления |
| `reach` | float64 | `Охват` из CSV, сумма по платформам | Охват [global_start_date, D] по объявлению |
| `increment` | float64 | `reach.diff()` | Прирост охвата за день D |

---

## 4. Формат CSV (подтверждён реальным запросом)

```
;Рекламная кампания № 24296538, ..., период 20.04.2026-24.04.2026
ID баннера;Название;Платформа;Показы;Клики;CTR (%);Охват;...
602634;Моб_Белый;Мобильное приложение;778392;405;0,05;687355;...
602634;Моб_Белый;Десктоп;1;0;0,00;1;...
602637;Моб_Ржаной;Мобильное приложение;758418;446;0,06;676886;...
602637;Моб_Ржаной;Десктоп;3;0;0,00;3;...
Корректировка;;;;;;;;-194,62
Всего;;;1536814;851;0,06;1232177;...
```

**Ключевое наблюдение:** одно объявление = несколько строк (по одной на платформу).

---

## 5. Агрегация по платформам

Reach суммируется по всем платформам. Одна строка результата = одно объявление × один день.
`increment` вычисляется по группе `(campaign_id, ad_id)`.

---

## 6. Алгоритм

```
Шаг 1. Получить campaign_ids — GET /api/client/campaign
Шаг 2. Для каждого дня D в [date_from, date_to]:
   Для каждого батча из 10 кампаний:
     - Проверить кэш: reach_{global_start_date}_{cid}_{D}.csv
       (тот же кэш что у get_reach_campaigns_daily_stat — файлы разделяются)
     - Если нет в кэше: submit → poll → download → сохранить
     - Парсить: _parse_reach_ads_csv(csv_bytes, campaign_id) → list[{ad_id, ad_name, reach}]
Шаг 3. Собрать строки: {date: D, campaign_id, ad_id, ad_name, reach}
Шаг 4. Суммировать по платформам:
   df = df.groupby(["date", "campaign_id", "ad_id", "ad_name"], as_index=False)["reach"].sum()
Шаг 5. Вычислить increment:
   df.sort_values(["campaign_id", "ad_id", "date"])
   df["increment"] = df.groupby(["campaign_id", "ad_id"])["reach"].diff()
   df["increment"] = df["increment"].fillna(df["reach"])
Шаг 6. Вернуть df[ADS_REACH_COLUMNS]
```

---

## 7. Общий кэш с `get_reach_campaigns_daily_stat`

Файлы `reach_{global_start_date}_{cid}_{day}.csv` разделяются между функциями.
При одинаковом `global_start_date` вторая функция читает из кэша — API не вызывается.

---

## 8. Пример результата

| date | campaign_id | ad_id | ad_name | reach | increment |
|------|-------------|-------|---------|-------|-----------|
| 2026-04-24 | 24251481 | 598953 | 14.04–20.04_Сок | 66758.0 | 66758.0 |
| 2026-04-25 | 24251481 | 598953 | 14.04–20.04_Сок | 66758.0 | 0.0 |
| 2026-04-24 | 24251481 | 598956 | 14.04–20.04_Туалетная | 87734.0 | 87734.0 |
