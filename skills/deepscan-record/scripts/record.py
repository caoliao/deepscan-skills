"""DeepScan Record 添加脚本 - 支持文本和图片两种方式添加 record"""

import argparse
import json
import os
import sys
import time

import requests

BASE_URL = "https://data.cli.im/x-deepscan"
FILESERVER_URL = "https://data.cli.im/x-fileserver/api/nencao/requestPostOss"
OSS_UPLOAD_URL = "https://upload-fs.cli.im"

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


def _require_session(config: dict) -> str:
    session_id = config.get("session_id")
    if not session_id:
        _output({"error": "尚未创建 session，请先执行 deepscan-task Skill 选择 task 或开启新批次"}, 1)
    return session_id


def _decode_qrcode(image_path: str) -> tuple[str, str]:
    """解码图片中的二维码/条码，返回 (内容, 类型)。无法解码时返回 ('', 'unknown')"""
    try:
        import zxingcpp
        from PIL import Image
        img = Image.open(image_path)
        results = zxingcpp.read_barcodes(img)
        if results:
            r = results[0]
            fmt = r.format.name.lower()
            scan_type = "barcode" if "qr" not in fmt else "qrcode"
            return r.text, scan_type
    except ImportError:
        _output({"error": "缺少依赖：请执行 pip install zxing-cpp Pillow"}, 1)
    except Exception as e:
        _output({"error": f"二维码解码失败: {e}"}, 1)
    return "", "unknown"


def _upload_image(image_path: str, token: str) -> str:
    """上传图片到 OSS，返回图片 URL"""
    filename = os.path.basename(image_path)

    # Step 1: 请求 OSS 上传参数
    try:
        resp = requests.post(
            FILESERVER_URL,
            json={"biz": 4, "file": {"name": filename}},
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        _output({"error": f"请求上传参数失败: {e}"}, 1)

    body = resp.json()
    if body.get("code") not in (0, 1) or "data" not in body:
        _output({"error": "获取 OSS 上传参数异常", "raw": body}, 1)

    oss = body["data"]["post"]

    # Step 2: 上传文件到 OSS
    try:
        with open(image_path, "rb") as f:
            form_data = {
                "key": oss["objectKey"],
                "Signature": oss["signature"],
                "OSSAccessKeyId": oss["ossAccessKeyId"],
                "callback": oss["callback"],
                "policy": oss["policy"],
                "uuid": (None, ""),
            }
            upload_resp = requests.post(
                OSS_UPLOAD_URL,
                files={**{k: (None, v) for k, v in form_data.items() if k != "uuid"},
                       "uuid": (None, ""),
                       "file": (filename, f)},
                timeout=30,
            )
            upload_resp.raise_for_status()
    except requests.RequestException as e:
        _output({"error": f"图片上传失败: {e}"}, 1)

    upload_body = upload_resp.json()
    file_url = upload_body.get("data", {}).get("file", "")
    if not file_url:
        _output({"error": "上传成功但未获取到文件 URL", "raw": upload_body}, 1)

    return file_url


def _create_record(token: str, session_id: str, scan_result: str,
                   scan_type: str, image_urls: list[str]) -> dict:
    """调用创建 record 接口"""
    local_time = int(time.time() * 1000)
    fields = [
        {"fieldKey": "scanResult", "fieldValue": scan_result},
        {"fieldKey": "scanType",   "fieldValue": scan_type},
        {"fieldKey": "localTime",  "fieldValue": local_time},
        {"fieldKey": "images",     "fieldValue": image_urls},
    ]
    payload = {
        "record": {"sessionId": session_id, "fields": fields},
        "options": {},
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/api/records/create",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        _output({"error": f"创建 record 失败: {e}"}, 1)

    body = resp.json()
    if body.get("code") != 1 or "data" not in body:
        _output({"error": "接口返回异常", "raw": body}, 1)

    return body["data"]


def add_text(text: str):
    """添加文本 record"""
    token = _load_token()
    config = _load_config()
    session_id = _require_session(config)

    record = _create_record(token, session_id, text, "text", [])
    _output({
        "record_id": record["id"],
        "scan_result": text,
        "scan_type": "text",
        "seq_number": record.get("readableSeqNumber", ""),
        "session_id": session_id,
        "task_id": config.get("task_id", ""),
        "task_title": config.get("task_title", ""),
    })


def add_image(image_path: str):
    """解码图片中的二维码并添加 record（图片同步上传）"""
    if not os.path.exists(image_path):
        _output({"error": f"图片文件不存在: {image_path}"}, 1)

    token = _load_token()
    config = _load_config()
    session_id = _require_session(config)

    scan_result, scan_type = _decode_qrcode(image_path)
    if not scan_result:
        _output({"error": "图片中未识别到二维码或条码内容，无法添加 record"}, 1)

    image_url = _upload_image(image_path, token)
    record = _create_record(token, session_id, scan_result, scan_type, [image_url])

    _output({
        "record_id": record["id"],
        "scan_result": scan_result,
        "scan_type": scan_type,
        "image_url": image_url,
        "seq_number": record.get("readableSeqNumber", ""),
        "session_id": session_id,
        "task_id": config.get("task_id", ""),
        "task_title": config.get("task_title", ""),
    })


def main():
    parser = argparse.ArgumentParser(description="DeepScan Record 添加工具")
    sub = parser.add_subparsers(dest="command", required=True)

    text_parser = sub.add_parser("add-text", help="添加文本 record")
    text_parser.add_argument("text", help="要添加的文本内容")

    img_parser = sub.add_parser("add-image", help="从图片解码二维码并添加 record")
    img_parser.add_argument("image_path", help="图片文件路径")

    args = parser.parse_args()

    if args.command == "add-text":
        add_text(args.text)
    elif args.command == "add-image":
        add_image(args.image_path)


if __name__ == "__main__":
    main()
