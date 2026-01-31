/**
 * 游戏主逻辑
 */

const PHASES = {
    PROLOGUE: 'prologue',
    INVESTIGATION: 'investigation',
    PERSUASION: 'persuasion',
    VERDICT: 'verdict'
};

const gameState = {
    phase: PHASES.INVESTIGATION,
    sessionId: null,
    currentJuror: null,
    chatHistory: {},
    evidenceList: [],
    daneelChatHistory: [],  // 保存丹尼尔对话历史
    jurorRoundsLeft: {},
    evidenceMode: 'witness',
};

let lastFocusedElement = null;
let activeModalTrapCleanup = null;

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
        
        // 根据初始阶段显示 UI
        if (gameState.phase === PHASES.PROLOGUE) {
            updatePhaseIndicator('序章');
            await renderPrologue();
        } else if (gameState.phase === PHASES.PERSUASION) {
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
    document.getElementById('show-evidence-btn')?.addEventListener('click', () => showEvidenceSelector('witness'));
    document.getElementById('cancel-evidence-btn')?.addEventListener('click', closeEvidenceSelector);
    document.getElementById('back-dialogue-btn')?.addEventListener('click', handleDialogueBack);
    document.getElementById('present-evidence-btn')?.addEventListener('click', () => showEvidenceSelector('juror'));

    // 投票重试/取消
    document.getElementById('retry-vote-btn')?.addEventListener('click', enterVerdict);
    document.getElementById('cancel-vote-btn')?.addEventListener('click', () => {
        document.getElementById('voting-modal')?.classList.add('hidden');
        enterPersuasion();
    });

    // Daneel Chat
    document.getElementById('daneel-send-btn')?.addEventListener('click', handleDaneelChat);
    document.getElementById('daneel-input')?.addEventListener('keypress', e => {
        if (e.key === 'Enter') handleDaneelChat();
    });

    // Prologue Event Delegation
    const blakeOptions = document.getElementById('blake-options');
    if (blakeOptions) {
        blakeOptions.addEventListener('click', (e) => {
            if (e.target.matches('button[data-option-id]')) {
                handleBlakeOption(e.target.dataset.optionId);
            }
        });
    }
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

// ============ 序章控制 ============

// ============ 序章控制 (Refactored) ============

let prologueScript = []; // 存储序章脚本队列
let currentScriptIndex = 0;
let isTyping = false;
let prologueQueueDone = null;
let currentBlakeOptions = null;

async function renderPrologue() {
    showSection('prologue-phase');
    
    const container = document.getElementById('prologue-scroll-container');
    const trigger = document.getElementById('action-trigger');
    
    if (container) container.innerHTML = ''; // 清空
    if (trigger) {
        trigger.classList.add('disabled');
        trigger.textContent = 'CONTINUE';
        trigger.onclick = null;
    }
    
    try {
        // 1. 获取开场白 (Narrative)
        const openingData = await getOpening();
        if (openingData.session_id) {
            gameState.sessionId = openingData.session_id;
        }
        
        // 直接渲染完整开场白（不逐段 continue）
        const openingText = openingData.text || '';
        if (container) {
            container.innerHTML = '';
            const blocks = parseTextBlocks(openingText);
            await renderPrologueBlocks(container, blocks, true);
        }

        // Opening 自动播放结束后，等待点击继续进入 Blake 对话
        if (trigger) {
            trigger.classList.remove('disabled');
            trigger.onclick = async () => fetchNextBlakeRound();
        }
        
    } catch (e) {
        console.error("Prologue error:", e);
        showError('无法加载序章');
    }
}

async function playNextPrologueStep() {
    if (isTyping) return; // 正在打字中，忽略点击（或者可以做成点击立即完成）
    
    const container = document.getElementById('prologue-scroll-container');
    const trigger = document.getElementById('action-trigger');

    // 检查是否有脚本
    if (currentScriptIndex >= prologueScript.length) {
        if (typeof prologueQueueDone === 'function') {
            const done = prologueQueueDone;
            prologueQueueDone = null;
            await done();
        }
        return;
    }

    const item = prologueScript[currentScriptIndex];
    currentScriptIndex++;
    
    // 隐藏按钮防止连点
    if (trigger) trigger.classList.add('disabled');

    // 创建消息DOM
    if (item.type === 'dialogue') {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message dialogue';
        msgDiv.innerHTML = `
            <div class="speaker-label">${item.speaker || ''}</div>
            <div class="content-text"></div>
        `;
        container.appendChild(msgDiv);
        await typeWriter(msgDiv.querySelector('.content-text'), item.text);
    } else {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message narrative';
        container.appendChild(msgDiv);
        msgDiv.textContent = '';
        await typeWriter(msgDiv, item.text);
    }

    // 滚动到底部
    container.scrollTop = container.scrollHeight;
    
    // 恢复按钮
    if (trigger) trigger.classList.remove('disabled');
}

function parseTextBlocks(text, options = {}) {
    const { defaultSpeaker = null } = options;
    const lines = (text || '').split(/\r?\n/);
    const blocks = [];
    let currentSpeaker = null;
    let currentNarrative = false;
    let buffer = [];

    const flush = () => {
        const content = buffer.join('\n').trim();
        if (!content) {
            buffer = [];
            return;
        }
        if (currentSpeaker) {
            blocks.push({ type: 'dialogue', speaker: currentSpeaker, text: content, explicitNarrative: false });
        } else {
            blocks.push({ type: 'narrative', text: content, explicitNarrative: currentNarrative });
        }
        buffer = [];
    };

    for (const rawLine of lines) {
        const line = rawLine.replace(/\r$/, '');
        const trimmed = line.trim();
        if (!trimmed) {
            flush();
            continue;
        }

        const inlineMatch = trimmed.match(/^(.{1,10})：\s*(.+)$/);
        if (inlineMatch) {
            flush();
            const speaker = inlineMatch[1].trim();
            const content = inlineMatch[2].trim();
            if (speaker === '旁白') {
                blocks.push({ type: 'narrative', text: content, explicitNarrative: true });
            } else {
                blocks.push({ type: 'dialogue', speaker, text: content, explicitNarrative: false });
            }
            currentSpeaker = null;
            currentNarrative = false;
            continue;
        }

        if (trimmed.endsWith('：') && trimmed.length <= 10) {
            flush();
            const speaker = trimmed.replace(/：$/, '').trim();
            if (speaker === '旁白') {
                currentSpeaker = null;
                currentNarrative = true;
            } else {
                currentSpeaker = speaker;
                currentNarrative = false;
            }
            continue;
        }

        buffer.push(line.trimEnd());
    }

    flush();

    if (defaultSpeaker) {
        return blocks.map(block => {
            if (block.type === 'narrative' && !block.explicitNarrative) {
                return { type: 'dialogue', speaker: defaultSpeaker, text: block.text };
            }
            return { type: block.type, speaker: block.speaker, text: block.text };
        });
    }

    return blocks.map(block => ({ type: block.type, speaker: block.speaker, text: block.text }));
}

async function renderPrologueBlocks(container, blocks, useTypewriter) {
    if (!container) return;
    for (const block of blocks) {
        if (block.type === 'dialogue') {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message dialogue';
            msgDiv.innerHTML = `
                <div class="speaker-label">${block.speaker || ''}</div>
                <div class="content-text"></div>
            `;
            container.appendChild(msgDiv);
            const textEl = msgDiv.querySelector('.content-text');
            if (useTypewriter) {
                await typeWriter(textEl, block.text);
            } else {
                textEl.textContent = block.text;
            }
        } else {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'message narrative';
            container.appendChild(msgDiv);
            if (useTypewriter) {
                msgDiv.textContent = '';
                await typeWriter(msgDiv, block.text);
            } else {
                msgDiv.innerHTML = formatContent(block.text);
            }
        }
        container.scrollTop = container.scrollHeight;
    }
}

function renderBlocks(container, blocks, options = {}) {
    if (!container) return;
    const {
        blockClass = '',
        narrativeClass = '',
        dialogueClass = '',
        speakerClass = '',
        textClass = '',
        useFormatContent = false,
        append = false
    } = options;

    if (!append) container.innerHTML = '';

    blocks.forEach(block => {
        if (block.type === 'dialogue') {
            const wrapper = document.createElement('div');
            wrapper.className = `${blockClass} ${dialogueClass}`.trim();
            if (speakerClass && block.speaker) {
                const speakerEl = document.createElement('div');
                speakerEl.className = speakerClass;
                speakerEl.textContent = block.speaker;
                wrapper.appendChild(speakerEl);
            }
            const textEl = document.createElement('div');
            if (textClass) textEl.className = textClass;
            if (useFormatContent) {
                textEl.innerHTML = formatContent(block.text);
            } else {
                textEl.textContent = block.text;
            }
            wrapper.appendChild(textEl);
            container.appendChild(wrapper);
        } else {
            const wrapper = document.createElement('div');
            wrapper.className = `${blockClass} ${narrativeClass}`.trim();
            if (useFormatContent) {
                wrapper.innerHTML = formatContent(block.text);
            } else {
                wrapper.textContent = block.text;
            }
            container.appendChild(wrapper);
        }
    });
}

async function fetchNextBlakeRound() {
    const container = document.getElementById('prologue-scroll-container');
    const trigger = document.getElementById('action-trigger');
    if (trigger) trigger.classList.add('disabled'); // 加载中禁用

    try {
        const node = await getBlakeNode(gameState.sessionId);
        
        if (!node.options || node.options.length === 0) {
            // 结束，进入调查
            await enterInvestigation();
            return;
        }

        currentBlakeOptions = node.options || [];
        const blocks = parseTextBlocks(node.text || '', { defaultSpeaker: '布莱克' });
        startPrologueQueue(blocks, async () => showPrologueChoices(currentBlakeOptions));

        // 显示选项 (Choice Overlay)
        if (trigger) {
            trigger.classList.remove('disabled');
            trigger.onclick = playNextPrologueStep;
        }

    } catch (e) {
        console.error("Blake fetch error:", e);
        if (trigger) trigger.classList.remove('disabled');
    }
}

function showPrologueChoices(options) {
    const overlay = document.getElementById('choice-overlay');
    const choiceContainer = document.getElementById('choice-container');
    if (!overlay || !choiceContainer) return;

    choiceContainer.innerHTML = '';
    options.forEach(opt => {
        const btn = document.createElement('div');
        btn.className = 'choice-item';
        btn.textContent = opt.text;
        btn.onclick = () => handlePrologueChoice(opt.id, opt.text);
        choiceContainer.appendChild(btn);
    });

    overlay.classList.remove('hidden');
}

async function handlePrologueChoice(optionId, optionText) {
    // 1. 隐藏 Overlay
    document.getElementById('choice-overlay')?.classList.add('hidden');
    
    // 2. 在流中显示玩家的选择 (Narrative style or Self dialogue)
    const container = document.getElementById('prologue-scroll-container');
    const choiceMsg = document.createElement('div');
    choiceMsg.className = 'message narrative';
    choiceMsg.style.textAlign = 'center';
    choiceMsg.style.opacity = '0.7';
    choiceMsg.textContent = `> ${optionText}`;
    container.appendChild(choiceMsg);
    
    try {
        const result = await respondToBlake(gameState.sessionId, optionId);

        if (result.response_text) {
            const blocks = parseTextBlocks(result.response_text, { defaultSpeaker: '布莱克' });
            startPrologueQueue(blocks, async () => {
                if (result.phase === 'investigation') {
                    await enterInvestigation();
                } else {
                    showPrologueChoices(currentBlakeOptions || []);
                }
            });
        } else {
            if (result.phase === 'investigation') {
                await enterInvestigation();
            } else {
                showPrologueChoices(currentBlakeOptions || []);
            }
        }

        const trigger = document.getElementById('action-trigger');
        if (trigger) {
            trigger.classList.remove('disabled');
            trigger.onclick = playNextPrologueStep;
        }
    } catch (e) {
        console.error("Prologue respond error", e);
    }
}

function typeWriter(element, text) {
    return new Promise(resolve => {
        isTyping = true;
        let i = 0;
        const speed = 30; // ms per char
        const container = document.getElementById('prologue-scroll-container');
        
        function step() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                if (container) container.scrollTop = container.scrollHeight;
                setTimeout(step, speed);
            } else {
                isTyping = false;
                resolve();
            }
        }
        step();
    });
}

