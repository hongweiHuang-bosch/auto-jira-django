from __future__ import annotations

from legacy_core.config_map import MAP_CAR_ROLE


def get_role_entry(role_index: int) -> dict:
    if role_index < 0 or role_index >= len(MAP_CAR_ROLE):
        raise IndexError(f"Invalid role index: {role_index}")
    return MAP_CAR_ROLE[role_index]


def get_role_label(role_index: int, entry: dict | None = None) -> str:
    role_entry = entry or get_role_entry(role_index)
    return role_entry.get("name") or role_entry.get("label") or f"规则组 {role_index + 1}"


def list_role_options() -> list[dict]:
    options: list[dict] = []
    for index, entry in enumerate(MAP_CAR_ROLE):
        options.append({
            "role_index": index,
            "role_label": get_role_label(index, entry),
            "jql": entry.get("jql", ""),
        })
    return options
