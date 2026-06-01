import time
from typing import Dict, Any, List
from src.telemetry.logger import logger

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to our telemetry.
        """
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(model, usage) # Mock cost calculation
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        Implement real pricing logic based on standard model pricing.
        """
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        model_lower = model.lower()
        if "gemini" in model_lower:
            # Gemini 1.5 Flash pricing: $0.075/1M input, $0.30/1M output
            input_rate = 0.075 / 1_000_000
            output_rate = 0.30 / 1_000_000
        elif "gpt-4o-mini" in model_lower:
            # GPT-4o-mini pricing: $0.150/1M input, $0.600/1M output
            input_rate = 0.150 / 1_000_000
            output_rate = 0.600 / 1_000_000
        elif "gpt-4o" in model_lower:
            # GPT-4o pricing: $5.00/1M input, $15.00/1M output
            input_rate = 5.00 / 1_000_000
            output_rate = 15.00 / 1_000_000
        elif "local" in model_lower or "phi" in model_lower or model_lower.endswith(".gguf"):
            # Local offline models are free to run
            return 0.0
        else:
            # Fallback estimation
            input_rate = 0.150 / 1_000_000
            output_rate = 0.600 / 1_000_000
            
        return (prompt_tokens * input_rate) + (completion_tokens * output_rate)

# Global tracker instance
tracker = PerformanceTracker()
