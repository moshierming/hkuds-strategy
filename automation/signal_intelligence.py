#!/usr/bin/env python3
"""
signal_intelligence.py
======================
情报分析引擎 — 从原始信号到结构化洞察。

这不是数据收集器，而是分析器。
核心能力：
  1. 主题提取 — 从多源信号中聚类出正在涌现的主题
  2. 速度评分 — 用新增量/基准量衡量动量，不是绝对值
  3. 威胁映射 — 与 HKUDS 投资组合做竞争定位对比
  4. 白空间检测 — 市场有信号但 HKUDS 没覆盖的区域
  5. 假设生成 — 基于模式产出可证伪的预测

用法:
    python automation/signal_intelligence.py
    python automation/signal_intelligence.py --brief  # 只输出简报摘要

输出:
    logs/intelligence_brief.md   — 当期情报简报
    logs/threat_radar.md         — 竞争威胁雷达
    logs/opportunity_signals.md  — 机会信号(更新 logs/opportunities.md)
"""

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / "logs"

# ─────────────────────────────────────────────────────────────────────────────
# HKUDS 投资组合映射 — 用于竞争定位
# ─────────────────────────────────────────────────────────────────────────────

HKUDS_PORTFOLIO = {
    "LightRAG": {
        "category": "knowledge_graph_rag",
        "keywords": [
            "rag", "graph rag", "graphrag", "knowledge graph", "retrieval", "lightrag",
            # 扩展：context db / agent memory 类都与 LightRAG 直接竞争
            "context database", "knowledge engine", "agent memory", "openrag",
            "cognee", "openviking", "hindsight", "memory that learns",
        ],
        "stars": 38000,
        "threat_sensitivity": "HIGH",  # 竞争激烈
        "description": "异构图 RAG 框架",
    },
    "MiniRAG": {
        "category": "edge_rag",
        "keywords": [
            "edge rag", "local rag", "slm rag", "offline rag", "minirag", "on-device",
            "1-bit", "bitnet", "unsloth", "local llm", "lightweight rag",
        ],
        "stars": 1800,
        "threat_sensitivity": "MEDIUM",
        "description": "边缘/离线 RAG (SLM 优化)",
    },
    "AutoAgent": {
        "category": "zero_code_agent",
        "keywords": [
            "autoagent", "no-code agent", "zero-code", "natural language agent",
            "agent framework", "agent harness", "skills framework", "superpowers",
            "deepagents", "agency agents", "open-swe", "agentic",
        ],
        "stars": 5000,
        "threat_sensitivity": "HIGH",
        "description": "Zero-Code LLM Agent 框架",
    },
    "nanobot": {
        "category": "im_agent",
        "keywords": ["nanobot", "im bot", "telegram bot", "discord bot", "slack bot", "wechat bot"],
        "stars": 35000,
        "threat_sensitivity": "LOW",
        "description": "多平台 IM Agent SDK",
    },
    "VideoRAG": {
        "category": "video_rag",
        "keywords": ["video rag", "video understanding", "long video", "multimodal rag"],
        "stars": 3000,
        "threat_sensitivity": "MEDIUM",
        "description": "超长视频 RAG",
    },
    "GraphGPT": {
        "category": "graph_llm",
        "keywords": ["graph gpt", "graph llm", "graph language model", "gnn llm"],
        "stars": 8000,
        "threat_sensitivity": "LOW",
        "description": "图神经网络 + LLM",
    },
    "SepLLM": {
        "category": "efficient_llm",
        "keywords": ["efficient llm", "token compression", "kv cache", "long context", "sparse attention"],
        "stars": 2000,
        "threat_sensitivity": "MEDIUM",
        "description": "LLM Token 效率压缩",
    },
    "RAG-Anything": {
        "category": "multimodal_rag",
        "keywords": ["multimodal rag", "rag anything", "file rag", "document rag", "pdf rag"],
        "stars": 4000,
        "threat_sensitivity": "MEDIUM",
        "description": "多模态 RAG 框架",
    },
}

