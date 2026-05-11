"""Ozon Performance API client.

Публичные функции, возвращающие pandas DataFrame:
- get_campaign_dict()                                                    — Справочник рекламных кампаний
- get_campaigns_daily_stat(date_from, date_to)                           — Статистика по кампаниям без охватов по дням  ✓
- get_ads_daily_stat(date_from, date_to)                                 — Статистика по объявлениям без охватов по дням  ✓
- get_reach_campaigns_daily_stat(global_start_date, date_from, date_to) — Охват кампаний накопительно по дням
- get_reach_ads_daily_stat(global_start_date, date_from, date_to)       — Охват объявлений накопительно по дням
- get_video_ads_daily_stat(date_from, date_to)                           — Видео-статистика по объявлениям по дням

Учётные данные читаются из переменных окружения OZON_CLIENT_ID и OZON_CLIENT_SECRET
(или передаются явно в OzonPerformanceClient).
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import os
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import sys

import pandas as pd
import requests
from tqdm.auto import tqdm

# Перенастройка кодировки — обязательно на Windows (cp1251 по умолчанию).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logger = logging.getLogger(__name__)

# ── Константы ─────────────────────────────────────────────────────────────────

BASE_URL = "https://api-performance.ozon.ru"
TOKEN_PATH = "/api/client/token"
ENTITY_LIST_PATH = "/api/client/campaign"
SUBMIT_PATH = "/api/client/statistics"
POLL_PATH_PREFIX = "/api/client/statistics/"
DOWNLOAD_PATH = "/api/client/statistics/report"
# ── [TODO] Видео — endpoint не подтверждён в доках, уточнить реальным запросом
VIDEO_STATS_PATH = "/api/client/statistics/video"

BATCH_SIZE = 10                  # максимум кампаний в одном запросе (ограничение API)
HTTP_TIMEOUT_SEC = 60
RATE_LIMIT_RETRY_MAX = 5         # максимум повторов при 429
RATE_LIMIT_BASE_SEC = 10         # начальная пауза при 429 (удваивается)

POLL_INTERVAL_SEC = 7            # пауза между проверками готовности отчёта
POLL_MAX_ATTEMPTS = 40           # макс. попыток (~40 × 7 сек ≈ 5 мин)
MAX_CONCURRENT = 3               # макс. одновременных задач генерации (ограничение API)
MIN_SUBMIT_INTERVAL_SEC = 3      # минимум между POST submit (защита от burst rate limit)

TOKEN_REFRESH_LEEWAY_SEC = 60    # обновлять токен за 60 сек до истечения

# ── Колонки итоговых DataFrame ─────────────────────────────────────────────────

CAMPAIGN_DICT_COLUMNS = [
    "campaign_id",
    "campaign_name",
]

CAMPAIGN_STAT_COLUMNS = [
    "date",
    "campaign_id",
    "views",
    "clicks",
    "money_spent",
]

ADS_STAT_COLUMNS = [
    "date",
    "campaign_id",
    "ad_id",
    "ad_name",
    "views",
    "clicks",
    "money_spent",
]

CAMPAIGN_REACH_COLUMNS = [
    "date",
    "campaign_id",
    "reach",
    "increment",
]

ADS_REACH_COLUMNS = [
    "date",
    "campaign_id",
    "ad_id",
    "ad_name",
    "reach",
    "increment",
]

VIDEO_ADS_COLUMNS = [
    "date",
    "campaign_id",
    "ad_id",
    "ad_name",
    "views",
    "viewable_views",
    "clicks",
    "reach",
    "quartile_25",
    "quartile_50",
    "quartile_75",
    "quartile_100",
    "views_with_sound",
    "money_spent",
]


# ── Клиент ────────────────────────────────────────────────────────────────────

class OzonPerformanceClient:
    """HTTP-клиент для Ozon Performance API с автоматической авторизацией.

    Авторизация — OAuth 2.0 grant_type=client_credentials.
    Токен живёт ~1800 сек; клиент сам запрашивает новый при истечении.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self._client_id = client_id or os.environ.get("OZON_CLIENT_ID")
        self._client_secret = client_secret or os.environ.get("OZON_CLIENT_SECRET")
        if not self._client_id or not self._client_secret:
            raise RuntimeError(
                "Учётные данные Ozon Performance не предоставлены. "
                "Передайте client_id/client_secret или задайте "
                "OZON_CLIENT_ID и OZON_CLIENT_SECRET."
            )
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._session = requests.Session()
        # _active_uuids — UUID submitted-but-not-yet-finalized отчётов
        self._active_uuids: set[str] = set()
        self._last_submit_ts: float = 0.0

    # ── Авторизация ───────────────────────────────────────────────────────────

    def _refresh_token(self) -> None:
        url = f"{BASE_URL}{TOKEN_PATH}"
        payload = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "grant_type": "client_credentials",
        }
        resp = self._session.post(url, json=payload, timeout=HTTP_TIMEOUT_SEC)
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        expires_in = int(data.get("expires_in", 1800))
        self._token_expires_at = time.time() + expires_in

    def _ensure_token(self) -> None:
        if self._token is None or time.time() >= self._token_expires_at - TOKEN_REFRESH_LEEWAY_SEC:
            self._refresh_token()

    def _headers(self) -> dict[str, str]:
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    # ── HTTP-обёртки ──────────────────────────────────────────────────────────

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{BASE_URL}{path}"
        resp = self._session.get(
            url, headers=self._headers(), params=params, timeout=HTTP_TIMEOUT_SEC
        )
        resp.raise_for_status()
        return resp.json()

    def _get_raw(self, path: str, params: dict[str, Any] | None = None) -> bytes:
        """GET-запрос, возвращает сырые байты (для скачивания CSV/ZIP)."""
        url = f"{BASE_URL}{path}"
        resp = self._session.get(
            url, headers=self._headers(), params=params, timeout=HTTP_TIMEOUT_SEC
        )
        resp.raise_for_status()
        return resp.content

    def _post(self, path: str, body: dict[str, Any]) -> Any:
        url = f"{BASE_URL}{path}"
        headers = self._headers() | {"Content-Type": "application/json"}
        wait = RATE_LIMIT_BASE_SEC
        for attempt in range(RATE_LIMIT_RETRY_MAX + 1):
            try:
                resp = self._session.post(url, headers=headers, json=body, timeout=HTTP_TIMEOUT_SEC)
                resp.raise_for_status()
                return resp.json()
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 429:
                    if attempt == RATE_LIMIT_RETRY_MAX:
                        raise
                    retry_after = int(exc.response.headers.get("Retry-After", wait))
                    logger.warning(
                        "429 Too Many Requests — ждём %d сек (попытка %d/%d)",
                        retry_after, attempt + 1, RATE_LIMIT_RETRY_MAX,
                    )
                    time.sleep(retry_after)
                    wait *= 2
                else:
                    raise

    # ── Получение списка кампаний ─────────────────────────────────────────────

    def _fetch_all_campaigns(self) -> list[dict[str, Any]]:
        """Загружает список всех кампаний аккаунта.

        Запрос: GET /api/client/campaign
        Ответ: {"list": [{id, title, state, advObjectType, ...}]}
        """
        data = self._get(ENTITY_LIST_PATH)
        if isinstance(data, dict):
            return data.get("list") or []
        if isinstance(data, list):
            return data
        return []

    # ── Управление асинхронными отчётами ──────────────────────────────────────

    def _submit_report(
        self,
        campaign_ids: list[str],
        date_from: str,
        date_to: str,
        group_by: str = "DATE",
        path: str = SUBMIT_PATH,
    ) -> str:
        """Отправляет запрос на формирование отчёта, возвращает UUID.

        При ошибке 429 повторяет запрос с экспоненциальным backoff.
        Ждёт освобождения слота если достигнут лимит MAX_CONCURRENT.
        """
        body = {
            "campaigns": campaign_ids,
            "dateFrom": date_from,
            "dateTo": date_to,
            "groupBy": group_by,
        }
        while len(self._active_uuids) >= MAX_CONCURRENT:
            self._wait_for_free_slot()
        elapsed = time.time() - self._last_submit_ts
        if elapsed < MIN_SUBMIT_INTERVAL_SEC:
            time.sleep(MIN_SUBMIT_INTERVAL_SEC - elapsed)
        data = self._post(path, body)
        self._last_submit_ts = time.time()
        uuid = data.get("UUID") or data.get("uuid")
        if not uuid:
            raise RuntimeError(f"Запрос отчёта не вернул UUID: {data!r}")
        self._active_uuids.add(uuid)
        return uuid

    def _wait_for_free_slot(self) -> None:
        """Ждёт, пока хотя бы один активный UUID не финализируется (OK/ERROR)."""
        while self._active_uuids:
            for uuid in list(self._active_uuids):
                try:
                    data = self._get(f"{POLL_PATH_PREFIX}{uuid}")
                except requests.HTTPError:
                    self._active_uuids.discard(uuid)
                    return
                state = (data.get("state") or "").upper()
                if state in ("OK", "ERROR"):
                    self._active_uuids.discard(uuid)
                    return
            time.sleep(POLL_INTERVAL_SEC)

    def _poll_uuid(self, uuid: str) -> None:
        """Ожидает готовности отчёта по UUID. Бросает RuntimeError при ошибке/таймауте."""
        try:
            for _ in range(POLL_MAX_ATTEMPTS):
                data = self._get(f"{POLL_PATH_PREFIX}{uuid}")
                state = (data.get("state") or "").upper()
                if state == "OK":
                    return
                if state == "ERROR":
                    raise RuntimeError(f"Отчёт {uuid} завершился с ошибкой: {data!r}")
                time.sleep(POLL_INTERVAL_SEC)
            raise RuntimeError(
                f"Таймаут ожидания отчёта {uuid} после {POLL_MAX_ATTEMPTS} попыток"
            )
        finally:
            self._active_uuids.discard(uuid)

    def _download_report_bytes(self, uuid: str) -> bytes:
        """Скачивает готовый отчёт по UUID, возвращает сырые байты (CSV или ZIP)."""
        return self._get_raw(DOWNLOAD_PATH, params={"UUID": uuid})

    def _extract_csvs(self, data: bytes) -> list[bytes]:
        """Извлекает список CSV-байтов из ответа.

        ZIP (несколько кампаний) → список CSV.
        Одиночный CSV → список из одного элемента.
        """
        if data[:2] == b"PK":  # ZIP magic bytes
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                return [zf.read(name) for name in zf.namelist() if name.endswith(".csv")]
        return [data]


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _date_range(date_from: str, date_to: str) -> list[str]:
    """Генерирует список дат от date_from до date_to включительно (YYYY-MM-DD)."""
    start = datetime.strptime(date_from, "%Y-%m-%d").date()
    end = datetime.strptime(date_to, "%Y-%m-%d").date()
    if end < start:
        raise ValueError(f"date_to ({date_to}) раньше date_from ({date_from})")
    days = []
    cur = start
    while cur <= end:
        days.append(cur.isoformat())
        cur += timedelta(days=1)
    return days


