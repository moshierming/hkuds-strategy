#!/usr/bin/env python3
"""
fetch_producthunt.py
====================
抓取 ProductHunt 每日/每周热门，聚焦 AI、开发者工具、生产力类目。
无需 API Key（公开 GraphQL，限速约 100次/小时）。

用法:
    python automation/fetch_producthunt.py
    python automation/fetch_producthunt.py --days 7   # 最近7天

依赖:
    pip install requests

输出:
    logs/producthunt_trends.md
"""

import argparse
import json
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
OUTPUT_FILE = LOGS_DIR / "producthunt_trends.md"

PH_API = "https://api.producthunt.com/v2/api/graphql"

# 目标 topics (slug)
TARGET_TOPICS = [
    "artificial-intelligence",
    "developer-tools",
    "productivity",
    "machine-learning",
    "bots",
    "open-source",
    "generative-ai",
    "llm",
    "automation",
]

# GraphQL 查询：按 topic 获取热门产品
QUERY = """
query TopicPosts($topic: String!, $after: String) {
  topic(slug: $topic) {
    name
    posts(order: VOTES, after: $after, first: 10) {
      edges {
        node {
          id
          name
          tagline
          description
          votesCount
          commentsCount
          createdAt
          url
          website
          topics {
            edges {
              node { name slug }
            }
          }
          makers {
            name
          }
        }
      }
    }
  }
}
"""


def fetch_topic_posts(topic_slug: str, token: str = "") -> list[dict]:
    """获取某 topic 下的热门产品"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.post(
            PH_API,
            headers=headers,
            json={"query": QUERY, "variables": {"topic": topic_slug}},
            timeout=15,
        )
        data = resp.json()
        topic_data = data.get("data", {}).get("topic")
        if not topic_data:
            return []
        edges = topic_data.get("posts", {}).get("edges", [])
        posts = []
        for edge in edges:
            node = edge["node"]
            posts.append({
                "id": node["id"],
                "name": node["name"],
                "tagline": node["tagline"],
                "description": (node.get("description") or "")[:200],
                "votes": node["votesCount"],
                "comments": node["commentsCount"],
                "created_at": node["createdAt"],
                "url": node["url"],
                "website": node.get("website", ""),
                "topics": [
                    e["node"]["name"]
                    for e in node.get("topics", {}).get("edges", [])
                ],
            })
        return posts
    except Exception as e:
        print(f"  ⚠️  {topic_slug} 获取失败: {e}")
        return []


def is_recent(post: dict, days: int) -> bool:
    """判断是否在最近 N 天内发布"""
    try:
        created = datetime.fromisoformat(post["created_at"].replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return created >= cutoff
    except Exception:
        return True  # 解析失败时不过滤


def deduplicate(posts: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for p in posts:
        if p["id"] not in seen:
            seen.add(p["id"])
            result.append(p)
    return result


def generate_report(posts: list[dict], days: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# ProductHunt AI/Dev 趋势报告",
        f"",
        f"> 生成时间: {now} | 范围: 最近 {days} 天 | 类目: AI/开发工具/生产力",
        f"",
    ]

    if not posts:
        lines += ["*本期无新产品发现*", ""]
        return "\n".join(lines)

    # Top 20 by votes
    top_posts = sorted(posts, key=lambda x: x["votes"], reverse=True)[:20]

    lines += [
        f"## 🔥 热门产品 Top {len(top_posts)} (按票数排序)",
        "",
        "| 产品 | Tagline | 票数 | 评论 | Topics |",
        "|------|---------|------|------|--------|",
    ]
    for p in top_posts:
        topics_str = ", ".join(p["topics"][:3]) if p["topics"] else "-"
        name_link = f"[{p['name']}]({p['url']})"
        tagline = p["tagline"][:50] + "..." if len(p["tagline"]) > 50 else p["tagline"]
        lines.append(
            f"| {name_link} | {tagline} | ▲{p['votes']:,} | {p['comments']} | {topics_str} |"
        )

    lines += [
        "",
        "## 💡 值得关注的产品（摘要）",
        "",
    ]
    for p in top_posts[:5]:
        lines += [
            f"### {p['name']}",
            f"",
            f"- **Tagline**: {p['tagline']}",
            f"- **链接**: {p['url']}",
            f"- **票数**: ▲{p['votes']:,} | 评论: {p['comments']}",
        ]
        if p["description"]:
            lines.append(f"- **描述**: {p['description'][:150]}...")
        lines += [
            f"",
            "**研究问题**:",
            "- [ ] 这解决了什么问题？和 HKUDS 的哪个方向有交叉？",
            "- [ ] 商业模型是什么？是否有启发？",
            "- [ ] 技术栈如何？有没有开源部分？",
            "",
        ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="抓取 ProductHunt 趋势")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--token", type=str, default="", help="PH API Token (可选)")
    args = parser.parse_args()

    import os
    token = args.token or os.environ.get("PH_TOKEN", "")

    LOGS_DIR.mkdir(exist_ok=True)

    print(f"🔍 抓取 ProductHunt 最近 {args.days} 天的 AI/Dev 产品...")
    if not token:
        print("⚠️  未设置 PH_TOKEN，使用公开 API（有限速）")

    all_posts = []
    for topic in TARGET_TOPICS:
        posts = fetch_topic_posts(topic, token)
        recent = [p for p in posts if is_recent(p, args.days)]
        if recent:
            print(f"  ✅ [{topic}] {len(recent)} 个近期产品")
        all_posts.extend(recent)

    all_posts = deduplicate(all_posts)
    all_posts.sort(key=lambda x: x["votes"], reverse=True)
    print(f"\n📦 去重后共 {len(all_posts)} 个产品")

    report = generate_report(all_posts, args.days)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📝 报告已写入 {OUTPUT_FILE}")

    if all_posts:
        print("\n🔥 Top 5:")
        for p in all_posts[:5]:
            print(f"  ▲{p['votes']:,} {p['name']} — {p['tagline'][:60]}")


if __name__ == "__main__":
    main()
