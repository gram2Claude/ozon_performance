"""Smoke-тест для get_campaign_dict() — реальный API."""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from ozon_performance import get_campaign_dict, CAMPAIGN_DICT_COLUMNS  # noqa: E402

df = get_campaign_dict()

# Assertions
assert list(df.columns) == CAMPAIGN_DICT_COLUMNS, f"Колонки не совпадают: {list(df.columns)}"
assert df.shape[0] > 0, "DataFrame пустой — кампаний не найдено"
assert df["campaign_id"].notna().all(), "Есть NaN в campaign_id"
assert df["campaign_id"].duplicated().sum() == 0, "Есть дубликаты campaign_id"
assert pd.api.types.is_string_dtype(df["campaign_id"]), f"campaign_id не str: {df['campaign_id'].dtype}"

print("Все проверки пройдены.")

out_path = PROJECT_ROOT / "raw_data" / "get_campaign_dict.csv"
df.to_csv(out_path, index=False, encoding="utf-8-sig")
print(f"Сохранено: {out_path}")

# Показ из сохранённого CSV
saved = pd.read_csv(out_path, encoding="utf-8-sig")
print(f"\nshape: {saved.shape}")
print(f"columns: {list(saved.columns)}")
print(f"\nhead(5) из {out_path.name}:")
print(saved.head(5).to_markdown(index=False))
