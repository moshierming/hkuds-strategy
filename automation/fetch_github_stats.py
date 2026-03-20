#!/usr/bin/env python3
"""
fetch_github_stats.py
=====================
自动抓取 HKUDS 所有仓库的 GitHub 统计数据，
更新 logs/github_stats.json 并生成变化摘要。

用法:
    python automation/fetch_github_stats.py

依赖:
    pip install requests python-dotenv

环境变量 (可选但强烈建议, 避免 API 限速):
    GITHUB_TOKEN=ghp_xxxxxxxxxxxx
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("请先安装依赖: pip install requests")
    sys.exit(1)

# ───────────────────────────── 配置 ─────────────────────────────

HKUDS_ORG = "HKUDS"
ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / "logs"
STATS_FILE = LOGS_DIR / "github_stats.json"
CHANGES_FILE = LOGS_DIR / "stats_changes.md"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

token = os.environ.get("GITHUB_TOKEN")
if token:
    HEADERS["Authorization"] = f"Bearer {token}"
else:
    print("⚠️  未设置 GITHUB_TOKEN，API 限速为 60次/小时")


# ───────────────────────────── 获取数据 ─────────────────────────────

def fetch_all_repos(org: str) -> list[dict]:
    """获取组织的所有公开仓库"""
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/orgs/{org}/repos"
        resp = requests.get(
            url,
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "public"},
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"❌ API 错误 {resp.status_code}: {resp.text[:200]}")
            break
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def extract_stats(repo: dict) -> dict:
    """从 API 响应中提取关键统计"""
    return {
        "name": repo["name"],
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "watchers": repo["watchers_count"],
        "open_issues": repo["open_issues_count"],
        "language": repo["language"],
        "updated_at": repo["updated_at"],
        "created_at": repo["created_at"],
        "description": (repo["description"] or "")[:120],
        "topics": repo.get("topics", []),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# ───────────────────────────── 比较变化 ─────────────────────────────

def compute_changes(old_data: dict, new_data: dict) -> list[dict]:
    """比较新旧数据，找出值得关注的变化"""
    changes = []
    for name, new in new_data.items():
        old = old_data.get(name, {})
        delta_stars = new["stars"] - old.get("stars", new["stars"])
        delta_forks = new["forks"] - old.get("forks", new["forks"])

        if abs(delta_stars) >= 10 or abs(delta_forks) >= 3:
            changes.append({
                "repo": name,
                "stars": new["stars"],
                "delta_stars": delta_stars,
                "forks": new["forks"],
                "delta_forks": delta_forks,
            })
    # 按 star 增量排序
    return sorted(changes, key=lambda x: x["delta_stars"], reverse=True)


def generate_changes_report(changes: list[dict], all_stats: dict) -> str:
    """生成 Markdown 格式的变化报告"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# HKUDS GitHub 动态报告",
        f"",
        f"> 生成时间: {now}",
        f"",
    ]

    # Top repos by stars
    top_repos = sorted(all_stats.values(), key=lambda x: x["stars"], reverse=True)[:10]
    lines += [
        "## ⭐ Stars 排行 Top 10",
        "",
        "| 仓库 | Stars | Forks | 最近更新 |",
        "|------|-------|-------|---------|",
    ]
    for r in top_repos:
        updated = r["updated_at"][:10]
        lines.append(
            f"| [{r['name']}](https://github.com/{HKUDS_ORG}/{r['name']}) "
            f"| {r['stars']:,} | {r['forks']:,} | {updated} |"
        )

    if changes:
        lines += [
            "",
            "## 📈 本周显著变化 (±10+ stars 或 ±3+ forks)",
            "",
            "| 仓库 | Stars | Δ Stars | Forks | Δ Forks |",
            "|------|-------|---------|-------|---------|",
        ]
        for c in changes:
            s_sign = "+" if c["delta_stars"] >= 0 else ""
            f_sign = "+" if c["delta_forks"] >= 0 else ""
            lines.append(
                f"| [{c['repo']}](https://github.com/{HKUDS_ORG}/{c['repo']}) "
                f"| {c['stars']:,} | {s_sign}{c['delta_stars']:,} "
                f"| {c['forks']:,} | {f_sign}{c['delta_forks']:,} |"
            )
    else:
        lines += ["", "## 📊 本周无显著变化", ""]

    # Recently active
    recent = sorted(all_stats.values(), key=lambda x: x["updated_at"], reverse=True)[:5]
    lines += [
        "",
        "## 🔥 最近活跃仓库",
        "",
    ]
    for r in recent:
        lines.append(f"- **{r['name']}** — {r['updated_at'][:10]} | {r['description'][:60]}")

    return "\n".join(lines)


# ───────────────────────────── 主流程 ─────────────────────────────

def main():
    LOGS_DIR.mkdir(exist_ok=True)

    # 加载历史数据
    old_data = {}
    if STATS_FILE.exists():
        with open(STATS_FILE) as f:
            old_data = json.load(f)
        print(f"📂 已加载历史数据: {len(old_data)} 个仓库")

    # 抓取最新数据
    print(f"🔍 正在抓取 {HKUDS_ORG} 的仓库数据...")
    repos = fetch_all_repos(HKUDS_ORG)
    print(f"✅ 共获取 {len(repos)} 个仓库")

    new_data = {r["name"]: extract_stats(r) for r in repos}

    # 计算变化
    changes = compute_changes(old_data, new_data)
    if changes:
        print(f"📈 {len(changes)} 个仓库有显著变化")
    else:
        print("📊 本周无显著变化")

    # 保存数据
    with open(STATS_FILE, "w") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    print(f"💾 数据已保存到 {STATS_FILE}")

    # 生成报告
    report = generate_changes_report(changes, new_data)
    with open(CHANGES_FILE, "w") as f:
        f.write(report)
    print(f"📝 变化报告已写入 {CHANGES_FILE}")

    # 打印摘要
    total_stars = sum(r["stars"] for r in new_data.values())
    print(f"\n{'='*50}")
    print(f"🌟 HKUDS 总 Stars: {total_stars:,}")
    print(f"📦 仓库数: {len(new_data)}")
    if changes:
        print(f"📈 Top 变化: {changes[0]['repo']} +{changes[0]['delta_stars']} stars")


if __name__ == "__main__":
    main()
