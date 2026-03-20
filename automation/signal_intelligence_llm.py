#!/usr/bin/env python3
"""
signal_intelligence_llm.py  (新版：LLM 驱动)
============================================
情报分析引擎 — 从原始信号到结构化洞察。

v2 架构：
  数据收集层  → fetch_*.py（保持不变）
  信号加载层  → 直接读取 markdown 原文，无需复杂解析
  分析层      → LLM（替换规则逻辑）— 主题/威胁/假设/白空间全部由 LLM 生成
  输出层      → Python 格式化 LLM JSON → Markdown（与 reflexion.py 输出格式兼容）

用法:
    python automation/signal_intelligence_llm.py
    python automation/signal_intelligence_llm.py --dry-run  # 打印 prompt 不调用 LLM

输出:
    logs/intelligence_brief.md   — 情报简报（格式与 reflexion.py 兼容）
    logs/threat_radar.md         — 威胁雷达
    logs/digests/YYYY-MM-DD-intelligence.md — 存档
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / "logs"

# ─────────────────────────────────────────────────────────────────────────────
# LLM 客户端
# ─────────────────────────────────────────────────────────────────────────────

def make_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        base_url=os.environ.get("ANTHROPIC_BASE_URL"),
    )

LLM_MODEL = os.environ.get("ANTHROPIC_MODEL", "qwen3-coder-plus")
MAX_TOKENS = 4096

# ─────────────────────────────────────────────────────────────────────────────
# HKUDS 投资组合上下文 — 提供给 LLM
# ─────────────────────────────────────────────────────────────────────────────

HKUDS_CONTEXT = """
# HKUDS 研究组投资组合

HKUDS 是香港大学数据科学实验室，核心开源项目如下：

| 项目 | Stars | 定位 | 竞争敏感度 |
|------|-------|------|-----------|
| LightRAG | 38,000 | 异构知识图谱 RAG 框架，核心创新是图+向量双索引 | HIGH |
| nanobot | 35,000 | 多平台 IM Agent SDK（Telegram/Discord/Slack/WeChat） | LOW |
| GraphGPT | 8,000 | 图神经网络+LLM 预训练框架 | LOW |
| AutoAgent | 5,000 | Zero-Code LLM Agent 框架，自然语言构建 agent | HIGH |
| VideoRAG | 3,000 | 超长视频 RAG，支持跨视频检索 | MEDIUM |
| RAG-Anything | 4,000 | 多模态 RAG（PDF/图片/代码/表格） | MEDIUM |
| MiniRAG | 1,800 | 边缘/离线 RAG，针对 SLM 优化 | MEDIUM |
| SepLLM | 2,000 | LLM Token 效率压缩（KV Cache/长上下文） | MEDIUM |
| AI-Researcher | - | 自主 AI 研究 Agent | HIGH |
| FastCode | - | LLM 加速代码生成 | MEDIUM |
| AnyTool | - | 工具调用框架 | MEDIUM |
| AI-Trader | - | AI 量化交易 Agent | MEDIUM |
| ClawTeam | - | 多 Agent 协作框架 | HIGH |
| DeepTutor | - | AI 教学辅导 Agent | LOW |

