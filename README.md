[English](README.md) | [中文](README.zh-cn.md)

# Caoliao DeepScan Skills

A collection of Agent Skills for [Caoliao DeepScan](https://cli.im) — manage scan logs through conversational AI. Works with Cursor, OpenClaw, and other agents that support the Agent Skills standard.

---

> **⚠ Please read before use**
>
> 1. **Token security**: After login, the Token is stored as a plain-text file on your machine. It carries full account permissions — do not share it or commit it to a repository. Also review access permissions of other Skills / Rules to prevent token leakage.
> 2. **Use with caution**: Skill execution quality depends heavily on the underlying model. **Destructive operations like deleting records are irreversible** — always confirm before proceeding.

---

## Installation

### Option 1: via npx skills (recommended)

```bash
npx skills add caoliao/deepscan-skills
```

Follow the prompts to select the skills you need. You can also install specific skills:

```bash
npx skills add caoliao/deepscan-skills --skill deepscan-login --skill deepscan-record
```

Install all skills at once:

```bash
npx skills add caoliao/deepscan-skills --all
```

### Option 2: Clone the repository

```bash
git clone https://github.com/caoliao/deepscan-skills.git
```

### Dependencies

- Python 3.8+
- Install requirements: `pip install -r requirements.txt`

## Features

| Feature | Trigger examples |
|---------|-----------------|
| Login | "Log in to DeepScan", "Re-login" |
| Create scan book | "Create a new scan book", "Create one called XX" |
| View / switch scan book | "My scan books", "Switch to XX", "List scan books" |
| Start new batch | "Start a new batch", "New batch", "Start over" |
| Add scan record | Send text or upload an image containing a QR code |
| View records | "Show records", "Scan history", "What did I scan" |
| Delete record | "Delete the latest record", "Delete #2" |
| Export records | "Export scan book", "Export Excel", "Download data" |

## Quick Start

A typical conversation flow, step by step:

---

**Step 1: Log in**

> "Log in to DeepScan"

The agent will generate a login QR code. Scan it with WeChat to complete authorization.

---

**Step 2: Select a scan book**

> "Show my scan books" / "Switch to XXX"

The agent lists all your scan books — just tell it which one to use.

---

**Step 3: Add scan records**

Send text or an image with a QR code:

> "https://cli.im"
>
> (or upload an image containing a QR code)

Text is added directly as the scan content; images are decoded automatically.

---

**Step 4 (optional): Start a new batch**

If you need to separate records into batches:

> "Start a new batch"

Subsequent records will belong to the new batch for easier grouping.

---

For more management features (export, delete, history, etc.) visit the **Caoliao DeepScan** WeChat Mini Program.

---
