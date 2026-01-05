"""
直接测试标签体系生成功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.business_models import TagSystemGeneration
from mcp_servers.llm_server import create_llm_mcp_server
from agents.config import ConfigManager


async def test_tag_system_generation():
    """测试标签体系生成"""
    print("=" * 60)
    print("测试标签体系生成功能")
    print("=" * 60)

    # 初始化配置
    config = ConfigManager()

    # 创建 LLM MCP 服务器
    print("\n[1/2] 创建 LLM 服务器...")
    llm_server = await create_llm_mcp_server(config)
    print("✓ LLM 服务器创建成功")

    # 测试生成标签体系
    print("\n[2/2] 测试标签体系生成...")

    test_prompt = """
请为以下产品构建一个三级标签体系。

产品：陈皮

用户评论样例：
1. "这个陈皮品质很好，适合泡茶"
2. "价格有点贵，但是效果不错"
3. "包装很精美，送朋友很有面子"
4. "物流很快，第二天就到了"

请按照以下四个维度构建标签体系：
- 人群场景
- 功能价值
- 保障价值
- 体验价值

返回 JSON 格式的标签体系。
"""

    try:
        print("\n调用 LLM 生成标签体系...")

        # 使用 LLM MCP 服务器
        result = await llm_server.call_tool(
            "generate_structured",
            prompt=test_prompt,
            schema=TagSystemGeneration.model_json_schema()
        )

        if result.get('success'):
            tag_system = result.get('data')
            print("\n✓ 标签体系生成成功！")
            print("\n生成的标签体系：")
            print("-" * 60)

            for category, subcategories in tag_system.items():
                print(f"\n【{category}】")
                for subcategory, tags in subcategories.items():
                    print(f"  └─ {subcategory}")
                    for tag in tags:
                        print(f"      • {tag}")

            print("\n" + "=" * 60)
            print("✓ 测试通过！TagSystemGeneration 模型工作正常")
            print("=" * 60)
            return True
        else:
            print(f"\n✗ 生成失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理资源
        print("\n清理资源...")
        await llm_server.stop()
        print("✓ 清理完成")


if __name__ == "__main__":
    success = asyncio.run(test_tag_system_generation())
    sys.exit(0 if success else 1)
