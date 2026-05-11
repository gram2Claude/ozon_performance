# Сущности и функции — {API_NAME}

Заполняется после основной анкеты (`02_NEW_PROJECT_QUESTIONNAIRE.md`).
Один файл на проект. Скопируй блок функции нужное количество раз.

**Как заполнять:** в каждом пункте под строкой `Пример:` есть строка `Ответ:`.
Замени `<впиши сюда>` своим значением. Строку `Пример:` не трогай —
она остаётся как подсказка. В пункте `Fn2. Тип` поставь `[x]` напротив одного
варианта (только один тип на функцию).

---

## Функции

### Функция 1

```
Fn1. Имя функции (snake_case):
     Пример:  get_campaign_dict, get_campaign_daily_stat
     Ответ:   get_campaign_dict
     → Плейсхолдер: {FUNCTION_1_NAME}

Fn2. Тип (поставь [x] напротив одного варианта):
     [ x] Справочник  — уникальные сущности с атрибутами, без дат
     [ ] Статистика  — метрики по дням, date_from / date_to
     [ ] Охват       — кумулятивная метрика, global_start_date + date_from / date_to

Fn4. Описание одной строкой:
     Пример:  Дневная статистика по рекламным кампаниям
     Ответ:   Справочник рекламных кампаний
     → Плейсхолдер: {FN_1_ONELINER}

Fn5. Колонки выходного DataFrame (перечисли имена через запятую):
     Пример:  date, campaign_id, campaign_name, views, clicks, money_spent
     Ответ:   campaign_id, campaign_name
     Правило: все имена колонок — snake_case (например: money_spent, ad_id, campaign_name).
     Типы данных определяются автоматически из ответа API.
     → Плейсхолдер: {DF_1_COLUMNS}
```

---

### Функция 2

```
Fn1. Имя функции (snake_case):
     Пример:  get_campaign_dict, get_campaign_daily_stat
     Ответ:  get_campaigns_daily_stat
     → Плейсхолдер: {FUNCTION_2_NAME}

Fn2. Тип (поставь [x] напротив одного варианта):
     [ ] Справочник  — уникальные сущности с атрибутами, без дат
     [ x] Статистика  — метрики по дням, date_from / date_to
     [ ] Охват       — кумулятивная метрика, global_start_date + date_from / date_to

Fn4. Описание одной строкой:
     Пример:  Дневная статистика по рекламным кампаниям
     Ответ:   Статистика по рекламным кампаниям БЕЗ охватов в разбивке по дням
     → Плейсхолдер: {FN_2_ONELINER}

Fn5. Колонки выходного DataFrame (перечисли имена через запятую):
     Пример:  date, campaign_id, campaign_name, views, clicks, money_spent
     Ответ:   date, campaign_id, views, clicks, money_spent
     Правило: все имена колонок — snake_case (например: money_spent, ad_id, campaign_name).
     Типы данных определяются автоматически из ответа API.
     → Плейсхолдер: {DF_2_COLUMNS}
```

---

### Функция 3 (скопируй блок ниже если нужно больше функций)

```
Fn1. Имя функции (snake_case):
     Пример:  get_campaign_dict, get_campaign_daily_stat
     Ответ:   get_ads_daily_stat
     → Плейсхолдер: {FUNCTION_3_NAME}

Fn2. Тип (поставь [x] напротив одного варианта):
     [ ] Справочник  — уникальные сущности с атрибутами, без дат
     [x ] Статистика  — метрики по дням, date_from / date_to
     [ ] Охват       — кумулятивная метрика, global_start_date + date_from / date_to

Fn4. Описание одной строкой:
     Пример:  Дневная статистика по рекламным кампаниям
     Ответ:  Статистика по рекламным объявлениям БЕЗ охватов в разбивке по дням
     → Плейсхолдер: {FN_3_ONELINER}

Fn5. Колонки выходного DataFrame (перечисли имена через запятую):
     Пример:  date, campaign_id, campaign_name, views, clicks, money_spent
     Ответ:   date, campaign_id, ad_id, ad_name, views, clicks, money_spent
     Правило: все имена колонок — snake_case (например: money_spent, ad_id, campaign_name).
     Типы данных определяются автоматически из ответа API.
     → Плейсхолдер: {DF_3_COLUMNS}
```