def _chunks(seq: list, size: int) -> Iterable[list]:
    """Разбивает список на подсписки заданного размера."""
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def _pick(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Возвращает значение первого найденного ключа из словаря."""
    for k in keys:
        if k in row and row[k] is not None:
            return row[k]
    return default


def _parse_num(value: Any) -> float | None:
    """Конвертирует значение в float.

    Числа в CSV приходят строками с запятой как десятичным разделителем:
    «25833,00» → 25833.0
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", ".").replace(" ", "").replace("\xa0", ""))
    except (ValueError, TypeError):
        return None


def _parse_date_str(value: str) -> str | None:
    """Приводит дату к ISO-формату YYYY-MM-DD. Возвращает None для нераспознанных значений.

    CSV даты приходят как DD.MM.YYYY.
    """
    if not value or len(value) < 10:
        return None
    if value[2] == "." and value[5] == ".":  # DD.MM.YYYY
        return f"{value[6:10]}-{value[3:5]}-{value[0:2]}"
    if value[4] == "-" and value[7] == "-" and len(value) == 10:  # YYYY-MM-DD
        return value
    return None


def _decode_csv(data: bytes) -> str:
    """Декодирует CSV-байты, пробуя utf-8-sig → utf-8 → cp1251."""
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("cp1251", errors="replace")


_STAT_CSV_COLUMNS_LOGGED = False


def _parse_stat_csv(data: bytes, campaign_id: str) -> list[dict[str, Any]]:
    """Парсит один CSV статистики кампании, возвращает строки агрегированные по дням.

    Формат Ozon Performance CSV:
    - Строка 0: метаданные кампании (`;Рекламная кампания № …`)
    - Строка 1: заголовки колонок, разделитель `;`
    - Строки данных: ad-level (один баннер/объявление на строку)
    - Последняя строка `Всего`: итог — пропускается

    Агрегация: суммируем показы/клики/расход по дате → campaign-level.
    """
    global _STAT_CSV_COLUMNS_LOGGED
    text = _decode_csv(data)
    lines = text.splitlines()

    # Найти строку с заголовками колонок (начинается с "День;")
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("День;"):
            header_idx = i
            break
    if header_idx is None:
        return []

    csv_text = "\n".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
    rows = list(reader)

    if not _STAT_CSV_COLUMNS_LOGGED:
        logger.info("Колонки CSV статистики: %s", reader.fieldnames)
        print(f"[CSV columns] {reader.fieldnames}")
        _STAT_CSV_COLUMNS_LOGGED = True

    # Агрегация по дате (CSV содержит строки уровня объявления)
    daily: dict[str, dict[str, float]] = {}
    for row in rows:
        date_raw = (row.get("День") or "").strip()
        if not date_raw or date_raw in ("Всего", "Итого", "Total"):
            continue
        date_val = _parse_date_str(date_raw)
        if not date_val:
            continue
        if date_val not in daily:
            daily[date_val] = {"views": 0.0, "clicks": 0.0, "money_spent": 0.0}
        daily[date_val]["views"] += _parse_num(row.get("Показы")) or 0
        daily[date_val]["clicks"] += _parse_num(row.get("Клики")) or 0
        daily[date_val]["money_spent"] += _parse_num(
            row.get("Расход, ₽, с НДС") or row.get("Расход, ₽") or row.get("Расход")
        ) or 0

    return [
        {"date": d, "campaign_id": str(campaign_id), **vals}
        for d, vals in daily.items()
    ]


def _parse_ads_csv(data: bytes, campaign_id: str) -> list[dict[str, Any]]:
    """Парсит один CSV статистики, возвращает строки уровня объявления (без агрегации).

    Формат CSV идентичен _parse_stat_csv. Отличие: одна строка на объявление × день.
    """
    text = _decode_csv(data)
    lines = text.splitlines()

    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("День;"):
            header_idx = i
            break
    if header_idx is None:
        return []

    csv_text = "\n".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=";")
    rows = list(reader)

    result = []
    for row in rows:
        date_raw = (row.get("День") or "").strip()
        if not date_raw or date_raw in ("Всего", "Итого", "Total"):
            continue
        date_val = _parse_date_str(date_raw)
        if not date_val:
            continue
        ad_id = str(row.get("ID баннера") or "").strip()
        if not ad_id:
            continue
        result.append({
            "date": date_val,
            "campaign_id": str(campaign_id),
            "ad_id": ad_id,
            "ad_name": str(row.get("Название") or "").strip(),
            "views": _parse_num(row.get("Показы")) or 0.0,
            "clicks": _parse_num(row.get("Клики")) or 0.0,
            "money_spent": _parse_num(
                row.get("Расход, ₽, с НДС") or row.get("Расход, ₽") or row.get("Расход")
            ) or 0.0,
        })
    return result


