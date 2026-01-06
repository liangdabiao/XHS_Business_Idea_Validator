"""
测试脚本：验证comments_tag_analysis数据
使用checkpoint数据重新生成tag分析
"""
import asyncio
import json
from pathlib import Path
from agents.orchestrator import OrchestratorAgent
from agents.context_store import ContextStore
from agents.config import ConfigManager
from mcp_servers.xhs_server import XHSMCPServer
from mcp_servers.llm_server import LLMMCPServer
from mcp_servers.storage_server import StorageMCPServer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """主测试函数"""
    # 加载checkpoint数据
    checkpoint_path = Path("agent_context/checkpoints/在贵州卖新会陈皮_20260106_115308_fe5dbc45/analysis_complete.json")

    if not checkpoint_path.exists():
        logger.error(f"Checkpoint文件不存在: {checkpoint_path}")
        return

    with open(checkpoint_path, 'r', encoding='utf-8') as f:
        checkpoint_data = json.load(f)

    logger.info(f"✓ 成功加载checkpoint: {checkpoint_path}")
    logger.info(f"  - 包含的key: {list(checkpoint_data.keys())}")

    # 提取posts_with_comments
    posts_with_comments = checkpoint_data.get("posts_with_comments_analyses", [])
    business_idea = "在贵州卖新会陈皮"

    logger.info(f"\n✓ 提取数据:")
    logger.info(f"  - 帖子数量: {len(posts_with_comments)}")
    logger.info(f"  - 业务创意: {business_idea}")

    # 统计评论数量
    total_comments = 0
    comments_with_analysis = 0
    for post in posts_with_comments:
        comments = post.get('comments_data', [])
        total_comments += len(comments)
        analysis = post.get('analysis', {})
        if analysis.get('relevant'):
            comments_with_analysis += len(comments)

    logger.info(f"  - 总评论数: {total_comments}")
    logger.info(f"  - 相关帖子的评论数: {comments_with_analysis}")

    # 初始化系统
    config_manager = ConfigManager()
    context_store = ContextStore()

    # 启动MCP服务器
    xhs_server = XHSMCPServer(config_manager)
    llm_server = LLMMCPServer(config_manager)
    storage_server = StorageMCPServer(config_manager)

    await xhs_server.start()
    await llm_server.start()
    await storage_server.start()

    mcp_clients = {
        "xhs": xhs_server,
        "llm": llm_server,
        "storage": storage_server
    }

    # 创建AnalyzerAgent
    from agents.subagents.analyzer_agent import AnalyzerAgent
    analyzer = AnalyzerAgent(config_manager, context_store, mcp_clients)
    await analyzer.start()

    logger.info("\n" + "="*80)
    logger.info("开始执行评论标签分析...")
    logger.info("="*80 + "\n")

    # 执行tag分析
    context = {
        "posts_with_comments": posts_with_comments,
        "business_idea": business_idea,
        "run_id": "test_tag_analysis"
    }

    try:
        result = await analyzer._analyze_comments_with_tags(context, {})

        logger.info("\n" + "="*80)
        logger.info("标签分析完成!")
        logger.info("="*80)

        if result.get("success"):
            tag_analysis = result.get("tag_analysis", {})
            logger.info(f"\n✓ 标签分析成功:")
            logger.info(f"  - 分析评论数: {tag_analysis.get('total_comments_analyzed', 0)}")
            logger.info(f"  - 应用标签数: {tag_analysis.get('total_tags_applied', 0)}")
            logger.info(f"  - 摘要: {tag_analysis.get('analysis_summary', 'N/A')}")

            # 显示标签分类统计
            logger.info(f"\n标签分类统计:")
            for category, subcategories in tag_analysis.items():
                if isinstance(subcategories, dict) and subcategories:
                    logger.info(f"  - {category}: {len(subcategories)} 个二级分类")
                    for subcat, tags in subcategories.items():
                        if isinstance(tags, list):
                            logger.info(f"    - {subcat}: {len(tags)} 个标签")

            # 保存结果
            output_path = Path("test_comments_tag_analysis.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"\n✓ 结果已保存到: {output_path}")

            # 验证数据完整性
            logger.info(f"\n✓ 数据完整性检查:")
            logger.info(f"  - success: {result.get('success')}")
            logger.info(f"  - tag_analysis存在: {'tag_analysis' in result}")
            logger.info(f"  - analyzed_results数量: {len(result.get('analyzed_results', []))}")

            if result.get('analyzed_results'):
                sample_result = result['analyzed_results'][0]
                logger.info(f"  - 示例评论结构: {list(sample_result.keys())}")
                logger.info(f"  - 示例评论tags字段存在: {'tags' in sample_result}")
                if 'tags' in sample_result:
                    tags = sample_result['tags']
                    logger.info(f"  - 示例tags类型: {type(tags)}")
                    logger.info(f"  - 示例tags内容: {str(tags)[:200]}...")

        else:
            logger.error(f"\n✗ 标签分析失败: {result.get('error', 'Unknown')}")
            if 'error_type' in result:
                logger.error(f"  错误类型: {result['error_type']}")

    except Exception as e:
        logger.error(f"\n✗ 执行失败: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())

    finally:
        # 清理
        await analyzer.stop()
        await xhs_server.stop()
        await llm_server.stop()
        await storage_server.stop()

    logger.info("\n测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
