import asyncio
from unittest.mock import MagicMock, patch

import pytest
from tavily import TavilyClient

from pipeline.search import SearchResult, search_all_queries


def make_mock_tavily_response(query: str) -> dict:
    return {
        "results": [
            {
                "url": f"https://example.com/{query.replace(' ', '-')}-1",
                "title": f"Result 1 for {query}",
                "content": f"Content about {query} from source 1.",
            },
            {
                "url": f"https://example.com/{query.replace(' ', '-')}-2",
                "title": f"Result 2 for {query}",
                "content": f"Content about {query} from source 2.",
            },
        ]
    }


@pytest.mark.asyncio
async def test_search_all_queries_returns_search_results():
    mock_client = MagicMock(spec=TavilyClient)
    mock_client.search.side_effect = lambda q, **kw: make_mock_tavily_response(q)

    queries = ["EV battery market size", "EV battery manufacturers"]
    results = await search_all_queries(queries, mock_client)

    assert isinstance(results, list)
    assert len(results) == 4  # 2 queries × 2 results each
    for r in results:
        assert isinstance(r, SearchResult)
        assert r.url.startswith("https://")
        assert len(r.title) > 0
        assert len(r.content) > 0
        assert r.query in queries


@pytest.mark.asyncio
async def test_search_all_queries_handles_failed_query():
    mock_client = MagicMock(spec=TavilyClient)

    def side_effect(q, **kw):
        if q == "bad query":
            raise Exception("API error")
        return make_mock_tavily_response(q)

    mock_client.search.side_effect = side_effect

    queries = ["good query", "bad query"]
    results = await search_all_queries(queries, mock_client)

    # bad query skipped, good query results returned
    assert len(results) == 2
    for r in results:
        assert r.query == "good query"
