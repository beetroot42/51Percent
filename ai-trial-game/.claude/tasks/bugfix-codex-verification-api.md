# Bugfix: Verification API Blocking Issue (Codex)

**Type**: Bug Fix
**Assigned to**: Codex
**Priority**: High
**Diagnosed by**: Codex + Claude

---

## Problem Description

The frontend verification panel shows endless loading spinner when fetching verification data. The `/api/votes/verification` endpoint may block indefinitely when querying blockchain data.

### Symptoms
- Verification panel shows "Verifying..." with spinner
- Spinner never stops (or takes very long)
- No error message displayed

---

## Root Cause Analysis

**Diagnosis**: The `/api/votes/verification` endpoint uses synchronous Web3 calls without timeout protection.

**Evidence** (`backend/main.py:274-314`):
```python
@app.get("/api/votes/verification")
async def get_vote_verification():
    # ...
    receipt = voting_tool.web3.eth.get_transaction_receipt(tx_hash)  # Can block
    block = voting_tool.web3.eth.get_block(receipt.blockNumber)      # Can block
    vote_state = voting_tool.get_vote_state()                        # Can block
```

**Issues**:
1. No RPC timeout configured
2. Synchronous calls in async endpoint (blocks event loop)
3. If Anvil is slow/unresponsive, request hangs indefinitely

**Secondary Issue**: `last_vote_tx_hash` may be empty if:
- Backend was restarted after voting
- Multiple workers don't share state
- Voting failed silently

---

## Required Fixes

### Fix 1: Add Timeout to Web3 Calls

**File**: `backend/main.py`

**Location**: `get_vote_verification()` function (line 274-314)

**Option A - Add request timeout wrapper**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=2)

@app.get("/api/votes/verification")
async def get_vote_verification():
    if not voting_tool:
        raise HTTPException(status_code=503, detail="Voting tool not configured")

    tx_hash = get_last_vote_tx_hash()
    if not tx_hash:
        raise HTTPException(status_code=404, detail="No vote record found")

    try:
        # Run blocking Web3 calls in thread pool with timeout
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, _fetch_verification_data, tx_hash),
            timeout=10.0  # 10 second timeout
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Blockchain query timeout")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Verification failed: {exc}") from exc


def _fetch_verification_data(tx_hash: str) -> dict:
    """Synchronous helper for Web3 calls"""
    receipt = voting_tool.web3.eth.get_transaction_receipt(tx_hash)
    block = voting_tool.web3.eth.get_block(receipt.blockNumber)
    vote_state = voting_tool.get_vote_state()
    chain_id = voting_tool.web3.eth.chain_id
    latest_block = voting_tool.web3.eth.block_number
    confirmations = max(0, latest_block - receipt.blockNumber)

    return {
        "verified": True,
        "chainData": {
            "chainId": chain_id,
            "chainName": get_chain_name(chain_id),
            "blockNumber": receipt.blockNumber,
            "blockHash": block.hash.hex(),
            "timestamp": block.timestamp,
            "txHash": tx_hash,
            "txStatus": receipt.status,
            "confirmations": confirmations,
        },
        "voteData": {
            "guiltyVotes": vote_state.guilty_votes,
            "notGuiltyVotes": vote_state.not_guilty_votes,
            "verdict": vote_state.verdict,
        },
        "contractAddress": voting_tool.contract_address,
    }
```

---

### Fix 2: Configure Web3 Request Timeout

**File**: `backend/tools/voting_tool.py`

**Location**: Web3 initialization (around line 30-50)

**Add timeout to Web3 provider**:
```python
from web3 import Web3
from web3.providers import HTTPProvider

# Configure provider with timeout
provider = HTTPProvider(
    rpc_url,
    request_kwargs={'timeout': 10}  # 10 second timeout
)
self.web3 = Web3(provider)
```

---

### Fix 3: Add Debug Logging

**File**: `backend/main.py`

**Location**: `get_vote_verification()` function

**Add logging to identify blocking point**:
```python
import logging
import time

logger = logging.getLogger(__name__)

@app.get("/api/votes/verification")
async def get_vote_verification():
    logger.info(f"Verification request started, tx_hash={get_last_vote_tx_hash()}")
    start_time = time.time()

    # ... existing code ...

    logger.info(f"get_transaction_receipt took {time.time() - start_time:.2f}s")
    # ... etc
```

---

## Acceptance Criteria

After fix, verify:

1. **Normal Case**:
   - Verification API responds within 2-3 seconds
   - Frontend displays verification data correctly

2. **Timeout Case**:
   - If Anvil is slow, API returns 504 within 10 seconds
   - Frontend shows appropriate error message

3. **No tx_hash Case**:
   - API returns 404 immediately
   - Frontend shows "No vote record found" error

4. **Anvil Down Case**:
   - API returns error within timeout period
   - Frontend shows connection error guidance

---

## Testing Steps

1. Start game normally, complete voting
2. Verify verification panel loads data quickly
3. Stop Anvil, try verification again
4. Verify timeout error appears within 10 seconds
5. Restart backend, try verification
6. Verify 404 error for missing tx_hash

---

## Files to Modify

| File | Changes |
|------|---------|
| `backend/main.py` | ~30 lines (add timeout wrapper) |
| `backend/tools/voting_tool.py` | ~5 lines (add provider timeout) |

**Do NOT modify**:
- Frontend files
- Contract files
- `start.py`

---

## Diagnostic Commands

To debug the issue:

```bash
# Check if Anvil is running
curl http://127.0.0.1:8545 -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Check last_vote_tx_hash
# Add this to main.py temporarily:
@app.get("/debug/tx_hash")
async def debug_tx_hash():
    return {"tx_hash": get_last_vote_tx_hash()}
```

---

**Ready for Implementation**: Yes
**Estimated Effort**: 30 minutes
**Risk Level**: Medium (async changes require testing)
