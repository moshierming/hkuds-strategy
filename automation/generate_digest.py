#!/usr/bin/env python3
"""
generate_digest.py
==================
汇合本周 GitHub 动态 + arXiv 新论文 + 机会日志，
生成一份 weekly digest markdown 文件。

用法:
    python automation/generate_digest.py

通常在 fetch_github_stats.py 和 arxiv_monitor.py 之后运行。
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / "logs"
DIGEST_DIR = ROOT / "logs" / "digests"


def read_file_safe(path: Path, default: str = "") -> str:
    """安全读取文件，不存在时返回默认值"""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return default


def get_git_log(n: int = 5) -> str:
    """获取最近几条 git commit"""
    try:
        result = subprocess.run(
            ["git", "log", f"-{n}", "--oneline", "--no-merges"],
            capture_output=True, text=True, cwd=ROOT
        )
        return result.stdout.strip()
    except Exception:
        return ""


def count_opportunities() -> int:
    """统计机会日志中的条目数"""
    opp_file = LOGS_DIR / "opportunities.md"
    if not opp_file.exists():
        return 0
    content = opp_file.read_text()
    return content.count("## [")


def load_top_repos(n: int = 5) -> list[dict]:
    """从 stats json 加载 Top N 仓库"""
    stats_file = LOGS_DIR / "github_stats.json"
    if not stats_file.exists():
        return []
    with open(stats_file) as f:
        data = json.load(f)
    repos = list(data.values())
    return sorted(repos, key=lambda x: x["stars"], reverse=True)[:n]


def generate_digest() -> str:
    now = datetime.now(timezone.utc)
    week_str = now.strftime("Week %W, %Y")
    date_str = now.strftime("%Y-%m-%d")

    lines = [
        f"# HKUDS 研究周报 · {week_str}",
        f"",
        f"> 生成时间: {date_str} | 这是一份自动生成的研究摘要",
        f"",
        f"---",
        f"",
    ]

    # ── Section 1: GitHub 动态 ──
    lines += [
        "## 1. GitHub 动态",
        "",
    ]
    top_repos = load_top_repos(5)
    if top_repos:
        lines += [
            "**Stars 排行 Top 5:**",
            "",
            "| 仓库 | Stars | Forks |",
            "|------|-------|-------|",
        ]
        for r in top_repos:
            lines.append(
                f"| [{r['name']}](https://github.com/HKUDS/{r['name']}) "
                f"| {r['stars']:,} | {r['forks']:,} |"
            )
        lines.append("")
    else:
        lines += ["*运行 `python automation/fetch_github_stats.py` 生成数据*", ""]

    # 变化报告摘录
    changes = read_file_safe(LOGS_DIR / "stats_changes.md")
    if changes:
        # 截取变化部分
        if "显著变化" in changes:
            start = changes.find("## 📈")
            end = changes.find("## 🔥")
            if start > 0 and end > 0:
                lines += [changes[start:end].strip(), ""]

    # ── Section 2: 新论文 ──
    lines += [
        "---",
        "",
        "## 2. arXiv 新论文",
        "",
    ]
    papers_content = read_file_safe(LOGS_DIR / "arxiv_papers.md")
    if papers_content and "无新论文" not in papers_content and "发现" in papers_content:
        # 提取论文标题列表
        for line in papers_content.split("\n"):
            if line.startswith("### "):
                title = line.replace("### ", "").strip()
                lines.append(f"- {title}")
        lines.append("")
        lines.append(f"📄 [查看完整论文报告](../logs/arxiv_papers.md)")
        lines.append("")
    else:
        lines += ["*本周暂无检测到新论文* | 或运行 `python automation/arxiv_monitor.py` 刷新", ""]

    # ── Section 3: 机会记录 ──
    opp_count = count_opportunities()
    lines += [
        "---",
        "",
        "## 3. 机会跟踪",
        "",
        f"当前记录: **{opp_count}** 个机会 → [查看完整列表](../logs/opportunities.md)",
        "",
    ]

    # ── Section 4: 本周行动 ──
    lines += [
        "---",
        "",
        "## 4. 待确认行动项",
        "",
        "从本周研究中提取的可执行行动（填写完成后勾选）：",
        "",
        "- [ ] [从 GitHub 动态中选一个有趣变化深入研究]",
        "- [ ] [从新论文中选一篇精读并记录洞察]",
        "- [ ] [推进一个机会日志中的具体行动]",
        "",
    ]

    # ── Section 5: 进度回顾 ──
    git_log = get_git_log()
    if git_log:
        lines += [
            "---",
            "",
            "## 5. 最近提交",
            "",
            "```",
            git_log,
            "```",
            "",
        ]

    lines += [
        "---",
        "",
        f"*由 `automation/generate_digest.py` 自动生成 · {date_str}*",
    ]

    return "\n".join(lines)


def main():
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)

    digest = generate_digest()

    # 保存到带日期的文件
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    digest_file = DIGEST_DIR / f"{date_str}.md"
    with open(digest_file, "w", encoding="utf-8") as f:
        f.write(digest)
    print(f"✅ 周报已生成: {digest_file}")

    # 同时更新 latest.md 快捷入口
    latest_file = LOGS_DIR / "latest_digest.md"
    with open(latest_file, "w", encoding="utf-8") as f:
        f.write(digest)
    print(f"📄 最新周报: {latest_file}")

    # 打印前几行预览
    preview = "\n".join(digest.split("\n")[:15])
    print(f"\n{'─'*50}\n{preview}\n{'─'*50}")


if __name__ == "__main__":
    main()
