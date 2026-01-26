"""
FastAPI端点测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestBasicEndpoints:
    """基础端点测试"""

    def test_root(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_get_state(self):
        """测试获取游戏状态"""
        response = client.get("/state")
        assert response.status_code == 200
        data = response.json()
        assert "phase" in data


class TestJurorEndpoints:
    """陪审员端点测试"""

    def test_get_jurors(self):
        """测试获取陪审员列表"""
        response = client.get("/jurors")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.skip(reason="需要实现后测试")
    def test_get_juror(self):
        """测试获取单个陪审员"""
        response = client.get("/juror/test_juror")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data

    @pytest.mark.skip(reason="需要API Key，手动测试")
    def test_chat(self):
        """测试对话"""
        response = client.post(
            "/chat/test_juror",
            json={"message": "你好"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data


class TestContentEndpoints:
    """内容端点测试"""

    def test_get_dossier(self):
        """测试获取卷宗"""
        response = client.get("/content/dossier")
        assert response.status_code == 200

    def test_get_evidence_list(self):
        """测试获取证据列表"""
        response = client.get("/content/evidence")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_witness_list(self):
        """测试获取当事人列表"""
        response = client.get("/content/witnesses")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestPhaseEndpoints:
    """阶段切换测试"""

    @pytest.mark.skip(reason="需要实现后测试")
    def test_set_phase_investigation(self):
        """测试切换到调查阶段"""
        response = client.post("/phase/investigation")
        assert response.status_code == 200

    @pytest.mark.skip(reason="需要实现后测试")
    def test_set_phase_persuasion(self):
        """测试切换到说服阶段"""
        response = client.post("/phase/persuasion")
        assert response.status_code == 200

    @pytest.mark.skip(reason="需要实现后测试")
    def test_set_phase_invalid(self):
        """测试无效阶段"""
        response = client.post("/phase/invalid_phase")
        assert response.status_code == 400


class TestVoteEndpoints:
    """投票端点测试"""

    @pytest.mark.skip(reason="需要合约部署，手动测试")
    def test_vote(self):
        """测试触发投票"""
        response = client.post("/vote")
        assert response.status_code == 200
        data = response.json()
        assert "verdict" in data
