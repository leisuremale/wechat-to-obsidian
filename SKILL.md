---
name: wechat-to-obsidian
description: Convert WeChat Official Account (微信公众号) articles to Markdown and save to Obsidian 0-INBOX. Use when the user provides article URLs from mp.weixin.qq.com.
---

# WeChat to Obsidian Skill

将微信公众号文章转换为 Markdown 格式，自动存入 Obsidian vault 的 `0-INBOX` 目录。

## 触发条件

- 用户提供 `mp.weixin.qq.com` 链接
- 用户说"保存到 Obsidian"、"转成 Markdown"、"收藏这篇文章"等

## 工作流程

### 1. 确认 URL

验证是有效的微信公众号文章链接。

### 2. 运行转换脚本

```bash
python3 ~/.openclaw/workspace/skills/wechat-to-obsidian/scripts/article_to_md.py "<文章URL>"
```

脚本会自动：
- 抓取文章内容（服务端渲染，无需浏览器）
- 提取标题、公众号名称、发布时间
- 修复懒加载图片
- 转换为 Markdown
- 清理噪音文本
- 添加 YAML frontmatter
- 保存到 Obsidian 0-INBOX

### 3. 预览（可选）

```bash
python3 ~/.openclaw/workspace/skills/wechat-to-obsidian/scripts/article_to_md.py "<URL>" --dry-run
```

### 4. 报告结果

告诉用户文章标题和保存位置。

## 输出格式

保存位置: `你的vault/0-INBOX/YYYY-MM-DD_标题.md`

```markdown
---
title: "文章标题"
source_url: https://mp.weixin.qq.com/s/...
platform: wechat
author: 公众号名称
publish_date: 2026-01-15
saved_date: 2026-05-01
tags: [inbox, article]
---

# 文章标题

> 原文链接: https://...

正文内容...
```

## ⚙️ 配置（首次使用前必须修改）

> **⚠️ 脚本内置了个人 vault 路径，使用前必须改成你自己的！**

编辑 `scripts/article_to_md.py`，找到顶部的这两行并修改：

```python
# 改成你自己的 Obsidian vault 根目录
OBSIDIAN_VAULT = os.path.expanduser("~/Documents/MyObsidianVault")

# vault 内的 inbox 子目录（默认 0-INBOX，可按需修改）
INBOX_DIR = os.path.join(OBSIDIAN_VAULT, "0-INBOX")
```

常见路径参考：
- 本地 vault: `~/Documents/你的vault名`
- iCloud vault: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/你的vault名`

## 依赖

```bash
pip3 install requests beautifulsoup4 markdownify
```

## 注意事项

- ✅ 公开文章可直接抓取（服务端渲染，无需浏览器）
- ❌ 付费文章、被删除文章无法抓取
- ⚠️ 频繁请求可能触发微信反爬，偶发失败时稍等重试即可
- 图片保留微信 CDN 链接（不下载到本地）

## 故障排查

| 问题 | 解决方法 |
|------|---------|
| 文章内容为空 | URL 可能无效或文章已删除 |
| 标题为"未命名文章" | 脚本未能提取标题，手动检查 URL |
| 文件未出现在 Obsidian | 检查 `OBSIDIAN_VAULT` 路径是否正确 |
