"""
SpoonVotingTool - SpoonOS blockchain voting tools.

Wraps on-chain voting operations using BaseTool.
"""

from typing import ClassVar, Optional, Any
from dataclasses import dataclass

from pydantic import Field

# spoon-core imports
from spoon_ai.tools.base import BaseTool, ToolFailure


@dataclass
class VoteState:
    """Voting state."""
    guilty_votes: int
    not_guilty_votes: int
    total_voted: int
    voting_closed: bool
    verdict: str | None


class CastVoteTool(BaseTool):
    """
    On-chain voting tool.

    Extends SpoonOS BaseTool for voting transactions.
    """

    name: str = "cast_vote"
    description: str = "Cast a vote on the blockchain jury voting contract. Vote guilty or not guilty for the AI defendant."
    parameters: dict = {
        "type": "object",
        "properties": {
            "juror_index": {
                "type": "integer",
                "description": "Index of the juror (0-based, corresponds to private key index)"
            },
            "guilty": {
                "type": "boolean",
                "description": "True to vote guilty, False to vote not guilty"
            }
        },
        "required": ["juror_index", "guilty"]
    }

    # Requires decrypted private keys
    requires_decrypted_env: ClassVar[bool] = True

    # Configuration
    contract_address: str = Field(...)
    rpc_url: str = Field(default="http://127.0.0.1:8545")
    private_keys: list[str] = Field(default_factory=list)

    # Internal state (not serialized)
    _web3: Any = None
    _contract: Any = None
    _initialized: bool = False

    model_config = {"arbitrary_types_allowed": True}

    def _ensure_initialized(self) -> None:
        """Ensure Web3 is initialized."""
        if self._initialized:
            return

        from web3 import Web3

        self._web3 = Web3(Web3.HTTPProvider(self.rpc_url))

        abi = [
            {"inputs": [{"name": "_totalJurors", "type": "uint256"}], "stateMutability": "nonpayable", "type": "constructor"},
            {"inputs": [{"name": "guilty", "type": "bool"}], "name": "vote", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [], "name": "getVoteState", "outputs": [{"name": "", "type": "uint256"}, {"name": "", "type": "uint256"}, {"name": "", "type": "uint256"}, {"name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "getVerdict", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "guiltyVotes", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "notGuiltyVotes", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "votingClosed", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "closeVoting", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
        ]

        self._contract = self._web3.eth.contract(
            address=self._web3.to_checksum_address(self.contract_address),
            abi=abi
        )
        self._initialized = True

    async def execute(self, juror_index: int, guilty: bool) -> str:
        """
        Execute a vote.

        Args:
            juror_index: Juror index
            guilty: True for guilty, False for not guilty

        Returns:
            Transaction hash

        Raises:
            ToolFailure: Voting failed
        """
        self._ensure_initialized()

        if juror_index < 0 or juror_index >= len(self.private_keys):
            raise ToolFailure(f"Juror index {juror_index} out of range (0-{len(self.private_keys)-1})")

        try:
            private_key = self.private_keys[juror_index]
            account = self._web3.eth.account.from_key(private_key)

            tx = self._contract.functions.vote(guilty).build_transaction({
                "from": account.address,
                "nonce": self._web3.eth.get_transaction_count(account.address),
                "gas": 200000,
                "gasPrice": self._web3.eth.gas_price,
                "chainId": self._web3.eth.chain_id,
            })

            signed_tx = self._web3.eth.account.sign_transaction(tx, private_key)
            raw_tx = getattr(signed_tx, "rawTransaction", None) or signed_tx.raw_transaction
            tx_hash = self._web3.eth.send_raw_transaction(raw_tx)
            self._web3.eth.wait_for_transaction_receipt(tx_hash)

            vote_type = "GUILTY" if guilty else "NOT_GUILTY"
            return f"Vote cast successfully: {vote_type}, tx_hash: {tx_hash.hex()}"

        except Exception as e:
            raise ToolFailure(f"Vote cast failed: {str(e)}", cause=e)


class GetVoteStateTool(BaseTool):
    """
    Voting state query tool.

    Reads current voting state from the chain.
    """

    name: str = "get_vote_state"
    description: str = "Query current voting state from the blockchain jury contract"
    parameters: dict = {
        "type": "object",
        "properties": {},
        "required": []
    }

    # Configuration
    contract_address: str = Field(...)
    rpc_url: str = Field(default="http://127.0.0.1:8545")

    # Internal state
    _web3: Any = None
    _contract: Any = None
    _initialized: bool = False

    model_config = {"arbitrary_types_allowed": True}

    def _ensure_initialized(self) -> None:
        """Ensure Web3 is initialized."""
        if self._initialized:
            return

        from web3 import Web3

        self._web3 = Web3(Web3.HTTPProvider(self.rpc_url))

        abi = [
            {"inputs": [], "name": "getVoteState", "outputs": [{"name": "", "type": "uint256"}, {"name": "", "type": "uint256"}, {"name": "", "type": "uint256"}, {"name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "getVerdict", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
        ]

        self._contract = self._web3.eth.contract(
            address=self._web3.to_checksum_address(self.contract_address),
            abi=abi
        )
        self._initialized = True

    async def execute(self) -> dict:
        """
        Query voting state.

        Returns:
            {
                "guilty_votes": int,
                "not_guilty_votes": int,
                "total_voted": int,
                "voting_closed": bool,
                "verdict": str | None
            }
        """
        self._ensure_initialized()

        try:
            guilty_votes, not_guilty_votes, total_voted, voting_closed = (
                self._contract.functions.getVoteState().call()
            )

            verdict = None
            if voting_closed:
                verdict = self._contract.functions.getVerdict().call()

            return {
                "guilty_votes": guilty_votes,
                "not_guilty_votes": not_guilty_votes,
                "total_voted": total_voted,
                "voting_closed": voting_closed,
                "verdict": verdict
            }

        except Exception as e:
            raise ToolFailure(f"Failed to get vote state: {str(e)}", cause=e)


class CloseVotingTool(BaseTool):
    """
    Close voting tool.

    Forces voting to close on-chain.
    """

    name: str = "close_voting"
    description: str = "Force close the voting process on the blockchain"
    parameters: dict = {
        "type": "object",
        "properties": {},
        "required": []
    }

    requires_decrypted_env: ClassVar[bool] = True

    # Configuration
    contract_address: str = Field(...)
    rpc_url: str = Field(default="http://127.0.0.1:8545")
    private_keys: list[str] = Field(default_factory=list)

    # Internal state
    _web3: Any = None
    _contract: Any = None
    _initialized: bool = False

    model_config = {"arbitrary_types_allowed": True}

    def _ensure_initialized(self) -> None:
        """Ensure Web3 is initialized."""
        if self._initialized:
            return

        from web3 import Web3

        self._web3 = Web3(Web3.HTTPProvider(self.rpc_url))

        abi = [
            {"inputs": [], "name": "closeVoting", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
        ]

        self._contract = self._web3.eth.contract(
            address=self._web3.to_checksum_address(self.contract_address),
            abi=abi
        )
        self._initialized = True

    async def execute(self) -> str:
        """
        Close voting.

        Returns:
            Transaction hash
        """
        self._ensure_initialized()

        if not self.private_keys:
            raise ToolFailure("No private keys configured")

        try:
            private_key = self.private_keys[0]
            account = self._web3.eth.account.from_key(private_key)

            tx = self._contract.functions.closeVoting().build_transaction({
                "from": account.address,
                "nonce": self._web3.eth.get_transaction_count(account.address),
                "gas": 200000,
                "gasPrice": self._web3.eth.gas_price,
                "chainId": self._web3.eth.chain_id,
            })

            signed_tx = self._web3.eth.account.sign_transaction(tx, private_key)
            raw_tx = getattr(signed_tx, "rawTransaction", None) or signed_tx.raw_transaction
            tx_hash = self._web3.eth.send_raw_transaction(raw_tx)
            self._web3.eth.wait_for_transaction_receipt(tx_hash)

            return f"Voting closed successfully, tx_hash: {tx_hash.hex()}"

        except Exception as e:
            raise ToolFailure(f"Failed to close voting: {str(e)}", cause=e)