def _evict_stale_raw_cache(cache_dir: Path, date_from: str, date_to: str) -> None:
    """Удаляет raw_* файлы с датами, отличными от текущего запроса."""
    prefix = f"raw_{date_from}_{date_to}_"
    for f in cache_dir.glob("raw_*"):
        if not f.name.startswith(prefix):
            f.unlink()


def _unpack_and_cache_report(
    raw: bytes,
    batch: list[str],
    day: str,
    date_from: str,
    date_to: str,
    cache_dir: Path | None,
) -> list[tuple[bytes, str]]:
    """Распаковывает ZIP или одиночный CSV, кэширует отдельные CSV-файлы.

    Возвращает список (csv_bytes, campaign_id).
    ZIP: campaign_id берётся из имени файла внутри архива ({id}.csv).
    CSV: campaign_id = batch[0].
    """
    result = []
    if raw[:2] == b"PK":  # ZIP
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            for name in zf.namelist():
                if not name.endswith(".csv"):
                    continue
                cid = name[:-4].split("_")[0]  # "{id}_{date}.csv" → campaign_id
                csv_bytes = zf.read(name)
                if cache_dir:
                    (cache_dir / f"raw_{date_from}_{date_to}_{cid}_{day}.csv").write_bytes(csv_bytes)
                result.append((csv_bytes, cid))
    else:
        cid = batch[0]
        if cache_dir:
            (cache_dir / f"raw_{date_from}_{date_to}_{cid}_{day}.csv").write_bytes(raw)
        result.append((raw, cid))
    return result


