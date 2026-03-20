#!/usr/bin/env python3
"""
fetch_github_trending.py
========================
抓取 GitHub Trending 中 AI/ML 领域的热门仓库，
不局限于 HKUDS，捕获全球维度的技术趋势。

用法:
    python automation/fetch_github_trending.py
    python automation/fetch_github_trending.py --lang python --since weekly

依赖:
    pip install requests beautifulsoup4

输出:
    logs/github_trending.md
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("请先安装依赖: pip install requests beautifulsoup4")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / "logs"
OUTPUT_FILE = LOGS_DIR / "github_trending.md"

TRENDING_URL = "https://github.com/trending"

# 抓取的语言 × 时间窗口组合
CONFIGS = [
    ("", "daily"),          # 所有语言 · 今日
    ("python", "weekly"),   # Python · 本周
    ("", "weekly"),         # 所有语言 · 本周（抓更多信号）
]

# 关键词过滤（命中任一即纳入）
AI_KEYWORDS = [
    "llm", "rag", "agent", "gpt", "transformer", "diffusion",
    "language model", "embedding", "vector", "knowledge graph",
    "inference", "fine-tun", "retrieval", "multimodal",
    "ai", "ml", "deep learning", "neural", "nlp",
    "copilot", "chatbot", "mcp",
]


def scrape_trending(language: str = "", since: str = "daily") -> list[dict]:
    """爬取 GitHub Trending 页面"""
    url = f"{TRENDING_URL}/{language}" if language else TRENDING_URL
    params = {"since": since}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        repos = []
        for article in soup.select("article.Box-row"):
            # 仓库名
            h2 = article.select_one("h2 a")
            if not h2:
                continue
            full_name = h2.get("href", "").strip("/")

            # 描述
            desc_el = article.select_one("p")
            description = desc_el.text.strip() if desc_el else ""

            # Star 数
            star_el = article.select("a.Link--muted")
            stars_text = star_el[0].text.strip().replace(",", "") if star_el else "0"
            try:
                stars = int(stars_text.replace("k", "000").replace(".", ""))
            except ValueError:
                stars = 0

            # 新增 stars
            gained_el = article.select_one("span.d-inline-block.float-sm-right")
            stars_gained = gained_el.text.strip() if gained_el else ""

            # 语言
            lang_el = article.select_one("span[itemprop='programmingLanguage']")
            repo_lang = lang_el.text.strip() if lang_el else ""

            repos.append({
                "full_name": full_name,
                "url": f"https://github.com/{full_name}",
                "description": description[:200],
                "stars": stars,
                "stars_gained": stars_gained,
                "language": repo_lang,
                "since": since,
            })
        return repos
    except Exception as e:
        print(f"  ⚠️  爬取失败 ({language}/{since}): {e}")
        return []


def is_ai_related(repo: dict) -> bool:
    """判断是否 AI 相关"""
    text = f"{repo['full_name']} {repo['description']}".lower()
    return any(kw in text for kw in AI_KEYWORDS)


def deduplicate(repos: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for r in repos:
        if r["full_name"] not in seen:
            seen.add(r["full_name"])
            result.append(r)
    return result


def generate_report(repos: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# GitHub Trending AI/ML 报告",
        f"",
        f"> 生成时间: {now} | 来源: GitHub Trending (全球，不限 HKUDS)",
        f"",
    ]

    if not repos:
        lines += ["*无相关结果*", ""]
        return "\n".join(lines)

    all_repos = sorted(repos, key=lambda x: x["stars"], reverse=True)

    lines += [
        f"## ⭐ AI/ML 热门仓库 (共 {len(all_repos)} 个)",
        "",
        "| 仓库 | 描述 | ⭐ Stars | 新增 | 语言 |",
        "|------|------|---------|------|------|",
    ]
    for r in all_repos[:25]:
        desc = r["description"][:50] + "..." if len(r["description"]) > 50 else r["description"]
        gained = r["stars_gained"].replace("stars this week", "").replace("stars today", "").strip()
        lines.append(
            f"| [{r['full_name']}]({r['url']}) | {desc} | {r['stars']:,} | {gained} | {r['language']} |"
        )

    lines += [
        "",
        "## 🏆 值得深入研究的 Top 5",
        "",
    ]
    for r in all_repos[:5]:
        lines += [
            f"### [{r['full_name']}]({r['url']})",
            f"",
            f"> {r['description']}",
            f"",
            f"- **Stars**: {r['stars']:,} | **新增**: {r['stars_gained']}",
            f"- **语言**: {r['language']}",
            f"",
            "**研究问题**:",
            "- [ ] 核心创新点是什么？与 HKUDS 的方向是竞争还是互补？",
            "- [ ] 是否有商业化路径？作者团队什么背景？",
            "- [ ] 能否基于它做延伸产品？",
            "",
        ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="抓取 GitHub Trending AI/ML 仓库")
    parser.add_argument("--lang", type=str, default="", help="过滤编程语言")
    parser.add_argument("--since", type=str, default="", help="daily/weekly/monthly")
    args = parser.parse_args()

    LOGS_DIR.mkdir(exist_ok=True)

    if args.lang or args.since:
        configs = [(args.lang, args.since or "weekly")]
    else:
        configs = CONFIGS

    print(f"🔍 抓取 GitHub Trending AI/ML 仓库...")
    all_repos = []
    for lang, since in configs:
        label = f"{lang or 'all'}/{since}"
        repos = scrape_trending(lang, since)
        ai_repos = [r for r in repos if is_ai_related(r)]
        print(f"  [{label}] 找到 {len(repos)} 个仓库，{len(ai_repos)} 个 AI 相关")
        all_repos.extend(ai_repos)

    all_repos = deduplicate(all_repos)
    all_repos.sort(key=lambda x: x["stars"], reverse=True)
    print(f"\n📦 去重后共 {len(all_repos)} 个 AI 相关热门仓库")

    report = generate_report(all_repos)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"📝 报告已写入 {OUTPUT_FILE}")

    if all_repos:
        print("\n🔥 Top 5:")
        for r in all_repos[:5]:
            print(f"  ⭐{r['stars']:,} {r['full_name']} — {r['description'][:60]}")


if __name__ == "__main__":
    main()