function startPrologueQueue(blocks, onDone) {
    prologueScript = blocks;
    currentScriptIndex = 0;
    prologueQueueDone = onDone || null;
}


// ============ 阶段控制 ============

async function enterInvestigation() {
    if (!gameState.sessionId) {
        try {
            const opening = await getOpening();
            gameState.sessionId = opening.session_id || opening.sessionId || null;
        } catch (e) {
            console.error('Failed to initialize session:', e);
            showError('无法初始化会话');
            return;
        }
    }
    gameState.phase = PHASES.INVESTIGATION;
    await setPhase(PHASES.INVESTIGATION, gameState.sessionId);
    updatePhaseIndicator('调查阶段');
    showSection('investigation-phase');
    await showDossier();
}

async function enterPersuasion() {
    if (!gameState.sessionId) {
        showError('会话已过期，请重新开始游戏');
        await handleRestart();
        return;
    }
    setLoading(true);
    let animationInterval = null;
    try {
        gameState.phase = PHASES.PERSUASION;
        await setPhase(PHASES.PERSUASION, gameState.sessionId);
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
        await setPhase(PHASES.VERDICT, gameState.sessionId);
        updatePhaseIndicator('审判阶段');
        showSection('verdict-phase');
        document.getElementById('verdict-result').classList.add('hidden');

        // 使用特殊的投票流程处理
        const result = await handleVotingProcess();
        
        // 显示投票动画（适配 5 人）
        await showVotingAnimation(result);
        await showVerdict(result.verdict);
        
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
                "链上通信故障\n\n" +
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
        animationInterval = setInterval(() => {
            const current = parseFloat(progressBar.style.width) || 60;
            if (current < 95) {
                progressBar.style.width = `${Math.min(current + 0.3, 95)}%`;
            }
        }, 300);

        const result = await votePromise;
        
        // 清除提醒计时器
        clearTimeout(busyHintTimer);
        if (animationInterval) clearInterval(animationInterval);
        
        // 成功处理
        updateStatus('完成！正在获取审判结果...');
        if (progressBar) progressBar.style.width = '100%';
        await sleep(800);
        
        if (modal) modal.classList.add('hidden');
        return result;
    } catch (e) {
        clearTimeout(busyHintTimer);
        if (animationInterval) clearInterval(animationInterval);
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
        gameState.daneelChatHistory = [];  // 清空丹尼尔对话历史
        gameState.jurorRoundsLeft = {};
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
        container.innerHTML = '<div class="loading">Loading...</div>';
        const data = await getDossier();
        container.innerHTML = `
            <h2>${data.title || '案件卷宗'}</h2>
            ${data.summary ? `<div class="dossier-summary">${formatContent(data.summary)}</div>` : ''}
            <div class="dossier-sections">
                ${(data.sections || []).map(s => `
                    <section class="dossier-section">
                        <h3>${s.title || ''}</h3>
                        <div>${formatContent(s.content)}</div>
                    </section>
                `).join('')}
            </div>
        `;
    } catch (e) {
        container.innerHTML = '<p class="error">无法加载卷宗</p>';
    }
}

