#!/usr/bin/env python3
"""
aggregate_signals.py
====================
信号聚合器：汇聚所有来源，生成跨渠道的综合周报。

不同于 generate_digest.py（只聚焦 HKUDS），
这里的视野是全局的：HKUDS + ProductHunt + HackerNews + GitHub Trending + arXiv

真正的洞察来自于**交叉**——
当 HN 的某个讨论、PH 的某个产品、和 HKUDS 的某个项目指向同一个方向时，
这才是值得押注的信号。

用法:
    python automation/aggregate_signals.py

输出:
    logs/weekly_signal_digest.md
    logs/digests/YYYY-MM-DD-full.md
"""

import json
import operator
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / "logs"
OUTPUT_FILE = LOGS_DIR / "weekly_signal_digest.md"


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def count_section(content: str, marker: str) -> int:
    """计数某个 marker 在内容中出现的次数"""
    return content.count(marker)


def extract_repo_names(stats_file: Path) -> dict:
    """从 github_stats.json 提取 Top 10 仓库"""
    if not stats_file.exists():
        return {}
    with open(stats_file) as f:
        data = json.load(f)
    repos = sorted(data.values(), key=lambda x: x["stars"], reverse=True)
    return {r["name"]: r["stars"] for r in repos[:10]}


def count_lines_with(content: str, keywords: list[str]) -> int:
    """统计包含关键词的行数（用于判断信号强度）"""
    count = 0
    for line in content.split("\n"):
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            count += 1
    return count


def detect_emerging_themes(contents: dict[str, str]) -> list[str]:
    """跨来源检测新兴主题（同时出现在多个来源才算信号）"""
    theme_keywords = {
        "RAG / 知识检索": ["rag", "retrieval", "knowledge graph", "graphrag", "lightrag"],
        "AI Agent": ["agent", "agentic", "autoagent", "autonomous", "multi-agent"],
        "边缘/本地 AI": ["local llm", "edge ai", "minirag", "private", "on-device", "offline"],
        "代码生成": ["code generation", "copilot", "cursor", "devin", "fastcode", "deepcode"],
        "多模态": ["multimodal", "vision", "video", "audio", "image"],
        "AI 助手/Bot": ["chatbot", "bot", "assistant", "nanobot", "openphone"],
        "MCP / 工具调用": ["mcp", "model context protocol", "tool use", "function calling"],
    }

    source_count = len([v for v in contents.values() if v])
    if source_count == 0:
        return []

    themes = []
    for theme, keywords in theme_keywords.items():
        hits = {}
        for source_name, content in contents.items():
            c = count_lines_with(content, keywords)
            if c > 0:
                hits[source_name] = c

        # 至少出现在 2+ 个来源才是「真信号」
        if len(hits) >= 2:
            total = sum(hits.values())
            hit_sources = ", ".join(f"{k}({v})" for k, v in hits.items())
            themes.append(f"**{theme}** — 来源覆盖: {hit_sources} | 总命中: {total}")

    return sorted(themes, key=lambda x: int(re.search(r"总命中: (\d+)", x).group(1)), reverse=True)


