# 信号来源总览 · Signal Sources

> 所有被监控的信息渠道。定期回顾：哪些来源产出了高质量洞察？哪些是噪音？

---

## 自动化监控 (每周运行)

| 来源 | 脚本 | 输出文件 | 覆盖范围 |
|------|------|---------|---------|
| **HKUDS GitHub** | `fetch_github_stats.py` | `logs/github_stats.json` | HKUDS 82 个仓库统计 |
| **arXiv** | `arxiv_monitor.py` | `logs/arxiv_papers.md` | AI/ML 相关新论文 |
| **ProductHunt** | `fetch_producthunt.py` | `logs/producthunt_trends.md` | AI/开发工具/生产力类目 |
| **HackerNews** | `fetch_hackernews.py` | `logs/hackernews_signals.md` | Show HN / 高分 AI 讨论 |
| **GitHub Trending** | `fetch_github_trending.py` | `logs/github_trending.md` | 全球 AI/ML 热门仓库 |
| **信号聚合** | `aggregate_signals.py` | `logs/weekly_signal_digest.md` | 跨渠道综合周报 |

---

## 手动跟踪 (需人工)

| 来源 | 频率 | 记录到 | 说明 |
|------|------|--------|------|
| **Twitter/X** | 实时 | `logs/insights_log.md` | 关注 @karpathy @simonw @yoheinakajima 等 |
| **Reddit** | 每周 | `logs/insights_log.md` | r/MachineLearning, r/LocalLLaMA, r/programming |
| **Discord/Slack** | 每周 | `logs/insights_log.md` | LangChain/LlamaIndex/Hugging Face 社区 |
| **竞品发布** | 随时 | `logs/opportunities.md` | 竞品有新功能/融资/收购时 |
| **客户反馈** | 随时 | `logs/opportunities.md` | GitHub Issues/邮件中的用户痛点 |
| **学术会议** | 按季度 | `logs/insights_log.md` | NeurIPS/ICLR/ACL/WWW 等 |

---

## 信号质量评估 (季度更新)

> 填写：哪个来源给你带来了最有价值的洞察？

| 来源 | 信号质量 (1-5) | 最近有价值的洞察 | 是否继续 |
|------|-------------|----------------|---------|
| HKUDS GitHub | 4 | stars 排名揭示真实热度 | ✅ |
| arXiv | 3 | 技术方向早期预警 | ✅ |
| ProductHunt | ? | 待评估 | 待定 |
| HackerNews | ? | 待评估 | 待定 |
| GitHub Trending | ? | 待评估 | 待定 |

---

## 关注人物列表

研究社区中值得持续关注的人（他们的想法本身就是信号）：

| 人物 | 领域 | 关注渠道 | 关注原因 |
|------|------|---------|---------|
| Andrej Karpathy | LLM 基础/教育 | Twitter | 判断力极强，善于解释核心 |
| Simon Willison | 开发者工具 | Blog/Twitter | 最早发现新工具价值 |
| Yohei Nakajima | AI Agent | Twitter | BabyAGI 作者，agent 前沿 |
| Jerry Liu | LlamaIndex | Twitter | RAG 工程最前沿 |
| Harrison Chase | LangChain | Twitter | Agent 框架生态 |
| HKUDS 作者团队 | HKUDS 全领域 | GitHub/论文 | 直接关注源头 |

---

## 添加新来源的标准

一个新来源值得加入监控，当且仅当：

1. **高信噪比**：有意义的内容 > 50%
2. **可自动化**：有 API 或可稳定爬取
3. **差异化**：与现有来源覆盖的信号不重叠
4. **时效性**：能提供比现有渠道更早的信号

目前候选中：
- [ ] Twitter/X API（成本问题）
- [ ] Reddit API（r/MachineLearning）
- [ ] Semantic Scholar（学术引用趋势）
- [ ] LinkedIn 职位 API（人才流向 = 资金流向）
