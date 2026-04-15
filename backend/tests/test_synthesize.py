from unittest.mock import MagicMock

import anthropic
import pytest

from pipeline.search import SearchResult
from pipeline.synthesize import synthesize_results


def make_mock_claude_response(text: str) -> MagicMock:
    message = MagicMock(spec=anthropic.types.Message)
    content_block = MagicMock()
    content_block.text = text
    message.content = [content_block]
    return message


MOCK_RESULTS = [
    SearchResult(
        query="EV battery market size",
        url="https://example.com/1",
        title="EV Market 2024",
        content="The global EV battery market was valued at $50B in 2023.",
    ),
    SearchResult(
        query="EV battery manufacturers",
        url="https://example.com/2",
        title="Top EV Battery Makers",
        content="CATL and LG Energy dominate with 60% market share.",
    ),
]

MOCK_SYNTHESIS = """## Key Findings

**Market Size:** $50B in 2023 with strong growth projected.

**Key Players:** CATL and LG Energy hold 60% combined market share.

**Coverage Gaps:** Limited data on Southeast Asian sub-markets."""


def test_synthesize_results_returns_string():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_claude_response(
        MOCK_SYNTHESIS
    )

    result = synthesize_results(MOCK_RESULTS, "EV battery market", mock_client)

    assert isinstance(result, str)
    assert len(result) > 0


def test_synthesize_results_passes_search_content_to_claude():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_claude_response(
        MOCK_SYNTHESIS
    )

    synthesize_results(MOCK_RESULTS, "EV battery market", mock_client)

    call_kwargs = mock_client.messages.create.call_args.kwargs
    user_content = str(call_kwargs["messages"])
    assert "EV Market 2024" in user_content
    assert "CATL" in user_content
