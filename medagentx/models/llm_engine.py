"""
LLM Engine Abstraction Layer for MedAgentX v1.7

Provides a pluggable interface for multiple LLM providers:
- OpenAI GPT (if API key in .env)
- Groq (if API key present)
- Ollama (local models)
- Anthropic Claude (claude-3.5-sonnet, claude-3-opus)
- Google Gemini (gemini-1.5-pro, gemini-1.5-flash)
- Mistral AI (mistral-large, codestral)
- Cohere (command-r, command-r+)
- Perplexity API (pplx-70b, sonar)

LLMs are optional - system must run without any LLM.
LLMs may ONLY be used for:
- Symptom normalization
- Reasoning plan generation
- Evidence summarization
- Explanation generation
- Explanation of ICD/CPT codes

All outputs must be structured (JSON) and pass through governance.
All LLM calls must be logged in AgentTrace with provider, model, purpose, and token usage.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Literal
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GROQ = "groq"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    COHERE = "cohere"
    PERPLEXITY = "perplexity"
    NONE = "none"  # No LLM (deterministic mode)


class LLMPurpose(str, Enum):
    """Allowed purposes for LLM usage."""
    SYMPTOM_NORMALIZATION = "symptom_normalization"
    REASONING_PLAN = "reasoning_plan"
    EVIDENCE_SUMMARIZATION = "evidence_summarization"
    CODE_EXPLANATION = "code_explanation"
    EXPLANATION_GENERATION = "explanation_generation"


class LLMEngine(ABC):
    """Abstract base class for LLM engines."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        purpose: LLMPurpose,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate LLM response.
        
        Args:
            prompt: User prompt
            purpose: Purpose of LLM call (for governance tracking)
            system_prompt: System prompt (optional)
            temperature: Temperature (0.0-2.0)
            max_tokens: Maximum tokens
            response_format: JSON schema for structured output (optional)
            
        Returns:
            Dict with:
                - content: Generated text
                - model: Model name used
                - usage: Token usage info
                - purpose: Purpose of call
                - structured_output: Parsed JSON if response_format provided
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if LLM is available (API key configured, etc.)."""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """Return provider name."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return model name."""
        pass


class OpenAIEngine(LLMEngine):
    """OpenAI GPT engine."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI package not installed. Install with: pip install openai")
                self._client = None
    
    async def generate(
        self,
        prompt: str,
        purpose: LLMPurpose,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Add JSON schema if provided
            if response_format:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self._client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON if response_format provided
            structured_output = None
            if response_format:
                try:
                    structured_output = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from LLM response: {content}")
            
            return {
                "content": content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                "purpose": purpose.value,
                "structured_output": structured_output,
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def is_available(self) -> bool:
        return self._client is not None and self.api_key is not None
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OPENAI
    
    @property
    def model_name(self) -> str:
        return self.model


class GroqEngine(LLMEngine):
    """Groq engine (fast inference)."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                from groq import AsyncGroq
                self._client = AsyncGroq(api_key=self.api_key)
            except ImportError:
                logger.warning("Groq package not installed. Install with: pip install groq")
                self._client = None
    
    async def generate(
        self,
        prompt: str,
        purpose: LLMPurpose,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Groq API key not configured")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON if response_format provided
            structured_output = None
            if response_format:
                try:
                    structured_output = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from LLM response: {content}")
            
            return {
                "content": content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                "purpose": purpose.value,
                "structured_output": structured_output,
            }
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    def is_available(self) -> bool:
        return self._client is not None and self.api_key is not None
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.GROQ
    
    @property
    def model_name(self) -> str:
        return self.model


class OllamaEngine(LLMEngine):
    """Ollama engine (local models)."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url
        self.model = model
        self._available = None
    
    async def generate(
        self,
        prompt: str,
        purpose: LLMPurpose,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Ollama not available. Is it running?")
        
        try:
            import aiohttp
            
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                        "stream": False,
                    },
                ) as response:
                    if response.status != 200:
                        raise ValueError(f"Ollama API error: {response.status}")
                    
                    data = await response.json()
                    content = data.get("response", "")
            
            # Try to parse as JSON if response_format provided
            structured_output = None
            if response_format:
                try:
                    structured_output = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from LLM response: {content}")
            
            return {
                "content": content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": 0,  # Ollama doesn't provide token counts
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "purpose": purpose.value,
                "structured_output": structured_output,
            }
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    async def _check_availability(self) -> bool:
        """Check if Ollama is running."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=2)) as response:
                    return response.status == 200
        except Exception:
            return False
    
    def is_available(self) -> bool:
        """Check availability (synchronous check)."""
        if self._available is None:
            # Try to check once
            try:
                import aiohttp
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                self._available = loop.run_until_complete(self._check_availability())
            except Exception:
                self._available = False
        return self._available
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OLLAMA
    
    @property
    def model_name(self) -> str:
        return self.model


class AnthropicEngine(LLMEngine):
    """Anthropic Claude engine."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("Anthropic package not installed. Install with: pip install anthropic")
                self._client = None
    
    async def generate(
        self,
        prompt: str,
        purpose: LLMPurpose,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Anthropic API key not configured")
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = await self._client.messages.create(**kwargs)
            
            content = response.content[0].text if response.content else ""
            
            # Try to parse as JSON if response_format provided
            structured_output = None
            if response_format:
                try:
                    structured_output = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from LLM response: {content}")
            
            return {
                "content": content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                    "completion_tokens": response.usage.output_tokens if response.usage else 0,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
                },
                "purpose": purpose.value,
                "structured_output": structured_output,
            }
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def is_available(self) -> bool:
        return self._client is not None and self.api_key is not None
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.ANTHROPIC
    
    @property
    def model_name(self) -> str:
        return self.model


class GoogleEngine(LLMEngine):
    """Google Gemini engine."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-pro"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
            except ImportError:
                logger.warning("Google Generative AI package not installed. Install with: pip install google-generativeai")
                self._client = None
    
    async def generate(
        self,
        prompt: str,
        purpose: LLMPurpose,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Google API key not configured")
        
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Gemini uses synchronous API, so we need to run in executor
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    }
                )
            )
            
            content = response.text if hasattr(response, 'text') else ""
            
            # Try to parse as JSON if response_format provided
            structured_output = None
            if response_format:
                try:
                    structured_output = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from LLM response: {content}")
            
            # Gemini doesn't provide token usage in the same way
            return {
                "content": content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": 0,  # Not available from Gemini API
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "purpose": purpose.value,
                "structured_output": structured_output,
            }
        except Exception as e:
            logger.error(f"Google API error: {e}")
            raise
    
    def is_available(self) -> bool:
        return self._client is not None and self.api_key is not None
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.GOOGLE
    
    @property
    def model_name(self) -> str:
        return self.model


