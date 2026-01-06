"""
快速测试修复后的评论tag分析

使用固定的数据测试，不需要完整的agent系统
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test():
    # 直接导入需要的函数
    from agents.skills.analyzer_skills import _extract_json_from_response
    from models.business_models import TagSystemGeneration
    import json

    # 测试数据
    tag_system_str = """{'人群场景': {'用户需求与痛点-痛点问题': ['价格透明', '购买渠道'], '用户需求与痛点-购买动机': ['社交媒体影响', '价格因素']}, '功能价值': {'产品反馈-产品优点': ['效果好', '性价比高']}}"""

    test_comment = {
        "comment_id": "test001",
        "user_nickname": "测试用户",
        "content": "请问最终你在哪里买？"
    }

    # 新的prompt格式
    tagging_prompt = f"""你是一个评论分析专家。请根据给定的标签体系，对用户的评论进行标签匹配分析。

## 标签体系

{tag_system_str}

## 分析规则

1. **匹配标签**：如果评论内容符合某个标签，保留该标签
2. **移除标签**：如果评论内容与某个标签无关，移除该标签
3. **反向标签**：如果评论内容表达了对某个标签的相反观点，使用负号标记（例如："-价格合理"）

## 待分析评论

用户: {test_comment.get('user_nickname', 'Anonymous')}
评论: {test_comment.get('content', '')}

## 输出要求

请直接返回JSON格式的分析结果，保持与标签体系相同的结构。只保留匹配到的标签。

返回格式示例：
```json
{{
  "人群场景": {{
    "用户需求与痛点-痛点问题": ["价格透明", "购买渠道"]
  }},
  "功能价值": {{}}
}}
```

注意：
- 只返回有标签的分类
- 空分类用 {{}}
- 直接返回JSON，不要包含其他解释文字
"""

    print("=" * 80)
    print("测试评论Tag分析的Prompt格式")
    print("=" * 80)
    print("\nPrompt内容:")
    print("-" * 80)
    print(tagging_prompt)
    print("-" * 80)

    # 测试JSON提取
    print("\n测试JSON提取功能:")
    test_response = '''```json
{
  "人群场景": {
    "用户需求与痛点-痛点问题": ["购买渠道"]
  },
  "功能价值": {}
}
```'''
    print(f"测试响应: {test_response}")
    extracted = _extract_json_from_response(test_response)
    print(f"提取结果: {extracted}")
    print(f"提取成功: {isinstance(extracted, dict) and len(extracted) > 0}")

    print("\n" + "=" * 80)
    print("Prompt格式测试完成！")
    print("建议: 运行完整的agent测试来验证LLM响应")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test())
