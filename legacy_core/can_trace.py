# -*- coding: utf-8 -*-
from __future__ import annotations
import io
import os
import re
import csv
import time
import json
import datetime
import tempfile
import logging
from contextlib import contextmanager
from typing import Dict, Any, List, Tuple, Optional

import cantools
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mplcursors
import numpy as np  # 若后续需要平滑/统计可用
from can.io import BLFReader
from can.io import ASCReader
from can.io import blf
from datetime import  timezone

logger = logging.getLogger("CAN-TRACE")

# ASC 清洗（过滤远程帧/异常帧）
@contextmanager
def _maybe_sanitized_asc(path: str):
    """
    如为 .asc，则生成一个临时“清洁版”：
    - 丢弃远程帧:   ... Rx r ... / ... Tx r ...
    - 丢弃可疑列:   ... Rx R ...（避免 can_id 读成 'R'）
    - 丢弃错误帧:   ErrorFrame / Error Passive / Bus Off / Overrun
    其它格式原样透传。
    """
    if not path.lower().endswith(".asc"):
        yield path
        return

    fd, out_path = tempfile.mkstemp(suffix=".asc", prefix="asc_sanitized_")
    os.close(fd)

    drop_patterns = [
        r"\b[RT]x\s+r\b",              # 远程帧（remote）
        r"\b[RT]x\s+R\b",              # 解析器可能把 R 当 CAN ID
        r"\bErrorFrame\b",
        r"\bError\s+Passive\b",
        r"\bBus\s+Off\b",
        r"\bOverrun\b",                 
        r"\bEnd\s+Triggerblock\b",      # End Triggerblock	
    ]
    drop_re = re.compile("|".join(drop_patterns), flags=re.IGNORECASE)

    removed = 0
    kept = 0
    with io.open(path, "r", encoding="utf-8", errors="ignore") as fin, \
         io.open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            if drop_re.search(line):
                removed += 1
                continue
            kept += 1
            fout.write(line)

    logger.info(f"[ASC 清洗] {os.path.basename(path)} -> 去除 {removed} 行, 保留 {kept} 行")
    try:
        yield out_path
    finally:
        # 若想保留清洗文件用于排查，可注释下一行
        try:
            os.remove(out_path)
        except Exception:
            pass

# DBC 辅助
def get_message_send_type(msg_name: str, dbcs: List[str]) -> Tuple[Optional[str], Optional[bool]]:
    for dbc in dbcs:
        db = cantools.database.load_file(dbc, strict=False)
        try:
            msg = db.get_message_by_name(msg_name)
        except Exception:
            msg = None
            continue
        if msg is None:
            continue
        is_checksum_in = any('CheckSum' in s.name for s in msg.signals)
        is_counter_in  = any('MsgCounter' in s.name for s in msg.signals)
        return (msg.send_type, (is_checksum_in and is_counter_in))
    return (None, None)

def get_signal_initial_value(msg_name: str, dbcs: List[str], signal_name: str):
    for dbc in dbcs:
        db = cantools.database.load_file(dbc, strict=False)
        try:
            msg = db.get_message_by_name(msg_name)
        except Exception:
            msg = None
            continue
        if msg:
            for siginfo in msg.signals:
                if siginfo.name == signal_name:
                    if 'GenSigStartValue' in siginfo.dbc.attributes:
                        return siginfo.dbc.attributes['GenSigStartValue']
    return None

def get_signal_sender_and_receiver(msg_name: str, dbcs: List[str], signal_name: str) -> str:
    for dbc in dbcs:
        db = cantools.database.load_file(dbc, strict=False)
        try:
            msg = db.get_message_by_name(msg_name)
        except Exception:
            msg = None
            continue
        if not msg:
            continue
        sender = msg.senders
        for siginfo in msg.signals:
            if siginfo.name == signal_name:
                receiver = siginfo.receivers
                return f"{sender}=>{receiver}"
    return ""

