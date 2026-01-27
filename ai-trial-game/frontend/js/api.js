/**
 * API调用模块
 */

const API_BASE = '';

/**
 * 通用请求函数
 */
async function request(endpoint, options = {}) {
    const { timeout = 60000, ...fetchOptions } = options;
    const url = `${API_BASE}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const config = {
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        ...fetchOptions
    };

    try {
        const response = await fetch(url, config);
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || `Request failed with status ${response.status}`);
        }
        return response.json();
    } catch (e) {
        clearTimeout(timeoutId);
        if (e.name === 'AbortError') {
            throw new Error(
                '请求超时 (超过 ' + (timeout / 1000) + 's)\n\n' +
                '建议排查：\n' +
                '1. 如果是投票请求，请检查 Anvil 生成区块是否正常\n' +
                '2. 检查后端终端是否有报错阻塞\n' +
                '3. 网络连接是否稳定'
            );
        }
        throw e;
    }
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
    return request('/vote', { 
        method: 'POST',
        timeout: 120000 // 120s for chain confirmation
    });
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
