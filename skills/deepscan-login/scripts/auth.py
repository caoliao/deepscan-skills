"""DeepScan Agent 认证脚本 - 处理 QR 码扫码登录流程"""

import argparse
import base64
import json
import os
import sys
import tempfile
import time

import requests

BASE_URL = "https://data.cli.im/x-deepscan"
TOKEN_DIR = os.path.join(os.path.expanduser("~"), ".deepscan")
TOKEN_PATH = os.path.join(TOKEN_DIR, "token")


def _output(data: dict, exit_code: int = 0):
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(exit_code)


def initiate():
    """发起授权请求，获取 QR 码并保存为 PNG 文件"""
    try:
        resp = requests.post(f"{BASE_URL}/api/auth/agent/authorize", timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        _output({"error": f"请求失败: {e}"}, 1)

    body = resp.json()
    if body.get("code") != 1 or "data" not in body:
        _output({"error": "接口返回异常", "raw": body}, 1)

    data = body["data"]
    token = data.get("token")
    qrcode_b64 = data.get("qrcodeBase64", "")
    expires_in = data.get("expiresIn", 300)

    qr_path = os.path.join(tempfile.gettempdir(), f"deepscan_qr_{token}.png")
    try:
        raw_b64 = qrcode_b64.split(",", 1)[-1] if "," in qrcode_b64 else qrcode_b64
        with open(qr_path, "wb") as f:
            f.write(base64.b64decode(raw_b64))
    except Exception as e:
        _output({"error": f"QR 码保存失败: {e}"}, 1)

    _output({
        "token": token,
        "auth_url": data.get("authUrl", ""),
        "qrcode_path": qr_path,
        "expires_in": expires_in,
    })


def poll(token: str):
    """查询授权状态，授权成功时返回 apiKey"""
    try:
        resp = requests.get(
            f"{BASE_URL}/api/auth/agent/authorize/{token}", timeout=10
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        _output({"error": f"请求失败: {e}"}, 1)

    body = resp.json()
    if body.get("code") != 1:
        _output({"error": "接口返回异常", "raw": body}, 1)

    data = body.get("data", {})
    authorized = data.get("status") == "authorized"
    result = {"success": authorized}
    if authorized:
        result["api_key"] = data.get("apiKey", "")
    _output(result)


def save_token(token: str):
    """将 token 持久化到本地文件"""
    os.makedirs(TOKEN_DIR, exist_ok=True)
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(token)
    _output({"saved": True, "path": TOKEN_PATH})


def get_token():
    """读取本地保存的 token"""
    if not os.path.exists(TOKEN_PATH):
        _output({"error": "未找到已保存的 token，请先登录"}, 1)
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        token = f.read().strip()
    if not token:
        _output({"error": "token 文件为空，请重新登录"}, 1)
    _output({"token": token})


def status():
    """检查登录状态"""
    if not os.path.exists(TOKEN_PATH):
        _output({"logged_in": False, "message": "未登录"})
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        token = f.read().strip()
    if not token:
        _output({"logged_in": False, "message": "token 为空"})
    _output({"logged_in": True, "token": token})


def main():
    parser = argparse.ArgumentParser(description="DeepScan Agent 认证工具")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("initiate", help="发起授权，获取 QR 码")

    poll_parser = sub.add_parser("poll", help="查询授权状态")
    poll_parser.add_argument("token", help="授权 token")

    save_parser = sub.add_parser("save-token", help="保存 token 到本地")
    save_parser.add_argument("token", help="要保存的 token")

    sub.add_parser("get-token", help="获取已保存的 token")
    sub.add_parser("status", help="检查登录状态")

    args = parser.parse_args()

    if args.command == "initiate":
        initiate()
    elif args.command == "poll":
        poll(args.token)
    elif args.command == "save-token":
        save_token(args.token)
    elif args.command == "get-token":
        get_token()
    elif args.command == "status":
        status()


if __name__ == "__main__":
    main()
