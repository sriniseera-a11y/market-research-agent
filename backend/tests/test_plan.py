from unittest.mock import MagicMock

import anthropic
import pytest

from pipeline.plan import generate_search_queries


def make_mock_claude_response(text: str) -> MagicMock:
    message = MagicMock(spec=anthropic.types.Message)
    content_block = MagicMock()
    content_block.text = text
    message.content = [content_block]
    return message


def test_generate_search_queries_returns_list():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_claude_response(
        "EV battery market size 2024\n"
        "electric vehicle battery manufacturers global\n"
        "EV battery technology trends\n"
        "lithium-ion battery supply chain\n"
        "EV battery market forecast 2030\n"
        "electric vehicle battery cost reduction\n"
    )

    queries = generate_search_queries("EV battery market", mock_client)

    assert isinstance(queries, list)
    assert 5 <= len(queries) <= 8
    for q in queries:
        assert isinstance(q, str)
        assert len(q.strip()) > 0


def test_generate_search_queries_calls_claude():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_claude_response(
        "query one\nquery two\nquery three\nquery four\nquery five\n"
    )

    generate_search_queries("test topic", mock_client)

    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-6"
    assert "test topic" in str(call_kwargs["messages"])