**核心优势**: 学术深度、图结构处理（LightRAG/GraphGPT）、多模态 RAG
**相对弱项**: 产品化、工具化、商业生态集成
"""

# ─────────────────────────────────────────────────────────────────────────────
# 信号加载器 — 直接读取 markdown 原文，LLM 自行理解
# ─────────────────────────────────────────────────────────────────────────────

SOURCE_FILES = {
    "GitHub Trending": LOGS_DIR / "github_trending.md",
    "HackerNews":      LOGS_DIR / "hackernews_signals.md",
    "ProductHunt":     LOGS_DIR / "producthunt_trends.md",
}

MAX_CHARS_PER_SOURCE = 6000

def load_signals() -> tuple[dict[str, str], dict[str, int]]:
    """
    Returns:
        sources_text: {source_name: truncated_markdown}
        counts: {source_name: estimated_item_count}
    """
    sources: dict[str, str] = {}
    counts: dict[str, int] = {}
    for name, path in SOURCE_FILES.items():
        if not path.exists():
            sources[name] = ""
            counts[name] = 0
            continue
        text = path.read_text(encoding="utf-8")
        # Estimate count by counting markdown table rows
        rows = len([l for l in text.split("\n") if l.startswith("| [") or l.startswith("| **")])
        counts[name] = rows
        # Truncate to budget
        sources[name] = text[:MAX_CHARS_PER_SOURCE]
    return sources, counts


# ─────────────────────────────────────────────────────────────────────────────
# LLM 分析核心
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""你是 HKUDS 研究组的情报分析师。
你的任务：从多源信号数据（GitHub Trending / HackerNews / ProductHunt）中提炼出对 HKUDS 有战略价值的洞察。

{HKUDS_CONTEXT}

分析要求：
1. **主题聚类**：识别 3-8 个正在涌现的技术/市场主题，每个主题需包含代表性信号和 HKUDS 相关性
2. **威胁检测**：找出与 HKUDS 各项目直接竞争或替代的外部信号，评估威胁等级
3. **白空间识别**：市场有明显信号但 HKUDS 没有覆盖的领域（机会区）
4. **假设生成**：生成 3-5 个可证伪的预测，聚焦未来 90 天内可能发生的变化
5. **速度评分**：GitHub Trending 中动量字段 = new_stars/base_stars，重视高动量信号

分析原则：
- 优先相对速度（动量），不是绝对规模
- 威胁评级: HIGH（直接替代HKUDS核心项目）/ MEDIUM（功能重叠）/ LOW（间接影响）
- 假设必须：可证伪 + 有具体时间窗口 + 有对 HKUDS 的直接含义

请以 JSON 格式输出，严格遵守以下 schema：
```json
{{
  "executive_summary": "3句话总结本期最重要发现",
  "top_speed_signals": [
    {{"name": "repo/product名", "url": "...", "momentum_pct": 数字, "reason": "为什么值得关注"}}
  ],
  "themes": [
    {{
      "label": "主题名称",
      "signal_count": 数字,
      "representative_signals": ["signal1", "signal2"],
      "hkuds_relevance": "与HKUDS哪个项目相关及关系",
      "momentum_assessment": "该主题的整体动量评估（一句话）"
    }}
  ],
  "threats": [
    {{
      "hkuds_project": "被威胁的HKUDS项目名",
      "signal_name": "威胁信号名称",
      "signal_url": "...",
      "threat_level": "HIGH|MEDIUM|LOW",
      "rationale": "为什么构成威胁（2-3句话）",
      "momentum_info": "动量信息"
    }}
  ],
  "white_spaces": [
    {{
      "area": "空白领域名称",
      "signals": ["相关信号1", "相关信号2"],
      "opportunity_for_hkuds": "HKUDS可以怎么切入（具体建议）"
    }}
  ],
  "hypotheses": [
    {{
      "confidence": "HIGH|MEDIUM-HIGH|MEDIUM|LOW",
      "prediction": "具体可证伪的预测（含时间窗口）",
      "supporting_signals": ["支撑信号1", "支撑信号2"],
      "implication_for_hkuds": "对HKUDS的具体含义和行动方向",
      "falsifier": "什么证据可以证伪这个假设"
    }}
  ]
}}
```
只输出 JSON，不要有额外的文字。"""


def build_user_message(sources: dict[str, str]) -> str:
    parts = ["以下是本期收集的信号数据，请分析：\n"]
    for name, text in sources.items():
        if text.strip():
            parts.append(f"\n## {name}\n\n{text[:MAX_CHARS_PER_SOURCE]}")
        else:
            parts.append(f"\n## {name}\n\n*（无数据）*")
    return "\n".join(parts)


