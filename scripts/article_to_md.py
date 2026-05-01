#!/usr/bin/env python3
"""
WeChat Article to Obsidian Converter
微信公众号文章 → Markdown → Obsidian 0-INBOX

特性（最小化 LLM 操作步骤）:
- JSON 驱动配置 (config.json + config.local.json 覆盖)
- 关键词自动标签 (tags_keyword_map.json)
- 标签自动规范化（大小写/连字符规则）
- 抓取失败自动降级（字数不足 → 链接存根）
"""

import sys
import os
import re
import json
import argparse
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

# ==================== 路径 ====================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)


# ==================== 内置默认配置 ====================

DEFAULT_CONFIG = {
    "obsidian": {
        "vault_path": "~/Documents/MyObsidianVault",
        "inbox_dir": "0-INBOX",
    },
    "fetching": {
        "user_agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept_language": "zh-CN,zh;q=0.9,en;q=0.8",
        "timeout": 30,
    },
    "failure": {
        "min_content_chars": 2000,
        "warn_content_chars": 5000,
        "on_failure": "save_link_stub",
    },
    "tags": {
        "default": ["inbox", "article"],
        "preserve_case": ["Anthropic", "OpenAI", "Google", "DeepSeek", "OpenClaw"],
        "auto_tag": True,
    },
    "noise_patterns": [
        "预览时标签不可点",
        "继续滑动看下一个",
        "轻触阅读原文",
        "微信扫一扫",
        "关注该公众号",
        "点赞.*在看",
        "分享.*收藏",
        "喜欢此内容的人还喜欢",
        "修改于",
        "收录于合集",
    ],
}

# ==================== JSON 配置加载 ====================


def deep_merge(base: dict, override: dict) -> dict:
    """深度合并，override 覆盖 base 中的同名键"""
    result = base.copy()
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_json_config() -> dict:
    """加载 config.json，config.local.json 深度覆盖"""
    config = DEFAULT_CONFIG.copy()

    config_path = os.path.join(SKILL_DIR, "config.json")
    local_path = os.path.join(SKILL_DIR, "config.local.json")

    for path in [config_path, local_path]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    override = json.load(f)
                # 移除 _说明 等元数据键
                override = {k: v for k, v in override.items() if not k.startswith("_")}
                config = deep_merge(config, override)
            except (json.JSONDecodeError, OSError) as e:
                print(f"⚠️ 配置文件解析失败: {path} — {e}", file=sys.stderr)

    return config


def load_keyword_map() -> dict:
    """加载 tags_keyword_map.json，.local.json 追加合并"""
    keyword_map = {"keyword_tags": {}}

    base_path = os.path.join(SKILL_DIR, "tags_keyword_map.json")
    local_path = os.path.join(SKILL_DIR, "tags_keyword_map.local.json")

    for path in [base_path, local_path]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                keyword_map["keyword_tags"].update(data.get("keyword_tags", {}))
            except (json.JSONDecodeError, OSError) as e:
                print(f"⚠️ 关键词映射解析失败: {path} — {e}", file=sys.stderr)

    return keyword_map


# ==================== 标签处理 ====================


def normalize_tag(tag: str, preserve_case: list) -> str:
    """按规范格式化单个标签"""
    if tag in preserve_case:
        return tag
    # 含中文 → 原样保留
    if re.search(r"[一-鿿]", tag):
        return tag
    # 英文 → 全小写 + 空格替换为连字符
    return tag.lower().replace(" ", "-")


def auto_tag(content: str, keyword_map: dict, preserve_case: list) -> list:
    """基于关键词匹配，自动推荐标签（已规范化）"""
    tags = set()
    for keyword, keyword_tags in keyword_map.get("keyword_tags", {}).items():
        if keyword.lower() in content.lower():
            for t in keyword_tags:
                tags.add(normalize_tag(t, preserve_case))
    return sorted(tags)


def build_tags(default_tags: list, auto_tags: list) -> list:
    """合并默认标签 + 自动标签，去重，默认标签在前"""
    result = list(default_tags)
    for t in auto_tags:
        if t not in result:
            result.append(t)
    return result


# ==================== 工具函数 ====================


def sanitize_filename(name: str, max_length: int = 80) -> str:
    """清理文件名中的非法字符"""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip().strip(".")
    return name[:max_length] if len(name) > max_length else name


