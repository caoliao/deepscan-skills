---
name: deepscan-create-task
description: 创建新的扫码本。当用户说"新建扫码本"、"创建扫码本"、"新增一个扫码本"等时触发。
---

# DeepScan 创建扫码本

所有脚本路径相对于本 Skill 目录。

**前置条件**：需要已登录（参考 deepscan-login Skill）。

## 交互流程

### Step 1：获取扫码本名称

如果用户已在对话中提供名称，直接使用；否则询问用户：

> 请输入新扫码本的名称：

### Step 2：创建扫码本

```bash
python scripts/create_task.py create "{扫码本名称}"
```

成功返回示例：

```json
{
  "task_id": "019cb178-a26e-7594-b66f-0fdd827e1705",
  "task_title": "我的新扫码本",
  "description": "",
  "record_count": 0,
  "switched": false
}
```

告知用户：扫码本「{task_title}」已创建成功。

### Step 3：询问是否切换

创建完成后，询问用户：

> 是否立即切换到新扫码本「{task_title}」开始使用？

- **是** → 执行切换并清除旧批次：

  ```bash
  python scripts/create_task.py create "{扫码本名称}" --switch
  ```

  切换成功后告知用户，并提示可以开始添加记录或开启新批次。

- **否** → 保持当前扫码本不变，告知用户可随时通过 deepscan-task Skill 切换。

## 可选：附带描述

如果用户提供了描述信息：

```bash
python scripts/create_task.py create "{名称}" --description "{描述}"
```

## 错误处理

- **未登录**：引导用户执行 deepscan-login Skill 完成登录。
- **名称为空**：提示用户必须提供扫码本名称。
