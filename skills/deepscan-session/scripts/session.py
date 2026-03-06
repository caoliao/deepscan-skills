"""DeepScan Session 管理脚本 - 创建和管理当前工作 session"""

import argparse
import json
import os
import sys

import requests

BASE_URL = "https://data.cli.im/x-deepscan"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".deepscan")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
TOKEN_PATH = os.path.join(CONFIG_DIR, "token")


def _output(data: dict, exit_code: int = 0):
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(exit_code)


def _load_token() -> str:
    if not os.path.exists(TOKEN_PATH):
        _output({"error": "未登录，请先执行 deepscan-login Skill 完成登录"}, 1)
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        token = f.read().strip()
    if not token:
        _output({"error": "token 为空，请重新登录"}, 1)
    return token


def _load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_config(config: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def create_session():
    """为当前 task 创建新 session"""
    token = _load_token()
    config = _load_config()

    task_id = config.get("task_id")
    if not task_id:
        _output({"error": "尚未选择 task，请先执行 deepscan-task Skill 选择一个 task"}, 1)

    payload = {
        "taskId": task_id,
        "options": {
            "forceNew": True,
            "session": {"config": {}},
        },
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/api/sessions/init",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        _output({"error": f"请求失败: {e}"}, 1)

    body = resp.json()
    if body.get("code") != 1 or "data" not in body:
        _output({"error": "接口返回异常", "raw": body}, 1)

    data = body["data"]
    session_id = data.get("id")
    session_name = data.get("name", "")

    config["session_id"] = session_id
    config["session_name"] = session_name
    _save_config(config)

    _output({
        "session_id": session_id,
        "session_name": session_name,
        "task_id": task_id,
        "task_title": config.get("task_title", ""),
    })


def current_session():
    """读取当前 session"""
    config = _load_config()
    session_id = config.get("session_id")
    if not session_id:
        _output({"error": "尚未创建 session，请先选择 task 或开启新批次"}, 1)
    _output({
        "session_id": session_id,
        "session_name": config.get("session_name", ""),
        "task_id": config.get("task_id", ""),
        "task_title": config.get("task_title", ""),
    })


def main():
    parser = argparse.ArgumentParser(description="DeepScan Session 管理工具")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("create", help="为当前 task 创建新 session")
    sub.add_parser("current", help="查看当前 session")

    args = parser.parse_args()

    if args.command == "create":
        create_session()
    elif args.command == "current":
        current_session()


if __name__ == "__main__":
    main()
