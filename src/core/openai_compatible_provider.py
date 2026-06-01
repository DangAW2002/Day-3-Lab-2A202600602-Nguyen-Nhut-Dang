import os
import time
from typing import Dict, Any, Optional, Generator, List
from openai import OpenAI
from src.core.llm_provider import LLMProvider

class OpenAICompatibleProvider(LLMProvider):
    """
    LLM Provider for OpenAI Compatible APIs (e.g., Ollama, vLLM, DeepSeek, LM Studio, etc.).
    Uses the official OpenAI Python SDK but allows overriding the base URL.
    """
    def __init__(
        self, 
        model_name: str, 
        base_url: str, 
        api_key: Optional[str] = None, 
        provider_name: str = "openai_compatible"
    ):
        # Local endpoints might not need a valid API key, but the OpenAI client expects a string.
        # Fallback to env variable or a placeholder string if not provided.
        resolved_api_key = (
            api_key 
            or os.getenv("COMPATIBLE_API_KEY") 
            or os.getenv("OPENAI_API_KEY") 
            or "fake-key-for-local-endpoint"
        )
        super().__init__(model_name, resolved_api_key)
        self.base_url = base_url
        self.provider_name = provider_name
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        stop: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stop=stop
        )

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        # Extraction from OpenAI response
        content = response.choices[0].message.content
        
        # Safely extract reasoning_content (thinking process) if available
        reasoning_content = None
        if response.choices and len(response.choices) > 0:
            message_obj = response.choices[0].message
            reasoning_content = getattr(message_obj, "reasoning_content", None)
            if not reasoning_content and hasattr(message_obj, "model_extra") and message_obj.model_extra:
                reasoning_content = message_obj.model_extra.get("reasoning_content")
        
        # Safely extract token usage (some local servers return None or don't return usage at all)
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        if response.usage:
            prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            total_tokens = getattr(response.usage, "total_tokens", 0) or 0

        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }

        return {
            "content": content,
            "reasoning_content": reasoning_content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": self.provider_name
        }

    def stream(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        stop: Optional[List[str]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
            stop=stop
        )

        for chunk in stream:
            # 1. Trích xuất reasoning_content (Thinking) nếu có trong delta chunk
            reasoning_content = None
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                reasoning_content = getattr(delta, "reasoning_content", None)
                if not reasoning_content and hasattr(delta, "model_extra") and delta.model_extra:
                    reasoning_content = delta.model_extra.get("reasoning_content")
                    
            if reasoning_content:
                yield {"type": "reasoning", "content": reasoning_content}
                
            # 2. Trích xuất content sinh ra
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield {"type": "content", "content": chunk.choices[0].delta.content}
