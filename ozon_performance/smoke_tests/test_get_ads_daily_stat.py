"""Smoke-тест для get_ads_daily_stat() — реальный API."""

import os
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from ozon_performance import get_ads_daily_stat, ADS_STAT_COLUMNS

date_from = os.environ["TEST_START_DATE"]
date_to = os.environ["TEST_END_DATE"]
RAW_CACHE_DIR = PROJECT_ROOT / "raw_data" / "raw_files"

print(f"get_ads_daily_stat({date_from!r}, {date_to!r})")
print(f"raw_cache_dir={RAW_CACHE_DIR}")

df = get_ads_daily_stat(date_from, date_to, raw_cache_dir=RAW_CACHE_DIR)

print(f"\nShape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

assert list(df.columns) == ADS_STAT_COLUMNS, f"Неверные колонки: {df.columns.tolist()}"
assert pd.api.types.is_string_dtype(df["campaign_id"]), "campaign_id должен быть string"
assert df["campaign_id"].notna().all(), "campaign_id содержит NaN"
assert pd.api.types.is_string_dtype(df["ad_id"]), "ad_id должен быть string"
assert df["ad_id"].notna().all(), "ad_id содержит NaN"

neg = df[df["money_spent"] < 0]
if len(neg):
    print(f"WARNING: {len(neg)} строк с отрицательным money_spent (корректировки бюджета)")

out_dir = PROJECT_ROOT / "raw_data"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / f"get_ads_daily_stat_{date_from}_{date_to}.csv"
df.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"\nСохранено: {out_path}")

saved = pd.read_csv(out_path, encoding="utf-8-sig")
print(f"\nHead(5) из сохранённого CSV:")
print(saved.head(5).to_markdown(index=False))
print("\nSMOKE TEST PASSED")
