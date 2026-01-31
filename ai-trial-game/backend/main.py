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
import re
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
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
from services.session_manager import Phase, SessionManager, require_phase
from agents.daneel_agent import DaneelAgent
from tools.voting_tool import VotingTool

APP_VERSION = "phase2-bugfix-2"
app = FastAPI(title="AI Trial Game", version="0.1.0")
logger = logging.getLogger(__name__)
_verification_executor = ThreadPoolExecutor(max_workers=2)
_evidence_cache: dict[str, object] = {"mtime": 0.0, "items": []}

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
    rounds_left: int = 0
    weakness_triggered: bool = False


class VoteResponse(BaseModel):
    """Vote response"""
    guilty_votes: int
    not_guilty_votes: int
    verdict: str
    tx_hashes: list[str]
    votes: list[dict] = Field(default_factory=list)

class VerifyVoteRequest(BaseModel):
    """Verify vote request"""
    txHash: str


class GameState(BaseModel):
    """Game state"""
    phase: str  # prologue / investigation / persuasion / verdict
    jurors: list[dict]
    vote_state: dict | None


class OpeningResponse(BaseModel):
    """Opening story response."""
    session_id: str
    text: str


class BlakeOption(BaseModel):
    """Blake dialogue option."""
    id: str
    text: str


class BlakeNodeResponse(BaseModel):
    """Blake dialogue node response."""
    round: int
    text: str
    options: list[BlakeOption]


class BlakeRespondRequest(BaseModel):
    """Blake response request."""
    session_id: str
    option_id: str


class BlakeRespondResponse(BaseModel):
    """Blake response payload."""
    response_text: str
    next_round: int
    phase: str


class EndingResponse(BaseModel):
    """Ending story response."""
    type: str = ""
    title: str = ""
    text: str = ""
    blake_reaction: str = ""


class WitnessChatRequest(BaseModel):
    """Witness chat request."""
    message: str | None = None
    option_id: str | None = None


class WitnessOption(BaseModel):
    """Witness option."""
    id: str
    text: str


class WitnessNodeResponse(BaseModel):
    """Witness chat response."""
    text: str
    options: list[WitnessOption] = Field(default_factory=list)
    is_llm: bool = False
    node_id: str | None = None


class PresentEvidenceResponse(BaseModel):
    """Witness evidence response."""
    text: str
    unlocks: list[str] = Field(default_factory=list)
    forced: bool = False


class PresentJurorEvidenceResponse(BaseModel):
    """Juror evidence response."""
    text: str
    stance_delta: int = 0
    rounds_left: int = 0
    weakness_triggered: bool = False


# ============ Global State ============

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = PROJECT_ROOT / "content"
JUROR_CONTENT = CONTENT_ROOT / "jurors"

game_phase_var: ContextVar[str] = ContextVar("game_phase", default="prologue")
session_manager = SessionManager()

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
daneel_agent = DaneelAgent(content_root=CONTENT_ROOT)
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

def get_game_phase() -> str:
    return game_phase_var.get()

def set_game_phase(phase: str) -> None:
    game_phase_var.set(phase)

def get_chain_name(chain_id: int) -> str:
    """Map chain id to friendly name."""
    chain_names = {
        31337: "Anvil Local",
        11155111: "Sepolia Testnet",
        1: "Ethereum Mainnet",
    }
    return chain_names.get(chain_id, f"Unknown Chain ({chain_id})")


def _load_evidence_triggers() -> dict:
    triggers_path = CONTENT_ROOT / "triggers" / "evidence_triggers.json"
    if not triggers_path.exists():
        return {}
    return json.loads(triggers_path.read_text(encoding="utf-8"))


def _resolve_evidence_ids(evidence_id: str) -> tuple[str, str]:
    """
    Resolve evidence id to (file_stem, internal_id).
    Accepts file stem or internal id (e.g., E01_jailbreak_chat or E1).
    """
    evidence_dir = CONTENT_ROOT / "case" / "evidence"
    direct_path = evidence_dir / f"{evidence_id}.json"
    if direct_path.exists():
        data = json.loads(direct_path.read_text(encoding="utf-8"))
        internal_id = str(data.get("id", evidence_id))
        return direct_path.stem, internal_id

    for path in sorted(evidence_dir.glob("*.json")):
        if path.name == "_template.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        internal_id = str(data.get("id", "")).upper()
        if internal_id == str(evidence_id).upper():
            return path.stem, internal_id

    raise HTTPException(status_code=404, detail="Evidence not found")


