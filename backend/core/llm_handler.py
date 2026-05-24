"""
UST Smart Chatbot — LLM Handler Module
Provides a unified interface for Ollama, Groq, and OpenAI language models.
Supports both regular and streaming generation.
"""

import json
import logging
import httpx
from typing import AsyncGenerator, Optional

from config import (
    LLM_PROVIDER, OLLAMA_MODEL, OLLAMA_BASE_URL,
    GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL,
    OPENAI_API_KEY, OPENAI_MODEL
)

logger = logging.getLogger(__name__)


class LLMHandler:
    """Unified LLM interface supporting Ollama, Groq, and OpenAI."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or LLM_PROVIDER
        logger.info(f"LLM Handler initialized with provider: {self.provider}")

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a response from the LLM (non-streaming)."""
        if self.provider == "ollama":
            return await self._generate_ollama(prompt, system_prompt)
        elif self.provider == "groq":
            return await self._generate_groq(prompt, system_prompt)
        elif self.provider == "openai":
            return await self._generate_openai(prompt, system_prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM. Yields text chunks."""
        if self.provider == "groq":
            async for chunk in self._stream_groq(prompt, system_prompt):
                yield chunk
        elif self.provider == "ollama":
            async for chunk in self._stream_ollama(prompt, system_prompt):
                yield chunk
        elif self.provider == "openai":
            async for chunk in self._stream_openai(prompt, system_prompt):
                yield chunk
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    # ──────── Ollama ────────

    def _build_ollama_payload(self, prompt, system_prompt, stream=False):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 1024,
            }
        }

    async def _generate_ollama(self, prompt: str, system_prompt: str) -> str:
        """Generate response using Ollama (local, non-streaming)."""
        url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = self._build_ollama_payload(prompt, system_prompt, stream=False)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "").strip()
        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama. Is it running?")
            raise ConnectionError(
                "لا يمكن الاتصال بـ Ollama. تأكد من تشغيله باستخدام: ollama serve"
            )
        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            raise TimeoutError("انتهت مهلة الاستجابة. حاول مرة أخرى.")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise

    async def _stream_ollama(self, prompt: str, system_prompt: str) -> AsyncGenerator[str, None]:
        """Stream response from Ollama."""
        url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = self._build_ollama_payload(prompt, system_prompt, stream=True)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                content = data.get("message", {}).get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            raise

    # ──────── Groq (Fast Cloud) ────────

    def _build_groq_headers(self):
        return {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

    def _build_groq_payload(self, prompt, system_prompt, stream=False):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024,
            "stream": stream,
        }

    async def _generate_groq(self, prompt: str, system_prompt: str) -> str:
        """Generate response using Groq API (fast cloud, non-streaming)."""
        if not GROQ_API_KEY:
            raise ValueError("Groq API key not configured. Get one free at console.groq.com")

        payload = self._build_groq_payload(prompt, system_prompt, stream=False)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    GROQ_BASE_URL,
                    json=payload,
                    headers=self._build_groq_headers()
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            logger.error(f"Groq API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Groq error: {e}")
            raise

    async def _stream_groq(self, prompt: str, system_prompt: str) -> AsyncGenerator[str, None]:
        """Stream response from Groq API (very fast)."""
        if not GROQ_API_KEY:
            raise ValueError("Groq API key not configured")

        payload = self._build_groq_payload(prompt, system_prompt, stream=True)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST", GROQ_BASE_URL,
                    json=payload,
                    headers=self._build_groq_headers()
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Groq stream error: {e}")
            raise

    # ──────── OpenAI ────────

    async def _generate_openai(self, prompt: str, system_prompt: str) -> str:
        """Generate response using OpenAI API."""
        if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-key-here":
            raise ValueError("OpenAI API key not configured")

        url = "https://api.openai.com/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": OPENAI_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise

    async def _stream_openai(self, prompt: str, system_prompt: str) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI."""
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")

        url = "https://api.openai.com/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": OPENAI_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                content = data["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
        except Exception as e:
            logger.error(f"OpenAI stream error: {e}")
            raise

    # ──────── Health Check ────────

    async def health_check(self) -> dict:
        """Check if the LLM provider is available."""
        if self.provider == "ollama":
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                    resp.raise_for_status()
                    models = [m["name"] for m in resp.json().get("models", [])]
                    return {
                        "status": "connected",
                        "provider": "ollama",
                        "model": OLLAMA_MODEL,
                        "available_models": models,
                    }
            except Exception as e:
                return {"status": "disconnected", "provider": "ollama", "error": str(e)}

        elif self.provider == "groq":
            if not GROQ_API_KEY:
                return {"status": "not_configured", "provider": "groq", "model": GROQ_MODEL}
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        "https://api.groq.com/openai/v1/models",
                        headers={"Authorization": f"Bearer {GROQ_API_KEY}"}
                    )
                    resp.raise_for_status()
                    models = [m["id"] for m in resp.json().get("data", [])]
                    return {
                        "status": "connected",
                        "provider": "groq",
                        "model": GROQ_MODEL,
                        "available_models": models[:10],
                    }
            except Exception as e:
                return {"status": "error", "provider": "groq", "error": str(e)}

        else:
            return {
                "status": "configured" if OPENAI_API_KEY else "not_configured",
                "provider": "openai",
                "model": OPENAI_MODEL,
            }


# Global singleton
_llm_handler = None


def get_llm_handler() -> LLMHandler:
    """Get or create the global LLMHandler instance."""
    global _llm_handler
    if _llm_handler is None:
        _llm_handler = LLMHandler()
    return _llm_handler
