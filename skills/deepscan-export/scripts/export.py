"""DeepScan Export 脚本 - 导出当前扫码本记录为 Excel / CSV / TXT"""

import argparse
import json
import os
import sys

import requests

BASE_URL = "https://data.cli.im/x-deepscan"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".deepscan")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
TOKEN_PATH = os.path.join(CONFIG_DIR, "token")

EXPORT_TYPES = {
    "excel": "2",
    "csv": "1",
    "txt": "3",
}


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


def _require_task(config: dict) -> tuple[str, str]:
    task_id = config.get("task_id")
    if not task_id:
        _output({"error": "尚未选择扫码本，请先执行 deepscan-task Skill 选择扫码本"}, 1)
    return task_id, config.get("task_title", "")


def cmd_export(fmt: str):
    export_type = EXPORT_TYPES.get(fmt.lower())
    if not export_type:
        _output({"error": f"不支持的格式 '{fmt}'，可选：excel、csv、txt"}, 1)

    token = _load_token()
    config = _load_config()
    task_id, task_title = _require_task(config)

    payload = {
        "query": {"taskId": task_id},
        "options": {"exportType": export_type},
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/api/records/export",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        _output({"error": f"导出请求失败: {e}"}, 1)

    body = resp.json()
    if body.get("code") != 1 or "data" not in body:
        _output({"error": "接口返回异常", "raw": body}, 1)

    data = body["data"]
    _output({
        "task_id": task_id,
        "task_title": task_title,
        "format": fmt.upper(),
        "file_name": data.get("fileName", ""),
        "file_url": data.get("fileUrl", ""),
        "file_size": data.get("fileSize", 0),
        "record_count": data.get("fileRecordCount", 0),
    })


def main():
    parser = argparse.ArgumentParser(description="DeepScan Export 工具")
    sub = parser.add_subparsers(dest="command", required=True)

    exp_parser = sub.add_parser("export", help="导出扫码本记录")
    exp_parser.add_argument(
        "--format",
        default="excel",
        choices=["excel", "csv", "txt"],
        help="导出格式（默认 excel）",
    )

    args = parser.parse_args()

    if args.command == "export":
        cmd_export(args.format)


if __name__ == "__main__":
    main()
