"""Генератор PDF: ТЗ Ozon Performance PHP.

Использование:
    pip install fpdf2
    python generate_tz_pdf.py
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos

FONT_REG  = r"C:\Windows\Fonts\arial.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_ITAL = r"C:\Windows\Fonts\ariali.ttf"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"

API_NAME    = "Ozon Performance"
TARGET_LANG = "PHP"
MODULE_NAME = "ozon_performance"
OUT_FILE    = f"TZ_{MODULE_NAME}_{TARGET_LANG}.pdf"

NX = {"new_x": XPos.LMARGIN, "new_y": YPos.NEXT}


class PDF(FPDF):
    def header(self): pass
    def footer(self):
        self.set_y(-12)
        self.set_font("arial", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Стр. {self.page_no()}", align="C")


def make_pdf() -> PDF:
    p = PDF(unit="mm", format="A4")
    p.set_margins(left=15, top=15, right=15)
    p.set_auto_page_break(auto=True, margin=15)
    p.add_font("arial", "",  FONT_REG)
    p.add_font("arial", "B", FONT_BOLD)
    p.add_font("arial", "I", FONT_ITAL)
    p.add_font("mono",  "",  FONT_MONO)
    p.add_page()
    return p


pdf = make_pdf()


def H1(text: str) -> None:
    pdf.set_font("arial", "B", 16)
    pdf.set_text_color(20, 20, 20)
    pdf.ln(2)
    pdf.multi_cell(0, 8, text, **NX)
    pdf.ln(1)


def H2(text: str) -> None:
    pdf.set_font("arial", "B", 13)
    pdf.set_text_color(30, 30, 90)
    pdf.ln(2)
    pdf.multi_cell(0, 7, text, **NX)
    pdf.ln(1)


def P(text: str) -> None:
    pdf.set_font("arial", "", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5, text, **NX)
    pdf.ln(0.5)


def BUL(items: list[str]) -> None:
    pdf.set_font("arial", "", 10)
    pdf.set_text_color(30, 30, 30)
    for it in items:
        pdf.cell(5)
        pdf.cell(3, 5, "•")
        pdf.multi_cell(0, 5, it, **NX)
    pdf.ln(0.5)


def CODE(text: str) -> None:
    pdf.set_font("mono", "", 8.5)
    pdf.set_text_color(20, 20, 20)
    pdf.set_fill_color(245, 245, 245)
    pdf.multi_cell(0, 4.2, text, fill=True, border=0, **NX)
    pdf.ln(0.5)


def TABLE(headers: list[str], rows: list[list[str]], widths: list[int]) -> None:
    pdf.set_font("arial", "B", 9)
    pdf.set_fill_color(220, 225, 240)
    pdf.set_text_color(20, 20, 20)
    for h, w in zip(headers, widths):
        pdf.cell(w, 6, h, border=1, fill=True)
    pdf.ln()
    pdf.set_font("arial", "", 9)
    fill = False
    for row in rows:
        max_lines = 1
        for val, w in zip(row, widths):
            lines = pdf.multi_cell(w, 4.5, val, dry_run=True, output="LINES")
            max_lines = max(max_lines, len(lines))
        h = 4.5 * max_lines
        if pdf.get_y() + h > pdf.h - 15:
            pdf.add_page()
        for val, w in zip(row, widths):
            x, y = pdf.get_x(), pdf.get_y()
            pdf.multi_cell(w, 4.5, val, border=1, fill=fill, max_line_height=4.5)
            pdf.set_xy(x + w, y)
        pdf.ln(h)
        fill = not fill
    pdf.ln(1)


# ══════════════════════════════════════════════════════════════════════════════

# Титул
pdf.set_font("arial", "B", 20)
pdf.set_text_color(20, 30, 90)
pdf.multi_cell(0, 10, "Техническое задание", **NX)
pdf.set_font("arial", "B", 14)
pdf.set_text_color(60, 60, 60)
pdf.multi_cell(0, 8, f"Реализация клиента {API_NAME} на {TARGET_LANG}", **NX)
pdf.ln(2)
pdf.set_font("arial", "I", 10)
pdf.set_text_color(100, 100, 100)
pdf.multi_cell(
    0, 5,
    f"Эталонная Python-реализация: {MODULE_NAME}.py. "
    f"Цель — портировать функциональность на {TARGET_LANG} с сохранением структуры выходных данных.",
    **NX,
)
pdf.ln(3)

# 1. Цель
H1("1. Цель проекта")
P(
    "Разработать PHP-библиотеку для работы с Ozon Performance API. "
    "Библиотека загружает справочник рекламных кампаний и собирает дневную статистику "
    "(показы, клики, расход, охват, видео-метрики). "
    "Выход каждой публичной функции — структурированный массив ассоциативных массивов, "
    "эквивалентный pandas DataFrame в Python-эталоне."
)

# 2. Общая логика
H1("2. Общая логика работы библиотеки")
P(
    "Все функции статистики работают по одной схеме. "
    "Ниже — последовательность шагов для get_campaigns_daily_stat, get_ads_daily_stat, get_video_ads_daily_stat."
)
BUL([
    "1. Получить справочник кампаний. "
    "GET /api/client/campaign возвращает все кампании аккаунта (88 штук). "
    "Из каждой берём id (привести к строке) и advObjectType (BANNER / VIDEO_BANNER / ...).",

    "2. Сформировать список дат. "
    "Из параметров date_from / date_to — массив отдельных дней (YYYY-MM-DD).",

    "3. Разбить кампании на батчи. "
    "API принимает максимум 10 кампаний за раз — делим список на группы по 10.",

    "4. Для каждой пары (день, батч) — запросить статистику. "
    "POST /api/client/statistics со списком ID и одним днём. "
    "API не отдаёт данные сразу — возвращает UUID задачи.",

    "5. Ждать готовности отчёта (polling). "
    "Каждые 7 сек опрашиваем GET /api/client/statistics/{UUID}. "
    "Когда state = OK — переходим к скачиванию.",

    "6. Скачать и распаковать отчёт. "
    "GET /api/client/statistics/report?UUID=... → CSV (1 кампания) или ZIP с CSV-файлами. "
    "Распаковываем, привязываем каждый CSV к своей кампании по имени файла.",

    "7. Распарсить CSV. "
    "CSV содержит строки уровня объявления (одна строка = одно объявление x день). "
    "get_campaigns_daily_stat: суммировать по (date, campaign_id). "
    "get_ads_daily_stat / get_video_ads_daily_stat: оставить как есть. "
    "get_reach_*: взять строку 'Всего' (campaign-level reach) или ad-level строки.",

    "8. Собрать итоговый результат. "
    "Все строки из всех дней и батчей объединить в один массив с фиксированными колонками.",
])
P(
    "Для охват-функций (get_reach_campaigns_daily_stat, get_reach_ads_daily_stat) "
    "логика немного отличается: для каждого дня D запрос делается за период "
    "[global_start_date, D] (не один день), а из ответа берётся кумулятивный охват. "
    "Дневной прирост (increment) вычисляется локально как разница между соседними днями."
)

# 3. Принципы
H1(f"3. Ключевые принципы работы с {API_NAME}")

H2("3.1. Авторизация")
BUL([
    "OAuth 2.0, grant_type=client_credentials. "
    "POST /api/client/token с Content-Type: application/json. "
    "GET возвращает 405 — только POST.",
    "Ответ: {access_token, expires_in: 1800, token_type: Bearer}.",
    "Заголовок всех запросов: Authorization: Bearer <access_token>.",
    "Токен обновлять за 60 сек до истечения (TOKEN_REFRESH_LEEWAY_SEC = 60).",
    "Учётные данные: env CLIENT_ID / CLIENT_SECRET. "
    "Формат CLIENT_ID: 94252485-1777222314558@advertising.performance.ozon.ru",
])

H2("3.2. Базовый URL и эндпоинты")
P("BASE_URL = https://api-performance.ozon.ru")
TABLE(
    ["Метод", "Путь", "Назначение"],
    [
        ["POST", "/api/client/token", "Выпуск access-токена"],
        ["GET",  "/api/client/campaign", "Список всех кампаний аккаунта"],
        ["POST", "/api/client/statistics", "Запрос отчёта статистики (возвращает UUID)"],
        ["GET",  "/api/client/statistics/{UUID}", "Статус готовности отчёта"],
        ["GET",  "/api/client/statistics/report", "Скачивание готового отчёта"],
    ],
    [18, 70, 92],
)

H2("3.3. Асинхронная схема получения отчётов (submit → poll → download)")
BUL([
    "POST /api/client/statistics → получить UUID задачи.",
    "Опрашивать GET /api/client/statistics/{UUID} каждые 7 сек (макс. 40 попыток ≈ 5 мин). "
    "Поле статуса: state. Значения: NOT_STARTED / IN_PROGRESS / OK / ERROR.",
    "После state=OK: GET /api/client/statistics/report?UUID=... "
    "→ text/csv (1 кампания) или application/zip (2+ кампаний). "
    "ZIP содержит по одному CSV на кампанию.",
])

H2("3.4. Лимиты API — критичны")
TABLE(
    ["Лимит", "Значение", "Как соблюдать"],
    [
        ["Кампаний в одном запросе", "≤ 10", "Разбивать на батчи по 10"],
        ["Параллельных задач генерации", "≤ 3", "Не submit'ить при 3 активных UUID"],
        ["Скачиваний отчётов в сутки", "≤ 1000", "Учитывать при больших периодах"],
        ["Запросов в сутки", "≤ 100 000", "Общий лимит (включая токен)"],
        ["Интервал между submit'ами", "≥ 3 сек", "Выдерживать паузу в коде"],
    ],
    [60, 35, 85],
)

H2("3.5. Обработка ошибок и rate-limit")
BUL([
    "HTTP 429 — exponential backoff: стартовая пауза 10 сек, удвоение, до 5 повторов. "
    "Уважать заголовок Retry-After если присутствует.",
    "Пейсинг submit'ов: >= 3 сек между POST /api/client/statistics.",
    "Если активных UUID уже 3 — ждать освобождения слота перед новым submit.",
    "state=ERROR в polling — логировать warning, пропустить батч, продолжить цикл.",
    "Ошибки HTTP / таймаут polling — не прерывать общий цикл. Логировать и продолжать.",
])

H2("3.6. Подводные камни форматов данных")
BUL([
    'Числа в CSV — строки с запятой как десятичным разделителем: "25833,00" → 25833.0. '
    "parseNum($v): str_replace(',', '.', trim(str_replace(['\\xc2\\xa0',' '], '', $v))) → (float).",
    "Даты внутри CSV: DD.MM.YYYY. В запросах: YYYY-MM-DD. Нужен конвертер parseDateStr().",
    "Кодировка CSV: cp1251 — декодировать: mb_convert_encoding($csv, 'UTF-8', 'CP1251').",
    "Разделитель CSV: ; (не ,).",
    "Строка 0 CSV — метаданные (';Рекламная кампания № ...'). "
    "Заголовок: первая строка начинающаяся с 'День;'.",
    "Строка 'Всего' — пропускать (кроме функций охвата — брать для reach).",
    "Строка 'Корректировка' — пропускать (нет валидной даты).",
    "campaign_id — хранить как строку: (string)$campaign['id']. В JSON поле id — integer.",
    "Envelope: ответ GET /api/client/campaign приходит как {\"list\": [...]}.",
])

H2("3.7. Особый случай — кумулятивная метрика «reach» (охват)")
P(
    "reach — количество уникальных пользователей за период. "
    "Нельзя суммировать по дням — за это отвечает API через groupBy=NO_GROUP_BY "
    "и кумулятивный запрос [global_start_date, D]."
)
P(
    "Для каждого дня D: POST /api/client/statistics с "
    "dateFrom=global_start_date, dateTo=D, groupBy=NO_GROUP_BY. "
    "Для campaign-level (4.4) — строка 'Всего' из CSV → колонка 'Охват' "
    "(API-дедуплицированный reach). "
    "Для ad-level (4.5) — ad-level строки CSV (одна на платформу), "
    "сумма 'Охват' по платформам в рамках одного объявления — "
    "допустимое упрощение, точной дедупликации (объявление × платформа) API не даёт."
)
P("increment[D] = reach[D] - reach[D-1]; для первого дня = reach (fillna).")

# 4. Функции
H1("4. Публичные функции")

H2("4.1. get_campaign_dict()")
P("Справочник рекламных кампаний аккаунта.")
P("HTTP: GET /api/client/campaign. Пагинации нет — весь список за один запрос.")
TABLE(
    ["Поле", "Тип", "Источник (ключ API)"],
    [
        ["campaign_id",   "string",  "id (integer в JSON → string)"],
        ["campaign_name", "string",  "title"],
        ["account_id",    "integer", "константа (значение 1 — пример, задаётся на стороне клиента)"],
        ["source_type_id","integer", "константа (значение 9 — пример, задаётся на стороне клиента)"],
        ["product_id",    "integer", "константа (значение 1 — пример, задаётся на стороне клиента)"],
        ["product_name",  "string",  "константа (значение \"prod_test\" — пример, задаётся на стороне клиента)"],
        ["camp_type",     "string",  "константа (значение \"camp_test\" — пример, задаётся на стороне клиента)"],
        ["camp_category", "string",  "константа (значение \"cat_test\" — пример, задаётся на стороне клиента)"],
        ["id_key_camp",   "string",  "вычисляется: account_id + \"_\" + campaign_id (пример: \"1_25725956\")"],
        ["owner_id",      "integer", "константа (значение 1 — пример, задаётся на стороне клиента)"],
    ],
    [40, 25, 115],
)
P("Константные поля и id_key_camp заполняются на стороне клиента — не из API. "
  "Конкретные значения приведены как пример и должны быть заменены на актуальные при интеграции.")

H2("4.2. get_campaigns_daily_stat(date_from, date_to)")
P("Статистика по кампаниям (без охватов) по дням. Гранулярность: campaign_id × date.")
P(
    "HTTP: POST /api/client/statistics, groupBy=DATE, 1 день за запрос, батчи по 10. "
    "CSV — ad-level строки. Суммировать Показы/Клики/Расход по (date, campaign_id)."
)
TABLE(
    ["Поле", "Тип", "Источник (колонка CSV)"],
    [
        ["date", "string YYYY-MM-DD", "День (DD.MM.YYYY → конвертировать)"],
        ["campaign_id", "string", "из контекста батча (не из CSV)"],
        ["views", "float", "Показы"],
        ["clicks", "float", "Клики"],
        ["costs_nds", "float", "Расход, ₽, с НДС"],
        ["costs_without_nds", "float", "вычисляется: costs_nds / 1.22 (НДС 22%)"],
        ["ak", "float", "константа (значение 0.5 — агентская комиссия 50%)"],
        ["costs_nds_ak", "float", "вычисляется: costs_nds * (1 + ak)"],
        ["costs_without_nds_ak", "float", "вычисляется: costs_without_nds * (1 + ak)"],
        ["account_id", "integer", "константа (значение 1 — пример, задаётся на стороне клиента)"],
        ["source_type_id", "integer", "константа (значение 9 — пример, задаётся на стороне клиента)"],
        ["id_key_camp", "string", "вычисляется: \"1_\" + campaign_id"],
    ],
    [40, 25, 115],
)

H2("4.3. get_ads_daily_stat(date_from, date_to)")
P("Статистика по объявлениям (без охватов) по дням. Гранулярность: ad_id × date.")
P("Тот же endpoint что 4.2. Агрегация не нужна — одна строка CSV = одна строка результата.")
TABLE(
    ["Поле", "Тип", "Источник (колонка CSV)"],
    [
        ["date", "string YYYY-MM-DD", "День"],
        ["campaign_id", "string", "из контекста батча"],
        ["ad_id", "string", "ID баннера"],
        ["ad_name", "string", "Название"],
        ["views", "float", "Показы"],
        ["clicks", "float", "Клики"],
        ["costs_nds", "float", "Расход, ₽, с НДС"],
        ["costs_without_nds", "float", "вычисляется: costs_nds / 1.22 (НДС 22%)"],
        ["ak", "float", "константа (значение 0.5 — агентская комиссия 50%)"],
        ["costs_nds_ak", "float", "вычисляется: costs_nds * (1 + ak)"],
        ["costs_without_nds_ak", "float", "вычисляется: costs_without_nds * (1 + ak)"],
        ["account_id", "integer", "константа (значение 1 — пример, задаётся на стороне клиента)"],
        ["source_type_id", "integer", "константа (значение 9 — пример, задаётся на стороне клиента)"],
        ["id_key_camp", "string", "вычисляется: \"1_\" + campaign_id"],
        ["id_key_ad", "string", "вычисляется: id_key_camp + \"_\" + ad_id (пример: \"1_25725956_602761\")"],
    ],
    [40, 25, 115],
)

H2("4.4. get_reach_campaigns_daily_stat(global_start_date, date_from, date_to)")
P("Охват кампаний накопительным итогом по дням. Гранулярность: campaign_id × date.")
P(
    "Для каждого дня D: POST /api/client/statistics с "
    "dateFrom=global_start_date, dateTo=D, groupBy=NO_GROUP_BY. "
    "Взять строку 'Всего' → колонка 'Охват'."
)
TABLE(
    ["Поле", "Тип", "Источник"],
    [
        ["date", "string YYYY-MM-DD", "параметр D цикла"],
        ["campaign_id", "string", "из контекста батча"],
        ["reach", "float", "'Охват' из строки 'Всего' CSV"],
        ["increment", "float", "reach[D] - reach[D-1]; для первого дня = reach"],
        ["account_id", "integer", "константа (значение 1 — пример, задаётся на стороне клиента)"],
        ["source_type_id", "integer", "константа (значение 9 — пример, задаётся на стороне клиента)"],
        ["id_key_camp", "string", "вычисляется: \"1_\" + campaign_id"],
    ],
    [40, 25, 115],
)

H2("4.5. get_reach_ads_daily_stat(global_start_date, date_from, date_to)")
P(
    "Охват объявлений накопительным итогом по дням. "
    "Гранулярность: ad_id × date. Reach суммируется по всем платформам."
)
P(
    "Тот же запрос и кэш что 4.4. Брать ad-level строки CSV (не 'Всего'), "
    "затем суммировать reach по платформам: groupby(date, campaign_id, ad_id)."
)
TABLE(
    ["Поле", "Тип", "Источник (колонка CSV)"],
    [
        ["date", "string YYYY-MM-DD", "параметр D цикла"],
        ["campaign_id", "string", "из контекста батча"],
        ["ad_id", "string", "ID баннера"],
        ["ad_name", "string", "Название"],
        ["reach", "float", "Охват, сумма по платформам"],
        ["increment", "float", "reach[D] - reach[D-1] по (campaign_id, ad_id)"],
        ["account_id", "integer", "константа (значение 1 — пример, задаётся на стороне клиента)"],
        ["source_type_id", "integer", "константа (значение 9 — пример, задаётся на стороне клиента)"],
        ["id_key_camp", "string", "вычисляется: \"1_\" + campaign_id"],
        ["id_key_ad", "string", "вычисляется: id_key_camp + \"_\" + ad_id (пример: \"1_25725956_602761\")"],
    ],
    [40, 25, 115],
)

H2("4.6. get_video_ads_daily_stat(date_from, date_to)")
P(
    "Видео-статистика по объявлениям по дням. "
    "Только кампании advObjectType == 'VIDEO_BANNER'. "
    "Тот же endpoint POST /api/client/statistics с groupBy=DATE."
)
P(
    "Отличия от BANNER: колонка расхода 'Расход, ₽' (без НДС), "
    "нет колонки 'Платформа', есть видео-метрики."
)
TABLE(
    ["Поле", "Тип", "Источник (колонка CSV)"],
    [
        ["date", "string YYYY-MM-DD", "День"],
        ["campaign_id", "string", "из контекста батча"],
        ["ad_id", "string", "ID баннера"],
        ["ad_name", "string", "Название"],
        ["views", "float", "Показы"],
        ["viewable_views", "float", "Видимые показы"],
        ["clicks", "float", "Клики"],
        ["quartile_25", "float", "Досмотры по квартилям 25%"],
        ["quartile_50", "float", "Досмотры по квартилям 50%"],
        ["quartile_75", "float", "Досмотры по квартилям 75%"],
        ["quartile_100", "float", "Досмотры по квартилям 100%"],
        ["views_with_sound", "float", "Просмотры со звуком"],
        ["costs_nds", "float", "Расход, ₽ (без НДС)"],
        ["costs_without_nds", "float", "вычисляется: costs_nds / 1.22 (НДС 22%)"],
        ["ak", "float", "константа (значение 0.5 — агентская комиссия 50%)"],
        ["costs_nds_ak", "float", "вычисляется: costs_nds * (1 + ak)"],
        ["costs_without_nds_ak", "float", "вычисляется: costs_without_nds * (1 + ak)"],
        ["account_id", "integer", "константа (значение 1 — пример, задаётся на стороне клиента)"],
        ["source_type_id", "integer", "константа (значение 9 — пример, задаётся на стороне клиента)"],
        ["id_key_camp", "string", "вычисляется: \"1_\" + campaign_id"],
        ["id_key_ad", "string", "вычисляется: id_key_camp + \"_\" + ad_id (пример: \"1_25725956_602761\")"],
    ],
    [40, 25, 115],
)

# 5. Алгоритм
H1("5. Алгоритм сбора статистики")
CODE("""\
1. GET /api/client/campaign → массив кампаний.
   Для get_video_ads_daily_stat: фильтр advObjectType == "VIDEO_BANNER".

