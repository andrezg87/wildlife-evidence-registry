import asyncio

import httpx

from app.config import settings

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.6-flash:generateContent"
)

MAX_ATTEMPTS = 3


async def generate_text(prompt: str) -> str:
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"x-goog-api-key": settings.gemini_api_key}

    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(MAX_ATTEMPTS):
            try:
                response = await client.post(GEMINI_URL, json=body, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (httpx.HTTPStatusError, httpx.TimeoutException) as error:
                last_error = error
                if attempt < MAX_ATTEMPTS - 1:
                    await asyncio.sleep(2**attempt)

    raise RuntimeError(f"Gemini API failed after {MAX_ATTEMPTS} attempts") from last_error
