"""
投票工具模块

职责：
- 与区块链合约交互
- 执行投票操作
- 查询投票状态
"""

from dataclasses import dataclass


@dataclass
class VoteState:
    """投票状态"""
    guilty_votes: int
    not_guilty_votes: int
    total_voted: int
    voting_closed: bool
    verdict: str | None  # None if not closed


class VotingTool:
    """
    链上投票工具

    封装与JuryVoting合约的交互。
    使用web3.py或spoon-core的链上交互能力。
    """

    def __init__(
        self,
        contract_address: str,
        rpc_url: str = "http://127.0.0.1:8545",
        private_keys: list[str] = None
    ):
        """
        初始化投票工具

        Args:
            contract_address: JuryVoting合约地址
            rpc_url: RPC节点URL（默认anvil本地）
            private_keys: 陪审员账户私钥列表（用于投票签名）
        """
        self.contract_address = contract_address
        self.rpc_url = rpc_url
        self.private_keys = private_keys or []
        self.web3 = None
        self.contract = None

        self._init_web3()

    def _init_web3(self) -> None:
        """
        初始化Web3连接和合约实例

        TODO:
        - from web3 import Web3
        - 连接RPC
        - 加载合约ABI
        - 创建合约实例
        """
        pass

    def get_vote_state(self) -> VoteState:
        """
        获取当前投票状态

        Returns:
            VoteState对象

        TODO:
        - 调用合约的getVoteState()
        - 如果votingClosed，调用getVerdict()
        - 封装返回
        """
        pass

    def cast_vote(self, juror_index: int, guilty: bool) -> str:
        """
        执行投票

        Args:
            juror_index: 陪审员索引（对应private_keys）
            guilty: True=有罪, False=无罪

        Returns:
            交易hash

        TODO:
        - 获取对应私钥
        - 构建交易
        - 签名并发送
        - 等待确认
        - 返回tx_hash
        """
        pass

    def cast_all_votes(self, votes: dict[str, bool]) -> list[str]:
        """
        批量执行所有陪审员投票

        Args:
            votes: {juror_id: guilty_bool, ...}

        Returns:
            交易hash列表

        TODO:
        - 遍历votes
        - 为每个陪审员调用cast_vote
        - 收集tx_hash
        """
        pass

    def close_voting(self) -> str:
        """
        强制关闭投票

        Returns:
            交易hash

        TODO:
        - 调用合约的closeVoting()
        """
        pass

    def get_verdict(self) -> str:
        """
        获取最终判决

        Returns:
            "GUILTY" 或 "NOT_GUILTY"

        Raises:
            Exception: 投票尚未结束

        TODO:
        - 调用合约的getVerdict()
        """
        pass
