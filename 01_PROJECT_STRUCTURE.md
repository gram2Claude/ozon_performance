# Структура проекта — {API_NAME}

Запусти этот файл в начале нового проекта. Claude создаст необходимые папки и файлы.

---

## Команда для инициализации

Скажи Claude: **«Инициализируй структуру проекта»** — и он создаст всё описанное ниже.

---

## Структура папок

```
{MODULE_NAME}/
│
├── {MODULE_NAME}.py          # основная библиотека-клиент
├── {MODULE_NAME}_demo.ipynb  # демо-ноутбук
├── requirements.txt          # зависимости
├── requirements-dev.txt      # dev-зависимости (pytest, ruff)
├── .env                      # учётные данные (не коммитить)
├── .env.example              # шаблон учётных данных
├── CLAUDE.md                 # инструкции для Claude Code
├── README.md                 # описание проекта
│
├── info/                     # справочные материалы по API и проекту
│   ├── 00_api_methods.md     # сводка методов API (заполняет Claude на Шаге 1.5)
│   └── 01_functions_implemented.md  # реестр реализованных функций (обновляется на Шаге 4)
│
├── specs/                    # спецификации функций
│   └── .gitkeep
│
├── plans/                    # планы реализации функций
│   └── .gitkeep
│
├── tests/                    # pytest unit-тесты с моками
│   ├── conftest.py           # фикстуры pytest (моки клиента, тестовые данные)
│   └── test_{MODULE_NAME}.py
│
├── smoke_tests/              # smoke-тесты на реальном API (требуют .env)
│   └── test_{FUNCTION_NAME}.py  # один файл на функцию
│
└── raw_data/                 # CSV-результаты успешных вызовов всех публичных функций (в .gitignore)
    ├── raw_files/            # сырые CSV до парсинга (кэш; raw_{date_from}_{date_to}_{campaign_id}_{day}.csv)
    └── .gitkeep
```

---

## Файлы для создания при инициализации

### `requirements.txt`
```
requests>=2.31.0
pandas>=2.0.0
python-dotenv>=1.0.0
tqdm>=4.66.0
```

### `.env.example`
```
CLIENT_ID=...
CLIENT_SECRET=...
```

### `requirements-dev.txt`
```
pytest>=8.0.0
pytest-mock>=3.12.0
ruff>=0.4.0
```

### `.gitignore`
```
.env
__pycache__/
*.pyc
.ipynb_checkpoints/
raw_data/
```

---

## Соглашения

| Тип файла | Папка | Пример имени |
|-----------|-------|-------------|
| Сводка методов API | `info/` | `00_api_methods.md` |
| Реестр реализованных функций | `info/` | `01_functions_implemented.md` |
| Спецификация функции | `specs/` | `get_campaign_daily_stat.md` |
| План реализации | `plans/` | `get_campaign_daily_stat.md` |
| Основная библиотека | корень | `{MODULE_NAME}.py` |
| Демо-ноутбук | корень | `{MODULE_NAME}_demo.ipynb` |
| Тесты | `tests/` | `test_{MODULE_NAME}.py` |
| CSV-результаты всех публичных функций | `raw_data/` | `get_campaign_dict.csv`, `get_campaigns_daily_stat_2026-04-24_2026-04-25.csv` |
