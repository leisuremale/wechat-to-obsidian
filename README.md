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
| **自动内容标签** | ✅ 关键词匹配 | ❌ | ❌ | ❌ |
| **抓取失败降级** | ✅ 自动保存链接存根 | ❌ | ❌ | ❌ |
| **JSON 驱动配置** | ✅ config.json | ❌ | ❌ | ❌ |
| **最小化 LLM 步骤** | ✅ 只执行脚本+报告 | — | — | ⚠️ 多步 LLM 判断 |

### ✨ 核心优势

1. **极简轻量** — 不用浏览器、不装 Playwright/Camoufox。三个轻量 Python 包搞定，安装体积不到 5MB（其他方案动辄 500MB+）

2. **直存本地或云端 Obsidian** — 直接写入你的 Obsidian vault 的 0-INBOX 目录，无论 vault 在本地磁盘还是 iCloud/OneDrive 等云端同步盘

3. **JSON 驱动配置** — 所有可变参数集中在 `config.json`，vault 路径、噪音正则、失败阈值一键修改。本地覆盖用 `config.local.json`（已 gitignore）

4. **自动内容标签** — `tags_keyword_map.json` 定义关键词→标签映射，脚本自动扫描文章内容打标签。支持 `.local.json` 追加个人关键词

5. **标签自动规范化** — 脚本内置规范化函数：平台名保大小写（`Anthropic`、`OpenAI`），产品名全小写连字符（`claude-code`），中文原样保留

6. **抓取失败自动降级** — 正文不足 2000 字符时自动保存链接存根，无需 LLM 判断。2000~5000 字符发出警告

7. **最小化 LLM 操作** — AI Agent 只需执行一条命令，脚本输出结构化结果直接转述。无需 LLM 判断标签、规范化格式、处理失败

8. **AI Agent 友好** — 专为 Claude Code / OpenClaw 设计的 SKILL.md，AI 助手可直接理解并执行

### 设计哲学

不做"大而全"，做"够用且好用"：

- **不用浏览器** → 少量使用无反爬需求，省下 500MB 安装空间
- **图片不下载** → 保留 CDN 链接，Obsidian 在线阅读无压力
- **JSON 配一切** → 脚本逻辑固定，行为由 JSON 数据驱动，LLM 零判断
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

# 3. 配置你的 Obsidian vault 路径
#    编辑 config.json 中的 obsidian.vault_path
#    或创建 config.local.json 覆盖（推荐，不会被 git 推送）
```

## 使用

### AI 对话中使用

```
帮我把这篇文章存到 Obsidian：
https://mp.weixin.qq.com/s/xxxxx
```

AI 助手自动执行脚本，脚本自动完成：抓取 → 解析 → 标签 → 规范化 → 失败判断 → 保存。

### 命令行使用

```bash
# 直接保存到 Obsidian 0-INBOX（含自动标签）
python3 scripts/article_to_md.py "https://mp.weixin.qq.com/s/xxxxx"

# 先预览，不保存
python3 scripts/article_to_md.py "https://mp.weixin.qq.com/s/xxxxx" --dry-run

# 保存到指定目录
python3 scripts/article_to_md.py "https://mp.weixin.qq.com/s/xxxxx" -o ~/Desktop/

# 打印到终端
python3 scripts/article_to_md.py "https://mp.weixin.qq.com/s/xxxxx" --print

# 禁用自动标签
python3 scripts/article_to_md.py "https://mp.weixin.qq.com/s/xxxxx" --no-auto-tag
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
tags: [inbox, article, AI, LLM, 知识管理]
---

# AI 时代的个人知识管理

> 原文链接: https://mp.weixin.qq.com/s/xxxxx

正文内容，格式整洁，图片保留 CDN 链接...
```

文件保存为：`0-INBOX/2026-04-15_AI时代的个人知识管理.md`

## ⚙️ 配置说明

### config.json（通用配置）

```json
{
  "obsidian":           { "vault_path": "~/Documents/MyVault", "inbox_dir": "0-INBOX" },
  "fetching":           { "user_agent": "...", "timeout": 30 },
  "failure":            { "min_content_chars": 2000, "warn_content_chars": 5000 },
  "tags":               { "default": ["inbox", "article"], "preserve_case": [...] },
  "noise_patterns":     ["预览时标签不可点", ...]
}
```

本地覆盖：创建 `config.local.json`，只写要覆盖的字段即可（深度合并）。

### tags_keyword_map.json（标签关键词映射）

```json
{
  "keyword_tags": {
    "Anthropic": ["Anthropic"],
    "Claude": ["Anthropic", "claude-code"],
    "产品经理": ["产品经理"],
    ...
  }
}
```

本地追加：创建 `tags_keyword_map.local.json`，新关键词会合并到基础映射中。

### 标签规范化规则（脚本内置）

| 类型 | 规则 | 示例 |
|------|------|------|
| 平台/公司名 | 保持原样 | `Anthropic`, `OpenAI`, `Google` |
| 产品/技术名 | 全小写 + 连字符 | `claude-code`, `prompt-engineering` |
| 中文标签 | 保持原样 | `产品经理`, `知识管理` |

## 项目结构

```
wechat-to-obsidian/
├── SKILL.md                    # AI Agent 指令文件
├── SKILL.local.md              # 本地 LLM 专属指引（gitignore）
├── README.md                   # 本文件
├── config.json                 # 通用配置
├── tags_keyword_map.json       # 标签关键词映射
├── .gitignore
└── scripts/
    └── article_to_md.py        # 核心转换脚本
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

## 📝 更新日志

### v2.0 (2026-05-01) — JSON 驱动 + 智能自动化

**核心理念：脚本逻辑固定，行为 JSON 驱动，LLM 零判断。**

| 更新 | 说明 |
|------|------|
| 🔧 **JSON 配置化** | 所有可变参数集中 `config.json`（vault路径/失败阈值/噪音正则/标签规范），支持 `config.local.json` 深度覆盖 |
| 🏷️ **自动内容标签** | 新建 `tags_keyword_map.json`（38个关键词），脚本自动扫描文章内容打标签，支持 `.local.json` 追加 |
| ✂️ **标签规范化** | `normalize_tag()` 自动处理大小写/连字符规则，LLM 不用再记忆格式规范 |
| 🛡️ **失败自动降级** | 字符数 < 2000 → 自动保存链接存根；< 5000 → 警告标记，全程无需 LLM 判断 |
| ⚡ **LLM 步骤减半** | 从 4 步（确认URL→打标签→判断成败→规范化）缩减到 2 步（执行脚本→报告结果） |

**LLM 工作流变化：**
```
v1: 确认URL → 执行脚本 → 读内容打标签 → 判断成败 → 规范化格式 → 报告
v2: 执行脚本 → 报告结果
      ↑ 脚本自动完成中间 4 步
```

### v1.0 (2026-04-30) — 初始版本
- 纯 HTTP 抓取（requests + BeautifulSoup + markdownify）
- 直存 Obsidian 0-INBOX
- 懒加载图片修复 + 微信噪音清理
- 多策略标题/作者/时间解析（含 Unix 时间戳）
- SKILL.local.md 本地个性化分离

## License

MIT
