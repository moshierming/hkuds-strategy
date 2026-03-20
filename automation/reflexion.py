#!/usr/bin/env python3
"""
reflexion.py
============
假设追踪与反思循环。

工作原理:
  1. 从 logs/digests/ 读取历史情报简报，提取所有假设
  2. 将假设与当期信号做对比，评估证据强度
  3. 在足够多周次后标记假设为 VALIDATED / FALSIFIED / OPEN
  4. 将已验证的洞察追加到 logs/insights_log.md
  5. 将完整追踪记录写入 logs/reflexion_log.md

用法:
    python automation/reflexion.py
    python automation/reflexion.py --update-insights   # 自动追加到 insights_log

输出:
    logs/reflexion_log.md        — 假设追踪数据库（所有时期）
    logs/insights_log.md         — 已验证洞察追加 (--update-insights 时)
"""

import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / "logs"
DIGESTS_DIR = LOGS_DIR / "digests"
REFLEXION_LOG = LOGS_DIR / "reflexion_log.md"
INSIGHTS_LOG = LOGS_DIR / "insights_log.md"
SIGNAL_BRIEF = LOGS_DIR / "intelligence_brief.md"

# ─────────────────────────────────────────────────────────────────────────────
# 解析器
# ─────────────────────────────────────────────────────────────────────────────

# 假设块格式（来自 signal_intelligence.py 的输出）:
# ### 假设N: [CONFIDENCE] 标题
# **预测**: ...
# **含义**: ...
# **证伪条件**: ...
_HYP_PATTERN = re.compile(
    r"#{2,3}\s*假设\s*(\d+)[:\s]+\[(\w[\w\s\-]*)\]\s+(.+?)(?=\n)\n?"
    r"(?:.*?\*\*预测\*\*\s*[:：]\s*(.+?)(?=\n|\*\*))?",
    re.DOTALL,
)
_FALSIFIER_PATTERN = re.compile(r"\*\*证伪条件\*\*\s*[:：]\s*(.+?)(?=\n###|\n##|$)", re.DOTALL)
_IMPLICATION_PATTERN = re.compile(r"\*\*含义\*\*\s*[:：]\s*(.+?)(?=\n\*\*|$)", re.DOTALL)
_DATE_PATTERN = re.compile(r"生成时间:\s*(\d{4}-\d{2}-\d{2})")


def parse_hypotheses_from_brief(text: str, date_str: str) -> list[dict]:
    """从一期简报文本中提取假设列表。

    支持两种字段命名风格:
      新版: **判断**: / **对 HKUDS 的含义**: / **如何证伪**:
      旧版: **预测**: / **含义**: / **证伪条件**:
    """
    hypotheses = []
    # 找到假设部分 — 用 \n##[^#] 防止 \n### 触发截断
    section_match = re.search(r"##\s*[🔮💡]\s*可证伪假设.+?(?=\n##[^#]|\Z)", text, re.DOTALL)
    if not section_match:
        # fallback: 任何包含"假设"的 ## 节
        section_match = re.search(r"##\s+[^\n]*假设[^\n]*\n.+?(?=\n##[^#]|\Z)", text, re.DOTALL)
    if not section_match:
        return hypotheses
    section = section_match.group()

    # 分割各个假设块 (### 假设 N)
    blocks = re.split(r"(?=###\s*假设\s*\d)", section)
    for block in blocks:
        if not re.match(r"###\s*假设", block.strip()):
            continue

        # 匹配: ### 假设 1 🟡 [MEDIUM-HIGH]
        hyp_match = re.search(
            r"###\s*假设\s*\d+\s*\S*\s*\[([^\]]+)\]\s*(?:\n|$)", block
        )
        if not hyp_match:
            continue
        confidence = hyp_match.group(1).strip()

        # 判断/预测字段 (两种风格)
        pred_match = (
            re.search(r"\*\*判断\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n###|$)", block, re.DOTALL)
            or re.search(r"\*\*预测\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n###|$)", block, re.DOTALL)
        )
        impl_match = (
            re.search(r"\*\*对 HKUDS 的含义\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n###|$)", block, re.DOTALL)
            or re.search(r"\*\*含义\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n###|$)", block, re.DOTALL)
        )
        fals_match = (
            re.search(r"\*\*如何证伪\*\*\s*[:：]\s*(.+?)(?=\n###|\Z)", block, re.DOTALL)
            or re.search(r"\*\*证伪条件\*\*\s*[:：]\s*(.+?)(?=\n###|\Z)", block, re.DOTALL)
        )
        # 从 **支撑信号** 提取 repo 短名 — 用作精确证据匹配词
        signals_match = re.search(r"\*\*支撑信号\*\*\s*[:：]\s*(.+?)(?=\n\*\*|\n###|$)", block, re.DOTALL)
        seed_repos: list[str] = []
        if signals_match:
            for part in re.split(r"[,，、\s]+", signals_match.group(1)):
                # 取 owner/repo 中的 repo 部分
                repo = part.strip().split("/")[-1].strip().lower()
                if repo:
                    seed_repos.append(repo)

        title = pred_match.group(1).strip()[:120] if pred_match else f"[假设 from {date_str}]"

        hypotheses.append({
            "date": date_str,
            "confidence": confidence,
            "title": title,
            "prediction": pred_match.group(1).strip() if pred_match else "",
            "implication": impl_match.group(1).strip() if impl_match else "",
            "falsifier": fals_match.group(1).strip() if fals_match else "",
            "seed_repos": seed_repos,   # 精确 repo 关键词
        })
    return hypotheses


