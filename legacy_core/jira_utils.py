'''
Author: huo2wx hongwei.huang@cn.bosch.com
Date: 2025-11-06 11:28:51
LastEditors: huo2wx huo2wx@bosch.com
LastEditTime: 2025-12-17 12:33:32
FilePath: \aitool-restructure\gpt-restructure-module\jira_utils.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from __future__ import annotations
import os
import time
import logging
import shutil
import re
import webbrowser

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Literal, TypedDict, Tuple, Any
from pathlib import Path
from jira import JIRA
from datetime import datetime
from .config_map import black_list,download_root

# 可调参数（按需修改）
_TMP_SUFFIXES = (".crdownload", ".part", ".tmp", ".partial")
_POLL_INTERVAL = 1.0  # 秒
_STABLE_SECONDS = 3    # 文件大小稳定判定秒数
_DEFAULT_TIMEOUT = 60 * 5  # 单个文件等待上限（秒）
DOWNLOAD_ROOT = Path(download_root)

logger = logging.getLogger("CAN-AI-JIRA")

class BrowserAttachmentDownloader:
    """
    使用 Playwright 进行浏览器附件下载。

    支持：
    - 无头模式下载
    - 指定下载目录
    - 可选 storage_state（复用登录态）
    - 可选额外 cookies
    """

    def __init__(
        self,
        download_dir: str,
        headless: bool = True,
        browser_type: str = "chromium",
        storage_state_path: Optional[str] = None,
        timeout_ms: int = 120000,
    ):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.headless = headless
        self.browser_type = browser_type
        self.storage_state_path = storage_state_path
        self.timeout_ms = timeout_ms

    def download(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        下载指定 URL，成功返回本地文件路径，失败返回 None。
        """
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            logger.exception("Playwright 未安装或导入失败: %s", e)
            return None

        try:
            with sync_playwright() as p:
                browser_launcher = getattr(p, self.browser_type, None)
                if browser_launcher is None:
                    logger.error("不支持的浏览器类型: %s", self.browser_type)
                    return None

                browser = browser_launcher.launch(headless=self.headless)

                context_kwargs = {
                    "accept_downloads": True,
                }
                if self.storage_state_path and os.path.exists(self.storage_state_path):
                    context_kwargs["storage_state"] = self.storage_state_path

                context = browser.new_context(**context_kwargs)
                page = context.new_page()
                page.set_default_timeout(self.timeout_ms)

                logger.info("浏览器准备下载: %s", url)

                with page.expect_download(timeout=self.timeout_ms) as download_info:
                    page.goto(url, wait_until="domcontentloaded")

                download = download_info.value

                suggested_name = download.suggested_filename
                final_name = filename or suggested_name or f"download_{int(time.time())}"
                save_path = self.download_dir / final_name

                download.save_as(str(save_path))

                try:
                    context.close()
                except Exception:
                    pass

                try:
                    browser.close()
                except Exception:
                    pass

                if save_path.exists() and save_path.stat().st_size > 0:
                    logger.info("浏览器下载成功: %s", save_path)
                    return str(save_path)

                logger.warning("浏览器下载后文件不存在或大小为 0: %s", save_path)
                return None

        except Exception as e:
            logger.exception("浏览器下载失败 url=%s, error=%s", url, e)
            return None
class JiraBrowserAuth:
    """
    用于首次登录 Jira 并保存 storage_state.json
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        storage_state_path: str = "playwright_jira_state.json",
        headless: bool = True,
        browser_type: str = "chromium",
        timeout_ms: int = 120000,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.storage_state_path = storage_state_path
        self.headless = headless
        self.browser_type = browser_type
        self.timeout_ms = timeout_ms

    def login_and_save_state(self) -> str:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser_launcher = getattr(p, self.browser_type)
            browser = browser_launcher.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(self.timeout_ms)

            login_url = f"{self.base_url}/login.jsp"
            logger.info("打开 Jira 登录页: %s", login_url)
            page.goto(login_url, wait_until="domcontentloaded")

            # 这里的选择器要按你们 Jira 登录页实际情况调整
            page.locator('input[name="os_username"]').fill(self.username)
            page.locator('input[name="os_password"]').fill(self.password)
            page.locator('input[name="login"]').click()

            page.wait_for_load_state("networkidle")

            context.storage_state(path=self.storage_state_path)

            context.close()
            browser.close()

        logger.info("Jira 登录态已保存: %s", self.storage_state_path)
        return self.storage_state_path
    
class JiraClient:
    def __init__(self, server: str, username: str, password: str):
        self.server = server
        self.username = username
        self.password = password
        self.client = JIRA(server=self.server, basic_auth=(self.username, self.password))

    def get_issue(self, key: str):
        return self.client.issue(key)

    def search_issues(self, jql: str, expand: str = "changelog"):
        return self.client.search_issues(jql, expand=expand)

    def fields(self):
        return self.client.fields()

    def add_comment(self, issue_key: str, content: str):
        return self.client.add_comment(issue_key, content)

    def add_attachment(self, issue_key: str, attachment_path: str):
        # python-jira: add_attachment(issue=<Issue|key>, attachment=<file|path>)
        return self.client.add_attachment(issue=issue_key, attachment=attachment_path)
    
    def add_comment_with_image(self, issue_key: str, text: str, image_path: str):
        """
        先上传图片，再在评论中用 !文件名! 的格式引用图片。
        """
        # 1. 先加附件
        attachment = self.client.add_attachment(
            issue=issue_key,
            attachment=image_path
        )
        if attachment:
            # 2. Jira 评论里用 wiki 语法插图：!filename!
            # attachment.filename 通常就是你上传的文件名
            img_token = f"!{attachment.filename}|width=600,height=400!"
            comment_body = f"{text}\n\n{img_token}"

            # 3. 再加评论
            return self.client.add_comment(issue_key, comment_body)
        else:
            return self.client.add_comment(issue_key, text)


def get_jira_comments(issue) -> str:
    comments_text = "<问题描述> \n"
    comments_text += f"问题键: {issue.key}\n"
    comments_text += f"摘要: {issue.fields.summary}\n"
    comments_text += f"状态: {issue.fields.status.name}\n"
    comments_text += "-" * 60 + "\n"

    if not issue.fields.comment or not issue.fields.comment.comments:
        comments_text += "这个问题没有任何评论。\n</问题描述> \n"
        return comments_text

    for idx, c in enumerate(issue.fields.comment.comments):
        comments_text += f"评论{idx}\n"
        comments_text += f"作者: {c.author.displayName}\n"
        comments_text += f"时间: {c.created}\n"
        comments_text += "内容:\n"
        comments_text += c.body + "\n"
        comments_text += "-" * 40 + "\n"
    comments_text += "</问题描述> \n"
    return comments_text

def _get_uploader_id(att) -> str:
    """
    从 attachment 中拿一个可用于匹配的“上传者标识”。
    可以按你的实际情况改成只用 name / accountId / displayName。
    """
    author = getattr(att, "author", None)
    if not author:
        return ""

    # JIRA Server：一般有 name / displayName
    # JIRA Cloud：一般有 accountId
    for attr in ("accountId", "name", "displayName"):
        val = getattr(author, attr, None)
        if val:
            return str(val)
    return ""

def download_latest_png(
    issue,
    download_dir: str = r".\data\log",
    suffixes: Tuple[str, ...] = (".png",),
    chunk_size: int = 8192,
    self_uploader_id: Optional[str] = None, 
) -> Optional[str]:
    atts = issue.fields.attachment
    if not atts:
        logger.info(f"票 {issue.key} 没有附件")
        return None

    # 选出 png 附件  
    # candidates = [a for a in atts if a.filename.endswith(suffixes)]
    # if not candidates:
    #     logger.info(f"票 {issue.key} 没有 png 文件")
    #     return None
    # 排除自己上传的图片
    candidates = []
    for a in atts:
        if not a.filename.endswith(suffixes):
            continue
        uploader_id = _get_uploader_id(a)
        logger.info(f"uploader_id : {uploader_id}")
        if self_uploader_id and uploader_id and uploader_id == str(self_uploader_id):
            logger.info(
                f"票 {issue.key} 跳过自己上传的图片: {a.filename} (uploader={uploader_id})"
            )
            continue
        candidates.append(a)
    if not candidates:
        logger.info(f"票 {issue.key} 没有 png 文件")
        return None
    latest = max(candidates, key=lambda a: a.created)
    filename = latest.filename
    size = latest.size
    logger.info(
        f"票 {issue.key} 最新的 png 图片: {filename} "
        f"(大小: {size / 1024 / 1024:.2f} MB)"
    )

    os.makedirs(download_dir, exist_ok=True)
    png_path = os.path.join(download_dir, filename)

    try:
        start = time.time()
        # 这里不用自己传 timeout，交给 jira 的 ResilientSession 处理
        resp = latest._session.get(latest.content, stream=True)
        resp.raise_for_status()  # ✅ 正确方法名

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(png_path, "wb") as f:
            if total == 0:
                # 没有 content-length 就一次性写
                data = resp.content
                f.write(data)
                downloaded = len(data)
            else:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

        dt = time.time() - start
        speed = downloaded / dt / 1024 / 1024 if dt > 0 else 0
        logger.info(
            f"票 {issue.key} png 下载完成: {png_path}"
            f"(耗时: {dt:.2f}s, 平均速度: {speed:.2f} MB/s)"
        )
        return png_path

    except Exception as e:
        logger.error(f"票 {issue.key} png 下载失败：{e}")
        if os.path.exists(png_path):
            os.remove(png_path)
        return None

# 定义结构
class DownloadResult(TypedDict):
    mode: Literal["can_only", "both", "reject", "can_in_zip"]  # 分别对应 a / b / c / d 4种情况
    can_files: List[str]
    log_files: List[str]
    reason: str

def _download_one_attachment(
    att,
    download_dir: str,
    suffixes: Tuple[str, ...],
    chunk_size: int = 65536,   # 默认块大一点，减少循环次数
) -> str | None:
    """下载单个附件，下载成功返回路径，失败返回 None。"""

    # 后缀过滤
    if not any(att.filename.endswith(suf) for suf in suffixes):
        return None

    out_path = Path(download_dir) / att.filename
    # 已存在且非空，直接复用
    if out_path.exists() and out_path.stat().st_size > 0:
        logger.info(f"附件已存在，跳过下载：{out_path}")
        return str(out_path)

    logger.info(f"下载附件：{att.filename} -> {out_path}")
    try:
        with open(out_path, "wb") as f:
            # 这里保持你的 att.get() 用法不变
            content = att.get()
            if isinstance(content, bytes):
                # 一次性返回 bytes，直接写
                f.write(content)
            else:
                # 假设是可迭代的流
                for chunk in content:
                    if not chunk:
                        continue
                    f.write(chunk)
        return str(out_path)
    except Exception as e:
        logger.exception(f"下载附件 {att.filename} 失败: {e}")
        # 如果失败可以考虑把半截文件删了
        try:
            if out_path.exists():
                out_path.unlink()
        except Exception:
            pass
        return None


def _detect_default_download_dir() -> Path:
    """探测常见的系统下载目录，找不到则返回用户主目录。"""
    home = Path.home()
    candidates = [home / "Downloads", home / "下载"]
    if os.name == "nt":
        up = Path(os.path.join(os.environ.get("USERPROFILE", ""), "Downloads"))
        candidates.append(up)
    for c in candidates:
        if c and c.exists():
            return c
    return home

def _get_att_url(att: Any) -> Optional[str]:
    """
    从 attachment 对象提取可在浏览器打开的下载链接。
    支持 dict 或对象，按优先级尝试字段名：content, url, href, link
    """
    if att is None:
        return None
    if isinstance(att, dict):
        for k in ("content", "url", "href", "link"):
            v = att.get(k)
            if isinstance(v, str) and v:
                return v
    else:
        for k in ("content", "url", "href", "link"):
            if hasattr(att, k):
                v = getattr(att, k)
                if isinstance(v, str) and v:
                    return v
    return None

def _open_in_browser(url: str) -> None:
    """用系统默认浏览器打开 URL（尝试在新标签打开）。"""
    try:
        webbrowser.open(url, new=2)
        logger.info("用系统默认浏览器打开 URL success")
    except Exception:
        webbrowser.open(url, new=1)

def _wait_for_download_complete(
    filename: str,
    src_dir: Optional[Path] = None,
    timeout: int = _DEFAULT_TIMEOUT,
    stable_seconds: int = _STABLE_SECONDS,
    poll_interval: float = _POLL_INTERVAL,
) -> Optional[Path]:
    if src_dir is None:
        src_dir = _detect_default_download_dir()
    else:
        src_dir = Path(src_dir)

    target = src_dir / filename
    start_ts = time.time()

    # 真实文件稳定计数
    last_size_target = None
    last_change_target = time.time()

    # 临时文件稳定计数（独立）
    last_size_temp = None
    last_change_temp = time.time()

    while True:
        if time.time() - start_ts > timeout:
            logger.debug("等待文件 %s 超时（%ds），目录=%s", filename, timeout, src_dir)
            return None

        # 1) 真实文件存在：只检查真实文件，别再碰 temp（避免 last_size 来回跳）
        try:
            if target.exists() and target.is_file():
                size = target.stat().st_size
                now = time.time()
                if last_size_target != size:
                    last_size_target = size
                    last_change_target = now
                elif now - last_change_target >= stable_seconds:
                    logger.debug("文件 %s 已稳定，认为下载完成（%d bytes）", target, size)
                    return target

                time.sleep(poll_interval)
                continue
        except Exception as e:
            logger.debug("检查目标文件时出错：%s", e)

        # 2) 真实文件不存在：再查找临时文件
        found_temp = None
        try:
            # 优先精确匹配（最可靠）
            for suf in _TMP_SUFFIXES:
                p = src_dir / (filename + suf)
                if p.exists() and p.is_file():
                    found_temp = p
                    break

            # 再做兜底：目录扫描（可能较慢）
            if not found_temp:
                for f in src_dir.iterdir():
                    if not f.is_file():
                        continue
                    if any(f.name.endswith(s) for s in _TMP_SUFFIXES):
                        # 这里尽量用 “包含” 或 “stem 接近” 的策略，比 startswith 更鲁棒
                        if f.name.startswith(filename) or filename in f.name:
                            found_temp = f
                            break
        except Exception as e:
            logger.debug("扫描临时文件出错：%s", e)
            found_temp = None

        if found_temp:
            try:
                size = found_temp.stat().st_size
                now = time.time()
                if last_size_temp != size:
                    last_size_temp = size
                    last_change_temp = now
                elif now - last_change_temp >= stable_seconds:
                    time.sleep(0.5)
                    if target.exists() and target.is_file():
                        continue
                    logger.debug("临时文件稳定但未见真实文件：%s（%d bytes）", found_temp, size)
                    return found_temp
            except Exception as e:
                logger.debug("检查临时文件出错：%s", e)

        time.sleep(poll_interval)


def _copy_to_download_dir(src_path: Path, dst_dir: str) -> Optional[str]:
    """复制 src_path 到 dst_dir 并返回目标路径字符串；失败返回 None。"""
    try:
        dst_dir_p = Path(dst_dir)
        dst_dir_p.mkdir(parents=True, exist_ok=True)
        dst = dst_dir_p / src_path.name
        shutil.copy2(str(src_path), str(dst))
        logger.debug("复制文件 %s -> %s", src_path, dst)
        return str(dst)
    except Exception as e:
        logger.warning("复制文件失败 %s -> %s : %s", src_path, dst_dir, e)
        return None

# def _download_attachments(
#     attachments,
#     download_dir: str,
#     suffixes: Tuple[str, ...],
#     chunk_size: int = 65536,
#     max_workers: int = 4,
#     use_browser_download: bool = False,
# ) -> List[str]:
#     """
#     串行手动模拟下载并保留回退逻辑版本。

#     逻辑：
#     - 对 attachments 中后缀匹配 suffixes 的条目：
#         1) 尝试从 attachment 中提取可在浏览器打开的 URL（content/url/href/link）
#         2) 若有 URL，则用浏览器打开并在系统下载目录等待对应 filename 出现并稳定，然后复制到 download_dir
#         3) 若没有 URL，或等待超时/失败，则**回退调用原始的** _download_one_attachment(att, download_dir, suffixes, chunk_size)
#     - 返回实际成功写入 download_dir 的本地路径列表（来自复制或 _download_one_attachment 的返回值）
#     """
#     Path(download_dir).mkdir(parents=True, exist_ok=True)
#     saved_paths: List[str] = []

#     if not attachments:
#         return saved_paths

#     logger.info("attachments total = %d", len(attachments) if hasattr(attachments, "__len__") else -1)


#     # 遍历串行处理
#     for att in attachments:
#         logger.info("iter att raw = %r", att if isinstance(att, dict) else getattr(att, "filename", att))
#         # 尝试获取 filename
#         filename = None
#         if isinstance(att, dict):
#             filename = att.get("filename")
#         else:
#             filename = getattr(att, "filename", None)

#         if not filename:
#             logger.debug("attachment 缺少 filename 字段，尝试回退到 _download_one_attachment")
#             # 回退尝试（若你希望在这种情况下直接跳过，可删除以下回退逻辑）
#             try:
#                 path = _download_one_attachment(att, download_dir, suffixes, chunk_size)
#                 if path:
#                     saved_paths.append(path)
#                 continue
#             except Exception as e:
#                 logger.warning("回退 _download_one_attachment 时出错：%s", e)
#                 continue

#         # 粗略后缀过滤
#         if not any(filename.endswith(suf) for suf in suffixes):
#             logger.debug("文件名 %s 后缀不匹配，跳过", filename)
#             continue


#         url = _get_att_url(att)

#         if use_browser_download and url:
#             logger.info("通过浏览器触发下载：%s", filename)
#             try:
#                 _open_in_browser(url)
#             except Exception:
#                 logger.debug("打开浏览器失败，继续尝试回退下载")

#             try:
#                 downloaded = _wait_for_download_complete(filename, src_dir=DOWNLOAD_ROOT)
#                 logger.info(f"附件下载成功：{downloaded}")
#             except Exception as e:
#                 logger.debug("等待下载过程中出错：%s", e)
#                 downloaded = None

#             if downloaded:
#                 dst = _copy_to_download_dir(downloaded, download_dir)
#                 if dst:
#                     saved_paths.append(dst)
#                     logger.info("复制下载文件 %s 到 %s 成功", downloaded, download_dir)
#                     continue

#         logger.info("附件 %s 使用 HTTP 直连下载", filename)
#         path = _download_one_attachment(att, download_dir, suffixes, chunk_size)
#         if path:
#             saved_paths.append(path)
#         # 尝试从 attachment 提取 URL 并用浏览器打开触发下载
#         # url = _get_att_url(att)
#         # logger.info("attachment: filename=%s url=%s", filename, url)

#         # if url:
#         #     logger.info("通过浏览器触发下载：%s", filename)
#         #     try:
#         #         _open_in_browser(url)
#         #     except Exception:
#         #         logger.debug("打开浏览器失败，继续尝试回退下载")

#         #     # 等待浏览器下载目录中的文件出现并稳定
#         #     try:
#         #         downloaded = _wait_for_download_complete(filename, src_dir=DOWNLOAD_ROOT)
#         #         logger.info(f"附件下载成功：{downloaded}")
#         #     except Exception as e:
#         #         logger.debug("等待下载过程中出错：%s", e)
#         #         downloaded = None

#         #     if downloaded:
#         #         # 复制到目标目录
#         #         dst = _copy_to_download_dir(downloaded, download_dir)
#         #         if dst:
#         #             saved_paths.append(dst)
#         #             # 成功后继续下一个附件
#         #             logger.warning("复制下载文件 %s 到 %s 成功， 继续下一个附件", downloaded, download_dir)
                    
#         #             continue
#         #         else:
#         #             logger.warning("复制下载文件 %s 到 %s 失败，尝试回退到 _download_one_attachment", downloaded, download_dir)
#         #     else:
#         #         logger.warning("未检测到浏览器下载的文件 %s（或等待超时），将回退到 _download_one_attachment", filename)
#         # else:
#         #     logger.info("附件 %s 没有可用于浏览器的 URL，使用回退 HTTP 下载", filename)

#         # 回退到原始的 HTTP 下载实现（确保这个函数在模块中存在）
#         try:
#             path = _download_one_attachment(att, download_dir, suffixes, chunk_size)
#             if path:
#                 saved_paths.append(path)
#         except Exception as e:
#             logger.exception("回退 _download_one_attachment 失败：%s", e)
#             # 失败则记录并继续下一个附件

#     return saved_paths


# browser download
def _download_attachments(
    attachments,
    download_dir: str,
    suffixes: Tuple[str, ...],
    chunk_size: int = 65536,
    max_workers: int = 4,
    use_browser_download: bool = False,
) -> List[str]:
    """
    串行手动模拟下载并保留回退逻辑版本。

    逻辑：
    - 对 attachments 中后缀匹配 suffixes 的条目：
        1) 尝试从 attachment 中提取可在浏览器打开的 URL（content/url/href/link）
        2) 若有 URL，则用浏览器下载类下载到 download_dir
        3) 若没有 URL，或浏览器下载失败，则回退调用 _download_one_attachment()
    - 返回实际成功写入 download_dir 的本地路径列表
    """
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    saved_paths: List[str] = []

    if not attachments:
        return saved_paths

    logger.info(
        "attachments total = %d",
        len(attachments) if hasattr(attachments, "__len__") else -1
    )

    browser_downloader = None
    if use_browser_download:
        browser_downloader = BrowserAttachmentDownloader(
            download_dir=download_dir,
            headless=True,
            browser_type="chromium",
            storage_state_path="playwright_jira_state.json",  # 没有可填 None
            timeout_ms=120000,
        )

    for att in attachments:
        logger.info(
            "iter att raw = %r",
            att if isinstance(att, dict) else getattr(att, "filename", att)
        )

        # 获取 filename
        filename = None
        if isinstance(att, dict):
            filename = att.get("filename")
        else:
            filename = getattr(att, "filename", None)

        if not filename:
            logger.warning("attachment 缺少 filename，跳过: %r", att)
            continue

        # 后缀过滤
        if not any(filename.lower().endswith(suf.lower()) for suf in suffixes):
            logger.debug("文件名 %s 后缀不匹配，跳过", filename)
            continue

        # 文件已存在则直接复用
        out_path = Path(download_dir) / filename
        if out_path.exists() and out_path.stat().st_size > 0:
            logger.info("附件已存在，跳过下载：%s", out_path)
            saved_paths.append(str(out_path))
            continue

        downloaded_path = None

        # 1) 浏览器下载
        if use_browser_download and browser_downloader is not None:
            url = _get_att_url(att)
            logger.info("attachment: filename=%s url=%s", filename, url)

            if url:
                downloaded_path = browser_downloader.download(
                    url=url,
                    filename=filename,
                )
                if downloaded_path:
                    saved_paths.append(downloaded_path)
                    logger.info("浏览器下载成功：%s", downloaded_path)
                    continue
                else:
                    logger.warning("浏览器下载失败，准备回退 HTTP 下载：%s", filename)
            else:
                logger.warning("附件 %s 没有可用于浏览器下载的 URL", filename)

        # 2) 回退到原始 HTTP 下载
        try:
            path = _download_one_attachment(att, download_dir, suffixes, chunk_size)
            if path:
                saved_paths.append(path)
                logger.info("HTTP 下载成功：%s", path)
            else:
                logger.warning("HTTP 下载失败：%s", filename)
        except Exception as e:
            logger.exception("回退 _download_one_attachment 失败：%s", e)

    return saved_paths
def _to_dt(created):
    """
    把 JIRA 的 Attachment.created 转成 datetime。
    """
    if isinstance(created, datetime):
        return created

    s = str(created).strip()
    if not s:
        logger.warning("附件 created 为空字符串")
        return None

    # 处理 Z 结尾 => +00:00
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    # 处理 +0800 / -0500 => +08:00 / -05:00
    m = re.search(r"([+-]\d{4})$", s)
    if m:
        tz = m.group(1)
        s = s[:-5] + tz[:3] + ":" + tz[3:]

    try:
        return datetime.fromisoformat(s)
    except Exception as e:
        logger.warning(f"无法解析附件时间 created={created!r}, 解析串={s!r}, 错误={e}")
        return None

def _expand_split_archives(latest_att, all_atts):
    """
    如果 latest_att 是 .zip.001/.zip.002/... 这类分卷，返回同前缀的全套分卷列表（按序）。
    否则返回 [latest_att]。
    """
    name = getattr(latest_att, "filename", None) or (latest_att.get("filename") if isinstance(latest_att, dict) else None)
    if not name:
        return [latest_att]

    m = re.match(r"^(.*)\.(zip|7z|rar)\.(\d+)$", name, re.IGNORECASE)
    if not m:
        return [latest_att]

    prefix, ext, _ = m.group(1), m.group(2).lower(), m.group(3)

    # 收集同组分卷
    parts = []
    for a in all_atts:
        fn = getattr(a, "filename", None) or (a.get("filename") if isinstance(a, dict) else None)
        if not fn:
            continue
        if re.match(rf"^{re.escape(prefix)}\.{ext}\.\d+$", fn, re.IGNORECASE):
            parts.append(a)

    # 按分卷序号排序
    def part_no(att):
        fn = getattr(att, "filename", None) or att.get("filename")
        mm = re.match(rf"^{re.escape(prefix)}\.{ext}\.(\d+)$", fn, re.IGNORECASE)
        return int(mm.group(1)) if mm else 10**9

    parts.sort(key=part_no)
    return parts or [latest_att]

def download_all_need_attachment(
    issue,
    download_dir: str = r".\data\log",
    suffixes: Tuple[str, ...] = (
        ".7z.001", ".7z.002", ".7z.003", ".7z.004", ".7z.005", ".7z.006", ".7z.007", ".7z.008", ".7z.009", ".7z.0010",
        ".zip.001", ".zip.002", ".zip.003", ".zip.004", ".zip.005", ".zip.006", ".zip.007", ".zip.008", ".zip.009", ".zip.0010",
        ".rar.001", ".rar.002", ".rar.003", ".rar.004", ".rar.005", ".rar.006", ".rar.007", ".rar.008", ".rar.009", ".rar.0010",
        ".7z", ".rar", ".zip", ".tgz", ".asc", ".blf",
    ),
    chunk_size: int = 8192,
) -> Optional[DownloadResult]:
    """
    重构后的 download_all_need_attachment：
    - 按创建时间比较最新的压缩日志包与 CAN Trace（.asc/.blf），
      并根据时间差返回四种主要决策：can_only / both / reject / can_in_zip。
    - 时间阈值与原行为保持一致；在灰区返回 None。
    - 若上传日志者在黑名单并且未上传 cantrace，返回 mode="can_in_zip"（保持原行为）。
    """

    max_diff_seconds = 7200        # 1 小时
    min_diff_seconds = 60 * 90     # 90 分钟

    # 常用后缀集合
    zip_suffixes = (".rar", ".001", ".002",".003", ".004", ".005", ".006",".7z", ".zip", ".tgz")
    can_suffixes = (".asc", ".blf")

    def _latest_by_suffixes(attachments, suffix_tuple) -> Optional[object]:
        """返回 attachments 中按 created 时间最新且以给定后缀结尾的附件（或 None）。"""
        filtered = [a for a in attachments if a.filename.endswith(suffix_tuple)]
        if not filtered:
            return None
        return max(filtered, key=lambda a: _to_dt(a.created) or datetime.min)

    def _safe_dt(obj) -> Optional[datetime]:
        """从附件对象解析时间，解析失败返回 None。"""
        dt = _to_dt(obj.created) if obj else None
        return dt

    def _decide_by_time_diff(latest_can, latest_zip):
        """
        根据两个 latest 附件对象的时间差做出决策并返回相应的 DownloadResult 或 None（灰区）。
        保证不重复下载（调用 _download_attachments 仅在需要下载时执行）。
        """
        latest_can_time = _safe_dt(latest_can)
        latest_zip_time = _safe_dt(latest_zip)

        if not latest_can_time or not latest_zip_time:
            logger.warning(f"票 {issue.key} 无法解析时间（can:{latest_can_time} zip:{latest_zip_time}）")
            return None

        diff = (latest_can_time - latest_zip_time).total_seconds()
        logger.info(
            f"票 {issue.key} 最新 CAN 时间 = {latest_can_time}, 最新 log 时间 = {latest_zip_time}, diff = {diff:.0f}s"
        )

        can_files: List[str] = []
        log_files: List[str] = []

        # 情况 a：CAN 显著更新，只分析 CAN
        if diff > max_diff_seconds:
            logger.info(
                f"票 {issue.key}：最新 CAN 比最新 log 晚 {diff:.0f}s (> {max_diff_seconds}s)，只分析 CAN。"
            )
            can_files = _download_attachments([latest_can], download_dir, can_suffixes, chunk_size)
            return DownloadResult(
                mode="can_only",
                can_files=can_files,
                log_files=log_files,
                reason=(
                    f"最新 CAN({latest_can.filename}) 显著晚于最新 log({latest_zip.filename})，"
                    f"时间差 {diff:.0f}s，仅分析 CAN。"
                ),
            )

        # 情况 b：时间差在 50 分钟以内，上下文分析
        if abs(diff) <= min_diff_seconds:
            logger.info(
                f"票 {issue.key}：CAN 与 log 时间差 {diff:.0f}s (<= {min_diff_seconds}s)，CAN + log 一起分析。"
            )
            can_files = _download_attachments([latest_can], download_dir, can_suffixes, chunk_size)
            zip_atts = _expand_split_archives(latest_zip, issue.fields.attachment)  # attachments = issue.fields.attachment（全量） 相关的00x 一并下载
            log_files = _download_attachments(zip_atts, download_dir, zip_suffixes, chunk_size)

            return DownloadResult(
                mode="both",
                can_files=can_files,
                log_files=log_files,
                reason=(
                    f"最新 CAN({latest_can.filename}) 与最新 log({latest_zip.filename}) "
                    f"时间差 {diff:.0f}s 在可接受范围内，进行上下文联合分析。"
                ),
            )

        # 情况 c：log 显著更新但 CAN 很久没更新，打回
        if diff < -max_diff_seconds:
            logger.info(
                f"票 {issue.key}：最新 log 比最新 CAN 晚 {-diff:.0f}s (> {max_diff_seconds}s)，没有对应的最新 CAN Trace，建议打回。"
            )
            # 检查黑名单
            uploader_id = _get_uploader_id(latest_zip)
            if uploader_id in black_list:
                logger.info(f"票 {issue.key} 日志上传者在黑名单且未上传最新 CAN trace，返回 can_in_zip 以便从 zip 解压查找")
                # 下载zip 
                log_files: List[str] = []
                zip_atts = _expand_split_archives(latest_zip, issue.fields.attachment)  # attachments = issue.fields.attachment（全量）
                log_files = _download_attachments(zip_atts, download_dir, zip_suffixes, chunk_size)
                return DownloadResult(
                    mode="can_in_zip",
                    can_files=[],
                    log_files=log_files,
                    reason=(
                        "日志上传者在黑名单中，且cantrace不存在，需要下载zip解压，查看cantrace文件",
                        "在解压文件中存在cantrace和android+qnx日志"
                    ),
                )
            return DownloadResult(
                mode="reject",
                can_files=can_files,
                log_files=log_files,
                reason=(
                    f"[没有最新 CAN Trace]"
                    f"车控车设问题分析需要CAN trace，请复测并提取问题发生时的Android log, QNX log, CAN trace，依次从应用->Framework再转给VHAL分析，谢谢"
                ),
            )

        # 灰区
        logger.info(
            f"票 {issue.key}：CAN 与 log 时间差 {diff:.0f}s 介于 {min_diff_seconds}s 和 {max_diff_seconds}s 之间，进入灰区，不自动下载。"
        )
        return None

    # --- 开始主流程 ---
    atts = issue.fields.attachment
    if not atts:
        logger.info(f"票 {issue.key} 没有附件")
        return None

    # 取最新的压缩日志（zip/7z/rar 等）
    latest_zip_log = _latest_by_suffixes(atts, zip_suffixes)
    if not latest_zip_log:
        logger.info(f"票 {issue.key} 没有 QNX / Android log")
        latest_can_log = _latest_by_suffixes(atts, can_suffixes)
        if not latest_can_log:
            logger.info(f"票 {issue.key} 没有找到 CAN Trace 文件")
            return None
        else:
            can_files = _download_attachments([latest_can_log], download_dir, can_suffixes, chunk_size)
            return DownloadResult(
                mode="can_only",
                can_files=can_files,
                log_files=[],
                reason=(
                    f"只有cantrace文件，"
                    f"仅分析 CAN。"
                ),
            )
        return None

    latest_zip_log_time = _safe_dt(latest_zip_log)
    if not latest_zip_log_time:
        logger.warning(f"票 {issue.key} 无法解析压缩日志时间")
        return None

    # 如果压缩日志上传者在黑名单，先特殊判断是否存在 cantrace
    uploader_id = _get_uploader_id(latest_zip_log)
    if uploader_id in black_list:
        cantrace_exists = any(a.filename.endswith(can_suffixes) for a in atts)
        if not cantrace_exists:
            logger.info(f"票 {issue.key} 日志上传者在黑名单且未上传 CAN trace，返回 can_in_zip 以便从 zip 解压查找")
            # 下载zip 
            log_files: List[str] = []
            zip_atts = _expand_split_archives(latest_zip_log, issue.fields.attachment)  # attachments = issue.fields.attachment（全量）
            log_files = _download_attachments(zip_atts, download_dir, zip_suffixes, chunk_size)
            return DownloadResult(
                mode="can_in_zip",
                can_files=[],
                log_files=log_files,
                reason=(
                    "日志上传者在黑名单中，且cantrace不存在，需要下载zip解压，查看cantrace文件",
                    "在解压文件中存在cantrace和android+qnx日志"
                ),
            )
        # 如果 cantrace 存在，则继续按常规比较时间（下面会复用同样逻辑）
        # （注意：这里不重复查询，直接选最新的 cantrace）
    
    # 查找最新的 CAN trace（无论是否黑名单）
    latest_can_log = _latest_by_suffixes(atts, can_suffixes)
    if not latest_can_log:
        logger.info(f"票 {issue.key} 没有找到 CAN Trace 文件")
        return None

    # 最终基于时间差决定
    return _decide_by_time_diff(latest_can_log, latest_zip_log)


if __name__  == "__main__":
    jira = JiraClient(
        server="https://jira-shzj.auto-link.com.cn",
        username="DaiYungui_bosch",
        password="Wibe4Bbs"
    )
    # jql = "project in (CHER, CHYT28) AND issuekey in updatedBy(DaiYungui_bosch) AND issue= CHER-132707"
    jql = "project in (CHERY-T1J-FL2-8255) AND assignee in (currentUser()) ORDER BY updated DESC"
    issues = jira.search_issues(jql)
    for idx, issue in enumerate(issues, 1):
        download_all_need_attachment(issue)
