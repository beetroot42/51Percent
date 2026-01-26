/**
 * 游戏主逻辑
 *
 * 控制游戏流程、UI渲染、阶段切换
 */

/**
 * 游戏阶段
 */
const PHASES = {
    INVESTIGATION: 'investigation',
    PERSUASION: 'persuasion',
    VERDICT: 'verdict'
};

/**
 * 游戏状态
 */
const gameState = {
    phase: PHASES.INVESTIGATION,
    currentJuror: null,         // 当前对话的陪审员
    chatHistory: {},            // {juror_id: [{role, content}, ...]}
};

// ============ 初始化 ============

/**
 * 游戏初始化
 *
 * TODO:
 * - 加载游戏状态
 * - 初始化UI
 * - 绑定事件
 */
async function initGame() {

}

/**
 * 绑定UI事件
 *
 * TODO:
 * - 绑定各按钮点击事件
 * - 绑定输入框回车事件
 */
function bindEvents() {

}

// ============ 阶段控制 ============

/**
 * 切换到调查阶段
 *
 * TODO:
 * - 更新gameState.phase
 * - 显示调查UI，隐藏其他
 * - 加载卷宗/证据/当事人列表
 */
async function enterInvestigation() {

}

/**
 * 切换到说服阶段
 *
 * TODO:
 * - 更新gameState.phase
 * - 显示说服UI，隐藏其他
 * - 加载陪审员列表
 */
async function enterPersuasion() {

}

/**
 * 切换到审判阶段
 *
 * TODO:
 * - 更新gameState.phase
 * - 触发投票
 * - 显示投票动画
 * - 显示最终判决
 */
async function enterVerdict() {

}

// ============ 调查阶段UI ============

/**
 * 显示卷宗
 *
 * TODO:
 * - 获取卷宗内容
 * - 渲染到UI
 */
async function showDossier() {

}

/**
 * 显示证据列表
 *
 * TODO:
 * - 获取证据列表
 * - 渲染证据卡片
 */
async function showEvidenceList() {

}

/**
 * 显示证据详情
 * @param {string} evidenceId
 *
 * TODO:
 * - 获取证据详情
 * - 显示弹窗或切换视图
 */
async function showEvidenceDetail(evidenceId) {

}

/**
 * 显示当事人列表
 *
 * TODO:
 * - 获取当事人列表
 * - 渲染当事人卡片
 */
async function showWitnessList() {

}

/**
 * 开始与当事人对话
 * @param {string} witnessId
 *
 * TODO:
 * - 加载对话树
 * - 显示对话UI
 * - 渲染当前节点
 */
async function startWitnessDialogue(witnessId) {

}

/**
 * 渲染当事人对话节点
 *
 * TODO:
 * - 获取当前节点
 * - 显示NPC文本
 * - 显示选项按钮
 * - 显示出示证物按钮
 */
function renderDialogueNode() {

}

/**
 * 处理对话选项点击
 * @param {string} optionId
 *
 * TODO:
 * - 调用selectOption()
 * - 重新渲染
 */
function handleDialogueOption(optionId) {

}

/**
 * 显示证物选择弹窗
 *
 * TODO:
 * - 显示可出示的证物列表
 * - 点击后调用handleShowEvidence
 */
function showEvidenceSelector() {

}

/**
 * 处理出示证物
 * @param {string} evidenceId
 *
 * TODO:
 * - 调用showEvidence()
 * - 如果有反应，显示反应文本
 * - 关闭选择弹窗
 */
function handleShowEvidence(evidenceId) {

}

// ============ 说服阶段UI ============

/**
 * 显示陪审员列表
 *
 * TODO:
 * - 获取陪审员列表
 * - 渲染陪审员卡片
 */
async function showJurorList() {

}

/**
 * 选择陪审员进行对话
 * @param {string} jurorId
 *
 * TODO:
 * - 设置currentJuror
 * - 显示对话UI
 * - 加载历史对话（如果有）
 * - 显示开场白（如果是首次）
 */
async function selectJuror(jurorId) {

}

/**
 * 发送消息给陪审员
 * @param {string} message
 *
 * TODO:
 * - 显示玩家消息
 * - 显示加载状态
 * - 调用API
 * - 显示陪审员回复
 * - 保存到chatHistory
 */
async function sendMessageToJuror(message) {

}

/**
 * 渲染对话历史
 * @param {string} jurorId
 *
 * TODO:
 * - 从chatHistory获取
 * - 渲染消息列表
 */
function renderChatHistory(jurorId) {

}

/**
 * 添加消息到UI
 * @param {string} role - 'player' | 'juror'
 * @param {string} content
 *
 * TODO:
 * - 创建消息元素
 * - 添加到对话容器
 * - 滚动到底部
 */
function appendMessage(role, content) {

}

// ============ 审判阶段UI ============

/**
 * 显示投票动画
 * @param {object} voteResult
 *
 * TODO:
 * - 依次显示每个陪审员的投票
 * - 动画效果
 */
async function showVotingAnimation(voteResult) {

}

/**
 * 显示最终判决
 * @param {string} verdict - 'GUILTY' | 'NOT_GUILTY'
 *
 * TODO:
 * - 显示大字判决结果
 * - 显示结局文本
 */
function showVerdict(verdict) {

}

// ============ 工具函数 ============

/**
 * 显示指定区域，隐藏其他
 * @param {string} sectionId
 *
 * TODO:
 * - 遍历所有section
 * - 设置display
 */
function showSection(sectionId) {

}

/**
 * 显示加载状态
 * @param {boolean} loading
 */
function setLoading(loading) {

}

/**
 * 显示错误提示
 * @param {string} message
 */
function showError(message) {

}

// ============ 启动 ============

document.addEventListener('DOMContentLoaded', initGame);
