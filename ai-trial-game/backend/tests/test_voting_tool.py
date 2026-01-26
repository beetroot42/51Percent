"""
VotingTool测试

前置条件:
- anvil运行中
- 合约已部署
- CONTRACT_ADDRESS已更新为实际地址
"""
import pytest
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.voting_tool import VotingTool, VoteState

# TODO: 替换为实际部署的合约地址
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

# anvil默认私钥
PRIVATE_KEYS = [
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
]


@pytest.fixture
def voting_tool():
    """创建VotingTool实例"""
    return VotingTool(
        contract_address=CONTRACT_ADDRESS,
        rpc_url="http://127.0.0.1:8545",
        private_keys=PRIVATE_KEYS
    )


class TestVotingToolInit:
    """Task 2.1: 初始化测试"""

    def test_init_creates_web3(self, voting_tool):
        """测试Web3初始化"""
        assert voting_tool.web3 is not None

    def test_init_creates_contract(self, voting_tool):
        """测试合约实例创建"""
        assert voting_tool.contract is not None

    def test_web3_connected(self, voting_tool):
        """测试Web3连接"""
        assert voting_tool.web3.is_connected()


class TestVotingToolState:
    """Task 2.2: 状态查询测试"""

    def test_get_vote_state_returns_votestate(self, voting_tool):
        """测试返回VoteState对象"""
        state = voting_tool.get_vote_state()
        assert isinstance(state, VoteState)

    def test_get_vote_state_has_all_fields(self, voting_tool):
        """测试VoteState包含所有字段"""
        state = voting_tool.get_vote_state()
        assert hasattr(state, 'guilty_votes')
        assert hasattr(state, 'not_guilty_votes')
        assert hasattr(state, 'total_voted')
        assert hasattr(state, 'voting_closed')


class TestVotingToolVote:
    """Task 2.2: 投票测试（会改变链上状态）"""

    @pytest.mark.skip(reason="会改变链状态，手动运行")
    def test_cast_vote(self, voting_tool):
        """测试投票"""
        tx_hash = voting_tool.cast_vote(0, True)
        assert tx_hash is not None
        assert tx_hash.startswith("0x")

    @pytest.mark.skip(reason="会改变链状态，手动运行")
    def test_cast_all_votes(self, voting_tool):
        """测试批量投票"""
        votes = {
            "juror_0": True,
            "juror_1": True,
            "juror_2": False,
        }
        tx_hashes = voting_tool.cast_all_votes(votes)
        assert len(tx_hashes) == 3
