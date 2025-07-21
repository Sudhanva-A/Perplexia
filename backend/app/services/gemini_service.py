import asyncio
import json
import google.generativeai as genai
from fastapi import HTTPException
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY) # Configure Gemini API key
model = genai.GenerativeModel("gemini-2.0-flash")

def generate_response_with_gemini_streaming(prompt: str):
    """Calls Google Gemini API and returns a streaming response."""

    response_stream = model.generate_content(
        prompt,
        stream=True,
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 3072,
            "response_mime_type": "text/plain"
        },
    )

    async def text_streamer():
        for chunk in response_stream:
            if chunk.text:
                yield f"data: {json.dumps({'type': 'answer_chunk', 'text': chunk.text})}\n\n"
            await asyncio.sleep(0.01)
    return text_streamer()