def generate_full_digest(contents: dict[str, str], top_repos: dict) -> str:
    now = datetime.now(timezone.utc)
    week_str = now.strftime("Week %W, %Y")
    date_str = now.strftime("%Y-%m-%d")

    lines = [
        f"# 全渠道信号周报 · {week_str}",
        f"",
        f"> 生成时间: {date_str}  ",
        f"> 信号来源: HKUDS GitHub + arXiv + ProductHunt + HackerNews + GitHub Trending",
        f"",
        f"---",
        f"",
        f"## 🧭 本周信号地图",
        f"",
        f"| 信号来源 | 状态 | 本周亮点 |",
        f"|---------|------|---------|",
    ]

    # 来源状态
    source_status = {
        "HKUDS GitHub": ("✅" if contents.get("github_stats") else "❌",
                         f"{len(top_repos)} 个仓库，TOP: "
                         + (list(top_repos.keys())[0] if top_repos else "N/A")),
        "arXiv 论文": ("✅" if contents.get("arxiv") else "❌",
                       f"{count_section(contents.get('arxiv',''), '### ')} 篇新论文"),
        "ProductHunt": ("✅" if contents.get("ph") else "⚠️",
                        f"{count_section(contents.get('ph',''), '| [')} 个产品" if contents.get("ph") else "未运行"),
        "HackerNews": ("✅" if contents.get("hn") else "⚠️",
                       f"{count_section(contents.get('hn',''), '| [')} 条讨论" if contents.get("hn") else "未运行"),
        "GitHub Trending": ("✅" if contents.get("trending") else "⚠️",
                             f"{count_section(contents.get('trending',''), '| [')} 个热门仓库" if contents.get("trending") else "未运行"),
    }
    for source, (status, desc) in source_status.items():
        lines.append(f"| {source} | {status} | {desc} |")

    # 跨渠道主题检测
    detection_contents = {
        "HKUDS": contents.get("github_stats", "") + contents.get("arxiv", ""),
        "PH": contents.get("ph", ""),
        "HN": contents.get("hn", ""),
        "Trending": contents.get("trending", ""),
    }
    emerging = detect_emerging_themes(detection_contents)

    lines += [
        "",
        "---",
        "",
        "## 🔭 跨渠道信号交叉分析",
        "",
        "> 以下主题在多个独立来源同时出现，提示真实市场热度。",
        "",
    ]
    if emerging:
        for theme in emerging:
            lines.append(f"- {theme}")
    else:
        lines.append("*本周各来源信号分散，无强聚合主题*")

    # HKUDS Top 10
    if top_repos:
        lines += [
            "",
            "---",
            "",
            "## 🏠 HKUDS 仓库 Top 10",
            "",
            "| 仓库 | Stars |",
            "|------|-------|",
        ]
        for name, stars in list(top_repos.items())[:10]:
            lines.append(f"| [{name}](https://github.com/HKUDS/{name}) | {stars:,} |")

    # 各来源摘要（精简版，避免重复）
    if contents.get("ph"):
        ph_lines = [l for l in contents["ph"].split("\n") if l.startswith("| [") and "voted" not in l.lower()]
        if ph_lines:
            lines += [
                "",
                "---",
                "",
                "## 🚀 ProductHunt 本周热门（前 5）",
                "",
                "| 产品 | Tagline | 票数 | Topics |",
                "|------|---------|------|--------|",
            ] + ph_lines[:5]

    if contents.get("hn"):
        hn_lines = [l for l in contents["hn"].split("\n") if l.startswith("| [")]
        if hn_lines:
            lines += [
                "",
                "---",
                "",
                "## 💬 HackerNews 热门讨论（前 5）",
                "",
                "| 标题 | 分值 | 评论 | 日期 | 链接 |",
                "|------|------|------|------|------|",
            ] + hn_lines[:5]

    if contents.get("trending"):
        tr_lines = [l for l in contents["trending"].split("\n") if l.startswith("| [")]
        if tr_lines:
            lines += [
                "",
                "---",
                "",
                "## 📈 GitHub Trending AI（前 5）",
                "",
                "| 仓库 | 描述 | ⭐ Stars | 新增 | 语言 |",
                "|------|------|---------|------|------|",
            ] + tr_lines[:5]

    # 反思区（人工填写）
    lines += [
        "",
        "---",
        "",
        "## 🪞 本周反思（人工填写）",
        "",
        "> 信号已由机器收集，洞察需要你来形成。",
        "",
        "**本周最重要的 1 个信号**:",
        "> ",
        "",
        "**这改变了我的哪个判断？**:",
        "> ",
        "",
        "**上周行动的结果**:",
        "> ",
        "",
        "**下周最值得做的 1 件事**:",
        "> ",
        "",
        "---",
        "",
        f"*由 `automation/aggregate_signals.py` 生成 · {date_str}*",
    ]

    return "\n".join(lines)


def main():
    LOGS_DIR.mkdir(exist_ok=True)

    # 读取所有来源
    contents = {
        "github_stats": read_file(LOGS_DIR / "stats_changes.md"),
        "arxiv": read_file(LOGS_DIR / "arxiv_papers.md"),
        "ph": read_file(LOGS_DIR / "producthunt_trends.md"),
        "hn": read_file(LOGS_DIR / "hackernews_signals.md"),
        "trending": read_file(LOGS_DIR / "github_trending.md"),
    }

    available = [k for k, v in contents.items() if v]
    missing = [k for k, v in contents.items() if not v]
    print(f"📡 已加载信号来源: {available}")
    if missing:
        print(f"⚠️  缺失来源: {missing} (先运行对应的 fetch_*.py)")

    top_repos = extract_repo_names(LOGS_DIR / "github_stats.json")

    digest = generate_full_digest(contents, top_repos)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(digest)
    print(f"✅ 全渠道周报已写入: {OUTPUT_FILE}")

    # 存档
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive = LOGS_DIR / "digests" / f"{date_str}-full.md"
    archive.parent.mkdir(exist_ok=True)
    with open(archive, "w", encoding="utf-8") as f:
        f.write(digest)
    print(f"📁 已存档: {archive}")

    # 预览
    preview = "\n".join(digest.split("\n")[:20])
    print(f"\n{'─'*60}\n{preview}\n{'─'*60}")


if __name__ == "__main__":
    main()
