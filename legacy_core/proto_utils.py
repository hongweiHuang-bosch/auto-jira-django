from __future__ import annotations
import re
import logging
from typing import Dict, Any

logger = logging.getLogger("CAN-AI-JIRA")

class ProtoParser:
    @staticmethod
    def parse_property_ids(proto_content: str) -> Dict[str, Dict[str, Any]]:
        prop_id_map: Dict[str, Dict[str, Any]] = {}

        enum_start = proto_content.find('enum Property_ID {')
        if enum_start == -1:
            logger.warning("未找到 enum Property_ID")
            return prop_id_map

        brace = 0
        enum_end = -1
        for i in range(enum_start, len(proto_content)):
            ch = proto_content[i]
            if ch == '{':
                brace += 1
            elif ch == '}':
                brace -= 1
                if brace == 0:
                    enum_end = i + 1
                    break
        if enum_end == -1:
            logger.warning("enum Property_ID 未正确结束")
            return prop_id_map

        enum_content = proto_content[enum_start:enum_end]
        pattern = r'(\w+)\s*=\s*(\d+);\s*//\s*([^|]+)'
        matches = re.findall(pattern, enum_content)

        for prop_name, prop_id, comment in matches:
            hex_match = re.search(r'(0X[0-9A-F]+)', comment.upper())
            hex_value = hex_match.group(1) if hex_match else None
            prop_id_map[prop_name] = {
                "decimal_id": int(prop_id),
                "hex_id": hex_value,
                "comment": comment.strip()
            }
        return prop_id_map