# ── Публичные функции ─────────────────────────────────────────────────────────

def get_campaign_dict() -> pd.DataFrame:
    """Справочник рекламных кампаний.

    Возвращает DataFrame с колонками: campaign_id, campaign_name
    """
    client = OzonPerformanceClient()
    campaigns = client._fetch_all_campaigns()
    if not campaigns:
        return pd.DataFrame(columns=CAMPAIGN_DICT_COLUMNS)
    df = pd.DataFrame([
        {
            "campaign_id": _pick(c, "id"),
            "campaign_name": _pick(c, "title"),
        }
        for c in campaigns
    ])
    df = df.dropna(subset=["campaign_id"]).drop_duplicates(subset=["campaign_id"])
    return df.reindex(columns=CAMPAIGN_DICT_COLUMNS).reset_index(drop=True)


def get_campaigns_daily_stat(
    date_from: str,
    date_to: str,
    raw_cache_dir: str | Path | None = None,
) -> pd.DataFrame:
    """Статистика по рекламным кампаниям БЕЗ охватов в разбивке по дням.

    Параметры:
        date_from     — начало периода, YYYY-MM-DD
        date_to       — конец периода,  YYYY-MM-DD
        raw_cache_dir — папка для кэша сырых байт (ZIP/CSV). Если задана,
                        повторный запуск использует кэш вместо API-запросов.

    Возвращает DataFrame с колонками: date, campaign_id, views, clicks, money_spent
    """
    client = OzonPerformanceClient()
    campaigns = client._fetch_all_campaigns()
    if not campaigns:
        return pd.DataFrame(columns=CAMPAIGN_STAT_COLUMNS)

    campaign_ids = [str(c["id"]) for c in campaigns if c.get("id") is not None]
    days = _date_range(date_from, date_to)
    all_rows: list[dict[str, Any]] = []

    cache_dir = Path(raw_cache_dir) if raw_cache_dir else None
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        _evict_stale_raw_cache(cache_dir, date_from, date_to)

    batches = list(_chunks(campaign_ids, BATCH_SIZE))
    total = len(days) * len(batches)
    with tqdm(total=total, desc="get_campaigns_daily_stat") as pbar:
        for day in days:
            for batch in batches:
                # Проверяем кэш: все ли CSV-файлы для батча уже есть
                if cache_dir:
                    cached = {
                        cid: cache_dir / f"raw_{date_from}_{date_to}_{cid}_{day}.csv"
                        for cid in batch
                    }
                    all_hit = all(f.exists() for f in cached.values())
                else:
                    all_hit = False

                if all_hit:
                    pairs = [(cf.read_bytes(), cid) for cid, cf in cached.items()]
                else:
                    uuid = client._submit_report(batch, day, day, group_by="DATE")
                    client._poll_uuid(uuid)
                    raw = client._download_report_bytes(uuid)
                    pairs = _unpack_and_cache_report(raw, batch, day, date_from, date_to, cache_dir)

                for csv_bytes, cid in pairs:
                    all_rows.extend(_parse_stat_csv(csv_bytes, cid))
                pbar.update(1)

    if not all_rows:
        return pd.DataFrame(columns=CAMPAIGN_STAT_COLUMNS)
    df = pd.DataFrame(all_rows)
    return df.reindex(columns=CAMPAIGN_STAT_COLUMNS).reset_index(drop=True)


