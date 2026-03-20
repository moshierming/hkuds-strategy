# HKUDS 研究引擎 · Research Engine

> 不是一个静态文档库，而是一个**持续运转的研究+执行系统**。
> 方法论驱动，多角度探索，自动化生产有价值的产出。

---

## 系统理念

```
观察 → 理解 → 行动 → 验证 → 观察 → ...（循环）
```

**三层架构**：
- **自动化层**（`automation/`）：机器持续收集信号，人不用手动盯着
- **方法论层**（`methodology/`）：系统框架确保每次分析不遗漏角度
- **产出层**（`analysis/` `gtm/` `landing/`）：每次循环产出可执行物

**适用于**：任何想对 AI/ML 开源项目做持续研究、发现商业机会、建立行业影响力的人。

---

## 目录结构

```
hkuds-strategy/
├── methodology/            # ★ 研究方法论 (新增)
│   └── FRAMEWORK.md       # 五维度分析法 + 研究节奏 + 行动标准
│
├── automation/             # ★ 自动化脚本 (新增)
│   ├── fetch_github_stats.py  # 每周抓取 HKUDS 所有仓库统计
│   ├── arxiv_monitor.py       # 监控 HKUDS 相关 arXiv 新论文
│   ├── generate_digest.py     # 生成每周研究摘要
│   └── README.md              # 使用说明
│
├── templates/              # ★ 可复用模板 (新增)
│   └── PROJECT_ANALYSIS.md  # 项目分析模板 (30分钟五维度评估)
│
├── logs/                   # ★ 输出日志 (自动生成)
│   ├── opportunities.md    # 机会跟踪日志 (手动维护)
│   ├── github_stats.json   # 最新 GitHub 统计 (自动更新)
│   ├── arxiv_papers.md     # 最新论文列表 (自动更新)
│   ├── latest_digest.md    # 最新周报 (自动更新)
│   └── digests/            # 历史周报存档
│
├── analysis/               # 深度分析产出
│   ├── INSIGHTS.md         # 8 卷 42+ 条洞察（3400+ 行）
│   ├── PROJECT_MAP.md      # 80+ 项目商业价值分级排名
│   └── STRATEGY_BRIEF.md  # 执行摘要
│
├── gtm/                    # Go-to-Market 策略
│   └── LIGHTRAG_GTM.md    # LightRAG GTM + 3封冷邮件模板
│
├── landing/                # 产品落地页
│   ├── index.html          # lightrag.io 零依赖 Landing Page
│   └── vercel.json         # Vercel 一键部署配置
│
├── scripts/
│   └── clone_hkuds.py      # 批量克隆全部 HKUDS 仓库
│
└── .github/workflows/
    ├── weekly-update.yml   # 每周一自动运行所有自动化脚本
    └── pages.yml           # Landing Page 自动部署
```

---

## 快速导航

### 🗺️ 看地图：项目商业价值排名 → [analysis/PROJECT_MAP.md](analysis/PROJECT_MAP.md)

80+ 项目按变现速度 × 商业规模分 5 级：

| 级别 | 代表项目 | 变现窗口 |
|------|---------|---------|
| **S 级 ★★★★★** | LightRAG、AutoAgent、MiniRAG、nanobot | 0-12 个月 |
| **A 级 ★★★★☆** | RAG-Anything、VideoRAG、DeepCode | 需加速商业化 |
| **B 级 ★★★☆☆** | ClawTeam、图 AI 套件、UrbanGPT | 12-24 个月 |
| **C-E 级 ★★☆☆☆** | 30+ 推荐系统、时空计算 | 学术积累期 |

### 💡 看洞察：42 条战略分析 → [analysis/INSIGHTS.md](analysis/INSIGHTS.md)

