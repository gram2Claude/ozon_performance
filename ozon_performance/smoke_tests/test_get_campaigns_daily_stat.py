"""Smoke-тест для get_campaigns_daily_stat() — реальный API."""

import os
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from ozon_performance import get_campaigns_daily_stat, CAMPAIGN_STAT_COLUMNS  # noqa: E402

date_from = os.environ["TEST_START_DATE"]
date_to = os.environ["TEST_END_DATE"]

RAW_CACHE_DIR = PROJECT_ROOT / "raw_data" / "raw_files"

print(f"Период: {date_from} — {date_to}")
df = get_campaigns_daily_stat(date_from, date_to, raw_cache_dir=RAW_CACHE_DIR)

# Assertions
assert list(df.columns) == CAMPAIGN_STAT_COLUMNS, f"Колонки не совпадают: {list(df.columns)}"
assert df["campaign_id"].notna().all(), "Есть NaN в campaign_id"
assert pd.api.types.is_string_dtype(df["campaign_id"]), f"campaign_id не str: {df['campaign_id'].dtype}"
if len(df) > 0:
    neg = df["money_spent"].dropna().lt(0).sum()
    if neg > 0:
        print(f"[warn] {neg} строк с отрицательным money_spent (возможны возвраты бюджета)")

print("\nВсе проверки пройдены.")

out_path = PROJECT_ROOT / "raw_data" / f"get_campaigns_daily_stat_{date_from}_{date_to}.csv"
df.to_csv(out_path, index=False, encoding="cp1251", errors="replace")
print(f"Сохранено: {out_path}")

saved = pd.read_csv(out_path, encoding="cp1251", errors="replace")
print(f"\nshape: {saved.shape}")
print(f"columns: {list(saved.columns)}")
print(f"\nhead(5) из {out_path.name}:")
print(saved.head(5).to_markdown(index=False))
