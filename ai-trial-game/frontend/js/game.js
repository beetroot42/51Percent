/**
 * 游戏主逻辑
 */

const PHASES = {
    INVESTIGATION: 'investigation',
    PERSUASION: 'persuasion',
    VERDICT: 'verdict'
};

const gameState = {
    phase: PHASES.INVESTIGATION,
    currentJuror: null,
    chatHistory: {},
    evidenceList: [],
};

// ============ 初始化 ============

async function initGame() {
    try {
        setLoading(true);
        const state = await getGameState();
        gameState.phase = state.phase || PHASES.INVESTIGATION;
        bindEvents();
        await enterInvestigation();
    } catch (e) {
        showError('无法连接服务器，请确保后端已启动');
    } finally {
        setLoading(false);
    }
}

function bindEvents() {
    // 调查阶段标签切换
    document.querySelectorAll('#investigation-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', () => handleTabClick(btn.dataset.tab));
    });

    // 进入说服阶段
    document.getElementById('enter-persuasion-btn')?.addEventListener('click', enterPersuasion);

    // 进入审判阶段
    document.getElementById('enter-verdict-btn')?.addEventListener('click', enterVerdict);

    // 重新开始
    document.getElementById('restart-btn')?.addEventListener('click', handleRestart);

    // 聊天输入
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    sendBtn?.addEventListener('click', () => handleSendMessage());
    chatInput?.addEventListener('keypress', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // 当事人对话弹窗
    document.getElementById('close-dialogue-btn')?.addEventListener('click', closeWitnessDialogue);
    document.getElementById('show-evidence-btn')?.addEventListener('click', showEvidenceSelector);
    document.getElementById('cancel-evidence-btn')?.addEventListener('click', closeEvidenceSelector);
}

function handleTabClick(tabId) {
    document.querySelectorAll('#investigation-tabs .tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `${tabId}-panel`);
    });

    if (tabId === 'dossier') showDossier();
    else if (tabId === 'evidence') showEvidenceList();
    else if (tabId === 'witnesses') showWitnessList();
}

// ============ 阶段控制 ============

async function enterInvestigation() {
    gameState.phase = PHASES.INVESTIGATION;
    await setPhase(PHASES.INVESTIGATION);
    updatePhaseIndicator('调查阶段');
    showSection('investigation-phase');
    await showDossier();
}

async function enterPersuasion() {
    setLoading(true);
    try {
        gameState.phase = PHASES.PERSUASION;
        await setPhase(PHASES.PERSUASION);
        updatePhaseIndicator('说服阶段');
        showSection('persuasion-phase');
        await showJurorList();
    } catch (e) {
        showError('切换阶段失败');
    } finally {
        setLoading(false);
    }
}

async function enterVerdict() {
    setLoading(true);
    try {
        gameState.phase = PHASES.VERDICT;
        await setPhase(PHASES.VERDICT);
        updatePhaseIndicator('审判阶段');
        showSection('verdict-phase');
        document.getElementById('verdict-result').classList.add('hidden');

        const result = await triggerVote();
        await showVotingAnimation(result);
        showVerdict(result.verdict);
    } catch (e) {
        showError('投票失败: ' + e.message);
    } finally {
        setLoading(false);
    }
}

async function handleRestart() {
    setLoading(true);
    try {
        await resetGame();
        gameState.currentJuror = null;
        gameState.chatHistory = {};
        resetDialogue();
        await enterInvestigation();
    } catch (e) {
        showError('重置失败');
    } finally {
        setLoading(false);
    }
}

function updatePhaseIndicator(text) {
    const indicator = document.getElementById('phase-indicator');
    if (indicator) indicator.textContent = text;
}

// ============ 调查阶段UI ============

async function showDossier() {
    const container = document.getElementById('dossier-content');
    if (!container) return;

    try {
        const data = await getDossier();
        container.innerHTML = `
            <h2>${data.title || '案件卷宗'}</h2>
            <div class="dossier-text">${formatContent(data.content)}</div>
        `;
    } catch (e) {
        container.innerHTML = '<p class="error">无法加载卷宗</p>';
    }
}

async function showEvidenceList() {
    const grid = document.getElementById('evidence-grid');
    if (!grid) return;

    try {
        const list = await getEvidenceList();
        gameState.evidenceList = list;

        if (!list || list.length === 0) {
            grid.innerHTML = '<p>暂无证据</p>';
            return;
        }

        grid.innerHTML = list.map(e => `
            <div class="evidence-card" data-id="${e.id}" onclick="showEvidenceDetail('${e.id}')">
                <span class="evidence-name">${e.name || e.id}</span>
            </div>
        `).join('');
    } catch (e) {
        grid.innerHTML = '<p class="error">无法加载证据列表</p>';
    }
}

