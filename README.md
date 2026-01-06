# XHS_Business_Idea_Validator 小红书解析市场机会智能体

## 📋 项目概述

小红书收集和分析数据来解析市场需求用户痛点及竞争格局 
深度！ 评论分析！用户画像！找商机！
都在说这些，但是感觉都没有人开源，那么我开源一个：

为什么找市场机会小红书？
商机在具体的问题里

小红书这里汇聚着包罗万象的生活问题和经验分享，“遇事不决小红书”成为年轻人常用的决策路径，他们相信能在这里找到答案。

对商家而言，要想深入了解今年的消费者在苦恼些什么、真正需要些什么，小红书是必经之路。

消费者不是没有需求，而是需求太具体。


### 核心功能

- 📊 **小红书数据抓取**: 自动抓取相关笔记和评论数据（使用用户输入作为搜索关键词，已移除关键词生成功能）
- 🤖 **AI 内容分析**: 使用 LLM 分析用户痛点和市场需求
- 📄 **自动化报告生成**: 生成专业的市场验证报告


### 系统流程图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              系统入口                                         │
│                    python run_agent.py "业务创意"                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           环境配置与初始化                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │  Config     │  │ Context     │  │ MCP Clients │  │ Storage     │           │
│  │  Manager    │  │  Store      │  │             │  │  Server     │           │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Orchestrator Agent 启动                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 任务: validate_business_idea                                           │   │
│  │ 业务创意: "用户输入的业务创意"                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        1. 数据抓取阶段 (Scraper Agent)                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 任务: scrape_data                                                     │   │
│  │ - 使用业务创意作为搜索关键词                                           │   │
│  │ - 通过 XHS MCP Server 抓取小红书笔记和评论                             │   │
│  │ - 保存 checkpoint: scraping_complete.json                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        2. 数据分析阶段 (Analyzer Agent)                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 任务: analyze_data                                                    │   │
│  │ ├── analyze_posts: 分析笔记内容，提取用户痛点和需求                    │   │
│  │ ├── analyze_comments: 分析评论情感和用户反馈                           │   │
│  │ ├── comments_tag_analysis: 评论标签分析                                │   │
│  │ └── combined_analysis: 综合分析生成市场验证评分                        │   │
│  │ 保存 checkpoint: analysis_complete.json, comments_tag_analysis_complete.json│ │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        3. 报告生成阶段 (Reporter Agent)                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 任务: generate_and_save_report                                        │   │
│  │ ├── generate_html_report: 生成 HTML 格式报告                          │   │
│  │ ├── save_report: 保存报告到 reports/ 目录                            │   │
│  │ └── 保存 checkpoint: report_saved.json                               │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        4. 结果输出与存储                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ 输出文件:                                                             │   │
│  │ ├── reports/{business_idea}_{timestamp}.html                          │   │
│  │ ├── agent_context/checkpoints/{run_id}/                               │   │
│  │ │   ├── scraping_complete.json                                        │   │
│  │ │   ├── analysis_complete.json                                        │   │
│  │ │   ├── comments_tag_analysis_complete.json                           │   │
│  │ │   ├── combined_analysis_complete.json                               │   │
│  │ │   └── report_saved.json                                             │   │
│  │ └── 小提示: 相关资料请到 agent_context/checkpoints/{run_id}/ 目录下查看 │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              任务完成                                         │
│                    返回 TaskResult 包含执行结果                                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 快速开始

```bash
# 安装依赖
cd XHS_Business_Idea_Validator
pip install -r requirements.txt

# 配置 API 密钥 (编辑 agent_system/.env 文件)
# OPENAI_API_KEY=your_key
# TIKHUB_TOKEN=your_token

# 运行验证
python run_agent.py 在深圳卖陈皮
```

👉 **详细使用指南**: [USER_GUIDE.md](USER_GUIDE.md)

  

## 📁 目录结构