def get_msg_cycle_time(msg_name: str, dbcs: List[str]) -> int:
    for dbc in dbcs:
        db = cantools.database.load_file(dbc, strict=False)
        try:
            msg = db.get_message_by_name(msg_name)
        except Exception:
            msg = None
            continue
        if msg:
            if msg.send_type in ('Periodic', 'Cyclic'):
                if (msg.cycle_time or 0) > 0:
                    return int(msg.cycle_time)
            else:
                return 0
    return 0

def get_GenSigSendType(msg_name: str, sig_name: str, dbcs: List[str]) -> str:
    for dbc in dbcs:
        db = cantools.database.load_file(dbc, strict=False)
        try:
            msg = db.get_message_by_name(msg_name)
        except Exception:
            msg = None
            continue
        if msg:
            for siginfo in msg.signals:
                if siginfo.name == sig_name:
                    if 'GenSigSendType' in siginfo.dbc.attributes:
                        sig_send_type_id = siginfo.dbc.attributes['GenSigSendType']
                        sig_send_type = siginfo.dbc.attribute_definitions['GenSigSendType']
                        return sig_send_type.choices[sig_send_type_id.value]
                    elif 'EventCommandSignal' in siginfo.dbc.attributes:
                        sig_send_type_id = siginfo.dbc.attributes['EventCommandSignal']
                        sig_send_type = siginfo.dbc.attribute_definitions['EventCommandSignal']
                        attr = sig_send_type.choices[sig_send_type_id.value]
                        return 'Triger*' if attr == 'Yes' else attr
                    else:
                        return ''
    return ''

# 解析 绘图核心
def _as_list(x) -> List[str]:
    if not x:
        return []
    return x if isinstance(x, list) else [x]

def _build_merged_database(dbc_paths: List[str]) -> cantools.database.Database:
    db = cantools.database.Database()
    for p in dbc_paths:
        try:
            db.add_dbc_file(p)
            logger.info(f"[DBC] 已载入 {p}")
        except Exception as e:
            logger.error(f"[DBC] 载入失败 {p}: {e}")
    return db

def _collect_messages_for_signals(signals: Dict[str, List[str]], dbc_paths: List[str], signals_in_msg : List[str]):
    # 这里的signals = msgnames
    db = _build_merged_database(dbc_paths)
    messages = {}
    for msg_name in signals.keys():
        try:
            # db.get_message_by_name("TBOX_3") 一定拿的是“最后被加载的那个 DBC 里的 TBOX_3”，不会是随机的。
            # 增加报文名+报文id 判断（报文名相同再判报文id）
            db_msg = db.get_message_by_name(msg_name)
            logger.warning(f"[DBC] db_msg: {db_msg}")

            # db_msg_id = db_msg.frame_id  # 报文id
            db_signals = db_msg.signals
            # logger.warning(f"[DBC] db_signals: {db_signals}")

            for db_sigs_name in db_signals:
                if db_sigs_name.name in signals_in_msg:
                    messages[msg_name] = db_msg
                    logger.warning(f"[DBC] {db_sigs_name.name} in : {signals_in_msg}")
                    break
            
        except KeyError:
            logger.warning(f"[DBC] 未找到消息: {msg_name}")
    return messages, db

def _get_ticks(messages, sigs):
    ticks = {}
    for msg_name, msg in messages.items():
        if msg is None:
            continue
        for sig in msg.signals:
            if sig.name in sigs.get(msg_name, []):
                if sig.choices:
                    y_ticks = []
                    y_labs = []
                    for key, val in sig.choices.items():
                        y_ticks.append(key)
                        y_labs.append(f"{val}:{key}")
                    key_name = f"{msg_name}({hex(msg.frame_id)}):{sig.name}"
                    ticks[key_name] = {'lable': y_labs, 'ticks': y_ticks}
    return ticks

def _push_trace_point(store: Dict[str, Any], key: str, msg_to_decode, value: Any):
    if key not in store:
        store[key] = {'x': [], 'y': []}
    # store[key]['x'].append(ts if isinstance(ts, datetime.datetime) else datetime.datetime.fromtimestamp(ts))
    store[key]['x'].append(datetime.datetime.fromtimestamp(msg_to_decode.timestamp))
    store[key]['y'].append(value)

