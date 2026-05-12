import os
import sys

sys.path.insert(0, str(__file__).replace("\\", "/").rsplit("/ozon_performance/", 1)[0])

from dotenv import load_dotenv
load_dotenv("ozon_performance/.env")

from ozon_performance.ozon_performance import get_reach_campaigns_daily_stat

GLOBAL_START = os.environ["TEST_START_DATE"]
DATE_FROM    = os.environ["TEST_START_DATE"]
DATE_TO      = os.environ["TEST_END_DATE"]
CACHE_DIR    = "ozon_performance/raw_data/raw_files"

df = get_reach_campaigns_daily_stat(GLOBAL_START, DATE_FROM, DATE_TO, raw_cache_dir=CACHE_DIR)
print(f"shape: {df.shape}")
print(f"columns: {list(df.columns)}")
print(df.head(5).to_markdown(index=False))
