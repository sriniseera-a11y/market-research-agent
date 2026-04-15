import anthropic

from pipeline.search import SearchResult

SYSTEM_PROMPT = """You are a market research analyst. You receive raw web search results and
synthesize them into a structured research summary.

Organize your synthesis as:
- Key Findings (bullet points with data)
- Key Players mentioned
- Important trends and data points
- Coverage gaps (what wasn't well covered)

Be factual and cite which sources support each finding."""


def _format_results(results: list[SearchResult]) -> str:
    sections = []
    for r in results:
        sections.append(
            f"Source: {r.title}\nURL: {r.url}\nQuery: {r.query}\n\n{r.content}"
        )
    return "\n\n---\n\n".join(sections)


def synthesize_results(
    results: list[SearchResult],
    topic: str,
    client: anthropic.Anthropic,
) -> str:
    formatted = _format_results(results)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Topic: {topic}\n\n"
                    f"Search results to synthesize:\n\n{formatted}"
                ),
            }
        ],
    )
    if not response.content:
        raise ValueError("Claude returned empty response during synthesis")
    return response.content[0].text
