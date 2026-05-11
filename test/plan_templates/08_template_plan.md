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
  сохраняет сырые байты каждого отчёта в `raw_data/raw_{hash}.bin`.
  При повторном запуске парсер перезапускается без API-вызовов.

### 4. Изменения в существующем коде
- (если есть — перечислить; если нет — «нет»)

## Порядок реализации

1. Добавить константу `{SPEC_COLUMNS_CONST}`
2. Реализовать приватный метод `_fetch_{SPEC_ENTITY}_for_{SPEC_SCOPE}()`
3. Реализовать публичную функцию `{SPEC_FUNCTION_NAME}()`
4. Обновить docstring модуля
5. Проверить с реальным API

## Проверка

- [ ] Функция возвращает DataFrame с колонками `{SPEC_COLUMNS_CONST}`
- [ ] При пустом ответе API возвращается пустой DataFrame с правильными колонками
- [ ] Существующие функции работают без изменений
