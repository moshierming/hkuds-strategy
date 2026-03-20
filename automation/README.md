# 自动化模块 · Automation

这个目录包含所有自动化脚本，让重复性研究工作由机器完成。
信息来源不局限于 HKUDS，而是全面覆盖 AI/开发者生态的多个渠道。

## 脚本列表

### HKUDS 核心监控
| 脚本 | 功能 | 输出 |
|------|------|------|
| `fetch_github_stats.py` | 抓取 HKUDS 所有仓库的 stars/forks/活跃度 | `logs/github_stats.json` |
| `arxiv_monitor.py` | 监控 HKUDS 相关 arXiv 新论文 | `logs/arxiv_papers.md` |
| `generate_digest.py` | 生成每周 HKUDS 聚焦摘要 | `logs/latest_digest.md` |

### 多源信号监控
| 脚本 | 功能 | 输出 |
|------|------|------|
| `fetch_hackernews.py` | 监控 HackerNews 高分 AI/开发者讨论 | `logs/hackernews_signals.md` |
| `fetch_github_trending.py` | 全球 GitHub Trending AI 仓库 | `logs/github_trending.md` |
| `fetch_producthunt.py` | ProductHunt AI/开发工具新品发布 | `logs/producthunt_trends.md` |

### 聚合与分析
| 脚本 | 功能 | 输出 |
|------|------|------|
| `aggregate_signals.py` | 跨渠道信号聚合、主题检测、综合周报 | `logs/weekly_signal_digest.md` |

## 快速开始

```bash
# 安装依赖
pip install requests feedparser beautifulsoup4

# 设置可选环境变量
export GITHUB_TOKEN=ghp_你的token    # 避免 API 限速
export PH_TOKEN=你的PH_token         # ProductHunt API (可选)

# 运行完整多源更新
python automation/fetch_github_stats.py
python automation/arxiv_monitor.py --days 7
python automation/fetch_hackernews.py --days 7
python automation/fetch_github_trending.py
python automation/fetch_producthunt.py
python automation/aggregate_signals.py
python automation/generate_digest.py
```

## 输出文件

所有输出保存在 `logs/` 目录：

```
logs/
├── github_stats.json          # HKUDS 仓库原始统计
├── stats_changes.md           # GitHub 动态变化报告
├── arxiv_papers.md            # arXiv 新论文列表
├── hackernews_signals.md      # HackerNews 热点信号
├── github_trending.md         # GitHub Trending 列表
├── producthunt_trends.md      # ProductHunt 新品
├── weekly_signal_digest.md    # 跨渠道综合周报 (最新)
├── latest_digest.md           # HKUDS 聚焦周报 (最新)
├── insights_log.md            # 洞察演化日志 (手动维护)
├── opportunities.md           # 机会跟踪日志 (手动维护)
└── digests/
    └── YYYY-MM-DD-full.md     # 历史完整周报存档
```

## GitHub Actions 自动化

每周一自动运行（UTC 8:00，北京时间 16:00），结果自动提交回仓库。

手动触发：GitHub → Actions → "每周研究自动化" → Run workflow

## ProductHunt API 配置

ProductHunt 免费计划每小时 100 次请求，无需 token 也可运行（匿名访问）。
如需更高配额，在 https://www.producthunt.com/v2/oauth/applications 申请并设置：

```bash
export PH_TOKEN=你的访问token
# 或在 GitHub Secrets 中添加 PH_TOKEN
```

