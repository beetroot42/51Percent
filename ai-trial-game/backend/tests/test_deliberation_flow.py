"""
Deliberation integration tests (requires live backend).
"""
import pytest


pytestmark = pytest.mark.skip(reason="requires live backend and SSE runtime")


def test_full_4_round_flow():
    pass


def test_skip_deliberation():
    pass


def test_note_injection_affects_speech():
    pass


def test_sse_event_ordering():
    pass