def _map_internal_ids_to_stems(internal_ids: list[str]) -> list[str]:
    evidence_dir = CONTENT_ROOT / "case" / "evidence"
    mapping: dict[str, str] = {}
    for path in sorted(evidence_dir.glob("*.json")):
        if path.name == "_template.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        internal_id = str(data.get("id", "")).upper()
        if internal_id:
            mapping[internal_id] = path.stem
    resolved = []
    for internal_id in internal_ids:
        stem = mapping.get(str(internal_id).upper())
        if stem:
            resolved.append(stem)
    return resolved


def _extract_tx_hash(text: str) -> str | None:
    match = re.search(r"tx_hash:\s*(0x[0-9a-fA-F]+)", text)
    return match.group(1) if match else None


def _build_juror_evidence_message(evidence_id: str, internal_id: str) -> str:
    evidence_path = CONTENT_ROOT / "case" / "evidence" / f"{evidence_id}.json"
    evidence_name = evidence_id
    if evidence_path.exists():
        try:
            data = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence_name = data.get("name", evidence_id)
        except json.JSONDecodeError:
            evidence_name = evidence_id
    return (
        f"玩家出示证物: {evidence_name} (ID: {evidence_id}, 编号: {internal_id}). "
        "如需查看内容，请使用 lookup_evidence 工具并传入该证物ID。"
    )


def _load_evidence_metadata() -> list[dict]:
    evidence_dir = CONTENT_ROOT / "case" / "evidence"
    if not evidence_dir.exists():
        return []

    evidence_files = [path for path in sorted(evidence_dir.glob("*.json")) if path.name != "_template.json"]
    latest_mtime = 0.0
    for path in evidence_files:
        try:
            latest_mtime = max(latest_mtime, path.stat().st_mtime)
        except OSError:
            continue

    cached_mtime = float(_evidence_cache.get("mtime", 0.0))
    cached_items = _evidence_cache.get("items", [])
    if cached_items and latest_mtime <= cached_mtime:
        return list(cached_items)

    items: list[dict] = []
    for path in evidence_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        items.append({
            "id": path.stem,
            "name": data.get("name", path.stem),
            "icon": data.get("icon", ""),
            "internal_id": data.get("id", path.stem),
            "locked": bool(data.get("locked", False)),
        })

    _evidence_cache["mtime"] = latest_mtime
    _evidence_cache["items"] = list(items)
    return items


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
    return {"status": "ok", "game": "AI Trial", "version": APP_VERSION}


@app.get("/state", response_model=GameState)
async def get_game_state():
    """
    Get current game state

    Returns:
        GameState object

    """
    vote_state = None
    current_phase = get_game_phase()
    if current_phase == "verdict":
        vote_state = agent_manager.collect_votes()

    return GameState(
        phase=current_phase,
        jurors=agent_manager.get_all_juror_info(),
        vote_state=vote_state
    )


@app.get("/story/opening", response_model=OpeningResponse)
async def get_story_opening():
    """
    Create a new session and return opening story text.
    """
    opening_path = CONTENT_ROOT / "story" / "opening.json"
    if not opening_path.exists():
        raise HTTPException(status_code=404, detail="Opening story not found")

    opening_data = json.loads(opening_path.read_text(encoding="utf-8"))
    state = session_manager.create_session()

    set_game_phase(state.phase.value)

    return OpeningResponse(
        session_id=state.session_id,
        text=opening_data.get("text", "")
    )


@app.get("/story/blake", response_model=BlakeNodeResponse)
async def get_blake_node(session_id: str):
    """
    Get the current Blake dialogue node for a session.
    """
    try:
        state = session_manager.get(session_id)
        require_phase(state, Phase.prologue)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    blake_path = CONTENT_ROOT / "story" / "blake.json"
    if not blake_path.exists():
        raise HTTPException(status_code=404, detail="Blake story not found")

    blake_data = json.loads(blake_path.read_text(encoding="utf-8"))
    rounds = blake_data.get("rounds", [])
    if not rounds:
        raise HTTPException(status_code=500, detail="Blake story is empty")
    if state.blake_round >= len(rounds):
        raise HTTPException(status_code=400, detail="Blake dialogue already completed")

    node = rounds[state.blake_round]
    options = [BlakeOption(id=opt.get("id", ""), text=opt.get("text", "")) for opt in node.get("options", [])]

    return BlakeNodeResponse(
        round=int(node.get("round", state.blake_round + 1)),
        text=node.get("topic", ""),
        options=options
    )


