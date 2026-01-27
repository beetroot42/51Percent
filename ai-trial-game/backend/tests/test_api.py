"""
FastAPI endpoint tests.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestBasicEndpoints:
    """Basic endpoint tests."""

    def test_root(self):
        """Test root path."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_get_state(self):
        """Test game state."""
        response = client.get("/state")
        assert response.status_code == 200
        data = response.json()
        assert "phase" in data


class TestJurorEndpoints:
    """Juror endpoint tests."""

    def test_get_jurors(self):
        """Test juror list."""
        response = client.get("/jurors")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.skip(reason="Enable after implementation")
    def test_get_juror(self):
        """Test single juror."""
        response = client.get("/juror/test_juror")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data

    @pytest.mark.skip(reason="Requires API key; run manually")
    def test_chat(self):
        """Test chat."""
        response = client.post(
            "/chat/test_juror",
            json={"message": "Hello"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data


class TestContentEndpoints:
    """Content endpoint tests."""

    def test_get_dossier(self):
        """Test dossier endpoint."""
        response = client.get("/content/dossier")
        assert response.status_code == 200

    def test_get_evidence_list(self):
        """Test evidence list."""
        response = client.get("/content/evidence")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_witness_list(self):
        """Test witness list."""
        response = client.get("/content/witnesses")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestPhaseEndpoints:
    """Phase switching tests."""

    @pytest.mark.skip(reason="Enable after implementation")
    def test_set_phase_investigation(self):
        """Test switching to investigation."""
        response = client.post("/phase/investigation")
        assert response.status_code == 200

    @pytest.mark.skip(reason="Enable after implementation")
    def test_set_phase_persuasion(self):
        """Test switching to persuasion."""
        response = client.post("/phase/persuasion")
        assert response.status_code == 200

    @pytest.mark.skip(reason="Enable after implementation")
    def test_set_phase_invalid(self):
        """Test invalid phase."""
        response = client.post("/phase/invalid_phase")
        assert response.status_code == 400


class TestVoteEndpoints:
    """Voting endpoint tests."""

    @pytest.mark.skip(reason="Requires contract deployment; run manually")
    def test_vote(self):
        """Test triggering vote."""
        response = client.post("/vote")
        assert response.status_code == 200
        data = response.json()
        assert "verdict" in data
