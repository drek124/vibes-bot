"""Easy access to config.json

    from data import config
    config.get("economy/currency", "d$")   # -> data["economy"]["currency"], or "d$" if missing
    config.get("economy/currency")         # -> raises KeyError if missing
"""
import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent.parent / 'config.json'


class _Missing:
    def __repr__(self):
        return 'MISSING'

    def __bool__(self):
        return False


MISSING: Any = _Missing()

_data: dict = {}


def reload():
    """Re-read config.json from disk"""
    global _data
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        _data = json.load(f)


def get(path: str, default: Any = MISSING) -> Any:
    """Get a value by its "/" separated path.

    Raises KeyError if the path doesn't exist and no default is given.
    """
    value = _data
    for key in path.split('/'):
        if not isinstance(value, dict) or key not in value:
            if default is MISSING:
                raise KeyError(path)
            return default
        value = value[key]
    return value


reload()
