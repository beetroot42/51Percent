# AI Trial - System Architecture

> Blockchain Jury Persuasion Game Based on SpoonOS

## I. Game Background

In a future world, court juries use blockchain to randomly select citizen nodes for voting, ensuring fairness and transparency.

**Case**: A prompt injection-induced embodied AI homicide case
- Core conflict: Is the AI the perpetrator or the victim?
- Player identity: Detective (neutral investigator)
- Objective: Form judgment through investigation, persuade jurors to support your conclusion

## II. Game Flow

```
┌─────────────────────────────────────────────────────────────┐
│                Investigation Phase (Traditional AVG)         │
│                                                             │
│   ┌──────────┐   ┌──────────┐   ┌──────────────────────┐   │
│   │  Dossier │   │ Evidence │   │   Witness Dialogue   │   │
│   │  (Read)  │   │  (View)  │   │  Choice + Present    │   │
│   └──────────┘   └──────────┘   └──────────────────────┘   │
│                                                             │
│              [I'm ready, enter persuasion phase]            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Persuasion Phase (Agent Dialogue)             │
│                                                             │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐              │
│   │ Juror A  │   │ Juror B  │   │ Juror C  │   ...        │
│   │  Agent   │   │  Agent   │   │  Agent   │              │
│   │(Free Input)│  │(Free Input)│  │(Free Input)│            │
│   └──────────┘   └──────────┘   └──────────┘              │
│                                                             │
│               [End persuasion, enter trial]                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Trial (On-chain Voting)                  │
│                                                             │
│     Jurors vote based on influenced stance → 51% majority   │
│                       → Ending                              │
│                                                             │
│      Guilty: Embodied AI judged as perpetrator             │
│      Not Guilty: Embodied AI judged as victim              │
└─────────────────────────────────────────────────────────────┘
```

## III. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Frontend                           │
│                  (HTML + CSS + JS)                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Investigation Phase UI                    │   │
│  │  - Dossier reading interface                       │   │
│  │  - Evidence viewing interface                      │   │
│  │  - Witness dialogue (choice + present evidence)    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Persuasion Phase UI                       │   │
│  │  - Juror list                                       │   │
│  │  - Free input dialogue box                         │   │
│  │  - Conversation history display                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Trial Phase UI                       │   │
│  │  - Voting animation/result display                 │   │
│  │  - Ending screen                                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Game API                               │
│                     (FastAPI)                               │
│                                                             │
│  POST /chat/{juror_id}     Chat with juror                 │
│  POST /vote                Trigger voting                   │
│  GET  /state               Get game state                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SpoonOS Core                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Juror Agents (ReAct)                   │   │
│  │                                                      │   │
│  │  Each juror = 1 ReAct Agent                         │   │
│  │  - Load character card (personality, stance, topics)│   │
│  │  - Record conversation history                      │   │
│  │  - Evaluate player arguments → update internal stance│  │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Tools                             │   │
│  │                                                      │   │
│  │  cast_vote(juror, stance)  Execute on-chain voting  │   │
│  │  get_vote_state()          Read voting state        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Blockchain (Foundry)                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              JuryVoting Contract                     │   │
│  │                                                      │   │
│  │  mapping(address => bool) public hasVoted;           │   │
│  │  mapping(address => bool) public votedGuilty;        │   │
│  │  uint public guiltyVotes;                            │   │
│  │  uint public notGuiltyVotes;                         │   │
│  │                                                      │   │
│  │  function vote(bool guilty) external;                │   │
│  │  function getVerdict() external view returns (bool); │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## IV. Core Modules

### 4.1 Frontend (Static Content + API Calls)

| Feature | Implementation |
|------|------------|
| Dossier/Evidence | Render static JSON/Markdown |
| Witness dialogue | Dialogue tree + present evidence triggers |
| Juror dialogue | Fetch call to backend Agent API |
| Voting results | Call contract to read |

### 4.2 Content Layer

```
/content
├── case/
│   ├── dossier.json          # Dossier
│   └── evidence/
│       ├── cctv.json         # Evidence 1
│       ├── chat_log.json     # Evidence 2
│       └── ...
├── witnesses/                 # Witness dialogue trees
│   ├── victim_family.json
│   ├── ai_developer.json
│   └── ...
└── jurors/                    # Juror character cards
    ├── juror_a.json
    ├── juror_b.json
    └── ...
```

