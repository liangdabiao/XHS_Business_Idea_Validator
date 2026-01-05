# 业务创意验证系统 - 用户使用指南

## 📋 目录

1. [系统概述](#系统概述)
2. [环境要求](#环境要求)
3. [快速开始](#快速开始)
4. [配置说明](#配置说明)
5. [使用方法](#使用方法)
6. [输出说明](#输出说明)
7. [常见问题](#常见问题)
8. [高级功能](#高级功能)

---

## 系统概述

**业务创意验证系统** 是一个基于 Agent 架构的自动化市场调研工具，用于验证业务创意的市场可行性。

### 核心功能

- 🔑 **智能关键词生成**: 根据业务创意自动生成搜索关键词
- 📊 **小红书数据抓取**: 自动抓取相关笔记和评论数据
- 🤖 **AI 内容分析**: 使用 LLM 分析用户痛点和市场需求
- 📄 **自动化报告生成**: 生成专业的市场验证报告

### 系统架构

```
用户输入业务创意
      ↓
┌─────────────────┐
│  Orchestrator   │ ← 主编排器
└─────────────────┘
      ↓
┌───────────┬───────────┬───────────┬───────────┐
│  Keyword  │ Scraper   │ Analyzer  │ Reporter  │
│  Agent    │  Agent    │  Agent    │  Agent    │
└───────────┴───────────┴───────────┴───────────┘
      ↓           ↓           ↓           ↓
   关键词生成   数据抓取     内容分析     报告生成
```

---

## 环境要求

### 必需环境

- **Python**: 3.9 或更高版本
- **操作系统**: Windows / macOS / Linux
- **网络**: 需要访问 OpenAI API 和小红书数据源

### API 密钥

需要以下 API 密钥：

| API | 用途 | 获取方式 |
|-----|------|---------|
| **OpenAI API Key** | LLM 分析 | [OpenAI Platform](https://platform.openai.com/) 或使用代理服务 |
| **TikHub Token** | 小红书数据 | [TikHub](https://www.tikhub.io/) |

---

## 快速开始

### 1. 安装依赖

```bash
cd E:/Business_Idea_Validator/agent_system
pip install -r requirements.txt
```

### 2. 配置 API 密钥

编辑 `.env` 文件：

```bash
# 复制示例配置（Windows 使用 copy 而非 cp）
cp .env.example .env

# 编辑配置文件，填入你的 API 密钥
# Windows: notepad .env
# macOS/Linux: nano .env
```

配置内容：

```env
# OpenAI API 配置
OPENAI_API_KEY="your_openai_api_key_here"
OPENAI_BASE_URL="https://api.openai.com/v1"

# 如果使用 API 代理（如 api2d.net）
# OPENAI_BASE_URL="https://oa.api2d.net/v1"

# TikHub API 配置（用于小红书数据）
TIKHUB_TOKEN="your_tikhub_token_here"
```

### 3. 运行测试验证

```bash
cd E:/Business_Idea_Validator/agent_system
python tests/test_e2e.py
```

如果看到 `🎉 端到端测试通过!`，说明系统已正确配置。

---

## 配置说明

### 完整配置示例

`.env` 文件：

```env
# ============================================================
# API Keys
# ============================================================

# OpenAI API Key（必需）
# 获取方式: https://platform.openai.com/api-keys
OPENAI_API_KEY="sk-proj-xxxxxxxxxxxxx"

# OpenAI Base URL（可选）
# 默认: https://api.openai.com/v1
# 如使用代理，修改为代理地址
OPENAI_BASE_URL="https://oa.api2d.net/v1"

# TikHub Token（必需）
# 获取方式: https://www.tikhub.io/user
TIKHUB_TOKEN="vZdfXsQag0VRrVysjLT4kjaa6yL0gTnBk/aTAi8aA=="

# ============================================================
# 系统配置
# ============================================================

# 每个关键词搜索的页数（默认: 2）
SCRAPER_PAGES_PER_KEYWORD=2

# 每个笔记获取的评论数（默认: 20）
SCRAPER_COMMENTS_PER_NOTE=20

# 最大笔记分析数（默认: 20）
ANALYZER_MAX_POSTS=20

# 报告输出目录（默认: reports）
REPORT_OUTPUT_DIR=reports
```

### 配置文件位置

系统会按以下顺序查找配置文件：

1. 当前目录的 `.env`
2. `agent_system/.env`
3. 项目根目录的 `.env`

---

## 使用方法

### 方法一：命令行使用（推荐）

使用提供的启动脚本 `run_agent.py`：

**使用方式：**

```bash
# 方式 1: 命令行参数
cd E:/Business_Idea_Validator/agent_system
python run_agent.py 在深圳卖陈皮

# 方式 2: 交互式输入
cd E:/Business_Idea_Validator/agent_system
python run_agent.py
# 然后输入: 在深圳卖陈皮
```

### 方法二：作为 Python 模块使用

```python
import asyncio
import sys
from pathlib import Path

# 添加 agent_system 到路径
sys.path.insert(0, str(Path("E:/Business_Idea_Validator/agent_system")))

from agents.orchestrator import OrchestratorAgent
from agents.config import ConfigManager
from agents.context_store import ContextStore
from mcp_servers.xhs_server import create_xhs_mcp_server
from mcp_servers.llm_server import create_llm_mcp_server
from mcp_servers.storage_server import create_storage_mcp_server


async def validate_business_idea(business_idea: str):
    """验证业务创意"""
    config = ConfigManager()
    context_store = ContextStore()

    # 获取 API 配置
    xhs_config = config.get_xhs_mcp_config()
    llm_config = config.get_llm_config()

    # 启动 MCP 服务器
    xhs_server = await create_xhs_mcp_server(xhs_config.auth_token)
    llm_server = await create_llm_mcp_server(llm_config.api_key, llm_config.base_url)
    storage_server = await create_storage_mcp_server("agent_context/checkpoints")

    mcp_clients = {
        "xhs": xhs_server,
        "llm": llm_server,
        "storage": storage_server
    }

    # 创建编排器
    orchestrator = OrchestratorAgent(config, context_store, mcp_clients)
    await orchestrator.start()

    # 执行验证
    result = await orchestrator.execute(
        task="validate_business_idea",
        context={},
        business_idea=business_idea,
        keyword_count=3,
        pages_per_keyword=2,
        comments_per_note=20,
        report_format="html"
    )

    # 清理资源
    await orchestrator.stop()
    await xhs_server.stop()
    await llm_server.stop()
    await storage_server.stop()

    return result


# 使用示例
if __name__ == "__main__":
    result = asyncio.run(validate_business_idea("在深圳卖陈皮"))
```

### 方法三：使用 Streamlit Web UI

如果项目已有 Streamlit UI，可以集成 Agent 系统：

```python
import streamlit as st
from agents.orchestrator import OrchestratorAgent

st.title("业务创意验证系统")

business_idea = st.text_area("请输入您的业务创意")

if st.button("开始验证"):
    with st.spinner("验证中..."):
        result = validate_idea(business_idea)

    st.success(f"验证完成！评分: {result.score}/100")
    st.markdown(result.report_html)
```

---

## 输出说明

### 1. 执行进度

系统会实时显示执行进度：

```
  [██████████████████████████████] 100.0% - 完成: 生成搜索关键词
  [████████████░░░░░░░░░░░░░░░░░░]  40.0% - 正在抓取数据...
```

### 2. 生成的报告

报告保存在 `reports/` 目录下，文件名格式：

```
{业务创意}_{时间戳}.html
```

例如：`在深圳卖陈皮_20260102_180534.html`

### 3. 报告内容

报告包含以下部分：

- **综合评分** (0-100): 市场可行性评分
- **市场验证摘要**: AI 分析总结
- **关键痛点**: 用户核心痛点
- **现有解决方案**: 市场上已有的解决方案
- **市场机会**: 发现的商机
- **建议**: 针对性建议

### 4. 检查点保存

系统会自动保存执行检查点，保存在 `agent_context/checkpoints/` 目录：

```
agent_context/checkpoints/
└── {业务创意}_{timestamp}/
    ├── scraping_complete.json      # 抓取完成检查点
    ├── analysis_complete.json      # 分析完成检查点
    └── combined_analysis_complete.json  # 综合分析检查点
```

---

## 常见问题

### Q1: 提示 "ModuleNotFoundError: No module named 'xxx'"

**解决方案：**

```bash
# 确保在 agent_system 目录
cd E:/Business_Idea_Validator/agent_system

# 安装依赖
pip install -r requirements.txt

# 或安装缺失的包
pip install python-dotenv openai pydantic httpx
```

### Q2: 提示 "401 Unauthorized" 或 "Invalid API Key"

**解决方案：**

1. 检查 `agent_system/.env` 文件是否存在
2. 确认 API Key 格式正确（没有多余空格）
3. 验证 API Key 是否有效
4. 检查 `OPENAI_BASE_URL` 是否正确

### Q3: TikHub API 返回错误

**解决方案：**

1. 访问 [TikHub](https://www.tikhub.io/) 检查账户余额
2. 确认 Token 正确复制（包含 `==` 后缀）
3. 检查 Token 是否过期

### Q4: 执行时间过长

**优化建议：**

使用快速模式运行 `run_agent.py` 时选择 `y`，这会使用更少的数据：
- 2 个关键词（而不是 3 个）
- 每个关键词 1 页（而不是 2 页）
- 每个笔记 5 条评论（而不是 20 条）

### Q5: 报告没有生成

**检查清单：**

1. 检查 `agent_system/reports/` 目录是否存在
2. 查看日志中是否有错误信息
3. 确认所有步骤都成功完成

---

## 高级功能

### 1. 自定义配置

创建 `agent_system/config.yaml`：

```yaml
llm:
  model_name: "gpt-4o"      # 或 "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 2000

scraper:
  pages_per_keyword: 3
  max_notes: 50
  request_delay: 1.5

analyzer:
  batch_size: 10
  max_retries: 3
```

### 2. 并行验证多个创意

```python
import asyncio
import sys
from pathlib import Path

# 添加 agent_system 到路径
sys.path.insert(0, str(Path("E:/Business_Idea_Validator/agent_system")))

from agents.orchestrator import OrchestratorAgent
from agents.config import ConfigManager
from agents.context_store import ContextStore
from mcp_servers.xhs_server import create_xhs_mcp_server
from mcp_servers.llm_server import create_llm_mcp_server
from mcp_servers.storage_server import create_storage_mcp_server

ideas = [
    "在深圳卖陈皮",
    "开一家宠物咖啡店",
    "做二手电子产品交易"
]

async def validate_all(ideas):
    """并行验证多个创意"""
    config = ConfigManager()
    context_store = ContextStore()

    xhs_config = config.get_xhs_mcp_config()
    llm_config = config.get_llm_config()

    xhs_server = await create_xhs_mcp_server(xhs_config.auth_token)
    llm_server = await create_llm_mcp_server(llm_config.api_key, llm_config.base_url)
    storage_server = await create_storage_mcp_server("agent_context/checkpoints")

    mcp_clients = {
        "xhs": xhs_server,
        "llm": llm_server,
        "storage": storage_server
    }

    results = []
    for idea in ideas:
        orchestrator = OrchestratorAgent(config, context_store, mcp_clients)
        await orchestrator.start()
        result = await orchestrator.execute(
            task="validate_business_idea",
            context={},
            business_idea=idea,
            keyword_count=2,
            pages_per_keyword=1,
            comments_per_note=10,
            report_format="html"
        )
        results.append(result)
        await orchestrator.stop()

    await xhs_server.stop()
    await llm_server.stop()
    await storage_server.stop()

    return results

results = asyncio.run(validate_all(ideas))

for idea, result in zip(ideas, results):
    score = result.data.get("step_results", {}).get("combined_analysis", {}).get("data", {}).get("analysis", {}).get("overall_score", "N/A")
    print(f"{idea}: {score}/100")
```

### 3. 导出为 JSON 格式

```python
import json

result = await validate_business_idea("你的创意")

# 导出为 JSON
with open("result.json", "w", encoding="utf-8") as f:
    json.dump(result.data, f, ensure_ascii=False, indent=2)
```

### 4. 自定义分析模板

修改 `agents/skills/analyzer_skills.py` 中的 prompt 来自定义分析逻辑。

---

## 技术支持

如有问题，请检查：

1. **日志文件**: 查看控制台输出的错误信息
2. **测试验证**: 运行 `python tests/test_e2e.py`
3. **配置检查**: 确认 `.env` 文件配置正确

---

## 更新日志

### v0.1.0 (2026-01-02)

- ✅ 完成 Phase 1: 基础架构搭建
- ✅ 完成 Phase 2: Subagents 实现
- ✅ 完成 Phase 3: Orchestrator 实现
- ✅ 支持 XHS 数据抓取
- ✅ 支持 LLM 内容分析
- ✅ 支持自动化报告生成

---

*文档最后更新: 2026-01-02*
