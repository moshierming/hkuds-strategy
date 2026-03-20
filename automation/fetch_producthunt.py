#!/usr/bin/env python3
"""
fetch_producthunt.py
====================
通过 ProductHunt 公开 RSS feed 抓取每日/每周热门产品。

不需要 API Token — 使用官方 Atom Feed（50条/feed）。
多 category feed 并行抓取，扩大覆盖范围。

用法:
    python automation/fetch_producthunt.py
    python automation/fetch_producthunt.py --days 7   # 最近7天

依赖:
    pip install requests

输出:
    logs/producthunt_trends.md
"""

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先安装依赖: pip install requests")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / "logs"
OUTPUT_FILE = LOGS_DIR / "producthunt_trends.md"

ATOM_NS = "http://www.w3.org/2005/Atom"

# PH 公开 RSS feed — 按 category 分类，无需 token
RSS_FEEDS = [
    ("artificial-intelligence", "https://www.producthunt.com/feed?category=artificial-intelligence"),
    ("developer-tools",         "https://www.producthunt.com/feed?category=developer-tools"),
    ("productivity",            "https://www.producthunt.com/feed?category=productivity"),
    ("machine-learning",        "https://www.producthunt.com/feed?category=machine-learning"),
    ("open-source",             "https://www.producthunt.com/feed?category=open-source"),
    ("bots",                    "https://www.producthunt.com/feed?category=bots"),
    ("general",                 "https://www.producthunt.com/feed"),  # 全站 top50 兜底
]

# 关注关键词 — 命中任一则优先展示
FOCUS_KEYWORDS = [
    "rag", "llm", "agent", "ai", "gpt", "claude", "knowledge graph",
    "vector", "embedding", "local ai", "open source", "automation",
    "copilot", "code", "mcp", "model context", "memory",
]


def strip_html(text: str) -> str:
    """去除 HTML 标签，还原 HTML 实体"""
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text).strip()


def fetch_feed(category: str, url: str, timeout: int = 12) -> list[dict]:
    """抓取单个 RSS feed，返回 entry 列表"""
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "hkuds-intelligence-bot/1.0"})
        resp.raise_for_status()
    except Exception as e:
        print(f"  ⚠️  [{category}] 抓取失败: {e}")
        return []

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        print(f"  ⚠️  [{category}] XML 解析失败: {e}")
        return []

    ns = {"atom": ATOM_NS}
    entries = []
    for entry in root.findall("atom:entry", ns):
        def txt(tag):
            el = entry.find(f"atom:{ tag}", ns)
            return (el.text or "").strip() if el is not None else ""

        # link.href
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "") if link_el is not None else txt("id")

        # 从 content 提取 tagline（第一段 <p> 内容）
        content_el = entry.find("atom:content", ns)
        raw_content = content_el.text if content_el is not None else ""
        p_match = re.search(r"<p[^>]*>(.*?)</p>", raw_content or "", re.DOTALL)
        tagline = strip_html(p_match.group(1)) if p_match else strip_html(raw_content or "")

        entries.append({
            "id": txt("id"),
            "title": txt("title"),
            "tagline": tagline[:200],
            "published": txt("published"),
            "link": link,
            "category": category,
        })
    return entries


def is_recent(entry: dict, days: int) -> bool:
    try:
        dt = datetime.fromisoformat(entry["published"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return dt >= cutoff
    except Exception:
        return True  # 解析失败不过滤


def is_focused(entry: dict) -> bool:
    """是否命中关注关键词"""
    text = (entry["title"] + " " + entry["tagline"]).lower()
    return any(kw in text for kw in FOCUS_KEYWORDS)


def deduplicate(entries: list[dict]) -> list[dict]:
    seen_ids, seen_titles = set(), set()
    result = []
    for e in entries:
        norm_title = e["title"].lower().strip()
        if e["id"] not in seen_ids and norm_title not in seen_titles:
            seen_ids.add(e["id"])
            seen_titles.add(norm_title)
            result.append(e)
    return result


def generate_report(all_entries: list[dict], focused: list[dict], days: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# ProductHunt AI/Dev 趋势报告",
        "",
        f"> 生成时间: {now} | 范围: 最近 {days} 天 | 来源: {len(RSS_FEEDS)} 个 category RSS feed",
        f"> 总条目: {len(all_entries)} | 聚焦 AI/Dev 条目: {len(focused)}",
        "",
    ]

    if not all_entries:
        lines += ["*本期无新产品发现（可能需要扩大天数范围）*", ""]
        return "\n".join(lines)

    if focused:
        lines += [
            f"## 🎯 聚焦 AI/Dev/工具 产品 ({len(focused)} 条)",
            "",
            "| 产品 | Tagline | 日期 | Category |",
            "|------|---------|------|----------|",
        ]
        for e in focused[:25]:
            date_str = e["published"][:10]
            name_link = f"[{e['title']}]({e['link']})"
            tagline = e["tagline"][:60] + "..." if len(e["tagline"]) > 60 else e["tagline"]
            lines.append(f"| {name_link} | {tagline} | {date_str} | {e['category']} |")
        lines.append("")

    if all_entries:
        lines += [
            f"## 📋 全部近期产品 ({len(all_entries)} 条)",
            "",
            "| 产品 | Tagline | 日期 |",
            "|------|---------|------|",
        ]
        for e in all_entries[:30]:
            date_str = e["published"][:10]
            name_link = f"[{e['title']}]({e['link']})"
            tagline = e["tagline"][:55] + "..." if len(e["tagline"]) > 55 else e["tagline"]
            lines.append(f"| {name_link} | {tagline} | {date_str} |")
        lines.append("")

    # 为情报引擎格式化的精简信号
    lines += [
        "---",
        "## 🔌 信号摘要（供情报引擎使用）",
        "",
    ]
    for e in focused[:20]:
        lines.append(f"- **{e['title']}** ({e['category']}): {e['tagline'][:120]}")
        lines.append(f"  {e['link']}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="抓取 ProductHunt AI/Dev 产品趋势（RSS）")
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    LOGS_DIR.mkdir(exist_ok=True)
    print(f"🔍 抓取 ProductHunt 最近 {args.days} 天产品 (RSS, 无需 token)...")

    all_entries: list[dict] = []
    for cat, url in RSS_FEEDS:
        entries = fetch_feed(cat, url)
        recent = [e for e in entries if is_recent(e, args.days)]
        if recent:
            print(f"  ✅ [{cat}] {len(recent)} 条近期产品")
        all_entries.extend(recent)

    all_entries = deduplicate(all_entries)
    all_entries.sort(key=lambda x: x["published"], reverse=True)
    focused = [e for e in all_entries if is_focused(e)]

    print(f"\n📦 去重后共 {len(all_entries)} 条 | 聚焦 AI/Dev: {len(focused)} 条")

    report = generate_report(all_entries, focused, args.days)
    OUTPUT_FILE.write_text(report, encoding="utf-8")
    print(f"📝 报告已写入 {OUTPUT_FILE}")

    if focused:
        print("\n🔥 Top 聚焦产品:")
        for e in focused[:5]:
            print(f"  • {e['title']} — {e['tagline'][:60]}")


if __name__ == "__main__":
    main()
