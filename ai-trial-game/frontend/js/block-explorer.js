const RPC_URL = 'http://127.0.0.1:8545';
let provider;

/**
 * 初始化
 */
async function init() {
    try {
        // 使用 JsonRpcProvider 连接本地 Anvil
        provider = new ethers.providers.JsonRpcProvider(RPC_URL);

        // 从 URL 参数获取区块号和交易哈希
        const params = new URLSearchParams(window.location.search);
        const blockNumber = params.get('block');
        const txHash = params.get('tx');

        if (blockNumber) {
            await loadBlock(parseInt(blockNumber));
        }

        if (txHash) {
            await loadTransaction(txHash);
        }
    } catch (error) {
        console.error('Initialization failed:', error);
        alert(`无法连接到本地链: ${error.message}\n请确保 Anvil 已启动并在 ${RPC_URL} 运行。`);
    }
}

/**
 * 加载区块信息
 */
async function loadBlock(blockNumber) {
    try {
        const block = await provider.getBlock(blockNumber);
        if (!block) {
            throw new Error('区块不存在');
        }

        // 填充区块信息
        document.getElementById('block-number').textContent = block.number;
        document.getElementById('block-hash').textContent = block.hash;
        document.getElementById('parent-hash').textContent = block.parentHash;

        const date = new Date(block.timestamp * 1000);
        document.getElementById('timestamp').textContent = date.toLocaleString('zh-CN');

        document.getElementById('tx-count').textContent = block.transactions.length;
        document.getElementById('gas-used').textContent = block.gasUsed.toString();
        document.getElementById('gas-limit').textContent = block.gasLimit.toString();

        // 加载交易列表
        await loadTransactionList(block.transactions);
    } catch (error) {
        console.error('Failed to load block:', error);
        alert(`加载区块失败: ${error.message}`);
    }
}

/**
 * 加载交易列表
 */
async function loadTransactionList(txHashes) {
    const container = document.getElementById('tx-list');
    if (!container) return;
    container.innerHTML = '';

    if (!txHashes || txHashes.length === 0) {
        container.innerHTML = '<p class="empty-message">此区块无交易</p>';
        return;
    }

    for (const txHash of txHashes) {
        const txCard = document.createElement('div');
        txCard.className = 'tx-card';
        txCard.innerHTML = `
            <div class="tx-hash-display">${shortenHash(txHash)}</div>
            <button class="btn-view-tx" onclick="loadTransaction('${txHash}')">
                查看详情
            </button>
        `;
        container.appendChild(txCard);
    }
}

/**
 * 加载交易详情
 */
async function loadTransaction(txHash) {
    try {
        const tx = await provider.getTransaction(txHash);
        const receipt = await provider.getTransactionReceipt(txHash);

        if (!tx || !receipt) {
            throw new Error('交易不存在');
        }

        const section = document.getElementById('tx-details-section');
        const content = document.getElementById('tx-details-content');

        content.innerHTML = `
            <div class="details-grid">
                <div class="detail-item">
                    <span class="label">交易哈希</span>
                    <span class="value monospace">${tx.hash}</span>
                </div>
                <div class="detail-item">
                    <span class="label">状态</span>
                    <span class="value ${receipt.status === 1 ? 'success' : 'failed'}">
                        ${receipt.status === 1 ? '✓ 成功' : '✗ 失败'}
                    </span>
                </div>
                <div class="detail-item">
                    <span class="label">区块号</span>
                    <span class="value">#${tx.blockNumber}</span>
                </div>
                <div class="detail-item">
                    <span class="label">发送者 (From)</span>
                    <span class="value monospace">${tx.from}</span>
                </div>
                <div class="detail-item">
                    <span class="label">接收者 (To)</span>
                    <span class="value monospace">${tx.to || '合约创建'}</span>
                </div>
                <div class="detail-item">
                    <span class="label">Gas 使用</span>
                    <span class="value">${receipt.gasUsed.toString()}</span>
                </div>
                <div class="detail-item">
                    <span class="label">Gas 价格</span>
                    <span class="value">${ethers.utils.formatUnits(tx.gasPrice, 'gwei')} Gwei</span>
                </div>
                <div class="detail-item">
                    <span class="label">Nonce</span>
                    <span class="value">${tx.nonce}</span>
                </div>
            </div>

            ${receipt.logs && receipt.logs.length > 0 ? `
                <div class="event-logs">
                    <h4>事件日志 (Logs)</h4>
                    ${receipt.logs.map((log, i) => `
                        <div class="log-item">
                            <div class="log-header">事件 #${i}</div>
                            <div class="log-body">
                                <div class="log-field">
                                    <span class="label">合约</span>
                                    <span class="value monospace">${log.address}</span>
                                </div>
                                <div class="log-field">
                                    <span class="label">主题 (Topics)</span>
                                    <span class="value monospace">${log.topics[0]}</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        `;

        section.classList.remove('hidden');
        section.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Failed to load transaction:', error);
        alert(`加载交易失败: ${error.message}`);
    }
}

/**
 * 缩短哈希显示
 */
function shortenHash(hash) {
    if (!hash) return '';
    return `${hash.slice(0, 10)}...${hash.slice(-8)}`;
}

// 页面加载时初始化
window.addEventListener('DOMContentLoaded', init);
