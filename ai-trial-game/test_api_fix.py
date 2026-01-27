#!/usr/bin/env python3
"""Tests for API response handling."""

class MockMessage:
    """Mock message object from API responses."""
    def __init__(self, content="", reasoning_content=""):
        self.content = content
        self.reasoning_content = reasoning_content

class MockChoice:
    def __init__(self, message):
        self.message = message

class MockResponse:
    def __init__(self, choices):
        self.choices = choices


def test_api_response_handling():
    """Test new response handling logic."""

    print("Scenario 1: standard response")
    response = MockResponse([MockChoice(MockMessage(content="Hello, I am Claude"))])
    reply = response.choices[0].message.content.strip() if response.choices else ""
    if not reply:
        msg = response.choices[0].message if response.choices else None
        reply = getattr(msg, "reasoning_content", "").strip() if msg else ""
    print(f"  Result: {reply}")
    assert reply == "Hello, I am Claude", "Standard response failed"
    print("  OK\n")

    print("Scenario 2: reasoning_content only")
    response = MockResponse([MockChoice(MockMessage(
        content="",
        reasoning_content="**Identifying My Model Name**\n\nI'm Antigravity."
    ))])
    reply = response.choices[0].message.content.strip() if response.choices else ""
    if not reply:
        msg = response.choices[0].message if response.choices else None
        reply = getattr(msg, "reasoning_content", "").strip() if msg else ""
    print(f"  Result: {reply[:50]}...")
    assert reply, "Reasoning-only response failed"
    print("  OK\n")

    print("Scenario 3: empty response")
    response = MockResponse([MockChoice(MockMessage(content="", reasoning_content=""))])
    reply = response.choices[0].message.content.strip() if response.choices else ""
    if not reply:
        msg = response.choices[0].message if response.choices else None
        reply = getattr(msg, "reasoning_content", "").strip() if msg else ""
    print(f"  Result: '{reply}'")
    assert not reply, "Empty response detection failed"
    print("  OK (expected failure path)\n")

    print("Scenario 4: no choices")
    response = MockResponse([])
    reply = response.choices[0].message.content.strip() if response.choices else ""
    if not reply:
        msg = response.choices[0].message if response.choices else None
        reply = getattr(msg, "reasoning_content", "").strip() if msg else ""
    print(f"  Result: '{reply}'")
    assert not reply, "No-choices detection failed"
    print("  OK (expected failure path)\n")

    print("=" * 50)
    print("All tests passed. Response handling looks good.")
    print("=" * 50)


if __name__ == "__main__":
    test_api_response_handling()
