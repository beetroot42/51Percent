# Architecture Analysis: Local Chain Migration

**Date:** 2026-01-27
**Scope:** Migration from Sepolia Testnet to Local Chain (Anvil/Foundry) for AI Trial Game.

## 1. Problem Statement
The current system is designed for a remote testnet (Sepolia), but the requirement is to move to a local chain environment to support a "true DAO" simulation with 5 jurors, minimizing external dependencies and latency. This analysis evaluates the impact on User Experience (UX) and Developer Experience (DX).

## 2. Architecture Overview
**Current Pattern:** "Backend-as-Wallet"
- **User (Player):** Interacts via Web UI. No wallet required.
- **Backend (Python):** Holds private keys for 5 AI Jurors. Signs and broadcasts transactions.
- **Blockchain:** Currently defaults to `localhost:8545` in code, but UI references "Sepolia".

## 3. Local Chain User Experience

### 3.1. The Player's View
Since the backend manages keys, the player's experience is largely unaffected by the network switch, with two critical exceptions:
- **Transaction Speed:** Instant confirmation on local chain vs. ~15s on Sepolia. This requires adjusting UI "loading" states to feel natural (too fast might feel fake).
- **Verification (Trust):**
    - *Sepolia:* Player could click an Etherscan link to verify.
    - *Local:* The current "View on Etherscan" links in the frontend will break.
    - **Action Item:** Remove or replace Etherscan links in `frontend/index.html` and `frontend/js/game.js`.

### 3.2. RPC & Network Configuration
- **No Frontend RPC:** The frontend (`api.js`) connects *only* to the Python backend. It does not require an RPC endpoint.
- **Backend Configuration:** The Python backend requires `RPC_URL` and `JURY_VOTING_CONTRACT_ADDRESS`.

## 4. Developer/Operator Workflow (The "User" running the game)

### 4.1. Onboarding Complexity
The shift to local chain increases the setup burden for the person running the game:
- **Requirement:** Must install Foundry (or another node like Hardhat/Ganache).
- **Process:**
    1.  Start `anvil` (Local Node).
    2.  Deploy `JuryVoting.sol` to local node.
    3.  Copy new Contract Address to `.env`.
    4.  Copy Anvil's pre-funded private keys to `.env` (for Jurors).

### 4.2. Testing & Debugging
- **Pros:** Zero gas costs, instant state resets, full stack trace on reverts.
- **Cons:** Requires managing local ledger state. If Anvil restarts, the contract address in `.env` becomes invalid unless deterministic deployment is used.

## 5. Alternative Architectures

| Architecture | Description | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **A. Local Chain (Current Goal)** | Backend signs to local Anvil node. | True "DAO" logic; Fast; No external dependencies. | High setup complexity for user (needs Anvil). |
| **B. Hybrid / Sepolia** | Backend signs to public testnet. | Persistent; Easy verification via Etherscan. | Slow; Requires testnet ETH; RPC flakiness. |
| **C. Simulation (Off-chain)** | No blockchain; DB only. | Zero setup; Instant. | Not a "DAO"; "Trust me" logic. |

## 6. Recommendations

### 6.1. Simplify the "Local" Setup
To improve the Developer Experience (DX) for the user running the game:
- **Automate Startup:** Create a script (`start_local.sh` or update `start.py`) that:
    1.  Checks if `anvil` is running.
    2.  Automatically deploys the contract using a known private key (deterministic address).
    3.  Writes the address to `.env` or passes it to the backend.

### 6.2. Fix Frontend UX
- **Remove Sepolia References:** Update `frontend/js/game.js` to remove the Etherscan link when running in local mode.
- **Visual Feedback:** clearly indicate "Local Chain Mode" in the UI so the user knows votes are recorded locally.

### 6.3. Implementation Plan
1.  **Frontend:** Update `enterVerdict` in `game.js` to handle local tx hashes (don't link to Etherscan).
2.  **Backend:** Ensure `main.py` logs the connection status to the local node on startup.
3.  **Docs:** Update `README.md` with explicit "Local Chain Setup" instructions.