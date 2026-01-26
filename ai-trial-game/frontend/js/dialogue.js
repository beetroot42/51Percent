/**
 * 对话树引擎
 *
 * 处理当事人的选项式对话 + 出示证物功能
 */

/**
 * 对话状态
 */
const dialogueState = {
    currentWitness: null,      // 当前当事人ID
    currentNode: null,         // 当前对话节点ID
    dialogueTree: null,        // 完整对话树数据
    unlockedClues: [],         // 已解锁的线索
    shownEvidence: [],         // 已出示的证物
};

/**
 * 加载当事人对话树
 * @param {string} witnessId
 *
 * TODO:
 * - 调用API获取对话树
 * - 存入dialogueState.dialogueTree
 * - 设置currentNode为"start"
 */
async function loadWitness(witnessId) {

}

/**
 * 获取当前对话节点
 * @returns {object} {text: string, options: array}
 *
 * TODO:
 * - 从dialogueTree中查找currentNode
 * - 返回节点数据
 */
function getCurrentNode() {

}

/**
 * 选择对话选项
 * @param {string} optionId - 选项ID或next节点ID
 *
 * TODO:
 * - 更新currentNode
 * - 触发UI更新
 */
function selectOption(optionId) {

}

/**
 * 出示证物
 * @param {string} evidenceId
 * @returns {object|null} 反应文本，如果没有特殊反应返回null
 *
 * TODO:
 * - 检查dialogueTree.evidence_reactions
 * - 如果有对应反应，返回反应数据
 * - 记录已出示证物
 * - 如果有unlock字段，添加到unlockedClues
 */
function showEvidence(evidenceId) {

}

/**
 * 检查是否已出示过某证物
 * @param {string} evidenceId
 * @returns {boolean}
 */
function hasShownEvidence(evidenceId) {

}

/**
 * 获取已解锁的线索
 * @returns {array}
 */
function getUnlockedClues() {

}

/**
 * 重置对话状态
 *
 * TODO:
 * - 清空所有状态
 */
function resetDialogue() {

}

/**
 * 检查对话是否结束
 * @returns {boolean}
 *
 * TODO:
 * - 检查当前节点是否有options
 * - 或者是否标记为end
 */
function isDialogueEnded() {

}
