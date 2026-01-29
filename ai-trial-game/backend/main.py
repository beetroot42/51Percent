"""
AI Trial Game - Backend API

Provides REST interface using FastAPI.
"""

import asyncio
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Windows encoding guard: keep UTF-8 output stable
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv

# Load backend/.env explicitly so it works from any working directory
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

# Ensure backend-local imports work when launched via uvicorn
sys.path.append(str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from services.agent_manager import AgentManager
from tools.voting_tool import VotingTool

app = FastAPI(title="AI Trial Game", version="0.1.0")
logger = logging.getLogger(__name__)
_verification_executor = ThreadPoolExecutor(max_workers=2)

# CORS configuration (allow frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Request/Response Models ============

class ChatRequest(BaseModel):
    """Chat request"""
    message: str


class ToolAction(BaseModel):
    """Tool action record"""
    tool: str
    input: dict
    result_summary: str = ""
    narrative: str = ""


class ChatResponse(BaseModel):
    """Chat response"""
    reply: str
    juror_id: str
    tool_actions: list[ToolAction] = Field(default_factory=list)
    has_voted: bool = False


class VoteResponse(BaseModel):
    """Vote response"""
    guilty_votes: int
    not_guilty_votes: int
    verdict: str
    tx_hashes: list[str]

class VerifyVoteRequest(BaseModel):
    """Verify vote request"""
    txHash: str


class GameState(BaseModel):
    """Game state"""
    phase: str  # investigation / persuasion / verdict
    jurors: list[dict]
    vote_state: dict | None


# ============ Global State ============

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = PROJECT_ROOT / "content"
JUROR_CONTENT = CONTENT_ROOT / "jurors"

game_phase = "investigation"

_contract_address = os.getenv(
    "JURY_VOTING_CONTRACT_ADDRESS",
    "0x5FbDB2315678afecb367f032d93F642f64180aa3"
)
_rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
_private_keys = os.getenv("JURY_VOTING_PRIVATE_KEYS", "")
_private_key_list = [key.strip() for key in _private_keys.split(",") if key.strip()]
_tx_timeout = int(os.getenv("VOTING_TX_TIMEOUT", "120"))
_tx_confirmations = int(os.getenv("VOTING_TX_CONFIRMATIONS", "1"))

_voting_config = {
    "contract_address": _contract_address,
    "rpc_url": _rpc_url,
    "private_keys": _private_key_list,
} if _contract_address and _private_key_list else None

agent_manager = AgentManager(voting_config=_voting_config)
agent_manager.load_all_jurors(content_path=str(JUROR_CONTENT))
voting_tool = VotingTool(
    contract_address=_contract_address,
    rpc_url=_rpc_url,
    private_keys=_private_key_list,
    tx_timeout=_tx_timeout,
    tx_confirmations=_tx_confirmations
) if _contract_address else None

last_vote_tx_hash: str | None = None

def get_last_vote_tx_hash() -> str | None:
    """Get the most recent vote transaction hash."""
    return last_vote_tx_hash

def get_chain_name(chain_id: int) -> str:
    """Map chain id to friendly name."""
    chain_names = {
        31337: "Anvil Local",
        11155111: "Sepolia Testnet",
        1: "Ethereum Mainnet",
    }
    return chain_names.get(chain_id, f"Unknown Chain ({chain_id})")


def _fetch_verification_data(tx_hash: str) -> dict:
    """Synchronous helper for Web3 calls."""
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
# ============ API Endpoints ============

@app.get("/")
async def serve_root():
    """Serve the root page (frontend)"""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
async def health_check():
    """Health check"""
    return {"status": "ok", "game": "AI Trial"}


@app.get("/state", response_model=GameState)
async def get_game_state():
    """
    Get current game state

    Returns:
        GameState object

    """
    vote_state = None
    if game_phase == "verdict":
        vote_state = agent_manager.collect_votes()

    return GameState(
        phase=game_phase,
        jurors=agent_manager.get_all_juror_info(),
        vote_state=vote_state
    )


@app.post("/phase/{phase_name}")
async def set_phase(phase_name: str):
    """
    Switch game phase

    Args:
        phase_name: investigation / persuasion / verdict

    """
    valid_phases = {"investigation", "persuasion", "verdict"}
    if phase_name not in valid_phases:
        raise HTTPException(status_code=400, detail="Invalid phase")

    global game_phase
    game_phase = phase_name

    return {"phase": game_phase}


@app.get("/jurors")
async def get_jurors():
    """
    Get all juror information

    Returns:
        [{"id": str, "name": str}, ...]

    """
    return agent_manager.get_all_juror_info()


@app.get("/juror/{juror_id}")
async def get_juror(juror_id: str):
    """
    Get specific juror information

    Args:
        juror_id: Juror ID

    Returns:
        {"id": str, "name": str, "first_message": str}

    """
    try:
        agent = agent_manager.get_juror(juror_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "id": agent.juror_id,
        "name": agent.config.name if agent.config else "",
        "first_message": agent.get_first_message(),
    }


@app.post("/chat/{juror_id}", response_model=ChatResponse)
async def chat_with_juror(juror_id: str, request: ChatRequest):
    """
    Chat with a juror

    Args:
        juror_id: Juror ID
        request: Request body containing message

    Returns:
        ChatResponse

    """
    if game_phase != "persuasion":
        raise HTTPException(status_code=400, detail="Not in persuasion phase")

    try:
        response = await agent_manager.chat_with_juror(juror_id, request.message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc

    return ChatResponse(
        reply=response["reply"],
        juror_id=response["juror_id"],
        tool_actions=response.get("tool_actions", []),
        has_voted=response.get("has_voted", False)
    )


@app.post("/vote", response_model=VoteResponse)
async def trigger_vote():
    """
    Trigger voting

    Collect all juror stances and execute on-chain voting.

    Returns:
        VoteResponse

    """
    if voting_tool is None:
        raise HTTPException(status_code=500, detail="Voting tool not configured")
    if not _private_key_list:
        raise HTTPException(status_code=500, detail="No juror private keys configured")

    vote_result = agent_manager.collect_votes()
    votes = {
        juror_id: (vote_data["vote"] == "GUILTY")
        for juror_id, vote_data in vote_result["votes"].items()
    }
    try:
        tx_hashes = voting_tool.cast_all_votes(votes)
        global last_vote_tx_hash
        last_vote_tx_hash = tx_hashes[0] if tx_hashes else None
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Voting failed: {exc}") from exc

    return VoteResponse(
        guilty_votes=vote_result["guilty_count"],
        not_guilty_votes=vote_result["not_guilty_count"],
        verdict=vote_result["verdict"],
        tx_hashes=tx_hashes
    )


@app.get("/api/votes/verification")
async def get_vote_verification():
    """
    Get verification info for the most recent vote transaction.
    """
    if not voting_tool:
        raise HTTPException(status_code=503, detail="Voting tool not configured")

    tx_hash = get_last_vote_tx_hash()
    if not tx_hash:
        raise HTTPException(status_code=404, detail="No vote record found")

    try:
        logger.info("verification request started tx_hash=%s", tx_hash)
        start_time = time.monotonic()
        loop = asyncio.get_running_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(_verification_executor, _fetch_verification_data, tx_hash),
            timeout=10.0,
        )
        logger.info("verification request finished duration=%.2fs", time.monotonic() - start_time)
        return result
    except asyncio.TimeoutError as exc:
        logger.warning("verification request timed out tx_hash=%s", tx_hash)
        raise HTTPException(status_code=504, detail="Blockchain query timeout") from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Verification failed: {exc}") from exc


@app.post("/api/votes/verify")
async def verify_vote(request: VerifyVoteRequest):
    """
    Re-verify vote results by tx hash.
    """
    if not voting_tool:
        raise HTTPException(status_code=503, detail="Voting tool not configured")

    tx_hash = request.txHash
    if not tx_hash:
        raise HTTPException(status_code=400, detail="txHash is required")

    try:
        receipt = voting_tool.web3.eth.get_transaction_receipt(tx_hash)
        logs = voting_tool.contract.events.VotingClosed().process_receipt(receipt)
        if not logs:
            raise HTTPException(status_code=404, detail="No VotingClosed event found")

        event_data = logs[0]["args"]
        vote_state = voting_tool.get_vote_state()

        mismatches = []
        if event_data["guiltyVotes"] != vote_state.guilty_votes:
            mismatches.append(
                f"Guilty votes mismatch: event={event_data['guiltyVotes']}, state={vote_state.guilty_votes}"
            )
        if event_data["notGuiltyVotes"] != vote_state.not_guilty_votes:
            mismatches.append(
                f"Not guilty votes mismatch: event={event_data['notGuiltyVotes']}, state={vote_state.not_guilty_votes}"
            )

        return {"verified": len(mismatches) == 0, "mismatches": mismatches}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Verification failed: {exc}") from exc


@app.get("/api/blockchain/genesis")
async def get_genesis_block():
    """
    Get genesis block hash for chain reset detection.
    """
    if not voting_tool:
        raise HTTPException(status_code=503, detail="Voting tool not configured")

    try:
        genesis_block = voting_tool.web3.eth.get_block(0)
        return {
            "genesisBlockHash": genesis_block.hash.hex(),
            "chainId": voting_tool.web3.eth.chain_id,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to get genesis block: {exc}") from exc


@app.post("/reset")
async def reset_game():
    """
    Reset game

    """
    global game_phase
    agent_manager.reset_all()
    game_phase = "investigation"
    return {"status": "reset", "phase": game_phase}


# ============ Static Content Endpoints ============

@app.get("/content/dossier")
async def get_dossier():
    """
    Get dossier content

    Returns:
        {"title": str, "content": str}

    """
    dossier_path = CONTENT_ROOT / "case" / "dossier.json"
    if not dossier_path.exists():
        raise HTTPException(status_code=404, detail="Dossier not found")

    return json.loads(dossier_path.read_text(encoding="utf-8"))


@app.get("/content/evidence")
async def get_evidence_list():
    """
    Get evidence list

    Returns:
        [{"id": str, "name": str, "icon": str}, ...]

    """
    evidence_dir = CONTENT_ROOT / "case" / "evidence"
    if not evidence_dir.exists():
        return []

    evidence_list = []
    for path in sorted(evidence_dir.glob("*.json")):
        if path.name == "_template.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        evidence_list.append({
            "id": data.get("id", path.stem),
            "name": data.get("name", path.stem),
            "icon": data.get("icon", "")
        })
    return evidence_list


