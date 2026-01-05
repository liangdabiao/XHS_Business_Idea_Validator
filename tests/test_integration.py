"""
Agent 系统集成测试

测试 MCP 服务器和上下文存储的集成
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_xhs_mcp_server():
    """测试 XHS MCP 服务器"""
    print("\n" + "="*80)
    print("测试 1: XHS MCP Server")
    print("="*80)

    from mcp_servers.xhs_server import create_xhs_mcp_server
    # 如果导入失败，尝试另一种方式
    # import importlib
    # xhs_server = importlib.import_module('mcp_servers.xhs_server')

    # 创建服务器
    token = "vZdfXsQag0amkXaLT4kjaa6yL0gTnBk/aTAi8aA=="
    server = await create_xhs_mcp_server(token)

    try:
        # 测试搜索
        print("\n🔍 测试搜索笔记...")
        result = await server.call_tool(
            "search_notes",
            keyword="深圳陈皮",
            page=1,
            pages=1
        )

        if result.get("success"):
            print(f"✅ 搜索成功!")
            print(f"   关键词: {result['keyword']}")
            print(f"   笔记数: {result['total_count']}")
            print(f"   执行时间: {result['execution_time']:.2f}s")

            # 显示前2条
            notes = result.get('notes', [])
            if notes:
                print(f"\n   前 {min(2, len(notes))} 条笔记:")
                for i, note in enumerate(notes[:2], 1):
                    print(f"   [{i}] {note['title']}")
                    print(f"       作者: {note['user_nickname']}")
                    print(f"       互动: 👍{note['liked_count']} ⭐{note['collected_count']} 💬{note['comments_count']}")
        else:
            print(f"❌ 搜索失败: {result.get('error')}")
            return False

        # 测试获取评论
        if notes:
            first_note_id = notes[0]['note_id']
            print(f"\n💬 测试获取评论: {first_note_id}")

            await asyncio.sleep(1)  # 延迟避免限流

            comments_result = await server.call_tool(
                "get_note_comments",
                note_id=first_note_id,
                limit=10
            )

            if comments_result.get("success"):
                print(f"✅ 获取评论成功!")
                print(f"   评论数: {comments_result['total_count']}")
            else:
                print(f"⚠️  获取评论失败: {comments_result.get('error')}")

        print("\n✅ XHS MCP Server 测试通过!")
        return True

    except Exception as e:
        logger.exception("XHS MCP Server test failed")
        print(f"\n❌ 测试失败: {e}")
        return False

    finally:
        await server.stop()


async def test_storage_mcp_server():
    """测试 Storage MCP 服务器"""
    print("\n" + "="*80)
    print("测试 2: Storage MCP Server")
    print("="*80)

    from mcp_servers.storage_server import create_storage_mcp_server

    # 创建服务器
    server = await create_storage_mcp_server("agent_context/test")

    try:
        # 测试保存检查点
        test_data = {
            "test_key": "test_value",
            "timestamp": datetime.now().isoformat(),
            "nested": {
                "a": 1,
                "b": [2, 3, 4]
            }
        }

        print("\n💾 测试保存检查点...")
        save_result = await server.call_tool(
            "save_checkpoint",
            run_id="test_run_001",
            step="test_step",
            data=test_data
        )

        if save_result.get("success"):
            print(f"✅ 保存成功!")
            print(f"   路径: {save_result['path']}")
        else:
            print(f"❌ 保存失败: {save_result.get('error')}")
            return False

        # 测试加载检查点
        print("\n📂 测试加载检查点...")
        load_result = await server.call_tool(
            "load_checkpoint",
            run_id="test_run_001",
            step="test_step"
        )

        if load_result.get("success"):
            print(f"✅ 加载成功!")
            print(f"   数据: {load_result['data']}")
        else:
            print(f"❌ 加载失败: {load_result.get('error')}")
            return False

        # 测试列出检查点
        print("\n📋 测试列出检查点...")
        list_result = await server.call_tool(
            "list_checkpoints",
            run_id="test_run_001"
        )

        if list_result.get("success"):
            print(f"✅ 列出成功!")
            print(f"   检查点: {list_result['checkpoints']}")
        else:
            print(f"❌ 列出失败: {list_result.get('error')}")
            return False

        print("\n✅ Storage MCP Server 测试通过!")
        return True

    except Exception as e:
        logger.exception("Storage MCP Server test failed")
        print(f"\n❌ 测试失败: {e}")
        return False

    finally:
        await server.stop()


async def test_context_store():
    """测试上下文存储"""
    print("\n" + "="*80)
    print("测试 3: Context Store")
    print("="*80)

    from agents.context_store import ContextStore
    from models.agent_models import ProgressUpdate

    context_store = ContextStore()

    try:
        # 测试创建运行
        print("\n🔧 测试创建运行上下文...")
        run_id = context_store.create_run(
            business_idea="测试创意",
            user_preferences={"location": "深圳"}
        )

        print(f"✅ 运行上下文创建成功!")
        print(f"   Run ID: {run_id}")

        # 测试获取运行
        print("\n📖 测试获取运行上下文...")
        context = context_store.get_run(run_id)

        if context:
            print(f"✅ 获取成功!")
            print(f"   业务创意: {context.business_idea}")
            print(f"   状态: {context.status}")
        else:
            print(f"❌ 获取失败")
            return False

        # 测试设置进度
        print("\n📊 测试设置进度...")
        progress = ProgressUpdate(
            agent_name="test_agent",
            step="test_step",
            progress=0.5,
            message="测试进度"
        )

        context_store.set_progress(run_id, progress)
        print(f"✅ 进度设置成功!")

        # 测试获取进度
        print("\n📈 测试获取进度...")
        progress_history = context_store.get_progress(run_id)

        if progress_history:
            print(f"✅ 获取成功!")
            print(f"   进度数: {len(progress_history)}")
            print(f"   最新进度: {progress_history[-1].message}")
        else:
            print(f"❌ 获取失败")
            return False

        # 测试列出运行
        print("\n📋 测试列出运行...")
        runs = context_store.list_runs(limit=5)

        print(f"✅ 列出成功!")
        print(f"   运行数: {len(runs)}")

        print("\n✅ Context Store 测试通过!")
        return True

    except Exception as e:
        logger.exception("Context Store test failed")
        print(f"\n❌ 测试失败: {e}")
        return False


async def test_config_manager():
    """测试配置管理器"""
    print("\n" + "="*80)
    print("测试 4: Config Manager")
    print("="*80)

    from agents.config import ConfigManager

    try:
        # 测试加载配置
        print("\n⚙️  测试加载配置...")
        config = ConfigManager()

        print(f"✅ 配置加载成功!")
        print(f"   配置节数: {len(config._config)}")

        # 测试获取 XHS 配置
        print("\n🔷 测试获取 XHS MCP 配置...")
        xhs_config = config.get_xhs_mcp_config()
        print(f"✅ XHS 配置获取成功!")
        print(f"   Base URL: {xhs_config.base_url}")
        print(f"   Request Delay: {xhs_config.request_delay}s")

        # 测试获取 LLM 配置
        print("\n🤖 测试获取 LLM 配置...")
        llm_config = config.get_llm_config()
        print(f"✅ LLM 配置获取成功!")
        print(f"   Provider: {llm_config.provider}")
        print(f"   Model: {llm_config.model_name}")

        print("\n✅ Config Manager 测试通过!")
        return True

    except Exception as e:
        logger.exception("Config Manager test failed")
        print(f"\n❌ 测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("="*80)
    print("Agent 系统集成测试")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    results = {}

    # 测试1: XHS MCP Server
    results['xhs_mcp'] = await test_xhs_mcp_server()

    # 测试2: Storage MCP Server
    results['storage_mcp'] = await test_storage_mcp_server()

    # 测试3: Context Store
    results['context_store'] = await test_context_store()

    # 测试4: Config Manager
    results['config'] = await test_config_manager()

    # 汇总
    print("\n" + "="*80)
    print("📊 测试汇总")
    print("="*80)

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")

    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
