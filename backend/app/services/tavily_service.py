from tavily import TavilyClient
from fastapi import HTTPException
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def fetch_tavily_data(query: str) -> str:
    """Fetch extra topical information from Tavilly."""
    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(query=query, include_images=False)
        print(response)
        return response
    except Exception as e:
        logger.error(f"Error fetching Tavily data: {e}", exc_info=True)
        return ""