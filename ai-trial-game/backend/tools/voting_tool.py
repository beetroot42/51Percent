"""
Voting Tool Module

Responsibilities:
- Interact with blockchain contracts
- Execute voting operations
- Query voting status
"""

import os
import time
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
    Uses web3.py with EIP-1559 fee handling for Sepolia compatibility.
    """

    def __init__(
        self,
        contract_address: str,
        rpc_url: str | None = None,
        private_keys: list[str] | None = None,
        tx_timeout: int | None = None,
        tx_confirmations: int | None = None
    ):
        """
        Initialize voting tool

        Args:
            contract_address: JuryVoting contract address
            rpc_url: RPC node URL (default from env or localhost)
            private_keys: Juror account private keys (for vote signing)
            tx_timeout: Transaction confirmation timeout in seconds
            tx_confirmations: Number of block confirmations to wait
        """
        self.contract_address = contract_address
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "http://127.0.0.1:8545")
        self.private_keys = private_keys or []
        self.tx_timeout = tx_timeout if tx_timeout is not None else int(os.getenv("VOTING_TX_TIMEOUT", "120"))
        self.tx_confirmations = (
            tx_confirmations if tx_confirmations is not None else int(os.getenv("VOTING_TX_CONFIRMATIONS", "1"))
        )
        self.web3 = None
        self.contract = None

        self._log(
            f"init rpc_url={self.rpc_url} keys={len(self.private_keys)} "
            f"tx_timeout={self.tx_timeout}s confirmations={self.tx_confirmations}"
        )
        self._init_web3()

    def _log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[VotingTool {timestamp}] {message}")

    def _init_web3(self) -> None:
        """
        Initialize Web3 connection and contract instance
        """
        from web3 import Web3

        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self._log("web3 provider initialized")

        abi = [
            {"inputs": [{"name": "_jurors", "type": "address[5]"}], "stateMutability": "nonpayable", "type": "constructor"},
            {"inputs": [{"name": "guilty", "type": "bool"}], "name": "vote", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [], "name": "getVoteState", "outputs": [{"name": "", "type": "uint256"}, {"name": "", "type": "uint256"}, {"name": "", "type": "uint256"}, {"name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "getVerdict", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "guiltyVotes", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "notGuiltyVotes", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "votingClosed", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"name": "", "type": "address"}], "name": "isJuror", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
        ]

        self.contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(self.contract_address),
            abi=abi
        )
        self._log(f"contract bound at {self.contract_address}")

    def _build_fee_params(self) -> dict:
        """
        Build EIP-1559 fee params with fallback to legacy gasPrice.
        """
        try:
            pending_block = self.web3.eth.get_block("pending")
            base_fee = pending_block.get("baseFeePerGas")
            if base_fee is None:
                raise ValueError("No baseFeePerGas")
            max_priority = self.web3.eth.max_priority_fee
            max_fee = base_fee * 2 + max_priority
            self._log("using EIP-1559 fee params")
            return {
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": max_priority,
            }
        except Exception:
            self._log("using legacy gasPrice fee params")
            return {"gasPrice": self.web3.eth.gas_price}

    def _wait_for_confirmations(self, tx_hash) -> None:
        """
        Wait for transaction receipt and optional block confirmations.
        """
        self._log(f"waiting for tx receipt (timeout={self.tx_timeout}s)")
        receipt = self.web3.eth.wait_for_transaction_receipt(
            tx_hash,
            timeout=self.tx_timeout,
        )
        if self.tx_confirmations <= 1:
            self._log("receipt confirmed (no extra confirmations)")
            return
        target_block = receipt.blockNumber + (self.tx_confirmations - 1)
        self._log(f"waiting for confirmations: target_block={target_block}")
        while True:
            latest_block = self.web3.eth.block_number
            if latest_block >= target_block:
                self._log("confirmation target reached")
                return
            time.sleep(1)

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
        self._log(f"casting vote juror_index={juror_index} address={account.address} guilty={guilty}")

        tx_params = {
            "from": account.address,
            "nonce": self.web3.eth.get_transaction_count(account.address),
            "chainId": self.web3.eth.chain_id,
        }
        tx_params.update(self._build_fee_params())

        # Estimate gas with safety margin
        gas_estimate = self.contract.functions.vote(guilty).estimate_gas(tx_params)
        tx_params["gas"] = int(gas_estimate * 1.2)
        self._log(f"gas_estimate={gas_estimate} gas_limit={tx_params['gas']}")

        tx = self.contract.functions.vote(guilty).build_transaction(tx_params)

        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
        raw_tx = getattr(signed_tx, "rawTransaction", None)
        if raw_tx is None:
            raw_tx = signed_tx.raw_transaction
        tx_hash = self.web3.eth.send_raw_transaction(raw_tx)
        self._log(f"tx sent hash={tx_hash.hex()}")
        self._wait_for_confirmations(tx_hash)
        return tx_hash.hex()

    def cast_all_votes(self, votes: dict[str, bool]) -> list[str]:
        """
        Batch execute all juror votes

        Args:
            votes: {juror_id: guilty_bool, ...}

        Returns:
            List of transaction hashes
        """
        self._log(f"batch voting start count={len(votes)}")
        tx_hashes = []
        for index, guilty in enumerate(votes.values()):
            self._log(f"batch voting juror_index={index}")
            tx_hashes.append(self.cast_vote(index, guilty))
        self._log("batch voting complete")
        return tx_hashes

    def get_verdict(self) -> str:
        """
        Get final verdict

        Returns:
            "GUILTY" or "NOT_GUILTY"

        Raises:
            Exception: Voting not yet closed
        """
        return self.contract.functions.getVerdict().call()