def get_ads_daily_stat(
    date_from: str,
    date_to: str,
    raw_cache_dir: str | Path | None = None,
) -> pd.DataFrame:
    """Статистика по рекламным объявлениям БЕЗ охватов в разбивке по дням.

    Параметры:
        date_from     — начало периода, YYYY-MM-DD
        date_to       — конец периода,  YYYY-MM-DD
        raw_cache_dir — папка для кэша сырых CSV. Тот же кэш что у
                        get_campaigns_daily_stat — при одинаковых датах API не вызывается.

    Возвращает DataFrame с колонками: date, campaign_id, ad_id, ad_name, views, clicks, money_spent
    """
    client = OzonPerformanceClient()
    campaigns = client._fetch_all_campaigns()
    if not campaigns:
        return pd.DataFrame(columns=ADS_STAT_COLUMNS)

    campaign_ids = [str(c["id"]) for c in campaigns if c.get("id") is not None]
    days = _date_range(date_from, date_to)
    all_rows: list[dict[str, Any]] = []

    cache_dir = Path(raw_cache_dir) if raw_cache_dir else None
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        _evict_stale_raw_cache(cache_dir, date_from, date_to)

    batches = list(_chunks(campaign_ids, BATCH_SIZE))
    total = len(days) * len(batches)
    with tqdm(total=total, desc="get_ads_daily_stat") as pbar:
        for day in days:
            for batch in batches:
                if cache_dir:
                    cached = {
                        cid: cache_dir / f"raw_{date_from}_{date_to}_{cid}_{day}.csv"
                        for cid in batch
                    }
                    all_hit = all(f.exists() for f in cached.values())
                else:
                    all_hit = False

                if all_hit:
                    pairs = [(cf.read_bytes(), cid) for cid, cf in cached.items()]
                else:
                    uuid = client._submit_report(batch, day, day, group_by="DATE")
                    client._poll_uuid(uuid)
                    raw = client._download_report_bytes(uuid)
                    pairs = _unpack_and_cache_report(raw, batch, day, date_from, date_to, cache_dir)

                for csv_bytes, cid in pairs:
                    all_rows.extend(_parse_ads_csv(csv_bytes, cid))
                pbar.update(1)

    if not all_rows:
        return pd.DataFrame(columns=ADS_STAT_COLUMNS)
    df = pd.DataFrame(all_rows)
    return df.reindex(columns=ADS_STAT_COLUMNS).reset_index(drop=True)


