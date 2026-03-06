"""DeepScan RecordList 查询脚本 - 获取当前扫码本的扫码记录列表"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

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


def _require_task(config: dict) -> tuple[str, str]:
    task_id = config.get("task_id")
    if not task_id:
        _output({"error": "尚未选择扫码本，请先执行 deepscan-task Skill 选择扫码本"}, 1)
    return task_id, config.get("task_title", "")


def _fmt_time(iso_str: str) -> str:
    """将 ISO 8601 时间字符串转为本地可读格式"""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_str


def _extract_field(fields: list, field_key: str):
    """从 fields 数组中提取指定 fieldKey 的值"""
    for f in fields:
        if f.get("fieldKey") == field_key:
            return f.get("fieldValue", "")
    return ""


def _simplify_record(record: dict, sessions: dict) -> dict:
    """将原始 record 精简为展示用数据"""
    fields = record.get("fields", [])
    session_id = record.get("sessionId", "")
    session_info = sessions.get(session_id, {})

    return {
        "id": record["id"],
        "seq_number": record.get("readableSeqNumber", f"R{record.get('seqNumber', '')}"),
        "scan_result": _extract_field(fields, "scanResult"),
        "scan_type": _extract_field(fields, "scanType"),
        "remark": _extract_field(fields, "remark"),
        "created_at": _fmt_time(record.get("createdAt", "")),
        "session_id": session_id,
        "session_name": session_info.get("name", ""),
    }


def list_records(page_size: int = 20, page_token: str = "", session_id: str = ""):
    """获取当前扫码本的扫码记录列表"""
    token = _load_token()
    config = _load_config()
    task_id, task_title = _require_task(config)

    payload = {
        "taskId": task_id,
        "pagination": {
            "pageSize": page_size,
            "pageToken": page_token,
        },
        "orderBy": {"updatedAt": "desc"},
    }

    if session_id:
        payload["sessionId"] = session_id

    try:
        resp = requests.post(
            f"{BASE_URL}/api/records/getListByTaskId",
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
    raw_records = data.get("records", [])
    sessions = data.get("sessions", {})

    records = [_simplify_record(r, sessions) for r in raw_records]

    _output({
        "task_id": task_id,
        "task_title": task_title,
        "records": records,
        "total": data.get("total", len(records)),
        "has_more": data.get("hasMore", False),
        "next_page_token": data.get("nextPageToken") or "",
    })


def main():
    parser = argparse.ArgumentParser(description="DeepScan RecordList 查询工具")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="获取当前扫码本的扫码记录列表")
    list_parser.add_argument("--page-size", type=int, default=20, help="每页条数（默认 20）")
    list_parser.add_argument("--page-token", default="", help="翻页 token（留空取第一页）")
    list_parser.add_argument("--session-id", default="", help="按批次 ID 过滤（可选）")

    args = parser.parse_args()

    if args.command == "list":
        list_records(
            page_size=args.page_size,
            page_token=args.page_token,
            session_id=args.session_id,
        )


if __name__ == "__main__":
    main()
