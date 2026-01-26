/**
 * API调用模块
 */

const API_BASE = 'http://localhost:5000';

/**
 * 通用请求函数
 */
async function request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        headers: { 'Content-Type': 'application/json' },
        ...options
    };

    const response = await fetch(url, config);
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || 'Request failed');
    }
    return response.json();
}

// ============ 游戏状态 ============

async function getGameState() {
    return request('/state');
}

async function setPhase(phase) {
    return request(`/phase/${phase}`, { method: 'POST' });
}

async function resetGame() {
    return request('/reset', { method: 'POST' });
}

// ============ 陪审员 ============

async function getJurors() {
    return request('/jurors');
}

async function getJuror(jurorId) {
    return request(`/juror/${jurorId}`);
}

async function chatWithJuror(jurorId, message) {
    return request(`/chat/${jurorId}`, {
        method: 'POST',
        body: JSON.stringify({ message })
    });
}

// ============ 投票 ============

async function triggerVote() {
    return request('/vote', { method: 'POST' });
}

// ============ 内容 ============

async function getDossier() {
    return request('/content/dossier');
}

async function getEvidenceList() {
    return request('/content/evidence');
}

async function getEvidence(evidenceId) {
    return request(`/content/evidence/${evidenceId}`);
}

async function getWitnessList() {
    return request('/content/witnesses');
}

async function getWitness(witnessId) {
    return request(`/content/witness/${witnessId}`);
}
