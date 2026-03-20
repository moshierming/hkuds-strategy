# MiniRAG GTM 方案 · Go-to-Market Strategy

> 目标：让 MiniRAG 从边缘 RAG 框架变成隐私优先的本地知识库产品，12 个月内达到 ARR $200K。

---

## 一、产品定位

### 核心主张

**"让小模型也能做好 RAG——在你自己的设备上，永不出境"**

MiniRAG 是专为 **资源受限场景** 设计的 RAG 框架：
- 用 Phi-3.5-mini（2GB 内存）替代 GPT-4 做知识库问答
- 异构图索引让 3B 参数小模型超过 NaiveRAG + GPT-4o-mini 的精度
- 仅需 LightRAG 25% 的存储空间
- 支持 10+ 图数据库（Neo4j / PostgreSQL / TiDB），完全离线部署

### 为什么现在是时候商业化

| 信号 | 数据 |
|------|------|
| GitHub Stars | 1,792（快速增长） |
| arXiv | 2501.06713，2025 年初发布 |
| 精度突破 | Phi-3.5-mini + MiniRAG = 53.3% vs GPT-4o-mini NaiveRAG = 46.6% |
| 合规压力 | GDPR / 中国《数据安全法》/ 《个人信息保护法》推动本地部署 |
| 边缘爆发 | AI PC（Intel NPU / Apple M4）+ IoT 设备 2025 年出货量激增 |
| pip 可安装 | `pip install minirag-hku`，3 步可跑通 |

### 与竞品的定位差异

| 维度 | LlamaIndex | PrivateGPT | Ollama | LightRAG | **MiniRAG** |
|------|-----------|------------|--------|----------|------------|
| 目标场景 | 云端 / 企业 | 本地 Chat | 本地推理 | 知识图谱 RAG | **边缘/离线 RAG** |
| SLM 支持 | 部分 | 有限 | 仅推理 | 需要较强 LLM | **专为 SLM 设计** |
| 存储效率 | 一般 | 一般 | 无 RAG | 高 | **极高（LightRAG 的 25%）** |
| 图结构检索 | 有 | 无 | 无 | 有 | **异构图，更轻** |
| 生产部署 | 复杂 | 复杂 | 简单 | 中等 | **pip + Docker** |
| 数据隐私 | 可选 | ✅ | ✅ | 可选 | **✅ 默认离线** |

**MiniRAG 的护城河**：不是"又一个 RAG 框架"，而是"让小模型在边缘设备上做出超预期 RAG 效果"的唯一工程化路径。

---

## 二、目标客户（ICP）

### 主要 ICP：「数据不能出门」的行业用户

**ICP-A：金融 / 保险机构内部知识库**

| 属性 | 描述 |
|------|------|
| 画像 | 股份行、券商、保险公司的 IT 或 AI 团队（100-10,000 人） |
| 痛点 | 监管禁止客户数据上云；GPT API 有数据泄露风险；本地部署 RAG 精度不达标 |
| 需求 | 合规本地知识库，能回答"这份合同条款适用哪个监管要求" |
| 获客渠道 | 金融科技峰会、银保监关联媒体、华为 / 腾讯云生态合作伙伴 |
| 付费意愿 | 项目制 $20K-100K，SaaS 私有化 $3,000-10,000/月 |

**ICP-B：医疗 / 生命科学研究机构**

| 属性 | 描述 |
|------|------|
| 画像 | 三甲医院数字化部门、CRO 公司、基因组学实验室 |
| 痛点 | 患者数据 / 临床数据受 HIPAA / 《医疗数据管理规定》约束 |
| 需求 | 本地病历知识库 + 诊疗指南问答，不依赖外部 API |
| 获客渠道 | 医疗 AI 展会、华为昇腾生态、HIS 系统供应商集成 |
| 付费意愿 | 项目制 $30K-200K |

**ICP-C：政府 / 军工 / 央企内网部署**

| 属性 | 描述 |
|------|------|
| 画像 | 政务云、国资委系统企业的涉密信息管理 |
| 痛点 | 数据绝对不可出境，本地 LLM 性能不足 |
| 需求 | 依托国产小模型（Qwen / GLM / MiniCPM）的高精度本地 RAG |
| 获客渠道 | 国产化替代政策采购、信创生态（华为 / 统信 / 麒麟）合作 |
| 付费意愿 | 项目制 $50K-500K |

**ICP-D：边缘设备 / 工业 IoT 开发商**

