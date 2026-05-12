# Plan: {SPEC_FUNCTION_NAME}

<!-- 
Имя файла: plans/{NN}_plan_{SPEC_FUNCTION_NAME}.md
где {NN} — тот же порядковый номер, что и в соответствующей спецификации specs/{NN}_spec_...
      "plan" — фиксированное ключевое слово (показывает, что это план)
Пример: plans/01_plan_get_campaign_dict.md
        plans/02_plan_get_campaign_daily_stat.md
        plans/03_plan_get_campaign_reach_daily_stat.md
-->

## Контекст

На основании спецификации `specs/{NN}_spec_{SPEC_FUNCTION_NAME}.md`.

## Изменения в `{MODULE_NAME}.py`

### 1. Новые константы
- `{SPEC_COLUMNS_CONST}` = [список колонок]

### 2. Новые приватные методы
- `_fetch_{SPEC_ENTITY}_for_{SPEC_SCOPE}(...)` — описание

### 3. Новая публичная функция
- `{SPEC_FUNCTION_NAME}(...)` — описание
- **[ASYNC]** Добавить параметр `raw_cache_dir: str | Path | None = None` —
  сохраняет каждый распакованный CSV-отчёт в `raw_data/raw_files/raw_{date_from}_{date_to}_{campaign_id}_{day}.csv`.
  При повторном запуске (например, после фикса парсера) данные берутся из кэша — API не вызывается.
  При запросе других дат `_evict_stale_raw_cache()` удаляет `raw_*.csv` с несоответствующим префиксом.
  Функции с одинаковым endpoint и теми же датами разделяют кэш автоматически.

### 4. Изменения в существующем коде
- (если есть — перечислить; если нет — «нет»)

## Порядок реализации

1. Добавить константу `{SPEC_COLUMNS_CONST}`
2. Реализовать приватный метод `_fetch_{SPEC_ENTITY}_for_{SPEC_SCOPE}()`
3. Реализовать публичную функцию `{SPEC_FUNCTION_NAME}()`
4. Обновить docstring модуля
5. Запустить smoke-тест самостоятельно (не ждать команды пользователя):
   - Smoke-тест сохраняет DataFrame в `{MODULE_NAME}/raw_data/<имя_функции>[_{date_from}_{date_to}].csv`
   - Показать результат **из сохранённого CSV** (не из памяти): shape, columns, head(5).to_markdown(index=False)
   - **[ОХВАТ]** параметр `global_start_date` брать из `TEST_GLOBAL_START_DATE`, НЕ из `TEST_START_DATE`

## Проверка

- [ ] Функция возвращает DataFrame с колонками `{SPEC_COLUMNS_CONST}`
- [ ] При пустом ответе API возвращается пустой DataFrame с правильными колонками
- [ ] Существующие функции работают без изменений
