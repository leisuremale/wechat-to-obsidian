# WeChat to Obsidian

> 一键将微信公众号文章转为 Markdown，自动存入 Obsidian 0-INBOX

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-WeChat-green)]()
[![Obsidian](https://img.shields.io/badge/Obsidian-ready-7C3AED)]()

## 为什么选这个 Skill？

市面上已有不少微信公众号文章转换工具，这个 Skill 针对**日常轻度使用、Obsidian 深度用户**做了专门优化：

### 🆚 对比现有方案

| | 本 Skill | `wechat-article-to-markdown` (★603) | `wechat-article-for-ai` (★60) | `wechat-article-to-md` (★15) |
|---|---|---|---|---|
| **无需浏览器** | ✅ | ❌ Camoufox/Playwright | ❌ Camoufox | ✅ |
| **安装体积** | 🟢 ~5MB | 🔴 ~500MB+ | 🔴 ~500MB+ | 🟢 ~5MB |
| **直存 Obsidian vault** | ✅ 自动写入 inbox | ⚠️ 需手动搬运 | ⚠️ 需配置 | ⚠️ 需指定参数 |
| **依赖数量** | 3 个轻量包 | 10+ 含浏览器内核 | 10+ 含浏览器内核 | 2 个 |
| **AI Agent 集成** | ✅ SKILL.md | ❌ | ✅ MCP Server | ✅ SKILL.md |
| **噪音清理** | ✅ 自动 | ❌ | ❌ | ❌ |

### ✨ 核心优势

1. **极简轻量** — 不用浏览器、不装 Playwright/Camoufox。三个轻量 Python 包搞定，安装体积不到 5MB（其他方案动辄 500MB+）

2. **直存本地或云端 Obsidian** — 直接写入你的 Obsidian vault 的 0-INBOX 目录，无论 vault 在本地磁盘还是 iCloud/OneDrive 等云端同步盘，一篇文章一个 .md 文件，无需手动搬运

3. **几乎零配置** — 不用填 API Key，不用配 MCP Server。只需改一行 vault 路径即可使用

4. **AI Agent 友好** — 专为 Claude Code / OpenClaw 设计的 SKILL.md，AI 助手可直接理解并执行

5. **噪音智能清理** — 自动去除微信公众号的"预览时标签不可点"、"继续滑动看下一个"等干扰文本

6. **结构化输出** — YAML frontmatter 包含标题、作者、发布日期、来源 URL、标签，Dataview 友好

### 设计哲学

不做"大而全"，做"够用且好用"：

- **不用浏览器** → 少量使用无反爬需求，省下 500MB 安装空间
- **图片不下载** → 保留 CDN 链接，Obsidian 在线阅读无压力
- **不追求 100% 还原** → 追求 90% 场景下的 100% 可靠

适合人群：每周存几篇公众号文章到 Obsidian 知识库的普通用户。

## 安装

```bash
# 1. 克隆到 skills 目录
# OpenClaw
git clone https://github.com/leisuremale/wechat-to-obsidian.git \
  ~/.openclaw/workspace/skills/wechat-to-obsidian

# Claude Code
git clone https://github.com/leisuremale/wechat-to-obsidian.git \
  ~/.claude/skills/wechat-to-obsidian

# 2. 安装依赖
pip3 install requests beautifulsoup4 markdownify
```

## 使用

### AI 对话中使用

```
帮我把这篇文章存到 Obsidian：
https://mp.weixin.qq.com/s/xxxxx
```

### 命令行使用

```bash
# 直接保存到 Obsidian 0-INBOX
python3 scripts/article_to_md.py "https://mp.weixin.qq.com/s/xxxxx"

# 先预览，不保存
python3 scripts/article_to_md.py "https://mp.weixin.qq.com/s/xxxxx" --dry-run

# 保存到指定目录
python3 scripts/article_to_md.py "https://mp.weixin.qq.com/s/xxxxx" -o ~/Desktop/

# 打印到终端
python3 scripts/article_to_md.py "https://mp.weixin.qq.com/s/xxxxx" --print
```

## 输出示例

```markdown
---
title: "AI 时代的个人知识管理"
source_url: https://mp.weixin.qq.com/s/xxxxx
platform: wechat
author: 腾讯研究院
publish_date: 2026-04-15
saved_date: 2026-05-01
tags: [inbox, article]
---

# AI 时代的个人知识管理

> 原文链接: https://mp.weixin.qq.com/s/xxxxx

正文内容，格式整洁，图片保留 CDN 链接...
```

文件保存为：`0-INBOX/2026-04-15_AI时代的个人知识管理.md`

## ⚙️ 配置（首次使用必读）

> **⚠️ 使用前必须修改 Obsidian vault 路径！** 脚本内置的是我个人的 iCloud vault 路径，不修改会存到错误位置。

编辑 `scripts/article_to_md.py`，修改顶部的配置：

```python
# 改成你自己的 Obsidian vault 根目录
OBSIDIAN_VAULT = os.path.expanduser("~/Documents/MyObsidianVault")

# vault 内的 inbox 子目录（不改也行）
INBOX_DIR = os.path.join(OBSIDIAN_VAULT, "0-INBOX")
```

常见 vault 路径参考：

| 场景 | 路径示例 |
|------|---------|
| 本地 vault | `~/Documents/MyVault` |
| iCloud vault | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/你的vault名` |
| Obsidian Sync | `~/Documents/你的vault名` |

## 项目结构

```
wechat-to-obsidian/
├── SKILL.md              # AI Agent 指令文件
├── README.md             # 本文件
├── .gitignore
└── scripts/
    └── article_to_md.py  # 核心转换脚本
```

## 依赖

- Python 3.9+
- `requests` — HTTP 请求
- `beautifulsoup4` — HTML 解析
- `markdownify` — HTML → Markdown

## 局限性

- 微信付费文章、已删除文章无法抓取
- 频繁请求可能触发微信反爬（少量使用无影响）
- 图片保留 CDN 链接，不下载到本地（离线不可见）

## License

MIT
