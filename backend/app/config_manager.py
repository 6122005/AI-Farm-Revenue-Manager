import yaml
from pathlib import Path
from typing import Any

class ConfigManager:
    _rules = {}

    @classmethod
    def load_rules(cls):
        path = Path(__file__).parent.parent / "business_rules.yaml"
        if path.exists():
            try:
                with open(path, "r") as f:
                    cls._rules = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Error loading business_rules.yaml: {e}")
                cls._rules = {}

    @classmethod
    def get_rule(cls, key: str, default: Any = None) -> Any:
        if not cls._rules:
            cls.load_rules()
        return cls._rules.get(key, default)