class MistralEngine(LLMEngine):
    """Mistral AI engine."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-large-latest"):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                from mistralai import Mistral
                self._client = Mistral(api_key=self.api_key)
            except ImportError:
                logger.warning("Mistral package not installed. Install with: pip install mistralai")
                self._client = None
    
    async def generate(
        self,
        prompt: str,
        purpose: LLMPurpose,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Mistral API key not configured")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Mistral uses synchronous API
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.chat.complete(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )
            
            content = response.choices[0].message.content if response.choices else ""
            
            # Try to parse as JSON if response_format provided
            structured_output = None
            if response_format:
                try:
                    structured_output = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from LLM response: {content}")
            
            return {
                "content": content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') and response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if hasattr(response, 'usage') and response.usage else 0,
                    "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 0,
                },
                "purpose": purpose.value,
                "structured_output": structured_output,
            }
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            raise
    
    def is_available(self) -> bool:
        return self._client is not None and self.api_key is not None
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.MISTRAL
    
    @property
    def model_name(self) -> str:
        return self.model


class CohereEngine(LLMEngine):
    """Cohere engine."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "command-r-plus"):
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                import cohere
                self._client = cohere.AsyncClient(api_key=self.api_key)
            except ImportError:
                logger.warning("Cohere package not installed. Install with: pip install cohere")
                self._client = None
    
    async def generate(
        self,
        prompt: str,
        purpose: LLMPurpose,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Cohere API key not configured")
        
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = await self._client.chat(
                model=self.model,
                message=full_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            content = response.text if hasattr(response, 'text') else ""
            
            # Try to parse as JSON if response_format provided
            structured_output = None
            if response_format:
                try:
                    structured_output = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from LLM response: {content}")
            
            return {
                "content": content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.meta.billed_units.input_tokens if hasattr(response, 'meta') and hasattr(response.meta, 'billed_units') else 0,
                    "completion_tokens": response.meta.billed_units.output_tokens if hasattr(response, 'meta') and hasattr(response.meta, 'billed_units') else 0,
                    "total_tokens": (response.meta.billed_units.input_tokens + response.meta.billed_units.output_tokens) if hasattr(response, 'meta') and hasattr(response.meta, 'billed_units') else 0,
                },
                "purpose": purpose.value,
                "structured_output": structured_output,
            }
        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            raise
    
    def is_available(self) -> bool:
        return self._client is not None and self.api_key is not None
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.COHERE
    
    @property
    def model_name(self) -> str:
        return self.model


class PerplexityEngine(LLMEngine):
    """Perplexity API engine."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "pplx-70b-online"):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                # Perplexity uses OpenAI-compatible API
                self._client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.perplexity.ai")
            except ImportError:
                logger.warning("OpenAI package not installed. Install with: pip install openai")
                self._client = None
    
    async def generate(
        self,
        prompt: str,
        purpose: LLMPurpose,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_available():
            raise ValueError("Perplexity API key not configured")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Add JSON schema if provided
            if response_format:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self._client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON if response_format provided
            structured_output = None
            if response_format:
                try:
                    structured_output = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from LLM response: {content}")
            
            return {
                "content": content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                "purpose": purpose.value,
                "structured_output": structured_output,
            }
        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            raise
    
    def is_available(self) -> bool:
        return self._client is not None and self.api_key is not None
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.PERPLEXITY
    
    @property
    def model_name(self) -> str:
        return self.model


class NullLLMEngine(LLMEngine):
    """Null LLM engine (no LLM, deterministic mode)."""
    
    async def generate(
        self,
        prompt: str,
        purpose: LLMPurpose,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return empty response (deterministic mode)."""
        return {
            "content": "",
            "model": "none",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "purpose": purpose.value,
            "structured_output": None,
        }
    
    def is_available(self) -> bool:
        return True
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.NONE
    
    @property
    def model_name(self) -> str:
        return "none"


class LLMEngineFactory:
    """Factory for creating LLM engines."""
    
    @staticmethod
    def create(provider: LLMProvider, **kwargs) -> LLMEngine:
        """
        Create LLM engine for specified provider.
        
        Args:
            provider: LLM provider
            **kwargs: Provider-specific arguments
            
        Returns:
            LLMEngine instance
        """
        if provider == LLMProvider.OPENAI:
            return OpenAIEngine(**kwargs)
        elif provider == LLMProvider.GROQ:
            return GroqEngine(**kwargs)
        elif provider == LLMProvider.OLLAMA:
            return OllamaEngine(**kwargs)
        elif provider == LLMProvider.ANTHROPIC:
            return AnthropicEngine(**kwargs)
        elif provider == LLMProvider.GOOGLE:
            return GoogleEngine(**kwargs)
        elif provider == LLMProvider.MISTRAL:
            return MistralEngine(**kwargs)
        elif provider == LLMProvider.COHERE:
            return CohereEngine(**kwargs)
        elif provider == LLMProvider.PERPLEXITY:
            return PerplexityEngine(**kwargs)
        elif provider == LLMProvider.NONE:
            return NullLLMEngine()
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> LLMEngine:
        """
        Create LLM engine from configuration dict.
        
        Args:
            config: Dict with 'provider' and optional provider-specific keys
            
        Returns:
            LLMEngine instance
        """
        provider_str = config.get("provider", "none")
        try:
            provider = LLMProvider(provider_str)
        except ValueError:
            logger.warning(f"Unknown provider '{provider_str}', using NONE")
            provider = LLMProvider.NONE
        
        kwargs = {k: v for k, v in config.items() if k != "provider"}
        return LLMEngineFactory.create(provider, **kwargs)
    
    @staticmethod
    def get_available_providers() -> List[LLMProvider]:
        """Get list of available LLM providers."""
        available = [LLMProvider.NONE]  # Always available
        
        # Check OpenAI
        if os.getenv("OPENAI_API_KEY"):
            try:
                engine = OpenAIEngine()
                if engine.is_available():
                    available.append(LLMProvider.OPENAI)
            except Exception:
                pass
        
        # Check Groq
        if os.getenv("GROQ_API_KEY"):
            try:
                engine = GroqEngine()
                if engine.is_available():
                    available.append(LLMProvider.GROQ)
            except Exception:
                pass
        
        # Check Ollama (async check, so we'll just add it if base_url is accessible)
        try:
            engine = OllamaEngine()
            if engine.is_available():
                available.append(LLMProvider.OLLAMA)
        except Exception:
            pass
        
        # Check Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                engine = AnthropicEngine()
                if engine.is_available():
                    available.append(LLMProvider.ANTHROPIC)
            except Exception:
                pass
        
        # Check Google
        if os.getenv("GOOGLE_API_KEY"):
            try:
                engine = GoogleEngine()
                if engine.is_available():
                    available.append(LLMProvider.GOOGLE)
            except Exception:
                pass
        
        # Check Mistral
        if os.getenv("MISTRAL_API_KEY"):
            try:
                engine = MistralEngine()
                if engine.is_available():
                    available.append(LLMProvider.MISTRAL)
            except Exception:
                pass
        
        # Check Cohere
        if os.getenv("COHERE_API_KEY"):
            try:
                engine = CohereEngine()
                if engine.is_available():
                    available.append(LLMProvider.COHERE)
            except Exception:
                pass
        
        # Check Perplexity
        if os.getenv("PERPLEXITY_API_KEY"):
            try:
                engine = PerplexityEngine()
                if engine.is_available():
                    available.append(LLMProvider.PERPLEXITY)
            except Exception:
                pass
        
        return available

