"""
AI审判游戏 - 后端API

使用FastAPI提供REST接口。
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# from backend.services.agent_manager import AgentManager
# from backend.tools.voting_tool import VotingTool

app = FastAPI(title="AI审判游戏", version="0.1.0")

# CORS配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 请求/响应模型 ============

class ChatRequest(BaseModel):
    """对话请求"""
    message: str


class ChatResponse(BaseModel):
    """对话响应"""
    reply: str
    juror_id: str


class VoteResponse(BaseModel):
    """投票响应"""
    guilty_votes: int
    not_guilty_votes: int
    verdict: str
    tx_hashes: list[str]


class GameState(BaseModel):
    """游戏状态"""
    phase: str  # investigation / persuasion / verdict
    jurors: list[dict]
    vote_state: dict | None


# ============ 全局状态 ============

# TODO: 初始化
# agent_manager = AgentManager()
# voting_tool = VotingTool(contract_address="...")
# game_phase = "investigation"


# ============ API端点 ============

@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "game": "AI审判"}


@app.get("/state", response_model=GameState)
async def get_game_state():
    """
    获取当前游戏状态

    Returns:
        GameState对象

    TODO:
    - 返回当前phase
    - 返回陪审员列表（基本信息）
    - 如果phase==verdict，返回投票状态
    """
    pass


@app.post("/phase/{phase_name}")
async def set_phase(phase_name: str):
    """
    切换游戏阶段

    Args:
        phase_name: investigation / persuasion / verdict

    TODO:
    - 验证phase_name有效
    - 更新全局game_phase
    - 如果切换到verdict，触发投票
    """
    pass


@app.get("/jurors")
async def get_jurors():
    """
    获取所有陪审员信息

    Returns:
        [{"id": str, "name": str}, ...]

    TODO:
    - 调用agent_manager.get_all_juror_info()
    """
    pass


@app.get("/juror/{juror_id}")
async def get_juror(juror_id: str):
    """
    获取指定陪审员信息

    Args:
        juror_id: 陪审员ID

    Returns:
        {"id": str, "name": str, "first_message": str}

    TODO:
    - 获取agent
    - 返回基本信息
    """
    pass


@app.post("/chat/{juror_id}", response_model=ChatResponse)
async def chat_with_juror(juror_id: str, request: ChatRequest):
    """
    与陪审员对话

    Args:
        juror_id: 陪审员ID
        request: 包含message的请求体

    Returns:
        ChatResponse

    TODO:
    - 检查phase是否为persuasion
    - 调用agent_manager.chat_with_juror()
    - 返回回复
    """
    pass


@app.post("/vote", response_model=VoteResponse)
async def trigger_vote():
    """
    触发投票

    收集所有陪审员立场，执行链上投票。

    Returns:
        VoteResponse

    TODO:
    - 调用agent_manager.collect_votes()
    - 调用voting_tool.cast_all_votes()
    - 返回结果
    """
    pass


@app.post("/reset")
async def reset_game():
    """
    重置游戏

    TODO:
    - 重置所有agent
    - 重置phase为investigation
    - 可选：部署新合约
    """
    pass


# ============ 静态内容接口 ============

@app.get("/content/dossier")
async def get_dossier():
    """
    获取卷宗内容

    Returns:
        {"title": str, "content": str}

    TODO:
    - 读取content/case/dossier.json
    """
    pass


@app.get("/content/evidence")
async def get_evidence_list():
    """
    获取证据列表

    Returns:
        [{"id": str, "name": str, "icon": str}, ...]

    TODO:
    - 扫描content/case/evidence/目录
    """
    pass


@app.get("/content/evidence/{evidence_id}")
async def get_evidence(evidence_id: str):
    """
    获取指定证据详情

    Args:
        evidence_id: 证据ID

    Returns:
        {"id": str, "name": str, "description": str, "content": str}

    TODO:
    - 读取content/case/evidence/{evidence_id}.json
    """
    pass


@app.get("/content/witnesses")
async def get_witness_list():
    """
    获取当事人列表

    Returns:
        [{"id": str, "name": str, "portrait": str}, ...]

    TODO:
    - 扫描content/witnesses/目录
    """
    pass


@app.get("/content/witness/{witness_id}")
async def get_witness(witness_id: str):
    """
    获取当事人对话树

    Args:
        witness_id: 当事人ID

    Returns:
        完整的对话树JSON

    TODO:
    - 读取content/witnesses/{witness_id}.json
    """
    pass


# ============ 启动 ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
