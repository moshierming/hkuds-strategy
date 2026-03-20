#!/usr/bin/env python3
"""
fetch_hackernews.py
===================
监控 HackerNews 上 AI/ML/开发者工具相关的高质量讨论。

关注三类内容：
1. Show HN — 开发者发布的新项目
2. Ask HN — 技术社区的关键讨论
3. 高分文章 — 行业信号

用法:
    python automation/fetch_hackernews.py
    python automation/fetch_hackernews.py --days 3 --min-score 50

依赖:
    pip install requests

输出:
    logs/hackernews_signals.md
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先安装依赖: pip install requests")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / "logs"
OUTPUT_FILE = LOGS_DIR / "hackernews_signals.md"

HN_API = "https://hacker-news.firebaseio.com/v0"

# 关键词：命中任一即纳入
KEYWORDS = [
    # AI/ML 核心
    "llm", "rag", "agent", "langchain", "llamaindex",
    "openai", "anthropic", "claude", "gpt", "gemini",
    "knowledge graph", "graph neural", "vector database",
    "embedding", "fine-tuning", "inference", "local llm",
    # 开发者工具
    "open source ai", "ai tool", "ai assistant",
    "code generation", "copilot", "cursor",
    "mcp", "model context protocol",
    # 商业/产业信号
    "ai startup", "vc", "series a", "acquiring",
    "agentic", "autonomous agent",
    # HKUDS 关联
    "lightrag", "nanobot", "autoagent", "minirag",
    "graph rag", "graphrag",
]


def fetch_top_stories(story_type: str = "topstories", limit: int = 200) -> list[int]:
    """获取 HN 置顶故事 ID 列表"""
    url = f"{HN_API}/{story_type}.json"
    resp = requests.get(url, timeout=10)
    ids = resp.json()
    return ids[:limit]


def fetch_story(story_id: int) -> dict | None:
    """获取单个故事详情"""
    url = f"{HN_API}/item/{story_id}.json"
    try:
        resp = requests.get(url, timeout=8)
        data = resp.json()
        return data if data and data.get("type") in ("story",) else None
    except Exception:
        return None


def is_relevant(story: dict) -> bool:
    """判断是否相关"""
    text = " ".join([
        (story.get("title") or "").lower(),
        (story.get("text") or "").lower(),
        (story.get("url") or "").lower(),
    ])
    return any(kw in text for kw in KEYWORDS)


def is_recent(story: dict, days: int) -> bool:
    """判断是否在最近 N 天内"""
    ts = story.get("time", 0)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return datetime.fromtimestamp(ts, tz=timezone.utc) >= cutoff


def classify_story(story: dict) -> str:
    """分类：Show HN / Ask HN / 其他"""
    title = story.get("title", "")
    if title.startswith("Show HN"):
        return "🛠️ Show HN"
    elif title.startswith("Ask HN"):
        return "❓ Ask HN"
    else:
        return "📰 文章"


def generate_report(stories: list[dict], days: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# HackerNews 信号报告",
        f"",
        f"> 生成时间: {now} | 范围: 最近 {days} 天 | 关注: AI/ML/Dev Tools",
        f"",
    ]

    if not stories:
        lines += ["*本期无相关讨论*", ""]
        return "\n".join(lines)

    # 按分类组织
    show_hn = [s for s in stories if classify_story(s) == "🛠️ Show HN"]
    ask_hn = [s for s in stories if classify_story(s) == "❓ Ask HN"]
    articles = [s for s in stories if classify_story(s) == "📰 文章"]

    def story_row(s):
        ts = datetime.fromtimestamp(s.get("time", 0), tz=timezone.utc).strftime("%m-%d")
        score = s.get("score", 0)
        comments = s.get("descendants", 0)
        title = s.get("title", "")[:60]
        url = s.get("url") or f"https://news.ycombinator.com/item?id={s['id']}"
        hn_url = f"https://news.ycombinator.com/item?id={s['id']}"
        return f"| [{title}]({url}) | ▲{score:,} | {comments} | {ts} | [讨论]({hn_url}) |"

    table_header = [
        "| 标题 | 分值 | 评论 | 日期 | 链接 |",
        "|------|------|------|------|------|",
    ]

    if show_hn:
        lines += [
            f"## 🛠️ Show HN — 新项目发布 ({len(show_hn)} 条)",
            "",
        ] + table_header + [story_row(s) for s in show_hn[:10]] + [""]

    if ask_hn:
        lines += [
            f"## ❓ Ask HN — 社区讨论 ({len(ask_hn)} 条)",
            "",
        ] + table_header + [story_row(s) for s in ask_hn[:8]] + [""]

    if articles:
        lines += [
            f"## 📰 高质量文章 ({len(articles)} 条)",
            "",
        ] + table_header + [story_row(s) for s in articles[:15]] + [""]

    # 自动提取洞察提示
    lines += [
        "---",
        "",
        "## 🧠 本期研究问题（需人工填写）",
        "",
        "从以上内容中，你观察到了什么趋势？填写你的判断：",
        "",
        "- **技术趋势**: ",
        "- **市场信号**: ",
        "- **对 HKUDS 项目的影响**: ",
        "- **值得追进的机会**: ",
        "",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="监控 HackerNews AI 相关内容")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--min-score", type=int, default=30, help="最低分值过滤")
    parser.add_argument("--limit", type=int, default=300, help="抓取前 N 条故事")
    args = parser.parse_args()

    LOGS_DIR.mkdir(exist_ok=True)

    print(f"🔍 抓取 HackerNews 最近 {args.days} 天 AI/ML 相关故事 (最低分: {args.min_score})...")

    # 同时抓 top + new + show HN
    story_types = ["topstories", "newstories", "showstories", "askstories"]
    all_ids = set()
    for st in story_types:
        ids = fetch_top_stories(st, limit=args.limit // len(story_types))
        all_ids.update(ids)
    print(f"  共 {len(all_ids)} 个 story ID 待检查")

    relevant = []
    checked = 0
    for sid in list(all_ids)[:args.limit]:
        story = fetch_story(sid)
        if not story:
            continue
        checked += 1
        if (is_recent(story, args.days)
                and story.get("score", 0) >= args.min_score
                and is_relevant(story)):
            relevant.append(story)

    relevant.sort(key=lambda x: x.get("score", 0), reverse=True)
    print(f"✅ 检查 {checked} 条，命中 {len(relevant)} 条相关内容")

    report = generate_report(relevant, args.days)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📝 报告已写入 {OUTPUT_FILE}")

    if relevant:
        print("\n🔥 Top 5:")
        for s in relevant[:5]:
            print(f"  ▲{s.get('score',0)} {s.get('title','')[:70]}")


if __name__ == "__main__":
    main()