| 属性 | 描述 |
|------|------|
| 画像 | 工业机器人、智能汽车、边缘服务器的软件开发商 |
| 痛点 | 网络不稳定甚至无网，设备算力 4-16GB 内存，需要 RAG 支持异常手册检索 |
| 需求 | 嵌入式知识库，能在 ARM / RISC-V 小板子上跑 |
| 获客渠道 | 嵌入式系统展、工业 AI 社区（百度飞桨 / NVIDIA Jetson 生态） |
| 付费意愿 | SDK 授权 $5K-50K，嵌入式 OEM 授权 |

---

## 三、产品策略

### 产品形态（分阶段）

**Phase 0（当前）：开源框架**
- `pip install minirag-hku`
- API + Docker 部署文档
- LiHua-World 基准数据集
- 面向研究者和技术早期用户

**Phase 1（1-3 个月）：MiniRAG Desktop**
- Electron / Tauri 封装桌面应用
- 一键导入 PDF / Word / Markdown
- 内置 Ollama 集成（自动下载 Qwen2.5-3B / Phi-3.5-mini）
- macOS / Windows 打包，面向个人 + SMB
- 目标：ProductHunt 发布，#1 Product of the Day

**Phase 2（3-6 个月）：MiniRAG Server（私有化版）**
- Docker Compose 一键部署
- Web 管理界面：知识库管理 / 权限控制 / 审计日志
- 支持 Active Directory / LDAP 集成
- 企业级 SLA 支持
- 定价：$999/月起（无限用户）

**Phase 3（6-12 个月）：行业垂直解决方案**
- MiniRAG for Finance（金融合规增强版）
- MiniRAG for Medical（医疗知识库版）
- MiniRAG for Gov（信创兼容版，支持麒麟 OS / 鲲鹏硬件）
- 合作伙伴集成：华为云 / 腾讯云 / 阿里云私有化

---

## 四、核心差异化：技术护城河

### 异构图索引（Heterogeneous Graph Indexing）

```
传统 RAG（NaiveRAG）：          MiniRAG：
文档 → 分块 → 向量检索          文档 → 文本块 + 命名实体
                                     ↓
                              异构图（Text Node + Entity Node）
                                     ↓
                              拓扑增强检索（跨实体多跳推理）
```

**为什么小模型需要异构图**：
- SLM（3B）语义理解弱 → 图结构弥补语义缺失
- 多跳问题（"LiHua 的手机什么颜色"需要跨文档推理）→ 图遍历比向量检索准确
- 存储压缩：Text+Entity 共享图结构 → 25% 存储

### 关键性能对比

| 场景 | 模型 | NaiveRAG | LightRAG | **MiniRAG** | 提升 |
|------|------|----------|----------|------------|------|
| LiHua-World | Phi-3.5-mini | 41.2% | 39.8% | **53.3%** | +12.1pp |
| LiHua-World | Qwen2.5-3B | 43.7% | 39.2% | **48.8%** | +5.1pp |
| MultiHop-RAG | Phi-3.5-mini | 42.7% | 27.0% | **50.0%** | +7.3pp |
| MultiHop-RAG | GLM-Edge-1.5B | 44.4% | / | **51.4%** | +7.0pp |

> 核心卖点：**用 3B 小模型，做出比 GPT-4o-mini NaiveRAG 更好的效果**

---

## 五、定价策略

### 开源 + 商业双轨

```
┌─────────────────────────────────────────────────┐
│  开源核心（MIT）                                   │
│  pip install minirag-hku                         │
│  永久免费，无功能限制，社区支持                      │
└─────────────────────────────────────────────────┘
         ↓ 商业化层
┌──────────────┬─────────────────┬────────────────┐
│ Personal     │ Business        │ Enterprise     │
│ $0/月        │ $99-499/月      │ 联系销售        │
│              │                 │                │
│ 开源完整功能  │ + 桌面 App      │ + 私有化部署    │
│ 社区 Forum   │ + 优先 Issue    │ + SLA 99.9%    │
│              │ + 商业支持 8/5  │ + 信创兼容版    │
│              │ + 私有数据不上云 │ + 行业定制      │
│              │ + 最多 5 用户   │ + 无限用户      │
└──────────────┴─────────────────┴────────────────┘
```

### 额外收入流

| 收入类型 | 定价 | 目标客户 |
|---------|------|---------|
| 实施/部署服务 | $5K-50K/项目 | 中大企业 |
| 私有化定制开发 | $20K-200K | 金融/政府 |
| 信创适配包（鲲鹏/飞腾） | $10K-50K/年 | 央企/政务 |
| OEM 嵌入式授权 | $5K-30K + 量产分成 | 工业设备商 |

---

## 六、获客策略

### 渠道优先级（12 个月）

#### 第一阶段（M1-3）：技术社区主导

**GitHub / arXiv 自然流量**
- 写"MiniRAG vs LlamaIndex vs PrivateGPT：在 M2 MacBook 上的实测对比"
- 写"在树莓派 5 上用 MiniRAG + Phi-3 构建离线知识库"
- 关键词：`local RAG`、`offline RAG`、`private LLM knowledge base`

