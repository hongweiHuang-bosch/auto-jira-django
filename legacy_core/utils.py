from __future__ import annotations
import os
import yaml
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s"
    )

def load_config(config_path="config.yaml"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件 {config_path} 不存在！")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_issue_text_file(path: str, issue:str, content: str):
    try:
        # 构造 comment 子目录路径
        comment_dir = os.path.join(os.getcwd(), f"comment/{issue}")
        os.makedirs(comment_dir, exist_ok=True)

        # 获取文件名并拼接到 comment/ 下
        filename = os.path.basename(path)
        new_path = os.path.join(comment_dir, filename)

        with open(new_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        logging.getLogger("CAN-AI-JIRA").warning(f"写文件失败 {path}: {e}")

def write_model_issue_text_file(model:str, path: str, issue:str, content: str):
    try:
        # 构造 comment 子目录路径
        comment_dir = os.path.join(os.getcwd(), f"comment/{model}/{issue}")
        os.makedirs(comment_dir, exist_ok=True)

        # 获取文件名并拼接到 comment/ 下
        filename = os.path.basename(path)
        new_path = os.path.join(comment_dir, filename)

        with open(new_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        logging.getLogger("CAN-AI-JIRA").warning(f"写文件失败 {path}: {e}")