# 主题聚类定义 — 用于识别涌现趋势
THEME_CLUSTERS = {
    "claude_code_ecosystem": {
        "label": "Claude Code 生态工具",
        "keywords": ["claude code", "claude", "agent harness", "skills framework", "superpowers"],
        "hkuds_relevance": "AutoAgent — 直接竞争",
    },
    "agent_memory_knowledge": {
        "label": "Agent 记忆 & 知识引擎",
        "keywords": ["agent memory", "knowledge engine", "context database", "cognee", "openrag",
                     "hindsight", "openviking", "memory", "knowledge base"],
        "hkuds_relevance": "LightRAG/MiniRAG — 直接威胁",
    },
    "edge_local_llm": {
        "label": "边缘/本地 LLM 推理",
        "keywords": ["local llm", "1-bit", "bitnet", "on-device", "edge", "unsloth", "quantization"],
        "hkuds_relevance": "MiniRAG — 有利生态",
    },
    "trading_finance_agent": {
        "label": "金融 & 交易 Agent",
        "keywords": ["trading", "stock", "financial", "crypto", "investment", "quant"],
        "hkuds_relevance": "空白 — HKUDS 无覆盖",
    },
    "multimodal_agent": {
        "label": "多模态 Agent & 视频理解",
        "keywords": ["multimodal", "vision", "video", "image understanding", "visual"],
        "hkuds_relevance": "VideoRAG — 可扩展",
    },
    "browser_web_agent": {
        "label": "浏览器 & Web 自动化 Agent",
        "keywords": ["browser", "web agent", "headless", "automation", "selenium", "playwright"],
        "hkuds_relevance": "空白 — CLI-Anything 可扩展",
    },
    "code_agent_dev_tool": {
        "label": "代码生成 & 开发 Agent",
        "keywords": ["code generation", "coding agent", "swe", "software engineer", "copilot",
                     "dev tool", "fastcode", "deepcode"],
        "hkuds_relevance": "FastCode/DeepCode — 可扩展",
    },
    "mcp_protocol": {
        "label": "MCP / Agent 协议标准化",
        "keywords": ["mcp", "model context protocol", "agent protocol", "a2a", "openai agents sdk"],
        "hkuds_relevance": "AnyTool — 部分相关",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 信号解析器
# ─────────────────────────────────────────────────────────────────────────────

def parse_github_trending(path: Path) -> list[dict]:
    """从 github_trending.md 解析仓库信号"""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    repos = []
    # 解析表格行: | [name](url) | desc | stars | new | lang |
    for line in text.split("\n"):
        m = re.match(r'\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+)\|\s*([0-9,]+)\s*\|\s*([0-9,]+)\s*\|\s*([^|]*)\|', line)
        if not m:
            continue
        name, url, desc, stars_raw, new_raw, lang = m.groups()
        try:
            stars = int(stars_raw.replace(",", ""))
            new_stars = int(new_raw.replace(",", ""))
        except ValueError:
            continue
        repos.append({
            "name": name.strip(),
            "url": url.strip(),
            "desc": desc.strip()[:120],
            "stars": stars,
            "new_stars": new_stars,
            "lang": lang.strip(),
            "source": "github_trending",
            "momentum": new_stars / max(stars - new_stars, 1),  # velocity ratio
        })
    return repos


def parse_hackernews(path: Path) -> list[dict]:
    """从 hackernews_signals.md 解析高分讨论"""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    items = []
    # 解析 "| [title](url) | score | comments | type | date |" 格式
    for line in text.split("\n"):
        m = re.match(r'\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([^|]*)\|', line)
        if not m:
            continue
        title, url, score, comments, type_ = m.groups()
        items.append({
            "title": title.strip(),
            "url": url.strip(),
            "score": int(score),
            "comments": int(comments),
            "type": type_.strip(),
            "source": "hackernews",
        })
    return items


def parse_producthunt(path: Path) -> list[dict]:
    """从 producthunt_trends.md 解析产品"""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    items = []
    for line in text.split("\n"):
        m = re.match(r'\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+)\|\s*(\d+)[^|]*\|', line)
        if not m:
            continue
        name, url, tagline, votes = m.groups()
        items.append({
            "name": name.strip(),
            "url": url.strip(),
            "tagline": tagline.strip()[:100],
            "votes": int(votes),
            "source": "producthunt",
        })
    return items


# ─────────────────────────────────────────────────────────────────────────────
# 信号分析引擎
# ─────────────────────────────────────────────────────────────────────────────

def extract_signal_text(signal: dict) -> str:
    """从信号 dict 提取可用于关键词匹配的文本"""
    parts = []
    for key in ["name", "title", "desc", "tagline", "description"]:
        if key in signal:
            parts.append(signal[key].lower())
    return " ".join(parts)


def classify_into_themes(signals: list[dict]) -> dict[str, list[dict]]:
    """将信号归类到主题"""
    theme_signals = defaultdict(list)
    for sig in signals:
        text = extract_signal_text(sig)
        matched_themes = set()
        for theme_id, theme in THEME_CLUSTERS.items():
            for kw in theme["keywords"]:
                if kw.lower() in text:
                    matched_themes.add(theme_id)
                    break
        for t in matched_themes:
            # 避免同一信号在同一主题重复
            existing_names = [s.get("name", s.get("title", "")) for s in theme_signals[t]]
            sig_name = sig.get("name", sig.get("title", ""))
            if sig_name not in existing_names:
                theme_signals[t].append(sig)

    return dict(theme_signals)


def detect_portfolio_threats(signals: list[dict]) -> dict[str, list[dict]]:
    """检测对 HKUDS 投资组合的潜在威胁"""
    threats = defaultdict(list)
    for proj_name, proj in HKUDS_PORTFOLIO.items():
        for sig in signals:
            text = extract_signal_text(sig)
            for kw in proj["keywords"]:
                if kw.lower() in text:
                    sig_name = sig.get("name", sig.get("title", ""))
                    existing = [s.get("name", s.get("title", "")) for s in threats[proj_name]]
                    if sig_name not in existing:
                        threats[proj_name].append(sig)
                    break
    return dict(threats)


def score_signal(sig: dict) -> float:
    """综合评分：速度 (velocity) + 规模 (scale) + 社区热度"""
    score = 0.0
    # GitHub trending signal
    if sig.get("source") == "github_trending":
        momentum = sig.get("momentum", 0)  # new_stars / base_stars
        new_stars = sig.get("new_stars", 0)
        # 速度得分 (0-50): momentum 越高越好
        score += min(momentum * 100, 50)
        # 规模得分 (0-30): 用 log 避免头部效应
        score += min(math.log1p(new_stars) * 3, 30)
        # 总 stars 背书 (0-20)
        total = sig.get("stars", 0)
        score += min(math.log1p(total) * 1.5, 20)
    elif sig.get("source") == "hackernews":
        s = sig.get("score", 0)
        c = sig.get("comments", 0)
        score = min(s / 5 + c / 3, 100)
    elif sig.get("source") == "producthunt":
        score = min(sig.get("votes", 0) / 10, 100)
    return round(score, 1)


def find_cross_source_signals(all_signals: list[dict], threshold: int = 2) -> list[dict]:
    """找出在多个信号源都有出现的主题（交叉验证信号）"""
    # 用描述文本的词集合做近似匹配
    from collections import Counter
    word_sources = defaultdict(set)
    word_to_sigs = defaultdict(list)

    # 提取有价值的关键词（长度 > 4，非停用词）
    stopwords = {"with", "that", "this", "from", "have", "were", "they", "your",
                 "code", "open", "using", "build", "built", "make", "like", "just",
                 "based", "tool", "tools", "model", "models", "data", "source", "more"}

    for sig in all_signals:
        text = extract_signal_text(sig)
        words = set(w for w in re.findall(r'\b[a-z]{4,}\b', text) if w not in stopwords)
        for w in words:
            word_sources[w].add(sig["source"])
            word_to_sigs[w].append(sig)

    # 找在 >= threshold 个来源中都出现的关键词
    cross_words = {w for w, srcs in word_sources.items() if len(srcs) >= threshold}

    # 收集这些词指向的信号
    cross_sigs = []
    seen = set()
    for w in cross_words:
        for sig in word_to_sigs[w]:
            uid = sig.get("name", sig.get("title", ""))
            if uid and uid not in seen:
                seen.add(uid)
                sig_copy = dict(sig)
                sig_copy["cross_source_word"] = w
                cross_sigs.append(sig_copy)

    return sorted(cross_sigs, key=lambda x: score_signal(x), reverse=True)[:10]


def detect_whitespace(theme_signals: dict) -> list[str]:
    """找出有市场信号但 HKUDS 投资组合无覆盖的空白区"""
    hkuds_categories = {p["category"] for p in HKUDS_PORTFOLIO.values()}
    whitespaces = []
    for theme_id, theme in THEME_CLUSTERS.items():
        if theme_id not in theme_signals:
            continue
        if len(theme_signals[theme_id]) < 2:
            continue
        # 如果相关性标注为"空白"就加入
        if "空白" in theme.get("hkuds_relevance", ""):
            whitespaces.append(theme_id)
    return whitespaces


def generate_hypotheses(theme_signals: dict, threats: dict) -> list[dict]:
    """基于信号模式生成可证伪的假设"""
    hypotheses = []

    # 假设生成规则
    if "claude_code_ecosystem" in theme_signals and len(theme_signals["claude_code_ecosystem"]) >= 2:
        sigs = theme_signals["claude_code_ecosystem"]
        hypotheses.append({
            "hypothesis": "Claude Code 工具生态将在 90 天内超越 Cursor 成为开发者首选 Agent 宿主",
            "confidence": "MEDIUM-HIGH",
            "evidence": [s.get("name", s.get("title","")) for s in sigs[:3]],
            "implication": "AutoAgent 应优先支持 Claude Code 作为 backend，而非通用 CLI",
            "falsifier": "如果 Claude Code 月活增长停滞 < 10%",
        })

    if "agent_memory_knowledge" in theme_signals and len(theme_signals["agent_memory_knowledge"]) >= 2:
        sigs = theme_signals["agent_memory_knowledge"]
        hypotheses.append({
            "hypothesis": "RAG/知识引擎赛道正在从「框架」转向「基础设施组件」，Cognee/OpenViking 代表新一代竞争者",
            "confidence": "HIGH",
            "evidence": [s.get("name", s.get("title","")) for s in sigs[:3]],
            "implication": "LightRAG 必须在 6 个月内推出托管 API 或 embeddable SDK，否则将被更轻量的方案替代",
            "falsifier": "如果 LightRAG stars 继续以 1K+/月增长且企业集成案例增加",
        })

    if "trading_finance_agent" in theme_signals:
        hypotheses.append({
            "hypothesis": "金融 Agent 是当前开发者愿意真正付钱的 AI 工具之一，但 HKUDS 完全没有覆盖",
            "confidence": "MEDIUM",
            "evidence": [s.get("name", "") for s in theme_signals["trading_finance_agent"][:3]],
            "implication": "考虑用 AutoAgent + RAG-Anything 快速打包一个金融研报 Agent Demo，可能是快速获客的捷径",
            "falsifier": "如果 TradingAgents 和 daily_stock_analysis 的 stars 停止增长",
        })

    if "edge_local_llm" in theme_signals:
        hypotheses.append({
            "hypothesis": "Unsloth + BitNet + MiniRAG 三者共振：2026 年底前，本地 SLM 推理将成为 enterprise 标准配置",
            "confidence": "MEDIUM",
            "evidence": [s.get("name", "") for s in theme_signals["edge_local_llm"][:3]],
            "implication": "MiniRAG 应加快与 Unsloth（最流行的本地 training/inference UI）的集成，借势获取分发",
            "falsifier": "如果大模型 API 价格继续下降 > 50% 使本地部署失去经济意义",
        })

    if "mcp_protocol" in theme_signals:
        hypotheses.append({
            "hypothesis": "MCP 正在成为 Agent 工具协议的事实标准，所有不支持 MCP 的框架将在 12 个月内失去开发者关注",
            "confidence": "HIGH",
            "evidence": [s.get("name", "") for s in theme_signals["mcp_protocol"][:3]],
            "implication": "AutoAgent / AnyTool / nanobot 都应在 30 天内发布 MCP 支持声明",
            "falsifier": "如果 Google A2A 协议获得超过 MCP 的开发者采纳",
        })

    return hypotheses


# ─────────────────────────────────────────────────────────────────────────────
# 报告生成
# ─────────────────────────────────────────────────────────────────────────────

def format_intelligence_brief(
    all_signals: list[dict],
    theme_signals: dict,
    threats: dict,
    hypotheses: list[dict],
    whitespaces: list[str],
    cross_source: list[dict],
    date_str: str,
) -> str:
    lines = []
    lines.append(f"# 情报简报 · Intelligence Brief")
    lines.append(f"")
    lines.append(f"> 生成时间: {date_str} UTC")
    lines.append(f"> 信号来源: GitHub Trending + HackerNews + ProductHunt + arXiv")
    lines.append(f"> 本文档由引擎生成，**洞察和判断需人工确认**")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # 执行摘要
    lines.append(f"## 📊 执行摘要")
    lines.append(f"")
    top_themes = sorted(theme_signals.items(), key=lambda x: len(x[1]), reverse=True)[:3]
    for theme_id, sigs in top_themes:
        theme = THEME_CLUSTERS.get(theme_id, {})
        lines.append(f"- **{theme.get('label', theme_id)}** — {len(sigs)} 个信号 | 相关性: {theme.get('hkuds_relevance', '待评估')}")
    lines.append(f"")
    lines.append(f"**本期最高速度信号**: ", )
    if all_signals:
        top_speed = sorted([s for s in all_signals if s.get("source") == "github_trending"],
                          key=lambda x: x.get("momentum", 0), reverse=True)[:3]
        for s in top_speed:
            momentum_pct = round(s.get("momentum", 0) * 100, 1)
            lines.append(f"  - [{s['name']}]({s.get('url','')}) — +{s.get('new_stars',0):,} stars, "
                         f"momentum {momentum_pct}%/基准")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # 🚨 威胁雷达
    lines.append(f"## 🚨 威胁雷达 — HKUDS 投资组合竞争分析")
    lines.append(f"")
    high_threats = {k: v for k, v in threats.items() if HKUDS_PORTFOLIO.get(k, {}).get("threat_sensitivity") == "HIGH" and v}
    medium_threats = {k: v for k, v in threats.items() if HKUDS_PORTFOLIO.get(k, {}).get("threat_sensitivity") == "MEDIUM" and v}

    if high_threats:
        lines.append(f"### 🔴 高威胁")
        for proj, sigs in high_threats.items():
            proj_info = HKUDS_PORTFOLIO[proj]
            lines.append(f"")
            lines.append(f"**{proj}** ({proj_info['description']}, ⭐{proj_info['stars']:,})")
            for sig in sigs[:4]:
                sig_name = sig.get("name", sig.get("title",""))
                sig_url = sig.get("url","")
                stars = sig.get("stars", 0)
                new_s = sig.get("new_stars", 0)
                desc = sig.get("desc", sig.get("tagline", ""))[:80]
                if stars:
                    lines.append(f"  - [{sig_name}]({sig_url}) ⭐{stars:,} (+{new_s:,}/week) — {desc}")
                else:
                    lines.append(f"  - [{sig_name}]({sig_url}) — {desc}")
        lines.append(f"")

    if medium_threats:
        lines.append(f"### 🟡 中威胁")
        for proj, sigs in medium_threats.items():
            proj_info = HKUDS_PORTFOLIO[proj]
            lines.append(f"")
            lines.append(f"**{proj}** ({proj_info['description']})")
            for sig in sigs[:3]:
                sig_name = sig.get("name", sig.get("title",""))
                sig_url = sig.get("url","")
                stars = sig.get("stars", 0)
                new_s = sig.get("new_stars", 0)
                desc = (sig.get("desc", sig.get("tagline","")) or "")[:80]
                if stars:
                    lines.append(f"  - [{sig_name}]({sig_url}) ⭐{stars:,} (+{new_s:,}/week) — {desc}")
                else:
                    lines.append(f"  - [{sig_name}]({sig_url}) — {desc}")
        lines.append(f"")

    if not high_threats and not medium_threats:
        lines.append(f"*本期未检测到直接威胁信号。*")
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"")

    # 🌱 涌现主题
    lines.append(f"## 🌱 涌现主题分析")
    lines.append(f"")
    for theme_id, sigs in sorted(theme_signals.items(), key=lambda x: len(x[1]), reverse=True):
        if not sigs:
            continue
        theme = THEME_CLUSTERS.get(theme_id, {})
        top_momentum = sorted([s for s in sigs if "momentum" in s],
                               key=lambda x: x.get("momentum", 0), reverse=True)
        lines.append(f"### {theme.get('label', theme_id)}")
        lines.append(f"**信号数**: {len(sigs)} | **HKUDS 相关性**: {theme.get('hkuds_relevance','')}")
        lines.append(f"")
        for sig in (top_momentum or sigs)[:4]:
            name = sig.get("name", sig.get("title",""))
            url = sig.get("url","")
            stars = sig.get("stars",0)
            new_s = sig.get("new_stars",0)
            momentum = sig.get("momentum",0)
            desc = (sig.get("desc", sig.get("tagline","")) or "")[:80]
            if stars:
                lines.append(f"- [{name}]({url}) ⭐{stars:,} (+{new_s:,}) {f'[momentum {momentum*100:.1f}%]' if momentum else ''}")
                if desc:
                    lines.append(f"  > {desc}")
            else:
                lines.append(f"- [{name}]({url}) — {desc}")
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"")

    # ⬜ 白空间
    if whitespaces:
        lines.append(f"## ⬜ 白空间机会")
        lines.append(f"")
        lines.append(f"以下领域有明确市场信号，但 HKUDS 投资组合无覆盖：")
        lines.append(f"")
        for ws in whitespaces:
            theme = THEME_CLUSTERS.get(ws, {})
            sigs = theme_signals.get(ws, [])
            lines.append(f"- **{theme.get('label', ws)}** — {len(sigs)} 个信号")
            for sig in sigs[:2]:
                name = sig.get("name", sig.get("title",""))
                url = sig.get("url","")
                lines.append(f"  - [{name}]({url})")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    # 🔮 假设
    lines.append(f"## 🔮 可证伪假设")
    lines.append(f"")
    lines.append(f"> 以下假设基于当期信号模式生成，需人工判断可信度并跟踪验证。")
    lines.append(f"")
    for i, h in enumerate(hypotheses, 1):
        confidence_emoji = {"HIGH": "🟢", "MEDIUM-HIGH": "🟡", "MEDIUM": "🟠", "LOW": "🔴"}.get(h["confidence"], "⚪")
        lines.append(f"### 假设 {i} {confidence_emoji} [{h['confidence']}]")
        lines.append(f"")
        lines.append(f"**判断**: {h['hypothesis']}")
        lines.append(f"")
        lines.append(f"**支撑信号**: {', '.join(h['evidence'])}")
        lines.append(f"")
        lines.append(f"**对 HKUDS 的含义**: {h['implication']}")
        lines.append(f"")
        lines.append(f"**如何证伪**: {h['falsifier']}")
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"")

    # 📈 速度表格
    lines.append(f"## 📈 本期最快速度信号 (GitHub Trending)")
    lines.append(f"")
    lines.append(f"| 项目 | 总 Stars | 新增/期 | 速度 % | 描述 |")
    lines.append(f"|------|---------|---------|-------|------|")
    trending_sigs = [s for s in all_signals if s.get("source") == "github_trending"]
    for sig in sorted(trending_sigs, key=lambda x: x.get("momentum", 0), reverse=True)[:12]:
        pct = f"{sig.get('momentum',0)*100:.1f}%"
        name = sig.get("name","")
        url = sig.get("url","")
        stars = sig.get("stars",0)
        new_s = sig.get("new_stars",0)
        desc = (sig.get("desc","") or "")[:50]
        lines.append(f"| [{name}]({url}) | ⭐{stars:,} | +{new_s:,} | {pct} | {desc} |")
    lines.append(f"")

    # 🙋 反思区
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 🙋 人工判断区 (待填写)")
    lines.append(f"")
    lines.append(f"**本期最重要的 1 个信号是**:")
    lines.append(f"> ")
    lines.append(f"")
    lines.append(f"**它改变了我的哪个判断**:")
    lines.append(f"> ")
    lines.append(f"")
    lines.append(f"**上期假设的验证情况**:")
    lines.append(f"> ")
    lines.append(f"")
    lines.append(f"**基于本期情报，下 2 周最值得做的 1 件事**:")
    lines.append(f"> ")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"*由 `automation/signal_intelligence.py` 生成 · {date_str}*")

    return "\n".join(lines)