**HackerNews Show HN**
- 标题："Show HN: I built a RAG system that runs on edge devices with 2GB RAM"
- 强调：无需 API Key，永不上云，开箱即用

**ProductHunt**
- 主打 Desktop App 版本发布
- 口号："Notion AI for your files — but runs entirely on your computer"
- 配合 Twitter/X 技术 KOL 联动

#### 第二阶段（M3-6）：垂直市场渗透

**中国市场（重点）**
- 微信公众号：GDPR/《数据安全法》合规方案专题
- HuggingFace 中文模型社区（Qwen / GLM 用户）
- 钉钉 / 飞书集成插件
- 联系华为昇腾 AI 生态合作伙伴计划

**海外合规场景**
- Reddit r/selfhosted、r/LocalLLaMA 社区
- LinkedIn 定向：金融/医疗/政府 IT Decision Maker
- Quora 回答 "how to build HIPAA compliant AI knowledge base"

#### 第三阶段（M6-12）：企业直销

**目标客户名单**
- 中国：四大行 IT 中心、字节/腾讯/阿里内部知识库替换
- 海外：德国制造业（ERP 本地 AI 助手）、日本金融（Fintech 隐私合规）

**合作伙伴渠道**
- 华为云 WeLink 生态（政府/国企触达）
- 腾讯云 TDSQL 集成（数据库原生知识库）
- 联想 AI PC 预装（ThinkPad X1 Carbon + MiniRAG Demo）

---

## 七、关键里程碑（12 个月路线图）

| 时间 | 里程碑 | 目标指标 |
|------|--------|---------|
| M1 | GitHub Star 突破 5,000 | 日新增 50+ Star |
| M2 | 发布 Desktop App Beta | 1,000 次下载 |
| M3 | ProductHunt 发布 | Top 5 Product of Day |
| M4 | 第一个付费企业客户 | $10K ARR |
| M5 | 信创兼容版发布（麒麟/鲲鹏） | 1 个政务客户 PoC |
| M6 | MRR $10K | 3 个付费企业 + 100 个 Business 订阅 |
| M9 | 行业解决方案上线（Finance/Medical） | 5 个企业客户 |
| M12 | ARR $200K | 10 个企业客户 + 500 Business 订阅 |

---

## 八、竞争响应预案

### 若 LlamaIndex / LangChain 发布轻量版

**应对**：强调 MiniRAG 专为 SLM 设计的异构图算法——大厂轻量化是"裁剪"，MiniRAG 是"重新设计"。数据：Phi-3.5-mini + MiniRAG > GPT-4o-mini + NaiveRAG。

### 若 Ollama 推出 RAG 功能

**应对**：Ollama 做的是**推理基础设施**，MiniRAG 做的是**知识检索算法**。两者可组合（MiniRAG 调用 Ollama 做推理），而非竞争关系。主打集成文档。

### 若 LightRAG 推出轻量版

**应对**：作为同门兄弟，强调 MiniRAG 是"LightRAG 边缘版"，社区可共享。实际上 LightRAG 定位高端/复杂场景，MiniRAG 定位边缘/低资源——市场切割清晰。

---

## 九、核心指标（North Star Metrics）

| 指标 | 当前 | M6 目标 | M12 目标 |
|------|------|---------|---------|
| GitHub Stars | 1,792 | 8,000 | 20,000 |
| pip 月下载量 | 未知 | 5,000/月 | 20,000/月 |
| ARR | $0 | $50K | $200K |
| 企业客户 | 0 | 3 | 10 |
| Business 订阅 | 0 | 100 | 500 |
| 贡献者数量 | ~10 | 30 | 80 |

---

## 十、总结：为什么 MiniRAG 能赢

1. **时机对**：GDPR/数据安全法落地 + AI PC 爆发，本地 RAG 需求从"可选"变"必选"
2. **技术真**：异构图让 3B 模型做出 GPT-4o 级别效果，不是 PR，是论文实验数据
3. **市场空**：没有一家公司同时做到"SLM 友好 + 图索引 + 离线 + 生产就绪"
4. **杠杆足**：LightRAG 的 IP + 社区背书（LightRAG 38K⭐），MiniRAG 站在巨人肩上
5. **合规刚需**：金融/医疗/政府的数据不出境是**法律要求**，不是功能偏好

> **MiniRAG = 给数据不能出门的企业，提供 GPT-4 级别的本地 RAG 能力**

---

*生成时间：2025 年*
*数据来源：HKUDS/MiniRAG GitHub、arXiv 2501.06713、INSIGHTS.md 分析报告*
