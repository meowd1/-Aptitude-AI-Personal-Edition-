import os
import aiohttp
import json
from typing import AsyncGenerator, Optional, Dict, Any

# Default to OmniRoute, but fallback to Ollama if someone wants to override
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:20128/v1")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct")

async def generate(
    prompt: str, 
    model: str = DEFAULT_MODEL, 
    system: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> str:
    """Generate a single response (non-streaming) using OpenAI compatible endpoint."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }
    
    if options:
        # OpenAI expects parameters like temperature at the top level
        for k, v in options.items():
            payload[k] = v

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{LLM_BASE_URL}/chat/completions", json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            return data["choices"][0]["message"]["content"]

async def generate_stream(
    prompt: str, 
    model: str = DEFAULT_MODEL, 
    system: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[str, None]:
    """Generate a streaming response using OpenAI compatible endpoint."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": True
    }
    
    if options:
        for k, v in options.items():
            payload[k] = v

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{LLM_BASE_URL}/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                if not line_str:
                    continue
                if line_str == "data: [DONE]":
                    break
                if line_str.startswith("data: "):
                    json_str = line_str[6:]
                    try:
                        data = json.loads(json_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        pass
