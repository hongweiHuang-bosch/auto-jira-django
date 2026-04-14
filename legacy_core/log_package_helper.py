# -*- coding: utf-8 -*-
"""
功能：
1. 扫描 ./zip_package/ 下的所有压缩包：
   - *.7z / *.7z.001（分卷）
   - *.zip / *.zip.001（分卷）
   - *.rar
   - *.tgz / *.tar.gz
2. 每个压缩包解压到：<压缩包主名>_unzip 目录。
   - 如果该目录已存在且非空，则认为已经解压过，跳过。
3. 针对每个 <主名>_unzip：
   3.1 递归解压目录树中所有 .tgz（android_log / nfs_log 等）
   3.2 在包含 "android_log" 的目录中解压所有 .gz 文件（如果目标已存在则跳过）。
   3.3 在这些 android_log 目录下所有已解压文件里，
       提取包含关键字的行，写到
       <主名>_unzip/android_log_<keyword>_time_filtered.txt。
   3.4 在包含 "qnx_log" 的目录中，找 cycle_数字 目录里数字最大的那个，
       并解压其中所有以 "Bosch" 开头的 zip 文件。
   3.5 在这些 qnx_log 目录下，提取包含关键字的行，写到
       <主名>_unzip/qnx_log_<keyword>_time_filtered.txt。

提供给 pipeline 使用的统一入口：
    process_zip_packages_for_pipeline(...)
"""
import shutil
import subprocess
import gzip
import shutil
import zipfile
import re
from typing import List, Optional, Dict, Iterable, Tuple
from datetime import datetime
from pathlib import Path

# 如果 7z 不在 PATH，请改成绝对路径，比如：
# SEVEN_ZIP = r"C:\Program Files\7-Zip\7z.exe"
SEVEN_ZIP = shutil.which("7z") or "7z"

ROOT = Path("./comment/D01P-/DPINT-1623")


# --------------------- 工具：解析日志时间 ---------------------

def parse_log_time(line: str, default_year: int = 2025) -> Optional[datetime]:
    """
    从一行日志里解析时间戳，返回 datetime 或 None。
    尝试支持几种常见格式：
      1) 2025-11-20 06:22:10.123
      2) 2025-11-20 06:22:10
      3) 11-20 06:22:10.123
      4) 11-20 06:22:10
    """
    # 优先匹配带年份的：YYYY-MM-DD HH:MM:SS(.ms)
    m = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{1,3})?)", line)
    if m:
        ts = m.group(1)
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(ts, fmt)
            except ValueError:
                pass

    # 再匹配无年份的：MM-DD HH:MM:SS(.ms)
    m = re.search(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{1,3})?)", line)
    if m:
        ts = m.group(1)
        for fmt in ("%m-%d %H:%M:%S.%f", "%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(ts, fmt)
                # 填上默认年份
                return dt.replace(year=default_year)
            except ValueError:
                pass

    return None


# --------------------- 工具：调用 7z 解压 ---------------------

def run_7z(archive: Path, out_dir: Path) -> None:
    """
    调用 7z 解压 archive 到 out_dir
    如果 out_dir 已存在且非空，则视为已经解压过，直接跳过
    """
    if out_dir.exists():
        try:
            if any(out_dir.iterdir()):
                print(f"[INFO] this dir has existed, skip: {out_dir}")
                return
        except Exception as e:
            print(f"[WARNING] check this dir error {out_dir}: {e}")

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] unzip this zip package: {archive} -> {out_dir}")
    cmd = [SEVEN_ZIP, "x", str(archive), f"-o{out_dir}", "-y"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] unzip error: {archive}")
        print(result.stdout)
        print(result.stderr)
    else:
        print(f"[INFO] unzip success {archive.name}")


