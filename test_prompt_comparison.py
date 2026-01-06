"""
测试三种不同prompt格式的效果
"""
import sys
sys.path.insert(0, 'D:\\agent_system')

def test_prompt_formats():
    """对比三种prompt格式"""

    # 测试数据
    tag_system_str = """{'人群场景': {'用户需求与痛点-痛点问题': ['价格透明', '购买渠道']}, '功能价值': {'产品反馈-产品优点': ['效果好']}}"""
    comment = {
        "user_nickname": "测试用户",
        "content": "请问最终你在哪里买？"
    }

    print("=" * 80)
    print("三种Prompt格式对比")
    print("=" * 80)

    # 版本1：参考代码格式
    prompt_v1 = f"""请基于评价标签体系进行标签分析，标签体系为： ### : {tag_system_str}, ### ,
要求：当评价满足标签则留下标签，当评价无关标签则去掉标签，当评价与标签相反则记下（-标签）作为标签， 格式返回原来的标签体系结构。
以下是评价内容：
##
用户: {comment['user_nickname']}
评论: {comment['content']}
 ##   """

    # 版本2：我之前的结构化格式
    prompt_v2 = f"""你是一个评论分析专家。请根据给定的标签体系，对用户的评论进行标签匹配分析。

## 标签体系

{tag_system_str}

## 分析规则

1. **匹配标签**：如果评论内容符合某个标签，保留该标签
2. **移除标签**：如果评论内容与某个标签无关，移除该标签
3. **反向标签**：如果评论内容表达了对某个标签的相反观点，使用负号标记（例如："-价格合理"）

## 待分析评论

用户: {comment['user_nickname']}
评论: {comment['content']}

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

    # 版本3：混合优化格式
    prompt_v3 = f"""请基于评价标签体系对评论进行标签匹配分析。

## 标签体系
{tag_system_str}

## 分析规则
- 满足标签：保留该标签
- 无关标签：移除该标签
- 相反标签：记为 -标签（例如：-价格合理）

## 评论内容
用户：{comment['user_nickname']}
评论：{comment['content']}

## 输出格式
直接返回JSON格式的标签体系结构，只保留匹配到的标签。空分类用{{}}。

示例：
```json
{{"人群场景": {{"用户需求与痛点-痛点问题": ["购买渠道"]}}, "功能价值": {{}}}}
```

重要：直接返回JSON，不要包含任何解释文字。
"""

    print("\n" + "=" * 80)
    print("版本1：参考代码格式（简洁版）")
    print("-" * 80)
    print(f"Token数: {len(prompt_v1)} 字符")
    print(f"内容:\n{prompt_v1}")

    print("\n" + "=" * 80)
    print("版本2：结构化格式（详细版）")
    print("-" * 80)
    print(f"Token数: {len(prompt_v2)} 字符")
    print(f"内容:\n{prompt_v2}")

    print("\n" + "=" * 80)
    print("版本3：混合优化格式（推荐）")
    print("-" * 80)
    print(f"Token数: {len(prompt_v3)} 字符")
    print(f"内容:\n{prompt_v3}")

    print("\n" + "=" * 80)
    print("对比总结")
    print("=" * 80)
    print(f"版本1（参考代码）: {len(prompt_v1)} 字符 - 最简洁，token消耗最少")
    print(f"版本2（结构化）:   {len(prompt_v2)} 字符 - 最详细，但token消耗多")
    print(f"版本3（混合优化）: {len(prompt_v3)} 字符 - 平衡点，清晰且简洁")
    print(f"\n版本3相比版本1增加: {len(prompt_v3) - len(prompt_v1)} 字符 ({(len(prompt_v3) - len(prompt_v1))/len(prompt_v1)*100:.1f}%)")
    print(f"版本3相比版本2减少: {len(prompt_v2) - len(prompt_v3)} 字符 ({(len(prompt_v2) - len(prompt_v3))/len(prompt_v2)*100:.1f}%)")

    print("\n" + "=" * 80)
    print("推荐使用版本3，原因：")
    print("✓ 结构清晰，易于LLM理解")
    print("✓ 有明确的JSON格式示例")
    print("✓ 比版本2简洁30%+")
    print("✓ 指令明确，降低理解偏差")
    print("=" * 80)

    return prompt_v3

if __name__ == "__main__":
    test_prompt_formats()