def _decode_and_collect(messages, msg_to_decode, db, sigs, out_store: Dict[str, Any]):
    """
    根据当前帧 msg_to_decode 的 arbitration_id，在 messages 里找到对应 DBC 消息，
    用 msg_to_decode.data 解码出我们关心的信号，并把时间戳+数值落到 out_store 里。

    out_store 结构：
        {
          "MsgName:SigName": {
              "x": [datetime, ...],
              "y": [value, ...]
          },
          ...
        }
    """
    arb_id = getattr(msg_to_decode, "arbitration_id", None)
    data   = getattr(msg_to_decode, "data", None)
    # ts     = getattr(msg_to_decode, "timestamp", None)

    # 防呆：缺字段就跳过
    if arb_id is None or data is None:
        return

    for msg_name, msg in messages.items():
        if msg is None:
            continue
        if msg.frame_id != arb_id:
            continue

        try:
            decoded = db.decode_message(msg.frame_id, data, decode_choices=False)
        except Exception as e:
            logger.debug(f"[CAN] 解码消息失败 {msg_name}({hex(msg.frame_id)}): {e}")
            continue

        if not decoded:
            continue

        for sig in sigs.get(msg_name, []):
            key = f"{msg_name}:{sig}"
            _push_trace_point(out_store, key, msg_to_decode, decoded.get(sig))



def _parse_trace_core(messages, sigs, log_path, db) -> Tuple[Dict[str, Any], float]:
    suffix = os.path.splitext(log_path)[-1].lower()
    start_time = 0.0
    index = 0
    first_time_print = False
    store: Dict[str, Any] = {}

    if suffix in ('.blf',):
        with BLFReader(log_path) as reader:
            for msg in reader:
                if index == 0:
                    start_time = msg.timestamp
                    index += 1
                if not first_time_print:
                    logger.info(f"[CAN] 首帧时间: {datetime.datetime.fromtimestamp(msg.timestamp,tz=timezone.utc)}")
                    first_time_print = True
                _decode_and_collect(messages, msg, db, sigs, store)

    elif suffix in ('.asc',):
        with ASCReader(log_path, relative_timestamp=False) as reader:
            for msg in reader:
                if index == 0:
                    start_time = msg.timestamp
                    index += 1
                if not first_time_print:
                    logger.info(f"[CAN] 首帧时间: {datetime.datetime.fromtimestamp(msg.timestamp,tz=timezone.utc)}")
                    first_time_print = True
                _decode_and_collect(messages, msg, db, sigs, store)

    # elif suffix == '.csv':
    #     with open(log_path, 'r', newline='') as csvfile:
    #         reader = csv.DictReader(csvfile)
    #         for row in reader:
    #             dt_string = row['WRITE_TIME'].strip('[]')
    #             dt_obj = datetime.datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S.%f")
    #             for msg_name, msg in messages.items():
    #                 if msg is None:
    #                     continue
    #                 if msg.frame_id == int(row['MAKE_CAN_ID(HEX)'], 0):
    #                     decoded = db.decode_message(msg.frame_id, bytes.fromhex(row['DATA(HEX)']), decode_choices=False)
    #                     if decoded:
    #                         for sig in sigs[msg_name]:
    #                             key = f"{msg_name}:{sig}"
    #                             _push_trace_point(store, key, dt_obj, decoded.get(sig))
    else:
        raise ValueError(f"不支持的日志格式: {suffix}")

    return store, start_time

