"""
数据分析 Agent

负责分析小红书笔记和评论数据
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta

from agents.base_agent import BaseAgent, AgentStatus, TaskResult
from agents.config import AgentConfig, ConfigManager, RetryConfig
from agents.context_store import ContextStore
from models.business_models import CombinedAnalysis
from agents.skills.analyzer_skills import (
    analyze_post_skill,
    analyze_comments_skill,
    analyze_post_with_comments_skill,
    batch_analyze_posts_skill,
    batch_analyze_posts_with_comments_skill,
    generate_combined_analysis_skill,
    analyze_comments_with_tags_skill,
    generate_combined_analysis_from_posts_skill
)


logger = logging.getLogger("agent.analyzer")


class AnalyzerAgent(BaseAgent):
    """
    数据分析 Agent

    职责:
    1. 分析单条笔记的相关性和内容
    2. 分析评论提取用户洞察
    3. 批量分析笔记
    4. 生成综合分析报告

    Skills:
    - analyze_post: 分析单条笔记
    - analyze_comments: 分析评论
    - batch_analyze_posts: 批量分析笔记
    - batch_analyze_with_comments: 批量分析帖子+评论（统一分析）
    - combined_analysis: 生成综合分析
    """

    def __init__(
        self,
        config: ConfigManager,
        context_store: ContextStore,
        mcp_clients: Dict[str, Any]
    ):
        # 从 ConfigManager 获取 agent 配置
        agent_configs = config.get_agent_configs()
        agent_config = agent_configs.get("analyzer", AgentConfig(
            name="analyzer_agent",
            type="analyzer",
            enabled=True,
            timeout=600.0
        ))

        super().__init__(
            name="analyzer_agent",
            config=agent_config,
            context_store=context_store,
            mcp_clients=mcp_clients
        )

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        **kwargs
    ) -> TaskResult:
        """
        执行分析任务

        Args:
            task: 任务类型 (analyze_post/analyze_comments/batch_analyze/batch_analyze_with_comments/combined/combined_from_posts)
            context: 执行上下文
            **kwargs: 额外参数

        Returns:
            TaskResult: 任务执行结果
        """
        self.status = AgentStatus.RUNNING
        start_time = datetime.now()

        try:
            if task == "analyze_post":
                result = await self._analyze_post(context, kwargs)
            elif task == "analyze_comments":
                result = await self._analyze_comments(context, kwargs)
            elif task == "analyze_comments_with_tags":
                result = await self._analyze_comments_with_tags(context, kwargs)
            elif task == "batch_analyze":
                result = await self._batch_analyze(context, kwargs)
            elif task == "batch_analyze_with_comments":
                result = await self._batch_analyze_with_comments(context, kwargs)
            elif task == "combined":
                result = await self._combined_analysis(context, kwargs)
            elif task == "combined_from_posts":
                result = await self._combined_analysis_from_posts(context, kwargs)
            else:
                raise ValueError(f"Unknown task: {task}")

            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(True, execution_time)

            self.status = AgentStatus.COMPLETED
            return TaskResult(
                success=True,
                data=result,
                agent_name=self.name,
                execution_time=execution_time
            )

        except Exception as e:
            logger.exception(f"Analyzer task failed: {task}")
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(False, execution_time)

            self.status = AgentStatus.FAILED
            return TaskResult(
                success=False,
                error=str(e),
                agent_name=self.name,
                execution_time=execution_time
            )

    async def _analyze_post(
        self,
        context: Dict[str, Any],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析单条笔记

        Args:
            context: 执行上下文
            kwargs: 参数
                - note: 笔记数据
                - business_idea: 业务创意

        Returns:
            分析结果
        """
        note = context.get("note", kwargs.get("note", {}))
        business_idea = context.get("business_idea", kwargs.get("business_idea", ""))

        if not note:
            raise ValueError("note is required")
        if not business_idea:
            raise ValueError("business_idea is required")

        self.update_progress(
            "analyzing_post",
            0.5,
            f"正在分析笔记: {note.get('title', 'Unknown')}"
        )

        # 调用 skill
        result = await analyze_post_skill(self, note, business_idea)

        if result.get("success"):
            self.update_progress("analyzing_post", 1.0, "笔记分析完成")
        else:
            self.update_progress("analyzing_post", 1.0, f"分析失败: {result.get('error', 'Unknown')}")

        return result

    async def _analyze_comments(
        self,
        context: Dict[str, Any],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析评论

        Args:
            context: 执行上下文
            kwargs: 参数
                - comments: 评论列表
                - business_idea: 业务创意

        Returns:
            评论分析结果
        """
        comments = context.get("comments", kwargs.get("comments", []))
        business_idea = context.get("business_idea", kwargs.get("business_idea", ""))

        if not business_idea:
            raise ValueError("business_idea is required")

        self.update_progress(
            "analyzing_comments",
            0.5,
            f"正在分析 {len(comments)} 条评论..."
        )

        # 调用 skill
        result = await analyze_comments_skill(self, comments, business_idea)

        if result.get("success"):
            self.update_progress("analyzing_comments", 1.0, "评论分析完成")
        else:
            self.update_progress("analyzing_comments", 1.0, f"分析失败: {result.get('error', 'Unknown')}")

        return result

    async def _analyze_comments_with_tags(
        self,
        context: Dict[str, Any],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用标签体系分析评论（基于 functions.txt）

        Args:
            context: 执行上下文
            kwargs: 参数
                - posts_with_comments: 包含评论的帖子列表
                - business_idea: 业务创意

        Returns:
            评论标签分析结果
        """
        posts_with_comments = context.get("posts_with_comments", kwargs.get("posts_with_comments", []))
        business_idea = context.get("business_idea", kwargs.get("business_idea", ""))

        if not posts_with_comments:
            raise ValueError("posts_with_comments is required")
        if not business_idea:
            raise ValueError("business_idea is required")

        self.update_progress(
            "analyzing_comments_with_tags",
            0.1,
            f"开始标签体系评论分析（{len(posts_with_comments)} 个帖子）..."
        )

        # 调用 skill
        result = await analyze_comments_with_tags_skill(
            self,
            posts_with_comments=posts_with_comments,
            business_idea=business_idea
        )

        if result.get("success"):
            tag_analysis = result.get("tag_analysis", {})
            total_posts = tag_analysis.get("total_posts_analyzed", 0)
            total_tags = tag_analysis.get("total_tags_applied", 0)

            self.update_progress(
                "analyzing_comments_with_tags",
                1.0,
                f"标签分析完成: {total_posts} 个帖子，应用 {total_tags} 个标签"
            )

            # 保存检查点
            run_id = context.get("run_id")
            if run_id:
                await self.save_checkpoint(
                    run_id,
                    "comments_tag_analysis_complete",
                    {
                        "tag_analysis": result
                    }
                )
        else:
            self.update_progress(
                "analyzing_comments_with_tags",
                1.0,
                f"标签分析失败: {result.get('error', 'Unknown')}"
            )

        return result

    async def _batch_analyze(
        self,
        context: Dict[str, Any],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        批量分析笔记

        Args:
            context: 执行上下文
            kwargs: 参数
                - posts: 笔记列表
                - business_idea: 业务创意

        Returns:
            批量分析结果
        """
        posts = context.get("posts", kwargs.get("posts", []))
        business_idea = context.get("business_idea", kwargs.get("business_idea", ""))

        if not posts:
            raise ValueError("posts is required")
        if not business_idea:
            raise ValueError("business_idea is required")

        self.update_progress(
            "batch_analyzing",
            0.1,
            f"开始批量分析 {len(posts)} 条笔记..."
        )

        # 调用 skill - 直接传递 self 的进度回调
        result = await batch_analyze_posts_skill(
            self,
            posts=posts,
            business_idea=business_idea,
            progress_callback=self._progress_callback
        )

        # 处理结果（包括部分结果）
        if result.get("success") or result.get("partial"):
            summary = result.get("summary", {})
            analyzed = summary.get("analyzed_count", len(result.get("analyses", [])))
            total = summary.get("total_posts", len(posts))

            if result.get("partial"):
                self.update_progress(
                    "batch_analyzing",
                    1.0,
                    f"批量分析部分完成: {analyzed}/{total} 条笔记（超时）"
                )
                logger.warning(f"Batch analysis partial: {analyzed}/{total} posts analyzed")
            else:
                self.update_progress(
                    "batch_analyzing",
                    1.0,
                    f"批量分析完成: {summary.get('relevant_count', 0)}/{len(posts)} 条相关笔记"
                )

            # 保存检查点（即使是部分结果也保存）
            run_id = context.get("run_id")
            if run_id:
                await self.save_checkpoint(
                    run_id,
                    "analysis_complete",
                    {
                        "posts_analyses": result
                    }
                )
        else:
            self.update_progress("batch_analyzing", 1.0, "批量分析失败")

        return result

    async def _batch_analyze_with_comments(
        self,
        context: Dict[str, Any],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        批量分析帖子及其评论（统一分析）

        每个帖子与其评论作为一个整体进行综合分析，失败时跳过。

        Args:
            context: 执行上下文
            kwargs: 参数
                - posts_with_comments: 包含评论的帖子列表
                - business_idea: 业务创意

        Returns:
            批量分析结果
        """
        posts_with_comments = context.get("posts_with_comments", kwargs.get("posts_with_comments", []))
        business_idea = context.get("business_idea", kwargs.get("business_idea", ""))

        if not posts_with_comments:
            raise ValueError("posts_with_comments is required")
        if not business_idea:
            raise ValueError("business_idea is required")

        # 从配置获取最大分析帖子数
        from agents.config import ConfigManager
        config_mgr = ConfigManager()
        max_posts = config_mgr.get('agents.scraper.max_posts_to_analyze', 20)
        logger.info(f"配置的最大分析帖子数: {max_posts}")

        self.update_progress(
            "batch_analyzing_with_comments",
            0.1,
            f"开始统一分析 {min(len(posts_with_comments), max_posts)} 条帖子+评论..."
        )

        # 调用 skill - 直接传递 self 的进度回调和 max_posts 限制
        result = await batch_analyze_posts_with_comments_skill(
            self,
            posts_with_comments=posts_with_comments,
            business_idea=business_idea,
            progress_callback=self._progress_callback,
            max_posts=max_posts
        )

        # 处理结果（包括部分结果）
        if result.get("success") or result.get("partial"):
            summary = result.get("summary", {})
            successful = summary.get("successful_count", len(result.get("analyses", [])))
            total = summary.get("total_posts", len(posts_with_comments))

            if result.get("partial"):
                self.update_progress(
                    "batch_analyzing_with_comments",
                    1.0,
                    f"统一分析部分完成: {successful}/{total} 条（超时）"
                )
                logger.warning(f"Batch analysis partial: {successful}/{total} posts analyzed")
            else:
                self.update_progress(
                    "batch_analyzing_with_comments",
                    1.0,
                    f"统一分析完成: {summary.get('relevant_count', 0)}/{total} 条相关帖子，"
                    f"跳过 {summary.get('skipped_count', 0)} 条"
                )

            # 保存检查点（新格式）
            run_id = context.get("run_id")
            if run_id:
                await self.save_checkpoint(
                    run_id,
                    "analysis_complete",
                    {
                        "posts_with_comments_analyses": result
                    }
                )
        else:
            self.update_progress("batch_analyzing_with_comments", 1.0, "统一分析失败")

        return result

    async def _combined_analysis(
        self,
        context: Dict[str, Any],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成综合分析报告

        Args:
            context: 执行上下文
            kwargs: 参数
                - posts_analyses: 笔记分析结果
                - comments_analyses: 评论分析结果
                - business_idea: 业务创意

        Returns:
            综合分析结果
        """
        posts_analyses = context.get("posts_analyses", kwargs.get("posts_analyses", {}))
        comments_analyses = context.get("comments_analyses", kwargs.get("comments_analyses", {}))
        business_idea = context.get("business_idea", kwargs.get("business_idea", ""))

        if not business_idea:
            raise ValueError("business_idea is required")

        self.update_progress(
            "generating_combined_analysis",
            0.5,
            "正在生成综合分析报告..."
        )

        # 调用 skill
        result = await generate_combined_analysis_skill(
            self,
            posts_analyses=posts_analyses,
            comments_analyses=comments_analyses,
            business_idea=business_idea
        )

        analysis = result.get("analysis", {})
        score = analysis.get("overall_score", 0)

        if result.get("success"):
            self.update_progress(
                "generating_combined_analysis",
                1.0,
                f"综合分析完成: 评分 {score}/100"
            )
        else:
            # 即使失败也更新进度，并保存检查点
            self.update_progress(
                "generating_combined_analysis",
                1.0,
                f"综合分析完成 (使用fallback): 评分 {score}/100"
            )

        # 无论成功或失败，都保存检查点（包含fallback分析）
        run_id = context.get("run_id")
        if run_id:
            await self.save_checkpoint(
                run_id,
                "combined_analysis_complete",
                {
                    "combined_analysis": result
                }
            )

        return result

    async def _combined_analysis_from_posts(
        self,
        context: Dict[str, Any],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从统一的帖子+评论分析生成综合报告

        与 _combined_analysis 的区别：
        - 只需要 posts_with_comments_analyses（不需要单独的 comments_analyses）
        - 帖子分析已经包含了从评论中提取的洞察

        Args:
            context: 执行上下文
            kwargs: 参数
                - posts_with_comments_analyses: 统一分析结果
                - business_idea: 业务创意

        Returns:
            综合分析结果
        """
        posts_with_comments_analyses = context.get(
            "posts_with_comments_analyses",
            kwargs.get("posts_with_comments_analyses", {})
        )
        business_idea = context.get("business_idea", kwargs.get("business_idea", ""))

        if not business_idea:
            raise ValueError("business_idea is required")

        self.update_progress(
            "generating_combined_analysis",
            0.5,
            "正在生成综合分析报告..."
        )

        # 从统一分析中提取数据
        relevant_posts = posts_with_comments_analyses.get("relevant_posts", [])
        summary = posts_with_comments_analyses.get("summary", {})

        # 1. 收集定性洞察（现有 - 保留）
        all_pain_points = []
        all_solutions = []
        all_signals = []
        all_user_insights = []
        all_user_needs = []

        # 2. 新增：收集定量指标用于加权分析
        engagement_scores = []
        sentiment_scores = []  # positive=1, neutral=0, negative=-1
        feedback_sentiments = []
        all_post_engagement = []  # 原始互动指标

        # 3. 新增：收集时间数据
        recent_posts_count = 0
        total_comments_analyzed = 0

        # 4. 新增：收集高质量内容（用于参考）
        top_posts = []  # 互动量最高的帖子

        for item in relevant_posts:
            post = item.get("post", {})
            analysis = item.get("analysis", {})

            # 定性洞察
            all_pain_points.extend(analysis.get("pain_points", []))
            all_solutions.extend(analysis.get("solutions_mentioned", []))
            all_signals.extend(analysis.get("market_signals", []))
            all_user_insights.extend(analysis.get("user_insights", []))
            all_user_needs.extend(analysis.get("user_needs", []))

            # 新增：定量指标
            engagement_scores.append(analysis.get("engagement_score", 0))

            # 将情感转换为数值
            sentiment = analysis.get("sentiment", "neutral")
            sentiment_value = {"positive": 1, "neutral": 0, "negative": -1}.get(sentiment, 0)
            sentiment_scores.append(sentiment_value)

            feedback_sentiments.append(analysis.get("feedback_sentiment", "neutral"))

            # 原始帖子互动量
            total_engagement = (
                post.get("liked_count", 0) +
                post.get("collected_count", 0) * 2 +  # 收藏加权更高
                post.get("shared_count", 0) * 3 +  # 分享加权更高
                post.get("comments_count", 0)
            )
            all_post_engagement.append({
                "note_id": post.get("note_id"),
                "title": post.get("title"),
                "total_engagement": total_engagement,
                "likes": post.get("liked_count", 0),
                "saves": post.get("collected_count", 0),
                "shares": post.get("shared_count", 0),
                "comments": post.get("comments_count", 0)
            })

            # 新增：时间分析
            publish_time = post.get("publish_time", 0)
            if publish_time:
                post_date = datetime.fromtimestamp(publish_time)
                if post_date > datetime.now() - timedelta(days=30):
                    recent_posts_count += 1

            # 新增：评论数量
            total_comments_analyzed += analysis.get("comments_count", 0)

            # 新增：追踪热门帖子
            if len(top_posts) < 5:
                top_posts.append({
                    "post": post,
                    "analysis": analysis,
                    "engagement_score": analysis.get("engagement_score", 0),
                    "total_engagement": total_engagement
                })
            else:
                # 如果互动量更高则替换
                min_idx = min(range(len(top_posts)), key=lambda i: top_posts[i]["total_engagement"])
                if total_engagement > top_posts[min_idx]["total_engagement"]:
                    top_posts[min_idx] = {
                        "post": post,
                        "analysis": analysis,
                        "engagement_score": analysis.get("engagement_score", 0),
                        "total_engagement": total_engagement
                    }

        # 5. 新增：计算汇总指标
        avg_engagement_score = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

        # 情感分布
        sentiment_dist = {
            "positive": feedback_sentiments.count("positive"),
            "neutral": feedback_sentiments.count("neutral"),
            "negative": feedback_sentiments.count("negative")
        }

        # 按互动量排序的热门帖子
        top_posts_sorted = sorted(top_posts, key=lambda x: x["total_engagement"], reverse=True)[:3]

        # 6. 新增：构建增强的提示（包含所有数据）
        prompt = f"""
你是一位资深市场分析师。请根据以下数据，为业务创意生成一份综合市场验证分析报告：

业务创意："{business_idea}"

=== 数据摘要 ===
相关帖子数: {summary.get('relevant_count', 0)}
成功率: {summary.get('successful_count', 0)}/{summary.get('total_posts', 0)}
相关帖子比例: {summary.get('relevance_rate', 0):.1%}
平均互动评分: {avg_engagement_score:.1f}/10
总体情感倾向: {"积极" if avg_sentiment > 0.2 else "中性" if avg_sentiment > -0.2 else "消极"} ({avg_sentiment:.2f})
情感分布: 积极={sentiment_dist['positive']}, 中性={sentiment_dist['neutral']}, 消极={sentiment_dist['negative']}
总评论分析数: {total_comments_analyzed}
最近30天活跃度: {recent_posts_count}/{len(relevant_posts)} 帖子

=== 热门帖子 TOP 3（按互动量排序）===
{chr(10).join(
    f"{i+1}. 【{p['post'].get('title', '无标题')}】"
    f"   互动量: {p['total_engagement']:,} (赞:{p['post'].get('liked_count',0)} 收藏:{p['post'].get('collected_count',0)} 分享:{p['post'].get('shared_count',0)} 评论:{p['post'].get('comments_count',0)})"
    f"   AI评分: {p['engagement_score']}/10"
    f"   情感: {p['analysis'].get('sentiment', 'neutral')}"
    for i, p in enumerate(top_posts_sorted)
) if top_posts_sorted else "无"}

=== 关键痛点（来自帖子+评论）===
{chr(10).join(f"- {p}" for p in all_pain_points[:15] if all_pain_points) or "无"}

=== 现有解决方案 ===
{chr(10).join(f"- {s}" for s in all_solutions[:15] if all_solutions) or "无"}

=== 市场信号 ===
{chr(10).join(f"- {s}" for s in all_signals[:15] if all_signals) or "无"}

=== 用户洞察（来自评论）===
{chr(10).join(f"- {i}" for i in all_user_insights[:15] if all_user_insights) or "无"}

=== 用户需求（来自评论）===
{chr(10).join(f"- {n}" for n in all_user_needs[:15] if all_user_needs) or "无"}

请生成综合分析报告，评分时请综合考虑：
1. 市场需求程度（基于痛点数量和用户需求）
2. 竞争激烈程度（基于现有解决方案数量）
3. 用户反馈质量（基于情感倾向和互动量）
4. 市场活跃度（基于近期帖子比例和总互动量）
5. 内容质量（基于热门帖子的AI评分和互动量）

请以 JSON 格式返回：
{{
    "overall_score": 75,
    "market_validation_summary": "市场验证摘要...",
    "key_pain_points": ["痛点1", "痛点2", "痛点3"],
    "existing_solutions": ["方案1", "方案2"],
    "market_opportunities": ["机会1", "机会2", "机会3"],
    "recommendations": ["建议1", "建议2", "建议3"]
}}
"""

        logger.debug(f"Combined analysis prompt:\n{prompt}")

        # 重试逻辑
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.warning(f"Retry attempt {attempt}/{max_retries} for combined analysis")
                    await asyncio.sleep(2 ** attempt)

                result = await self.use_llm(prompt, response_model=CombinedAnalysis)

                if hasattr(result, 'model_dump'):
                    analysis = result.model_dump()
                else:
                    analysis = result

                # 词频分析 - 对关键维度进行标签分析
                logger.info("Starting word frequency analysis for combined insights")

                # 提取需要进行词频分析的数据
                key_pain_points = analysis.get("key_pain_points", [])
                existing_solutions = analysis.get("existing_solutions", [])
                market_opportunities = analysis.get("market_opportunities", [])
                recommendations = analysis.get("recommendations", [])

                # 添加到 metadata（需要包含在 LLM 返回的 metadata 中）
                metadata = {
                    "total_posts_analyzed": summary.get('total_posts', 0),
                    "relevant_posts": summary.get('relevant_count', 0),
                    "avg_engagement_score": avg_engagement_score,
                    "avg_sentiment": avg_sentiment,
                    "sentiment_distribution": sentiment_dist,
                    "total_comments_analyzed": total_comments_analyzed,
                    "recent_posts_30days": recent_posts_count,
                    "top_posts_engagement": [p['total_engagement'] for p in top_posts_sorted],
                    "analysis_date": datetime.now().isoformat()
                }

                analysis["metadata"] = metadata

                logger.info(f"Combined analysis complete: score={analysis.get('overall_score')}/100")

                # 保存检查点
                result = {
                    "success": True,
                    "analysis": analysis
                }
                run_id = context.get("run_id")
                if run_id:
                    await self.save_checkpoint(
                        run_id,
                        "combined_analysis_complete",
                        {
                            "combined_analysis": result
                        }
                    )

                return result

            except (ValueError, ConnectionError, TimeoutError) as e:
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed for combined analysis: {e}, will retry...")
                    continue
                else:
                    logger.error(f"All retries exhausted for combined analysis: {e}")
                    # 使用收集的数据构建 fallback
                    fallback_analysis = {
                        "overall_score": 50,
                        "market_validation_summary": f"分析失败（重试{max_retries}次后仍失败）: {type(e).__name__}",
                        "key_pain_points": all_pain_points[:5] if all_pain_points else [],
                        "existing_solutions": all_solutions[:5] if all_solutions else [],
                        "market_opportunities": [],
                        "recommendations": ["请重新运行分析"],
                        "platform_insights": [],
                        "metadata": {
                            "total_posts_analyzed": summary.get('total_posts', 0),
                            "relevant_posts": summary.get('relevant_count', 0),
                            "successful_count": summary.get('successful_count', 0),
                            "skipped_count": summary.get('skipped_count', 0),
                            "avg_engagement_score": avg_engagement_score,
                            "avg_sentiment": avg_sentiment,
                            "sentiment_distribution": sentiment_dist,
                            "total_comments_analyzed": total_comments_analyzed,
                            "recent_posts_30days": recent_posts_count,
                            "top_posts_engagement": [p['total_engagement'] for p in top_posts_sorted],
                            "error": str(e)
                        }
                    }
                    return {
                        "success": False,
                        "analysis": fallback_analysis,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }

            except Exception as e:
                logger.error(f"Generate combined analysis skill failed: {type(e).__name__}: {e}")
                return {
                    "success": False,
                    "analysis": {
                        "overall_score": 50,
                        "market_validation_summary": f"分析失败: {type(e).__name__}",
                        "key_pain_points": all_pain_points[:5] if all_pain_points else [],
                        "existing_solutions": all_solutions[:5] if all_solutions else [],
                        "market_opportunities": [],
                        "recommendations": ["请重新运行分析"],
                        "platform_insights": [],
                        "metadata": {
                            "total_posts_analyzed": summary.get('total_posts', 0),
                            "relevant_posts": summary.get('relevant_count', 0),
                            "avg_engagement_score": avg_engagement_score,
                            "avg_sentiment": avg_sentiment,
                            "sentiment_distribution": sentiment_dist,
                            "total_comments_analyzed": total_comments_analyzed,
                            "recent_posts_30days": recent_posts_count
                        }
                    },
                    "error": str(e),
                    "error_type": type(e).__name__
                }

    def _update_metrics(
        self,
        success: bool,
        execution_time: float
    ):
        """更新运行指标"""
        self.metrics.tasks_completed += 1 if success else 0
        self.metrics.tasks_failed += 0 if success else 1
        self.metrics.total_execution_time += execution_time

        total = self.metrics.tasks_completed + self.metrics.tasks_failed
        if total > 0:
            self.metrics.avg_execution_time = self.metrics.total_execution_time / total

        self.metrics.last_execution = datetime.now()
