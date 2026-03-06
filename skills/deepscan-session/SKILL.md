---
name: deepscan-session
description: 为当前扫码本开启新批次（session）。当用户说"开启新批次"、"新建批次"、"开始新一批"、"重新开始"、"开启新会话"，或切换扫码本后需要开启新上下文时触发。
---

# DeepScan 批次管理

所有脚本路径相对于本 Skill 目录。

**前置条件**：需要已登录且已选择扫码本（参考 deepscan-login、deepscan-task Skill）。

## 场景一：查看当前批次

```bash
python scripts/session.py current
```

- 成功返回 → 告知用户当前正在进行的批次名称和所属扫码本。
- 退出码为 1 → 尚无批次，需要创建。

## 场景二：开启新批次

用户说"开启新批次"/"新建批次"/"重新开始"时执行：

```bash
python scripts/session.py create
```

返回示例：

```json
{
  "session_id": "019cade8-4f13-7d6c-8930-2690fcc242f4",
  "session_name": "20260302173648扫描列表",
  "task_id": "019c30a1-d44f-7378-a373-6f7e77e4fd25",
  "task_title": "默认扫码本"
}
```

告知用户：已在扫码本「{task_title}」下开启新批次「{session_name}」，可以开始添加扫码记录。

## 配置文件

批次信息存储在 `~/.deepscan/config.json`：

```json
{
  "task_id": "...",
  "task_title": "...",
  "session_id": "019cade8-4f13-7d6c-8930-2690fcc242f4",
  "session_name": "20260302173648扫描列表"
}
```

其他 Skill 获取当前批次 ID 时执行：

```bash
python scripts/session.py current
```
