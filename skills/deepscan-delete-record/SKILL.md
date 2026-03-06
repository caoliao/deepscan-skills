---
name: deepscan-delete-record
description: 删除扫码本中的扫码记录。当用户说"删除记录"、"删掉最新的"、"撤销上一条"、"删第几条"等时触发。
---

# DeepScan 删除扫码记录

所有脚本路径相对于本 Skill 目录。

**前置条件**：需要已登录、已选择扫码本（参考 deepscan-login、deepscan-task Skill）。

记录列表缓存路径：`~/.deepscan/records_cache.json`

---

## 场景一：用户明确说"删除最新记录"

直接拉取最新一条记录并删除，无需用户二次确认：

```bash
python scripts/delete_record.py delete-latest
```

成功返回示例：

```json
{
  "deleted": true,
  "record_id": "019cb14d-...",
  "seq_number": "R3",
  "scan_result": "https://qr71.cn/o2eikt/qGkeF3M",
  "task_title": "默认扫码本"
}
```

告知用户：已删除扫码本「{task_title}」中的最新记录 {seq_number}（内容：{scan_result}）。

---

## 场景二：用户未明确指定哪条记录

**Step 1**：拉取最新 20 条记录并缓存到本地：

```bash
python scripts/delete_record.py list
```

返回 `records` 数组后，以编号列表展示给用户：

> 扫码本「{task_title}」最近的记录，请告诉我要删除第几条：
>
> 1. R3 | 2026-03-03 09:26 | https://qr71.cn/...
> 2. R2 | 2026-03-03 09:23 | 123321
> 3. R1 | 2026-03-02 22:02 | https://cli.im

**Step 2**：用户回复后（如"删第 2 条"或"删 R2"），执行删除：

按列表编号删除（1-based）：
```bash
python scripts/delete_record.py delete --index 2
```

按序号删除：
```bash
python scripts/delete_record.py delete --seq R2
```

成功返回示例：

```json
{
  "deleted": true,
  "record_id": "019cb14b-...",
  "seq_number": "R2",
  "scan_result": "123321"
}
```

告知用户：已删除记录 {seq_number}（内容：{scan_result}）。

---

## 场景三：已知 record ID

直接传入 ID 删除：

```bash
python scripts/delete_record.py delete --id "{record_id}"
```

---

## 缓存说明

- `list` 命令执行后，结果会自动保存到 `~/.deepscan/records_cache.json`
- `delete --seq` 和 `delete --index` 从缓存中查找对应记录 ID
- 若提示"本地缓存为空"，需先执行 `list` 命令刷新缓存

---

## 错误处理

- **扫码本无记录**：告知用户当前扫码本暂无记录。
- **缓存为空**：执行 `list` 命令后重试。
- **索引/序号不存在**：告知用户编号超出范围，展示 `list` 结果让用户重新选择。
- **未选择扫码本**：引导用户执行 deepscan-task Skill。
