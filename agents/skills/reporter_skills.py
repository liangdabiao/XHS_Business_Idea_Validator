"""
报告生成 Skills

提供业务验证报告生成的业务技能
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from models.business_models import CombinedAnalysis, ValidationResult
from agents.base_agent import BaseAgent


logger = logging.getLogger(__name__)


async def generate_text_report_skill(
    agent: BaseAgent,
    analysis: Dict[str, Any],
    business_idea: str,
    run_id: str
) -> Dict[str, Any]:
    """
    生成文本格式报告

    Args:
        agent: Agent 实例
        analysis: 综合分析结果
        business_idea: 业务创意
        run_id: 运行 ID

    Returns:
        文本报告
    """
    logger.info("Generating text report")

    # 提取分析数据
    combined_analysis = analysis.get("analysis", {})
    overall_score = combined_analysis.get("overall_score", 0)
    summary = combined_analysis.get("market_validation_summary", "")
    key_pain_points = combined_analysis.get("key_pain_points", [])
    existing_solutions = combined_analysis.get("existing_solutions", [])
    market_opportunities = combined_analysis.get("market_opportunities", [])
    recommendations = combined_analysis.get("recommendations", [])
    metadata = combined_analysis.get("metadata", {})

    # 构建文本报告
    report_lines = [
        "=" * 80,
        "业务创意市场验证报告",
        "=" * 80,
        "",
        f"业务创意: {business_idea}",
        f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"运行 ID: {run_id}",
        "",
        "=" * 80,
        "综合评分",
        "=" * 80,
        "",
        f"评分: {overall_score}/100",
        "",
        get_score_interpretation(overall_score),
        "",
        "=" * 80,
        "市场验证摘要",
        "=" * 80,
        "",
        summary,
        "",
        "=" * 80,
        "关键痛点",
        "=" * 80,
        "",
    ]

    if key_pain_points:
        for i, point in enumerate(key_pain_points, 1):
            report_lines.append(f"{i}. {point}")
    else:
        report_lines.append("未发现明确痛点")

    report_lines.extend([
        "",
        "=" * 80,
        "现有解决方案",
        "=" * 80,
        "",
    ])

    if existing_solutions:
        for i, solution in enumerate(existing_solutions, 1):
            report_lines.append(f"{i}. {solution}")
    else:
        report_lines.append("未发现明确的现有解决方案")

    report_lines.extend([
        "",
        "=" * 80,
        "市场机会",
        "=" * 80,
        "",
    ])

    if market_opportunities:
        for i, opportunity in enumerate(market_opportunities, 1):
            report_lines.append(f"{i}. {opportunity}")
    else:
        report_lines.append("未发现明确的市场机会")

    report_lines.extend([
        "",
        "=" * 80,
        "建议",
        "=" * 80,
        "",
    ])

    if recommendations:
        for i, recommendation in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {recommendation}")
    else:
        report_lines.append("暂无建议")

    report_lines.extend([
        "",
        "=" * 80,
        "元数据",
        "=" * 80,
        "",
    ])

    for key, value in metadata.items():
        report_lines.append(f"{key}: {value}")

    report_lines.extend([
        "",
        "=" * 80,
        f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 80,
    ])

    report = "\n".join(report_lines)

    logger.info(f"Text report generated: {len(report)} characters")

    return {
        "success": True,
        "report_format": "text",
        "content": report,
        "length": len(report)
    }


async def generate_html_report_skill(
    agent: BaseAgent,
    analysis: Dict[str, Any],
    business_idea: str,
    run_id: str,
    posts_data: Optional[Dict[str, Any]] = None,
    comments_data: Optional[Dict[str, Any]] = None,
    tag_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    生成 HTML 格式报告（增强版，展示全部分析数据）

    Args:
        agent: Agent 实例
        analysis: 综合分析结果（包含增强的 metadata）
        business_idea: 业务创意
        run_id: 运行 ID
        posts_data: 笔记数据（已废弃，保留兼容性）
        comments_data: 评论数据（已废弃，保留兼容性）
        tag_analysis: 评论标签分析结果（新增）

    Returns:
        HTML 报告
    """
    logger.info("Generating HTML report with enhanced data")

    # 提取分析数据
    combined_analysis = analysis.get("analysis", {})
    overall_score = combined_analysis.get("overall_score", 0)
    summary = combined_analysis.get("market_validation_summary", "")
    key_pain_points = combined_analysis.get("key_pain_points", [])
    existing_solutions = combined_analysis.get("existing_solutions", [])
    market_opportunities = combined_analysis.get("market_opportunities", [])
    recommendations = combined_analysis.get("recommendations", [])
    metadata = combined_analysis.get("metadata", {})

    # 新增：提取增强的 metadata 数据
    relevant_posts = metadata.get("relevant_posts", 0)
    avg_engagement_score = metadata.get("avg_engagement_score", 0)
    avg_sentiment = metadata.get("avg_sentiment", 0)
    sentiment_distribution = metadata.get("sentiment_distribution", {})
    total_comments_analyzed = metadata.get("total_comments_analyzed", 0)
    recent_posts_30days = metadata.get("recent_posts_30days", 0)
    total_posts = metadata.get("total_posts_analyzed", 0)

    # 新增：提取标签分析数据
    tag_data = None
    persona_data = None
    if tag_analysis:
        tag_data = tag_analysis.get("tag_analysis", {})
        persona_data = tag_analysis.get("tag_analysis", {}).get("persona_analysis")

    # 评分颜色
    score_color = get_score_color(overall_score)

    # 情感倾向描述
    sentiment_label = "积极" if avg_sentiment > 0.2 else "中性" if avg_sentiment > -0.2 else "消极"
    sentiment_color = "#28a745" if avg_sentiment > 0.2 else "#6c757d" if avg_sentiment > -0.2 else "#dc3545"

    # 构建 HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>业务创意市场验证报告 - {business_idea}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #ff2442;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-left: 4px solid #ff2442;
            padding-left: 10px;
        }}
        .score-box {{
            background: linear-gradient(135deg, {score_color} 0%, #ff9a9e 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
        }}
        .score {{
            font-size: 48px;
            font-weight: bold;
        }}
        .score-interpretation {{
            font-size: 18px;
            margin-top: 10px;
        }}
        .summary {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            line-height: 1.8;
        }}
        .list-item {{
            padding: 10px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .sentiment-bar {{
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .sentiment-positive {{
            height: 100%;
            background: #28a745;
            display: inline-block;
        }}
        .sentiment-neutral {{
            height: 100%;
            background: #6c757d;
            display: inline-block;
        }}
        .sentiment-negative {{
            height: 100%;
            background: #dc3545;
            display: inline-block;
        }}
        .metadata {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 8px;
            font-size: 14px;
            color: #666;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #999;
            font-size: 14px;
        }}
        .word-frequency-section {{
            margin: 20px 0;
        }}
        .word-frequency-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin: 15px 0;
        }}
        .word-frequency-category {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid #ff2442;
        }}
        .word-frequency-category h3 {{
            font-size: 16px;
            color: #333;
            margin-top: 0;
            margin-bottom: 12px;
        }}
        .tag-item {{
            background: white;
            padding: 8px 12px;
            margin: 6px 0;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
        }}
        .tag-name {{
            font-weight: 500;
            color: #333;
            flex: 1;
        }}
        .tag-meta {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 12px;
        }}
        .tag-count {{
            background: #ff2442;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: bold;
        }}
        .tag-sentiment {{
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 500;
        }}
        .sentiment-positive {{
            background: #d4edda;
            color: #155724;
        }}
        .sentiment-negative {{
            background: #f8d7da;
            color: #721c24;
        }}
        .sentiment-neutral {{
            background: #e2e3e5;
            color: #383d41;
        }}
        .sentiment-mixed {{
            background: #fff3cd;
            color: #856404;
        }}
        .tag-keywords {{
            font-size: 11px;
            color: #666;
            margin-top: 4px;
        }}
        .persona-section {{
            margin: 20px 0;
        }}
        .persona-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 15px 0;
        }}
        .persona-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #ff2442;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .persona-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .persona-name {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }}
        .persona-emotion {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }}
        .emotion-positive {{
            background: #d4edda;
            color: #155724;
        }}
        .emotion-neutral {{
            background: #e2e3e5;
            color: #383d41;
        }}
        .emotion-negative {{
            background: #f8d7da;
            color: #721c24;
        }}
        .persona-section-title {{
            font-size: 13px;
            font-weight: 600;
            color: #666;
            margin-top: 12px;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .persona-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .persona-tag {{
            background: #f8f9fa;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 13px;
            color: #495057;
        }}
        .persona-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .persona-list li {{
            padding: 4px 0;
            font-size: 14px;
            color: #495057;
            position: relative;
            padding-left: 16px;
        }}
        .persona-list li:before {{
            content: "•";
            position: absolute;
            left: 0;
            color: #ff2442;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>业务创意市场验证报告</h1>

        <div class="metadata">
            <strong>业务创意:</strong> {business_idea}<br>
            <strong>验证时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>运行 ID:</strong> {run_id}
        </div>

        <h2>综合评分</h2>
        <div class="score-box">
            <div class="score">{overall_score}</div>
            <div class="score-interpretation">{get_score_interpretation(overall_score)}</div>
        </div>

        <h2>数据统计</h2>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-label">分析帖子数</div>
                <div class="stat-value">{total_posts}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">相关帖子</div>
                <div class="stat-value">{relevant_posts}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">平均互动评分</div>
                <div class="stat-value">{avg_engagement_score:.1f}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">分析评论数</div>
                <div class="stat-value">{total_comments_analyzed}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">最近30天活跃</div>
                <div class="stat-value">{recent_posts_30days}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">情感倾向</div>
                <div class="stat-value" style="color: {sentiment_color}">{sentiment_label}</div>
            </div>
        </div>

        <h2>情感分布</h2>
        <div class="summary">
            <div style="margin-bottom: 10px;">
                积极: {sentiment_distribution.get('positive', 0)} |
                中性: {sentiment_distribution.get('neutral', 0)} |
                消极: {sentiment_distribution.get('negative', 0)}
            </div>
            <div class="sentiment-bar">
                {" ".join([
                    f'<span class="sentiment-positive" style="width: {sentiment_distribution.get("positive", 0) / (sentiment_distribution.get("positive", 0) + sentiment_distribution.get("neutral", 0) + sentiment_distribution.get("negative", 0) + 1) * 100}%"></span>' if sentiment_distribution.get('positive', 0) > 0 else '',
                    f'<span class="sentiment-neutral" style="width: {sentiment_distribution.get("neutral", 0) / (sentiment_distribution.get("positive", 0) + sentiment_distribution.get("neutral", 0) + sentiment_distribution.get("negative", 0) + 1) * 100}%"></span>' if sentiment_distribution.get('neutral', 0) > 0 else '',
                    f'<span class="sentiment-negative" style="width: {sentiment_distribution.get("negative", 0) / (sentiment_distribution.get("positive", 0) + sentiment_distribution.get("neutral", 0) + sentiment_distribution.get("negative", 0) + 1) * 100}%"></span>' if sentiment_distribution.get('negative', 0) > 0 else ''
                ])}
            </div>
        </div>

        <h2>市场验证摘要</h2>
        <div class="summary">
            {summary}
        </div>

        <h2>关键痛点</h2>
        """

    if key_pain_points:
        for point in key_pain_points:
            html += f'        <div class="list-item">{point}</div>\n'
    else:
        html += '        <div class="list-item">未发现明确痛点</div>\n'

    html += f"""
        <h2>现有解决方案</h2>
        """

    if existing_solutions:
        for solution in existing_solutions:
            html += f'        <div class="list-item">{solution}</div>\n'
    else:
        html += '        <div class="list-item">未发现明确的现有解决方案</div>\n'

    html += f"""
        <h2>市场机会</h2>
        """

    if market_opportunities:
        for opportunity in market_opportunities:
            html += f'        <div class="list-item">{opportunity}</div>\n'
    else:
        html += '        <div class="list-item">未发现明确的市场机会</div>\n'

    html += f"""
        <h2>建议</h2>
        """

    if recommendations:
        for recommendation in recommendations:
            html += f'        <div class="list-item">{recommendation}</div>\n'
    else:
        html += '        <div class="list-item">暂无建议</div>\n'

    # 新增：评论标签分析部分
    if tag_data and tag_data.get("total_posts_analyzed", 0) > 0:
        html += f"""
        <h2>评论标签体系分析</h2>
        <div class="summary">
            <p><strong>分析帖子数:</strong> {tag_data.get('total_posts_analyzed', 0)} 个</p>
            <p><strong>应用标签数:</strong> {tag_data.get('total_tags_applied', 0)} 个</p>
            <p>{tag_data.get('analysis_summary', '')}</p>
        </div>
        """

        # 按二级分类展示标签统计（参考代码的方式）
        tag_statistics = tag_data.get("tag_statistics", {})
        
        if tag_statistics:
            html += '        <div class="word-frequency-grid">\n'
            
            for subcategory, tag_counts in tag_statistics.items():
                if not tag_counts:
                    continue
                
                # 按出现次数排序
                sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
                
                html_parts = []
                html_parts.append(f"""
        <div class="word-frequency-category">
            <h3>{subcategory}</h3>
            <div style="margin-bottom: 15px;">
                <div style="font-weight: 600; color: #555; margin-bottom: 8px; font-size: 14px;">标签统计（按出现次数排序）</div>
        """)

                for tag, count in sorted_tags[:10]:  # 限制显示前10个标签
                    # 判断标签情感（负面标签以"-"开头）
                    is_negative = tag.startswith("-")
                    display_tag = tag[1:] if is_negative else tag
                    sentiment_class = "sentiment-negative" if is_negative else "sentiment-positive"
                    sentiment_label = "负" if is_negative else "正"

                    html_parts.append(f"""
                <div class="tag-item">
                    <div class="tag-name">{display_tag}</div>
                    <div class="tag-meta">
                        <span class="tag-count">{count}</span>
                        <span class="tag-sentiment {sentiment_class}">{sentiment_label}</span>
                    </div>
                </div>""")

                html_parts.append('            </div>\n        </div>')
                html += "".join(html_parts)
            
            html += '        </div>\n'

    # 新增：用户画像分析部分
    if persona_data and persona_data.get("personas"):
        html += f"""
        <h2>用户画像分析</h2>
        <div class="summary">
            <p><strong>生成画像数:</strong> {persona_data.get('total_personas', 0)} 个典型用户</p>
            <p>{persona_data.get('analysis_summary', '')}</p>
        </div>
        <div class="persona-grid">
        """

        for idx, persona in enumerate(persona_data.get("personas", []), 1):
            # 提取画像数据
            gender = persona.get("gender", "未知")
            age = persona.get("age_estimate", "未知")
            emotion = persona.get("emotional_tone", "neutral")
            demand_keywords = persona.get("demand_keywords", [])
            purchase_motivations = persona.get("purchase_motivation", [])
            persona_tags = persona.get("persona_tags", [])

            # 情感标签样式 - 改进判断逻辑
            emotion_lower = emotion.lower() if emotion else ""
            
            if "积极" in emotion or "positive" in emotion_lower:
                emotion_class = "emotion-positive"
                emotion_label = "积极"
            elif "消极" in emotion or "negative" in emotion_lower or "焦虑" in emotion or "担心" in emotion:
                emotion_class = "emotion-negative"
                emotion_label = "消极"
            else:
                emotion_class = "emotion-neutral"
                emotion_label = "中性"

            html += f"""
            <div class="persona-card">
                <div class="persona-header">
                    <div class="persona-name">用户画像 {idx}: {gender} · {age}</div>
                    <span class="persona-emotion {emotion_class}">{emotion_label}</span>
                </div>

                <div class="persona-section-title">需求关键词</div>
                <div class="persona-tags">
            """

            for keyword in demand_keywords[:5]:
                html += f'<span class="persona-tag">{keyword}</span>\n                    '

            html += """
                </div>

                <div class="persona-section-title">购买动机</div>
                <ul class="persona-list">
            """

            for motivation in purchase_motivations[:4]:
                html += f'                    <li>{motivation}</li>\n'

            html += """
                </ul>

                <div class="persona-section-title">用户标签</div>
                <div class="persona-tags">
            """

            for tag in persona_tags[:5]:
                html += f'<span class="persona-tag">{tag}</span>\n                    '

            html += """
                </div>
            </div>
            """

        html += '        </div>\n'

    html += f"""
        <h2>元数据</h2>
        <div class="metadata">
        """

    for key, value in metadata.items():
        html += f'            <strong>{key}:</strong> {value}<br>\n'

    html += f"""        </div>

        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>由 Business Idea Validator Agent System 自动生成</p>
            <p style="margin-top: 10px; font-size: 14px; color: #888; font-style: italic;">小提示: 相关资料请到 agent_context/checkpoints/{run_id}/ 目录下查看</p>
        </div>
    </div>
</body>
</html>
"""

    logger.info(f"HTML report generated: {len(html)} characters")

    return {
        "success": True,
        "report_format": "html",
        "content": html,
        "length": len(html)
    }


async def save_report_skill(
    agent: BaseAgent,
    report_content: str,
    report_format: str,
    output_path: str
) -> Dict[str, Any]:
    """
    保存报告到文件

    Args:
        agent: Agent 实例
        report_content: 报告内容
        report_format: 报告格式 (text/html)
        output_path: 输出路径

    Returns:
        保存结果
    """
    logger.info(f"Saving report to: {output_path}")

    try:
        # 创建输出目录
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        file_size = output_file.stat().st_size

        logger.info(f"Report saved: {output_path} ({file_size} bytes)")

        return {
            "success": True,
            "path": str(output_file.absolute()),
            "format": report_format,
            "size": file_size
        }

    except Exception as e:
        logger.error(f"Save report failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# 辅助函数
# ============================================================================

def get_score_interpretation(score: int) -> str:
    """获取评分解释"""
    if score >= 80:
        return "市场需求强烈，建议尽快启动"
    elif score >= 60:
        return "市场机会存在，需要进一步验证"
    elif score >= 40:
        return "市场反应平平，建议调整策略"
    else:
        return "市场需求不足，建议重新评估"


def get_score_color(score: int) -> str:
    """获取评分颜色"""
    if score >= 80:
        return "#28a745"  # 绿色
    elif score >= 60:
        return "#ffc107"  # 黄色
    elif score >= 40:
        return "#fd7e14"  # 橙色
    else:
        return "#dc3545"  # 红色