def load_all_digests() -> list[tuple[str, str]]:
    """加载 logs/digests/ 中的所有历史简报，返回 [(date, text), ...].

    同日期去重: 优先保留 YYYY-MM-DD-intelligence.md，其次取排序最后的文件。
    """
    if not DIGESTS_DIR.exists():
        return []
    # 按文件名排序后收集，优先 -intelligence.md
    by_date: dict[str, Path] = {}
    for path in sorted(DIGESTS_DIR.glob("*.md")):
        if path.name.startswith("."):
            continue
        date_match = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
        if not date_match:
            continue
        date_str = date_match.group(1)
        existing = by_date.get(date_str)
        if existing is None:
            by_date[date_str] = path
        elif "-intelligence" in path.name:
            # 优先使用 LLM 格式的 digest
            by_date[date_str] = path
    return [
        (date_str, path.read_text(encoding="utf-8"))
        for date_str, path in sorted(by_date.items())
    ]


def load_current_brief() -> Optional[str]:
    if SIGNAL_BRIEF.exists():
        return SIGNAL_BRIEF.read_text(encoding="utf-8")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 证据评估 — 简单关键词 heuristic
# ─────────────────────────────────────────────────────────────────────────────

# 假设主题 → 支撑信号关键词
HYPOTHESIS_EVIDENCE_KEYWORDS = {
    "claude code": [
        "claude code", "claude-code", "everything-claude", "learn-claude",
        "claude ecosystem", "claude hud",
    ],
    "cursor": ["cursor", "cursor.sh", "cursor ide", "cursor ai"],
    "rag infrastructure": [
        "openrag", "openviking", "cognee", "hindsight", "rag api",
        "rag sdk", "context database", "hosted rag",
    ],
    "lightrag hosted": [
        "lightrag api", "lightrag sdk", "lightrag cloud", "lightrag enterprise",
    ],
    "agent memory": [
        "memory", "agent memory", "long-term memory", "episodic memory",
        "persistent memory", "openviking", "cognee", "hindsight",
    ],
    "trading agent": [
        "trading", "finance agent", "stock agent", "quant", "market agent",
        "automated trading", "ai trader",
    ],
    "mcp protocol": ["mcp", "model context protocol", "mcp server", "mcp tool"],
    "multimodal": ["multimodal", "video", "vision agent", "image agent"],
}


