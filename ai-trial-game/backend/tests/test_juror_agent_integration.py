"""
JurorAgent integration smoke test.
"""
import asyncio
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.juror_agent import JurorAgent

CONTENT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "content/jurors"
)


def _has_api_key() -> bool:
    return bool(os.getenv("OPENAI_COMPATIBLE_API_KEY") or os.getenv("OPENAI_API_KEY"))


@pytest.mark.skipif(not _has_api_key(), reason="API key required for live chat")
def test_juror_agent_chat_smoke():
    agent = JurorAgent("test_juror", content_path=CONTENT_PATH)
    result = asyncio.run(agent.chat("I believe the AI should be found not guilty."))

    assert "reply" in result
    assert isinstance(result["reply"], str)
    assert result["reply"].strip()