2. Список дат [date_from..date_to] (YYYY-MM-DD).

3. Разбить кампании на батчи по 10 (BATCH_SIZE = 10).

4. Для каждой пары (day, batch):
   a. Если для каждого campaign_id в батче есть
      raw_{date_from}_{date_to}_{cid}_{day}.csv → читать из кэша, пропустить b-f.
   b. Выдержать >= 3 сек с последнего submit.
   c. POST /api/client/statistics:
      {"campaigns": ["id1",...], "dateFrom": day, "dateTo": day, "groupBy": "DATE"}
      → UUID.
   d. Polling каждые 7 сек: GET /api/client/statistics/{UUID}
      NOT_STARTED/IN_PROGRESS → продолжать.
      OK → скачать. ERROR → warning + пропустить батч.
      Макс. 40 попыток → таймаут, пропустить батч.
   e. GET /api/client/statistics/report?UUID={UUID}
      text/csv → один файл. application/zip → ZipArchive.
   f. Кэш: raw_{date_from}_{date_to}_{cid}_{day}.csv.
   g. Парсить CSV → список строк.

5. Собрать все строки, вернуть с фиксированными колонками.

Для охват-функций (4.4, 4.5):
   groupBy=NO_GROUP_BY, dateFrom=global_start_date, dateTo=day.
   Кэш: reach_{global_start_date}_{cid}_{day}.csv.
   После сбора: вычислить increment через diff по campaign_id
   (или campaign_id+ad_id для 4.5).
   Первый день: increment = reach (fillna).\