def extract_signals_from_brief(text: str) -> list[str]:
    """从简报文本中提取所有信号（repo + 描述）为纯文本列表"""
    lines = []
    for line in text.split("\n"):
        if line.startswith("- [") or "momentum" in line.lower() or "⭐" in line:
            lines.append(line.lower())
    return lines


def score_evidence(hypothesis_title: str, hypothesis_text: str, signal_lines: list[str],
                   seed_repos: list[str] | None = None) -> dict:
    """
    对一个假设打分：
      - supporting_count: 多少个信号支持这个假设
      - opposing_count: 多少个信号对立
      - evidence_level: STRONG / MODERATE / WEAK / NONE

    匹配优先级:
      1. seed_repos — 从假设的**支撑信号**字段提取的精确 repo 短名
      2. HYPOTHESIS_EVIDENCE_KEYWORDS — 主题关键词集合
    """
    combined_query = (hypothesis_title + " " + hypothesis_text).lower()

    best_keywords: list[str] = list(seed_repos or [])

    # 添加主题关键词（只有在语义上匹配时）
    for theme, kws in HYPOTHESIS_EVIDENCE_KEYWORDS.items():
        # 用英文 theme key 和关键词列表双重检查
        if any(kw in combined_query for kw in kws):
            best_keywords.extend(kws)

    # 去重
    best_keywords = list(dict.fromkeys(best_keywords))

    if not best_keywords:
        # fallback：只用 seed_repos 的英文词（不在这里扩展到全文匹配，避免误报）
        return {"supporting_count": 0, "supporting_signals": [], "evidence_level": "NONE"}

    supporting_signals = []
    for line in signal_lines:
        if any(kw in line for kw in best_keywords):
            supporting_signals.append(line[:120])

    count = len(supporting_signals)
    if count >= 4:
        level = "STRONG"
    elif count >= 2:
        level = "MODERATE"
    elif count >= 1:
        level = "WEAK"
    else:
        level = "NONE"

    return {
        "supporting_count": count,
        "supporting_signals": supporting_signals[:5],
        "evidence_level": level,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 假设状态推断
# ─────────────────────────────────────────────────────────────────────────────

def infer_status(evidence_history: list[dict], weeks_elapsed: int) -> str:
    """
    根据多期证据历史推断假设状态：
      VALIDATED   — 5+ 强证据或 3+ 期连续中等证据
      TRENDING    — 近期有强/中等证据但未达阈值
      OPEN        — 证据不足或混合信号
      FALSIFIED   — 多期出现反向信号且正向信号消失
      PREMATURE   — 时间太短(<2 periods)
    """
    if weeks_elapsed < 2 or len(evidence_history) < 2:
        return "PREMATURE"

    strong_weeks = sum(1 for e in evidence_history if e.get("evidence_level") == "STRONG")
    moderate_weeks = sum(1 for e in evidence_history if e.get("evidence_level") in ("STRONG", "MODERATE"))
    none_weeks = sum(1 for e in evidence_history if e.get("evidence_level") == "NONE")
    total_supporting = sum(e.get("supporting_count", 0) for e in evidence_history)

    if strong_weeks >= 3 or (moderate_weeks >= 4 and total_supporting >= 10):
        return "VALIDATED"
    elif strong_weeks >= 1 or moderate_weeks >= 2:
        return "TRENDING"
    elif none_weeks >= len(evidence_history) and weeks_elapsed >= 8:
        return "FALSIFIED"
    else:
        return "OPEN"


# ─────────────────────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────────────────────

def build_reflexion_db() -> list[dict]:
    """
    构建假设追踪数据库：
      - 从所有历史 digest 读取假设
      - 从每一期 digest 中获取该期信号
      - 在每期信号上评估每个假设
      - 返回结构化追踪记录
    """
    digests = load_all_digests()
    current_brief = load_current_brief()

    # 所有简报 — 如果今日尚无 digest，才补入当期简报
    all_briefs: list[tuple[str, str]] = digests[:]
    if current_brief:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        existing_dates = {d for d, _ in digests}
        if today not in existing_dates:
            all_briefs.append((today, current_brief))

    print(f"  📁 历史 digest: {len(digests)} 期")

    # 第一步：收集所有曾经出现过的假设（去重）
    all_hypotheses: dict[str, dict] = {}  # key = title (归一化)
    for date, text in all_briefs:
        for hyp in parse_hypotheses_from_brief(text, date):
            key = re.sub(r"\s+", " ", hyp["title"].lower().strip())[:80]
            if key not in all_hypotheses:
                all_hypotheses[key] = hyp
                all_hypotheses[key]["first_seen"] = date
                all_hypotheses[key]["evidence_by_period"] = []

    print(f"  🧠 唯一假设数: {len(all_hypotheses)}")

    # 第二步：对每期简报，为每个假设评估证据
    for date, text in all_briefs:
        signal_lines = extract_signals_from_brief(text)
        for key, hyp in all_hypotheses.items():
            evidence = score_evidence(
                hyp["title"], hyp.get("prediction", ""),
                signal_lines,
                seed_repos=hyp.get("seed_repos"),
            )
            evidence["date"] = date
            hyp["evidence_by_period"].append(evidence)

    # 第三步：推断最终状态
    for key, hyp in all_hypotheses.items():
        weeks = len(hyp["evidence_by_period"])
        hyp["status"] = infer_status(hyp["evidence_by_period"], weeks)
        hyp["total_supporting"] = sum(e.get("supporting_count", 0) for e in hyp["evidence_by_period"])

    return list(all_hypotheses.values())


def format_reflexion_report(records: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    validated = [r for r in records if r["status"] == "VALIDATED"]
    trending = [r for r in records if r["status"] == "TRENDING"]
    open_ = [r for r in records if r["status"] == "OPEN"]
    premature = [r for r in records if r["status"] == "PREMATURE"]
    falsified = [r for r in records if r["status"] == "FALSIFIED"]

    lines = [
        f"# 反思日志 · Reflexion Log",
        f"",
        f"> 更新时间: {now}",
        f"> 使用 `python automation/reflexion.py` 刷新",
        f"> 状态: PREMATURE(<2期) → OPEN → TRENDING → VALIDATED / FALSIFIED",
        f"",
        f"---",
        f"",
        f"## 摘要",
        f"",
        f"| 状态 | 数量 |",
        f"|------|------|",
        f"| ✅ VALIDATED | {len(validated)} |",
        f"| 📈 TRENDING | {len(trending)} |",
        f"| ❓ OPEN | {len(open_)} |",
        f"| 🕐 PREMATURE | {len(premature)} |",
        f"| ❌ FALSIFIED | {len(falsified)} |",
        f"",
    ]

    def format_record(r: dict, emoji: str) -> list[str]:
        out = [
            f"### {emoji} {r['title']}",
            f"",
            f"- **首次提出**: {r.get('first_seen', '?')}",
            f"- **置信标签**: {r.get('confidence', '?')}",
            f"- **追踪期数**: {len(r['evidence_by_period'])} 期",
            f"- **总支撑信号**: {r['total_supporting']} 条",
        ]
        if r.get("prediction"):
            out.append(f"- **预测**: {r['prediction'][:200]}")
        if r.get("falsifier"):
            out.append(f"- **证伪条件**: {r['falsifier'][:200]}")
        out.append("")
        out.append("**证据时间线**:")
        for ev in r["evidence_by_period"]:
            level_icon = {"STRONG": "🔥", "MODERATE": "📈", "WEAK": "💧", "NONE": "⬜"}.get(ev["evidence_level"], "?")
            out.append(f"  - {ev['date']} | {level_icon} {ev['evidence_level']} ({ev['supporting_count']} 条支撑)")
            for sig in ev.get("supporting_signals", [])[:2]:
                out.append(f"    - `{sig[:100]}`")
        out.append("")
        return out

    if validated:
        lines += ["---", "", "## ✅ 已验证假设 (VALIDATED)", ""]
        for r in sorted(validated, key=lambda x: -x["total_supporting"]):
            lines += format_record(r, "✅")

    if trending:
        lines += ["---", "", "## 📈 趋势验证中 (TRENDING)", ""]
        for r in sorted(trending, key=lambda x: -x["total_supporting"]):
            lines += format_record(r, "📈")

    if open_:
        lines += ["---", "", "## ❓ 开放假设 (OPEN)", ""]
        for r in open_:
            lines += format_record(r, "❓")

    if premature:
        lines += ["---", "", "## 🕐 过早评估 (PREMATURE — 需更多周期)", ""]
        for r in premature:
            lines += [
                f"- **{r['title']}** | 置信: {r.get('confidence','?')} | 首见: {r.get('first_seen','?')} | 支撑: {r['total_supporting']}条",
            ]
        lines.append("")

    if falsified:
        lines += ["---", "", "## ❌ 已证伪假设 (FALSIFIED)", ""]
        for r in falsified:
            lines += format_record(r, "❌")

    return "\n".join(lines)


def generate_validated_insights(records: list[dict]) -> list[str]:
    """从 VALIDATED / TRENDING 假设生成可追加到 insights_log 的洞察条目"""
    insights = []
    for r in records:
        if r["status"] not in ("VALIDATED", "TRENDING"):
            continue
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        level = "✅ 验证洞察" if r["status"] == "VALIDATED" else "📈 趋势洞察"
        insight_text = r.get("implication") or r.get("prediction") or r["title"]
        insights.append(
            f"\n### {level} [{date}] — {r['title']}\n\n"
            f"> 来源: reflexion 追踪 | 置信: {r.get('confidence','?')} | "
            f"追踪期数: {len(r['evidence_by_period'])} | 支撑信号: {r['total_supporting']}\n\n"
            f"{insight_text}\n"
        )
    return insights


def append_to_insights_log(insights: list[str]) -> None:
    if not insights:
        print("  ℹ️  无新增洞察可写入 insights_log")
        return
    existing = INSIGHTS_LOG.read_text(encoding="utf-8") if INSIGHTS_LOG.exists() else ""
    to_add = []
    for insight in insights:
        # 避免重复追加同一洞察（按标题行去重）
        title_line = insight.strip().split("\n")[0]
        if title_line not in existing:
            to_add.append(insight)
    if not to_add:
        print("  ℹ️  所有洞察已存在于 insights_log，无重复追加")
        return
    with INSIGHTS_LOG.open("a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(to_add))
    print(f"  ✅ 追加 {len(to_add)} 条洞察到 insights_log.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="反思循环 — 假设追踪与验证")
    parser.add_argument("--update-insights", action="store_true", help="将已验证洞察追加到 insights_log.md")
    args = parser.parse_args()

    print("🔄 反思分析启动...")
    records = build_reflexion_db()

    report = format_reflexion_report(records)
    REFLEXION_LOG.write_text(report, encoding="utf-8")
    print(f"  ✅ 反思日志: {REFLEXION_LOG.relative_to(ROOT)}")

    if args.update_insights:
        insights = generate_validated_insights(records)
        append_to_insights_log(insights)

    # 打印摘要
    validated = [r for r in records if r["status"] == "VALIDATED"]
    trending = [r for r in records if r["status"] == "TRENDING"]
    premature = [r for r in records if r["status"] == "PREMATURE"]
    print(f"\n📊 反思摘要:")
    print(f"   ✅ VALIDATED: {len(validated)}")
    print(f"   📈 TRENDING:  {len(trending)}")
    print(f"   ❓ OPEN/PREMATURE: {len(premature) + len([r for r in records if r['status'] == 'OPEN'])}")
    print(f"   ❌ FALSIFIED: {len([r for r in records if r['status'] == 'FALSIFIED'])}")

    if premature:
        print(f"\n  📋 待追踪假设 (当前处于 PREMATURE 状态):")
        for r in premature:
            print(f"     - [{r.get('confidence','?')}] {r['title'][:70]}")


if __name__ == "__main__":
    main()