```
agent_system/
├── models/                          # 数据模型
│   ├── __init__.py
│   ├── agent_models.py              # TaskResult, ProgressUpdate, ExecutionPlan
│   ├── context_models.py            # RunContext, ContextQuery
│   └── business_models.py           # KeywordModel, XhsNoteModel, etc.
│
├── agents/                          # Agent 核心
│   ├── __init__.py
│   ├── base_agent.py                # Agent 基类
│   ├── context_store.py             # 上下文存储
│   ├── config.py                    # 配置管理（支持 .env）
│   ├── orchestrator.py              # ✅ 主编排 Agent
│   ├── subagents/                   # ✅ 子 Agents
│   │   ├── __init__.py
│   │   ├── scraper_agent.py         # 数据抓取 Agent
│   │   ├── analyzer_agent.py        # 数据分析 Agent
│   │   └── reporter_agent.py        # 报告生成 Agent
│   └── skills/                      # ✅ Skills
│       ├── __init__.py
│       ├── scraper_skills.py
│       ├── analyzer_skills.py
│       └── reporter_skills.py
│
├── mcp_servers/                     # MCP 服务器
│   ├── __init__.py
│   ├── xhs_server.py                # 小红书 MCP 服务 ✅
│   ├── llm_server.py                # LLM MCP 服务 ✅
│   └── storage_server.py            # 存储服务 ✅
│
└── tests/                           # 测试
    ├── __init__.py
    ├── test_integration.py          # 集成测试 ✅
    └── test_e2e.py                  # 端到端测试 ✅
```





## 📊 指标利用情况总结

### 1. **liked_count (点赞数)** ✅ 已利用
- **用途**：计算互动评分、热门帖子排序
- **计算公式**：`total_engagement = liked + collected * 2 + shared * 3 + comments`
- **位置**：[analyzer_skills.py:1784](file:///d:\agent_system\agents\skills\analyzer_skills.py#L1784), [analyzer_agent.py:591](file:///d:\agent_system\agents\subagents\analyzer_agent.py#L591)

### 2. **collected_count (收藏数)** ✅ 已利用（加权 2 倍）
- **用途**：计算互动评分，权重更高（×2）
- **计算公式**：`collected * 2`
- **位置**：[analyzer_agent.py:592](file:///d:\agent_system\agents\subagents\analyzer_agent.py#L592)
- **理由**：收藏代表更强的用户认可度

### 3. **shared_count (分享数)** ✅ 已利用（加权 3 倍）
- **用途**：计算互动评分，权重最高（×3）
- **计算公式**：`shared * 3`
- **位置**：[analyzer_agent.py:593](file:///d:\agent_system\agents\subagents\analyzer_agent.py#L593)
- **理由**：分享代表传播价值最高

### 4. **comments_count (评论数)** ✅ 已利用
- **用途**：计算互动评分、分析评论数量
- **计算公式**：`comments * 3` (在 analyzer_skills.py 中)
- **位置**：[analyzer_skills.py:1784](file:///d:\agent_system\agents\skills\analyzer_skills.py#L1784), [analyzer_agent.py:594](file:///d:\agent_system\agents\subagents\analyzer_agent.py#L594)

### 5. **publish_time (发布时间)** ✅ 已利用
- **用途**：分析最近 30 天活跃度
- **计算逻辑**：统计 30 天内发布的帖子数量
- **位置**：[analyzer_agent.py:607-611](file:///d:\agent_system\agents\subagents\analyzer_agent.py#L607-L611)

---

## 🎯 核心计算逻辑

### **互动评分 (engagement_score)**
```python
total_engagement = liked + collected * 2 + shared * 3 + comments * 3

if total_engagement > 1000:
    engagement_score = 10
elif total_engagement > 500:
    engagement_score = 8
elif total_engagement > 100:
    engagement_score = 6
elif total_engagement > 50:
    engagement_score = 4
else:
    engagement_score = 2
```

### **加权策略**
- 点赞：权重 1×
- 收藏：权重 2×（用户认可度高）
- 分享：权重 3×（传播价值最高）
- 评论：权重 3×（参与度高）

---

## 📈 指标应用场景

1. **热门帖子排序**：按 `total_engagement` 降序排列，取 TOP 3
2. **平均互动评分**：所有相关帖子的 `engagement_score` 平均值
3. **报告展示**：在 HTML 报告中显示平均互动评分
4. **活跃度分析**：统计最近 30 天发布的帖子比例

---

## 💡 总结

✅ **所有重要指标都已充分利用**，包括：
- 点赞、收藏、分享、评论数都参与了互动评分计算
- 不同指标有合理的权重分配
- 发布时间用于分析内容活跃度
- 计算结果用于排序、评分和报告展示

系统对这些指标的利用是**完整且合理**的。