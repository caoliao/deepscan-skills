"""DeepScan Task 管理脚本 - 获取 task 列表并管理当前选中的 task"""

import argparse
import json
import os
import sys

import requests

BASE_URL = "https://data.cli.im/x-deepscan"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".deepscan")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
TOKEN_PATH = os.path.join(CONFIG_DIR, "token")
TASKS_CACHE_PATH = os.path.join(CONFIG_DIR, "tasks_cache.json")


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


def list_tasks():
    """获取 task 列表并缓存到本地"""
    token = _load_token()
    payload = {
        "query": {"mode": 2},
        "pagination": {
            "pageSize": 50,
            "pageToken": "",
            "orderBy": {"updatedAt": "desc"},
        },
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/api/tasks/getList",
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

    tasks = body["data"].get("tasks", [])
    result = []
    for t in tasks:
        result.append({
            "id": t["id"],
            "title": t.get("title", ""),
            "description": t.get("description", ""),
            "record_count": t.get("recordCount", 0),
            "status": t.get("status"),
            "updated_at": t.get("updatedAt", ""),
        })

    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(TASKS_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    _output({"tasks": result, "total": body["data"].get("total", len(result))})


def select_task(task_id: str, title: str = ""):
    """将选中的 task ID 保存到配置文件，清除旧 session"""
    config = _load_config()
    config["task_id"] = task_id
    if title:
        config["task_title"] = title
    config.pop("session_id", None)
    config.pop("session_name", None)
    _save_config(config)
    _output({"selected": True, "task_id": task_id, "task_title": title})


def current_task():
    """读取当前选中的 task"""
    config = _load_config()
    task_id = config.get("task_id")
    if not task_id:
        _output({"error": "尚未选择 task，请先执行 deepscan-task Skill 选择一个 task"}, 1)
    _output({
        "task_id": task_id,
        "task_title": config.get("task_title", ""),
    })


def main():
    parser = argparse.ArgumentParser(description="DeepScan Task 管理工具")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="获取 task 列表（结果缓存至本地）")

    select_parser = sub.add_parser("select", help="选择一个 task（清除旧 session）")
    select_parser.add_argument("task_id", help="task ID")
    select_parser.add_argument("--title", default="", help="task 标题（可选）")

    sub.add_parser("current", help="查看当前选中的 task")

    args = parser.parse_args()

    if args.command == "list":
        list_tasks()
    elif args.command == "select":
        select_task(args.task_id, args.title)
    elif args.command == "current":
        current_task()


if __name__ == "__main__":
    main()