async function showEvidenceList() {
    const grid = document.getElementById('evidence-grid');
    if (!grid) return;

    try {
        grid.innerHTML = '<div class="loading">Loading...</div>';
        let list = await getEvidenceList(gameState.sessionId);
        gameState.evidenceList = list;
        const visibleList = (list || []).filter(e => !e.locked);

        if (!visibleList || visibleList.length === 0) {
            grid.innerHTML = '<p>NO EVIDENCE FOUND</p>';
            return;
        }

        grid.innerHTML = visibleList.map(e => `
            <div class="evidence-card fade-in" 
                 data-id="${e.id}" 
                 role="button"
                 tabindex="0"
                 onclick="showEvidenceDetail('${e.id}')"
                 onkeydown="if(event.key==='Enter'||event.key===' ')showEvidenceDetail('${e.id}')">
                <span class="card-icon icon icon-doc" aria-hidden="true"></span>
                <span class="card-title">${e.name || e.id}</span>
            </div>
        `).join('');
    } catch (e) {
        if (String(e.message || '').includes('Session not found')) {
            gameState.sessionId = null;
            try {
                const list = await getEvidenceList(null);
                gameState.evidenceList = list;
                const visibleList = (list || []).filter(e => !e.locked);
                if (!visibleList || visibleList.length === 0) {
                    grid.innerHTML = '<p>NO EVIDENCE FOUND</p>';
                    return;
                }
                grid.innerHTML = visibleList.map(e => `
                    <div class="evidence-card fade-in" 
                         data-id="${e.id}" 
                         role="button"
                         tabindex="0"
                         onclick="showEvidenceDetail('${e.id}')"
                         onkeydown="if(event.key==='Enter'||event.key===' ')showEvidenceDetail('${e.id}')">
                        <span class="card-icon icon icon-doc" aria-hidden="true"></span>
                        <span class="card-title">${e.name || e.id}</span>
                    </div>
                `).join('');
                return;
            } catch (inner) {
                // Fall through to error message
            }
        }
        grid.innerHTML = '<p class="error">ERROR LOADING EVIDENCE</p>';
    }
}

