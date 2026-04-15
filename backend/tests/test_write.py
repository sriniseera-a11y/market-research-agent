from unittest.mock import MagicMock

import anthropic
import pytest

from pipeline.write import write_report

MOCK_SYNTHESIS = """## Key Findings
Market valued at $50B. CATL leads with 35% share. CAGR of 18% expected through 2030."""

MOCK_REPORT = """# EV Battery Market Research Report

## Executive Summary
The global EV battery market...

## Market Overview
Valued at $50B in 2023...

## Key Players & Competitive Landscape
CATL holds 35% market share...

## Trends & Opportunities
18% CAGR expected through 2030...

## Challenges & Risks
Supply chain constraints...

## Conclusions & Recommendations
Strong growth trajectory..."""


def make_mock_claude_response(text: str) -> MagicMock:
    message = MagicMock(spec=anthropic.types.Message)
    content_block = MagicMock()
    content_block.text = text
    message.content = [content_block]
    return message


def test_write_report_returns_string():
    mock_client = MagicMock(spec=anthropic.Anthropic)
    mock_client.messages.create.return_value = make_mock_claude_response(MOCK_REPORT)

    result = write_report(MOCK_SYNTHESIS, "EV battery market", mock_client)

    assert isinstance(result, str)
    assert len(result) > 0


def test_write_report_contains_all_sections():
    mock_client = MagicMock(spec=anthropic.Anthropic)
    mock_client.messages.create.return_value = make_mock_claude_response(MOCK_REPORT)

    result = write_report(MOCK_SYNTHESIS, "EV battery market", mock_client)

    required_sections = [
        "Executive Summary",
        "Market Overview",
        "Key Players",
        "Trends",
        "Challenges",
        "Conclusions",
    ]
    for section in required_sections:
        assert section in result, f"Missing section: {section}"
