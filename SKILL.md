---
name: wechat-to-obsidian
description: Convert WeChat Official Account (微信公众号) articles to Markdown and save to Obsidian 0-INBOX. Use when the user provides article URLs from mp.weixin.qq.com.
---

# WeChat to Obsidian Skill

> 📌 如有 `SKILL.local.md` 或 `config.local.json`/`tags_keyword_map.local.json`，优先读取本地规则。

将微信公众号文章转换为 Markdown 格式，自动存入 Obsidian vault 的 `0-INBOX` 目录。

## 触发条件

- 用户提供 `mp.weixin.qq.com` 链接
- 用户说"保存到 Obsidian"、"转成 Markdown"、"收藏这篇文章"等

## 工作流程（最小化 LLM 步骤）

> 脚本已内置：URL 验证、自动标签、标签规范化、抓取失败降级。LLM 只需执行脚本 + 报告结果。

### 1. 运行转换脚本

```bash
python3 ./skills/wechat-to-obsidian/scripts/article_to_md.py "<文章URL>"
```

### 2. 报告结果

脚本输出已经包含全部关键信息，LLM 直接转述即可：

- ✅ 成功：告知用户标题、保存位置、标签
- ⚠️ 链接存根：告知用户正文抓取失败，已保存原文链接
- ❌ 不支持：告知用户链接格式不支持

## 脚本自动完成的功能

| 动作 | 机制 |
|------|------|
| URL 验证 | 脚本内置 `is_wechat_url()` |
| 内容标签 | `tags_keyword_map.json` 关键词自动匹配 |
| 标签规范化 | 脚本内置 `normalize_tag()`（平台名大写、产品小写连字符、中文保留） |
| 抓取失败降级 | 字符数 < 2000 → 自动保存链接存根 |
| 噪音清理 | `config.json` 中 `noise_patterns` 正则列表 |

## 输出格式

保存位置: `your-vault/0-INBOX/YYYY-MM-DD_标题.md`

```markdown
---
title: "文章标题"
source_url: https://mp.weixin.qq.com/s/...
platform: wechat
author: 公众号名称
publish_date: 2026-01-15
saved_date: 2026-05-01
tags: [inbox, article, AI, claude-code]
---
```

## ⚙️ 配置

所有配置集中在 `config.json`（可创建 `config.local.json` 覆盖本地设置）：

| 配置项 | 说明 |
|--------|------|
| `obsidian.vault_path` | Obsidian vault 根目录 |
| `obsidian.inbox_dir` | inbox 子目录名 |
| `failure.min_content_chars` | 低于此值自动保存链接存根（默认 2000） |
| `failure.warn_content_chars` | 低于此值发出警告（默认 5000） |
| `tags.preserve_case` | 保持原始大小写的标签名列表 |
| `noise_patterns` | 要清除的噪音文本正则列表 |

标签关键词映射见 `tags_keyword_map.json`（可创建 `.local.json` 追加个人关键词）。

## 依赖

```bash
pip3 install requests beautifulsoup4 markdownify
```

## 注意事项

- ✅ 公开文章可直接抓取（服务端渲染，无需浏览器）
- ❌ 付费文章、被删除文章无法抓取
- ⚠️ 频繁请求可能触发微信反爬，偶发失败时稍等重试即可
- 图片保留微信 CDN 链接（不下载到本地）
