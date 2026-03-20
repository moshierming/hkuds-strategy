#!/usr/bin/env python3
"""
arxiv_monitor.py
================
监控 arXiv 上 HKUDS 团队的新论文，输出摘要和推荐行动。

用法:
    python automation/arxiv_monitor.py
    python automation/arxiv_monitor.py --days 7   # 查最近 7 天

依赖:
    pip install requests feedparser
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import feedparser
    import requests
except ImportError:
    print("请先安装依赖: pip install requests feedparser")
    sys.exit(1)

# ───────────────────────────── 配置 ─────────────────────────────

ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / "logs"
PAPERS_FILE = LOGS_DIR / "arxiv_papers.md"

# 搜索关键词 (OR 关系)
SEARCH_QUERIES = [
    # 作者/机构
    "au:yao_junliang",
    "au:chen_guanglin",
    # 主要方向关键词
    "ti:LightRAG",
    "ti:GraphRAG",
    "ti:knowledge+graph+retrieval+augmented",
    "ti:graph+neural+network+recommendation",
    "ti:spatial+temporal+urban+computing",
    "ti:self+supervised+graph",
    "ti:contrastive+learning+recommendation",
    "ti:diffusion+model+recommendation",
    "ti:LLM+recommendation",
    "ti:graph+foundation+model",
]

ARXIV_API = "http://export.arxiv.org/api/query"


# ───────────────────────────── 抓取论文 ─────────────────────────────

def fetch_arxiv(query: str, max_results: int = 5) -> list[dict]:
    """查询 arXiv API，返回论文列表"""
    params = {
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }
    try:
        resp = requests.get(ARXIV_API, params=params, timeout=15)
        feed = feedparser.parse(resp.text)
        papers = []
        for entry in feed.entries:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            papers.append({
                "title": entry.title.replace("\n", " ").strip(),
                "authors": [a.name for a in entry.authors],
                "summary": entry.summary[:300].replace("\n", " "),
                "link": entry.link,
                "published": published,
                "arxiv_id": entry.id.split("/abs/")[-1],
            })
        return papers
    except Exception as e:
        print(f"⚠️  查询失败 ({query}): {e}")
        return []


def is_relevant(paper: dict, cutoff_date: datetime) -> bool:
    """判断论文是否在截止日期之后"""
    return paper["published"] >= cutoff_date


def deduplicate(papers: list[dict]) -> list[dict]:
    """按 arxiv_id 去重"""
    seen = set()
    result = []
    for p in papers:
        if p["arxiv_id"] not in seen:
            seen.add(p["arxiv_id"])
            result.append(p)
    return result


# ───────────────────────────── 生成报告 ─────────────────────────────

def generate_report(papers: list[dict], days: int) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# arXiv 论文监控报告",
        f"",
        f"> 生成时间: {now} | 时间范围: 最近 {days} 天",
        f"",
    ]

    if not papers:
        lines += [
            f"## 最近 {days} 天无新论文",
            "",
            "搜索关键词未命中新内容，可能需要调整查询策略。",
        ]
        return "\n".join(lines)

    lines += [
        f"## 发现 {len(papers)} 篇相关论文",
        "",
    ]

    for p in papers:
        date_str = p["published"].strftime("%Y-%m-%d")
        authors_str = ", ".join(p["authors"][:3])
        if len(p["authors"]) > 3:
            authors_str += f" 等{len(p['authors'])}人"

        lines += [
            f"### {p['title']}",
            f"",
            f"- **作者**: {authors_str}",
            f"- **时间**: {date_str}",
            f"- **链接**: {p['link']}",
            f"",
            f"> {p['summary']}...",
            f"",
            "**可能的行动**:",
            "- [ ] 阅读全文，评估技术贡献",
            "- [ ] 检查是否有开源代码",
            "- [ ] 判断商业化可能性",
            "",
            "---",
            "",
        ]

    return "\n".join(lines)


# ───────────────────────────── 主流程 ─────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="监控 arXiv 新论文")
    parser.add_argument("--days", type=int, default=7, help="查最近多少天的论文 (默认: 7)")
    args = parser.parse_args()

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    print(f"🔍 搜索 arXiv，时间范围: 最近 {args.days} 天 (>{cutoff.strftime('%Y-%m-%d')})")

    all_papers = []
    for query in SEARCH_QUERIES:
        papers = fetch_arxiv(query, max_results=5)
        recent = [p for p in papers if is_relevant(p, cutoff)]
        if recent:
            print(f"  ✅ [{query}] 命中 {len(recent)} 篇")
        all_papers.extend(recent)

    all_papers = deduplicate(all_papers)
    all_papers.sort(key=lambda x: x["published"], reverse=True)
    print(f"\n📚 去重后共 {len(all_papers)} 篇新论文")

    LOGS_DIR.mkdir(exist_ok=True)
    report = generate_report(all_papers, args.days)
    with open(PAPERS_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📝 报告已写入 {PAPERS_FILE}")

    # 快速打印
    if all_papers:
        print("\n🔥 最新论文:")
        for p in all_papers[:5]:
            print(f"  • {p['title'][:70]}")
            print(f"    {p['link']}")


if __name__ == "__main__":
    main()
