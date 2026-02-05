"""
LLM Client for OpenAI API
"""
import os
import json
from typing import Dict, Any, Optional

from openai import AsyncOpenAI


class LLMClient:
    """Wrapper for OpenAI API with structured and text outputs"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def generate_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output from OpenAI.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            user_prompt
                            + "\n\nRespond ONLY with valid JSON, no explanations."
                        ),
                    },
                ],
            )

            content = response.choices[0].message.content or ""

            # Extract JSON if wrapped in fences
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            return json.loads(json_str)

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse JSON from LLM response: {e}\nContent: {content}"
            )
        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {e}")

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate free-form text from OpenAI.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            return (response.choices[0].message.content or "").strip()

        except Exception as e:
            raise RuntimeError(f"LLM text generation failed: {e}")


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

