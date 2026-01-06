import re
import json

# 测试LLM返回的格式
test_text = """根据您的要求，我们需要分析评论内容并判断其与标签体系的匹配情况。以下是对评论内容 "这是小程序叫什么名字" 的标签分析：

在给定的评价标签体系中，评论内容与任何标签都不匹配，因为评论内容只是询问小程序的名字，并未涉及任何关于产品或服务的具体评价。因此，所有标签都去掉，最后返回的标签体系结构如下：

```json
{
    "人群场景": {},
    "功能价值": {
        "产品反馈-产品优点": [],
        "产品反馈-产品缺点": [],
        "产品反馈-用户期望建议": []
    },
    "保障价值": {
        "服务评价-物流配送": [],
        "服务评价-售后服务": []
    },
    "体验价值": {
        "品牌形象与口碑-推荐意愿": [],
        "价格感知": []
    }
}
```

在这个分析中，没有任何标签适用于评论内容，因此所有标签列表都是空的。"""

# 使用正则表达式提取 JSON 代码块
json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
match = re.search(json_pattern, test_text)

if match:
    extracted_json = match.group(1).strip()
    print('✅ 成功提取JSON代码块')
    print(f'提取的JSON长度: {len(extracted_json)} 字符')
    print(f'JSON前100字符: {extracted_json[:100]}')
    
    # 尝试解析JSON
    try:
        data = json.loads(extracted_json)
        print('✅ JSON解析成功')
        print(f'JSON keys: {list(data.keys())}')
        print(f'完整JSON: {json.dumps(data, ensure_ascii=False, indent=2)}')
    except json.JSONDecodeError as e:
        print(f'❌ JSON解析失败: {e}')
else:
    print('❌ 未找到JSON代码块')
