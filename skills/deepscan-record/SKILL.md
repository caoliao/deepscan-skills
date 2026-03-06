---
name: deepscan-record
description: 向当前扫码本的批次中添加扫码记录（record）。当用户发送一段文本或上传一张图片，且没有其他明确意图时自动触发。图片自动解码二维码作为扫描内容，文本直接作为扫描结果。
---

# DeepScan 添加扫码记录

所有脚本路径相对于本 Skill 目录。

**前置条件**：需要已登录、已选择扫码本、已开启批次（参考 deepscan-login、deepscan-task、deepscan-session Skill）。

## 前置检查

执行前先确认批次存在：

```bash
python ../deepscan-session/scripts/session.py current
```

- 退出码为 1 → 先执行 deepscan-task Skill 选择扫码本并开启批次，再继续。
- 成功 → 继续添加。

## 场景一：用户发送文本

```bash
python scripts/record.py add-text "{用户文本内容}"
```

成功返回示例：

```json
{
  "record_id": "019caedb-69bd-...",
  "scan_result": "用户输入的文本",
  "scan_type": "text",
  "seq_number": "R1",
  "task_title": "默认扫码本"
}
```

告知用户：已将内容「{scan_result}」添加到扫码本「{task_title}」（{seq_number}）。

## 场景二：用户上传图片

用 Read 工具获取图片本地路径，然后执行：

```bash
python scripts/record.py add-image "{图片本地路径}"
```

脚本自动完成：
1. 用 `zxing-cpp` 解码图片中的二维码/条码
2. 将图片上传到 OSS 获取 URL
3. 添加扫码记录（扫码内容 + 图片 URL）

成功返回示例：

```json
{
  "record_id": "019caedb-69bd-...",
  "scan_result": "https://cli.im",
  "scan_type": "qrcode",
  "image_url": "https://...",
  "seq_number": "R1",
  "task_title": "默认扫码本"
}
```

告知用户：已添加扫码记录 {seq_number}，内容为「{scan_result}」。

## 错误处理

- **图片中无二维码**：告知用户图片未识别到二维码，可手动输入内容改用文本方式添加。
- **未选择扫码本 / 无批次**：引导用户执行 deepscan-task Skill。
- **缺少依赖**：提示用户执行 `pip install zxing-cpp Pillow`。

## 依赖安装

```bash
pip install zxing-cpp Pillow
```
