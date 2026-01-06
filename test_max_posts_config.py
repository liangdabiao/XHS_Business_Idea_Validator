"""
测试 ANALYZER_MAX_POSTS 配置是否生效
"""
import sys
import os
sys.path.insert(0, 'D:\\agent_system')

from agents.config import ConfigManager

def test_config():
    print("=" * 80)
    print("测试 ANALYZER_MAX_POSTS 配置加载")
    print("=" * 80)

    config = ConfigManager()

    # 检查环境变量
    print(f"\n环境变量 ANALYZER_MAX_POSTS = {os.environ.get('ANALYZER_MAX_POSTS', '未设置')}")

    # 检查配置加载
    max_posts = config.get('agents.scraper.max_posts_to_analyze', 20)
    print(f"配置中的 max_posts_to_analyze = {max_posts}")

    # 验证
    if max_posts == 2:
        print(f"\n✅ 配置正确！ANALYZER_MAX_POSTS=2 已生效")
        print(f"   将只分析前 2 条帖子")
    else:
        print(f"\n❌ 配置错误！期望值=2, 实际值={max_posts}")
        print(f"   检查 .env 文件中的 ANALYZER_MAX_POSTS 配置")

    print("=" * 80)
    return max_posts == 2

if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)