def llm_analyze(sources: dict[str, str], dry_run: bool = False) -> dict:
    """调用 LLM 分析信号，返回结构化 JSON"""
    user_msg = build_user_message(sources)

    if dry_run:
        print("=== DRY RUN: SYSTEM PROMPT ===")
        print(SYSTEM_PROMPT[:500] + "...")
        print(f"\n=== USER MESSAGE ({len(user_msg)} chars) ===")
        print(user_msg[:1000] + "...")
        return {}

    print(f"  🤖 LLM 分析中 ({LLM_MODEL})...")
    client = make_client()
    resp = client.messages.create(
        model=LLM_MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = resp.content[0].text.strip()

    # 提取 JSON（有时模型会加 ```json 包裹）
    json_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw)
    if json_match:
        raw = json_match.group(1)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  LLM 输出 JSON 解析失败: {e}")
        print(f"  原始输出: {raw[:500]}")
        # 降级：返回包含原始文本的结构
        return {
            "executive_summary": raw[:500],
            "top_speed_signals": [],
            "themes": [],
            "threats": [],
            "white_spaces": [],
            "hypotheses": [],
        }


# ─────────────────────────────────────────────────────────────────────────────
# 输出格式化（与 reflexion.py 的解析器保持兼容）
# ─────────────────────────────────────────────────────────────────────────────

_CONF_EMOJI = {
    "HIGH": "🟢",
    "MEDIUM-HIGH": "🟡",
    "MEDIUM": "🟠",
    "LOW": "🔴",
}

_THREAT_EMOJI = {
    "HIGH": "🔴",
    "MEDIUM": "🟡",
    "LOW": "🟢",
}


