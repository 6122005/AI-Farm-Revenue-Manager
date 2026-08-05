with open('app/services/guest_pricing_engine.py', 'r') as f:
    content = f.read()

fixed_content = content.replace("        df = cls._cache_df.copy()\n        except Exception as e:\n            return None, None", "        df = cls._cache_df.copy()")

with open('app/services/guest_pricing_engine.py', 'w') as f:
    f.write(fixed_content)
