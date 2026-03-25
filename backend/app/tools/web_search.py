"""Tavily web search wrapper."""
from langchain_tavily import TavilySearch

from app.config import get_tavily_api_key


def get_web_search_tool(max_results: int = 3) -> TavilySearch:
    return TavilySearch(
        max_results=max_results,
        tavily_api_key=get_tavily_api_key(),
    )
