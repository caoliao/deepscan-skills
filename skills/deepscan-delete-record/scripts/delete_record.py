"""DeepScan Delete Record 脚本 - 支持删除最新记录或按序号/索引删除"""

import argparse
import json
import os
import sys
from datetime import datetime

import requests

BASE_URL = "https://data.cli.im/x-deepscan"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".deepscan")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
TOKEN_PATH = os.path.join(CONFIG_DIR, "token")
RECORDS_CACHE_PATH = os.path.join(CONFIG_DIR, "records_cache.json")


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
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_str


def _extract_field(fields: list, field_key: str):
    for f in fields:
        if f.get("fieldKey") == field_key:
            return f.get("fieldValue", "")
    return ""


def _fetch_records(token: str, task_id: str, page_size: int = 20) -> tuple[list, dict]:
    """从接口拉取记录列表，返回 (raw_records, sessions)"""
    payload = {
        "taskId": task_id,
        "pagination": {"pageSize": page_size, "pageToken": ""},
        "orderBy": {"updatedAt": "desc"},
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/api/records/getListByTaskId",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        _output({"error": f"请求记录列表失败: {e}"}, 1)

    body = resp.json()
    if body.get("code") != 1 or "data" not in body:
        _output({"error": "接口返回异常", "raw": body}, 1)

    data = body["data"]
    return data.get("records", []), data.get("sessions", {})


def _simplify_record(record: dict, sessions: dict) -> dict:
    fields = record.get("fields", [])
    session_id = record.get("sessionId", "")
    session_name = sessions.get(session_id, {}).get("name", "")
    return {
        "id": record["id"],
        "seq_number": record.get("readableSeqNumber", f"R{record.get('seqNumber', '')}"),
        "scan_result": _extract_field(fields, "scanResult"),
        "scan_type": _extract_field(fields, "scanType"),
        "remark": _extract_field(fields, "remark"),
        "created_at": _fmt_time(record.get("createdAt", "")),
        "session_id": session_id,
        "session_name": session_name,
    }


def _save_cache(records: list, task_id: str, task_title: str):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    cache = {
        "task_id": task_id,
        "task_title": task_title,
        "cached_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "records": records,
    }
    with open(RECORDS_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _load_cache() -> dict:
    if not os.path.exists(RECORDS_CACHE_PATH):
        return {}
    with open(RECORDS_CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _do_delete(token: str, record_id: str) -> dict:
    """调用删除接口，返回被删除的记录数据"""
    try:
        resp = requests.post(
            f"{BASE_URL}/api/records/deleteById",
            json={"recordId": record_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        _output({"error": f"删除请求失败: {e}"}, 1)

    body = resp.json()
    if body.get("code") != 1 or "data" not in body:
        _output({"error": "删除接口返回异常", "raw": body}, 1)

    return body["data"]


# ── 子命令实现 ──────────────────────────────────────────────────────────────

def cmd_list(page_size: int):
    """拉取最新记录列表并缓存，供后续删除操作使用"""
    token = _load_token()
    config = _load_config()
    task_id, task_title = _require_task(config)

    raw_records, sessions = _fetch_records(token, task_id, page_size)
    records = [_simplify_record(r, sessions) for r in raw_records]

    _save_cache(records, task_id, task_title)

    _output({
        "task_id": task_id,
        "task_title": task_title,
        "records": records,
        "total_fetched": len(records),
        "cached": True,
    })


def cmd_delete_latest():
    """获取最新一条记录并删除"""
    token = _load_token()
    config = _load_config()
    task_id, task_title = _require_task(config)

    raw_records, sessions = _fetch_records(token, task_id, page_size=1)
    if not raw_records:
        _output({"error": f"扫码本「{task_title}」暂无记录"}, 1)

    target = _simplify_record(raw_records[0], sessions)
    _do_delete(token, target["id"])

    _output({
        "deleted": True,
        "record_id": target["id"],
        "seq_number": target["seq_number"],
        "scan_result": target["scan_result"],
        "task_title": task_title,
    })


def cmd_delete(record_id: str = "", seq: str = "", index: int = 0):
    """按 record_id / seq_number / 列表索引删除"""
    token = _load_token()

    if record_id:
        pass
    elif seq or index:
        cache = _load_cache()
        records = cache.get("records", [])
        if not records:
            _output({"error": "本地缓存为空，请先执行 list 命令获取记录列表"}, 1)

        if seq:
            matched = [r for r in records if r["seq_number"].upper() == seq.upper()]
            if not matched:
                _output({"error": f"未在缓存中找到序号 {seq}，请先执行 list 命令刷新列表"}, 1)
            record_id = matched[0]["id"]
            seq_number = matched[0]["seq_number"]
            scan_result = matched[0]["scan_result"]
        else:
            if index < 1 or index > len(records):
                _output({"error": f"索引 {index} 超出范围（共 {len(records)} 条记录）"}, 1)
            target = records[index - 1]
            record_id = target["id"]
            seq_number = target["seq_number"]
            scan_result = target["scan_result"]
    else:
        _output({"error": "请指定 --id、--seq 或 --index 参数"}, 1)

    _do_delete(token, record_id)

    _output({
        "deleted": True,
        "record_id": record_id,
        "seq_number": seq_number if (seq or index) else "",
        "scan_result": scan_result if (seq or index) else "",
    })


def main():
    parser = argparse.ArgumentParser(description="DeepScan Delete Record 工具")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="列出最新记录并缓存")
    list_parser.add_argument("--page-size", type=int, default=20, help="获取条数（默认 20）")

    sub.add_parser("delete-latest", help="删除最新一条记录")

    del_parser = sub.add_parser("delete", help="按 ID / 序号 / 索引删除记录")
    del_parser.add_argument("--id", dest="record_id", default="", help="记录 ID")
    del_parser.add_argument("--seq", default="", help="序号，如 R3")
    del_parser.add_argument("--index", type=int, default=0, help="列表中的 1-based 序位")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args.page_size)
    elif args.command == "delete-latest":
        cmd_delete_latest()
    elif args.command == "delete":
        cmd_delete(
            record_id=args.record_id,
            seq=args.seq,
            index=args.index,
        )


if __name__ == "__main__":
    main()