def format_threat_radar(threats: dict, date_str: str) -> str:
    """生成精简的威胁雷达 — 按威胁等级排列"""
    lines = [f"# 威胁雷达 · Threat Radar", f"", f"> 更新时间: {date_str}", f""]

    # 排序：HIGH → MEDIUM → LOW
    order = ["HIGH", "MEDIUM", "LOW"]
    grouped = defaultdict(list)
    for proj, sigs in threats.items():
        if not sigs:
            continue
        sensitivity = HKUDS_PORTFOLIO.get(proj, {}).get("threat_sensitivity", "LOW")
        grouped[sensitivity].append((proj, sigs))

    for level in order:
        if level not in grouped:
            continue
        emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}[level]
        lines.append(f"## {emoji} {level} 威胁")
        lines.append(f"")
        for proj, sigs in grouped[level]:
            proj_info = HKUDS_PORTFOLIO.get(proj, {})
            lines.append(f"### {proj} ({proj_info.get('description','')})")
            for sig in sigs[:5]:
                name = sig.get("name", sig.get("title",""))
                url = sig.get("url","")
                stars = sig.get("stars",0)
                new_s = sig.get("new_stars",0)
                momentum = sig.get("momentum", 0)
                desc = (sig.get("desc", sig.get("tagline","")) or "")[:80]
                momentum_str = f" [momentum {momentum*100:.1f}%]" if momentum > 0.01 else ""
                stars_str = f" ⭐{stars:,} (+{new_s:,}){momentum_str}" if stars else ""
                lines.append(f"- [{name}]({url}){stars_str}")
                if desc:
                    lines.append(f"  > {desc}")
            lines.append(f"")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="情报分析引擎")
    parser.add_argument("--brief", action="store_true", help="只输出摘要到 stdout")
    parser.add_argument("--no-save", action="store_true", help="不写入文件，只打印")
    args = parser.parse_args()

    LOGS_DIR.mkdir(exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    print("📡 加载信号数据...")
    all_signals = []

    trending = parse_github_trending(LOGS_DIR / "github_trending.md")
    all_signals.extend(trending)
    print(f"  GitHub Trending: {len(trending)} 信号")

    hn = parse_hackernews(LOGS_DIR / "hackernews_signals.md")
    all_signals.extend(hn)
    print(f"  HackerNews:      {len(hn)} 信号")

    ph = parse_producthunt(LOGS_DIR / "producthunt_trends.md")
    all_signals.extend(ph)
    print(f"  ProductHunt:     {len(ph)} 信号")

    if not all_signals:
        print("❌ 无信号数据，请先运行 fetch_*.py 脚本")
        sys.exit(1)

    print(f"\n🔍 分析 {len(all_signals)} 个信号...")

    theme_signals = classify_into_themes(all_signals)
    print(f"  主题聚类: {len(theme_signals)} 个活跃主题")

    threats = detect_portfolio_threats(all_signals)
    threat_count = sum(len(v) for v in threats.values())
    print(f"  威胁信号: {threat_count} 个 (覆盖 {len(threats)} 个 HKUDS 项目)")

    hypotheses = generate_hypotheses(theme_signals, threats)
    print(f"  假设生成: {len(hypotheses)} 个可证伪假设")

    whitespaces = detect_whitespace(theme_signals)
    print(f"  白空间: {len(whitespaces)} 个市场空白")

    cross_source = find_cross_source_signals(all_signals)
    print(f"  交叉验证: {len(cross_source)} 个跨源信号")

    # 生成报告
    brief = format_intelligence_brief(
        all_signals, theme_signals, threats, hypotheses, whitespaces, cross_source, date_str
    )
    threat_radar = format_threat_radar(threats, date_str)

    if args.brief:
        # 只打印摘要
        lines = brief.split("\n")
        summary_lines = []
        for line in lines:
            if line.startswith("## 📊"):
                for l in lines[lines.index(line):lines.index(line)+12]:
                    summary_lines.append(l)
                break
        print("\n".join(summary_lines))
        return

    if not args.no_save:
        brief_path = LOGS_DIR / "intelligence_brief.md"
        brief_path.write_text(brief, encoding="utf-8")
        print(f"\n✅ 情报简报: {brief_path}")

        radar_path = LOGS_DIR / "threat_radar.md"
        radar_path.write_text(threat_radar, encoding="utf-8")
        print(f"✅ 威胁雷达: {radar_path}")

        # 归档
        date_only = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        archive = LOGS_DIR / "digests" / f"{date_only}-intelligence.md"
        archive.parent.mkdir(exist_ok=True)
        archive.write_text(brief, encoding="utf-8")
        print(f"📁 已存档: {archive}")
    else:
        print("\n" + "="*60)
        print(brief[:3000])
        print("...(截断)")

    # 摘要打印
    print(f"\n{'─'*60}")
    print(f"🌡  活跃主题数:  {len(theme_signals)}")
    print(f"🚨  威胁项目数:  {len([k for k,v in threats.items() if v])}")
    print(f"🔮  新生假设数:  {len(hypotheses)}")
    print(f"⬜  白空间数:    {len(whitespaces)}")
    print(f"{'─'*60}")

    if hypotheses:
        print(f"\n最值得关注的假设：")
        for h in hypotheses[:2]:
            print(f"  • {h['hypothesis'][:80]}...")
            print(f"    → {h['implication'][:80]}...")


if __name__ == "__main__":
    main()
