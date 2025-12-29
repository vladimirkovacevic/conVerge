"""
OpenRouter LLM client with streaming support
"""
import json
import httpx
from typing import AsyncGenerator, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class OpenRouterClient:
    """Client for OpenRouter API with streaming support"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = os.getenv("DEFAULT_MODEL", "google/gemma-2-9b-it:free")

        # Free models to try in order
        self.free_models = [
            "meta-llama/llama-3.3-70b-instruct:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "amazon/nova-2-lite-v1:free",
            "openai/gpt-oss-20b:free",
            "google/gemma-3-27b-it:free",
            "mistralai/mistral-7b-instruct:free",
            "nvidia/nemotron-nano-9b-v2:free",
            "alibaba/tongyi-deepresearch-30b-a3b:free",
            "moonshotai/kimi-k2:free"
        ]

    async def stream_response(
        self,
        context: str,
        query: str,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM response token by token

        Args:
            context: System context/prompt
            query: User query
            model: Model to use (defaults to trying free models)

        Yields:
            Token strings as they arrive
        """
        # If specific model provided, try only that one
        # Otherwise try all free models in sequence
        models_to_try = [model] if model else self.free_models

        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": query}
        ]

        print(f"🔑 API Key (first 10 chars): {self.api_key[:10]}...")

        last_error = None

        for model_name in models_to_try:
            print(f"\n🎯 Trying model: {model_name}")
            print(f"🌐 URL: {self.base_url}/chat/completions")

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "HTTP-Referer": "https://converge.local",
                            "X-Title": "ConVerge"
                        },
                        json={
                            "model": model_name,
                            "messages": messages,
                            "stream": True
                        }
                    ) as response:
                        print(f"📡 Response status: {response.status_code}")

                        if response.status_code != 200:
                            error_body = await response.aread()
                            error_msg = error_body.decode()
                            print(f"❌ Model {model_name} failed: {error_msg}")
                            last_error = f"HTTP {response.status_code}: {error_msg}"
                            continue  # Try next model

                        print(f"✅ Model {model_name} accepted! Starting stream...")
                        response.raise_for_status()

                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()

                                # Check for end of stream
                                if data_str == "[DONE]":
                                    print(f"\n✅ Stream completed successfully with {model_name}")
                                    return

                                try:
                                    data = json.loads(data_str)
                                    if content := data.get("choices", [{}])[0].get("delta", {}).get("content"):
                                        yield content
                                except (json.JSONDecodeError, KeyError, IndexError):
                                    # Skip malformed chunks
                                    continue

                        # If we got here, streaming completed successfully
                        return

            except httpx.HTTPStatusError as e:
                print(f"❌ HTTP Error with {model_name}: {e}")
                last_error = str(e)
                continue  # Try next model
            except Exception as e:
                print(f"❌ Unexpected error with {model_name}: {e}")
                last_error = str(e)
                continue  # Try next model

        # If we exhausted all models, raise the last error
        error_msg = f"All models failed. Last error: {last_error}"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)

    async def generate_response(
        self,
        context: str,
        query: str,
        model: Optional[str] = None
    ) -> str:
        """
        Generate complete LLM response (non-streaming)

        Args:
            context: System context/prompt
            query: User query
            model: Model to use

        Returns:
            Complete response text
        """
        chunks = []
        async for chunk in self.stream_response(context, query, model):
            chunks.append(chunk)
        return "".join(chunks)


# Global client instance - lazy initialization
_llm_client = None

def get_llm_client() -> OpenRouterClient:
    """Get or create the global LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenRouterClient()
    return _llm_client

# For backwards compatibility
llm_client = property(lambda self: get_llm_client())