### 4.3 Witness Dialogue Tree Structure

```json
{
  "id": "ai_developer",
  "name": "AI Developer",
  "portrait": "developer.png",
  "dialogues": [
    {
      "id": "start",
      "text": "What do you want to ask?",
      "options": [
        { "text": "Tell me what happened that day", "next": "that_day" },
        { "text": "Your AI safety measures", "next": "safety" }
      ]
    },
    {
      "id": "that_day",
      "text": "When I got the emergency call that day, I was completely stunned...",
      "options": [...]
    }
  ],
  "evidence_reactions": {
    "chat_log": {
      "text": "This conversation... someone was testing prompt injection!",
      "unlock": "injection_clue"
    },
    "cctv": {
      "text": "Look here, the AI's behavior is clearly abnormal",
      "unlock": null
    }
  }
}
```

### 4.4 Juror Character Card Structure

```json
{
  "id": "juror_a",
  "name": "Wang",
  "background": "Retired engineer with some technical understanding",
  "personality": "Rational, cautious, likes data-driven reasoning",
  "initial_stance": "neutral",
  "care_about": ["Technical details", "Attribution of responsibility"],
  "weakness": "Not responsive to emotional appeals",
  "persuadability": 50,
  "first_message": "Hmm, tell me your thoughts, I'm listening."
}
```

## V. API Design

### 5.1 Juror Dialogue

```
POST /chat/{juror_id}
Body: { "message": "Player input" }
Response: {
  "reply": "Juror reply",
  "stance": "leaning_guilty",  // neutral/leaning_guilty/leaning_not_guilty
  "conversation_id": "xxx"
}
```

### 5.2 Trigger Voting

```
POST /vote
Response: {
  "guilty_votes": 3,
  "not_guilty_votes": 2,
  "verdict": "guilty",
  "tx_hash": "0x..."
}
```

### 5.3 Game State

```
GET /state
Response: {
  "phase": "investigation",  // investigation/persuasion/verdict
  "jurors": [
    { "id": "juror_a", "name": "Wang", "stance": "neutral" },
    ...
  ],
  "evidence_found": ["cctv", "chat_log"],
  "unlocked_clues": ["injection_clue"]
}
```

## VI. Smart Contract

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract JuryVoting {
    mapping(address => bool) public hasVoted;
    mapping(address => bool) public votedGuilty;

    uint public guiltyVotes;
    uint public notGuiltyVotes;
    uint public totalJurors;

    bool public votingClosed;

    constructor(uint _totalJurors) {
        totalJurors = _totalJurors;
    }

    function vote(bool guilty) external {
        require(!hasVoted[msg.sender], "Already voted");
        require(!votingClosed, "Voting closed");

        hasVoted[msg.sender] = true;
        votedGuilty[msg.sender] = guilty;

        if (guilty) {
            guiltyVotes++;
        } else {
            notGuiltyVotes++;
        }

        if (guiltyVotes + notGuiltyVotes >= totalJurors) {
            votingClosed = true;
        }
    }

    function getVerdict() external view returns (string memory) {
        require(votingClosed, "Voting not closed");
        if (guiltyVotes > notGuiltyVotes) {
            return "GUILTY";
        }
        return "NOT_GUILTY";
    }
}
```

## VII. Directory Structure

```
ai-trial-game/
├── contracts/                 # Foundry project
│   ├── src/
│   │   └── JuryVoting.sol
│   ├── test/
│   └── foundry.toml
├── backend/                   # Python backend
│   ├── main.py               # FastAPI entry
│   ├── agents/
│   │   └── juror_agent.py    # Juror Agent
│   ├── tools/
│   │   └── voting_tool.py    # On-chain voting Tool
│   └── requirements.txt
├── frontend/                  # Web frontend
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/               # Pixel art and materials
├── content/                   # Game content
│   ├── case/
│   ├── witnesses/
│   └── jurors/
└── README.md
```

## VIII. MVP Scope

### Included

- 1 case
- 3 pieces of evidence
- 2 witnesses (choice dialogue + present evidence)
- 3 jurors (Agent dialogue)
- Simple voting contract
- Basic Web UI

### Not Included (Future)

- Multiple cases
- Complex evidence chains
- Juror mutual influence
- Save/load
- Sound effects/animations