@app.post("/story/blake/respond", response_model=BlakeRespondResponse)
async def respond_to_blake(request: BlakeRespondRequest):
    """
    Submit a response to the current Blake dialogue node.
    """
    try:
        state = session_manager.get(request.session_id)
        require_phase(state, Phase.prologue)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    blake_path = CONTENT_ROOT / "story" / "blake.json"
    if not blake_path.exists():
        raise HTTPException(status_code=404, detail="Blake story not found")

    blake_data = json.loads(blake_path.read_text(encoding="utf-8"))
    rounds = blake_data.get("rounds", [])
    if not rounds:
        raise HTTPException(status_code=500, detail="Blake story is empty")
    if state.blake_round >= len(rounds):
        raise HTTPException(status_code=400, detail="Blake dialogue already completed")

    node = rounds[state.blake_round]
    options = node.get("options", [])
    selected = next((opt for opt in options if opt.get("id") == request.option_id), None)
    if not selected:
        raise HTTPException(status_code=400, detail="Invalid option_id")

    response_text = selected.get("response", "")
    next_phase = selected.get("next_phase")

    if next_phase:
        try:
            state.phase = Phase(next_phase)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid next_phase")
        state.blake_round = len(rounds)
        set_game_phase(state.phase.value)
        return BlakeRespondResponse(
            response_text=response_text,
            next_round=0,
            phase=state.phase.value
        )

    # Keep the same round unless an option explicitly changes phase.
    set_game_phase(state.phase.value)

    next_round = int(rounds[state.blake_round].get("round", state.blake_round + 1))

    return BlakeRespondResponse(
        response_text=response_text,
        next_round=next_round,
        phase=state.phase.value
    )


@app.get("/story/ending", response_model=EndingResponse)
async def get_story_ending(verdict: str):
    """
    Get ending story text based on verdict.
    """
    verdict_norm = verdict.strip().upper().replace(" ", "_")
    if verdict_norm == "GUILTY":
        ending_file = "ending_guilty.json"
    elif verdict_norm == "NOT_GUILTY":
        ending_file = "ending_not_guilty.json"
    elif verdict_norm == "BETRAYAL":
        ending_file = "ending_betrayal.json"
    else:
        raise HTTPException(status_code=400, detail="Invalid verdict")

    ending_path = CONTENT_ROOT / "story" / ending_file
    if not ending_path.exists():
        raise HTTPException(status_code=404, detail="Ending story not found")

    ending_data = json.loads(ending_path.read_text(encoding="utf-8"))
    return EndingResponse(
        type=ending_data.get("type", ""),
        title=ending_data.get("title", ""),
        text=ending_data.get("text", ""),
        blake_reaction=ending_data.get("blake_reaction", "")
    )


