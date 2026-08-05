import re
with open('app/services/guest_pricing_engine.py', 'r') as f:
    content = f.read()

new_content = content.replace(
    "class HistoricalGuestPricingEngine:",
    "class HistoricalGuestPricingEngine:\n    _cache_df = None\n    _cache_time = 0"
)

new_content = new_content.replace(
    "        try:\n            df = pd.read_csv(CLEAN_DATA_PATH)",
    "        import time\n        if cls._cache_df is None or time.time() - cls._cache_time > 60:\n            try:\n                cls._cache_df = pd.read_csv(CLEAN_DATA_PATH)\n                cls._cache_time = time.time()\n            except:\n                return None, None\n        df = cls._cache_df.copy()"
)

with open('app/services/guest_pricing_engine.py', 'w') as f:
    f.write(new_content)
