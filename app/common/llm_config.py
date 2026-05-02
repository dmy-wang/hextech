# coding:utf-8
"""
大模型 API 配置和管理
"""
import json
import aiohttp
from typing import Optional, List, Dict, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum

from app.common.config import cfg
from app.common.logger import logger


class LLMProvider(Enum):
    """大模型提供商"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """大模型配置"""
    provider: str = "deepseek"
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 2048
    enable_cache: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LLMConfig":
        return cls(**data)


# 预设的提供商配置
PROVIDER_PRESETS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "default_model": "deepseek-chat"
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default_model": "gpt-4o-mini"
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-3-5-haiku-20241022"],
        "default_model": "claude-sonnet-4-20250514"
    },
    "custom": {
        "base_url": "",
        "models": [],
        "default_model": ""
    }
}


class LLMClient:
    """
    大模型 API 客户端
    支持 OpenAI 兼容的 API 格式
    """

    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self._message_cache: Dict[str, str] = {}

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def start(self):
        """启动会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                }
            )

    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()

    def update_config(self, config: LLMConfig):
        """更新配置"""
        self.config = config
        # 需要重建会话
        if self.session and not self.session.closed:
            self.session._default_headers["Authorization"] = f"Bearer {config.api_key}"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user/assistant/system", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式输出

        Returns:
            模型回复内容
        """
        await self.start()

        url = f"{self.config.base_url}/chat/completions"

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "stream": stream
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error {response.status}: {error_text}")

                if stream:
                    # 流式响应处理
                    full_content = ""
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content += content
                            except json.JSONDecodeError:
                                continue
                    return full_content
                else:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]

        except aiohttp.ClientError as e:
            logger.error(f"LLM API request failed: {e}", "LLMClient")
            raise

    async def chat_with_context(
        self,
        user_message: str,
        system_prompt: str = "",
        history: List[Dict[str, str]] = None
    ) -> str:
        """
        带上下文的聊天

        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
            history: 历史对话

        Returns:
            模型回复
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        return await self.chat(messages)

    async def test_connection(self) -> bool:
        """测试 API 连接"""
        try:
            response = await self.chat(
                [{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return bool(response)
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}", "LLMClient")
            return False


# 全局 LLM 客户端实例
llm_client = LLMClient()


# BP 推荐相关的提示词模板
BP_SYSTEM_PROMPT = """你是一个英雄联盟 BP（Ban/Pick）助手专家。
你的任务是分析当前 BP 状态，为玩家提供专业的英雄推荐和战术建议。

你需要考虑以下因素：
1. 版本强势英雄（基于 OP.GG 数据）
2. 英雄克制关系
3. 阵容搭配
4. 玩家熟练度（如果有数据）

请用简洁、专业的语言给出建议，格式如下：
- 推荐英雄及理由
- 阵容分析
- 战术建议
"""

BP_BAN_PROMPT_TEMPLATE = """当前 BP 状态：
- 阶段：禁用阶段
- 己方已选：{ally_picks}
- 敌方已选：{enemy_picks}
- 己方已禁：{ally_bans}
- 敌方已禁：{enemy_bans}
- 版本强势英雄：{tier_champions}

请推荐 3 个应该禁用的英雄，并说明理由。
"""

BP_PICK_PROMPT_TEMPLATE = """当前 BP 状态：
- 阶段：选择阶段
- 需要位置：{position}
- 己方已选：{ally_picks}
- 敌方已选：{enemy_picks}
- 己方已禁：{ally_bans}
- 敌方已禁：{enemy_bans}
- 玩家擅长英雄：{player_masteries}
- 版本强势英雄（该位置）：{tier_champions}

请推荐 3-5 个应该选择的英雄，并说明理由。
"""
