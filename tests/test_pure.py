"""纯函数单元测试（无网络）。

运行：pytest tests/
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import article_to_md as m  # noqa: E402


# ---------- normalize_tag ----------


def test_normalize_tag_preserves_case_in_list():
    assert m.normalize_tag("Anthropic", ["Anthropic", "OpenAI"]) == "Anthropic"


def test_normalize_tag_lowercases_ascii():
    assert m.normalize_tag("LLM", ["Anthropic"]) == "llm"
    assert m.normalize_tag("Hello World", []) == "hello-world"


def test_normalize_tag_keeps_chinese():
    assert m.normalize_tag("产品经理", []) == "产品经理"


# ---------- deep_merge ----------


def test_deep_merge_overrides_top_level():
    assert m.deep_merge({"a": 1, "b": 2}, {"b": 99}) == {"a": 1, "b": 99}


def test_deep_merge_recurses_into_dicts():
    assert m.deep_merge(
        {"x": {"y": 1, "z": 2}}, {"x": {"y": 10}}
    ) == {"x": {"y": 10, "z": 2}}


def test_deep_merge_replaces_lists_wholesale():
    # 列表是整体替换，不做合并（当前设计）
    assert m.deep_merge({"a": [1, 2]}, {"a": [3]}) == {"a": [3]}


# ---------- sanitize_filename ----------


def test_sanitize_filename_replaces_illegal_chars():
    assert m.sanitize_filename("a<b>c?d") == "a_b_c_d"


def test_sanitize_filename_collapses_underscores():
    assert m.sanitize_filename("???") == ""
    assert m.sanitize_filename("a???b") == "a_b"


def test_sanitize_filename_truncates():
    assert len(m.sanitize_filename("x" * 200, max_length=50)) == 50


# ---------- is_wechat_url ----------


def test_is_wechat_url_accepts_canonical():
    assert m.is_wechat_url("https://mp.weixin.qq.com/s/abc")
    assert m.is_wechat_url("https://weixin.qq.com/foo")


def test_is_wechat_url_rejects_lookalike_substrings():
    assert not m.is_wechat_url("https://evil.mp.weixin.qq.com.attacker.com/x")
    assert not m.is_wechat_url("https://attacker.com/?q=mp.weixin.qq.com")


def test_is_wechat_url_rejects_non_http():
    assert not m.is_wechat_url("ftp://mp.weixin.qq.com/x")
    assert not m.is_wechat_url("not a url")
    assert not m.is_wechat_url("")


# ---------- auto_tag (keyword matching) ----------


def test_auto_tag_word_boundary_for_ascii():
    km = {"keyword_tags": {"GPT": ["LLM"]}}
    assert "llm" in m.auto_tag("GPT-4 is fine", km, [])
    assert "llm" not in m.auto_tag("chatGPT4 model", km, [])


def test_auto_tag_substring_for_chinese():
    km = {"keyword_tags": {"产品经理": ["产品经理"]}}
    assert "产品经理" in m.auto_tag("我是产品经理", km, [])


def test_auto_tag_multiword_keyword():
    km = {"keyword_tags": {"AI Agent": ["AI", "AI-Agent"]}}
    tags = m.auto_tag("an AI Agent system", km, [])
    assert "ai" in tags and "ai-agent" in tags


def test_auto_tag_preserves_case_via_list():
    km = {"keyword_tags": {"Anthropic": ["Anthropic"]}}
    tags = m.auto_tag("by Anthropic team", km, ["Anthropic"])
    assert tags == ["Anthropic"]


# ---------- build_frontmatter (YAML escaping) ----------


def test_frontmatter_escapes_quotes_in_title():
    fm = m.build_frontmatter('Hello "world"', "https://x")
    assert 'title: "Hello \\"world\\""' in fm


def test_frontmatter_quotes_special_tags_only():
    fm = m.build_frontmatter("t", "https://x", tags=["inbox", "a,b", "AI"])
    assert '"a,b"' in fm  # tag with comma must be quoted
    assert ", AI]" in fm  # plain tag stays bare


def test_frontmatter_default_tags_when_none():
    fm = m.build_frontmatter("t", "https://x")
    assert "tags: [inbox, article]" in fm


# ---------- parse_wechat (publish_iso_date) ----------


def test_parse_wechat_iso_date_from_unix_timestamp():
    art = m.parse_wechat("<html><script>var ct = '1620000000';</script></html>")
    assert art["publish_iso_date"] != ""


def test_parse_wechat_iso_date_from_string_with_single_digits():
    art = m.parse_wechat("<html><script>var publish_time = '2024-3-5';</script></html>")
    assert art["publish_iso_date"] == "2024-03-05"


def test_parse_wechat_no_date_returns_empty():
    art = m.parse_wechat("<html><title>x</title></html>")
    assert art["publish_iso_date"] == ""


def test_parse_wechat_title_fallback_chain():
    # Falls back to <title> when no JS variable
    art = m.parse_wechat("<html><title>From title tag</title></html>")
    assert art["title"] == "From title tag"
