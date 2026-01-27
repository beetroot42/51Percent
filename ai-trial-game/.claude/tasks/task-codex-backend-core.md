# Task: Backend Core Implementation (Codex)

**Phase**: 1 - Backend Core
**Assigned to**: Codex
**Priority**: Critical
**Specification**: `local-chain-migration-spec.md`

---

## 🎯 Objective

Implement backend changes to support Anvil local chain with:
1. MODE configuration detection
2. Auto-injection of Anvil default accounts
3. Supervisor process management
4. Graceful shutdown handlers

---

## 📋 Implementation Tasks

### Task 1.1: Add MODE Configuration
**File**: `start.py`

**Requirements**:
1. Read `MODE` from `.env` (default to "local" if missing)
2. Validate MODE is either "local" or "sepolia"
3. Exit with error if invalid

**Code location**: Near line 100 (after loading .env)

**Example**:
```python
MODE = os.getenv("MODE", "local").lower()
if MODE not in ["local", "sepolia"]:
    print(f"Error: Invalid MODE '{MODE}'. Must be 'local' or 'sepolia'")
    sys.exit(1)
```

---

### Task 1.2: Anvil Account Auto-Injection
**File**: `start.py`

**Requirements**: When `MODE == "local"`, programmatically set environment variables for Anvil default accounts.

**CRITICAL CONSTRAINT**: Use exact values from specification (FR-3).

**Code location**: Before Anvil startup (around line 320)

**Implementation**:
```python
if MODE == "local":
    # Anvil default mnemonic accounts (deterministic)
    LOCAL_ACCOUNTS = {
        "PRIVATE_KEY": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        "JUROR_1": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "JUROR_2": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
        "JUROR_3": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
        "JUROR_4": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
        "JUROR_5": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc",
        "JURY_VOTING_PRIVATE_KEYS": ",".join([
            "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
            "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
            "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
            "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a",
            "0x8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
        ])
    }

    for key, value in LOCAL_ACCOUNTS.items():
        os.environ[key] = value

    print("✓ Auto-configured Anvil default accounts")
```

---

### Task 1.3: Refactor to Supervisor Pattern
**File**: `start.py`

**Current Problem**: Line 467 uses `os.execvp`, which replaces the process and orphans Anvil.

**Required Changes**:

1. **Remove `os.execvp`** (line 467)

2. **Add signal handlers** (at top of file):
```python
import signal
import sys

anvil_proc = None
backend_proc = None

def cleanup_handler(signum, frame):
    """Graceful shutdown for all child processes"""
    print("\n[start.py] Shutting down...")

    if backend_proc:
        print("[start.py] Terminating backend...")
        backend_proc.terminate()
        try:
            backend_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_proc.kill()

    if anvil_proc:
        print("[start.py] Terminating Anvil...")
        anvil_proc.terminate()
        try:
            anvil_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            anvil_proc.kill()

    print("[start.py] Cleanup complete")
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)
```

3. **Replace Anvil startup** (around line 351):
```python
# OLD: subprocess.Popen([...], shell=True, ...)
# NEW:
if MODE == "local":
    global anvil_proc
    anvil_proc = subprocess.Popen(
        [
            "anvil",
            "--port", "8545",
            "--host", "127.0.0.1",
            "--chain-id", "31337",
            "--accounts", "10"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print(f"[start.py] Anvil started (PID: {anvil_proc.pid})")
    time.sleep(2)  # Wait for initialization
```

4. **Replace backend startup** (line 467):
```python
# OLD: os.execvp(...)
# NEW:
global backend_proc
backend_proc = subprocess.Popen(
    ["python", "backend/main.py"],
    cwd=os.path.dirname(os.path.abspath(__file__))
)
print(f"[start.py] Backend started (PID: {backend_proc.pid})")

try:
    backend_proc.wait()
except KeyboardInterrupt:
    cleanup_handler(None, None)
finally:
    cleanup_handler(None, None)
```

