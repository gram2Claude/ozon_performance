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

# 2. Принципы
H1(f"2. Ключевые принципы работы с {API_NAME}")

H2("2.1. Авторизация")
BUL([
    "OAuth 2.0, grant_type=client_credentials. "
    "POST /api/client/token с Content-Type: application/json. "
    "GET возвращает 405 — только POST.",
    "Ответ: {access_token, expires_in: 1800, token_type: Bearer}.",
    "Заголовок всех запросов: Authorization: Bearer <access_token>.",
    "Токен обновлять за 60 сек до истечения (TOKEN_REFRESH_LEEWAY_SEC = 60).",
    "Учётные данные: env OZON_CLIENT_ID / OZON_CLIENT_SECRET. "
    "Формат CLIENT_ID: 94252485-1777222314558@advertising.performance.ozon.ru",
])

H2("2.2. Базовый URL и эндпоинты")
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

H2("2.3. Асинхронная схема получения отчётов (submit → poll → download)")
BUL([
    "POST /api/client/statistics → получить UUID задачи.",
    "Опрашивать GET /api/client/statistics/{UUID} каждые 7 сек (макс. 40 попыток ≈ 5 мин). "
    "Поле статуса: state. Значения: NOT_STARTED / IN_PROGRESS / OK / ERROR.",
    "После state=OK: GET /api/client/statistics/report?UUID=... "
    "→ text/csv (1 кампания) или application/zip (2+ кампаний). "
    "ZIP содержит по одному CSV на кампанию.",
])

H2("2.4. Лимиты API — критичны")
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

H2("2.5. Обработка ошибок и rate-limit")
BUL([
    "HTTP 429 — exponential backoff: стартовая пауза 10 сек, удвоение, до 5 повторов. "
    "Уважать заголовок Retry-After если присутствует.",
    "Пейсинг submit'ов: >= 3 сек между POST /api/client/statistics.",
    "Если активных UUID уже 3 — ждать освобождения слота перед новым submit.",
    "state=ERROR в polling — логировать warning, пропустить батч, продолжить цикл.",
    "Ошибки HTTP / таймаут polling — не прерывать общий цикл. Логировать и продолжать.",
])

H2("2.6. Подводные камни форматов данных")
BUL([
    'Числа в CSV — строки с запятой как десятичным разделителем: "25833,00" → 25833.0. '
    "parseNum($v): str_replace(',', '.', trim(str_replace(['\\xc2\\xa0',' '], '', $v))) → (float).",
    "Даты внутри CSV: DD.MM.YYYY. В запросах: YYYY-MM-DD. Нужен конвертер parseDateStr().",
    "Кодировка CSV: UTF-8 BOM (\\xef\\xbb\\xbf) — стрипать перед парсингом: ltrim($csv, \"\\xef\\xbb\\xbf\").",
    "Разделитель CSV: ; (не ,).",
    "Строка 0 CSV — метаданные (';Рекламная кампания № ...'). "
    "Заголовок: первая строка начинающаяся с 'День;'.",
    "Строка 'Всего' — пропускать (кроме функций охвата — брать для reach).",
    "Строка 'Корректировка' — пропускать (нет валидной даты).",
    "campaign_id — хранить как строку: (string)$campaign['id']. В JSON поле id — integer.",
    "Envelope: ответ GET /api/client/campaign приходит как {\"list\": [...]}.",
])

H2("2.7. Особый случай — кумулятивная метрика «reach» (охват)")
P(
    "reach — количество уникальных пользователей за период. "
    "Нельзя суммировать ни по дням, ни по объявлениям, ни по платформам."
)
P(
    "Для каждого дня D: POST /api/client/statistics с "
    "dateFrom=global_start_date, dateTo=D, groupBy=NO_GROUP_BY. "
    "Брать строку 'Всего' из CSV → колонка 'Охват' (API-дедуплицированный reach). "
    "increment[D] = reach[D] - reach[D-1]; для первого дня = reach."
)

# 3. Функции
H1("3. Публичные функции")

H2("3.1. get_campaign_dict()")
P("Справочник рекламных кампаний аккаунта.")
P("HTTP: GET /api/client/campaign. Пагинации нет — весь список за один запрос.")
TABLE(
    ["Поле", "Тип", "Источник (ключ API)"],
    [
        ["campaign_id", "string", "id (integer в JSON → string)"],
        ["campaign_name", "string", "title"],
    ],
    [40, 25, 115],
)

H2("3.2. get_campaigns_daily_stat(date_from, date_to)")
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
        ["money_spent", "float", "Расход, ₽, с НДС"],
    ],
    [40, 25, 115],
)

