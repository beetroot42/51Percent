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

async function setPhase(phase, sessionId) {
    const query = sessionId ? `?session_id=${sessionId}` : '';
    return request(`/phase/${phase}${query}`, { method: 'POST' });
}

async function resetGame() {
    return request('/reset', { method: 'POST' });
}

// ============ 陪审员 ============

async function getJurors(sessionId) {
    const query = sessionId ? `?session_id=${sessionId}` : '';
    return request(`/jurors${query}`);
}

async function getJuror(jurorId, sessionId) {
    const query = sessionId ? `?session_id=${sessionId}` : '';
    return request(`/juror/${jurorId}${query}`);
}

async function chatWithJuror(jurorId, message, sessionId) {
    if (!sessionId) {
        throw new Error('Session ID is required');
    }
    return request(`/chat/${jurorId}?session_id=${sessionId}`, {
        method: 'POST',
        body: JSON.stringify({ message })
    });
}

async function presentEvidenceToJuror(jurorId, evidenceId, sessionId) {
    if (!sessionId) {
        throw new Error('Session ID is required');
    }
    return request(`/juror/${jurorId}/present/${evidenceId}?session_id=${sessionId}`, {
        method: 'POST'
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

async function getEvidenceList(sessionId) {
    const query = sessionId ? `?session_id=${sessionId}` : '';
    return request(`/content/evidence${query}`);
}

async function getEvidence(evidenceId, sessionId) {
    const query = sessionId ? `?session_id=${sessionId}` : '';
    return request(`/content/evidence/${evidenceId}${query}`);
}

async function getWitnessList() {
    return request('/content/witnesses');
}

async function getWitness(witnessId) {
    return request(`/content/witness/${witnessId}`);
}

async function witnessChat(witnessId, sessionId, body) {
    if (!sessionId) {
        throw new Error('Session ID is required');
    }
    return request(`/witness/${witnessId}/chat?session_id=${sessionId}`, {
        method: 'POST',
        body: JSON.stringify(body)
    });
}

async function presentEvidence(witnessId, evidenceId, sessionId) {
    return request(`/witness/${witnessId}/present/${evidenceId}?session_id=${sessionId}`, {
        method: 'POST'
    });
}

// ============ 陪审团辩论 (Deliberation) ============

async function startDeliberation(sessionId) {
    if (!sessionId) {
        throw new Error('Session ID is required');
    }
    return request(`/deliberation/start?session_id=${sessionId}`, {
        method: 'POST'
    });
}

async function submitNote(sessionId, targetId, content, key) {
    if (!sessionId) {
        throw new Error('Session ID is required');
    }
    return request(`/deliberation/note?session_id=${sessionId}`, {
        method: 'POST',
        body: JSON.stringify({
            target_id: targetId,
            content: content,
            idempotency_key: key
        })
    });
}

async function skipDeliberation(sessionId) {
    if (!sessionId) {
        throw new Error('Session ID is required');
    }
    return request(`/deliberation/skip?session_id=${sessionId}`, {
        method: 'POST'
    });
}

async function getDeliberationState(sessionId) {
    if (!sessionId) {
        throw new Error('Session ID is required');
    }
    return request(`/deliberation/state?session_id=${sessionId}`);
}

// ============ 序章 (Prologue) ============

async function getOpening() {
    return request('/story/opening');
}

async function getBlakeNode(sessionId) {
    return request(`/story/blake?session_id=${sessionId}`);
}

async function respondToBlake(sessionId, optionId) {
    return request('/story/blake/respond', {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId, option_id: optionId })
    });
}

async function getEnding(verdict) {
    return request(`/story/ending?verdict=${encodeURIComponent(verdict)}`);
}
