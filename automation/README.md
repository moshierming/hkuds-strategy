# 自动化模块 · Automation

这个目录包含所有自动化脚本，让重复性研究工作由机器完成。

## 脚本列表

| 脚本 | 功能 | 运行频率 |
|------|------|---------|
| `fetch_github_stats.py` | 抓取 HKUDS 所有仓库的 stars/forks/活跃度 | 每周一 |
| `arxiv_monitor.py` | 监控 HKUDS 相关 arXiv 新论文 | 每周一 |
| `generate_digest.py` | 合并以上数据，生成每周研究摘要 | 每周一 |

## 快速开始

```bash
# 安装依赖
pip install requests feedparser

# 设置 GitHub Token (可选，建议设置以避免限速)
export GITHUB_TOKEN=ghp_你的token

# 运行完整的每周更新
python automation/fetch_github_stats.py
python automation/arxiv_monitor.py --days 7
python automation/generate_digest.py
```

## 输出文件

所有输出保存在 `logs/` 目录：

```
logs/
├── github_stats.json      # 所有仓库的原始统计数据
├── stats_changes.md       # GitHub 动态变化报告
├── arxiv_papers.md        # arXiv 新论文列表
├── latest_digest.md       # 最新周报 (快捷入口)
├── opportunities.md       # 机会跟踪日志 (手动维护)
└── digests/
    └── YYYY-MM-DD.md      # 历史周报存档
```

## GitHub Actions 自动化

每周一自动运行（UTC 8:00），结果自动提交回仓库。

手动触发：GitHub → Actions → "每周研究自动化" → Run workflow

## 扩展建议

- 增加 `monitor_issues.py` 监控高质量 Issue 并第一时间回应
- 增加 `competitor_analysis.py` 追踪竞品仓库动态
- 增加 `twitter_monitor.py` 追踪相关话题的社交媒体讨论