def extract_tgz_or_tar_gz(archive: Path, out_dir: Path) -> None:
    """
    顶层 .tgz / .tar.gz 两步解压：
      tgz -> out_dir/_tgz_tmp/*.tar -> out_dir
    """
    if out_dir.exists():
        try:
            if any(out_dir.iterdir()):
                print(f"[SKIP] 目标目录已存在且非空，认为已解压过，跳过：{out_dir}")
                return
        except Exception as e:
            print(f"[WARN] 检查目录内容失败：{out_dir}，继续尝试解压。原因：{e}")
    tmp_dir = out_dir / "_tgz_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # tgz -> tmp_dir = .tar
    cmd1 = [SEVEN_ZIP, "x", str(archive), f"-o{tmp_dir}", "-y"]
    r1 = subprocess.run(cmd1, capture_output=True, text=True)
    if r1.returncode != 0:
        print(f"[ERROR] unzip tgz to tar failed {archive}")
        print(r1.stdout)
        print(r1.stderr)
        return

    tar_files = list(tmp_dir.glob("*.tar"))
    if not tar_files:
        print(f"[ERROR] no .tar after tgz extract: {archive}")
        return
    tar_file = tar_files[0]

    # tar -> out_dir
    cmd2 = [SEVEN_ZIP, "x", str(tar_file), f"-o{out_dir}", "-y"]
    r2 = subprocess.run(cmd2, capture_output=True, text=True)
    if r2.returncode != 0:
        print(f"[ERROR] unzip tar failed {tar_file}")
        print(r2.stdout)
        print(r2.stderr)
        return

    try:
        shutil.rmtree(tmp_dir)
    except Exception as e:
        print(f"[ERROR] rm tmp dir failed {e}")

    print(f"[INFO] tgz fully extracted to {out_dir}")


def extract_inner_tgz_in_place(unzip_root: Path) -> None:
    """
    在 unzip_root 目录树中查找 android_log.tgz 和 nfs_log.tgz，
    对每个 .tgz 做两步解压：
      - tgz -> 临时目录 -> tar -> 同级目录
    输出内容直接落在 tgz 所在目录（in-place），不再新建 *_unzip。
    """
    targets = ("android_log.tgz", "nfs_log.tgz")
    for tgz_name in targets:
        for tgz_file in unzip_root.rglob(tgz_name):
            parent = tgz_file.parent
            tmp_dir = parent / f"._tmp_{tgz_file.stem}"
            tmp_dir.mkdir(parents=True, exist_ok=True)

            print(f"[INFO] inner tgz step1: {tgz_file} -> {tmp_dir}")
            cmd1 = [SEVEN_ZIP, "x", str(tgz_file), f"-o{tmp_dir}", "-y"]
            r1 = subprocess.run(cmd1, capture_output=True, text=True)
            if r1.returncode != 0:
                print(f"[ERROR] inner tgz -> tar failed: {tgz_file}")
                print(r1.stdout)
                print(r1.stderr)
                try:
                    shutil.rmtree(tmp_dir)
                except Exception:
                    pass
                continue

            tar_files = list(tmp_dir.glob("*.tar"))
            if not tar_files:
                print(f"[ERROR] inner tgz no .tar found: {tgz_file}")
                try:
                    shutil.rmtree(tmp_dir)
                except Exception:
                    pass
                continue

            for tar_file in tar_files:
                print(f"[INFO] inner tgz step2: tar -> parent: {tar_file} -> {parent}")
                cmd2 = [SEVEN_ZIP, "x", str(tar_file), f"-o{parent}", "-y"]
                r2 = subprocess.run(cmd2, capture_output=True, text=True)
                if r2.returncode != 0:
                    print(f"[ERROR] inner tar unzip failed: {tar_file}")
                    print(r2.stdout)
                    print(r2.stderr)

            try:
                shutil.rmtree(tmp_dir)
            except Exception as e:
                print(f"[WARNING] remove inner tmp dir failed: {tmp_dir}, {e}")

            print(f"[INFO] inner tgz fully extracted in place: {tgz_file}")


