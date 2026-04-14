
from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def _flatten(value: Any, indent: int = 0) -> list[str]:
    prefix = '  ' * indent
    lines: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.extend(_flatten(v, indent + 1))
            else:
                lines.append(f"{prefix}{k}: {v}")
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            lines.append(f"{prefix}- item[{idx}]")
            lines.extend(_flatten(item, indent + 1))
    else:
        lines.append(f"{prefix}{value}")
    return lines


def transfer_json_to_txt(json_path: str, txt_path: str) -> str:
    src = Path(json_path)
    dst = Path(txt_path)
    data = json.loads(src.read_text(encoding='utf-8'))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text('\n'.join(_flatten(data)), encoding='utf-8')
    return str(dst)
