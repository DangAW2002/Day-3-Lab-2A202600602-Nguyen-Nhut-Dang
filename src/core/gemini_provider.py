import os
import time
from google import genai
from google.genai import types
from typing import Dict, Any, Optional, Generator, List
from src.core.llm_provider import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.0-flash", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        # Client will look for GEMINI_API_KEY env variable automatically if api_key is None
        self.client = genai.Client(api_key=self.api_key)

    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        stop: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        # Pass system prompt and stop sequences natively using GenerateContentConfig
        config = None
        if system_prompt or stop:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                stop_sequences=stop
            )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        # Get response details and token usage
        content = response.text or ""
        usage = {
            "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
            "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0
        }

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "google"
        }

    def stream(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        stop: Optional[List[str]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        config = None
        if system_prompt or stop:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                stop_sequences=stop
            )

        response_stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=config
        )
        for chunk in response_stream:
            # Safely check if Gemini returns thinking process (for newer model revisions)
            reasoning_content = None
            if hasattr(chunk, "candidates") and chunk.candidates:
                part = chunk.candidates[0].content.parts[0] if chunk.candidates[0].content.parts else None
                if part and hasattr(part, "thought") and part.thought:
                    reasoning_content = part.text
            
            if reasoning_content:
                yield {"type": "reasoning", "content": reasoning_content}
            else:
                yield {"type": "content", "content": chunk.text or ""}

