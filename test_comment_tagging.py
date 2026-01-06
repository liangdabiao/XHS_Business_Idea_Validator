"""
测试评论tag分析功能

用于调试评论tag分析失败的问题
"""
import asyncio
import sys
sys.path.insert(0, 'D:\\agent_system')

from agents.subagents.analyzer_agent import AnalyzerAgent
from agents.base_agent import BaseAgent
from agents.config import Config
from mcp_servers.llm_server import LLMMCPServer
from mcp_servers.storage_server import StorageMCPServer
from models.business_models import TagSystemGeneration
import logging

logging.basicConfig(level=logging.DEBUG)

async def test_comment_tagging():
    """测试单条评论的tag分析"""

    # 初始化MCP服务器
    config = Config()
    llm_server = LLMMCPServer(config)
    storage_server = StorageMCPServer(config)

    await llm_server.start()
    await storage_server.start()

    mcp_clients = {
        "llm": llm_server,
        "storage": storage_server
    }

    # 创建Agent
    agent = AnalyzerAgent("test_analyzer", mcp_clients)

    # 测试单条评论
    test_comment = {
        "comment_id": "test123",
        "user_nickname": "测试用户",
        "content": "请问最终你在哪里买？"
    }

    # 简化的标签体系
    test_tag_system = {
        "人群场景": {
            "用户需求与痛点-痛点问题": ["价格透明", "购买渠道"]
        },
        "功能价值": {
            "产品反馈-产品优点": ["性价比高"]
        }
    }

    print("=" * 80)
    print("测试评论tag分析")
    print("=" * 80)
    print(f"评论内容: {test_comment['content']}")
    print(f"标签体系: {test_tag_system}")
    print("=" * 80)

    # 构建分析提示
    tag_system_str = str(test_tag_system)
    comment_text = f"用户: {test_comment.get('user_nickname')}\n评论: {test_comment.get('content')}"

    tagging_prompt = f"""请基于评价标签体系进行标签分析，标签体系为： ### : {tag_system_str}, ### ,
要求：当评价满足标签则留下标签，当评价无关标签则去掉标签，当评价与标签相反则记下（-标签）作为标签， 格式返回原来的标签体系结构。
以下是评价内容：
##
   {comment_text}
 ##   """

    print("\n发送到LLM的Prompt:")
    print("-" * 80)
    print(tagging_prompt)
    print("-" * 80)

    try:
        # 调用LLM
        print("\n开始调用LLM...")
        result = await agent.use_llm(
            prompt=tagging_prompt,
            response_model=TagSystemGeneration
        )

        print("\nLLM返回成功!")
        print(f"返回类型: {type(result)}")
        print(f"返回内容: {result}")

        # 转换为字典
        if hasattr(result, 'model_dump'):
            result_dict = result.model_dump()
        else:
            result_dict = result

        print(f"\n解析后的字典: {result_dict}")

    except Exception as e:
        print(f"\nLLM调用失败!")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        import traceback
        print(f"\n完整堆栈:\n{''.join(traceback.format_tb(e.__traceback__))}")

    finally:
        await llm_server.stop()
        await storage_server.stop()

if __name__ == "__main__":
    asyncio.run(test_comment_tagging())