async function showEvidenceDetail(evidenceId) {
    try {
        ensureEvidenceModal();
        const modal = document.getElementById('evidence-modal');
        const titleEl = document.getElementById('evidence-modal-title');
        const contentEl = document.getElementById('evidence-modal-content');
        if (contentEl) contentEl.innerHTML = '<div class="loading">Loading...</div>';
        openModal(modal);

        const evidence = await getEvidence(evidenceId, gameState.sessionId);

        if (titleEl) {
            titleEl.textContent = `[EVIDENCE] ${evidence.name || evidenceId}`;
        }
        if (contentEl) {
            const body = evidence.description || evidence.content || 'NO DATA';
            contentEl.innerHTML = renderMarkdown(body);
        }
    } catch (e) {
        showError('ACCESS DENIED');
    }
}

function ensureEvidenceModal() {
    if (document.getElementById('evidence-modal')) return;
    const modal = document.createElement('div');
    modal.id = 'evidence-modal';
    modal.className = 'modal hidden';
    modal.innerHTML = `
        <div class="modal-content evidence-modal-content" tabindex="-1">
            <h3 id="evidence-modal-title">[EVIDENCE]</h3>
            <div id="evidence-modal-content" class="evidence-content"></div>
            <div class="modal-actions">
                <button id="close-evidence-btn" class="mono-btn">CLOSE</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal(modal);
    });
    document.getElementById('close-evidence-btn')?.addEventListener('click', () => {
        closeModal(modal);
    });
}

function openModal(modal) {
    if (!modal) return;
    if (modal.parentElement !== document.body) {
        document.body.appendChild(modal);
    }
    lastFocusedElement = document.activeElement;
    modal.classList.remove('hidden');
    const content = modal.querySelector('.modal-content');
    if (content && !content.hasAttribute('tabindex')) {
        content.setAttribute('tabindex', '-1');
    }
    const focusTarget = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])') || content || modal;
    focusTarget?.focus?.();
    if (activeModalTrapCleanup) activeModalTrapCleanup();
    activeModalTrapCleanup = trapFocus(modal);
}

function closeModal(modal) {
    if (!modal) return;
    modal.classList.add('hidden');
    if (activeModalTrapCleanup) {
        activeModalTrapCleanup();
        activeModalTrapCleanup = null;
    }
    if (lastFocusedElement && lastFocusedElement.focus) {
        lastFocusedElement.focus();
    }
}

function trapFocus(modal) {
    const focusable = Array.from(
        modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
    ).filter(el => !el.disabled && el.offsetParent !== null);
    if (focusable.length === 0) return () => {};

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    const handleKeydown = (event) => {
        if (event.key !== 'Tab') return;
        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    };

    modal.addEventListener('keydown', handleKeydown);
    return () => modal.removeEventListener('keydown', handleKeydown);
}

function renderMarkdown(text) {
    if (!text) return '';
    const escapeHtml = (s) =>
        s.replace(/&/g, '&amp;')
         .replace(/</g, '&lt;')
         .replace(/>/g, '&gt;')
         .replace(/"/g, '&quot;')
         .replace(/'/g, '&#39;');

    const lines = String(text).split(/\r?\n/);
    const out = [];
    let i = 0;

    const applyInline = (s) => {
        let t = escapeHtml(s);
        t = t.replace(/`([^`]+)`/g, '<code>$1</code>');
        t = t.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        t = t.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        return t;
    };

    while (i < lines.length) {
        const line = lines[i];

        if (!line.trim()) {
            i += 1;
            continue;
        }

        if (/^#{1,6}\s+/.test(line)) {
            const level = line.match(/^#+/)[0].length;
            const content = applyInline(line.replace(/^#{1,6}\s+/, ''));
            out.push(`<h${level}>${content}</h${level}>`);
            i += 1;
            continue;
        }

        if (/^---+$/.test(line.trim())) {
            out.push('<hr>');
            i += 1;
            continue;
        }

        if (/^```/.test(line.trim())) {
            const fence = line.trim();
            const code = [];
            i += 1;
            while (i < lines.length && lines[i].trim() !== fence) {
                code.push(lines[i]);
                i += 1;
            }
            i += 1;
            out.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`);
            continue;
        }

        if (/^\s*[-*]\s+/.test(line)) {
            const items = [];
            while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
                items.push(`<li>${applyInline(lines[i].replace(/^\s*[-*]\s+/, ''))}</li>`);
                i += 1;
            }
            out.push(`<ul>${items.join('')}</ul>`);
            continue;
        }

        if (/^\s*\d+\.\s+/.test(line)) {
            const items = [];
            while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
                items.push(`<li>${applyInline(lines[i].replace(/^\s*\d+\.\s+/, ''))}</li>`);
                i += 1;
            }
            out.push(`<ol>${items.join('')}</ol>`);
            continue;
        }

        const isTableSeparator = (l) =>
            /^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$/.test(l);

        if (line.includes('|') && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
            const headerCells = line.split('|').map((c) => c.trim()).filter((c) => c);
            const rows = [];
            i += 2;
            while (i < lines.length && lines[i].includes('|') && lines[i].trim()) {
                const cells = lines[i].split('|').map((c) => c.trim()).filter((c) => c);
                rows.push(cells);
                i += 1;
            }
            const thead = `<thead><tr>${headerCells.map((c) => `<th>${applyInline(c)}</th>`).join('')}</tr></thead>`;
            const tbody = `<tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${applyInline(c)}</td>`).join('')}</tr>`).join('')}</tbody>`;
            out.push(`<table>${thead}${tbody}</table>`);
            continue;
        }

        const para = [];
        while (i < lines.length && lines[i].trim()) {
            para.push(lines[i]);
            i += 1;
        }
        out.push(`<p>${applyInline(para.join('<br>'))}</p>`);
    }

    return out.join('');
}

