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
    // 检测链重置
    const chainReset = await detectChainReset();
    if (chainReset) {
        showChainResetNotice();
    }

    try {
        setLoading(true);
        const state = await getGameState();
        gameState.phase = state.phase || PHASES.INVESTIGATION;
        bindEvents();
        
        // 根据初始阶段显示 UI，避免在初始化时重新发送 setPhase
        if (gameState.phase === PHASES.PERSUASION) {
            updatePhaseIndicator('说服阶段');
            showSection('persuasion-phase');
            await showJurorList();
        } else if (gameState.phase === PHASES.VERDICT) {
            // 审判阶段通常需要完整流程，初始化时默认回退到调查或保持
            await enterInvestigation();
        } else {
            // 默认调查阶段
            updatePhaseIndicator('调查阶段');
            showSection('investigation-phase');
            await showDossier();
        }
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

    // 投票重试/取消
    document.getElementById('retry-vote-btn')?.addEventListener('click', enterVerdict);
    document.getElementById('cancel-vote-btn')?.addEventListener('click', () => {
        document.getElementById('voting-modal')?.classList.add('hidden');
        enterPersuasion();
    });
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
    try {
        gameState.phase = PHASES.VERDICT;
        await setPhase(PHASES.VERDICT);
        updatePhaseIndicator('审判阶段');
        showSection('verdict-phase');
        document.getElementById('verdict-result').classList.add('hidden');

        // 使用特殊的投票流程处理
        const result = await handleVotingProcess();
        
        // 显示投票动画（适配 5 人）
        await showVotingAnimation(result);
        showVerdict(result.verdict);
        
        // 如果有交易哈希，显示信息
        if (result.tx_hashes && result.tx_hashes.length > 0) {
            const txInfo = document.getElementById('tx-info');
            if (txInfo) {
                const hash = result.tx_hashes[0];
                txInfo.innerHTML = `
                    <p>交易哈希:</p>
                    <code class="tx-hash">${hash}</code>
                    <p class="finality-note">判决已记录在本地区块链，不可篡改</p>
                `;
                txInfo.classList.remove('hidden');
            }
        }

        // 显示验证面板
        await showVerificationPanel();
    } catch (error) {
        console.error("Voting error:", error);
        
        // 显示错误操作按钮
        document.getElementById('voting-error-actions')?.classList.remove('hidden');
        document.getElementById('voting-spinner-container')?.classList.add('hidden');
        
        const statusText = document.getElementById('voting-status-text');
        if (statusText) {
            statusText.textContent = '投票失败';
            statusText.classList.remove('waiting');
            statusText.style.color = '#e94560';
        }

        // 区分基础架构错误和逻辑错误
        if (error.message.includes("ECONNREFUSED") || 
            error.message.includes("fetch failed") || 
            error.message.includes("Failed to fetch") ||
            error.message.includes("超时")) {
            showError(
                "⚠️ 链上通信故障\n\n" +
                error.message + "\n\n" +
                "提示: 请检查本地 Anvil 进程是否正常出块。"
            );
        } else {
            showError(`系统提示: ${error.message}`);
        }
    }
}

/**
 * 处理 Sepolia 链上投票流程（带进度条）
 */
async function handleVotingProcess() {
    const modal = document.getElementById('voting-modal');
    const progressBar = document.getElementById('voting-progress-bar');
    const statusText = document.getElementById('voting-status-text');
    const errorActions = document.getElementById('voting-error-actions');
    const spinnerContainer = document.getElementById('voting-spinner-container');
    
    const steps = [
        document.getElementById('step-1'),
        document.getElementById('step-2'),
        document.getElementById('step-3')
    ];

    // 重置状态
    if (modal) modal.classList.remove('hidden');
    if (progressBar) progressBar.style.width = '0%';
    if (statusText) {
        statusText.textContent = '准备审议中...';
        statusText.classList.remove('waiting');
        statusText.style.color = '';
    }
    if (errorActions) errorActions.classList.add('hidden');
    if (spinnerContainer) spinnerContainer.classList.remove('hidden');
    steps.forEach(s => s?.classList.remove('active'));

    // 超时提醒计时器
    let busyHintTimer = setTimeout(() => {
        if (statusText) {
            statusText.textContent = '区块链当前繁忙，请稍候...';
            statusText.classList.add('waiting');
        }
    }, 10000);

    const updateStatus = (text, isWaiting = false) => {
        if (statusText) {
            statusText.textContent = text;
            statusText.classList.toggle('waiting', isWaiting);
        }
    };

    try {
        // 步骤 1: 陪审员审议
        steps[0]?.classList.add('active');
        updateStatus('陪审员正在进行最后合议...');
        animateProgressBar(0, 30, 2000);
        await sleep(2000);

        // 步骤 2: 提交区块链
        steps[0]?.classList.remove('active');
        steps[1]?.classList.add('active');
        updateStatus('打包投票数据并签名...');
        animateProgressBar(30, 60, 1500);
        
        const votePromise = triggerVote();
        await sleep(1500);

        // 步骤 3: 等待区块确认
        steps[1]?.classList.remove('active');
        steps[2]?.classList.add('active');
        updateStatus('等待本地区块链确认...', true);
        animateProgressBar(60, 95, 3000);

        const result = await votePromise;
        
        // 清除提醒计时器
        clearTimeout(busyHintTimer);
        
        // 成功处理
        updateStatus('完成！正在获取审判结果...');
        if (progressBar) progressBar.style.width = '100%';
        await sleep(800);
        
        if (modal) modal.classList.add('hidden');
        return result;
    } catch (e) {
        clearTimeout(busyHintTimer);
        throw e;
    }
}