def get_decode_trace_data(messages, msg_to_decode, db, sigs, trace_signal_datas):
    for msg_name, msg in messages.items():
        if msg.frame_id == msg_to_decode.arbitration_id:
            can_msg_decode = db.decode_message(msg.frame_id, msg_to_decode.data, decode_choices=False)
            if len(can_msg_decode) > 0:
                for sig in sigs[msg_name]:
                    #x.append(datetime.datetime.fromtimestamp(msg_to_decode.timestamp))
                    #y.append(can_msg_decode[sig])
                    sig_plot_name = '{}:{}'.format(msg_name, sig)
                    #print(sig_plot_name)
                    #sig_plot_name = 'HVACF_1:HVACF_ACSt'
                    #print(sig_plot_name)
                    #print(datetime.datetime.fromtimestamp(msg_to_decode.timestamp))
                    #print(can_msg_decode[sig])
                    if trace_signal_datas.get(sig_plot_name) == None:
                        trace_signal_datas[sig_plot_name] = {'x':[datetime.datetime.fromtimestamp(msg_to_decode.timestamp,  tz=timezone.utc)], 'y':[can_msg_decode[sig]]}
                    else:
                        trace_data = trace_signal_datas[sig_plot_name]
                        trace_data['x'].append(datetime.datetime.fromtimestamp(msg_to_decode.timestamp, tz=timezone.utc))
                        trace_data['y'].append(can_msg_decode[sig])

            else:
                pass

def _parse_trace_with_retry(messages, sigs, log_path, db) -> Tuple[Dict[str, Any], float]:
    """
    对 .asc：
      - 先通过 _maybe_sanitized_asc 生成清洗后的临时 ASC
      - 再用 _parse_trace_core 解析（远程帧 / ErrorFrame / End Triggerblock 等都会被过滤）
    对其它格式 (.blf/.csv)：
      - 直接用 _parse_trace_core
    """
    suffix = os.path.splitext(log_path)[-1].lower()

    # 非 ASC，直接解析
    # if suffix != ".asc":
    #     return _parse_trace_core(messages, sigs, log_path, db)

    # ASC：一律先清洗再读
    # with _maybe_sanitized_asc(log_path) as cleaned:
    return _parse_trace_core(messages, sigs, log_path, db)

def _fmt_ts(t):
    # 已经是 datetime
    if isinstance(t, datetime.datetime):
        return t.isoformat(sep=" ", timespec="milliseconds")

    # 数值：猜测秒/毫秒
    if isinstance(t, (int, float)):
        # 1e12 量级通常是毫秒；1e9 量级通常是秒
        ts = t / 1000.0 if t > 1e11 else float(t)
        return datetime.datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(sep=" ", timespec="milliseconds")

    # 兜底：原样转字符串
    return str(t)

def _summarize_segments(trace_signal_datas: Dict[str, Any]) -> str:
    output_lines = ""
    for key, data in trace_signal_datas.items():
        # key: "MSG:SIG" 或 "MSG(hexid):SIG" 的绘图名会在 ticks 里带 hexid
        m = re.match(r'([^(]+)\(([^)]+)\):(.+)', key)
        signal_name = key.split(":")[-1] if not m else m.group(3)

        xs = data['x']
        ys = data['y']
        current_y = None
        current_count = 0
        current_start = None
        for i, yv in enumerate(ys):
            if current_y is None:
                current_y = yv
                current_count = 1
                current_start = xs[i]
            elif yv == current_y:
                current_count += 1
            else:
                output_lines += f"{signal_name}值为 {current_y} 持续了 {current_count} 帧，从时间 {_fmt_ts(current_start)} 到 {_fmt_ts(xs[i-1])}\n"
                current_y = yv
                current_count = 1
                current_start = xs[i]
        if current_y is not None:
            output_lines += f"{signal_name}值为 {current_y} 持续了 {current_count} 帧，从时间 {_fmt_ts(current_start)} 到结束\n"
    return output_lines

def _summarize_missing_signals(trace_signal_datas: Dict[str, Any], sigs: Dict[str, List[str]]) -> str:
    miss_signal_lines = ""
    str_trace_data = str(trace_signal_datas)
    for message, sig_list in sigs.items():
        if message not in str_trace_data:
            miss_signal_lines += f"报文{message} 不在CAN trace中，且其信号："
            for sig in sig_list:
                miss_signal_lines += f"{sig}, "
            miss_signal_lines += "也不在 CAN trace中\n"
    return miss_signal_lines