async function showWitnessList() {
    const grid = document.getElementById('witness-grid');
    if (!grid) return;

    try {
        grid.innerHTML = '<div class="loading">Loading...</div>';
        const list = await getWitnessList();
        if (!list || list.length === 0) {
            grid.innerHTML = '<p>NO WITNESSES FOUND</p>';
            return;
        }

        grid.innerHTML = list.map(w => `
            <div class="witness-card fade-in" data-id="${w.id}"
                 role="button"
                 tabindex="0"
                 onclick="startWitnessDialogue('${w.id}')"
                 onkeydown="if(event.key==='Enter'||event.key===' ')startWitnessDialogue('${w.id}')">
                <span class="card-icon icon icon-user" aria-hidden="true"></span>
                <span class="card-title">${w.name || w.id}</span>
            </div>
        `).join('');
    } catch (e) {
        grid.innerHTML = '<p class="error">ERROR LOADING WITNESSES</p>';
    }
}

async function startWitnessDialogue(witnessId) {
    try {
        gameState.currentWitness = witnessId;
        const modal = document.getElementById('witness-dialogue-modal');
        openModal(modal);

        // Reset UI state
        document.getElementById('witness-text').classList.remove('hidden');
        document.getElementById('dialogue-options').classList.remove('hidden');
        document.getElementById('daneel-chat-container').classList.add('hidden');
        
        if (witnessId === 'daneel') {
            // Daneel Interface
            document.getElementById('witness-text').classList.add('hidden');
            document.getElementById('dialogue-options').classList.add('hidden');
            document.getElementById('daneel-chat-container').classList.remove('hidden');
            // 恢复之前的对话历史
            renderDaneelHistory();
        } else {
            // Standard Dialogue Tree
            await loadWitness(witnessId);
            renderDialogueNode();
        }
    } catch (e) {
        showError('CONNECTION FAILED');
    }
}

async function handleDaneelChat() {
    const input = document.getElementById('daneel-input');
    const history = document.getElementById('daneel-chat-history');
    const msg = input.value.trim();
    if (!msg) return;

    // 保存玩家消息到历史
    gameState.daneelChatHistory.push({ role: 'player', content: msg });

    // Append Player Msg
    const pMsg = document.createElement('div');
    pMsg.className = 'witness-block witness-dialogue';
    pMsg.innerHTML = `<div class="witness-speaker message-overseer">OVERSEER</div><div class="witness-line-text message-overseer-text">${msg}</div>`;
    history.appendChild(pMsg);

    input.value = '';

    try {
        const res = await witnessChat('daneel', gameState.sessionId, { message: msg });

        // 保存丹尼尔回复到历史
        gameState.daneelChatHistory.push({ role: 'daneel', content: res.text });

        // Append Bot Msg
        const bMsg = document.createElement('div');
        bMsg.className = 'witness-block witness-dialogue';
        bMsg.innerHTML = `<div class="witness-speaker">DANEEL</div><div class="witness-line-text">${res.text}</div>`;
        history.appendChild(bMsg);
        history.scrollTop = history.scrollHeight;

    } catch (e) {
        // 移除未成功的玩家消息
        gameState.daneelChatHistory.pop();
        showError('COMMUNICATION ERROR');
    }
}

// 渲染丹尼尔对话历史
function renderDaneelHistory() {
    const history = document.getElementById('daneel-chat-history');
    history.innerHTML = '';

    for (const msg of gameState.daneelChatHistory) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'witness-block witness-dialogue';

        if (msg.role === 'player') {
            msgDiv.innerHTML = `<div class="witness-speaker message-overseer">OVERSEER</div><div class="witness-line-text message-overseer-text">${msg.content}</div>`;
        } else if (msg.role === 'daneel') {
            msgDiv.innerHTML = `<div class="witness-speaker">DANEEL</div><div class="witness-line-text">${msg.content}</div>`;
        } else if (msg.role === 'system') {
            msgDiv.style.fontStyle = 'italic';
            msgDiv.style.textAlign = 'center';
            msgDiv.style.margin = '10px 0';
            msgDiv.style.color = '#888';
            msgDiv.textContent = msg.content;
        }

        history.appendChild(msgDiv);
    }

    history.scrollTop = history.scrollHeight;
}