@app.post("/phase/{phase_name}")
async def set_phase(phase_name: str, session_id: str | None = None):
    """
    Switch game phase

    Args:
        phase_name: investigation / persuasion / verdict

    """
    valid_phases = {"prologue", "investigation", "persuasion", "verdict"}
    if phase_name not in valid_phases:
        raise HTTPException(status_code=400, detail="Invalid phase")

    set_game_phase(phase_name)

    if session_id:
        try:
            state = session_manager.get(session_id)
            state.phase = Phase(phase_name)
        except (KeyError, ValueError):
            pass

    return {"phase": get_game_phase()}


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
async def chat_with_juror(juror_id: str, request: ChatRequest, session_id: str):
    """
    Chat with a juror

    Args:
        juror_id: Juror ID
        request: Request body containing message

    Returns:
        ChatResponse

    """
    try:
        state = session_manager.get(session_id)
        require_phase(state, Phase.persuasion)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    rounds_used = state.juror_rounds_used.get(juror_id, 0)
    if rounds_used >= 10:
        raise HTTPException(status_code=429, detail="已用完与该陪审员的对话次数")

    try:
        response = await agent_manager.chat_with_juror(juror_id, request.message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc

    state.juror_rounds_used[juror_id] = rounds_used + 1
    rounds_left = max(0, 10 - state.juror_rounds_used[juror_id])

    return ChatResponse(
        reply=response["reply"],
        juror_id=response["juror_id"],
        tool_actions=response.get("tool_actions", []),
        has_voted=response.get("has_voted", False),
        rounds_left=rounds_left,
        weakness_triggered=response.get("weakness_triggered", False)
    )


@app.post("/juror/{juror_id}/present/{evidence_id}", response_model=PresentJurorEvidenceResponse)
async def present_evidence_to_juror(juror_id: str, evidence_id: str, session_id: str):
    """
    Present evidence to a juror during persuasion.
    """
    try:
        state = session_manager.get(session_id)
        require_phase(state, Phase.persuasion)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    rounds_used = state.juror_rounds_used.get(juror_id, 0)
    if rounds_used >= 10:
        raise HTTPException(status_code=429, detail="已用完与该陪审员的对话次数")

    evidence_stem, internal_id = _resolve_evidence_ids(evidence_id)
    if evidence_stem not in state.evidence_unlocked:
        raise HTTPException(status_code=403, detail="Evidence is locked")

    try:
        agent = agent_manager.get_juror(juror_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    before_stance = agent.stance_value
    response = await agent.chat(_build_juror_evidence_message(evidence_stem, internal_id))
    after_stance = agent.stance_value

    state.juror_rounds_used[juror_id] = rounds_used + 1
    rounds_left = max(0, 10 - state.juror_rounds_used[juror_id])

    return PresentJurorEvidenceResponse(
        text=response["reply"],
        stance_delta=int(after_stance - before_stance),
        rounds_left=rounds_left,
        weakness_triggered=response.get("weakness_triggered", False),
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

    votes: list[dict] = []
    tx_hashes: list[str] = []

    for juror_id, agent in agent_manager.agents.items():
        try:
            response = await agent.chat(
                "审判阶段已开始，请根据当前立场作出最终投票，并调用 cast_vote 工具提交结果。"
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Juror vote failed: {exc}") from exc

        guilty: bool | None = None
        tx_hash: str | None = None
        for action in response.get("tool_actions", []):
            if action.get("tool") == "cast_vote":
                guilty = bool(action.get("input", {}).get("guilty"))
                tx_hash = _extract_tx_hash(action.get("result_summary", ""))
                if tx_hash:
                    tx_hashes.append(tx_hash)
        if guilty is None:
            raise HTTPException(status_code=500, detail=f"Juror did not cast vote: {juror_id}")

        votes.append({
            "juror_id": juror_id,
            "name": agent.config.name if agent.config else juror_id,
            "vote": guilty
        })

    guilty_count = sum(1 for vote in votes if vote.get("vote"))
    not_guilty_count = len(votes) - guilty_count

    verdict = "GUILTY" if guilty_count > not_guilty_count else "NOT_GUILTY"
    try:
        vote_state = voting_tool.get_vote_state()
        guilty_count = int(vote_state.guilty_votes)
        not_guilty_count = int(vote_state.not_guilty_votes)
        verdict = vote_state.verdict or verdict
    except Exception:
        pass

    global last_vote_tx_hash
    last_vote_tx_hash = tx_hashes[0] if tx_hashes else None

    return VoteResponse(
        guilty_votes=guilty_count,
        not_guilty_votes=not_guilty_count,
        verdict=verdict,
        tx_hashes=tx_hashes,
        votes=votes
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
    agent_manager.reset_all()
    daneel_agent.reset()
    set_game_phase("prologue")
    return {"status": "reset", "phase": get_game_phase()}


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

    try:
        return json.loads(dossier_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid JSON: {exc}") from exc


@app.get("/content/evidence")
async def get_evidence_list(session_id: str | None = None):
    """
    Get evidence list

    Returns:
        [{"id": str, "name": str, "icon": str, "locked": bool}, ...]

    """
    evidence_dir = CONTENT_ROOT / "case" / "evidence"
    if not evidence_dir.exists():
        return []

    state = None
    if session_id:
        try:
            state = session_manager.get(session_id)
        except KeyError as exc:
            state = None

    evidence_list = []
    for item in _load_evidence_metadata():
        locked = bool(item.get("locked", False))
        if state is not None and locked:
            locked = item.get("id") not in state.evidence_unlocked
        evidence_list.append({
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "icon": item.get("icon", ""),
            "internal_id": item.get("internal_id", item.get("id", "")),
            "locked": locked,
        })
    return evidence_list


@app.get("/content/evidence/{evidence_id}")
async def get_evidence(evidence_id: str, session_id: str | None = None):
    """
    Get specific evidence details

    Args:
        evidence_id: Evidence ID

    Returns:
        {"id": str, "name": str, "description": str, "content": str}

    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    try:
        state = session_manager.get(session_id)
    except KeyError:
        state = None

    evidence_path = CONTENT_ROOT / "case" / "evidence" / f"{evidence_id}.json"
    if not evidence_path.exists():
        raise HTTPException(status_code=404, detail="Evidence not found")

    if state is not None:
        if evidence_path.stem not in state.evidence_unlocked:
            raise HTTPException(status_code=403, detail="Evidence is locked")
    else:
        try:
            evidence_data = json.loads(evidence_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail=f"Invalid JSON: {exc}") from exc
        if bool(evidence_data.get("locked", False)):
            raise HTTPException(status_code=403, detail="Evidence is locked")
        return evidence_data

    try:
        return json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid JSON: {exc}") from exc


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


@app.post("/witness/{witness_id}/chat", response_model=WitnessNodeResponse)
async def chat_with_witness(witness_id: str, request: WitnessChatRequest, session_id: str):
    """
    Chat with witness during investigation.
    """
    try:
        state = session_manager.get(session_id)
        require_phase(state, Phase.investigation)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if witness_id == "daneel":
        if not request.message:
            raise HTTPException(status_code=400, detail="message is required")
        rounds = session_manager.increment_witness_rounds(session_id, witness_id)
        if rounds > 15:
            raise HTTPException(status_code=403, detail="Daneel chat limit reached")
        try:
            reply = await daneel_agent.chat(request.message, session_id=session_id)
        except Exception as exc:
            logger.error("Daneel chat error: %s", exc)
            raise HTTPException(status_code=502, detail="AI communication error") from exc
        return WitnessNodeResponse(text=reply, is_llm=True)

    witness_path = CONTENT_ROOT / "witnesses" / f"{witness_id}.json"
    if not witness_path.exists():
        raise HTTPException(status_code=404, detail="Witness not found")

    witness_data = json.loads(witness_path.read_text(encoding="utf-8"))
    dialogue_nodes = {node.get("id", ""): node for node in witness_data.get("dialogues", [])}
    if not dialogue_nodes:
        raise HTTPException(status_code=500, detail="Witness dialogue is empty")

    current_node_id = session_manager.get_witness_node(session_id, witness_id)
    current_node = dialogue_nodes.get(current_node_id)
    if not current_node:
        current_node_id = "start"
        current_node = dialogue_nodes.get(current_node_id)
        if not current_node:
            raise HTTPException(status_code=500, detail="Witness start node missing")

    if request.option_id:
        options = current_node.get("options", [])
        selected = None
        for option in options:
            if option.get("next") == request.option_id or option.get("id") == request.option_id:
                selected = option
                break
        if not selected:
            raise HTTPException(status_code=400, detail="Invalid option_id")

        next_node_id = selected.get("next") or request.option_id
        session_manager.set_witness_node(session_id, witness_id, next_node_id)
        current_node_id = next_node_id
        current_node = dialogue_nodes.get(current_node_id)
        if not current_node:
            raise HTTPException(status_code=500, detail="Witness node not found")

    options_payload = []
    for option in current_node.get("options", []):
        option_id = option.get("next") or option.get("id") or ""
        options_payload.append(WitnessOption(id=str(option_id), text=option.get("text", "")))

    return WitnessNodeResponse(
        text=current_node.get("text", ""),
        options=options_payload,
        is_llm=False,
        node_id=current_node_id
    )


@app.post("/witness/{witness_id}/present/{evidence_id}", response_model=PresentEvidenceResponse)
async def present_evidence_to_witness(witness_id: str, evidence_id: str, session_id: str):
    """
    Present evidence to a witness and unlock new evidence when matched.
    """
    try:
        state = session_manager.get(session_id)
        require_phase(state, Phase.investigation)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    evidence_stem, internal_id = _resolve_evidence_ids(evidence_id)
    if evidence_stem not in state.evidence_unlocked:
        raise HTTPException(status_code=403, detail="Evidence is locked")

    triggers = _load_evidence_triggers()
    witness_triggers = triggers.get(witness_id, {})
    trigger = witness_triggers.get(internal_id)

    if not trigger:
        return PresentEvidenceResponse(
            text="我暂时没有更多可补充的。",
            unlocks=[],
            forced=False
        )

    unlocks_internal = list(trigger.get("unlocks", []))
    unlock_stems = _map_internal_ids_to_stems(unlocks_internal)
    if unlock_stems:
        session_manager.unlock_evidence(session_id, unlock_stems)

    return PresentEvidenceResponse(
        text=trigger.get("response", ""),
        unlocks=unlocks_internal,
        forced=bool(trigger.get("forced", True))
    )


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
