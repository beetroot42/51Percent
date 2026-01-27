# Local Chain Migration Specification

**Version**: 1.0
**Date**: 2026-01-27
**Status**: Ready for Implementation

---

## 📋 Executive Summary

Migrate AI Trial Game from Sepolia testnet to Foundry Anvil local chain to achieve true DAO governance with 5 isolated jurors.

**Key Decisions**:
- Tool: Foundry Anvil
- Chain Model: Ephemeral (per-game)
- Process Model: Supervisor (start.py manages lifecycle)
- UI: Remove Etherscan links, 2s animations

---

## 🎯 Requirements

### FR-1: Local Chain Mode Detection
**CONSTRAINT**: Add explicit `MODE` configuration to `.env`

```bash
# .env
MODE=local  # or "sepolia"
```

**Logic**:
- `MODE=local` → Start Anvil + deploy contract
- `MODE=sepolia` → Connect to remote RPC (requires pre-deployed contract)

**Validation**: On startup, `start.py` must read `MODE` and error if value is invalid.

---

### FR-2: Anvil Configuration
**CONSTRAINT**: Fixed Anvil startup parameters

```bash
anvil \
  --port 8545 \
  --host 127.0.0.1 \
  --chain-id 31337 \
  --mnemonic "test test test test test test test test test test test junk" \
  --accounts 10
```

**Invariants**:
- Port must be 8545 (backend expects `RPC_URL=http://127.0.0.1:8545`)
- Host must be `127.0.0.1` (no external access)
- Mnemonic must be Anvil default (ensures deterministic accounts)
- Mining mode: instant (default, no `--block-time`)

---

### FR-3: Account Management
**CONSTRAINT**: Use Anvil default mnemonic accounts 0-5

| Role | Account Index | Address | Private Key |
|------|---------------|---------|-------------|
| Deployer | 0 | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` | `0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80` |
| Juror 1 (Chen) | 1 | `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` | `0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d` |
| Juror 2 (Liu) | 2 | `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` | `0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a` |
| Juror 3 (Wang) | 3 | `0x90F79bf6EB2c4f870365E785982E1f101E93b906` | `0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6` |
| Juror 4 (Zhang) | 4 | `0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65` | `0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a` |
| Juror 5 (Li) | 5 | `0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc` | `0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba` |

**Auto-Configuration Rule**: In `MODE=local`, `start.py` must programmatically set:

```python
os.environ["PRIVATE_KEY"] = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
os.environ["JUROR_1"] = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
os.environ["JUROR_2"] = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
os.environ["JUROR_3"] = "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
os.environ["JUROR_4"] = "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"
os.environ["JUROR_5"] = "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc"

os.environ["JURY_VOTING_PRIVATE_KEYS"] = ",".join([
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
    "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a",
    "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
])
```

**Invariant**: `JUROR_1..5` addresses must match `JURY_VOTING_PRIVATE_KEYS` derived addresses (1-to-1 by index).

---

### FR-4: Process Lifecycle Management
**CONSTRAINT**: Supervisor mode with graceful shutdown

**Current Problem**: `start.py` uses `os.execvp` (line 467), which replaces the process and orphans the Anvil subprocess.

**Required Behavior**:

```python
import subprocess
import signal
import sys

anvil_proc = None
backend_proc = None

def cleanup(signum, frame):
    print("\nShutting down...")
    if backend_proc:
        backend_proc.terminate()
        backend_proc.wait(timeout=5)
    if anvil_proc:
        anvil_proc.terminate()
        anvil_proc.wait(timeout=5)
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

anvil_proc = subprocess.Popen(["anvil", ...])
time.sleep(2)  # Wait for Anvil to initialize
deploy_contract()  # Synchronous
backend_proc = subprocess.Popen(["python", "backend/main.py"])

try:
    backend_proc.wait()
finally:
    cleanup(None, None)