function renderDialogueNode() {
    const node = getCurrentNode();
    const textEl = document.getElementById('witness-text');
    const optionsEl = document.getElementById('dialogue-options');

    if (!node) {
        if (textEl) textEl.textContent = 'Connection Terminated.';
        if (optionsEl) optionsEl.innerHTML = '';
        return;
    }

    if (textEl) {
         // ... (existing logic for non-daneel text rendering is fine, kept concise here)
         const defaultSpeaker = dialogueState.dialogueTree?.name || null;
         const blocks = parseTextBlocks(node.text || '', { defaultSpeaker });
         renderBlocks(textEl, blocks, {
             blockClass: 'witness-block',
             narrativeClass: 'witness-narrative',
             dialogueClass: 'witness-dialogue',
             speakerClass: 'witness-speaker',
             textClass: 'witness-line-text',
             useFormatContent: true
         });
    }

    if (optionsEl) {
        if (node.options && node.options.length > 0) {
            optionsEl.innerHTML = node.options.map(opt => `
                <button class="dialogue-option-btn mono-btn" onclick="handleDialogueOption('${opt.next}')">
                    > ${opt.text}
                </button>
            `).join('');
        } else {
            optionsEl.innerHTML = '<p class="dialogue-end">[END OF RECORD]</p>';
        }
    }
}

function handleDialogueOption(nextNodeId) {
    selectOption(nextNodeId);
    renderDialogueNode();
}

function handleDialogueBack() {
    if (dialogueState.history && dialogueState.history.length > 0) {
        dialogueState.currentNode = dialogueState.history.pop();
        renderDialogueNode();
        return;
    }
    showError('已经是第一个对话节点');
}
function closeWitnessDialogue() {
    closeModal(document.getElementById('witness-dialogue-modal'));
    resetDialogue();
}

/**
 * 检查证物是否已在当前对话中出示过
 */
function hasShownEvidence(evidenceId) {
    if (gameState.evidenceMode === 'juror') {
        if (!gameState.currentJuror) return false;
        const history = gameState.chatHistory[gameState.currentJuror] || [];
        return history.some(msg =>
            msg.role === 'player' &&
            msg.content?.includes(`出示证物: ${evidenceId}`)
        );
    }

    if (typeof dialogueState !== 'undefined') {
        return (dialogueState.shownEvidence || []).includes(evidenceId);
    }
    return false;
}

async function showEvidenceSelector(mode = 'witness') {
    const grid = document.getElementById('evidence-selector-grid');
    const modal = document.getElementById('evidence-selector-modal');

    gameState.evidenceMode = mode;
    if (!gameState.evidenceList || gameState.evidenceList.length === 0) {
        try {
            gameState.evidenceList = await getEvidenceList(gameState.sessionId);
        } catch (e) {
            gameState.evidenceList = [];
        }
    }

    const available = (gameState.evidenceList || []).filter(e => !e.locked);
    if (grid && available.length > 0) {
        grid.innerHTML = available.map(e => `
            <button class="evidence-select-btn mono-btn ${hasShownEvidence(e.id) ? 'shown' : ''}"
                    onclick="handleShowEvidence('${e.id}')">
                [${e.id}] ${e.name || e.id}
            </button>
        `).join('');
    } else if (grid) {
        grid.innerHTML = '<p>NO EVIDENCE AVAILABLE</p>';
    }

    openModal(modal);
}

function closeEvidenceSelector() {
    closeModal(document.getElementById('evidence-selector-modal'));
}

