import os
import time
from typing import Dict, Any, Optional, Generator
from google import genai
from google.genai import types
from src.core.llm_provider import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        self.client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        
        config = None
        if system_prompt:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt
            )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        content = response.text
        usage = {
            "prompt_tokens": response.usage_metadata.prompt_token_count,
            "completion_tokens": response.usage_metadata.candidates_token_count,
            "total_tokens": response.usage_metadata.total_token_count
        }

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "google"
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        config = None
        if system_prompt:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt
            )

        response = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=config
        )
        for chunk in response:
            yield chunk.text