def _subplot_data(trace_signal_datas: Dict[str, Any], ticks, logfile: str, start_time: float, sigs: Dict[str, List[str]] = {}) -> Tuple[str, str]:
    matplotlib.rc("font", family='MicroSoft YaHei', weight="bold")

    # 保存路径同名 .png
    logfile_dir = os.path.dirname(logfile)
    logfile_basename = os.path.basename(logfile)
    logfile_name_without_ext = os.path.splitext(logfile_basename)[0]
    save_path = os.path.join(logfile_dir, f"{logfile_name_without_ext}.png")

    if len(trace_signal_datas) == 0:
        return "", save_path

    # 统计摘要
    output_lines = _summarize_segments(trace_signal_datas)
    # 统计没有的信号
    miss_signal_comment = _summarize_missing_signals(trace_signal_datas, sigs)
    output_lines += miss_signal_comment

    # 单信号：沿用单图风格
    print(f"信号图风格： {len(trace_signal_datas)} 个信号")
    if len(trace_signal_datas) == 1:
        _plot_single(trace_signal_datas, start_time, in_ticks=ticks, in_logfile=logfile)
        mplcursors.cursor(hover=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        return output_lines, save_path

    # 多信号子图
    if start_time > 1.0:
        # can_trace_start_time = 'Start Time:{}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)))
        local_time = time.localtime(start_time)
        can_trace_start_time = 'Start Time:{}'.format(time.strftime("%Y-%m-%d %H:%M:%S", local_time))
    else:
        # 任取一个
        # first_key = next(iter(trace_signal_datas))
        # can_trace_start_time = 'Start Time:{}'.format(trace_signal_datas[first_key]['x'][0].strftime("%Y-%m-%d %H:%M:%S"))
        for name, data in trace_signal_datas.items():
            can_trace_start_time = 'Start Time:{}'.format(data['x'][0].strftime("%Y-%m-%d %H:%M:%S"))
            break
    fig, axs = plt.subplots(len(trace_signal_datas), sharex=True)
    title = logfile_basename
    fig.suptitle(title)

    colors = ['r','g','b','c','m','y','k']
    for idx, (name, data) in enumerate(trace_signal_datas.items()):
        line_style = f"*--{colors[idx % len(colors)]}"
        axs[idx].plot(data['x'], data['y'], line_style, label=f"{name}({len(data['x'])})")
        axs[idx].legend(loc="best")
        axs[idx].grid()

        if ticks:
            plot_ticks = ticks.get(name)
            if plot_ticks:
                axs[idx].set_yticks(plot_ticks['ticks'])
                axs[idx].set_yticklabels(plot_ticks['lable'])

    plt.xlabel(can_trace_start_time)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return output_lines, save_path

def _plot_single(trace_signal_datas, start_time, in_ticks=None, in_logfile=None):
    fig = plt.figure()
    ax = plt.axes()
    colors = ['r','g','b','c','m','y','k']
    idx = 0

    for name, data in trace_signal_datas.items():
        if start_time > 1.0:
            can_trace_start_time = 'Start Time:{}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)))
        else:
            can_trace_start_time = 'Start Time:{}'.format(data['x'][0].strftime("%Y-%m-%d %H:%M:%S"))

        line_style = f"*--{colors[idx % len(colors)]}"
        idx += 1
        plt.plot(data['x'], data['y'], line_style, label=f"{name}({len(data['x'])})")

        if (in_ticks is not None) and (len(in_ticks) != 0):
            plot_ticks = in_ticks.get(name)
            if plot_ticks:
                ax.set_yticks(plot_ticks['ticks'])
                ax.set_yticklabels(plot_ticks['lable'])
            ax.grid()

        if in_logfile:
            plt.title(os.path.basename(in_logfile))

    plt.gcf().autofmt_xdate()
    plt.legend(loc="best")
    plt.xlabel(can_trace_start_time)
    plt.ylabel("Value")
    fig.set_label('CAN Trace')

# 对外主入口
def plot_signals(signals:List[str],
                signal_to_info: Dict[str, Dict[str, Any]],
                 dbc_paths: List[str] | str,
                 log_path: str) -> Tuple[str, str]:
    """
    输入:
      - signal_to_info: {signal: {prop,msgname,propid_decimal,propid_hex}}
      - dbc_paths: str 或 [str,...]
      - log_path: .asc / .blf / .csv
    返回:
      - can_trace_outputs: 时序段摘要（中文）
      - can_trace_path:    生成的图片路径（与 log 同名 .png）
    """
    logger.info(f"[plot_signals] ")

    # 无信号直接返回
    if not signal_to_info:
        return "", ""
    dbc_list = _as_list(dbc_paths)
    logger.info(f"[plot_signals:dbc_list] {str(dbc_list)} ")

    # 1) 抽取参与解码的信号: 按 msgname 聚集
    sigs: Dict[str, List[str]] = {}
    for signal, info in signal_to_info.items():
        if "GROUP" in signal:
            continue
        msgname = info.get('msgname')
        if not msgname:
            continue
        sigs.setdefault(msgname, []).append(signal)
    # 没有任何有效 msgname，直接返回
    if not sigs:
        return "", ""
    
    # msgname_map_msgid : Dict[str, str] = {}
    # for signal, info in signal_to_info.items():
    #     msgname_map_msgid[info.get("msgname")] = info.get("msgid")

    # 2) 多路dbc处理 合并 dbc 收集消息 
    print("_collect_messages_for_signals")
    messages, db = _collect_messages_for_signals(sigs, dbc_list, signals)

    # 3) 选择枚举 tick
    print("_get_ticks")
    ticks = _get_ticks(messages, sigs)

    # 4) 解析 CAN Trace（含 ASC 清洗重试）
    print("_parse_trace_with_retry")
    trace_datas, start_time = _parse_trace_with_retry(messages, sigs, log_path, db)
    logger.info(f"[start_time] {str(start_time)} ")
    print(f"[start_time] {str(start_time)} ")
    
    # with open("./trace.txt", "w", encoding="utf-8") as f:
    #     if isinstance(trace_datas, str):
    #         f.write(trace_datas)
    #     elif isinstance(trace_datas, (list, tuple)):
    #         for item in trace_datas:
    #             f.write(f"{item}\n" + f"sigs: {sigs}\n")
    #     else:
    #         f.write(str(trace_datas))
    
    # with open("./signals.txt", "w", encoding="utf-8") as f:
    #     f.write(str(sigs) + " \n messages " + str(messages))

    # 5) 绘图 + 汇总
    print("_subplot_data")
    can_trace_outputs, can_trace_path = _subplot_data(trace_datas, ticks, log_path, start_time, sigs)
    return can_trace_outputs, can_trace_path



if __name__ == "__main__":
    # 1. 要画哪些信号 + 一些辅助信息（根据你自己函数内部实际需要调整字段）
    signal_to_info: Dict[str, Dict[str, Any]] = {
        # 信号名要和 DBC 里一致
        "RRCR_1_SysSt": {
            "msgname": "RRCR_1",   # 所在报文名（示例）
            "propid_decimal": "557850762",
            "propid_hex": "0x2140208a",
        },
        "RLCR_1_SysSt": {
            "msgname": "RLCR_1",
            "propid_decimal": "557850759",
            "propid_hex": "0x21402087",
        }
    }

    # 2. DBC 文件路径（可以是 list，也可以是 str）
    dbc_paths: List[str] = [
        "../../../config——chery/8255/car_D01.dbc",
        # 如果你有多个 DBC，可以继续加
        # "dbc/car_T1J_FL2_8255.dbc",
    ]
    signals = ["RRCR_1_SysSt", "RLCR_1_SysSt"]
    # 3. CAN 日志路径（asc/blf/dbc 都行，看你函数支持什么）
    log_path: str = "./../comment/D01P/DPINT-2941/can.asc"

    # 4. 调用函数
    out_fig_path, out_data_path = plot_signals(
        signals,
        signal_to_info=signal_to_info,
        dbc_paths=dbc_paths,
        log_path=log_path,
    )

    print("figure saved to:", out_fig_path)
    print("data   saved to:", out_data_path)