| 卷 | 核心内容 |
|----|---------|
| 第一篇 | HKUDS 内部技术/市场/运营 31 条核心洞察 |
| 第二篇 | 外部宏观视角：RAG 断裂、主权 AI、AIBOM |
| 第三篇 | AuditRAG 产品规格 + 6 封冷邮件模板 |
| 第四篇 | a16z 投资人视角 10 条（真正竞争对手/AEO/合规） |
| 第五篇 | 4 角色 × 6 战场市场辩论（大模型/Agent/RAG/教育） |
| 第六篇 | 个人策略：ProductHunt 15 类别 + 路径 A/B/C |
| 第七篇 | VideoRAG/RAG-Anything/nanobot/OpenPhone/AI-Trader |
| 第八篇 | DeepCode/FutureShow/LightReasoner/ClawTeam/DeepTutor |

### 🚀 看 GTM：LightRAG 商业化路径 → [gtm/LIGHTRAG_GTM.md](gtm/LIGHTRAG_GTM.md)

- **ICP**：法律事务所、金融研究、医疗 R&D、咨询公司
- **定价**：Free → $99/月 Pro → $499/月 Team → Enterprise 定制
- **12 个月目标**：ARR $1M，付费用户 500+
- **附录**：3 封天使投资人 Cold Email（a16z 版、故事版、数据版）

### 🌐 看落地页：lightrag.io → [landing/index.html](landing/index.html)

- 587 行零依赖 HTML + CSS
- 已部署：https://moshierming.github.io/lightrag-landing/
- 自定义域名：lightrag.io（已绑定）

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

## 如何使用本仓库

### 🆕 新的研究循环（每周做一遍）

```bash
# 1. 安装依赖
pip install requests feedparser

# 2. 拉取最新仓库状态
git pull

# 3. 运行自动化（或等 GitHub Actions 自动运行）
export GITHUB_TOKEN=你的token  # 可选，避免限速
python automation/fetch_github_stats.py   # 抓 GitHub 动态
python automation/arxiv_monitor.py        # 查新论文
python automation/generate_digest.py     # 生成周报

# 4. 阅读周报，找到行动机会
cat logs/latest_digest.md

# 5. 记录新机会
vim logs/opportunities.md

# 6. 执行至少一个具体行动
#    （PR / 博客 / 邮件 / 新工具 / 新分析）
```

### 分析新项目（用模板）

```bash
cp templates/PROJECT_ANALYSIS.md analysis/new-project-name.md
# 填写模板，30分钟五维度评估
```

### 如果你是研究者
→ 从 [INSIGHTS.md](analysis/INSIGHTS.md) 开始，了解 8 卷分析

### 如果你是创业者 / 产品经理
→ 看 [PROJECT_MAP.md](analysis/PROJECT_MAP.md) 找方向 + [方法论框架](methodology/FRAMEWORK.md) 学工具

### 如果你想立刻动手
→ Fork 本仓库 → 设置 GitHub Token → 运行自动化脚本 → 开始你自己的研究循环

---

## 持续更新计划

系统会自动更新 `logs/` 目录。手动产出按优先级：

- [ ] 每周阅读 `logs/latest_digest.md` 并执行一个行动
- [ ] 为 AutoAgent 补充 GTM 方案  
- [ ] 为 MiniRAG/nanobot 写 Landing Page
- [ ] 分析 ClawTeam 的 2026 年竞争格局
- [ ] 出品 HKUDS 项目英文版评估报告（面向国际社区）

---

## 关联资源

| 资源 | 链接 |
|------|------|
| HKUDS GitHub 主页 | https://github.com/HKUDS |
| LightRAG 官方仓库 | https://github.com/HKUDS/LightRAG |
| LightRAG Landing Page | https://moshierming.github.io/lightrag-landing/ |
| 克隆脚本所需的 HKUDS 项目列表 | 见 `scripts/clone_hkuds.py` |

---

## License

本仓库的分析文档（INSIGHTS.md 等）基于公开信息撰写，采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。代码文件（landing page、scripts）采用 MIT 协议。