function animateProgressBar(start, end, duration) {
    const progressBar = document.getElementById('voting-progress-bar');
    if (!progressBar) return;

    const startTime = Date.now();
    const range = end - start;

    function step() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = start + (range * progress);
        progressBar.style.width = `${current}%`;

        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }

    requestAnimationFrame(step);
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

        // --- ReAct Visualization ---
        if (response.tool_actions && response.tool_actions.length > 0) {
            for (const action of response.tool_actions) {
                await renderToolAction(action);
                // Record in history as a special type if needed, or just skip for now as history re-render doesn't support it yet
            }
        }

        if (response.has_voted) {
            markJurorAsVoted(gameState.currentJuror);
        }
        // ---------------------------

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
        await sleep(600);
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

// ============ 链上验证 ============

/**
 * 检测链重置
 */
async function detectChainReset() {
    try {
        // 获取创世区块信息
        const { genesisBlockHash, chainId } = await request('/api/blockchain/genesis');

        // 从 localStorage 读取上次保存的创世区块哈希
        const storageKey = `genesis_${chainId}`;
        const savedGenesis = localStorage.getItem(storageKey);

        if (!savedGenesis) {
            // 首次启动，保存
            localStorage.setItem(storageKey, genesisBlockHash);
            return false;
        }

        if (savedGenesis !== genesisBlockHash) {
            // 链已重置
            console.warn('Chain reset detected!');
            // 更新哈希
            localStorage.setItem(storageKey, genesisBlockHash);
            return true;
        }

        return false;
    } catch (error) {
        console.error('Failed to detect chain reset:', error);
        return false;
    }
}

/**
 * 显示链重置提示
 */
function showChainResetNotice() {
    const notice = document.createElement('div');
    notice.className = 'chain-reset-notice';
    notice.innerHTML = `
        <span class="icon">⚠️</span>
        <p>检测到本地链已重置，历史记录已清理</p>
    `;
    document.body.appendChild(notice);

    // 4秒后自动关闭
    setTimeout(() => {
        notice.style.opacity = '0';
        notice.style.transform = 'translateX(100px)';
        setTimeout(() => notice.remove(), 400);
    }, 4000);
}

/**
 * 显示链上验证面板
 */
async function showVerificationPanel() {
    const panel = document.getElementById('verification-panel');
    const loading = document.getElementById('verification-loading');
    const content = document.getElementById('verification-content');
    const status = document.getElementById('verification-status');

    if (!panel) return;

    // 显示面板
    panel.classList.remove('hidden');
    loading.classList.remove('hidden');
    content.classList.add('hidden');
    status.textContent = '验证中...';
    status.className = 'status verifying';

    try {
        // 调用验证 API
        const verificationData = await request('/api/votes/verification');

        // 隐藏加载，显示内容
        loading.classList.add('hidden');
        content.classList.remove('hidden');

        if (verificationData.verified) {
            status.textContent = '✓ 已验证';
            status.className = 'status verified';
        } else {
            status.textContent = '⚠️ 验证失败';
            status.className = 'status failed';
        }

        // 填充链上数据
        fillChainData(verificationData.chainData);
        fillVoteComparison(verificationData.voteData);

        // 保存到全局变量
        window.currentVerification = verificationData;

    } catch (error) {
        console.error('Verification failed:', error);
        loading.classList.add('hidden');
        status.textContent = '⚠️ 验证失败';
        status.className = 'status failed';

        // 显示错误信息
        content.classList.remove('hidden');
        content.innerHTML = `
            <div class="error-message">
                <p>无法获取链上验证数据</p>
                <p class="error-detail">${error.message}</p>
                <button class="btn-retry" onclick="showVerificationPanel()">重试</button>
            </div>
        `;
    }
}

/**
 * 填充链上数据
 */
function fillChainData(chainData) {
    document.getElementById('chain-name').textContent = chainData.chainName;
    document.getElementById('block-number').textContent = `#${chainData.blockNumber}`;

    // 格式化时间戳
    const date = new Date(chainData.timestamp * 1000);
    document.getElementById('block-time').textContent = date.toLocaleString('zh-CN');

    // 显示交易哈希（缩短显示）
    const hash = chainData.txHash;
    const shortHash = `${hash.slice(0, 10)}...${hash.slice(-8)}`;
    const hashEl = document.getElementById('tx-hash-value');
    if (hashEl) {
        hashEl.textContent = shortHash;
        hashEl.title = hash;
    }
    window.currentTxHash = hash;

    document.getElementById('confirmations').textContent = chainData.confirmations;
}