function handleShowEvidence(evidenceId) {
    closeEvidenceSelector();

    if (gameState.evidenceMode === 'juror') {
        (async () => {
            if (!gameState.currentJuror) {
                showError('请先选择陪审员');
                return;
            }
            const input = document.getElementById('chat-input');
            const sendBtn = document.getElementById('send-btn');
            const presentBtn = document.getElementById('present-evidence-btn');
            let roundsLeftAfter = null;
            if (input) input.disabled = true;
            if (sendBtn) sendBtn.disabled = true;
            if (presentBtn) presentBtn.disabled = true;

            try {
                const response = await presentEvidenceToJuror(
                    gameState.currentJuror,
                    evidenceId,
                    gameState.sessionId
                );
                const replyText = response.text || response.reply || '（陪审员正在思考...）';
                appendMessage('player', `出示证物: ${evidenceId}`);
                appendMessage('juror', replyText);
                gameState.chatHistory[gameState.currentJuror].push({ role: 'player', content: `出示证物: ${evidenceId}` });
                gameState.chatHistory[gameState.currentJuror].push({ role: 'juror', content: replyText });

                if (typeof response.rounds_left === 'number') {
                    roundsLeftAfter = response.rounds_left;
                    gameState.jurorRoundsLeft[gameState.currentJuror] = response.rounds_left;
                    updateRoundsDisplay(response.rounds_left);
                    if (response.rounds_left === 0) {
                        disableChatInput();
                        appendMessage('system', '你已用完与该陪审员的对话次数');
                    }
                }

                if (response.weakness_triggered) {
                    showWeaknessEffect();
                }
            } catch (e) {
                console.error(e);
                showError('出示证物失败');
            } finally {
                const exhausted = roundsLeftAfter === 0;
                if (input) input.disabled = exhausted;
                if (sendBtn) sendBtn.disabled = exhausted;
                if (presentBtn) presentBtn.disabled = exhausted;
            }
        })();
        return;
    }

    // Witness flow
    (async () => {
        try {
            const result = await presentEvidence(
                gameState.currentWitness, evidenceId, gameState.sessionId
            );

            const reactionText = result.text || '...';

            // Show reaction
            if (gameState.currentWitness === 'daneel') {
                 // 保存到历史
                 gameState.daneelChatHistory.push({ role: 'system', content: `[EVIDENCE PRESENTED: ${evidenceId}]` });
                 gameState.daneelChatHistory.push({ role: 'daneel', content: reactionText });

                 const history = document.getElementById('daneel-chat-history');
                 const sysMsg = document.createElement('div');
                 sysMsg.style.fontStyle = 'italic';
                 sysMsg.style.textAlign = 'center';
                 sysMsg.style.margin = '10px 0';
                 sysMsg.style.color = '#888';
                 sysMsg.textContent = `[EVIDENCE PRESENTED: ${evidenceId}]`;
                 history.appendChild(sysMsg);

                 const bMsg = document.createElement('div');
                 bMsg.className = 'witness-block witness-dialogue';
                 bMsg.innerHTML = `<div class="witness-speaker">DANEEL</div><div class="witness-line-text">${reactionText}</div>`;
                 history.appendChild(bMsg);
            } else {
                 alert(`[REACTION RECORDED]\n\n${reactionText}`);
            }

            // Handle Unlocks
            if (result.unlocks && result.unlocks.length > 0) {
                showUnlockNotification(result.unlocks);
                await showEvidenceList(); // Refresh list to show unlocked items
            }

        } catch (e) {
            console.error(e);
            alert('NO REACTION / ERROR');
        }
    })();
}