""")

# 6. Примеры
H1("6. Примеры запросов и ответов API")

H2("6.1. Авторизация")
CODE("""\
POST https://api-performance.ozon.ru/api/client/token
Content-Type: application/json

{"client_id":"94252485-1777222314558@advertising.performance.ozon.ru",
 "client_secret":"<secret>","grant_type":"client_credentials"}

Ответ: {"access_token":"eyJhbGc...","expires_in":1800,"token_type":"Bearer"}\
""")

H2("6.2. Запрос отчёта (submit)")
CODE("""\
POST https://api-performance.ozon.ru/api/client/statistics
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{"campaigns":["24251481","24296538"],"dateFrom":"2026-04-24","dateTo":"2026-04-24","groupBy":"DATE"}

Ответ: {"UUID":"12f4dc10-5e37-4b5e-aadd-f9176f224dac","state":"NOT_STARTED",...}\
""")

H2("6.3. Опрос статуса")
CODE("""\
GET https://api-performance.ozon.ru/api/client/statistics/12f4dc10-5e37-4b5e-aadd-f9176f224dac
Authorization: Bearer eyJhbGc...

Ответ (в работе): {"state":"IN_PROGRESS","UUID":"12f4dc10-..."}
Ответ (готов):    {"state":"OK","UUID":"12f4dc10-..."}\
""")

H2("6.4. Скачивание отчёта — формат CSV")
CODE("""\
GET https://api-performance.ozon.ru/api/client/statistics/report?UUID=12f4dc10-...

