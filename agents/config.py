"""
Agent 配置管理

提供 Agent 系统的配置加载和管理
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import timedelta

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class MCPConfig:
    """MCP 配置"""
    host: str = "localhost"
    port: int = 8000
    timeout: int = 30


@dataclass
class XHSMCPConfig(MCPConfig):
    """小红书 MCP 配置"""
    auth_token: str = ""
    request_delay: float = 1.0
    max_concurrent: int = 5
    base_url: str = "https://api.tikhub.io"


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "openai"  # openai, gemini
    model_name: str = "gpt-4o"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.7
    max_tokens: int = 12000


@dataclass
class StorageConfig:
    """存储配置"""
    type: str = "file"  # file, redis
    data_dir: str = "agent_context"
    ttl_seconds: int = 3600


@dataclass
class AgentConfig:
    """单个 Agent 配置"""
    name: str
    type: str
    enabled: bool = True
    timeout: float = 300.0
    max_retries: int = 3
    retry_config: RetryConfig = field(default_factory=RetryConfig)


@dataclass
class ScraperAgentConfig(AgentConfig):
    """抓取 Agent 配置"""
    max_pages_per_keyword: int = 2
    max_posts_to_analyze: int = 20
    max_comments_per_post: int = 50


@dataclass
class OrchestratorConfig:
    """编排器配置"""
    max_parallel_tasks: int = 3
    checkpoint_interval: int = 5
    enable_fallback: bool = True
    resume_from_checkpoint: bool = True


class ConfigManager:
    """
    配置管理器

    支持从 YAML 文件、环境变量和默认值加载配置
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}

        # 首先加载 .env 文件
        self._load_dotenv()

        # 加载配置
        if config_path and Path(config_path).exists():
            self._load_from_file(config_path)
        else:
            self._config = self._get_default_config()

        # 从环境变量覆盖
        self._load_from_env()

        logger.info(f"ConfigManager initialized with {len(self._config)} sections")

    def _load_dotenv(self):
        """加载 .env 文件"""
        if DOTENV_AVAILABLE:
            # 尝试在当前目录和上级目录查找 .env 文件
            env_paths = [
                Path('.env'),
                Path('agent_system/.env'),
                Path(__file__).parent.parent / '.env',
                Path(__file__).parent / '.env',
            ]
            for env_path in env_paths:
                if env_path.exists():
                    load_dotenv(env_path)
                    logger.info(f"Loaded .env from: {env_path}")
                    return
            logger.debug("No .env file found")
        else:
            logger.debug("python-dotenv not available, skipping .env loading")

    def _load_from_file(self, config_path: str):
        """从文件加载配置"""
        path = Path(config_path)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix in ['.yml', '.yaml']:
                    self._config = yaml.safe_load(f)
                elif path.suffix == '.json':
                    self._config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {path.suffix}")

            logger.info(f"Loaded config from: {config_path}")

        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            self._config = self._get_default_config()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # XHS Token
        if 'TIKHUB_TOKEN' in os.environ:
            self._set_nested('mcp.xhs.auth_token', os.environ['TIKHUB_TOKEN'])

        # OpenAI API Key
        if 'OPENAI_API_KEY' in os.environ:
            self._set_nested('llm.api_key', os.environ['OPENAI_API_KEY'])

        # OpenAI Base URL
        if 'OPENAI_BASE_URL' in os.environ:
            self._set_nested('llm.base_url', os.environ['OPENAI_BASE_URL'])

        # Redis URL
        if 'REDIS_URL' in os.environ:
            self._set_nested('storage.redis_url', os.environ['REDIS_URL'])

        # Logging Level
        if 'LOGGING_LEVEL' in os.environ:
            self._set_nested('logging.level', os.environ['LOGGING_LEVEL'].upper())

        # Analyzer Max Posts
        if 'ANALYZER_MAX_POSTS' in os.environ:
            try:
                max_posts = int(os.environ['ANALYZER_MAX_POSTS'])
                self._set_nested('agents.scraper.max_posts_to_analyze', max_posts)
                logger.info(f"Loaded ANALYZER_MAX_POSTS from env: {max_posts}")
            except ValueError:
                logger.warning(f"Invalid ANALYZER_MAX_POSTS value: {os.environ['ANALYZER_MAX_POSTS']}")

    def _set_nested(self, key: str, value: Any):
        """设置嵌套配置值"""
        keys = key.split('.')
        current = self._config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'mcp': {
                'xhs': {
                    'host': 'localhost',
                    'port': 8001,
                    'auth_token': os.getenv('TIKHUB_TOKEN', ''),  # 安全：从环境变量读取，无硬编码默认值
                    'request_delay': 1.0,
                    'max_concurrent': 5,
                    'base_url': 'https://api.tikhub.io'
                },
                'llm': {
                    'host': 'localhost',
                    'port': 8002
                },
                'storage': {
                    'host': 'localhost',
                    'port': 8003,
                    'data_dir': 'agent_context'
                }
            },
            'llm': {
                'provider': 'openai',
                'model_name': 'gpt-5.1',
                'api_key': os.getenv('OPENAI_API_KEY', ''),
                'base_url': os.getenv('OPENAI_BASE_URL', 'https://openai.api2d.net/v1'),
                'temperature': 0.7,
                'max_tokens': 12000
            },
            'storage': {
                'type': 'file',
                'data_dir': 'agent_context',
                'ttl_seconds': 3600
            },
            'orchestrator': {
                'max_parallel_tasks': 3,
                'checkpoint_interval': 5,
                'enable_fallback': True,
                'resume_from_checkpoint': True
            },
            'agents': {
                'keyword': {
                    'name': 'keyword',
                    'type': 'keyword',
                    'enabled': True,
                    'timeout': 60.0
                },
                'scraper': {
                    'name': 'scraper',
                    'type': 'scraper',
                    'enabled': True,
                    'timeout': 300.0,
                    'max_pages_per_keyword': 2,
                    'max_posts_to_analyze': 20,
                    'max_comments_per_post': 50
                },
                'analyzer': {
                    'name': 'analyzer',
                    'type': 'analyzer',
                    'enabled': True,
                    'timeout': 600.0
                },
                'reporter': {
                    'name': 'reporter',
                    'type': 'reporter',
                    'enabled': True,
                    'timeout': 120.0
                }
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        current = self._config

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        self._set_nested(key, value)

    def get_xhs_mcp_config(self) -> XHSMCPConfig:
        """获取小红书 MCP 配置"""
        return XHSMCPConfig(
            host=self.get('mcp.xhs.host', 'localhost'),
            port=self.get('mcp.xhs.port', 8001),
            auth_token=self.get('mcp.xhs.auth_token', ''),
            request_delay=self.get('mcp.xhs.request_delay', 1.0),
            max_concurrent=self.get('mcp.xhs.max_concurrent', 5),
            base_url=self.get('mcp.xhs.base_url', 'https://api.tikhub.io')
        )

    def get_llm_config(self) -> LLMConfig:
        """获取 LLM 配置"""
        return LLMConfig(
            provider=self.get('llm.provider', 'openai'),
            model_name=self.get('llm.model_name', 'gpt-4o'),
            api_key=self.get('llm.api_key', ''),
            base_url=self.get('llm.base_url', 'https://api.openai.com/v1'),
            temperature=self.get('llm.temperature', 0.7),
            max_tokens=self.get('llm.max_tokens', 12000)
        )

    def get_storage_config(self) -> StorageConfig:
        """获取存储配置"""
        return StorageConfig(
            type=self.get('storage.type', 'file'),
            data_dir=self.get('storage.data_dir', 'agent_context'),
            ttl_seconds=self.get('storage.ttl_seconds', 3600)
        )

    def get_orchestrator_config(self) -> OrchestratorConfig:
        """获取编排器配置"""
        return OrchestratorConfig(
            max_parallel_tasks=self.get('orchestrator.max_parallel_tasks', 3),
            checkpoint_interval=self.get('orchestrator.checkpoint_interval', 5),
            enable_fallback=self.get('orchestrator.enable_fallback', True),
            resume_from_checkpoint=self.get('orchestrator.resume_from_checkpoint', True)
        )

    def get_agent_configs(self) -> Dict[str, AgentConfig]:
        """获取所有 Agent 配置"""
        agents_config = self.get('agents', {})
        result = {}

        for name, config in agents_config.items():
            agent_type = config.get('type', name)

            if agent_type == 'scraper':
                result[name] = ScraperAgentConfig(
                    name=name,
                    type=agent_type,
                    enabled=config.get('enabled', True),
                    timeout=config.get('timeout', 300.0),
                    max_pages_per_keyword=config.get('max_pages_per_keyword', 2),
                    max_posts_to_analyze=config.get('max_posts_to_analyze', 20),
                    max_comments_per_post=config.get('max_comments_per_post', 50)
                )
            else:
                result[name] = AgentConfig(
                    name=name,
                    type=agent_type,
                    enabled=config.get('enabled', True),
                    timeout=config.get('timeout', 300.0)
                )

        return result

    def save_to_file(self, path: str):
        """保存配置到文件"""
        path = Path(path)

        try:
            with open(path, 'w', encoding='utf-8') as f:
                if path.suffix in ['.yml', '.yaml']:
                    yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
                elif path.suffix == '.json':
                    json.dump(self._config, f, ensure_ascii=False, indent=2)
                else:
                    raise ValueError(f"Unsupported config format: {path.suffix}")

            logger.info(f"Saved config to: {path}")

        except Exception as e:
            logger.error(f"Failed to save config to {path}: {e}")
            raise


# ============================================================================
# 全局配置实例
# ============================================================================

_global_config: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    获取全局配置管理器实例

    Args:
        config_path: 配置文件路径

    Returns:
        配置管理器实例
    """
    global _global_config

    if _global_config is None or config_path:
        _global_config = ConfigManager(config_path)

    return _global_config


def load_config(config_path: str = None) -> ConfigManager:
    """加载配置的便捷函数"""
    return get_config(config_path)