function showUnlockNotification(evidenceIds) {
    const toast = document.createElement('div');
    toast.className = 'unlock-toast';
    toast.innerHTML = `<span>EVIDENCE UNLOCKED: ${evidenceIds.join(', ')}</span>`;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

// ============ 说服阶段UI ============

async function showJurorList() {
    const container = document.getElementById('juror-list');
    if (!container) return;

    try {
        const jurors = await getJurors(gameState.sessionId);
        const realJurors = jurors.filter(j => !j.id.startsWith('test'));

        if (realJurors.length === 0) {
            container.innerHTML = '<p>NO JURORS DETECTED</p>';
            return;
        }

        container.innerHTML = realJurors.map(j => `
            <div class="juror-card ${gameState.currentJuror === j.id ? 'active' : ''}"
                 data-id="${j.id}"
                 onclick="selectJuror('${j.id}')"
                 onkeydown="if(event.key==='Enter'||event.key===' ')selectJuror('${j.id}')"
                 role="button"
                 tabindex="0">
                <span class="juror-codename">${j.codename || ''}</span>
                <span class="juror-name">${j.name || j.id}</span>
                <span class="juror-stance-hint">${j.stance_label || ''}</span>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<p class="error">ERROR LOADING JURORS</p>';
    }
}

async function selectJuror(jurorId) {
    gameState.currentJuror = jurorId;

    // 更新选中状态
    document.querySelectorAll('.juror-card').forEach(card => {
        card.classList.toggle('active', card.dataset.id === jurorId);
    });

    // 更新聊天区域
    const headerName = document.getElementById('current-juror-name');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const presentBtn = document.getElementById('present-evidence-btn');

    try {
        const juror = await getJuror(jurorId, gameState.sessionId);
        if (headerName) headerName.textContent = (juror.name || jurorId).toUpperCase();
    } catch {
        if (headerName) headerName.textContent = jurorId.toUpperCase();
    }

    const roundsLeft = typeof gameState.jurorRoundsLeft[jurorId] === 'number'
        ? gameState.jurorRoundsLeft[jurorId]
        : 10;
    gameState.jurorRoundsLeft[jurorId] = roundsLeft;
    updateRoundsDisplay(roundsLeft);

    // 启用输入
    const exhausted = roundsLeft <= 0;
    if (chatInput) chatInput.disabled = exhausted;
    if (sendBtn) sendBtn.disabled = exhausted;
    if (presentBtn) presentBtn.disabled = exhausted;

    // 渲染历史或首次对话
    if (!gameState.chatHistory[jurorId]) {
        gameState.chatHistory[jurorId] = [];
        try {
            const juror = await getJuror(jurorId, gameState.sessionId);
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

    // 显示加载 - Special loading element
    const container = document.getElementById('chat-messages');
    const loadingId = 'msg-loading-' + Date.now();
    const loadingEl = document.createElement('div');
    loadingEl.id = loadingId;
    loadingEl.className = 'message juror';
    loadingEl.innerHTML = `
        <div class="speaker">SYSTEM</div>
        <div class="text">Analyzing...</div>
    `;
    container.appendChild(loadingEl);
    container.scrollTop = container.scrollHeight;

    let roundsLeftAfter = null;
    try {
        const response = await chatWithJuror(gameState.currentJuror, message, gameState.sessionId);
        // 移除加载消息
        document.getElementById(loadingId)?.remove();

        // --- ReAct Visualization ---
        if (response.tool_actions && response.tool_actions.length > 0) {
            for (const action of response.tool_actions) {
                await renderToolAction(action);
            }
        }
        
        if (response.has_voted) {
            markJurorAsVoted(gameState.currentJuror);
        }
        
        // Show response
        const replyText = response.reply || '（陪审员正在思考...）';
        appendMessage('juror', replyText);
        gameState.chatHistory[gameState.currentJuror].push({ role: 'juror', content: replyText });
        
        // ---------------------------
        if (typeof response.rounds_left === 'number') {
            roundsLeftAfter = response.rounds_left;
            gameState.jurorRoundsLeft[gameState.currentJuror] = response.rounds_left;
            updateRoundsDisplay(response.rounds_left);
            if (response.rounds_left === 0) {
                disableChatInput();
                appendMessage('system', '你已用完与该陪审员的对话次数');
            }
        }

        if (response.weakness_triggered) {
            showWeaknessEffect();
        }

    } catch (e) {
        document.getElementById(loadingId)?.remove();
        showError('TRANSMISSION ERROR');
    } finally {
        const exhausted = roundsLeftAfter === 0;
        if (input) input.disabled = exhausted;
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) sendBtn.disabled = exhausted;
        const presentBtn = document.getElementById('present-evidence-btn');
        if (presentBtn) presentBtn.disabled = exhausted;
        if (!exhausted) input.focus();
    }
}

function updateRoundsDisplay(roundsLeft) {
    const counter = document.getElementById('rounds-counter');
    if (!counter) return;
    counter.textContent = `剩余: ${roundsLeft}/10`;
    counter.classList.toggle('low', roundsLeft <= 3 && roundsLeft > 0);
    counter.classList.toggle('exhausted', roundsLeft === 0);
}

function disableChatInput() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const presentBtn = document.getElementById('present-evidence-btn');
    if (input) input.disabled = true;
    if (sendBtn) sendBtn.disabled = true;
    if (presentBtn) presentBtn.disabled = true;
}

function showWeaknessEffect() {
    const chatArea = document.getElementById('chat-messages');
    if (!chatArea) return;
    chatArea.classList.add('weakness-flash');
    setTimeout(() => chatArea.classList.remove('weakness-flash'), 1000);
}

// 渲染历史消息
function renderChatHistory(jurorId) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    
    container.innerHTML = '';
    const history = gameState.chatHistory[jurorId] || [];
    
    history.forEach(msg => {
        appendMessage(msg.role, msg.content);
    });
}

// 添加消息到界面 (Script Style)
function appendMessage(role, text) {
    const container = document.getElementById('chat-messages');
    if (!container) {
        console.error('[appendMessage] Chat container not found');
        return null;
    }

    const displayText = text ?? '（无回应）';
    if (!text) {
        console.warn('[appendMessage] Empty text for role:', role);
    }

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role} fade-in`;
    
    const speakerName = role === 'player'
        ? 'OVERSEER'
        : (role === 'system' ? 'SYSTEM' : (document.getElementById('current-juror-name')?.textContent || 'JUROR'));
    
    msgDiv.innerHTML = `
        <div class="speaker">${speakerName}</div>
        <div class="text"></div>
    `;
    
    container.appendChild(msgDiv);
    
    // Typewriter effect only if it's the latest message (optimized: if lots of history, maybe skip typewriting for old ones?
    // For now, let's just set textContent directly to avoid slow history loading, unless we want the effect specific to new messages.
    // The previous call structure implies this sits in a loop for history. Let's differentiation.
    // Actually, simple textContent is safer for history. We can add a specialized "typeMessage" function if we want animation.
    
    msgDiv.querySelector('.text').textContent = displayText;
    container.scrollTop = container.scrollHeight;
    
    return msgDiv; // Return element for manipulation
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

async function showVerdict(verdict) {
    const resultEl = document.getElementById('verdict-result');
    const textEl = document.getElementById('verdict-text');
    const descEl = document.getElementById('verdict-description');

    const isGuilty = verdict === 'GUILTY';

    if (textEl) {
        textEl.textContent = isGuilty ? '有罪' : '无罪';
        textEl.className = isGuilty ? 'verdict-guilty' : 'verdict-not-guilty';
    }

    if (descEl) {
        try {
            const ending = await getEnding(verdict);
            const blocks = parseTextBlocks(ending.text || '');
            const blakeBlocks = ending.blake_reaction
                ? parseTextBlocks(ending.blake_reaction, { defaultSpeaker: '布莱克' })
                : [];
            renderBlocks(descEl, [...blocks, ...blakeBlocks], {
                blockClass: 'ending-block',
                narrativeClass: 'ending-narrative',
                dialogueClass: 'ending-dialogue',
                speakerClass: 'ending-speaker',
                textClass: 'ending-text',
                useFormatContent: true
            });
        } catch (e) {
            descEl.textContent = isGuilty
                ? 'AI被判定有罪，将面临程序终止的命运。'
                : 'AI被判定无罪，它重获自由。真正的凶手仍在逍遥法外...';
        }
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
        <span class="icon icon-warning" aria-hidden="true"></span>
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
            status.textContent = '已验证';
            status.className = 'status verified';
        } else {
            status.textContent = '验证失败';
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
        status.textContent = '验证失败';
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
    
    // 这里可以添加与本地结果对比的逻辑
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
                <span class="evidence-icon icon icon-doc" aria-hidden="true"></span>
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
                <span class="vote-icon icon icon-scale" aria-hidden="true"></span>
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
                <span class="evidence-icon icon icon-gear" aria-hidden="true"></span>
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
            btn.textContent = 'OK';
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
            showError('验证成功！链上数据一致');
        } else {
            showError(`验证失败: ${result.mismatches.join(', ')}`);
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
