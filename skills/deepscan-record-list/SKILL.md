---
name: deepscan-record-list
description: 查看当前扫码本的扫码记录列表。当用户问"有哪些记录"、"查看记录"、"历史扫码"、"扫了什么"、"记录列表"等时触发。
---

# DeepScan 查看扫码记录列表

所有脚本路径相对于本 Skill 目录。

**前置条件**：需要已登录、已选择扫码本（参考 deepscan-login、deepscan-task Skill）。

## 前置检查

执行前先确认已选择扫码本：

```bash
python ../deepscan-task/scripts/task.py current
```

- 退出码为 1 → 先执行 deepscan-task Skill 选择扫码本，再继续。
- 成功 → 继续查询记录。

## 查询记录列表

```bash
python scripts/recordlist.py list
```

成功返回示例：

```json
{
  "task_id": "019c30a1-...",
  "task_title": "默认扫码本",
  "records": [
    {
      "id": "019cb14d-...",
      "seq_number": "R3",
      "scan_result": "https://qr71.cn/o2eikt/qGkeF3M",
      "scan_type": "qrcode",
      "remark": "",
      "created_at": "2026-03-03 09:26:28",
      "session_id": "019cb14a-...",
      "session_name": "20260303092317扫描列表"
    }
  ],
  "total": 3,
  "has_more": false,
  "next_page_token": ""
}
```

向用户展示时，用表格或列表形式展示，包含：序号（seq_number）、扫码内容（scan_result）、时间（created_at）、批次（session_name）。

## 可选参数

### 指定每页条数（默认 20）

```bash
python scripts/recordlist.py list --page-size 10
```

### 翻页（使用上一次返回的 next_page_token）

```bash
python scripts/recordlist.py list --page-token "{next_page_token}"
```

### 按批次过滤

如需只看当前批次的记录，先获取当前批次 ID：

```bash
python ../deepscan-session/scripts/session.py current
```

然后过滤：

```bash
python scripts/recordlist.py list --session-id "{session_id}"
```

## 展示格式建议

返回记录后，按以下格式告知用户（以 Markdown 表格或列表展示）：

> 扫码本「{task_title}」共有 {total} 条记录：
>
> | 序号 | 扫码内容 | 时间 | 批次 |
> |------|---------|------|------|
> | R3   | https://... | 2026-03-03 09:26 | 20260303... |

- 若 `has_more` 为 true，提示用户"还有更多记录，可继续翻页查看"。
- 若 `records` 为空列表，告知用户"当前扫码本暂无记录"。

## 错误处理

- **未选择扫码本**：引导用户执行 deepscan-task Skill 选择扫码本。
- **未登录**：引导用户执行 deepscan-login Skill 完成登录。