def fetch_page(url: str, config: dict) -> str:
    """抓取页面 HTML"""
    fc = config["fetching"]
    resp = requests.get(
        url,
        headers={
            "User-Agent": fc["user_agent"],
            "Accept": fc["accept"],
            "Accept-Language": fc["accept_language"],
        },
        timeout=fc["timeout"],
    )
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def html_to_md(html_content: str) -> str:
    """HTML → Markdown（仅移除 script/style 标签和行内 style 属性）"""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()
    for tag in soup.find_all(style=True):
        del tag["style"]
    return markdownify(str(soup), heading_style="ATX", bullets="-")


def clean_noise(text: str, patterns: list) -> str:
    """清理微信文章噪音"""
    compiled = [re.compile(p) for p in patterns]
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if any(p.search(stripped) for p in compiled):
            continue
        if stripped == "" and cleaned and cleaned[-1] == "":
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def build_frontmatter(
    title: str,
    source_url: str,
    author: str = "",
    publish_date: str = "",
    tags: list = None,
) -> str:
    """构建 YAML frontmatter"""
    today = datetime.now().strftime("%Y-%m-%d")
    if tags is None:
        tags = ["inbox", "article"]
    fm = [
        "---",
        f'title: "{title}"',
        f"source_url: {source_url}",
        "platform: wechat",
    ]
    if author:
        fm.append(f"author: {author}")
    fm.append(f"publish_date: {publish_date or today}")
    fm.extend(
        [
            f"saved_date: {today}",
            f"tags: [{', '.join(tags)}]",
            "---",
            "",
        ]
    )
    return "\n".join(fm)


# ==================== 微信文章解析 ====================


def parse_wechat(html: str) -> dict:
    """解析微信公众号文章 HTML"""
    soup = BeautifulSoup(html, "html.parser")

    # 标题（多种策略）
    title = ""
    for pattern in [
        r"var\s+msg_title\s*=\s*['\"](.+?)['\"]",
        r"var\s+title\s*=\s*['\"](.+?)['\"]",
    ]:
        m = re.search(pattern, html)
        if m:
            title = m.group(1).strip()
            break
    if not title:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            title = og["content"].strip()
    if not title:
        t = soup.find("title")
        if t:
            title = t.text.strip()

    # 作者 / 公众号名称
    author = ""
    for pattern in [
        r"var\s+nickname\s*=\s*['\"](.+?)['\"]",
        r"var\s+msg_source\s*=\s*['\"](.+?)['\"]",
    ]:
        m = re.search(pattern, html)
        if m:
            author = m.group(1).strip()
            break
    if not author:
        ma = soup.find("meta", attrs={"name": "author"})
        if ma and ma.get("content"):
            author = ma["content"].strip()

    # 发布时间（多种策略：字符串 + Unix 时间戳）
    publish_date = ""
    for pattern in [
        r"var\s+publish_time\s*=\s*['\"](.+?)['\"]",
        r"var\s+ct\s*=\s*['\"](.+?)['\"]",
        r"var\s+create_time\s*=\s*['\"](.+?)['\"]",
    ]:
        m = re.search(pattern, html)
        if m:
            ts = m.group(1).strip()
            try:
                if ts.isdigit() and int(ts) > 1000000000:
                    publish_date = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
                else:
                    publish_date = ts
            except (ValueError, OSError):
                publish_date = ts
            break

    # 正文
    content_html = ""
    js_content = soup.find("div", id="js_content")
    if js_content:
        # 修复懒加载图片
        for img in js_content.find_all("img"):
            if img.get("data-src"):
                img["src"] = img["data-src"]
        content_html = str(js_content)
    else:
        rich = soup.find("div", class_="rich_media_content")
        if rich:
            content_html = str(rich)
    if not content_html:
        body = soup.find("body")
        if body:
            content_html = str(body)

    return {
        "title": title or "未命名文章",
        "author": author,
        "publish_date": publish_date,
        "content_html": content_html,
    }


# ==================== 主流程 ====================


def is_wechat_url(url: str) -> bool:
    """判断是否为微信公众号文章链接"""
    domain = urlparse(url).netloc.lower()
    return "mp.weixin.qq.com" in domain or "weixin.qq.com" in domain