```

**Invariants**:
- Ctrl+C must terminate both Anvil and backend
- Anvil must terminate within 5 seconds
- No orphaned processes

---

### FR-5: Contract Deployment
**CONSTRAINT**: Deploy only in local mode; fail fast on error

**Logic**:
```python
if MODE == "local":
    # Deploy contract using Foundry
    result = subprocess.run([
        "forge", "script",
        "script/Deploy.s.sol",
        "--rpc-url", "http://127.0.0.1:8545",
        "--private-key", os.environ["PRIVATE_KEY"],
        "--broadcast"
    ], cwd="contracts", capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Deployment failed:\n{result.stderr}")
        sys.exit(1)  # Fail fast

    # Parse contract address from output
    contract_address = parse_address_from_output(result.stdout)
    update_env("JURY_VOTING_CONTRACT_ADDRESS", contract_address)
```

**Error Handling**: If deployment fails → Exit with error code 1 (do not fall back to Agent-only mode).

---

### FR-6: Frontend UI Changes

#### FR-6.1: Remove Etherscan Links
**Files**: `frontend/js/game.js`, `frontend/index.html`

**Changes**:
1. `game.js` line ~123: Remove Etherscan URL construction
   ```javascript
   // OLD: const etherscanUrl = `https://sepolia.etherscan.io/tx/${hash}`;
   // NEW: Display hash as plain text
   verdictElement.innerHTML = `
     <h3>判决结果</h3>
     <p>${verdict === 'Not Guilty' ? '无罪' : '有罪'}</p>
     <p>交易哈希: <code>${hash}</code></p>
   `;
   ```

2. `index.html` line ~148: Update network name
   ```html
   <!-- OLD: 2. 提交区块链 (Sepolia) -->
   <!-- NEW: 2. 提交区块链 (本地链) -->
   ```

#### FR-6.2: Reduce Animation Duration
**File**: `frontend/js/game.js` line ~167

```javascript
// OLD: animateProgressBar(60, 90, 9000);
// NEW:
animateProgressBar(60, 90, 2000);  // 2 seconds for local chain
```

#### FR-6.3: Enhanced Error Handling
**File**: `frontend/js/game.js` line ~115

```javascript
// Distinguish infrastructure vs logic errors
if (error.message.includes("ECONNREFUSED") || error.message.includes("fetch failed")) {
    showError("本地链连接失败。请检查 Anvil 进程是否正在运行。");
} else {
    showError(`投票失败: ${error.message}`);
}
```

---

### FR-7: Configuration Template
**File**: `backend/.env.example`

**Add**:
```bash
# Network Mode
MODE=local  # Options: local, sepolia

# Local Chain (Anvil) - Auto-configured by start.py
RPC_URL=http://127.0.0.1:8545
JURY_VOTING_CONTRACT_ADDRESS=  # Auto-populated after deployment
JURY_VOTING_PRIVATE_KEYS=  # Auto-populated in local mode

# Sepolia (if MODE=sepolia)
# RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
# JURY_VOTING_CONTRACT_ADDRESS=0x...
# JURY_VOTING_PRIVATE_KEYS=0x...,0x...,0x...,0x...,0x...
```

---

## 🧪 Property-Based Testing Requirements

### PBT-1: Account Invariants
**Property**: Juror addresses must match private key derivations

```python
def test_juror_key_address_mapping():
    """Invariant: Each private key derives to its corresponding address"""
    for i, (addr, key) in enumerate(zip(JUROR_ADDRS, JUROR_KEYS), 1):
        derived_addr = Account.from_key(key).address
        assert derived_addr == addr, f"Juror {i} key-address mismatch"
```

### PBT-2: Process Cleanup
**Property**: No orphaned Anvil processes after shutdown

```python
def test_no_orphaned_processes():
    """Invariant: Ctrl+C must terminate all child processes"""
    start_proc = subprocess.Popen(["python", "start.py"])
    time.sleep(5)

    # Send SIGINT
    start_proc.send_signal(signal.SIGINT)
    start_proc.wait(timeout=10)

    # Verify no anvil processes remain
    anvil_procs = [p for p in psutil.process_iter(['name']) if 'anvil' in p.info['name'].lower()]
    assert len(anvil_procs) == 0, "Orphaned Anvil process detected"
```

### PBT-3: Idempotent Deployment
**Property**: Multiple deployments yield different contract addresses

```python
def test_ephemeral_chain_independence():
    """Property: Each game session has isolated contract state"""
    addr1 = deploy_and_get_address()
    restart_anvil()
    addr2 = deploy_and_get_address()

    # Addresses differ because chain state resets
    assert addr1 != addr2, "Contract addresses should differ across restarts"
```

### PBT-4: Transaction Confirmation Speed
**Property**: Local chain confirmations must be < 3 seconds

```python
def test_local_chain_speed():
    """Boundary: Local chain must confirm within 3 seconds"""
    start_time = time.time()
    tx_hash = vote_and_get_hash()
    receipt = wait_for_receipt(tx_hash)
    elapsed = time.time() - start_time

    assert elapsed < 3.0, f"Local chain too slow: {elapsed}s"
```

---

## 📦 Implementation Tasks

### Task 1: Update start.py
**File**: `start.py`

**Changes**:
1. Add `MODE` configuration reading
2. Inject Anvil default accounts in local mode
3. Replace `os.execvp` with supervisor pattern
4. Add signal handlers for graceful shutdown

**Acceptance Criteria**:
- [ ] `MODE=local` starts Anvil + deploys + runs backend
- [ ] Ctrl+C terminates all processes
- [ ] No orphaned Anvil processes

---

### Task 2: Update Frontend
**Files**: `frontend/js/game.js`, `frontend/index.html`

**Changes**:
1. Remove Etherscan link generation
2. Update network name text
3. Reduce animation duration to 2s
4. Add infrastructure error detection

**Acceptance Criteria**:
- [ ] No Etherscan URLs in verdict display
- [ ] Voting animation completes in ~2s
- [ ] Anvil connection errors show specific message

---

### Task 3: Update .env Configuration
**Files**: `backend/.env.example`

**Changes**:
1. Add `MODE` variable
2. Document local vs Sepolia configurations
3. Note auto-configuration behavior

**Acceptance Criteria**:
- [ ] Template includes `MODE=local`
- [ ] Comments explain auto-configuration

---

### Task 4: Add Tests
**Files**: `backend/tests/test_local_chain.py` (new)

**Changes**:
1. Implement PBT-1 through PBT-4
2. Add integration test for full startup flow

**Acceptance Criteria**:
- [ ] All PBT tests pass
- [ ] Integration test verifies E2E flow

---

## 🚫 Anti-Patterns to Avoid

1. **No hardcoded fallbacks**: If deployment fails, exit immediately (don't fall back to simulation)
2. **No mixed modes**: Never start Anvil when `MODE=sepolia`
3. **No orphaned processes**: Always register cleanup handlers
4. **No placeholder addresses**: Contract address must be real or error

---

## ✅ Exit Criteria

Implementation is complete when:
- [ ] All FR requirements implemented
- [ ] All PBT tests passing
- [ ] start.py supervisor mode working
- [ ] Frontend animations at 2s
- [ ] No Etherscan links remain
- [ ] Documentation updated
- [ ] User can run `python start.py` and play full game

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `start.py` | Orchestration (main changes) |
| `backend/tools/voting_tool.py` | Uses JURY_VOTING_PRIVATE_KEYS |
| `contracts/script/Deploy.s.sol` | Reads JUROR_1..5 addresses |
| `frontend/js/game.js` | UI changes (links, timing) |
| `frontend/index.html` | Text updates |
| `backend/.env.example` | Configuration template |

---

**End of Specification**