def get_reach_campaigns_daily_stat(
    global_start_date: str, date_from: str, date_to: str
) -> pd.DataFrame:
    """Статистика по рекламным кампаниям c охватами накопительным итогом по дням.

    reach — кумулятивный показатель. Для каждого дня D запрашивается период
    [global_start_date, D] с groupBy=NO_GROUP_BY. increment вычисляется локально.

    Параметры:
        global_start_date — начало накопительного периода, YYYY-MM-DD
        date_from         — первый день диапазона, YYYY-MM-DD
        date_to           — последний день диапазона, YYYY-MM-DD

    Возвращает DataFrame с колонками: date, campaign_id, reach, increment
    """
    raise NotImplementedError(
        "Реализуется в Шаге 4. "
        "Требует уточнения поля reach в CSV-ответе."
    )


def get_reach_ads_daily_stat(
    global_start_date: str, date_from: str, date_to: str
) -> pd.DataFrame:
    """Статистика по рекламным объявлениям c охватами накопительным итогом по дням.

    Параметры:
        global_start_date — начало накопительного периода, YYYY-MM-DD
        date_from         — первый день диапазона, YYYY-MM-DD
        date_to           — последний день диапазона, YYYY-MM-DD

    Возвращает DataFrame с колонками: date, campaign_id, ad_id, ad_name, reach, increment
    """
    raise NotImplementedError(
        "Реализуется в Шаге 4. "
        "Требует уточнения endpoint по объявлениям и поля reach."
    )


def get_video_ads_daily_stat(date_from: str, date_to: str) -> pd.DataFrame:
    """Видео-статистика по рекламным объявлениям по дням.

    Параметры:
        date_from — начало периода, YYYY-MM-DD
        date_to   — конец периода,  YYYY-MM-DD

    Возвращает DataFrame с колонками:
        date, campaign_id, ad_id, ad_name,
        views, viewable_views, clicks, reach,
        quartile_25, quartile_50, quartile_75, quartile_100,
        views_with_sound, money_spent
    """
    raise NotImplementedError(
        "Реализуется в Шаге 4. "
        "Требует подтверждения endpoint видео-статистики (open question #9 в info/00_api_methods.md)."
    )