H2("3.3. get_ads_daily_stat(date_from, date_to)")
P("Статистика по объявлениям (без охватов) по дням. Гранулярность: ad_id × date.")
P("Тот же endpoint что 3.2. Агрегация не нужна — одна строка CSV = одна строка результата.")
TABLE(
    ["Поле", "Тип", "Источник (колонка CSV)"],
    [
        ["date", "string YYYY-MM-DD", "День"],
        ["campaign_id", "string", "из контекста батча"],
        ["ad_id", "string", "ID баннера"],
        ["ad_name", "string", "Название"],
        ["views", "float", "Показы"],
        ["clicks", "float", "Клики"],
        ["money_spent", "float", "Расход, ₽, с НДС"],
    ],
    [40, 25, 115],
)

H2("3.4. get_reach_campaigns_daily_stat(global_start_date, date_from, date_to)")
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
    ],
    [40, 25, 115],
)

H2("3.5. get_reach_ads_daily_stat(global_start_date, date_from, date_to)")
P(
    "Охват объявлений накопительным итогом по дням. "
    "Гранулярность: ad_id × platform × date. "
    "Нельзя агрегировать по платформам — уникальные пользователи пересекаются."
)
P("Тот же запрос и кэш что 3.4. Брать ad-level строки CSV (не 'Всего').")
TABLE(
    ["Поле", "Тип", "Источник (колонка CSV)"],
    [
        ["date", "string YYYY-MM-DD", "параметр D цикла"],
        ["campaign_id", "string", "из контекста батча"],
        ["ad_id", "string", "ID баннера"],
        ["ad_name", "string", "Название"],
        ["platform", "string", "Платформа"],
        ["reach", "float", "Охват"],
        ["increment", "float", "reach[D] - reach[D-1] по (campaign_id, ad_id, platform)"],
    ],
    [40, 25, 115],
)

H2("3.6. get_video_ads_daily_stat(date_from, date_to)")
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
        ["money_spent", "float", "Расход, ₽ (без НДС)"],
    ],
    [40, 25, 115],
)

# 4. Алгоритм
H1("4. Алгоритм сбора статистики")
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

Для охват-функций (3.4, 3.5):
   groupBy=NO_GROUP_BY, dateFrom=global_start_date, dateTo=day.
   Кэш: reach_{global_start_date}_{cid}_{day}.csv.
   После сбора: вычислить increment через diff по campaign_id
   (или campaign_id+ad_id+platform для 3.5).\
""")

# 5. Примеры
H1("5. Примеры запросов и ответов API")

H2("5.1. Авторизация")
CODE("""\
POST https://api-performance.ozon.ru/api/client/token
Content-Type: application/json

{"client_id":"94252485-1777222314558@advertising.performance.ozon.ru",
 "client_secret":"<secret>","grant_type":"client_credentials"}

Ответ: {"access_token":"eyJhbGc...","expires_in":1800,"token_type":"Bearer"}\
""")

H2("5.2. Запрос отчёта (submit)")
CODE("""\
POST https://api-performance.ozon.ru/api/client/statistics
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{"campaigns":["24251481","24296538"],"dateFrom":"2026-04-24","dateTo":"2026-04-24","groupBy":"DATE"}

Ответ: {"UUID":"12f4dc10-5e37-4b5e-aadd-f9176f224dac","state":"NOT_STARTED",...}\
""")

H2("5.3. Опрос статуса")
CODE("""\
GET https://api-performance.ozon.ru/api/client/statistics/12f4dc10-5e37-4b5e-aadd-f9176f224dac
Authorization: Bearer eyJhbGc...

