# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
from .log_package_helper import process_zip_packages_for_pipeline

from .ai_client_by_langchain import AIClient, EXTRACT_SIGNALS_SYSTEM, LOG_SUMMARY_SYSTEM, CONSISTENCY_SYSTEM, COMPARE_CANTRACE, ANDROID_QNX_LOG_SUMMARY_SYSTEM, REQUIREMENT_EXTRACT_SYSTEM
from .jira_utils import JiraClient, get_jira_comments, download_all_need_attachment, download_latest_png
from .signal_mapping import (
    gen_signal_to_info, gen_propid_text,
    gen_signal_to_group, gen_group_text,
    gen_propid_decimal_list, gen_propid_hex_list
)
from .can_trace import plot_signals
from .utils import write_model_issue_text_file
from .proto_utils import ProtoParser
from datetime import datetime
from .config_map import max_tokens
from .transfer_json import transfer_json_to_txt

logger = logging.getLogger("CAN-AI-JIRA")
_PROCESSED_FILE = Path("processed_issues.json")
_PROJECT_ROOT = Path(__file__).resolve().parents[1]

import tkinter as tk
from tkinter import scrolledtext


def load_processed_issues() -> set[str]:
    if _PROCESSED_FILE.exists():
        try:
            return set(json.loads(_PROCESSED_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_processed_issues(keys: set[str]):
    _PROCESSED_FILE.write_text(
        json.dumps(sorted(keys), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def ask_submit_to_jira(issue_key: str, summary: str, reply: str) -> bool:
    """
    弹窗询问是否将 reply 提交到 Jira 评论
    - 优先使用 Tk 自定义弹窗（可滚动查看完整内容）
    - 无 GUI 环境则回退到命令行 [y/n] 询问
    """
    msg = (
        f"票 {issue_key} 处理完成。\n"
        f"标题: {summary}\n\n"
        f"解票结果:\n{reply}\n"
    )

    # 1) 优先使用 Tk 自定义弹窗（带滚动条）
    try:
        result = {"ok": False}

        def _on_yes():
            result["ok"] = True
            root.destroy()

        def _on_no():
            result["ok"] = False
            root.destroy()

        root = tk.Tk()
        root.title("CAN-AI-JIRA - 解票结果确认")
        # 置顶、防止弹在后面看不到
        root.attributes("-topmost", True)
        # 给一个相对大一点的默认大小，方便阅读
        root.geometry("900x600")  # 宽 x 高，可根据屏幕调整
        # 允许调整窗口大小
        root.resizable(True, True)

        # 上方简单说明
        label = tk.Label(
            root,
            text=f"票 {issue_key} 处理完成，是否将以下内容提交到 Jira 评论？",
            anchor="w",
            justify="left"
        )
        label.pack(fill="x", padx=10, pady=10)

        # 中间：带滚动条的文本框，展示完整解票结果
        text = scrolledtext.ScrolledText(root, wrap="word")
        text.insert("1.0", msg)
        text.configure(state="disabled")  # 只读
        text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 底部按钮
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=10, pady=10)

        btn_yes = tk.Button(btn_frame, text="提交到 Jira", width=12, command=_on_yes)
        btn_yes.pack(side="left", padx=5)

        btn_no = tk.Button(btn_frame, text="取消", width=12, command=_on_no)
        btn_no.pack(side="right", padx=5)

        # 进入事件循环，等待用户选择
        root.mainloop()
        return bool(result["ok"])

    except Exception:
        # GUI 失败（比如无显示环境）则回退到命令行模式
        pass

    # 2) 无 GUI 环境 fallback：命令行交互
    cli_msg = (
        f"票 {issue_key} 处理完成。\n"
        f"标题: {summary}\n\n"
        f"解票结果:\n{reply}\n\n"
        f"是否提交到 Jira 评论？ [y/n]: "
    )
    while True:
        ans = input(cli_msg).strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("请输入 y/n 或 yes/no。")

def ask_true_or_false(issue_key: str)->bool:
    msg = (
        f"票 {issue_key}  ai处理结果是正确？\n"
    )

    # 1) 优先弹窗sour 
    try:
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        ok = messagebox.askyesno("CAN-AI-JIRA", msg)
        root.destroy()
        return bool(ok)
    except Exception:
        pass
    except Exception:
        return False


    # 2) 无 GUI 环境 fallback
    while True:
        ans = input(f"{msg} [y/n]: ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False

# ------------------------- JSON/Proto 索引与分类 -------------------------
def _merge_json_list(json_paths: List[str]) -> Any:
    """合并多个 JSON 文件；list 追加、dict 覆盖；其余用后者覆盖。"""
    merged = None
    for jp in json_paths or []:
        if not jp or not os.path.exists(jp):
            logger.error(f"JSON 不存在: {jp}")
            continue
        try:
            with open(jp, "r", encoding="utf-8") as f:
                data = json.load(f)
            if merged is None:
                merged = data
            else:
                if isinstance(merged, list) and isinstance(data, list):
                    merged.extend(data)
                elif isinstance(merged, dict) and isinstance(data, dict):
                    merged.update(data)
                else:
                    logger.warning(f"JSON 合并类型不一致，已用后者覆盖: {jp}")
                    merged = data
            logger.info(f"已载入 JSON: {jp}")
        except Exception as e:
            logger.error(f"读取 JSON 失败({jp}): {e}")
    return merged if merged is not None else []

def _join_dir_and_files(base_dir: str, files: Any) -> List[str]:
    """files 可为 str 或 list[str]；返回拼接后的路径列表"""
    if not files:
        return []
    names = files if isinstance(files, list) else [files]
    base_path = Path(base_dir)
    parts = base_path.parts
    if "config——chery" in parts:
        config_index = parts.index("config——chery")
        base_path = _PROJECT_ROOT.joinpath(*parts[config_index:])
    return [str(base_path / name) for name in names]

def extract_min_max_time_from_comments(comments_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    从 comments_text 中提取最小和最大时间点。
    时间格式固定为：YYYY-MM-DD HH:MM:SS，例如 2023-01-01 00:03:00

    返回：
        (min_time_str, max_time_str)
        若未找到任何时间，则返回 (None, None)
    """
    TIME_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
    matches = TIME_PATTERN.findall(comments_text)
    if not matches:
        return None, None

    times = []
    for t in matches:
        try:
            dt = datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
            times.append(dt)
        except ValueError:
            # 理论上不会进这里，格式匹配得很严格
            continue

    if not times:
        return None, None

    min_dt = min(times)
    max_dt = max(times)

    return min_dt.strftime("%Y-%m-%d %H:%M:%S"), max_dt.strftime("%Y-%m-%d %H:%M:%S")
def analysize_signal_mapping(json_data, first_match_signals):
    json_mapping = json_data
    upper_signals = {str(sig).upper() for sig in (first_match_signals or []) if sig}
    result: List[str] = []
    seen = set()

    def append_signal(signal_name: str):
        if signal_name and signal_name not in seen:
            seen.add(signal_name)
            result.append(signal_name)

    for item in json_mapping:
        prop_value = str(item.get("prop") or "")
        configs = item.get("config") or []

        if prop_value.upper() in upper_signals:
            for cfg in configs:
                for signal_name in cfg.get("setSignals") or []:
                    append_signal(signal_name)
                for signal_name in cfg.get("getSignals") or []:
                    append_signal(signal_name)

        for cfg in configs:
            for signal_name in cfg.get("setSignals") or []:
                if signal_name.upper() in upper_signals:
                    append_signal(signal_name)
            for signal_name in cfg.get("getSignals") or []:
                if signal_name.upper() in upper_signals:
                    append_signal(signal_name)
    return result

# ------------------------------- Pipeline -------------------------------
class Pipeline:
    def __init__(self,
                 jira: JiraClient,
                 ai: AIClient,
                 custom_field_name: str,
                 paths_cfg: Dict[str, Any]):
        self.jira = jira
        self.ai = ai
        self.paths_cfg = paths_cfg
        self.custom_field_name = custom_field_name
        self.processed_issues = load_processed_issues()
        # 缓存
        self._proto_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}   # proto_path -> prop_map
        self._json_cache: Dict[Tuple[str, ...], Any] = {}               # (json_paths...) -> merged_json

    # ---------- 进度钩子（子类可覆写） ----------
    def _update_progress(self, stage: str, progress: int, message: str = ''):
        """子类覆写此方法以实时上报处理进度。默认空实现。"""
        pass

    # ---------- 缓存加载 ----------
    def _get_prop_map(self, proto_path: Optional[str]) -> Dict[str, Dict[str, Any]]:
        if not proto_path or not os.path.exists(proto_path) or not proto_path.endswith(".proto"):
            return {}
        if proto_path in self._proto_cache:
            return self._proto_cache[proto_path]
        try:
            with open(proto_path, "r", encoding="utf-8") as f:
                content = f.read()
            prop_map = ProtoParser.parse_property_ids(content) or {}
            self._proto_cache[proto_path] = prop_map
            logger.info(f"解析 proto 成功: {proto_path} -> {len(prop_map)} 条")
            return prop_map
        except Exception as e:
            logger.error(f"解析 proto 失败({proto_path}): {e}")
            return {}

    def _get_json_merged(self, json_paths: List[str]) -> Any:
        key = tuple(json_paths)
        if key in self._json_cache:
            return self._json_cache[key]
        merged = _merge_json_list(json_paths)
        self._json_cache[key] = merged
        return merged

    # DBC 绘图 
    def _plot_with_multi_dbc(self, signals: List[str], signal_to_info: Dict[str, Any],
                             dbc_paths: List[str], log_path: str):
        """兼容你的 can_trace.plot_signals：优先尝试列表；不行则逐个回退。"""
        try:
            logger.info("plot_signals(signal_to_info, dbc_paths, log_path)")
            return plot_signals(signals,signal_to_info, dbc_paths, log_path)  # 列表
        except TypeError:
            logger.info("_plot_with_multi_dbc TypeError ")
            # return "", ""
        last_exc: Optional[Exception] = None
        for dbc in dbc_paths:
            try:
                logger.info("plot_signals(signal_to_info, dbc, log_path)")
                return plot_signals(signals,signal_to_info, dbc, log_path)    # 单个
            except Exception as e:
                last_exc = e
                logger.warning(f"plot_signals 失败，尝试下一个 DBC：{dbc}，原因：{e}")
        if last_exc:
            raise last_exc
        return "", ""

    # ---------- 根据车型映射到文件路径 ----------
    def _resolve_paths_by_model(self,
                                model: Optional[str],
                                base_paths: Dict[str, str],
                                model_to_files: Dict[str, Dict[str, Any]],
                                fallback_files: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        json_dir = base_paths["json_dir"]
        dbc_dir  = base_paths["dbc_dir"]
        proto_dir= base_paths["proto_dir"]

        files = None
        if model and model in model_to_files:
            files = model_to_files[model]
            logger.info(f"命中车型映射: {model}")
        else:
            logger.warning(f"车型未映射或为空: {model}，使用 fallback_files")
            files = fallback_files or {}
            return None

        json_paths  = _join_dir_and_files(json_dir,  files.get("json"))  if files.get("json")  else []
        dbc_paths   = _join_dir_and_files(dbc_dir,   files.get("dbc"))   if files.get("dbc")   else []
        proto_paths = _join_dir_and_files(proto_dir, files.get("proto")) if files.get("proto") else []

        proto_path = proto_paths[0] if proto_paths else None
        return {"json_paths": json_paths, "dbc_paths": dbc_paths, "proto_path": proto_path}
    
    def save_true_or_false(self, issue_key):
        if ask_true_or_false(issue_key):
            logger.info(f"[{issue_key}] 用户选择true，即本次给出的结果是正确的")
            with open("cal_True.txt", "a", encoding="utf-8") as f:
                f.write(f"\n{issue_key}: 结果正确")
        else:
            logger.info(f"[{issue_key}] 用户选择false，即本次给出的结果是错误的")
            with open("cal_False.txt", "a", encoding="utf-8") as f:
                f.write(f"\n{issue_key}: 结果错误")
    # 每张处理完的票 都要执行的人工流程
    def _finalize_issue(
        self,
        issue_key: str,
        summary: str,
        reply_text: str,
        can_img_path: str,
        can_trace_outputs: str = '',
        upper_comment: str = '',
    ):
        """
        每张票处理完的统一出口：
        - 弹窗展示结果
        - 询问是否回填 Jira
        - 回填则记录到 processed_issues 并持久化
        """
        if ask_submit_to_jira(issue_key, summary, reply_text):
            try:
                if can_img_path == "":
                    self.jira.add_comment(issue_key, reply_text)  # JiraClient 已有:contentReference[oaicite:3]{index=3}
                else:
                    self.jira.add_comment_with_image(issue_key, reply_text, can_img_path) 
                self.processed_issues.add(issue_key)
                save_processed_issues(self.processed_issues)
                logger.info(f"[{issue_key}] 已提交评论并加入过滤列表")
            except Exception as e:
                logger.error(f"[{issue_key}] 提交 Jira 评论失败: {e}")
        else:
            logger.info(f"[{issue_key}] 用户选择不回填，保留待下次处理")

    def get_android_log(self, results : Dict[Path, Dict[str, Dict[str, Optional[Path]]]]):
        parts: list[str] = []
        for unzip_root, out_map in results.items():
            android_files = out_map.get("android", {})
            for kw, path in android_files.items():
                if not path:
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception as e:
                    logger.warning(f"读取 Android 日志失败: {path}, {e}")
                    continue
                parts.append(f"{text.rstrip()}\n")
        return parts
    
    def get_qnx_log(self, results : Dict[Path, Dict[str, Dict[str, Optional[Path]]]]):
        parts: list[str] = []
        for unzip_root, out_map in results.items():
            qnx_files = out_map.get("qnx", {})
                # 汇总 qnx 日志
            for kw, path in qnx_files.items():
                if not path:
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception as e:
                    logger.warning(f"读取 qnx 日志失败: {path}, {e}")
                    continue

                    # f"\n===== QNX_LOG [{unzip_root.name}] KEY={kw} FILE={path.name} =====\n"
                parts.append(
                    f"{text.rstrip()}\n"
                )
        return parts

    def get_latest_cantrace_path_str(self, root_dir: Path) -> Optional[str]:
        """
        在 root_dir 下递归查找 .asc/.blf，返回修改时间最新的一个文件路径（str）。
        若不存在则返回 None。
        """
        root_dir = Path(root_dir)
        if not root_dir.exists() or not root_dir.is_dir():
            return None

        latest_path: Optional[Path] = None
        latest_mtime: float = -1.0

        # 递归扫描
        for p in root_dir.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in (".asc", ".blf"):
                continue

            try:
                mt = p.stat().st_mtime
            except Exception:
                continue

            if mt > latest_mtime:
                latest_mtime = mt
                latest_path = p

        return str(latest_path) if latest_path else None
    
    # --------------------------- 主流程（批量） ---------------------------
    def run_batch_with_model_map(self,
                                 jql: str,
                                 expand: str,
                                 base_paths: Dict[str, str],
                                 model_to_files: Dict[str, Dict[str, Any]],
                                 fallback_files: Optional[Dict[str, Any]] = None,
                                 extract_prompt: Optional[str] = None,
                                 summary_prompt: Optional[str] = None,
                                 compare_prompt: Optional[str] = None,
                                 android_qnx_summary_prompt: Optional[str] = None,
                                 requirement_extract_prompt: Optional[str] = None,
                                 consistency_prompt: Optional[str] = None):
        """
        - 以 JQL 批量检索票
        - 票题【车型】→ 拼接 json/dbc/proto
        - AI 提取 tokens（可能是信号或 prop）
        - 基于规则与 JSON 索引判断缺失项；缺失则短路并生成话术
        - 正常流程：上层摘要→解析 CAN→一致性→生成话术
        """
        p_extract = (extract_prompt or EXTRACT_SIGNALS_SYSTEM)
        p_summary = (summary_prompt or LOG_SUMMARY_SYSTEM)
        p_cons    = (consistency_prompt or CONSISTENCY_SYSTEM)
        aq_summary= (android_qnx_summary_prompt or ANDROID_QNX_LOG_SUMMARY_SYSTEM)
        c_compare = (compare_prompt or COMPARE_CANTRACE)
        requirement_extract = (requirement_extract_prompt or REQUIREMENT_EXTRACT_SYSTEM)

        # 基础目录检查
        for key in ("json_dir", "dbc_dir", "proto_dir"):
            if key not in base_paths:
                raise ValueError(f"base_paths 缺少字段: {key}")
            if not os.path.isdir(base_paths[key]):
                logger.warning(f"目录不存在: {key}={base_paths[key]}")

        issues = self.jira.search_issues(jql, expand=expand)
        logger.info(f"共检索到 {len(issues)} 张票")

        for issue in issues:
            self.process_issue_with_model_map(
                issue,
                base_paths=base_paths,
                model_to_files=model_to_files,
                fallback_files=fallback_files,
                extract_prompt=extract_prompt,
                summary_prompt=summary_prompt,
                compare_prompt=compare_prompt,
                android_qnx_summary_prompt=android_qnx_summary_prompt,
                requirement_extract_prompt=requirement_extract_prompt,
                consistency_prompt=consistency_prompt,
            )

    def process_issue_with_model_map(self,
                                     issue,
                                     base_paths: Dict[str, str],
                                     model_to_files: Dict[str, Dict[str, Any]],
                                     fallback_files: Optional[Dict[str, Any]] = None,
                                     extract_prompt: Optional[str] = None,
                                     summary_prompt: Optional[str] = None,
                                     compare_prompt: Optional[str] = None,
                                     android_qnx_summary_prompt: Optional[str] = None,
                                     requirement_extract_prompt: Optional[str] = None,
                                     consistency_prompt: Optional[str] = None):
        """单票处理入口 — 从 run_batch_with_model_map 的 for 循环体提炼而来。"""
        p_extract = (extract_prompt or EXTRACT_SIGNALS_SYSTEM)
        p_summary = (summary_prompt or LOG_SUMMARY_SYSTEM)
        p_cons    = (consistency_prompt or CONSISTENCY_SYSTEM)
        aq_summary= (android_qnx_summary_prompt or ANDROID_QNX_LOG_SUMMARY_SYSTEM)
        c_compare = (compare_prompt or COMPARE_CANTRACE)
        requirement_extract = (requirement_extract_prompt or REQUIREMENT_EXTRACT_SYSTEM)

        # 基础目录检查
        for key in ("json_dir", "dbc_dir", "proto_dir"):
            if key not in base_paths:
                raise ValueError(f"base_paths 缺少字段: {key}")

        models_list = list(model_to_files.keys())

        issue_key = getattr(issue, "key", str(issue))
        summary   = getattr(getattr(issue, "fields", None), "summary", "") or ""

        # 过滤提交过评论的票
        if issue_key in self.processed_issues:
            logger.info(f"[{issue_key}] 已回填过评论，跳过")
            return
        model = ""
        for m in models_list:
            if m in summary:
                model = m
        # model     = _extract_model_from_summary(summary)
        # if model is None:
        #     model = _extract_model_from_summary_min(summary)
            
        model_str = str(model)
        if "国际" in str(model):
            model_str = f"{str(model).replace('国际','-')}"

        if "国内" in str(model):
            model_str = f"{str(model).replace('国内','guonei')}"
        
        if "华为" in str(model):
            model_str = f"{str(model).replace('华为','huawei')}"
        if "右舵" in str(model):
            model_str = f"{str(model).replace('右舵','right')}"

        s_download_dir = f"comment/{model_str}/{issue}"
        download_dir = os.path.join(os.getcwd(), s_download_dir)
        os.makedirs(download_dir, exist_ok=True)

        logger.info("=" * 100)
        logger.info(f"!!!--- [{issue_key}] 处理 {issue_key}  车型: {model}  标题: {summary} ---!!!")

        # 1) 车型 文件路径
        self._update_progress('PREPARING', 5, f'{issue_key} 正在解析车型配置')
        paths = self._resolve_paths_by_model(model, base_paths, model_to_files, fallback_files)
        if paths is None:
            logger.error(f"{issue_key} 车型映射为空")
            return
        json_paths = paths["json_paths"]
        dbc_paths  = paths["dbc_paths"]
        proto_path = paths["proto_path"]

        if not json_paths or not dbc_paths:
            logger.error(f"{issue_key} 无法确定 json/dbc 路径，跳过。json={json_paths} dbc={dbc_paths}")
            write_model_issue_text_file(f"{model_str}", f"{issue_key}_reply.txt", f"{issue_key}", "无法确定 json/dbc 路径，跳过")
            return

        # 2) 载入 JSON / 解析 proto（带缓存）
        json_data   = self._get_json_merged(json_paths)
        prop_id_map = self._get_prop_map(proto_path)

        # 3) 下载票中的附件
        self._update_progress('DOWNLOADING', 15, f'{issue_key} 正在下载附件')
        download_result = download_all_need_attachment(issue, s_download_dir)
        if download_result is None:
            write_model_issue_text_file(f"{model_str}", f"{issue_key}_reply.txt", f"{issue_key}", "附件下载异常，请手动处理\n ")
            logger.warning(f"[{issue_key}] 附件下载异常，请手动处理")
            self._finalize_issue(issue_key, summary, "\n 车控车设问题分析需要CAN trace，请复测并提取问题发生时的Android log, QNX log, CAN trace，依次从应用->Framework再转给VHAL分析，谢谢", "")
            return
        
        # 打回
        if download_result["mode"] == "reject":
            write_model_issue_text_file(f"{model_str}", f"{issue_key}_reply.txt", f"{issue_key}", f"{download_result['reason']}")
            logger.warning(f"[{issue_key}] : {download_result['reason']}")
            # self._finalize_issue(issue_key, summary, f"{download_result['reason']}", "")
            self._finalize_issue(issue_key, summary, f"{download_result['reason']}", "")
            self.save_true_or_false(issue_key)
            return
        else:
            # both & can & can_in_log
            # 4) 上层描述
            comments_text = get_jira_comments(issue)
            write_model_issue_text_file(f"{model_str}", f"{issue_key}_comments.txt", f"{issue_key}", comments_text)
            if len(comments_text) > max_tokens * 2:
                logger.warning(f"[{issue_key}] 评论文本超出模型范围，建议手动处理")
                return


            # 4.1) 上层需求
            self._update_progress('PARSING', 25, f'{issue_key} AI 提取需求')
            ai_extract_requirement  = self.ai.chat_by_langchain(requirement_extract, comments_text)
            logger.info(f"[{issue_key}] 提取需求结果:\n{ai_extract_requirement}\n" + "-" * 80)
            if (not ai_extract_requirement):
                logger.warning(f"[{issue_key}] 未解析需求，继续分析")
            

            # 5) AI 提取条目（可能是信号或 prop）
            # ai_extract = self.ai.chat_by_langchain(p_extract, comments_text)
            # logger.info(f"[{issue_key}] 提取信号结果:\n{ai_extract}\n" + "-" * 80)


            if isinstance(json_paths, list):
                    # 多个路径
                for json_path in json_paths:
                    txt_path = str(Path(json_path).with_suffix(".txt"))
                    transfer_json_to_txt(json_path, txt_path)
            else:
                # 单个字符串路径
                json_path = json_paths
                txt_path = str(Path(json_path).with_suffix(".txt"))
                transfer_json_to_txt(json_path, txt_path)

            # 添加提示词
            query = (
                f"<车型>{model}</车型>"
                f"<标题>{summary}</标题>"
                f"{p_extract}"
                f"\n{comments_text}"
            )
            self._update_progress('PARSING', 35, f'{issue_key} AI 提取信号')

            query_signal_nums = (
                "请提取与车控车设相关的信号的个数，没有信号就返回0，有信号只返回个数，不要返回其他任何无关内容\n"
            )
            signal_nums = self.ai.chat_by_langchain(query_signal_nums, comments_text + ai_extract_requirement)
            logger.info(f"[{issue_key}] signal_nums:\n{signal_nums}\n" + "-" * 80)

            ai_extract = self.ai.query_signal_by_rag(query, txt_path, signal_nums)
            
            if not ai_extract:
                # 没提取到
                logger.info(f"[{issue_key}] 没提取到:\n{ai_extract}\n" + "-" * 80)
                return
            if isinstance(ai_extract, str) and ai_extract.strip() in ("无法提取", ""):
                # 模型明确告诉“无法提取”
                logger.info(f"[{issue_key}] 无法提取:\n{ai_extract}\n" + "-" * 80)
                return
            logger.info(f"[{issue_key}] 原始提取结果:ai_extract: {ai_extract}\n " + "-" * 80)
            
            #  成功提取到配置 JSON，直接用
            first_match_signals = ai_extract.get("signals")
            analysis = ai_extract.get("analysis", [])
            logger.info(f"[{issue_key}] 原始提取信号/prop: {first_match_signals}\n analysis:\n{analysis}\n" + "-" * 80)
            write_model_issue_text_file(f"{model_str}", f"{issue_key}_signals.txt", f"{issue_key}", str(first_match_signals))

            signals = analysize_signal_mapping(json_data, first_match_signals)
            logger.info(f"[{issue_key}] 归一化后的配置信号: {signals}\n " + "-" * 80)

            '''
                <信号映射关系> 
                信号'CEM_IPM_FrontBlowSpdCtrlsts'的prop是'HVAC_VENDOR_FAN_SPEED_READ', 对应的十进制propid是'557843978',十六进制propid是'0X2140060A'
                信号'IHU_5_BlowSpeedLevel_Req'的prop是'IHU_5_GROUP', 对应的十进制propid是'557909562',十六进制propid是'0X2141063A'
                信号'CEM_IPM_FrontOFFSts'的prop是'HVAC_VENDOR_POWER_STATUS_READ', 对应的十进制propid是'557843968',十六进制propid是'0X21400600'
                信号'IHU_5_FrontOFF_Req'的prop是'IHU_5_GROUP', 对应的十进制propid是'557909562',十六进制propid是'0X2141063A'
                </信号映射关系> 
                <信号组信息> 
                信号'IHU_5_BlowSpeedLevel_Req'出现在以下组中: 'IHU_5_GROUP'
                信号'CEM_IPM_FrontBlowSpdCtrlsts'没有信号组
                信号'IHU_5_FrontOFF_Req'出现在以下组中: 'IHU_5_GROUP'
                信号'CEM_IPM_FrontOFFSts'没有信号组
                </信号组信息>
            '''
            signal_to_info = gen_signal_to_info(json_data, prop_id_map, signals)
            propid_text = gen_propid_text(signal_to_info)
            signal_to_groups, group_to_signals = gen_signal_to_group(json_data)
            group_text = gen_group_text(signal_to_groups, group_to_signals, signals)

            # 7) both 情况
            # 如果有png 添加png comment
            ai_res = ""
            cantrace_path = ""
            can_trace_outputs = ""
            if download_result["mode"] == "both" or download_result["mode"] == "can_in_zip":
                # 下载 最近的一张png图片，作为comment的最后
                png_path = download_latest_png(issue, download_dir = s_download_dir, self_uploader_id = self.jira.username)
                if not png_path:
                    logger.info("没有png文件，上层没有贴图评论")
                else:
                    png_comment = str(self.ai.read_img(png_path))
                    comments_text = comments_text + png_comment
                    logger.warning(f"[{issue_key}] 图片识别日志：{png_comment}")

                bundle = comments_text + propid_text + group_text
                write_model_issue_text_file(f"{model_str}", f"{issue_key}_upper_bundle.txt", f"{issue_key}", bundle)
                if len(bundle) > max_tokens * 2:
                    logger.warning(f"[{issue_key}] 评论文本+信号内容超出模型范围，建议手动处理")
                    return

                # 8）both 要摘取上层日志
                ai_summary = self.ai.chat_by_langchain(p_summary, bundle)
                write_model_issue_text_file(f"{model_str}", f"{issue_key}_upper_summary.txt", f"{issue_key}", ai_summary)
                logger.info("-" * 80)
                logger.info(f"[{issue_key}] 上层日志摘要:\n{ai_summary}")
                logger.info("-" * 80)

                # 9） both 获取qnx和android日志
                # android_qnx_log 已经下载解压，需要取提取，时间点，关键字
                android_qnx_log = ""
                android_log = ""
                qnx_log = ""
                min_t, max_t = extract_min_max_time_from_comments(comments_text)
                # 使用默认最小时间和当前最大时间
                if min_t is None:
                    min_dt = datetime(1970, 1, 1, 0, 0, 0)
                    min_t = min_dt.strftime("%Y-%m-%d %H:%M:%S")
                if max_t is None:
                    max_dt = datetime.now()
                    max_t = max_dt.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"[{issue_key}] 最小时间点:\n{min_t}")
                logger.info(f"[{issue_key}] 最大时间点:\n{max_t}")
                logger.info(f"[{issue_key}] propids:\n{gen_propid_decimal_list(signal_to_info)}")

                self._update_progress('UNPACKING', 50, f'{issue_key} 提取 Android/QNX 日志')
                results = process_zip_packages_for_pipeline(
                    root_dir=Path(s_download_dir),
                    android_keywords=gen_propid_decimal_list(signal_to_info),  # 比如 ["559940304", "559992853"]
                    android_start_time=min_t,
                    android_end_time=max_t,
                    qnx_keywords=gen_propid_hex_list(signal_to_info),          # 比如 ["0X214002D7", "0x2160d015"]
                    qnx_start_time=min_t,
                    qnx_end_time=max_t,
                )
                # qnx android 日志结果是0  需要看一下
                if not results:
                    logger.info(f"[{issue_key}] 日志提取结果不存在")
                else:
                    android_log_part = self.get_android_log(results)
                    android_log = "".join(android_log_part)
                    write_model_issue_text_file(f"{model_str}", f"{issue_key}_android_log.txt", f"{issue_key}", android_log or "")
                    logger.info(f"[{issue_key}] 已合并 android 日志到 android_log，长度={len(android_log)}")

                    qnx_log_part = self.get_qnx_log(results)
                    qnx_log = "".join(qnx_log_part)
                    write_model_issue_text_file(f"{model_str}", f"{issue_key}_qnx_log.txt", f"{issue_key}", qnx_log or "")
                    logger.info(f"[{issue_key}] 已合并 qnx 日志到 qnx_log={len(qnx_log)}")

                # 10) 解析qnx android 日志
                self._update_progress('MODEL_INFERENCE', 60, f'{issue_key} AI 分析 Android/QNX 日志')
                ai_android_summary = self.ai.chat_by_langchain(aq_summary, android_log)
                # ai_android_summary = summarize_long_log(self.ai, aq_summary, android_log)
                logger.info(f"[{issue_key}] ai_android_summary={ai_android_summary}")

                ai_qnx_summary = self.ai.chat_by_langchain(aq_summary, qnx_log)
                # ai_qnx_summary = summarize_long_log(self.ai, aq_summary, qnx_log)
                logger.info(f"[{issue_key}] ai_qnx_summary={ai_qnx_summary}")

                ai_android_qnx_summary = (
                    ai_android_summary
                    + "\n\n==== QNX 日志总结 ====\n"
                    + ai_qnx_summary
                )
                write_model_issue_text_file(f"{model_str}", f"{issue_key}_android_qnx_log_summary.txt", f"{issue_key}", ai_android_qnx_summary)
                logger.info("-" * 80)
                logger.info(f"[{issue_key}] android qnx日志摘要:\n{ai_android_qnx_summary}")
                logger.info("-" * 80)

                # # 11) 解析 CAN Trace & 绘图
                latest_cantrace = ""
                if download_result["mode"] == "can_in_zip":
                    # asc 文件要从zip文件去找
                    # 可以从result中添加一个处理流程，返回cantrace的路径
                    latest_cantrace = self.get_latest_cantrace_path_str(root_dir=Path(s_download_dir))
                    logger.info(f"latest_cantrace : {latest_cantrace}")
                    if latest_cantrace is None:
                        logger.info(f"压缩包里没有cantrace  ")
                        self._finalize_issue(issue_key, summary, "压缩包里没有cantrace ，请复测", cantrace_path)
                        return
                else:
                    can_files = download_result.get("can_files") or []
                    if not can_files:
                        logger.warning(f"[{issue_key}] can_files 为空，下载未产出可用 cantrace")
                        self._finalize_issue(issue_key, summary, "未下载到可用 cantrace 文件，请检查 Jira 附件后重试", cantrace_path)
                        return
                    latest_cantrace = can_files[0]
                    
                if latest_cantrace=="":
                    logger.warning(f"latest_cantrace is null {latest_cantrace}  ")
                    self._finalize_issue(issue_key, summary, "cantrace 路径是空，没有找到cantrace文件，请复测", cantrace_path)
                    return
                self._update_progress('MODEL_INFERENCE', 70, f'{issue_key} 解析 CAN Trace 并绘图')
                can_trace_outputs, can_trace_path = self._plot_with_multi_dbc(signals, signal_to_info, dbc_paths, latest_cantrace)
                cantrace_path = can_trace_path

                # 校验 signals 是否全部出现在 can_trace_outputs 中
                missing_signals = [s for s in signals if s not in (can_trace_outputs or "")]
                if missing_signals:
                    missing_msg = f"以下信号在 CAN Trace 中不存在: {', '.join(missing_signals)}"
                    logger.warning(f"[{issue_key}] {missing_msg}")
                    write_model_issue_text_file(f"{model_str}", f"{issue_key}_reply.txt", f"{issue_key}", missing_msg)
                    self._finalize_issue(issue_key, summary, missing_msg, cantrace_path)
                    return

                write_model_issue_text_file(f"{model_str}", f"{issue_key}_can_trace.txt", f"{issue_key}", can_trace_outputs or "")

                # 12) 一致性分析
                # ai_summary: 上层日志中关于模块，信号，时间点，值，propid的信息
                # can_trace_outputs：cantrace中关于信号持续的值
                merged = (
                    "<需求描述>\n"+ai_extract_requirement+"\n</需求描述>\n"+
                    propid_text + "\n"+
                    "<上层提供的信号日志>\n" + ai_summary + "\n</上层提供的信号日志>"+
                    "\n<安卓+qnx日志>\n" + ai_android_qnx_summary + "\n</安卓+qnx日志>"+
                    "\n<CAN Trace日志>\n" + (can_trace_outputs or "") + "\n</CAN Trace日志>\n"
                )
                logger.info(f"cantrace output : {can_trace_outputs}")
                write_model_issue_text_file(f"{model_str}", f"{issue_key}_upper_and_qnxlog.txt", f"{issue_key}", merged)
                if ((len(merged) + len(p_cons) )> max_tokens * 2):
                    logger.warning(f"[{issue_key}] 一致性分析内容超出模型范围，建议手动处理")
                    return
                self._update_progress('GENERATING_REPLY', 85, f'{issue_key} AI 一致性分析')
                ai_consistency = self.ai.chat_by_langchain(p_cons, merged)
                write_model_issue_text_file(f"{model_str}", f"{issue_key}_consistency.txt", f"{issue_key}", ai_consistency)
                ai_res = ai_consistency
            else:
                # can
                # 使用上层解析的信号，解析cantrace，使用新的prompt单独解析cantrace
                # 8） 解析 CAN Trace & 绘图
                logger.info("self._plot_with_multi_dbc(signal_to_info, dbc_paths, log_path)")
                logger.info(f"download_result : {download_result}")
                logger.info(f"signals : {signals}")
                self._update_progress('MODEL_INFERENCE', 70, f'{issue_key} 解析 CAN Trace 并绘图')
                can_files = download_result.get("can_files") or []
                if not can_files:
                    logger.warning(f"[{issue_key}] can_files 为空，无法进行 CAN Trace 分析")
                    self._finalize_issue(issue_key, summary, "未下载到可用 cantrace 文件，请检查 Jira 附件后重试", cantrace_path)
                    return
                can_trace_outputs, can_trace_path = self._plot_with_multi_dbc(signals, signal_to_info, dbc_paths, can_files[0])
                cantrace_path = can_trace_path

                # 校验 signals 是否全部出现在 can_trace_outputs 中
                missing_signals = [s for s in signals if s not in (can_trace_outputs or "")]
                if missing_signals:
                    missing_msg = f"以下信号在 CAN Trace 中不存在: {', '.join(missing_signals)}"
                    logger.warning(f"[{issue_key}] {missing_msg}")
                    write_model_issue_text_file(f"{model_str}", f"{issue_key}_reply.txt", f"{issue_key}", missing_msg)
                    self._finalize_issue(issue_key, summary, missing_msg, cantrace_path)
                    return

                prop_signal_info = propid_text + group_text
                merged = (
                    "<信号及信号组关系>\n" + prop_signal_info + 
                    "</信号及信号组关系>\n<上层评论>\n" + comments_text +
                    "</上层评论>\n" + 
                    "<CAN Trace日志>\n" + (can_trace_outputs or "") +
                    "\n</CAN Trace日志>\n"
                )
                logger.info(f"cantrace output : {can_trace_outputs}")
                if ((len(merged) + len(p_cons) )> max_tokens * 2):
                    logger.warning(f"[{issue_key}] 一致性分析内容超出模型范围，建议手动处理")
                    return
                self._update_progress('GENERATING_REPLY', 85, f'{issue_key} AI 分析 CAN Trace')
                ai_cantrace_res = self.ai.chat_by_langchain(c_compare, merged)
                write_model_issue_text_file(f"{model_str}", f"{issue_key}_only_cantrace.txt", f"{issue_key}", ai_cantrace_res)
                ai_res = ai_cantrace_res
            logger.info("-" * 80)
            logger.info(f"[{issue_key}] ai分析结果:\n{ai_res}")
            logger.info("-" * 80)

            #  生成结论
            # self.process_ai_reply_consistency(ai_consistency)
            write_model_issue_text_file(f"{model_str}", f"{issue_key}_reply.txt", f"{issue_key}", ai_res)
            final_res = ""
            for key in ["最终结论", "最终结论:", "最终结论"]:
                idx = ai_res.find(key)
                if idx != -1:
                    final_res = ai_res[idx + len(key):].strip()
            self._update_progress('SAVING_RESULT', 95, f'{issue_key} 正在保存结果')
            self._finalize_issue(issue_key, summary, final_res or ai_res, cantrace_path, can_trace_outputs, comments_text)
