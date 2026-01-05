"""
BlueVektor Agents - LLM Management and Routing
Handles Claude API, model selection, and fallback to local LLMs.
"""
from enum import Enum
from typing import Any

import structlog
from anthropic import Anthropic
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import get_settings

logger = structlog.get_logger()


class ModelTier(str, Enum):
    """Model tiers for different task complexities."""
    REASONING = "reasoning"  # Complex analysis, strategy (Opus)
    STANDARD = "standard"    # General tasks (Sonnet)
    FAST = "fast"           # Simple tasks, high volume (Haiku)
    LOCAL = "local"         # Ollama for cost-sensitive tasks


class LLMRouter:
    """
    Routes requests to appropriate LLM based on task requirements.
    Supports Claude API (Opus, Sonnet, Haiku) and local Ollama.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._clients: dict[ModelTier, BaseChatModel] = {}
        self._anthropic_client = Anthropic(api_key=self.settings.anthropic_api_key)
        
    def get_model(
        self,
        tier: ModelTier = ModelTier.STANDARD,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> BaseChatModel:
        """
        Get a LangChain chat model for the specified tier.
        
        Args:
            tier: Model tier (reasoning, standard, fast, local)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Configured LangChain chat model
        """
        model_name = self._get_model_name(tier)
        
        if tier == ModelTier.LOCAL and self.settings.use_local_llm:
            return self._get_ollama_model(temperature, max_tokens)
        
        return ChatAnthropic(
            model=model_name,
            api_key=self.settings.anthropic_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    def _get_model_name(self, tier: ModelTier) -> str:
        """Map tier to actual model name."""
        mapping = {
            ModelTier.REASONING: self.settings.reasoning_model,
            ModelTier.STANDARD: self.settings.default_model,
            ModelTier.FAST: self.settings.fast_model,
            ModelTier.LOCAL: self.settings.ollama_model,
        }
        return mapping[tier]
    
    def _get_ollama_model(self, temperature: float, max_tokens: int) -> BaseChatModel:
        """Get Ollama model for local inference."""
        try:
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(
                model=self.settings.ollama_model,
                base_url=self.settings.ollama_url,
                temperature=temperature,
                num_predict=max_tokens,
            )
        except ImportError:
            logger.warning("Ollama not available, falling back to Haiku")
            return self.get_model(ModelTier.FAST, temperature, max_tokens)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(
        self,
        messages: list[dict[str, str]],
        tier: ModelTier = ModelTier.STANDARD,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate a response using the Anthropic API directly.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tier: Model tier to use
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Generated text response
        """
        model_name = self._get_model_name(tier)
        
        logger.info(
            "Generating response",
            model=model_name,
            tier=tier,
            num_messages=len(messages)
        )
        
        response = self._anthropic_client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "",
            messages=messages,
        )
        
        return response.content[0].text
    
    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        output_schema: type,
        tier: ModelTier = ModelTier.STANDARD,
        system: str | None = None,
    ) -> Any:
        """
        Generate a structured response that conforms to a Pydantic schema.
        
        Args:
            messages: List of message dicts
            output_schema: Pydantic model class for output
            tier: Model tier to use
            system: System prompt
            
        Returns:
            Parsed Pydantic model instance
        """
        model = self.get_model(tier)
        structured_model = model.with_structured_output(output_schema)
        
        if system:
            messages = [{"role": "system", "content": system}] + messages
            
        return await structured_model.ainvoke(messages)


# Singleton instance
_llm_router: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    """Get the global LLM router instance."""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
