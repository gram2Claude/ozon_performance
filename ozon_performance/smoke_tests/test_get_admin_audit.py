"""Smoke-тест для get_admin_audit() — реальный API.

Сводный аудит (admin_audit): агрегат поверх get_campaigns_daily_stat.
Даты берутся из .env (TEST_START_DATE / TEST_END_DATE).
"""

import os
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from ozon_performance import get_admin_audit, ADMIN_AUDIT_COLUMNS  # noqa: E402

date_from = os.environ["TEST_START_DATE"]
date_to = os.environ["TEST_END_DATE"]

RAW_CACHE_DIR = PROJECT_ROOT / "raw_data" / "raw_files"

print(f"Период: {date_from} — {date_to}")
df = get_admin_audit(date_from, date_to, raw_cache_dir=RAW_CACHE_DIR)

# Assertions
assert list(df.columns) == ADMIN_AUDIT_COLUMNS, f"Колонки не совпадают: {list(df.columns)}"
if len(df) > 0:
    assert df["chef_flag"].eq(1).all(), "chef_flag должен быть == 1"
    assert df["owner_id"].notna().all(), "Есть NaN в owner_id (join со справочником не сошёлся)"
    # зерно агрегата: date × account_id × source_type_id × owner_id — без дублей
    grain = ["date", "account_id", "source_type_id", "owner_id"]
    assert not df.duplicated(subset=grain).any(), "Дубли по ключу группировки"

print("\nВсе проверки пройдены.")

out_path = PROJECT_ROOT / "raw_data" / f"get_admin_audit_{date_from}_{date_to}.csv"
df.to_csv(out_path, index=False, encoding="cp1251", errors="replace")
print(f"Сохранено: {out_path}")

saved = pd.read_csv(out_path, encoding="cp1251")
print(f"\nshape: {saved.shape}")
print(f"columns: {list(saved.columns)}")
print(f"\nhead(5) из {out_path.name}:")
print(saved.head(5).to_markdown(index=False))