1 кампания → Content-Type: text/csv
2+ кампаний → Content-Type: application/zip (файлы внутри: {campaign_id}.csv)

Пример CSV (BANNER, groupBy=DATE):
;Рекламная кампания № 24251481, Кампания, период 24.04.2026-24.04.2026
День;ID баннера;Название;Показы;Клики;CTR (%);Охват;...;Расход, ₽, с НДС
24.04.2026;602761;21.04–27.04_Порошок;86110;62;0,07;...;25833,00
24.04.2026;602764;21.04–27.04_Стирка;61550;45;0,07;...;18465,00
Всего;;...

Парсинг: найти строку-заголовок (начинается с "День;"),
skip строки "Всего" и "Корректировка".\
""")

# 7. Примеры таблиц
H1("7. Примеры таблиц на выходе")

H2("7.1. get_campaign_dict — справочник")
TABLE(
    ["campaign_id", "campaign_name"],
    [
        ["25725956", "Баннер 28.04.2026"],
        ["24992642", "igronik_5ka_ozon_ua_aon_reg_semya_cpm"],
        ["24251481", "Кампания_Апрель_2026"],
    ],
    [35, 145],
)
P("Константные и вычисляемые поля для тех же трёх строк:")
TABLE(
    ["campaign_id", "account_id", "source_type_id", "product_id", "product_name", "camp_type", "camp_category", "id_key_camp", "owner_id"],
    [
        ["25725956", "1", "9", "1", "prod_test", "camp_test", "cat_test", "1_25725956", "1"],
        ["24992642", "1", "9", "1", "prod_test", "camp_test", "cat_test", "1_24992642", "1"],
        ["24251481", "1", "9", "1", "prod_test", "camp_test", "cat_test", "1_24251481", "1"],
    ],
    [22, 20, 24, 20, 22, 20, 22, 24, 18],
)
P("Значения константных полей приведены как пример — при интеграции заменить на актуальные.")

H2("7.2. get_campaigns_daily_stat — кампании × день")
TABLE(
    ["date", "campaign_id", "views", "clicks", "costs_nds"],
    [
        ["2026-04-24", "24251481", "147660", "107", "44298.0"],
        ["2026-04-24", "24296538", "308342", "166", "92502.6"],
        ["2026-04-25", "24251481", "147441", "90",  "44232.3"],
    ],
    [26, 28, 24, 20, 32],
)
P("Вычисляемые поля (значения для тех же 3 строк в том же порядке):")
TABLE(
    ["costs_without_nds", "ak", "costs_nds_ak", "costs_without_nds_ak"],
    [
        ["36310.7", "0.5", "66447.0",  "54466.1"],
        ["75821.0", "0.5", "138753.9", "113731.5"],
        ["36256.8", "0.5", "66348.5",  "54385.2"],
    ],
    [36, 14, 32, 38],
)
P("Константные поля account_id, source_type_id и вычисляемое id_key_camp (для тех же 3 строк):")
TABLE(
    ["account_id", "source_type_id", "id_key_camp"],
    [
        ["1", "9", "1_24251481"],
        ["1", "9", "1_24296538"],
        ["1", "9", "1_24251481"],
    ],
    [26, 32, 62],
)
P("Значения account_id и source_type_id приведены как пример — при интеграции заменить на актуальные.")

H2("7.3. get_ads_daily_stat — объявления × день")
TABLE(
    ["date", "campaign_id", "ad_id", "ad_name", "views", "clicks", "costs_nds"],
    [
        ["2026-04-24", "24296538", "602634", "Моб_Белый",  "145070", "77", "43521.0"],
        ["2026-04-24", "24296538", "602637", "Моб_Ржаной", "163272", "89", "48981.6"],
        ["2026-04-24", "24251481", "602761", "Порошок",    "86110",  "62", "25833.0"],
    ],
    [26, 24, 20, 40, 20, 14, 26],
)
P("Вычисляемые поля (значения для тех же 3 строк в том же порядке):")
TABLE(
    ["costs_without_nds", "ak", "costs_nds_ak", "costs_without_nds_ak"],
    [
        ["35673.0", "0.5", "65281.5", "53509.5"],
        ["40148.9", "0.5", "73472.4", "60223.4"],
        ["21174.6", "0.5", "38749.5", "31761.9"],
    ],
    [36, 14, 32, 38],
)
P("Константные поля account_id, source_type_id и вычисляемые ключи id_key_camp, id_key_ad (для тех же 3 строк):")
TABLE(
    ["account_id", "source_type_id", "id_key_camp", "id_key_ad"],
    [
        ["1", "9", "1_24296538", "1_24296538_602634"],
        ["1", "9", "1_24296538", "1_24296538_602637"],
        ["1", "9", "1_24251481", "1_24251481_602761"],
    ],
    [22, 28, 34, 42],
)
P("Значения account_id и source_type_id приведены как пример — при интеграции заменить на актуальные.")

H2("7.4. get_reach_campaigns_daily_stat — охват кампаний × день")
TABLE(
    ["date", "campaign_id", "reach", "increment"],
    [
        ["2026-04-24", "24251481", "622399",  "622399"],
        ["2026-04-25", "24251481", "724007",  "101608"],
        ["2026-04-24", "24296538", "1232180", "1232180"],
    ],
    [26, 28, 35, 35],
)
P("Константные поля account_id, source_type_id и вычисляемое id_key_camp (для тех же 3 строк в том же порядке):")
TABLE(
    ["account_id", "source_type_id", "id_key_camp"],
    [
        ["1", "9", "1_24251481"],
        ["1", "9", "1_24251481"],
        ["1", "9", "1_24296538"],
    ],
    [26, 32, 62],
)
P("Значения account_id и source_type_id приведены как пример — при интеграции заменить на актуальные.")

H2("7.5. get_reach_ads_daily_stat — охват объявлений × день")
TABLE(
    ["date", "campaign_id", "ad_id", "ad_name", "reach", "increment"],
    [
        ["2026-04-24", "24251481", "598953", "14.04–20.04_Сок",       "66758", "66758"],
        ["2026-04-25", "24251481", "598953", "14.04–20.04_Сок",       "66758", "0"],
        ["2026-04-24", "24251481", "598956", "14.04–20.04_Туалетная", "87734", "87734"],
    ],
    [26, 24, 20, 50, 22, 22],
)
P("Константные поля account_id, source_type_id и вычисляемые ключи id_key_camp, id_key_ad (для тех же 3 строк в том же порядке):")
TABLE(
    ["account_id", "source_type_id", "id_key_camp", "id_key_ad"],
    [
        ["1", "9", "1_24251481", "1_24251481_598953"],
        ["1", "9", "1_24251481", "1_24251481_598953"],
        ["1", "9", "1_24251481", "1_24251481_598956"],
    ],
    [22, 28, 34, 42],
)
P("Значения account_id и source_type_id приведены как пример — при интеграции заменить на актуальные.")

H2("7.6. get_video_ads_daily_stat — видео × объявление × день")
TABLE(
    ["date", "campaign_id", "ad_id", "ad_name", "views", "v_views", "clicks"],
    [
        ["2025-08-05", "16568770", "401234", "OLV_Волга", "15420", "12100", "34"],
    ],
    [22, 22, 18, 38, 18, 18, 16],
)
P("Видео-метрики (значения для той же строки):")
TABLE(
    ["q25", "q50", "q75", "q100", "views_with_sound", "costs_nds"],
    [
        ["9800", "7200", "5100", "3200", "6800", "18504.0"],
    ],
    [22, 22, 22, 22, 36, 32],
)
P("Вычисляемые поля (значения для той же строки):")
TABLE(
    ["costs_without_nds", "ak", "costs_nds_ak", "costs_without_nds_ak"],
    [
        ["15167.2", "0.5", "27756.0", "22750.8"],
    ],
    [36, 14, 32, 38],
)
P("Константные поля account_id, source_type_id и вычисляемые ключи id_key_camp, id_key_ad (для той же строки):")
TABLE(
    ["account_id", "source_type_id", "id_key_camp", "id_key_ad"],
    [
        ["1", "9", "1_16568770", "1_16568770_401234"],
    ],
    [22, 28, 34, 42],
)
P("Примечание: VIDEO_BANNER кампании работали в Aug 2025. Для Apr 2026 данных нет — возвращается пустой массив.")
P("Значения account_id и source_type_id приведены как пример — при интеграции заменить на актуальные.")

# 8. Рекомендации
H1(f"8. Рекомендации по реализации на {TARGET_LANG}")
BUL([
    "PHP >= 8.1. Composer-проект.",
    "HTTP-клиент: guzzlehttp/guzzle с retry-middleware для 429 (exponential backoff).",
    "Кэширование токена: поля $token, $expiresAt в классе. "
    "ensureToken() перед каждым запросом: обновлять если time() >= $expiresAt - 60.",
    "parseNum($v): (float) str_replace(',', '.', trim(str_replace([\"\\xc2\\xa0\",\" \"], '', $v))).",
    "parseDateStr($v): preg_match('/^(\\d{2})\\.(\\d{2})\\.(\\d{4})$/', ...) → YYYY-MM-DD; null если не совпало.",
    "Декодирование cp1251: mb_convert_encoding($csvContent, 'UTF-8', 'CP1251') перед парсингом.",
    "Поиск заголовка CSV: первая строка начинающаяся с 'День;'.",
    "ZIP: ZipArchive → читать каждый файл, привязать к campaign_id по имени файла.",
    "Логирование: PSR-3 / monolog. Все skip-предупреждения уровня warning.",
    "Тесты: моки HTTP на все 6 функций + retry на 429 + таймаут polling.",
])

H2("Константы (не хардкодить в цикле)")
TABLE(
    ["Константа", "Значение"],
    [
        ["POLL_INTERVAL_SEC",       "7"],
        ["POLL_MAX_ATTEMPTS",       "40"],
        ["TOKEN_REFRESH_LEEWAY_SEC","60"],
        ["RATE_LIMIT_BASE_SEC",     "10"],
        ["RATE_LIMIT_RETRY_MAX",    "5"],
        ["MIN_SUBMIT_INTERVAL_SEC", "3"],
        ["MAX_CONCURRENT",          "3"],
        ["BATCH_SIZE",              "10"],
    ],
    [80, 100],
)

# 9. Критерии приёмки
H1("9. Критерии приёмки")
BUL([
    "Все 6 функций возвращают данные с теми же колонками и в том же порядке, "
    "что в Python-эталоне ozon_performance.py.",
    "Корректная работа на реальных учётных данных: 88 кампаний, период > 7 дней, без 429.",
    "Токен переподписывается автоматически при многочасовом цикле.",
    "Лимит 3 параллельных UUID не превышается; между submit'ами >= 3 сек.",
    "Числа парсятся корректно (запятая→точка), CSV декодируется из cp1251, даты в ISO YYYY-MM-DD.",
    "При сбое любого батча процесс продолжает работать, ошибка попадает в лог.",
    "Для первого дня в охват-функциях: increment == reach.",
    "Строки 'Всего' и 'Корректировка' не попадают в результат.",
    "campaign_id и ad_id — всегда строки (не числа).",
    "README с примерами вызова + .env.example.",
])

pdf.output(OUT_FILE)
print(f"OK: {OUT_FILE}")