@app.get("/content/evidence/{evidence_id}")
async def get_evidence(evidence_id: str):
    """
    Get specific evidence details

    Args:
        evidence_id: Evidence ID

    Returns:
        {"id": str, "name": str, "description": str, "content": str}

    """
    evidence_path = CONTENT_ROOT / "case" / "evidence" / f"{evidence_id}.json"
    if not evidence_path.exists():
        raise HTTPException(status_code=404, detail="Evidence not found")

    return json.loads(evidence_path.read_text(encoding="utf-8"))


@app.get("/content/witnesses")
async def get_witness_list():
    """
    Get witness list

    Returns:
        [{"id": str, "name": str, "portrait": str}, ...]

    """
    witness_dir = CONTENT_ROOT / "witnesses"
    if not witness_dir.exists():
        return []

    witness_list = []
    for path in sorted(witness_dir.glob("*.json")):
        if path.name == "_template.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        witness_list.append({
            "id": data.get("id", path.stem),
            "name": data.get("name", path.stem),
            "portrait": data.get("portrait", "")
        })
    return witness_list


@app.get("/content/witness/{witness_id}")
async def get_witness(witness_id: str):
    """
    Get witness dialogue tree

    Args:
        witness_id: Witness ID

    Returns:
        Complete dialogue tree JSON

    """
    witness_path = CONTENT_ROOT / "witnesses" / f"{witness_id}.json"
    if not witness_path.exists():
        raise HTTPException(status_code=404, detail="Witness not found")

    return json.loads(witness_path.read_text(encoding="utf-8"))