def format_intelligence_brief(analysis: dict, counts: dict[str, int], date_str: str) -> str:
    """生成与 reflexion.py 解析格式兼容的情报简报 Markdown"""
    lines = [
        "# 情报简报 · Intelligence Brief",
        "",
        f"> 生成时间: {date_str} UTC",
        f"> 信号来源: GitHub Trending + HackerNews + ProductHunt",
        f"> 信号数量: GitHub {counts.get('GitHub Trending', 0)} | HN {counts.get('HackerNews', 0)} | PH {counts.get('ProductHunt', 0)}",
        f"> 分析引擎: LLM ({LLM_MODEL}) — 本文档由 AI 生成，**洞察和判断需人工确认**",
        "",
        "---",
        "",
    ]

    # 执行摘要
    summary = analysis.get("executive_summary", "")
    if summary:
        lines += ["## 📊 执行摘要", "", summary, ""]

    # 主题速览
    themes = analysis.get("themes", [])
    if themes:
        lines.append("")
        for t in themes:
            lines.append(
                f"- **{t.get('label', '?')}** — {t.get('signal_count', '?')} 个信号 | "
                f"相关性: {t.get('hkuds_relevance', '?')}"
            )
        lines.append("")

    # 最快速度信号
    top_signals = analysis.get("top_speed_signals", [])
    if top_signals:
        lines += [
            "**本期最高速度信号**: ",
        ]
        for s in top_signals[:3]:
            momen = s.get("momentum_pct", "?")
            momen_str = f"{momen:.1f}%" if isinstance(momen, (int, float)) else str(momen)
            lines.append(
                f"  - [{s.get('name', '?')}]({s.get('url', '#')}) — momentum {momen_str}"
            )
        lines.append("")

    # 威胁雷达
    threats = analysis.get("threats", [])
    if threats:
        lines += ["---", "", "## 🚨 威胁雷达 — HKUDS 投资组合竞争分析", ""]
        high = [t for t in threats if t.get("threat_level") == "HIGH"]
        medium = [t for t in threats if t.get("threat_level") == "MEDIUM"]
        low = [t for t in threats if t.get("threat_level") == "LOW"]

        def format_threat_block(t: dict) -> list[str]:
            emoji = _THREAT_EMOJI.get(t.get("threat_level", "LOW"), "⚪")
            proj = t.get("hkuds_project", "?")
            name = t.get("signal_name", "?")
            url = t.get("signal_url", "#")
            rationale = t.get("rationale", "")
            momentum = t.get("momentum_info", "")
            return [
                f"**{proj}**",
                f"  - [{name}]({url}) — {rationale}",
                f"    {momentum}" if momentum else "",
                "",
            ]

        if high:
            lines += [f"### 🔴 高威胁", ""]
            for t in high:
                lines += format_threat_block(t)
        if medium:
            lines += [f"### 🟡 中威胁", ""]
            for t in medium:
                lines += format_threat_block(t)
        if low:
            lines += [f"### 🟢 低威胁", ""]
            for t in low:
                lines += format_threat_block(t)

    # 涌现主题详情
    if themes:
        lines += ["---", "", "## 🌱 涌现主题分析", ""]
        for t in themes:
            label = t.get("label", "?")
            count = t.get("signal_count", "?")
            relevance = t.get("hkuds_relevance", "?")
            momentum = t.get("momentum_assessment", "")
            signals = t.get("representative_signals", [])
            lines += [
                f"### {label}",
                f"**信号数**: {count} | **HKUDS 相关性**: {relevance}",
                "",
            ]
            if momentum:
                lines.append(f"> {momentum}")
                lines.append("")
            for s in signals:
                lines.append(f"- {s}")
            lines.append("")

    # 白空间
    white_spaces = analysis.get("white_spaces", [])
    if white_spaces:
        lines += ["---", "", "## ⬜ 白空间机会", ""]
        for ws in white_spaces:
            area = ws.get("area", "?")
            signals = ws.get("signals", [])
            opp = ws.get("opportunity_for_hkuds", "")
            lines += [
                f"### {area}",
                "",
                f"**相关信号**: {', '.join(signals)}",
                "",
                f"**HKUDS 机会**: {opp}",
                "",
            ]

    # 可证伪假设 — 格式与 reflexion.py 兼容
    hypotheses = analysis.get("hypotheses", [])
    if hypotheses:
        lines += [
            "---",
            "",
            "## 🔮 可证伪假设",
            "",
            "> 以下假设基于当期信号模式生成，需人工判断可信度并跟踪验证。",
            "",
        ]
        for i, h in enumerate(hypotheses, 1):
            conf = h.get("confidence", "MEDIUM")
            conf_emoji = _CONF_EMOJI.get(conf, "🔘")
            prediction = h.get("prediction", "").strip()
            supporting = h.get("supporting_signals", [])
            implication = h.get("implication_for_hkuds", "").strip()
            falsifier = h.get("falsifier", "").strip()

            lines += [
                f"### 假设 {i} {conf_emoji} [{conf}]",
                "",
                f"**判断**: {prediction}",
                "",
                f"**支撑信号**: {', '.join(supporting)}",
                "",
                f"**对 HKUDS 的含义**: {implication}",
                "",
                f"**如何证伪**: {falsifier}",
                "",
            ]

    # 人工判断区
    lines += [
        "---",
        "",
        "## 🙋 人工判断区 (待填写)",
        "",
        "**上期假设的验证情况**:",
        "",
        "- [ ] 假设 1: ",
        "- [ ] 假设 2: ",
        "",
        "**本期新增洞察**:",
        "",
        "> (在此处填写本期最值得关注的发现和行动建议)",
        "",
    ]

    return "\n".join(lines)