def extract_tgz_recursively_in_dir(base_dir: Path) -> None:
    """
    在 base_dir 目录树中递归查找 *.tgz，并在原地解压：
      - 先把 .tgz 解到一个临时目录，得到 .tar
      - 再把 .tar 解到 .tgz 所在目录
      - 删除临时目录
    """
    for tgz_file in base_dir.rglob("*.tgz"):
        parent = tgz_file.parent
        tmp_dir = parent / f"._tmp_{tgz_file.stem}"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] android inner tgz step1: {tgz_file} -> {tmp_dir}")
        cmd1 = [SEVEN_ZIP, "x", str(tgz_file), f"-o{tmp_dir}", "-y"]
        r1 = subprocess.run(cmd1, capture_output=True, text=True)
        if r1.returncode != 0:
            print(f"[ERROR] android inner tgz -> tar failed: {tgz_file}")
            print(r1.stdout)
            print(r1.stderr)
            try:
                shutil.rmtree(tmp_dir)
            except Exception:
                pass
            continue

        tar_files = list(tmp_dir.glob("*.tar"))
        if not tar_files:
            print(f"[ERROR] android inner tgz no .tar found: {tgz_file}")
            try:
                shutil.rmtree(tmp_dir)
            except Exception:
                pass
            continue

        for tar_file in tar_files:
            print(f"[INFO] android inner tgz step2: tar -> parent: {tar_file} -> {parent}")
            cmd2 = [SEVEN_ZIP, "x", str(tar_file), f"-o{parent}", "-y"]
            r2 = subprocess.run(cmd2, capture_output=True, text=True)
            if r2.returncode != 0:
                print(f"[ERROR] android inner tar unzip failed: {tar_file}")
                print(r2.stdout)
                print(r2.stderr)

        try:
            shutil.rmtree(tmp_dir)
        except Exception as e:
            print(f"[WARNING] remove android inner tmp dir failed: {tmp_dir}, {e}")

        print(f"[INFO] android inner tgz fully extracted in place: {tgz_file}")


# --------------------- 步骤 1：识别并解压所有压缩包 ---------------------

def extract_all_archives(root: Path) -> List[Path]:
    """
    在 root（./zip_package）目录下识别压缩包并解压。
    返回所有对应的 <主名>_unzip 目录列表（无论是刚解压还是之前已存在）。
    """
    files = [f for f in root.iterdir() if f.is_file()]
    processed_archives = set()
    out_dirs: List[Path] = []

    # 1）分卷 7z：入口 *.7z.001
    for f in files:
        name = f.name.lower()
        if name.endswith(".7z.001") and f not in processed_archives:
            base = f.name.rsplit(".7z.001", 1)[0]
            out_dir = root / f"{base}_unzip"
            run_7z(f, out_dir)
            processed_archives.add(f)
            out_dirs.append(out_dir)

    # 2）分卷 zip：入口 *.zip.001
    for f in files:
        name = f.name.lower()
        if name.endswith(".zip.001") and f not in processed_archives:
            base = f.name.rsplit(".zip.001", 1)[0]
            out_dir = root / f"{base}_unzip"
            run_7z(f, out_dir)
            processed_archives.add(f)
            out_dirs.append(out_dir)

    # 3）单包 7z（排除 .7z.001）
    for f in files:
        name = f.name.lower()
        if name.endswith(".7z") and not name.endswith(".7z.001") and f not in processed_archives:
            base = f.stem
            out_dir = root / f"{base}_unzip"
            run_7z(f, out_dir)
            processed_archives.add(f)
            out_dirs.append(out_dir)

    # 4）单包 zip（排除 .zip.001）
    for f in files:
        name = f.name.lower()
        if name.endswith(".zip") and not name.endswith(".zip.001") and f not in processed_archives:
            base = f.stem
            out_dir = root / f"{base}_unzip"
            run_7z(f, out_dir)
            processed_archives.add(f)
            out_dirs.append(out_dir)

    # 5) rar
    for f in files:
        name = f.name.lower()
        if name.endswith(".rar") and not name.endswith(".rar.001") and f not in processed_archives:
            base = f.stem
            out_dir = root / f"{base}_unzip"
            run_7z(f, out_dir)
            processed_archives.add(f)
            out_dirs.append(out_dir)

    # 6) tgz / tar.gz
    for f in files:
        name = f.name.lower()
        if (name.endswith(".tgz") or name.endswith(".tar.gz")) and f not in processed_archives:
            if name.endswith(".tgz"):
                base = f.stem          # foo.tgz -> foo
            else:
                base = f.name[:-7]     # foo.tar.gz -> foo
            out_dir = root / f"{base}_unzip"
            extract_tgz_or_tar_gz(f, out_dir)
            processed_archives.add(f)
            out_dirs.append(out_dir)

    print(f"[INFO] 解压流程结束，涉及 {len(out_dirs)} 个 *_unzip 目录。")
    return out_dirs


# --------------------- 步骤 2：android_log 相关 ---------------------

