---
name: deepscan-task
description: 列出并切换扫码本（task）。当用户说"列出扫码本"、"我的扫码本"、"切换扫码本"、"换一个扫码本"、"查看扫码本列表"，或首次使用但尚未选择扫码本时触发。
---

# DeepScan 扫码本选择

所有脚本路径相对于本 Skill 目录。

**前置条件**：需要已登录（参考 deepscan-login Skill）。

## 流程

### Step 1: 检查当前扫码本

```bash
python scripts/task.py current
```

- 返回 `{"task_id": "...", "task_title": "..."}` → 告知用户当前扫码本名称，询问是否需要切换。
  - 不切换 → 流程结束。
  - 切换 → 继续 Step 2。
- 退出码为 1 → 尚未选择扫码本，继续 Step 2。

### Step 2: 获取扫码本列表

```bash
python scripts/task.py list
```

返回示例：

```json
{
  "tasks": [
    {"id": "019c30a1-...", "title": "默认扫码本", "description": "", "record_count": 5}
  ],
  "total": 1
}
```

列表同时缓存到 `~/.deepscan/tasks_cache.json`，无需重复请求。

如果提示未登录，先执行 deepscan-login Skill 后重试。

### Step 3: 让用户选择

将扫码本列表以编号展示，让用户选择：

- 每项格式：`{title}（共 {record_count} 条记录）`
- 记录用户选择的 `id` 和 `title`

### Step 4: 保存选择

```bash
python scripts/task.py select {task_id} --title "{task_title}"
```

此命令保存扫码本 ID，并自动清除旧批次。

### Step 5: 为新扫码本开启批次

切换扫码本后必须开启新批次：

```bash
python ../deepscan-session/scripts/session.py create
```

告知用户：已切换到扫码本「{task_title}」，并开启新批次「{session_name}」，可以开始添加扫码记录。

## 配置文件

`~/.deepscan/config.json` 中记录当前扫码本和批次信息：

```json
{
  "task_id": "019c30a1-d44f-7378-a373-6f7e77e4fd25",
  "task_title": "默认扫码本",
  "session_id": "019cade8-4f13-7d6c-8930-2690fcc242f4",
  "session_name": "20260302173648扫描列表"
}
```
