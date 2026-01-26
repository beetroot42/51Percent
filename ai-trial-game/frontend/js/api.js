/**
 * API调用模块
 *
 * 封装与后端的所有HTTP通信
 */

const API_BASE = 'http://localhost:8000';

/**
 * 通用请求函数
 * @param {string} endpoint - API端点
 * @param {object} options - fetch选项
 * @returns {Promise<object>} 响应数据
 */
async function request(endpoint, options = {}) {
    // TODO: 实现
    // - 拼接URL
    // - 设置默认headers
    // - 发送请求
    // - 处理错误
    // - 返回JSON
}

// ============ 游戏状态 ============

/**
 * 获取游戏状态
 * @returns {Promise<{phase: string, jurors: array, vote_state: object}>}
 */
async function getGameState() {
    // TODO: GET /state
}

/**
 * 切换游戏阶段
 * @param {string} phase - investigation / persuasion / verdict
 */
async function setPhase(phase) {
    // TODO: POST /phase/{phase}
}

// ============ 陪审员 ============

/**
 * 获取所有陪审员
 * @returns {Promise<array>}
 */
async function getJurors() {
    // TODO: GET /jurors
}

/**
 * 获取陪审员详情
 * @param {string} jurorId
 * @returns {Promise<object>}
 */
async function getJuror(jurorId) {
    // TODO: GET /juror/{jurorId}
}

/**
 * 与陪审员对话
 * @param {string} jurorId
 * @param {string} message
 * @returns {Promise<{reply: string, juror_id: string}>}
 */
async function chatWithJuror(jurorId, message) {
    // TODO: POST /chat/{jurorId}
    // body: {message}
}

// ============ 投票 ============

/**
 * 触发投票
 * @returns {Promise<{guilty_votes: number, not_guilty_votes: number, verdict: string}>}
 */
async function triggerVote() {
    // TODO: POST /vote
}

// ============ 内容 ============

/**
 * 获取卷宗
 * @returns {Promise<{title: string, content: string}>}
 */
async function getDossier() {
    // TODO: GET /content/dossier
}

/**
 * 获取证据列表
 * @returns {Promise<array>}
 */
async function getEvidenceList() {
    // TODO: GET /content/evidence
}

/**
 * 获取证据详情
 * @param {string} evidenceId
 * @returns {Promise<object>}
 */
async function getEvidence(evidenceId) {
    // TODO: GET /content/evidence/{evidenceId}
}

/**
 * 获取当事人列表
 * @returns {Promise<array>}
 */
async function getWitnessList() {
    // TODO: GET /content/witnesses
}

/**
 * 获取当事人对话树
 * @param {string} witnessId
 * @returns {Promise<object>}
 */
async function getWitness(witnessId) {
    // TODO: GET /content/witness/{witnessId}
}

// 导出（如果使用模块）
// export { getGameState, setPhase, getJurors, ... }