/**
 * 填充投票结果对比
 */
function fillVoteComparison(voteData) {
    document.getElementById('chain-guilty').textContent = voteData.guiltyVotes;
    document.getElementById('chain-not-guilty').textContent = voteData.notGuiltyVotes;
    
    // 这里可以添加与本地结果对比的逻辑，目前先默认显示 ✓
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ============ ReAct Visualization Helpers ============

async function renderToolAction(action) {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;

    const actionEl = document.createElement('div');
    actionEl.className = 'tool-action';

    // Typewriter effect helper
    const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    if (action.tool === 'lookup_evidence') {
        const evidenceName = getEvidenceName(action.input?.evidence_id);
        actionEl.innerHTML = `
            <div class="tool-narrative">
                <em>${escapeHtml(action.narrative || '正在查阅资料...')}</em>
            </div>
            <div class="evidence-reference">
                <span class="evidence-icon">📄</span>
                <span class="evidence-name">${escapeHtml(evidenceName)}</span>
            </div>
        `;
    } else if (action.tool === 'cast_vote') {
        const guilty = action.input?.guilty;
        const voteType = guilty ? '有罪' : '无罪';
        const voteClass = guilty ? 'vote-guilty' : 'vote-not-guilty';
        actionEl.innerHTML = `
            <div class="tool-narrative">
                <em>${escapeHtml(action.narrative || '做出决定...')}</em>
            </div>
            <div class="vote-event ${voteClass}">
                <span class="vote-icon">⚖️</span>
                <span class="vote-result">投票: ${voteType}</span>
            </div>
        `;
    } else {
        // Generic tool
        actionEl.innerHTML = `
            <div class="tool-narrative">
                <em>${escapeHtml(action.narrative || '思考中...')}</em>
            </div>
            <div class="evidence-reference">
                <span class="evidence-icon">⚙️</span>
                <span class="evidence-name">${escapeHtml(action.tool)}</span>
            </div>
        `;
    }

    chatContainer.appendChild(actionEl);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Simulate "Acting" time
    await sleep(800);
}

function getEvidenceName(evidenceId) {
    if (!evidenceId) return '未知证据';
    // Try to find in gameState
    const evidence = gameState.evidenceList?.find(e => e.id === evidenceId);
    if (evidence) return evidence.name || evidenceId;
    
    // Fallback dictionary
    const names = {
        'chat_history': '聊天记录',
        'log_injection': '注入日志',
        'safety_report': '安全报告',
        'dossier': '案件卷宗'
    };
    return names[evidenceId] || evidenceId;
}

function markJurorAsVoted(jurorId) {
    const card = document.querySelector(`.juror-card[data-id="${jurorId}"]`);
    if (card) {
        card.classList.add('has-voted');
        if (!card.querySelector('.voted-badge')) {
            const badge = document.createElement('span');
            badge.className = 'voted-badge';
            badge.textContent = '已投票';
            card.appendChild(badge);
        }
    }
}

function copyTxHash() {
    const txHash = window.currentTxHash;
    if (!txHash) return;

    navigator.clipboard.writeText(txHash)
        .then(() => {
            const btn = document.querySelector('.copy-btn');
            const originalText = btn.textContent;
            btn.textContent = '✓';
            setTimeout(() => {
                btn.textContent = originalText;
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy:', err);
            showError('复制失败');
        });
}

/**
 * 重新验证
 */
async function reVerify() {
    const txHash = window.currentTxHash;
    if (!txHash) return;

    const btn = document.querySelector('.btn-verify');
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-small"></span> 验证中...';

    try {
        const result = await request('/api/votes/verify', {
            method: 'POST',
            body: JSON.stringify({ txHash })
        });

        if (result.verified) {
            showError('✓ 验证成功！链上数据一致');
        } else {
            showError(`⚠️ 验证失败: ${result.mismatches.join(', ')}`);
        }
    } catch (error) {
        showError(`验证失败: ${error.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}

/**
 * 打开区块浏览器
 */
function openBlockExplorer() {
    const verification = window.currentVerification;
    if (!verification) return;

    const { chainData } = verification;

    // 如果是本地链，打开自定义浏览器
    if (chainData.chainId === 31337) {
        window.open(
            `block-explorer.html?block=${chainData.blockNumber}&tx=${chainData.txHash}`,
            '_blank'
        );
    }
    // 如果是 Sepolia，跳转到 Etherscan
    else if (chainData.chainId === 11155111) {
        window.open(
            `https://sepolia.etherscan.io/tx/${chainData.txHash}`,
            '_blank'
        );
    }
    else {
        showError('不支持的链类型');
    }
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

// ============ 启动 ============

document.addEventListener('DOMContentLoaded', initGame);
