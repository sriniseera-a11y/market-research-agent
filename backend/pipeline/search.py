import asyncio
import logging
from dataclasses import dataclass

from tavily import TavilyClient

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    query: str
    url: str
    title: str
    content: str


async def _search_single_query(
    query: str, client: TavilyClient
) -> list[SearchResult]:
    try:
        response = await asyncio.to_thread(
            client.search, query, max_results=5, search_depth="basic"
        )
        return [
            SearchResult(
                query=query,
                url=r["url"],
                title=r["title"],
                content=r.get("content", ""),
            )
            for r in response.get("results", [])
        ]
    except Exception as exc:
        logger.warning("Search failed for query %r: %s", query, exc)
        return []


async def search_all_queries(
    queries: list[str], client: TavilyClient
) -> list[SearchResult]:
    tasks = [_search_single_query(q, client) for q in queries]
    results_per_query = await asyncio.gather(*tasks)
    return [result for results in results_per_query for result in results]