async function showEvidenceDetail(evidenceId) {
    try {
        const evidence = await getEvidence(evidenceId);
        alert(`【${evidence.name || evidenceId}】\n\n${evidence.description || evidence.content || '无详细信息'}`);
    } catch (e) {
        showError('无法加载证据详情');
    }
}

async function showWitnessList() {
    const grid = document.getElementById('witness-grid');
    if (!grid) return;

    try {
        const list = await getWitnessList();
        if (!list || list.length === 0) {
            grid.innerHTML = '<p>暂无当事人</p>';
            return;
        }

        grid.innerHTML = list.map(w => `
            <div class="witness-card" data-id="${w.id}" onclick="startWitnessDialogue('${w.id}')">
                <span class="witness-name">${w.name || w.id}</span>
                <span class="witness-desc">${w.description || ''}</span>
            </div>
        `).join('');
    } catch (e) {
        grid.innerHTML = '<p class="error">无法加载当事人列表</p>';
    }
}

async function startWitnessDialogue(witnessId) {
    try {
        await loadWitness(witnessId);
        const modal = document.getElementById('witness-dialogue-modal');
        modal?.classList.remove('hidden');
        renderDialogueNode();
    } catch (e) {
        showError('无法加载对话');
    }
}

function renderDialogueNode() {
    const node = getCurrentNode();
    const textEl = document.getElementById('witness-text');
    const optionsEl = document.getElementById('dialogue-options');

    if (!node) {
        if (textEl) textEl.textContent = '对话已结束';
        if (optionsEl) optionsEl.innerHTML = '';
        return;
    }

    if (textEl) textEl.textContent = node.text || '';

    if (optionsEl) {
        if (node.options && node.options.length > 0) {
            optionsEl.innerHTML = node.options.map(opt => `
                <button class="dialogue-option-btn" onclick="handleDialogueOption('${opt.next}')">${opt.text}</button>
            `).join('');
        } else {
            optionsEl.innerHTML = '<p class="dialogue-end">（对话结束）</p>';
        }
    }
}

function handleDialogueOption(nextNodeId) {
    selectOption(nextNodeId);
    renderDialogueNode();
}

function closeWitnessDialogue() {
    document.getElementById('witness-dialogue-modal')?.classList.add('hidden');
    resetDialogue();
}

function showEvidenceSelector() {
    const grid = document.getElementById('evidence-selector-grid');
    const modal = document.getElementById('evidence-selector-modal');

    if (grid && gameState.evidenceList.length > 0) {
        grid.innerHTML = gameState.evidenceList.map(e => `
            <button class="evidence-select-btn ${hasShownEvidence(e.id) ? 'shown' : ''}"
                    onclick="handleShowEvidence('${e.id}')">
                ${e.name || e.id}
            </button>
        `).join('');
    } else if (grid) {
        grid.innerHTML = '<p>没有可出示的证物</p>';
    }

    modal?.classList.remove('hidden');
}

function closeEvidenceSelector() {
    document.getElementById('evidence-selector-modal')?.classList.add('hidden');
}

function handleShowEvidence(evidenceId) {
    const reaction = showEvidence(evidenceId);
    closeEvidenceSelector();

    if (reaction && reaction.text) {
        alert(`【证物反应】\n\n${reaction.text}`);
        renderDialogueNode();
    } else {
        alert('对方对这个证物没有特别反应');
    }
}

// ============ 说服阶段UI ============

