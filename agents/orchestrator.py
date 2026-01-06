"""
编排器 Agent

负责协调整个业务验证流程，分配任务给子 Agent
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum

from agents.base_agent import BaseAgent, AgentStatus, TaskResult
from agents.config import AgentConfig, ConfigManager, RetryConfig
from agents.context_store import ContextStore
from agents.subagents import ScraperAgent, AnalyzerAgent, ReporterAgent
from models.agent_models import (
    ExecutionPlan,
    ExecutionStep,
    OrchestratorState,
    ProgressUpdate
)
from models.business_models import ValidationResult


logger = logging.getLogger("agent.orchestrator")


class WorkflowStage(Enum):
    """工作流阶段"""
    INITIALIZATION = "initialization"
    KEYWORD_GENERATION = "keyword_generation"
    DATA_SCRAPING = "data_scraping"
    DATA_ANALYSIS = "data_analysis"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"
    FAILED = "failed"


class OrchestratorAgent(BaseAgent):
    """
    编排器 Agent

    职责:
    1. 解析用户输入，生成执行计划
    2. 分配任务给子 Agent
    3. 监控执行进度
    4. 处理错误和重试
    5. 汇总结果并生成报告

    子 Agents:
    - KeywordAgent: 生成关键词
    - ScraperAgent: 抓取数据
    - AnalyzerAgent: 分析数据
    - ReporterAgent: 生成报告
    """

    def __init__(
        self,
        config: ConfigManager,
        context_store: ContextStore,
        mcp_clients: Dict[str, Any],
        subagents: Optional[Dict[str, BaseAgent]] = None
    ):
        # 为 Orchestrator 创建一个 AgentConfig
        orchestrator_config = AgentConfig(
            name="orchestrator",
            type="orchestrator",
            enabled=True,
            timeout=600.0,
            max_retries=3,
            retry_config=RetryConfig()
        )

        super().__init__(
            name="orchestrator",
            config=orchestrator_config,
            context_store=context_store,
            mcp_clients=mcp_clients
        )

        # 保存 ConfigManager 引用
        self.config_manager = config

        # 初始化子 Agents
        self.subagents = subagents or {}

        # 工作流状态
        self.state = OrchestratorState(
            current_stage=WorkflowStage.INITIALIZATION.value,
            total_steps=0,
            completed_steps=0,
            failed_steps=0
        )

    # ========================================================================
    # 生命周期管理
    # ========================================================================

    async def start(self):
        """启动编排器"""
        await super().start()
        # 初始化并启动子 Agents
        await self._initialize_and_start_subagents()
        logger.info("Orchestrator started")

    async def stop(self):
        """停止编排器"""
        await super().stop()
        logger.info("Orchestrator stopped")

    # ========================================================================
    # 核心执行方法
    # ========================================================================

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        **kwargs
    ) -> TaskResult:
        """
        执行编排任务

        Args:
            task: 任务类型 (validate_business_idea)
            context: 执行上下文
            **kwargs: 额外参数

        Returns:
            TaskResult: 任务执行结果
        """
        if task == "validate_business_idea":
            return await self._validate_business_idea(context, kwargs)
        else:
            raise ValueError(f"Unknown task: {task}")

    async def _validate_business_idea(
        self,
        context: Dict[str, Any],
        kwargs: Dict[str, Any]
    ) -> TaskResult:
        """
        执行完整的业务创意验证流程

        Args:
            context: 执行上下文
            kwargs: 参数
                - business_idea: 业务创意
                - keyword_count: 关键词数量 (默认3)
                - pages_per_keyword: 每个关键词的搜索页数 (默认2)
                - comments_per_note: 每个笔记的评论数 (默认20)
                - report_format: 报告格式 (text/html，默认html)
                - use_user_input_as_keyword: 是否直接使用用户输入作为关键词

        Returns:
            验证结果
        """
        start_time = datetime.now()
        business_idea = context.get("business_idea", kwargs.get("business_idea", ""))

        if not business_idea:
            raise ValueError("business_idea is required")

        # 创建运行上下文
        run_id = self.context_store.create_run(
            business_idea=business_idea,
            user_preferences=kwargs.get("user_preferences", {})
        )

        logger.info(f"Starting validation for: {business_idea} (run_id: {run_id})")

        # 设置初始状态
        self.state = OrchestratorState(
            current_stage=WorkflowStage.INITIALIZATION.value,
            run_id=run_id,
            total_steps=6,  # 更新：增加了评论标签分析步骤
            completed_steps=0,
            failed_steps=0
        )

        try:
            # 阶段1: 生成执行计划
            execution_plan = await self._create_execution_plan(business_idea, kwargs)

            # 执行工作流
            result = await self._execute_workflow(
                run_id=run_id,
                business_idea=business_idea,
                execution_plan=execution_plan,
                context=context,
                kwargs=kwargs
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # 更新最终状态
            if result["success"]:
                self.state.current_stage = WorkflowStage.COMPLETED.value
                self.state.completed_steps = self.state.total_steps
                logger.info(f"Validation completed successfully in {execution_time:.2f}s")
            else:
                self.state.current_stage = WorkflowStage.FAILED.value
                self.state.failed_steps += 1
                logger.error(f"Validation failed: {result.get('error')}")

            # 更新运行上下文
            self.context_store.update_run_status(run_id, self.state.current_stage)

            return TaskResult(
                success=result["success"],
                data=result,
                agent_name=self.name,
                run_id=run_id,
                execution_time=execution_time
            )

        except Exception as e:
            logger.exception(f"Validation failed with exception")
            execution_time = (datetime.now() - start_time).total_seconds()

            self.state.current_stage = WorkflowStage.FAILED.value
            self.context_store.update_run_status(run_id, self.state.current_stage)

            return TaskResult(
                success=False,
                error=str(e),
                agent_name=self.name,
                run_id=run_id,
                execution_time=execution_time
            )

    # ========================================================================
    # 执行计划
    # ========================================================================

    async def _create_execution_plan(
        self,
        business_idea: str,
        kwargs: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        创建执行计划

        Args:
            business_idea: 业务创意
            kwargs: 参数

        Returns:
            执行计划
        """
        keyword_count = kwargs.get("keyword_count", 3)
        pages_per_keyword = kwargs.get("pages_per_keyword", 2)
        comments_per_note = kwargs.get("comments_per_note", 20)
        use_fast_mode = kwargs.get("use_user_input_as_keyword", False)

        # 从配置获取最大分析帖子数
        from agents.config import ConfigManager
        config_mgr = ConfigManager()
        max_notes = config_mgr.get('agents.scraper.max_posts_to_analyze', 20)
        logger.info(f"使用配置的最大帖子分析数: {max_notes} (来源: ANALYZER_MAX_POSTS)")

        # Always use the user input directly as the search keyword (remove keyword generation step)
        logger.info(f"直接使用用户输入作为搜索关键词 - '{business_idea}'")

        # Fast mode: 减少数据量
        if use_fast_mode:
            pages_per_keyword = 1
            comments_per_note = 5
            logger.info(f"[快速模式] 减少数据量: pages=1, comments=5")

        steps = [
            ExecutionStep(
                step_id="scrape_data",
                agent_name="scraper_agent",
                task="batch_scrape_with_comments",
                description="抓取小红书数据（带评论合并）",
                params={
                    "pages_per_keyword": pages_per_keyword,
                    "comments_per_note": comments_per_note,
                    "max_notes": max_notes
                },
                depends_on=[],  # 无依赖，直接开始
                retry_on_failure=True,
                timeout=600
            ),
            ExecutionStep(
                step_id="analyze_posts_with_comments",
                agent_name="analyzer_agent",
                task="batch_analyze_with_comments",
                description="分析笔记和评论（统一分析）",
                params={},
                depends_on=["scrape_data"],
                retry_on_failure=True,
                timeout=900
            ),
            ExecutionStep(
                step_id="analyze_comments_with_tags",
                agent_name="analyzer_agent",
                task="analyze_comments_with_tags",
                description="评论标签体系分析（人群/功能/保障/体验价值）",
                params={},
                depends_on=["analyze_posts_with_comments"],
                retry_on_failure=False,  # 评论标签分析失败不重试（可选）
                timeout=600  # 10分钟
            ),
            ExecutionStep(
                step_id="combined_analysis",
                agent_name="analyzer_agent",
                task="combined_from_posts",
                description="生成综合分析",
                params={},
                depends_on=["analyze_posts_with_comments"],  # 只依赖帖子分析，标签分析是可选的
                retry_on_failure=True,
                timeout=180
            ),
            ExecutionStep(
                step_id="generate_report",
                agent_name="reporter_agent",
                task="generate_html",
                description="生成验证报告",
                params={"auto_save": True},
                depends_on=["combined_analysis"],
                retry_on_failure=False,
                timeout=60
            )
        ]

        return ExecutionPlan(
            business_idea=business_idea,
            steps=steps,
            total_steps=len(steps)
        )

    # ========================================================================
    # 工作流执行
    # ========================================================================

    async def _execute_workflow(
        self,
        run_id: str,
        business_idea: str,
        execution_plan: ExecutionPlan,
        context: Dict[str, Any],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行工作流

        Args:
            run_id: 运行 ID
            business_idea: 业务创意
            execution_plan: 执行计划
            context: 执行上下文
            kwargs: 参数

        Returns:
            执行结果
        """
        results = {}
        shared_context = {
            "business_idea": business_idea,
            "run_id": run_id,
            **context
        }

        # 快速模式：直接使用用户输入作为关键词
        use_fast_mode = kwargs.get("use_user_input_as_keyword", False)
        if use_fast_mode:
            shared_context["keywords"] = [business_idea]
            logger.info(f"[快速模式] 直接使用用户输入作为搜索关键词: {business_idea}")

        # 按顺序执行步骤（处理依赖关系）
        for step in execution_plan.steps:
            # 检查依赖是否满足
            if not self._check_dependencies(step.depends_on, results):
                logger.warning(f"Step {step.step_id} dependencies not met, skipping")
                continue

            # 更新状态
            self.state.current_stage = f"executing_{step.step_id}"
            self.update_progress(
                step.step_id,
                0.0,
                f"执行: {step.description}"
            )

            # 执行步骤
            try:
                step_result = await self._execute_step(
                    step=step,
                    shared_context=shared_context,
                    results=results
                )

                results[step.step_id] = step_result

                if step_result["success"]:
                    self.state.completed_steps += 1
                    self.update_progress(
                        step.step_id,
                        1.0,
                        f"完成: {step.description}"
                    )

                    # 更新共享上下文
                    shared_context = self._update_shared_context(
                        step.step_id,
                        step_result,
                        shared_context
                    )
                else:
                    if step.retry_on_failure:
                        logger.warning(f"Step {step.step_id} failed, retrying...")
                        # 重试逻辑
                        step_result = await self._execute_step_with_retry(
                            step=step,
                            shared_context=shared_context,
                            results=results,
                            max_retries=2
                        )
                        results[step.step_id] = step_result

                        if not step_result["success"]:
                            self.state.failed_steps += 1
                    else:
                        self.state.failed_steps += 1
                        logger.error(f"Step {step.step_id} failed: {step_result.get('error')}")

            except asyncio.CancelledError as e:
                # 任务被取消（通常是超时导致的）
                logger.error(f"Step {step.step_id} was cancelled (likely timeout after {step.timeout}s)")
                # 检查是否已有部分结果（skill 可能已经返回了部分数据）
                # 注意：由于 asyncio.wait_for 的问题，部分结果可能已经丢失
                # 这里我们标记为失败，但保留后续步骤继续的可能性
                results[step.step_id] = {
                    "success": False,
                    "error": f"Task cancelled - likely timeout after {step.timeout}s. Consider increasing timeout or reducing data size.",
                    "error_type": "CancelledError",
                    "timeout": step.timeout,
                    "data": {}  # 空数据，后续步骤需要处理
                }
                # 对于可重试的步骤，增加失败计数
                if step.retry_on_failure:
                    self.state.failed_steps += 1
            except Exception as e:
                logger.exception(f"Step {step.step_id} failed with exception")
                results[step.step_id] = {
                    "success": False,
                    "error": str(e),
                    "data": {}  # 空数据
                }
                if not step.retry_on_failure:
                    self.state.failed_steps += 1

        # 检查是否成功
        success = self.state.failed_steps == 0

        return {
            "success": success,
            "run_id": run_id,
            "business_idea": business_idea,
            "state": self.state.model_dump(),
            "step_results": results
        }

    async def _execute_step(
        self,
        step: ExecutionStep,
        shared_context: Dict[str, Any],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行单个步骤

        Args:
            step: 执行步骤
            shared_context: 共享上下文
            results: 已完成的结果

        Returns:
            步骤结果
        """
        agent = self.subagents.get(step.agent_name)
        if not agent:
            return {
                "success": False,
                "error": f"Agent not found: {step.agent_name}"
            }

        # 合并参数和上下文
        exec_context = {**shared_context}
        exec_context.update(step.params)

        # DEBUG: Log parameters for keyword generation step
        if step.step_id == "generate_keywords":
            logger.debug(f"[ORCHESTRATOR] Executing generate_keywords with params: {step.params}")
            logger.debug(f"[ORCHESTRATOR] use_user_input_as_keyword = {step.params.get('use_user_input_as_keyword')}")

        # 执行任务
        task_result = await asyncio.wait_for(
            agent.execute(step.task, exec_context),
            timeout=step.timeout
        )

        return {
            "success": task_result.success,
            "data": task_result.data,
            "error": task_result.error,
            "execution_time": task_result.execution_time
        }

    async def _execute_step_with_retry(
        self,
        step: ExecutionStep,
        shared_context: Dict[str, Any],
        results: Dict[str, Any],
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        带重试的步骤执行

        Args:
            step: 执行步骤
            shared_context: 共享上下文
            results: 已完成的结果
            max_retries: 最大重试次数

        Returns:
            步骤结果
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"Retrying step {step.step_id}, attempt {attempt + 1}/{max_retries}")
                result = await self._execute_step(step, shared_context, results)

                if result["success"]:
                    return result

                last_error = result.get("error", "Unknown error")
                await asyncio.sleep(2 ** attempt)  # 指数退避

            except asyncio.CancelledError:
                # 任务被取消（超时）
                last_error = f"Task cancelled (timeout after {step.timeout}s). This suggests the operation is taking too long. Try reducing max_notes or increasing timeout."
            except asyncio.TimeoutError:
                last_error = f"Timeout after {step.timeout}s"
            except Exception as e:
                last_error = str(e)

        return {
            "success": False,
            "error": f"Retry failed: {last_error}"
        }

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _check_dependencies(
        self,
        dependencies: List[str],
        results: Dict[str, Any]
    ) -> bool:
        """
        检查依赖是否满足

        Args:
            dependencies: 依赖的步骤 ID 列表
            results: 已完成的结果

        Returns:
            是否满足依赖
        """
        for dep in dependencies:
            if dep not in results:
                return False
            if not results[dep].get("success", False):
                return False
        return True

    def _update_shared_context(
        self,
        step_id: str,
        step_result: Dict[str, Any],
        shared_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据步骤结果更新共享上下文

        Args:
            step_id: 步骤 ID
            step_result: 步骤结果
            shared_context: 当前共享上下文

        Returns:
            更新后的共享上下文
        """
        # Skip the generate_keywords step since we're using user input directly
        # Initialize keywords from business idea if not already set
        if step_id == "scrape_data":
            # 新格式：posts_with_comments 结构
            data = step_result.get("data", {})
            shared_context["posts_with_comments"] = data.get("posts_with_comments", [])
            metadata = data.get("metadata", {})

            # If keywords haven't been set yet, use the business idea
            if "keywords" not in shared_context and "business_idea" in shared_context:
                business_idea = shared_context.get("business_idea", "")
                if business_idea:
                    shared_context["keywords"] = [business_idea]

            logger.info(
                f"scrape_data completed: {metadata.get('total_posts', 0)} posts, "
                f"{metadata.get('posts_with_comments', 0)} with comments"
            )

        elif step_id == "analyze_posts_with_comments":
            # 新格式：posts_with_comments_analyses 结构
            shared_context["posts_with_comments_analyses"] = step_result.get("data", {})
            summary = step_result.get("data", {}).get("summary", {})
            logger.info(
                f"analyze_posts_with_comments completed: "
                f"{summary.get('relevant_count', 0)} relevant posts from "
                f"{summary.get('total_posts', 0)} total"
            )

        elif step_id == "analyze_comments_with_tags":
            # 新增：评论标签分析结果
            shared_context["comments_tag_analysis"] = step_result.get("data", {})
            tag_analysis = step_result.get("data", {}).get("tag_analysis", {})
            logger.info(
                f"analyze_comments_with_tags completed: "
                f"{tag_analysis.get('total_posts_analyzed', 0)} posts analyzed, "
                f"{tag_analysis.get('total_tags_applied', 0)} tags applied"
            )

        elif step_id == "combined_analysis":
            shared_context["analysis"] = step_result.get("data", {})

        elif step_id == "generate_report":
            shared_context["report"] = step_result.get("data", {})

        return shared_context

    async def _initialize_and_start_subagents(self):
        """初始化并启动子 Agents"""
        if not self.subagents:
            self.subagents = {
                "scraper_agent": ScraperAgent(
                    self.config_manager,
                    self.context_store,
                    self.mcp_clients
                ),
                "analyzer_agent": AnalyzerAgent(
                    self.config_manager,
                    self.context_store,
                    self.mcp_clients
                ),
                "reporter_agent": ReporterAgent(
                    self.config_manager,
                    self.context_store,
                    self.mcp_clients
                )
            }

        # 启动所有子 Agents
        for agent_name, agent in self.subagents.items():
            try:
                await agent.start()
                logger.info(f"Subagent {agent_name} started")
            except Exception as e:
                logger.error(f"Failed to start subagent {agent_name}: {e}")
