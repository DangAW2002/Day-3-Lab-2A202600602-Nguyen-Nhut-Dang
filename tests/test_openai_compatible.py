import os
import sys
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.openai_compatible_provider import OpenAICompatibleProvider

def run_mock_tests():
    print("--- Running Mock Tests for OpenAICompatibleProvider ---")
    
    # Define dummy mock classes mimicking OpenAI response structure
    class DummyUsage:
        def __init__(self):
            self.prompt_tokens = 15
            self.completion_tokens = 25
            self.total_tokens = 40

    class DummyMessage:
        def __init__(self, content):
            self.content = content

    class DummyChoice:
        def __init__(self, content):
            self.message = DummyMessage(content)

    class DummyChatCompletion:
        def __init__(self, content):
            self.choices = [DummyChoice(content)]
            self.usage = DummyUsage()

    # Mock elements for streaming
    class DummyDelta:
        def __init__(self, content):
            self.content = content

    class DummyStreamChoice:
        def __init__(self, content):
            self.delta = DummyDelta(content)

    class DummyStreamChunk:
        def __init__(self, content):
            self.choices = [DummyStreamChoice(content)]

    # We patch the OpenAI client inside our module
    with patch("src.core.openai_compatible_provider.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        
        # Configure client response for generate
        mock_client.chat.completions.create.return_value = DummyChatCompletion("This is a mock response from the compatible API.")
        
        provider = OpenAICompatibleProvider(
            model_name="dummy-model",
            base_url="http://localhost:11434/v1"
        )
        
        # Test generate
        print("\n[Testing generate()...]")
        res = provider.generate("Hello there!")
        print(f"Response: {res}")
        assert res["content"] == "This is a mock response from the compatible API."
        assert res["usage"]["prompt_tokens"] == 15
        assert res["usage"]["completion_tokens"] == 25
        assert res["usage"]["total_tokens"] == 40
        assert res["provider"] == "openai_compatible"
        print("[OK] generate() verification successful!")

        # Configure client response for stream
        mock_client.chat.completions.create.return_value = [
            DummyStreamChunk("Hello"),
            DummyStreamChunk(" world"),
            DummyStreamChunk(" from"),
            DummyStreamChunk(" compatible"),
            DummyStreamChunk(" stream!")
        ]
        
        # Test stream
        print("\n[Testing stream()...]")
        stream_chunks = list(provider.stream("Hello stream!"))
        stream_content = "".join(c["content"] for c in stream_chunks)
        print(f"Stream content: {stream_content}")
        assert stream_content == "Hello world from compatible stream!"
        print("[OK] stream() verification successful!")


def run_live_test_if_configured():
    load_dotenv()
    base_url = os.getenv("COMPATIBLE_BASE_URL")
    model_name = os.getenv("COMPATIBLE_MODEL_NAME", "phi3") # default name for local testing
    
    if not base_url:
        print("\n[INFO] Live test skipped. To run a live integration test, set COMPATIBLE_BASE_URL in your .env file.")
        print("    Example: COMPATIBLE_BASE_URL=http://localhost:11434/v1")
        return
        
    print(f"\n--- Running Live Integration Test against: {base_url} ---")
    try:
        provider = OpenAICompatibleProvider(
            model_name=model_name,
            base_url=base_url,
            provider_name="custom_local_server"
        )
        
        prompt = "Explain artificial intelligence in one simple sentence."
        print(f"Prompt: {prompt}")
        
        print("Generating non-streaming response...")
        res = provider.generate(prompt)
        print(f"Result: {res}")
        
        print("\nStreaming response:")
        print("Assistant: ", end="", flush=True)
        for chunk in provider.stream(prompt):
            print(chunk["content"], end="", flush=True)
        print("\n")
        
        print("[OK] Live integration test completed successfully!")
    except Exception as e:
        print(f"[ERROR] Error during live integration test: {e}")


if __name__ == "__main__":
    run_mock_tests()
    run_live_test_if_configured()
