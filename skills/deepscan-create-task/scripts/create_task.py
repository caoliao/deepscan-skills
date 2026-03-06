"""DeepScan Create Task 脚本 - 创建新扫码本"""

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


def cmd_create(title: str, description: str = "", switch: bool = False):
    token = _load_token()

    payload = {
        "task": {
            "title": title,
            "description": description,
            "mode": 2,
        },
        "options": {"forceNew": True},
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/api/tasks/init",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        _output({"error": f"创建扫码本失败: {e}"}, 1)

    body = resp.json()
    if body.get("code") != 1 or "data" not in body:
        _output({"error": "接口返回异常", "raw": body}, 1)

    task = body["data"]
    task_id = task["id"]
    task_title = task.get("title", title)

    if switch:
        config = _load_config()
        config["task_id"] = task_id
        config["task_title"] = task_title
        config.pop("session_id", None)
        config.pop("session_name", None)
        _save_config(config)

    _output({
        "task_id": task_id,
        "task_title": task_title,
        "description": task.get("description", ""),
        "record_count": task.get("recordCount", 0),
        "switched": switch,
    })


def main():
    parser = argparse.ArgumentParser(description="DeepScan Create Task 工具")
    sub = parser.add_subparsers(dest="command", required=True)

    create_parser = sub.add_parser("create", help="创建新扫码本")
    create_parser.add_argument("title", help="扫码本名称")
    create_parser.add_argument("--description", default="", help="扫码本描述（可选）")
    create_parser.add_argument("--switch", action="store_true", help="创建后立即切换到该扫码本")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args.title, args.description, args.switch)


if __name__ == "__main__":
    main()