Ответ (в работе): {"state":"IN_PROGRESS","UUID":"12f4dc10-..."}
Ответ (готов):    {"state":"OK","UUID":"12f4dc10-..."}\
""")

H2("5.4. Скачивание отчёта — формат CSV")
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

# 6. Примеры таблиц
H1("6. Примеры таблиц на выходе")

H2("6.1. get_campaign_dict — справочник")
TABLE(
    ["campaign_id", "campaign_name"],
    [
        ["25725956", "Баннер 28.04.2026"],
        ["24992642", "igronik_5ka_ozon_ua_aon_reg_semya_cpm"],
        ["24251481", "Кампания_Апрель_2026"],
    ],
    [35, 145],
)

H2("6.2. get_campaigns_daily_stat — кампании × день")
TABLE(
    ["date", "campaign_id", "views", "clicks", "money_spent"],
    [
        ["2026-04-24", "24251481", "147660", "107", "44298.0"],
        ["2026-04-24", "24296538", "308342", "166", "92502.6"],
        ["2026-04-25", "24251481", "147441", "90",  "44232.3"],
    ],
    [26, 28, 24, 20, 32],
)

H2("6.3. get_ads_daily_stat — объявления × день")
TABLE(
    ["date", "campaign_id", "ad_id", "ad_name", "views", "clicks", "money_spent"],
    [
        ["2026-04-24", "24296538", "602634", "Моб_Белый",  "145070", "77", "43521.0"],
        ["2026-04-24", "24296538", "602637", "Моб_Ржаной", "163272", "89", "48981.6"],
        ["2026-04-24", "24251481", "602761", "Порошок",    "86110",  "62", "25833.0"],
    ],
    [26, 26, 22, 42, 22, 18, 24],
)

H2("6.4. get_reach_campaigns_daily_stat — охват кампаний × день")
TABLE(
    ["date", "campaign_id", "reach", "increment"],
    [
        ["2026-04-24", "24251481", "622399",  "622399"],
        ["2026-04-25", "24251481", "724007",  "101608"],
        ["2026-04-24", "24296538", "1232180", "1232180"],
    ],
    [26, 28, 35, 35],
)

H2("6.5. get_reach_ads_daily_stat — охват объявлений × платформа × день")
TABLE(
    ["date", "campaign_id", "ad_id", "ad_name", "platform", "reach", "increment"],
    [
        ["2026-04-24", "24251481", "598953", "14.04–20.04_Сок", "Десктоп",    "1",     "1"],
        ["2026-04-24", "24251481", "598953", "14.04–20.04_Сок", "Моб. прил.", "66757", "66757"],
        ["2026-04-25", "24251481", "598953", "14.04–20.04_Сок", "Моб. прил.", "66757", "0"],
    ],
    [26, 26, 20, 38, 26, 20, 24],
)

H2("6.6. get_video_ads_daily_stat — видео × объявление × день")
TABLE(
    ["date", "campaign_id", "ad_id", "ad_name", "views", "v_views", "clicks",
     "q25", "q50", "q75", "q100", "snd", "money_spent"],
    [
        ["2025-08-05", "16568770", "401234", "OLV_Волга",
         "15420", "12100", "34", "9800", "7200", "5100", "3200", "6800", "18504.0"],
    ],
    [22, 22, 18, 32, 16, 16, 14, 12, 12, 12, 12, 12, 22],
)
P("Примечание: VIDEO_BANNER кампании работали в Aug 2025. Для Apr 2026 данных нет — возвращается пустой массив.")

# 7. Рекомендации
H1(f"7. Рекомендации по реализации на {TARGET_LANG}")
BUL([
    "PHP >= 8.1. Composer-проект.",
    "HTTP-клиент: guzzlehttp/guzzle с retry-middleware для 429 (exponential backoff).",
    "Кэширование токена: поля $token, $expiresAt в классе. "
    "ensureToken() перед каждым запросом: обновлять если time() >= $expiresAt - 60.",
    "parseNum($v): (float) str_replace(',', '.', trim(str_replace([\"\\xc2\\xa0\",\" \"], '', $v))).",
    "parseDateStr($v): preg_match('/^(\\d{2})\\.(\\d{2})\\.(\\d{4})$/', ...) → YYYY-MM-DD; null если не совпало.",
    "BOM-стрип: ltrim($csvContent, \"\\xef\\xbb\\xbf\") перед парсингом.",
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

# 8. Критерии приёмки
H1("8. Критерии приёмки")
BUL([
    "Все 6 функций возвращают данные с теми же колонками и в том же порядке, "
    "что в Python-эталоне ozon_performance.py.",
    "Корректная работа на реальных учётных данных: 88 кампаний, период > 7 дней, без 429.",
    "Токен переподписывается автоматически при многочасовом цикле.",
    "Лимит 3 параллельных UUID не превышается; между submit'ами >= 3 сек.",
    "Числа парсятся корректно (запятая→точка), BOM стрипается, даты в ISO YYYY-MM-DD.",
    "При сбое любого батча процесс продолжает работать, ошибка попадает в лог.",
    "Для первого дня в охват-функциях: increment == reach.",
    "Строки 'Всего' и 'Корректировка' не попадают в результат.",
    "campaign_id и ad_id — всегда строки (не числа).",
    "README с примерами вызова + .env.example.",
])

pdf.output(OUT_FILE)
print(f"OK: {OUT_FILE}")
