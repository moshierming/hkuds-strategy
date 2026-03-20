# AI 情报研究引擎 · Intelligence Research Engine

> 以 HKUDS 为基础锚点，持续扫描 AI 生态的多个信号源，  
> 形成自己的洞察，不断更新，不断迭代，不断反思。

```
信号采集 → 主题涌现 → 洞察形成 → 行动执行 → 结果验证 → 洞察修正 → ...
```

---

## 核心理念

**HKUDS 是一个很好的 baseline，但绝不是终点。**

这套系统会同时监听：
- HKUDS 82 个研究项目的最新动态（GitHub + arXiv）
- HackerNews 的 Show HN、技术讨论、Ask HN
- ProductHunt AI/开发工具类目的新产品发布
- GitHub Trending 全球 AI/ML 热门仓库

每周自动聚合，通过跨渠道主题检测发现真正涌现的信号——而不是某个单一来源的噪音。

---

## 三层架构

| 层 | 目录 | 职责 |
|---|------|------|
| **自动化层** | `automation/` | 机器 24/7 采集，人不用手动盯着 |
| **方法论层** | `methodology/` | 系统框架确保分析有章法 |
| **产出层** | `analysis/` `gtm/` `landing/` | 每个循环产出可执行物 |

---

## 目录结构

```
hkuds-strategy/
├── methodology/
│   ├── FRAMEWORK.md        # 五维度分析法 + 永不封闭信号网络
│   └── SIGNAL_SOURCES.md  # ★ 所有监控渠道 + 信号质量评估
│
├── automation/
│   ├── fetch_github_stats.py    # HKUDS 仓库统计 (84 repos)
│   ├── arxiv_monitor.py         # HKUDS 相关 arXiv 新论文
│   ├── fetch_hackernews.py      # ★ HackerNews 信号
│   ├── fetch_github_trending.py # ★ GitHub Trending AI 仓库
│   ├── fetch_producthunt.py     # ★ ProductHunt 新产品
│   ├── aggregate_signals.py     # ★ 跨渠道聚合 + 主题检测
│   ├── generate_digest.py       # HKUDS 聚焦周报
│   └── README.md
│
├── templates/
│   └── PROJECT_ANALYSIS.md    # 30 分钟五维度评估模板
│
├── logs/                       # 自动生成 + 手动维护
│   ├── weekly_signal_digest.md # ★ 跨渠道综合周报
│   ├── insights_log.md         # ★ 洞察演化日志 (手动维护)
│   ├── hackernews_signals.md   # HN 信号
│   ├── github_trending.md      # GitHub Trending
│   ├── producthunt_trends.md   # ProductHunt
│   ├── arxiv_papers.md         # 最新论文
│   ├── github_stats.json       # HKUDS 统计
│   ├── opportunities.md        # 机会跟踪日志
│   └── digests/                # 历史完整周报
│
├── analysis/
│   ├── INSIGHTS.md             # 8 卷 42+ 条洞察（3400+ 行）
│   ├── PROJECT_MAP.md          # 80+ 项目商业价值分级排名
│   └── STRATEGY_BRIEF.md
│
├── gtm/
│   └── LIGHTRAG_GTM.md        # LightRAG GTM + 3 封冷邮件模板
│
├── landing/
│   └── index.html             # lightrag.io Landing Page
│
└── .github/workflows/
    ├── weekly-update.yml      # 每周一自动运行全部脚本
    └── pages.yml              # Landing Page 自动部署
```

---

## 快速导航

### 📡 看本周信号 → [logs/weekly_signal_digest.md](logs/weekly_signal_digest.md)

跨 HN + ProductHunt + GitHub Trending + arXiv 的聚合周报，每周一自动更新。

### 💡 看演化中的洞察 → [logs/insights_log.md](logs/insights_log.md)

带时间戳的洞察日志：每条洞察都有来源、判断、反驳证据、更新历史。

### 🗺️ 看项目排名 → [analysis/PROJECT_MAP.md](analysis/PROJECT_MAP.md)

80+ 项目按变现速度 × 商业规模分 5 级：

| 级别 | 代表项目 | 变现窗口 |
|------|---------|---------|
| **S 级 ★★★★★** | LightRAG、AutoAgent、MiniRAG、nanobot | 0-12 个月 |
| **A 级 ★★★★☆** | RAG-Anything、VideoRAG、DeepCode | 需加速商业化 |
| **B 级 ★★★☆☆** | ClawTeam、图 AI 套件、UrbanGPT | 12-24 个月 |
| **C-E 级 ★★☆☆☆** | 30+ 推荐系统、时空计算 | 学术积累期 |

### 🚀 看 GTM 方案 → [gtm/LIGHTRAG_GTM.md](gtm/LIGHTRAG_GTM.md)

- 目标客户：法律事务所、金融研究、医疗 R&D
- 定价：Free → $99/月 → $499/月 → Enterprise
- 12 个月目标：ARR $1M，付费用户 500+
- 附 3 封天使投资人 Cold Email 模板

---

## 核心结论：TOP 5 最值得押注的项目

```
#1  LightRAG      ── $1B+ 市场，图增强 RAG，企业知识库基础设施层
#2  AutoAgent     ── $200-500M，自然语言创建 Agent，Zero-code Agent 工厂
#3  MiniRAG       ── $100-300M，边缘/隐私场景，SLM 友好，本地可运行
#4  nanobot       ── $50-150M，30 天最短变现路径，9 大 IM 渠道覆盖
#5  OpenPhone     ── $100M+，手机 Agent 中间件空白，12 个月先发窗口
```

---

## 每周工作流

```bash
# 1. 安装依赖（首次）
pip install requests feedparser beautifulsoup4

# 2. 拉取最新仓库
git pull

# 3. 运行全渠道采集（或等 GitHub Actions 自动运行）
export GITHUB_TOKEN=你的token  # 可选
python automation/fetch_github_stats.py
python automation/arxiv_monitor.py
python automation/fetch_hackernews.py --days 7
python automation/fetch_github_trending.py
python automation/fetch_producthunt.py
python automation/aggregate_signals.py
python automation/generate_digest.py

# 4. 阅读聚合周报
cat logs/weekly_signal_digest.md

# 5. 更新洞察日志（关键一步：机器给不了，只有人能做）
vim logs/insights_log.md

# 6. 执行至少一个具体行动
#    （PR / 博客 / 邮件 / 新工具 / 新分析）
```

---

## 关联资源

| 资源 | 链接 |
|------|------|
| HKUDS GitHub | https://github.com/HKUDS |
| LightRAG Landing Page | https://moshierming.github.io/lightrag-landing/ |
| 信号来源总览 | [methodology/SIGNAL_SOURCES.md](methodology/SIGNAL_SOURCES.md) |
| 方法论框架 | [methodology/FRAMEWORK.md](methodology/FRAMEWORK.md) |

---

## License

分析文档采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)，代码采用 MIT 协议。