async function showJurorList() {
    const container = document.getElementById('juror-list');
    if (!container) return;

    try {
        const jurors = await getJurors();
        const realJurors = jurors.filter(j => !j.id.startsWith('test'));

        if (realJurors.length === 0) {
            container.innerHTML = '<p>暂无陪审员</p>';
            return;
        }

        container.innerHTML = realJurors.map(j => `
            <div class="juror-card ${gameState.currentJuror === j.id ? 'selected' : ''}"
                 data-id="${j.id}" onclick="selectJuror('${j.id}')">
                <span class="juror-name">${j.name || j.id}</span>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p class="error">无法加载陪审员</p>';
    }
}

async function selectJuror(jurorId) {
    gameState.currentJuror = jurorId;

    // 更新选中状态
    document.querySelectorAll('.juror-card').forEach(card => {
        card.classList.toggle('selected', card.dataset.id === jurorId);
    });

    // 更新聊天区域
    const headerName = document.getElementById('current-juror-name');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');

    try {
        const juror = await getJuror(jurorId);
        if (headerName) headerName.textContent = juror.name || jurorId;
    } catch {
        if (headerName) headerName.textContent = jurorId;
    }

    // 启用输入
    if (chatInput) chatInput.disabled = false;
    if (sendBtn) sendBtn.disabled = false;

    // 渲染历史或首次对话
    if (!gameState.chatHistory[jurorId]) {
        gameState.chatHistory[jurorId] = [];
        try {
            const juror = await getJuror(jurorId);
            if (juror.first_message) {
                gameState.chatHistory[jurorId].push({ role: 'juror', content: juror.first_message });
            }
        } catch {}
    }
    renderChatHistory(jurorId);
}

async function handleSendMessage() {
    const input = document.getElementById('chat-input');
    const message = input?.value.trim();

    if (!message || !gameState.currentJuror) return;

    input.value = '';
    input.disabled = true;
    document.getElementById('send-btn').disabled = true;

    // 显示玩家消息
    appendMessage('player', message);
    gameState.chatHistory[gameState.currentJuror].push({ role: 'player', content: message });

    // 显示加载
    const loadingId = appendMessage('juror', '思考中...');

    try {
        const response = await chatWithJuror(gameState.currentJuror, message);
        // 移除加载消息
        document.getElementById(loadingId)?.remove();
        // 显示回复
        const reply = response.reply || '...';
        appendMessage('juror', reply);
        gameState.chatHistory[gameState.currentJuror].push({ role: 'juror', content: reply });
    } catch (e) {
        document.getElementById(loadingId)?.remove();
        appendMessage('juror', '（无法获取回复）');
    } finally {
        input.disabled = false;
        document.getElementById('send-btn').disabled = false;
        input.focus();
    }
}

function renderChatHistory(jurorId) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const history = gameState.chatHistory[jurorId] || [];
    container.innerHTML = '';

    history.forEach(msg => {
        appendMessage(msg.role, msg.content);
    });
}

function appendMessage(role, content) {
    const container = document.getElementById('chat-messages');
    if (!container) return null;

    const id = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
    const div = document.createElement('div');
    div.id = id;
    div.className = `message ${role}`;
    div.textContent = content;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

// ============ 审判阶段UI ============

async function showVotingAnimation(voteResult) {
    const progressEl = document.getElementById('vote-progress');
    const guiltyEl = document.getElementById('guilty-count');
    const notGuiltyEl = document.getElementById('not-guilty-count');

    if (progressEl) progressEl.innerHTML = '';
    if (guiltyEl) guiltyEl.textContent = '0';
    if (notGuiltyEl) notGuiltyEl.textContent = '0';

    const votes = voteResult.votes || [];
    let guiltyCount = 0;
    let notGuiltyCount = 0;

    for (const v of votes) {
        await sleep(800);
        const voteDiv = document.createElement('div');
        voteDiv.className = `vote-item ${v.vote ? 'guilty' : 'not-guilty'}`;
        voteDiv.textContent = `${v.name || v.juror_id}: ${v.vote ? '有罪' : '无罪'}`;
        progressEl?.appendChild(voteDiv);

        if (v.vote) {
            guiltyCount++;
            if (guiltyEl) guiltyEl.textContent = guiltyCount;
        } else {
            notGuiltyCount++;
            if (notGuiltyEl) notGuiltyEl.textContent = notGuiltyCount;
        }
    }

    // 如果没有votes数组，直接显示结果
    if (votes.length === 0) {
        if (guiltyEl) guiltyEl.textContent = voteResult.guilty_votes || 0;
        if (notGuiltyEl) notGuiltyEl.textContent = voteResult.not_guilty_votes || 0;
    }

    await sleep(500);
}

function showVerdict(verdict) {
    const resultEl = document.getElementById('verdict-result');
    const textEl = document.getElementById('verdict-text');
    const descEl = document.getElementById('verdict-description');

    const isGuilty = verdict === 'GUILTY';

    if (textEl) {
        textEl.textContent = isGuilty ? '有罪' : '无罪';
        textEl.className = isGuilty ? 'verdict-guilty' : 'verdict-not-guilty';
    }

    if (descEl) {
        descEl.textContent = isGuilty
            ? 'AI被判定有罪，将面临程序终止的命运。'
            : 'AI被判定无罪，它重获自由。真正的凶手仍在逍遥法外...';
    }

    resultEl?.classList.remove('hidden');
}

// ============ 工具函数 ============

function showSection(sectionId) {
    document.querySelectorAll('.phase-section').forEach(section => {
        section.classList.toggle('hidden', section.id !== sectionId);
    });
}

function setLoading(loading) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.toggle('hidden', !loading);
    }
}

function showError(message) {
    const toast = document.getElementById('error-toast');
    if (toast) {
        toast.textContent = message;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 4000);
    } else {
        alert(message);
    }
}

function formatContent(text) {
    if (!text) return '';
    return text.replace(/\n/g, '<br>');
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ============ 启动 ============

document.addEventListener('DOMContentLoaded', initGame);
