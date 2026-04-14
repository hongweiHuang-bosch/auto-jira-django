from __future__ import annotations
from typing import Any, Dict, List, Tuple

def gen_signal_to_info(json_data: List[Dict[str, Any]],
                       prop_id_map: Dict[str, Dict[str, Any]],
                       signals: List[str]) -> Dict[str, Dict[str, Any]]:
    signal_to_info: Dict[str, Dict[str, Any]] = {}
    signal_set = set([s for s in signals if s])
    '''
        signal_name:{
            "prop": prop_value,
            "msgname": msgname,
            "msgid": msgid,
            "propid_decimal": prop_info.get('decimal_id'),
            "propid_hex": prop_info.get('hex_id')
            "signal_direction": item.get('access')
        },
        ...
    '''
    for item in json_data:
        prop_value = item.get("prop")
        # 组
        for s in signal_set:
            if "GROUP" in s and prop_value == s:
                if "config" in item and isinstance(item["config"], list):
                    for cfg in item["config"]:
                        msgname = cfg.get("setMsgName")
                        msgid = cfg.get("setMsgId")
                        prop_info = prop_id_map.get(prop_value, {})
                        signal_to_info[s] = {
                            "prop": prop_value,
                            "msgname": msgname,
                            "msgid": msgid,
                            "propid_decimal": prop_info.get('decimal_id'),
                            "propid_hex": prop_info.get('hex_id'),
                            "signal_direction": item.get('access')
                        }
        if "config" in item and isinstance(item["config"], list):
            for cfg in item["config"]:
                # setSignals
                if "setSignals" in cfg and isinstance(cfg["setSignals"], list):
                    for s in cfg["setSignals"]:
                        if s in signal_set:
                            msgname = cfg.get("setMsgName")
                            msgid = cfg.get("setMsgId")
                            prop_info = prop_id_map.get(prop_value, {})
                            signal_to_info[s] = {
                                "prop": prop_value,
                                "msgname": msgname,
                                "msgid": msgid,
                                "propid_decimal": prop_info.get('decimal_id'),
                                "propid_hex": prop_info.get('hex_id'),
                                "signal_direction": item.get('access')
                            }
                # getSignals
                if "getSignals" in cfg and isinstance(cfg["getSignals"], list):
                    for s in cfg["getSignals"]:
                        if s in signal_set:
                            msgname = cfg.get("getMsgName")
                            msgid = cfg.get("getMsgId")
                            prop_info = prop_id_map.get(prop_value, {})
                            signal_to_info[s] = {
                                "prop": prop_value,
                                "msgname": msgname,
                                "msgid": msgid,
                                "propid_decimal": prop_info.get('decimal_id'),
                                "propid_hex": prop_info.get('hex_id'),
                                "signal_direction": item.get('access')
                            }
    return signal_to_info

def gen_propid_text(signal_to_info: Dict[str, Dict[str, Any]]) -> str:
    s = "<信号映射关系> \n"
    for sig, info in signal_to_info.items():
        if sig == info['prop']:
            s += f"信号组'{sig}'的prop是'{info['prop']}', 对应的十进制propid是'{info['propid_decimal']}',十六进制propid是'{info['propid_hex']}', 是一个'{'上报' if info['signal_direction']=='READ' else '下设'}信号'\n"
        else:
            s += f"信号'{sig}'的prop是'{info['prop']}', 对应的十进制propid是'{info['propid_decimal']}',十六进制propid是'{info['propid_hex']}', 是一个'{'上报' if info['signal_direction']=='READ' else '下设'}信号\n"
    s += "</信号映射关系> \n"
    return s

def gen_propid_decimal_list(signal_to_info: Dict[str, Dict[str, Any]]):
    propids = []
    
    for sig, info in signal_to_info.items():
        propids.append(info['propid_decimal'])
    return propids
        
def gen_propid_hex_list(signal_to_info: Dict[str, Dict[str, Any]]):
    propids = []
    for sig, info in signal_to_info.items():
        propids.append(info['propid_hex'])
    return propids

def gen_signal_to_group(json_data: List[Dict[str, Any]]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    signal_to_groups: Dict[str, List[str]] = {}
    group_to_signals: Dict[str, List[str]] = {}

    for item in json_data:
        prop_value = item.get("prop", "")
        if "GROUP" not in prop_value:
            continue
        group_signals: List[str] = []
        if "config" in item and isinstance(item["config"], list):
            for cfg in item["config"]:
                ss = cfg.get("setSignals", [])
                if isinstance(ss, list):
                    group_signals.extend(ss)
                    for s in ss:
                        signal_to_groups.setdefault(s, []).append(prop_value)
                gs = cfg.get("getSignals", [])
                if isinstance(gs, list):
                    group_signals.extend(gs)
                    for s in gs:
                        signal_to_groups.setdefault(s, []).append(prop_value)
        group_to_signals.setdefault(prop_value, []).extend(group_signals)
    return signal_to_groups, group_to_signals

def gen_group_text(signal_to_groups, group_to_signals, signals):
    s = "<信号组信息> \n"
    for sig in signals:
        if sig in group_to_signals:
            lst = group_to_signals.get(sig, [])
            s += f"信号组'{sig}'中的信号为 " + ", ".join([f"'{x}'" for x in lst]) + "\n"
        elif sig in signal_to_groups:
            groups = signal_to_groups.get(sig, [])
            s += f"信号'{sig}'出现在以下组中: " + ", ".join([f"'{x}'" for x in groups]) + "\n"
        else:
            s += f"信号'{sig}'没有信号组\n"
    s += "</信号组信息> \n"
    return s


def gen_prop_to_info(json_data: List[Dict[str, Any]],
                       prop_id_map: Dict[str, Dict[str, Any]],
                       props: List[str]) -> Dict[str, Dict[str, Any]]:
    prop_to_info: Dict[str, Dict[str, Any]] = {}
    prop_set = set([s for s in props if s])

    for item in json_data:
        prop_value = item.get("prop")
        # 组
        for s in prop_set:
            if "GROUP" in s and prop_value == s:
                if "config" in item and isinstance(item["config"], list):
                    for cfg in item["config"]:
                        msgname = cfg.get("setMsgName")
                        prop_info = prop_id_map.get(prop_value, {})
                        prop_to_info[s] = {
                            "prop": prop_value,
                            "msgname": msgname,
                            "propid_decimal": prop_info.get('decimal_id'),
                            "propid_hex": prop_info.get('hex_id')
                        }