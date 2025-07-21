import requests
from fastapi import HTTPException
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_embedding(text: str) -> list:
    """Generates embeddings using Jina AI."""
    url = "https://api.jina.ai/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.JINAAI_API_KEY}"
    }
    payload = {
        "input": [text],
        "model": "jina-embeddings-v2-base-en"
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        if "data" in data and data["data"]:
            return data["data"][0]["embedding"]
        else:
            raise HTTPException(status_code=500, detail="No embeddings returned from Jina AI API.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Jina AI API request failed: {str(e)}")