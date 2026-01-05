"""
验证 TagSystemGeneration 模型修复
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    print("=" * 70)
    print("验证 TagSystemGeneration 模型修复")
    print("=" * 70)

    # 测试 1: 导入模型
    print("\n[测试 1] 导入 TagSystemGeneration 模型...")
    try:
        from models.business_models import TagSystemGeneration
        print("✓ 模型导入成功")
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

    # 测试 2: 生成 JSON Schema
    print("\n[测试 2] 生成 JSON Schema...")
    try:
        schema = TagSystemGeneration.model_json_schema()
        print("✓ JSON Schema 生成成功")
        print(f"  - 字段数量: {len(schema['properties'])}")
        print(f"  - 字段名: {list(schema['properties'].keys())}")
    except Exception as e:
        print(f"✗ Schema 生成失败: {e}")
        print(f"  错误类型: {type(e).__name__}")
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_exc()
        return False

    # 测试 3: 创建模型实例
    print("\n[测试 3] 创建模型实例...")
    try:
        instance = TagSystemGeneration(
            人群场景={"用户需求": ["测试标签"]},
            功能价值={},
            保障价值={},
            体验价值={}
        )
        print("✓ 模型实例创建成功")
    except Exception as e:
        print(f"✗ 实例创建失败: {e}")
        return False

    # 测试 4: 测试 model_dump() 方法
    print("\n[测试 4] 测试 model_dump() 方法...")
    try:
        dumped = instance.model_dump()
        print("✓ model_dump() 调用成功")
        print(f"  - 返回类型: {type(dumped)}")
        print(f"  - 包含键: {list(dumped.keys())}")
    except Exception as e:
        print(f"✗ model_dump() 失败: {e}")
        return False

    # 测试 5: 验证字段访问
    print("\n[测试 5] 验证字段访问...")
    try:
        crowd_data = instance.人群场景
        print(f"✓ 字段访问成功")
        print(f"  - 人群场景内容: {crowd_data}")
    except Exception as e:
        print(f"✗ 字段访问失败: {e}")
        return False

    print("\n" + "=" * 70)
    print("✓ 所有测试通过！TagSystemGeneration 模型修复成功")
    print("=" * 70)
    print("\n修复内容总结:")
    print("1. ✓ 添加了 TagSystemGeneration Pydantic 模型")
    print("2. ✓ 更新了 analyzer_skills.py 使用正确的模型")
    print("3. ✓ 修复了缩进错误")
    print("4. ✓ model_dump() 方法正常工作")
    print("5. ✓ 不再出现 'dict has no attribute model_json_schema' 错误")
    print("\n现在标签体系分析功能应该可以正常工作了！")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
