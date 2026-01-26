"""
Voting Tool Module

Responsibilities:
- Interact with blockchain contracts
- Execute voting operations
- Query voting status
"""

from dataclasses import dataclass


@dataclass
class VoteState:
    """Voting state"""
    guilty_votes: int
    not_guilty_votes: int
    total_voted: int
    voting_closed: bool
    verdict: str | None  # None if not closed


class VotingTool:
    """
    On-chain Voting Tool

    Encapsulates interactions with the JuryVoting contract.
    Uses web3.py or spoon-core's on-chain interaction capabilities.
    """

    def __init__(
        self,
        contract_address: str,
        rpc_url: str = "http://127.0.0.1:8545",
        private_keys: list[str] = None
    ):
        """
        Initialize voting tool

        Args:
            contract_address: JuryVoting contract address
            rpc_url: RPC node URL (default anvil local)
            private_keys: Juror account private keys (for vote signing)
        """
        self.contract_address = contract_address
        self.rpc_url = rpc_url
        self.private_keys = private_keys or []
        self.web3 = None
        self.contract = None

        self._init_web3()

    def _init_web3(self) -> None:
        """
        Initialize Web3 connection and contract instance
        """
        from web3 import Web3

        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))

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

        self.contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(self.contract_address),
            abi=abi
        )

    def get_vote_state(self) -> VoteState:
        """
        Get current voting state

        Returns:
            VoteState object
        """
        guilty_votes, not_guilty_votes, total_voted, voting_closed = (
            self.contract.functions.getVoteState().call()
        )
        verdict = None
        if voting_closed:
            verdict = self.contract.functions.getVerdict().call()

        return VoteState(
            guilty_votes=guilty_votes,
            not_guilty_votes=not_guilty_votes,
            total_voted=total_voted,
            voting_closed=voting_closed,
            verdict=verdict
        )

    def cast_vote(self, juror_index: int, guilty: bool) -> str:
        """
        Execute a vote

        Args:
            juror_index: Juror index (corresponds to private_keys)
            guilty: True=guilty, False=not guilty

        Returns:
            Transaction hash
        """
        if juror_index < 0 or juror_index >= len(self.private_keys):
            raise IndexError("Juror index out of range")

        private_key = self.private_keys[juror_index]
        account = self.web3.eth.account.from_key(private_key)

        tx = self.contract.functions.vote(guilty).build_transaction({
            "from": account.address,
            "nonce": self.web3.eth.get_transaction_count(account.address),
            "gas": 200000,
            "gasPrice": self.web3.eth.gas_price,
            "chainId": self.web3.eth.chain_id,
        })

        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    def cast_all_votes(self, votes: dict[str, bool]) -> list[str]:
        """
        Batch execute all juror votes

        Args:
            votes: {juror_id: guilty_bool, ...}

        Returns:
            List of transaction hashes
        """
        tx_hashes = []
        for index, guilty in enumerate(votes.values()):
            tx_hashes.append(self.cast_vote(index, guilty))
        return tx_hashes

    def close_voting(self) -> str:
        """
        Force close voting

        Returns:
            Transaction hash
        """
        if not self.private_keys:
            raise ValueError("No private keys configured")

        private_key = self.private_keys[0]
        account = self.web3.eth.account.from_key(private_key)

        tx = self.contract.functions.closeVoting().build_transaction({
            "from": account.address,
            "nonce": self.web3.eth.get_transaction_count(account.address),
            "gas": 200000,
            "gasPrice": self.web3.eth.gas_price,
            "chainId": self.web3.eth.chain_id,
        })

        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        self.web3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    def get_verdict(self) -> str:
        """
        Get final verdict

        Returns:
            "GUILTY" or "NOT_GUILTY"

        Raises:
            Exception: Voting not yet closed
        """
        return self.contract.functions.getVerdict().call()
