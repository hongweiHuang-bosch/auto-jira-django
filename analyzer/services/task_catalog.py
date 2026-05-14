from __future__ import annotations

import importlib
from pathlib import Path

from legacy_core import config_map


def _module_mtime() -> int | None:
    module_file = getattr(config_map, '__file__', None)
    if not module_file:
        return None
    try:
        return Path(module_file).stat().st_mtime_ns
    except OSError:
        return None


_config_map_mtime = _module_mtime()


def _get_map_car_role() -> tuple[dict, ...]:
    global _config_map_mtime, config_map
    current_mtime = _module_mtime()
    if (
        current_mtime is not None
        and _config_map_mtime is not None
        and current_mtime != _config_map_mtime
    ):
        config_map = importlib.reload(config_map)
        _config_map_mtime = current_mtime
    elif _config_map_mtime is None:
        _config_map_mtime = current_mtime
    return config_map.MAP_CAR_ROLE


def get_role_entry(role_index: int) -> dict:
    map_car_role = _get_map_car_role()
    if role_index < 0 or role_index >= len(map_car_role):
        raise IndexError(f"Invalid role index: {role_index}")
    return map_car_role[role_index]


def get_role_label(role_index: int, entry: dict | None = None) -> str:
    role_entry = entry or get_role_entry(role_index)
    return role_entry.get("name") or role_entry.get("label") or f"规则组 {role_index + 1}"


def list_role_options() -> list[dict]:
    options: list[dict] = []
    for index, entry in enumerate(_get_map_car_role()):
        role_label = get_role_label(index, entry)
        options.append({
            "role_index": index,
            "name": role_label,
            "role_label": role_label,
            "jql": entry.get("jql", ""),
        })
    return options
