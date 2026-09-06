import json
import os
from pathlib import Path
from typing import Dict, List

import requests

from prompt_builder import build_prompt_messages


class LLMClient:
    def __init__(self) -> None:
        self.backend = os.getenv("LLM_BACKEND", "openai").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "60"))

    def generate(self, messages: List[Dict[str, str]]) -> str:
        if self.backend == "openai":
            return self._openai(messages)
        if self.backend == "claude":
            return self._claude(messages)
        if self.backend == "ollama":
            return self._ollama(messages)
        raise ValueError(f"Unsupported backend: {self.backend}")

    def _openai(self, messages: List[Dict[str, str]]) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY in environment.")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
            json={"model": self.model, "messages": messages, "temperature": 0.8},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def _claude(self, messages: List[Dict[str, str]]) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Missing ANTHROPIC_API_KEY in environment.")
        system_prompt = ""
        converted = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = f"{system_prompt}\n{m['content']}".strip()
            else:
                converted.append({"role": m["role"], "content": m["content"]})
        resp = requests.post(
            os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages"),
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={"model": self.model, "max_tokens": 512, "system": system_prompt, "messages": converted},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()

    def _ollama(self, messages: List[Dict[str, str]]) -> str:
        endpoint = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        resp = requests.post(
            f"{endpoint}/api/chat",
            json={"model": self.model, "messages": messages, "stream": False},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "").strip()


class PersonalChatbot:
    def __init__(self, profile_path: str = "personal_profile.json") -> None:
        if not Path(profile_path).exists():
            raise FileNotFoundError(f"Profile not found: {profile_path}")
        self.profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
        self.client = LLMClient()
        self.history: List[Dict[str, str]] = []
        self.max_history_messages = 12

    def reply(self, user_input: str) -> str:
        user_input = user_input.strip()
        if not user_input:
            return ""
        messages = build_prompt_messages(self.profile, self.history, user_input)
        answer = self.client.generate(messages)
        self.history.extend(
            [{"role": "user", "content": user_input}, {"role": "assistant", "content": answer}]
        )
        if len(self.history) > self.max_history_messages:
            self.history = self.history[-self.max_history_messages :]
        return answer
