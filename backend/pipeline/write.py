import anthropic

SYSTEM_PROMPT = """You are a professional market research report writer. Write comprehensive,
well-structured market research reports in markdown format.

Your reports must include exactly these sections in this order:
1. Executive Summary (2-3 paragraphs)
2. Market Overview (size, growth rate, geography, segmentation)
3. Key Players & Competitive Landscape (major companies, market shares, strategies)
4. Trends & Opportunities (emerging trends, growth drivers, untapped segments)
5. Challenges & Risks (market barriers, threats, regulatory risks)
6. Conclusions & Recommendations (strategic takeaways, action items)

Use headers (##), bullet points, and bold text for clarity. Be specific with numbers and data."""


def write_report(synthesis: str, topic: str, client: anthropic.Anthropic) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
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
                    f"Write a market research report on: {topic}\n\n"
                    f"Based on this research synthesis:\n\n{synthesis}"
                ),
            }
        ],
    )
    if not response.content:
        raise ValueError("Claude returned empty response during report writing")
    return response.content[0].text