def format_threat_radar(analysis: dict, date_str: str) -> str:
    threats = analysis.get("threats", [])
    lines = [
        "# 威胁雷达 · Threat Radar",
        "",
        f"> 更新: {date_str} UTC",
        "",
        "| HKUDS 项目 | 威胁信号 | 威胁等级 | 理由摘要 |",
        "|-----------|---------|---------|---------|",
    ]
    for t in sorted(threats, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x.get("threat_level", "LOW"), 3)):
        emoji = _THREAT_EMOJI.get(t.get("threat_level", "LOW"), "⚪")
        proj = t.get("hkuds_project", "?")
        name = t.get("signal_name", "?")
        url = t.get("signal_url", "#")
        level = f"{emoji} {t.get('threat_level', '?')}"
        rationale = (t.get("rationale", "")[:80] + "...") if len(t.get("rationale", "")) > 80 else t.get("rationale", "")
        lines.append(f"| {proj} | [{name}]({url}) | {level} | {rationale} |")
    lines.append("")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 主函数
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="情报分析引擎 v2 (LLM 驱动)")
    parser.add_argument("--dry-run", action="store_true", help="打印 prompt，不实际调用 LLM")
    parser.add_argument("--no-save", action="store_true", help="不写入文件，只打印摘要")
    args = parser.parse_args()

    LOGS_DIR.mkdir(exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    # 加载信号
    print("📡 加载信号数据...")
    sources, counts = load_signals()
    for name, count in counts.items():
        print(f"  {name}: {count} 条")

    total = sum(counts.values())
    if total == 0 and not args.dry_run:
        print("❌ 无信号数据，请先运行 fetch_*.py")
        sys.exit(1)

    # LLM 分析
    print(f"\n🔍 LLM 分析 {total} 条信号...")
    analysis = llm_analyze(sources, dry_run=args.dry_run)

    if args.dry_run:
        return

    if not analysis:
        print("❌ LLM 分析失败")
        sys.exit(1)

    # 统计
    threats = analysis.get("threats", [])
    themes = analysis.get("themes", [])
    hypotheses = analysis.get("hypotheses", [])
    white_spaces = analysis.get("white_spaces", [])
    high_threats = [t for t in threats if t.get("threat_level") == "HIGH"]

    print(f"  ✅ 主题: {len(themes)} | 威胁: {len(threats)} ({len(high_threats)} 高) | 假设: {len(hypotheses)} | 白空间: {len(white_spaces)}")

    # 生成报告
    brief = format_intelligence_brief(analysis, counts, date_str)
    threat_radar_md = format_threat_radar(analysis, date_str)

    if not args.no_save:
        brief_path = LOGS_DIR / "intelligence_brief.md"
        brief_path.write_text(brief, encoding="utf-8")
        print(f"\n✅ 情报简报: {brief_path}")

        radar_path = LOGS_DIR / "threat_radar.md"
        radar_path.write_text(threat_radar_md, encoding="utf-8")
        print(f"✅ 威胁雷达: {radar_path}")

        date_only = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        archive = LOGS_DIR / "digests" / f"{date_only}-intelligence.md"
        archive.parent.mkdir(exist_ok=True)
        archive.write_text(brief, encoding="utf-8")
        print(f"📁 已存档: {archive}")
    else:
        print("\n" + "=" * 60)
        print(brief[:3000])

    # 终端摘要
    print(f"\n{'─' * 60}")
    if analysis.get("executive_summary"):
        print(f"📋 {analysis['executive_summary'][:200]}")
    print(f"\n🌡  活跃主题: {len(themes)}")
    print(f"🚨  高威胁:   {len(high_threats)}")
    print(f"🔮  假设:     {len(hypotheses)}")
    print(f"⬜  白空间:   {len(white_spaces)}")
    print(f"{'─' * 60}")

    if hypotheses:
        print("\n最值得关注的假设：")
        for h in hypotheses[:2]:
            print(f"  • [{h.get('confidence','?')}] {h.get('prediction','')[:80]}...")
            print(f"    → {h.get('implication_for_hkuds','')[:80]}...")


if __name__ == "__main__":
    main()
