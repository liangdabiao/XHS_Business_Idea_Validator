"""
LLM MCP 服务器

提供大语言模型调用服务
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import os

from agents.logging_config import RequestLogger

logger = logging.getLogger("mcp.llm_server")


class LLMClient:
    """
    LLM 客户端

    封装 OpenAI API 调用
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 12000
    ):
        """
        初始化 LLM 客户端

        Args:
            api_key: OpenAI API Key
            base_url: API Base URL
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

        # 请求日志记录器
        self.request_logger = RequestLogger(logger)

        logger.info(f"LLM Client initialized: model={model_name}")

    async def start(self):
        """启动客户端"""
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        logger.info("LLM Client started")

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.close()
        logger.info("LLM Client closed")

    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        生成文本

        Args:
            prompt: 提示词
            max_tokens: 最大 token 数
            temperature: 温度参数

        Returns:
            生成的文本
        """
        if not self._client:
            await self.start()

        # 验证配置
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise ValueError(
                "OpenAI API Key 未配置或无效。请检查 agent_system/.env 文件中的 OPENAI_API_KEY。"
            )

        # 记录请求日志
        self.request_logger.log_request(
            api_name="OpenAI",
            method="POST",
            url=f"{self.base_url}/chat/completions",
            body={
                "model": self.model_name,
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature
            }
        )

        start_time = time.time()

        try:
            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                timeout=30.0  # 添加超时
            )

            duration_ms = (time.time() - start_time) * 1000
            content = response.choices[0].message.content

            # 记录响应日志
            self.request_logger.log_response(
                api_name="OpenAI",
                body={
                    "model": self.model_name,
                    "response_length": len(content),
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                },
                duration_ms=duration_ms
            )

            return content

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            # 记录错误日志
            self.request_logger.log_response(
                api_name="OpenAI",
                error=str(e),
                duration_ms=duration_ms
            )
            # 提供更详细的错误信息
            error_type = type(e).__name__
            error_msg = str(e)

            logger.error(f"OpenAI API 调用失败: {error_type}: {error_msg}")
            logger.error(f"配置: model={self.model_name}, base_url={self.base_url}")

            # 针对不同错误类型提供建议
            if "401" in error_msg or "Unauthorized" in error_msg:
                raise ValueError(
                    f"OpenAI API 认证失败 (401 Unauthorized)。请检查 OPENAI_API_KEY 是否正确。"
                ) from e
            elif "404" in error_msg or "Not Found" in error_msg:
                raise ValueError(
                    f"OpenAI API 端点未找到 (404)。请检查 OPENAI_BASE_URL 是否正确: {self.base_url}"
                ) from e
            elif "timeout" in error_msg.lower() or "Timeout" in error_type:
                raise TimeoutError(
                    f"OpenAI API 请求超时。请检查网络连接或稍后重试。"
                ) from e
            elif "connection" in error_msg.lower():
                raise ConnectionError(
                    f"无法连接到 OpenAI API ({self.base_url})。请检查网络连接和 base_url 配置。"
                ) from e
            else:
                raise

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        生成结构化输出

        Args:
            prompt: 提示词
            schema: JSON Schema (仅用于验证，不附加到prompt)
            max_tokens: 最大 token 数

        Returns:
            结构化数据
        """
        # 不再附加schema到prompt，避免LLM混淆
        # schema仅用于后续验证
        text = await self.generate_text(prompt, max_tokens=max_tokens)

        logger.debug(f"LLM raw response (first 7500 chars): {text[:7500]}")

        # 清理文本：提取 markdown 代码块中的 JSON
        text = text.strip()
        
        # 使用正则表达式提取 JSON 代码块
        import re
        json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        match = re.search(json_pattern, text)
        
        if match:
            text = match.group(1).strip()
            logger.debug(f"Extracted JSON from code block (length: {len(text)})")
        else:
            # 如果没有找到代码块，尝试直接解析
            logger.debug("No code block found, trying to parse directly")
            text = text.strip()

        # 解析 JSON
        import json
        try:
            data = json.loads(text)
            logger.debug(f"Successfully parsed JSON with keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            
            # 可选：使用schema进行验证（如果需要）
            # 这里暂时不进行验证，因为schema可能过于严格
            
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse structured output: {e}")
            logger.error(f"Raw text (first 1000 chars): {text[:1000]}")
            logger.error(f"Text length: {len(text)}")
            raise


class LLMMCPServer:
    """
    LLM MCP 服务器

    提供工具:
    - generate_text: 生成文本
    - generate_structured: 生成结构化输出
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model_name: str = "gpt-4o"
    ):
        """
        初始化 LLM MCP 服务器

        Args:
            api_key: OpenAI API Key
            base_url: API Base URL
            model_name: 模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self._client = None

        logger.info("LLM MCP Server initialized")

    async def start(self):
        """启动服务器"""
        self._client = LLMClient(
            api_key=self.api_key,
            base_url=self.base_url,
            model_name=self.model_name
        )
        await self._client.start()
        logger.info("LLM MCP Server started")

    async def stop(self):
        """停止服务器"""
        if self._client:
            await self._client.close()
        logger.info("LLM MCP Server stopped")

    # ========================================================================
    # MCP 工具实现
    # ========================================================================

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        调用工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        if tool_name == "generate_text":
            return await self.generate_text(**kwargs)
        elif tool_name == "generate_structured":
            return await self.generate_structured(**kwargs)
        elif tool_name == "test_connection":
            return await self.test_connection()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 12000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        生成文本

        Args:
            prompt: 提示词
            max_tokens: 最大 token 数
            temperature: 温度参数

        Returns:
            {
                "success": true,
                "text": "生成的文本",
                "model": "模型名称",
                "tokens_used": 使用token数
            }
        """
        start_time = datetime.now()

        try:
            text = await self._client.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"Generated text in {execution_time:.2f}s")

            return {
                "success": True,
                "text": text,
                "model": self.model_name,
                "tokens_used": len(text.split()) * 1.3,  # 估算
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(f"Generate text failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        max_tokens: int = 12000
    ) -> Dict[str, Any]:
        """
        生成结构化输出

        Args:
            prompt: 提示词
            schema: JSON Schema
            max_tokens: 最大 token 数

        Returns:
            {
                "success": true,
                "data": 结构化数据,
                "model": "模型名称"
            }
        """
        start_time = datetime.now()

        try:
            data = await self._client.generate_structured(
                prompt=prompt,
                schema=schema,
                max_tokens=max_tokens
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"Generated structured output in {execution_time:.2f}s")

            return {
                "success": True,
                "data": data,
                "model": self.model_name,
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(f"Generate structured failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }

    async def test_connection(self) -> Dict[str, Any]:
        """
        测试 API 连接

        Returns:
            {
                "success": true/false,
                "model": "模型名称",
                "base_url": "API Base URL",
                "message": "测试消息"
            }
        """
        start_time = datetime.now()

        try:
            # 发送一个简单的测试请求
            test_response = await self._client.generate_text(
                prompt="Reply with just: OK",
                max_tokens=10
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            if "OK" in test_response:
                logger.info(f"LLM API connection test successful in {execution_time:.2f}s")
                return {
                    "success": True,
                    "model": self.model_name,
                    "base_url": self.base_url,
                    "message": f"连接成功，响应时间: {execution_time:.2f}s",
                    "execution_time": execution_time
                }
            else:
                logger.warning(f"LLM API response unexpected: {test_response}")
                return {
                    "success": False,
                    "model": self.model_name,
                    "base_url": self.base_url,
                    "message": f"响应异常: {test_response}",
                    "execution_time": execution_time
                }

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_type = type(e).__name__
            error_msg = str(e)

            logger.error(f"LLM API connection test failed: {error_type}: {error_msg}")

            # 提供详细的错误信息
            if "401" in error_msg or "Unauthorized" in error_msg:
                message = "API Key 认证失败 (401)。请检查 OPENAI_API_KEY 是否正确。"
            elif "404" in error_msg or "Not Found" in error_msg:
                message = f"API 端点未找到 (404)。请检查 OPENAI_BASE_URL: {self.base_url}"
            elif "timeout" in error_msg.lower() or "Timeout" in error_type:
                message = "请求超时。请检查网络连接。"
            elif "connection" in error_msg.lower():
                message = f"无法连接到 API ({self.base_url})。请检查网络。"
            else:
                message = f"未知错误: {error_type}: {error_msg}"

            return {
                "success": False,
                "model": self.model_name,
                "base_url": self.base_url,
                "message": message,
                "error": error_msg,
                "error_type": error_type,
                "execution_time": execution_time
            }

    async def ping(self) -> bool:
        """健康检查"""
        return self._client is not None


# ============================================================================
# 服务器工厂
# ============================================================================

async def create_llm_mcp_server(
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model_name: str = "gpt-4o"
) -> LLMMCPServer:
    """
    创建 LLM MCP 服务器实例

    Args:
        api_key: OpenAI API Key
        base_url: API Base URL
        model_name: 模型名称

    Returns:
        LLM MCP 服务器实例
    """
    server = LLMMCPServer(api_key, base_url, model_name)
    await server.start()
    return server
