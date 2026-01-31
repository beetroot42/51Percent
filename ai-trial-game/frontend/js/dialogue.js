/**
 * 对话树引擎
 */

const dialogueState = {
    currentWitness: null,
    currentNode: null,
    dialogueTree: null,
    unlockedClues: [],
    shownEvidence: [],
    history: [],
};

async function loadWitness(witnessId) {
    const data = await getWitness(witnessId);
    dialogueState.currentWitness = witnessId;
    dialogueState.dialogueTree = data;
    dialogueState.currentNode = 'start';
    dialogueState.shownEvidence = [];
}

function getCurrentNode() {
    if (!dialogueState.dialogueTree || !dialogueState.currentNode) return null;
    const dialogues = dialogueState.dialogueTree.dialogues || [];
    return dialogues.find(d => d.id === dialogueState.currentNode) || null;
}

function selectOption(nextNodeId) {
    const dialogues = dialogueState.dialogueTree?.dialogues || [];
    const targetNode = dialogues.find(d => d.id === nextNodeId);
    if (targetNode) {
        if (dialogueState.currentNode) {
            dialogueState.history.push(dialogueState.currentNode);
        }
        dialogueState.currentNode = nextNodeId;
        if (targetNode.unlock_clue && !dialogueState.unlockedClues.includes(targetNode.unlock_clue)) {
            dialogueState.unlockedClues.push(targetNode.unlock_clue);
        }
    }
}

function showEvidence(evidenceId) {
    const reactions = dialogueState.dialogueTree?.evidence_reactions || {};
    const reaction = reactions[evidenceId];

    if (!dialogueState.shownEvidence.includes(evidenceId)) {
        dialogueState.shownEvidence.push(evidenceId);
    }

    if (reaction) {
        if (reaction.unlock_clue && !dialogueState.unlockedClues.includes(reaction.unlock_clue)) {
            dialogueState.unlockedClues.push(reaction.unlock_clue);
        }
        if (reaction.unlock_dialogue) {
            dialogueState.currentNode = reaction.unlock_dialogue;
        }
        return reaction;
    }
    return null;
}

function hasShownEvidence(evidenceId) {
    return dialogueState.shownEvidence.includes(evidenceId);
}

function getUnlockedClues() {
    return [...dialogueState.unlockedClues];
}

function resetDialogue() {
    dialogueState.currentWitness = null;
    dialogueState.currentNode = null;
    dialogueState.dialogueTree = null;
    dialogueState.unlockedClues = [];
    dialogueState.shownEvidence = [];
    dialogueState.history = [];
}

function isDialogueEnded() {
    const node = getCurrentNode();
    if (!node) return true;
    return !node.options || node.options.length === 0;
}