def convert_article(url: str, output_dir: str = None, dry_run: bool = False) -> dict:
    """转换微信文章并保存到 Obsidian。返回结果字典供 LLM 报告使用。"""
    config = load_json_config()
    keyword_map = load_keyword_map()

    if not is_wechat_url(url):
        return {"success": False, "error": f"不支持该链接，目前仅支持微信公众号文章 (mp.weixin.qq.com)"}

    if output_dir is None:
        obsidian_cfg = config["obsidian"]
        vault = os.path.expanduser(obsidian_cfg["vault_path"])
        output_dir = os.path.join(vault, obsidian_cfg["inbox_dir"])

    print(f"📡 抓取: {url}")

    html = fetch_page(url, config)
    article = parse_wechat(html)

    title = article["title"]
    print(f"📝 标题: {title}")
    if article["author"]:
        print(f"👤 公众号: {article['author']}")
    if article["publish_date"]:
        print(f"📅 发布时间: {article['publish_date']}")

    print("🔄 转换 Markdown...")
    md_body = html_to_md(article["content_html"])
    md_body = clean_noise(md_body, config["noise_patterns"])

    # ─── 自动标签 ───
    tags = list(config["tags"]["default"])
    if config["tags"].get("auto_tag", True):
        auto_tags = auto_tag(md_body, keyword_map, config["tags"]["preserve_case"])
        tags = build_tags(tags, auto_tags)
        if auto_tags:
            print(f"🏷️  自动标签: {auto_tags}")

    # ─── 构建全文 ───
    frontmatter = build_frontmatter(
        title=title,
        source_url=url,
        author=article["author"],
        publish_date=article["publish_date"],
        tags=tags,
    )
    full_md = frontmatter + f"# {title}\n\n" + f"> 原文链接: {url}\n\n" + md_body

    if dry_run:
        print("\n─── 预览（前 2000 字符）───")
        print(full_md[:2000])
        return {"success": True, "dry_run": True}

    # ─── 内容长度判断 ───
    content_len = len(full_md)
    failure_cfg = config["failure"]
    is_stub = False

    if content_len < failure_cfg["min_content_chars"]:
        print(f"⚠️  内容过短 ({content_len} 字符，阈值 {failure_cfg['min_content_chars']})")
        stub_md = frontmatter + (
            f"# {title}\n\n"
            f"⚠️ 无法抓取正文（仅 {content_len} 字符）\n\n"
            f"原文链接: {url}\n"
        )
        full_md = stub_md
        is_stub = True
    elif content_len < failure_cfg["warn_content_chars"]:
        print(f"⚠️  内容偏少 ({content_len} 字符)，请人工审核")

    # ─── 生成文件名 ───
    date_str = article.get("publish_date", "")
    dm = re.match(r"(\d{4}-\d{2}-\d{2})", date_str) if date_str else None
    date_str = dm.group(1) if dm else datetime.now().strftime("%Y-%m-%d")

    filename = f"{date_str}_{sanitize_filename(title)}.md"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_md)

    # ─── 输出结构化结果 ───
    print(f"\n{'⚠️  已保存链接存根' if is_stub else '✅ 已保存'}: {filepath}")
    print(f"📊 字符数: {content_len}")
    print(f"🏷️  最终标签: {tags}")

    return {
        "success": True,
        "is_stub": is_stub,
        "title": title,
        "author": article["author"],
        "publish_date": article["publish_date"],
        "filepath": filepath,
        "content_length": content_len,
        "tags": tags,
        "auto_tags": auto_tags if config["tags"].get("auto_tag", True) else [],
    }


def main():
    parser = argparse.ArgumentParser(description="微信公众号文章 → Markdown → Obsidian 0-INBOX")
    parser.add_argument("url", help="微信公众号文章链接")
    parser.add_argument("-o", "--output-dir", default=None, help="输出目录（覆盖 config.json）")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不保存")
    parser.add_argument("--print", action="store_true", help="打印到 stdout（含自动标签）")
    parser.add_argument(
        "--no-auto-tag", action="store_true", help="禁用关键词自动标签"
    )
    args = parser.parse_args()

    if args.print:
        config = load_json_config()
        keyword_map = load_keyword_map()

        html = fetch_page(args.url, config)
        article = parse_wechat(html)
        md_body = html_to_md(article["content_html"])
        md_body = clean_noise(md_body, config["noise_patterns"])

        tags = list(config["tags"]["default"])
        if config["tags"].get("auto_tag", True) and not args.no_auto_tag:
            auto_tags = auto_tag(md_body, keyword_map, config["tags"]["preserve_case"])
            tags = build_tags(tags, auto_tags)

        fm = build_frontmatter(
            title=article["title"],
            source_url=args.url,
            author=article["author"],
            publish_date=article["publish_date"],
            tags=tags,
        )
        print(fm + f"# {article['title']}\n\n" + f"> 原文链接: {args.url}\n\n" + md_body)
    else:
        result = convert_article(args.url, output_dir=args.output_dir, dry_run=args.dry_run)
        if not result["success"]:
            print(f"❌ {result['error']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
