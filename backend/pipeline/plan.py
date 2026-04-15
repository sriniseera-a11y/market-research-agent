import anthropic

SYSTEM_PROMPT = """You are a market research specialist. When given a research topic, generate
6 precise web search queries that together will produce comprehensive market research coverage.

Queries should cover: market size and growth, key players and competitive landscape,
recent trends and innovations, market opportunities, challenges and risks, and regulatory environment.

Output ONLY the search queries, one per line, with no numbering, bullets, or extra text."""


def generate_search_queries(topic: str, client: anthropic.Anthropic) -> list[str]:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Generate search queries for: {topic}"}
        ],
    )
    raw = response.content[0].text.strip()
    queries = [line.strip() for line in raw.splitlines() if line.strip()]
    return queries[:8]  # cap at 8 queries