**INVARIANT**: Ctrl+C must terminate both processes within 5 seconds.

---

### Task 1.4: Conditional Deployment
**File**: `start.py`

**Requirements**: Only deploy contract when `MODE == "local"`

**Code location**: Around line 380 (deploy_with_foundry function call)

**Implementation**:
```python
if MODE == "local":
    if foundry_available:
        deploy_with_foundry(RPC_URL)
    else:
        print("Error: MODE=local requires Foundry to be installed")
        sys.exit(1)
elif MODE == "sepolia":
    # Sepolia mode: require pre-deployed contract
    if not os.getenv("JURY_VOTING_CONTRACT_ADDRESS"):
        print("Error: MODE=sepolia requires JURY_VOTING_CONTRACT_ADDRESS in .env")
        sys.exit(1)
    print(f"✓ Using existing contract at {os.getenv('JURY_VOTING_CONTRACT_ADDRESS')}")
```

---

### Task 1.5: Update .env.example
**File**: `backend/.env.example`

**Add at top**:
```bash
# Network Mode
MODE=local  # Options: local, sepolia

# ============================================
# Local Mode Configuration (Auto-configured)
# ============================================
# When MODE=local, the following are set automatically by start.py:
# - RPC_URL=http://127.0.0.1:8545
# - JURY_VOTING_CONTRACT_ADDRESS (after deployment)
# - JURY_VOTING_PRIVATE_KEYS (Anvil accounts 1-5)
# - JUROR_1..5 addresses (Anvil accounts)
#
# DO NOT manually set these values in local mode.

# ============================================
# Sepolia Mode Configuration
# ============================================
# When MODE=sepolia, you must manually configure:
# RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
# JURY_VOTING_CONTRACT_ADDRESS=0x...
# JURY_VOTING_PRIVATE_KEYS=0x...,0x...,0x...,0x...,0x...
# JUROR_1=0x...
# JUROR_2=0x...
# JUROR_3=0x...
# JUROR_4=0x...
# JUROR_5=0x...
```

---

## ✅ Acceptance Criteria

After implementation, the following must work:

1. **Local mode startup**:
   ```bash
   python start.py
   # Should print:
   # ✓ Auto-configured Anvil default accounts
   # [start.py] Anvil started (PID: ...)
   # [start.py] Backend started (PID: ...)
   ```

2. **Graceful shutdown**:
   ```bash
   # Press Ctrl+C
   # Should print:
   # [start.py] Shutting down...
   # [start.py] Terminating backend...
   # [start.py] Terminating Anvil...
   # [start.py] Cleanup complete
   ```

3. **No orphaned processes**:
   ```bash
   # After Ctrl+C, verify:
   ps aux | grep anvil  # Should return nothing
   ```

4. **Contract deployment**:
   - In local mode: Contract auto-deploys, address saved to .env
   - In sepolia mode: Uses existing address from .env

---

## 🚫 Critical Constraints

1. **Do NOT change contract code** - Only modify `start.py` and `.env.example`
2. **Use exact private keys from FR-3** - Do not generate new accounts
3. **Fail fast on errors** - Do not fall back to simulation mode
4. **Preserve existing Sepolia mode** - Must still work with MODE=sepolia

---

## 📂 Files to Modify

| File | Changes |
|------|---------|
| `start.py` | ~150 lines modified (add MODE, accounts, supervisor) |
| `backend/.env.example` | +30 lines (MODE config docs) |

**Do NOT modify**:
- `backend/tools/voting_tool.py` (unchanged)
- `contracts/` (unchanged)
- `backend/main.py` (unchanged)

---

## 🐛 Known Issues to Fix

1. **Line 467**: Remove `os.execvp` (causes orphaned Anvil)
2. **Line 351**: Make Anvil startup conditional on MODE
3. **Missing validation**: Add MODE validation on startup

---

**Ready for Implementation**: ✅
**Specification Reference**: FR-1, FR-2, FR-3, FR-4, FR-5, FR-7
