#!/usr/bin/env python3
"""
WeChat Article to Obsidian Converter
微信公众号文章 → Markdown → Obsidian 0-INBOX
"""

import sys
import os
import re
import argparse
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

# ==================== 配置 ====================
# ⚠️ 使用前请修改为你的 Obsidian vault 路径
# 常见路径:
#   本地:   ~/Documents/MyVault
#   iCloud: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/你的vault名

OBSIDIAN_VAULT = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Le"
)
INBOX_DIR = os.path.join(OBSIDIAN_VAULT, "0-INBOX")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 微信文章常见噪音
WECHAT_NOISE_PATTERNS = [
    re.compile(r"预览时标签不可点"),
    re.compile(r"继续滑动看下一个"),
    re.compile(r"轻触阅读原文"),
    re.compile(r"微信扫一扫"),
    re.compile(r"关注该公众号"),
    re.compile(r"点赞.*在看"),
    re.compile(r"分享.*收藏"),
    re.compile(r"喜欢此内容的人还喜欢"),
    re.compile(r"修改于"),
    re.compile(r"收录于合集"),
]


# ==================== 工具函数 ====================

def sanitize_filename(name: str, max_length: int = 80) -> str:
    """清理文件名中的非法字符"""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip().strip(".")
    return name[:max_length] if len(name) > max_length else name


def fetch_page(url: str) -> str:
    """抓取页面 HTML"""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def html_to_md(html_content: str) -> str:
    """HTML → Markdown"""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()
    for tag in soup.find_all(style=True):
        del tag["style"]
    return markdownify(str(soup), heading_style="ATX", bullets="-")


def clean_noise(text: str) -> str:
    """清理微信文章噪音"""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if any(p.search(stripped) for p in WECHAT_NOISE_PATTERNS):
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
) -> str:
    """构建 YAML frontmatter"""
    today = datetime.now().strftime("%Y-%m-%d")
    fm = [
        "---",
        f'title: "{title}"',
        f"source_url: {source_url}",
        "platform: wechat",
    ]
    if author:
        fm.append(f"author: {author}")
    fm.append(f"publish_date: {publish_date or today}")
    fm.extend([
        f"saved_date: {today}",
        "tags: [inbox, article]",
        "---",
        "",
    ])
    return "\n".join(fm)


# ==================== 微信文章解析 ====================

def parse_wechat(html: str) -> dict:
    """解析微信公众号文章 HTML"""
    soup = BeautifulSoup(html, "html.parser")

    # 标题（多种策略）
    title = ""
    for pattern, source in [
        (r"var\s+msg_title\s*=\s*['\"](.+?)['\"]", "var"),
        (r"var\s+title\s*=\s*['\"](.+?)['\"]", "var_title"),
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

    # 发布时间（多种策略）
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
                    publish_date = datetime.fromtimestamp(int(ts)).strftime(
                        "%Y-%m-%d %H:%M"
                    )
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


def convert_article(url: str, output_dir: str = None, dry_run: bool = False) -> str:
    """转换微信文章并保存到 Obsidian"""
    if not is_wechat_url(url):
        print("❌ 不支持该链接，目前仅支持微信公众号文章 (mp.weixin.qq.com)")
        sys.exit(1)

    if output_dir is None:
        output_dir = INBOX_DIR

    print(f"📡 抓取: {url}")

    html = fetch_page(url)
    article = parse_wechat(html)

    title = article["title"]
    print(f"📝 标题: {title}")
    if article["author"]:
        print(f"👤 公众号: {article['author']}")
    if article["publish_date"]:
        print(f"📅 发布时间: {article['publish_date']}")

    print("🔄 转换 Markdown...")
    md_body = html_to_md(article["content_html"])
    md_body = clean_noise(md_body)

    frontmatter = build_frontmatter(
        title=title,
        source_url=url,
        author=article["author"],
        publish_date=article["publish_date"],
    )
    full_md = frontmatter + f"# {title}\n\n" + f"> 原文链接: {url}\n\n" + md_body

    if dry_run:
        print("\n─── 预览（前 2000 字符）───")
        print(full_md[:2000])
        return ""

    # 生成文件名: YYYY-MM-DD_标题.md
    date_str = article.get("publish_date", "")
    dm = re.match(r"(\d{4}-\d{2}-\d{2})", date_str) if date_str else None
    date_str = dm.group(1) if dm else datetime.now().strftime("%Y-%m-%d")

    filename = f"{date_str}_{sanitize_filename(title)}.md"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_md)

    print(f"✅ 已保存: {filepath}")
    print(f"📊 {len(full_md)} 字符")
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="微信公众号文章 → Markdown → Obsidian 0-INBOX"
    )
    parser.add_argument("url", help="微信公众号文章链接")
    parser.add_argument("-o", "--output-dir", default=None, help="输出目录")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不保存")
    parser.add_argument("--print", action="store_true", help="打印到 stdout")
    args = parser.parse_args()

    if args.print:
        html = fetch_page(args.url)
        article = parse_wechat(html)
        md_body = html_to_md(article["content_html"])
        md_body = clean_noise(md_body)
        fm = build_frontmatter(
            title=article["title"],
            source_url=args.url,
            author=article["author"],
            publish_date=article["publish_date"],
        )
        print(fm + f"# {article['title']}\n\n" + md_body)
    else:
        convert_article(args.url, output_dir=args.output_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