# ============ Frontend Static Files ============

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

@app.get("/game")
async def serve_frontend():
    """Serve the game frontend"""
    return FileResponse(FRONTEND_DIR / "index.html")

# Mount static files (css, js)
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")


# ============ Startup ============

def find_available_port(host: str, start_port: int, max_attempts: int = 10) -> int:
    """Find an available port in a range."""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((host, port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(
        f"Unable to find an available port (tried {start_port}-{start_port + max_attempts - 1})"
    )

if __name__ == "__main__":
    import uvicorn
    server_host = os.getenv("SERVER_HOST", "0.0.0.0")
    preferred_port = int(os.getenv("SERVER_PORT", "5000"))

    # Try preferred port; if occupied, find an available one.
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((server_host, preferred_port))
        sock.close()
        server_port = preferred_port
    except OSError:
        sock.close()
        print(f"\nWarning: port {preferred_port} is in use (possibly the LLM API proxy).")
        server_port = find_available_port(server_host, preferred_port + 1)
        print(f"Switched to port {server_port}.\n")

    print("AI Trial Game")
    print(f"   Listening: {server_host}:{server_port}")
    print(f"   API: http://localhost:{server_port}/")
    print(f"   Game: http://localhost:{server_port}/game\n")
    uvicorn.run(app, host=server_host, port=server_port)
