---
name: deepscan-export
description: 导出当前扫码本的扫码记录为文件。当用户说"导出记录"、"导出扫码本"、"下载数据"、"导出 Excel/CSV"等时触发。
---

# DeepScan 导出扫码记录

所有脚本路径相对于本 Skill 目录。

**前置条件**：需要已登录、已选择扫码本（参考 deepscan-login、deepscan-task Skill）。

## 默认导出（Excel）

```bash
python scripts/export.py export
```

## 指定格式导出

| 格式 | 命令 |
|------|------|
| Excel（默认） | `python scripts/export.py export --format excel` |
| CSV | `python scripts/export.py export --format csv` |
| TXT | `python scripts/export.py export --format txt` |

若用户未指定格式，默认使用 Excel。

## 成功返回示例

```json
{
  "task_id": "019c30a1-...",
  "task_title": "默认扫码本",
  "format": "EXCEL",
  "file_name": "20260303095041扫码记录.xlsx",
  "file_url": "https://cli-deepscan-net.oss-cn-hangzhou.aliyuncs.com/exports/...",
  "file_size": 6802,
  "record_count": 2
}
```

告知用户：已生成导出文件，包含 {record_count} 条记录，[点击下载 {file_name}]({file_url})。

## 错误处理

- **未选择扫码本**：引导用户执行 deepscan-task Skill 选择扫码本。
- **未登录**：引导用户执行 deepscan-login Skill 完成登录。