---

### Функция 4 

```
Fn1. Имя функции (snake_case):
     Пример:  get_campaign_dict, get_campaign_daily_stat
     Ответ:  get_reach_campaigns_daily_stat
     → Плейсхолдер: {FUNCTION_2_NAME}

Fn2. Тип (поставь [x] напротив одного варианта):
     [ ] Справочник  — уникальные сущности с атрибутами, без дат
     [ ] Статистика  — метрики по дням, date_from / date_to
     [ x] Охват       — кумулятивная метрика, global_start_date + date_from / date_to

Fn4. Описание одной строкой:
     Пример:  Дневная статистика по рекламным кампаниям
     Ответ:   Статистика по рекламным кампаниям c учетом охватов накопительным итогом в по дням
     → Плейсхолдер: {FN_2_ONELINER}

Fn5. Колонки выходного DataFrame (перечисли имена через запятую):
     Пример:  date, campaign_id, campaign_name, views, clicks, money_spent
     Ответ:   date, campaign_id, reach, increment
     Правило: все имена колонок — snake_case (например: money_spent, ad_id, campaign_name).
     Типы данных определяются автоматически из ответа API.
     → Плейсхолдер: {DF_2_COLUMNS}
```

---

### Функция 5 

```
Fn1. Имя функции (snake_case):
     Пример:  get_campaign_dict, get_campaign_daily_stat
     Ответ:   get_reach_ads_daily_stat
     → Плейсхолдер: {FUNCTION_3_NAME}

Fn2. Тип (поставь [x] напротив одного варианта):
     [ ] Справочник  — уникальные сущности с атрибутами, без дат
     [ ] Статистика  — метрики по дням, date_from / date_to
     [x ] Охват       — кумулятивная метрика, global_start_date + date_from / date_to

Fn4. Описание одной строкой:
     Пример:  Дневная статистика по рекламным кампаниям
     Ответ:  Статистика по рекламным объявлениям c учетом охватов накопительным итогом в по дням
     → Плейсхолдер: {FN_3_ONELINER}

Fn5. Колонки выходного DataFrame (перечисли имена через запятую):
     Пример:  date, campaign_id, campaign_name, views, clicks, money_spent
     Ответ:   date, campaign_id, ad_id, ad_name, reach, increment
     Правило: все имена колонок — snake_case (например: money_spent, ad_id, campaign_name).
     Типы данных определяются автоматически из ответа API.
     → Плейсхолдер: {DF_3_COLUMNS}
```


---

### Функция 6

```
Fn1. Имя функции (snake_case):
     Пример:  get_campaign_dict, get_campaign_daily_stat
     Ответ:  get_video_ads_daily_stat
     → Плейсхолдер: {FUNCTION_2_NAME}

Fn2. Тип (поставь [x] напротив одного варианта):
     [ ] Справочник  — уникальные сущности с атрибутами, без дат
     [ x] Статистика  — метрики по дням, date_from / date_to
     [ ] Охват       — кумулятивная метрика, global_start_date + date_from / date_to

Fn4. Описание одной строкой:
     Пример:  Дневная статистика по рекламным кампаниям
     Ответ:   Статистика по видео статистике по рекламным объявлениям c учетом охватов накопительным итогом в по дням
     → Плейсхолдер: {FN_2_ONELINER}

Fn5. Колонки выходного DataFrame (перечисли имена через запятую):
     Пример:  date, campaign_id, campaign_name, views, clicks, money_spent
     Ответ:   date, campaign_id, ad_id, ad_name, views, viewable_views,clicks,reach,quartile_25,quartile_50,quartile_75,quartile_100,views_with_sound,money_spent
     Правило: все имена колонок — snake_case (например: money_spent, ad_id, campaign_name).
     Типы данных определяются автоматически из ответа API.
     → Плейсхолдер: {DF_2_COLUMNS}
```