def find_android_dirs(unzip_root: Path) -> List[Path]:
    """
    在 unzip_root 下查找所有包含 'android_log' 的目录。
    """
    return [d for d in unzip_root.rglob("*") if d.is_dir() and "android_log" in d.name]


def decompress_gz_in_android_logs(unzip_root: Path) -> None:
    """
    在 unzip_root 目录下查找 android_log 的目录，
    对这些目录中所有 .gz 文件进行解压。
    如果 .gz 对应的目标文件已经存在，跳过。
    """
    android_dirs = find_android_dirs(unzip_root)
    if not android_dirs:
        print(f"[WARING] not find android_log dir : {unzip_root}")
        return

    for adir in android_dirs:
        print(f"[INFO] this dir is {adir}")
        for gz_file in adir.rglob("*.gz"):
            target = gz_file.with_suffix("")  # 去掉.gz
            if target.exists():
                print(f"[INFO] skip, this target has been in the dir: {target}")
                continue
            try:
                with gzip.open(gz_file, "rb") as f_in, open(target, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            except Exception as e:
                print(f"[ERROR] unzip error: {gz_file}, {e}")


def extract_lines_with_keyword_in_android_logs(
    unzip_root: Path,
    keyword: str = "559992853",
    start_time_str: str = "2025-11-20 06:22:09",
    end_time_str: str = "2025-11-20 06:22:11",
) -> Optional[Path]:
    """
    在 unzip_root 下的所有 android_log 目录中，扫描所有已解压文件（排除 .gz），
    提取：
      - 包含 keyword 的行
      - 且行内时间戳在 [start_time, end_time] 范围内

    写到：
        <unzip_root>/android_log_<keyword>_time_filtered.txt

    返回：输出文件路径，如果未找到 android_log 目录则返回 None。
    """
    android_dirs = find_android_dirs(unzip_root)
    print(f"android_dir is : {android_dirs}")
    if not android_dirs:
        print(f"[WARN] 未找到 android_log 目录（提取关键字行）：{unzip_root}")
        return None

    # 解析时间范围
    if start_time_str is None or end_time_str is None:
        print(f"[WARN] 提取时间错误")
        return None
        
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

    if start_time is None or end_time is None:
        print(f"[WARN] 提取时间错误")
        return None

    out_file = unzip_root / f"android_log_{keyword}_time_filtered.txt"
    # print(f"[INFO] 提取包含 {keyword} 且时间在 [{start_time_str} ~ {end_time_str}] 的行，输出到：{out_file}")

    count = 0
    with out_file.open("w", encoding="utf-8") as out:
        for adir in android_dirs:
            for f in adir.rglob("*"):
                if not f.is_file():
                    continue
                if f.suffix.lower() == ".gz":
                    continue

                try:
                    rel_path = f.relative_to(unzip_root)
                    with f.open("r", encoding="utf-8", errors="ignore") as fin:
                        for lineno, line in enumerate(fin, 1):
                            if not (
                                str(keyword) in line
                                and ("BoschVehicleHal" in line or "VehicleClient" in line)
                            ):
                                continue
                            ts = parse_log_time(line, default_year=2025)
                            if ts is None:
                                continue
                            if start_time <= ts <= end_time:
                                # 如果你想带上文件路径和行号，可以改成：
                                # out.write(f"{rel_path}:{lineno}: {line}")
                                out.write(f"{line}")
                                count += 1
                except Exception as e:
                    print(f"[ERROR] 读取文件失败：{f}，原因：{e}")

    print(f"[INFO] 提取完成，共找到 {count} 行满足条件。")
    return out_file


# --------------------- 步骤 3：qnx_log / cycle_N / Bosch*.zip ---------------------

def find_qnx_dirs(unzip_root: Path) -> List[Path]:
    """
    在 unzip_root 下查找所有包含 qnx_log 的目录。
    """
    return [d for d in unzip_root.rglob("*") if d.is_dir() and "qnx_log" in d.name]


def find_largest_cycle_dir(qnx_dir: Path) -> Optional[Path]:
    """
    在 qnx_dir 下查找名字为 cycle_数字 的子目录，返回数字最大的那个。
    """
    _cycle_re = re.compile(r"^cycle_(\d+)$")
    candidates = []
    for child in qnx_dir.iterdir():
        if child.is_dir():
            m = _cycle_re.match(child.name)
            if m:
                num = int(m.group(1))
                candidates.append((num, child))
    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    largest = candidates[0][1]
    return largest


def unzip_bosch_zips_in_qnx_logs(unzip_root: Path) -> None:
    """
    在 unzip_root 下查找包含 "qnx_log" 的目录，
    对每个这样的目录：
      - 找到其中 cycle_数字 子目录中的数字最大者
      - 在该目录中解压所有以 Bosch 开头的 zip 文件
    """
    qnx_dirs = [d for d in unzip_root.rglob("*") if d.is_dir() and "qnx_log" in d.name]
    if not qnx_dirs:
        print(f"[WARN] 未找到 qnx_log 目录：{unzip_root}")
        return

    for qdir in qnx_dirs:
        print(f"[INFO] 处理 qnx_log 目录：{qdir}")
        largest_cycle = find_largest_cycle_dir(qdir)
        if not largest_cycle:
            print(f"[WARN] qnx_log 下未找到 cycle_数字 目录：{qdir}")
            continue

        print(f"[INFO] 选中的最大 cycle 目录：{largest_cycle}")
        bosch_zips = [
            f for f in largest_cycle.iterdir()
            if f.is_file() and f.name.startswith("Bosch") and f.suffix.lower() == ".zip"
        ]

        if not bosch_zips:
            print(f"[WARN] 在 {largest_cycle} 下未找到 Bosch*.zip 文件")
            continue

        for z in bosch_zips:
            try:
                print(f"[INFO] 解压 Bosch ZIP：{z}")
                with zipfile.ZipFile(z, "r") as zf:
                    zf.extractall(path=largest_cycle)
                print(f"[OK] 解压完成：{z.name}")
            except Exception as e:
                print(f"[ERROR] 解压 Bosch ZIP 失败：{z}，原因：{e}")


def extrace_lines_with_keyword_in_qnx_logs(
    unzip_root: Path,
    keyword: str = "559992853",
    start_time_str: str = "2025-11-20 06:22:09",
    end_time_str: str = "2025-11-20 06:22:09",
) -> Optional[Path]:
    """
    在 qnx_log 目录中扫描所有文件， 排除 .gz，
    提取包含 keyword 的行，且在时间 [start, end] 之间。

    保存在：
        unzip_root/qnx_log_<keyword>_time_filtered.txt
    """
    qnx_dirs = find_qnx_dirs(unzip_root)
    if not qnx_dirs:
        print(f"[WARNING] not find any qnx_log dir {unzip_root}")
        return None

    if start_time_str is None or start_time_str is None:
        print(f"[ERROR] start_time end_time is none")
        return None

    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

    out_file = unzip_root / f"qnx_log_{keyword}_time_filtered.txt"
    print(f"[INFO] extract {keyword} in qnx_log between {start_time_str} ~ {end_time_str}, output: {out_file}")

    count = 0
    with out_file.open("w", encoding="utf-8") as out:
        for qdir in qnx_dirs:
            for f in qdir.rglob("*"):
                if not f.is_file():
                    continue
                if f.suffix.lower() == ".gz":
                    continue
                try:
                    rel_path = f.relative_to(unzip_root)
                    with f.open("r", encoding="utf-8", errors="ignore") as fin:
                        for lineno, line in enumerate(fin, 1):
                            if str(keyword) not in line:
                                continue
                            ts = parse_log_time(line, default_year=2025)
                            if ts is None:
                                continue
                            if start_time <= ts <= end_time:
                                # 同样，如果要带路径+行号，这里可以写成：
                                # out.write(f"{rel_path}:{lineno}: {line}")
                                out.write(f"{line}")
                                count += 1
                except Exception as e:
                    print(f"[ERROR] read qnx log error : {f}, {e}")
    print(f"[INFO] extract qnx_log finished, total: {count}")
    return out_file


def extract_lines_with_keyword_in_qnx_logs(
    unzip_root: Path,
    keyword: str = "559992853",
    start_time_str: str = "2025-11-20 06:22:09",
    end_time_str: str = "2025-11-20 06:22:09",
) -> Optional[Path]:
    """给外部用的名字比较顺的别名。"""
    return extrace_lines_with_keyword_in_qnx_logs(
        unzip_root=unzip_root,
        keyword=keyword,
        start_time_str=start_time_str,
        end_time_str=end_time_str,
    )



# --------------------- 给 pipeline 用的统一入口 ---------------------

def process_zip_packages_for_pipeline(
    root_dir: str  = "./zip_package",
    android_keywords: str  = "559992853",
    android_start_time: str = "2025-11-20 06:22:09",
    android_end_time: str = "2025-11-20 06:22:11",
    qnx_keywords: str  = "0X214002D7",
    qnx_start_time: str = "2023-01-01 00:00:00",
    qnx_end_time: str = "2023-01-01 04:29:11",
) -> Dict[Path, Dict[str, Dict[str, Optional[Path]]]]:
    """
    给 pipeline 调用的统一入口（支持多个关键字；允许 android/qnx 传 None 表示不处理）。

    返回结构：
      {
        unzip_root1: {
          "android": { "kw1": Path 或 None, ... }  # 如果 android_keywords 为 None，这里是 {}
          "qnx":     { "kwA": Path 或 None, ... }, # 如果 qnx_keywords 为 None，这里是 {}
        },
        ...
      }
    """
    root_path = Path(root_dir)
    if not root_path.exists():
        raise FileNotFoundError(f"root_dir 不存在：{root_path}")

    # --- 关键：容错处理 None + 字符串/可迭代 ---

    if android_keywords is None:
        android_kw_list: list[str] = []
    elif isinstance(android_keywords, str):
        android_kw_list = [android_keywords]
    else:
        android_kw_list = list(android_keywords)

    if qnx_keywords is None:
        qnx_kw_list: list[str] = []
    elif isinstance(qnx_keywords, str):
        qnx_kw_list = [qnx_keywords]
    else:
        qnx_kw_list = list(qnx_keywords)

    print(f"[INFO] pipeline: 开始处理目录：{root_path.resolve()}")

    unzip_dirs = extract_all_archives(root_path)
    results: Dict[Path, Dict[str, Dict[str, Optional[Path]]]] = {}

    for d in unzip_dirs:
        print(f"\n========== pipeline 处理解压目录：{d} ==========")

        # 0. 递归解所有 *.tgz（包含 android_log.tgz / nfs_log.tgz 等）
        extract_tgz_recursively_in_dir(d)

        # 1. android_log 下解压 .gz（即使 android_kw_list 为空，也没关系，解了没坏处）
        if android_kw_list:
            decompress_gz_in_android_logs(d)

        # 2. android_log 下提取多个关键字
        android_out_map: Dict[str, Optional[Path]] = {}
        for kw in android_kw_list:
            android_out = extract_lines_with_keyword_in_android_logs(
                d,
                keyword=kw,
                start_time_str=android_start_time,
                end_time_str=android_end_time,
            )
            android_out_map[kw] = android_out

        # 3. qnx_log 下处理 Bosch*.zip
        if qnx_kw_list:
            unzip_bosch_zips_in_qnx_logs(d)

        # 4. qnx_log 下提取多个关键字
        qnx_out_map: Dict[str, Optional[Path]] = {}
        for kw in qnx_kw_list:
            qnx_out = extrace_lines_with_keyword_in_qnx_logs(
                d,
                keyword=kw,
                start_time_str=qnx_start_time,
                end_time_str=qnx_end_time,
            )
            qnx_out_map[kw] = qnx_out
        results[d] = {
            "android": android_out_map,
            "qnx": qnx_out_map,
        }

    print("\n[DONE] pipeline: 所有压缩包及日志后处理完成。")
    return results

# --------------------- 主流程（命令行直接运行时用） ---------------------

def main() -> None:
    if not ROOT.exists():
        print(f"[ERROR] 目录不存在：{ROOT}")
        return

    # 这里用你当前调试用的参数
    results = process_zip_packages_for_pipeline(
        root_dir=str(ROOT),
        android_keywords="557895757",
        android_start_time="2023-01-01 00:03:00",
        android_end_time="2026-01-20 04:29:11",
        qnx_keywords="0X214002D7",
        qnx_start_time="2023-01-01 00:00:00",
        qnx_end_time="2026-01-20 04:29:11",
    )
    print(f"results:\n{str(results)}")
    if not results:
        print(f"[ERROR] 日志提取结果不存在")


if __name__ == "__main__":
    main()
