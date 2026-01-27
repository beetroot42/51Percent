# AI Trial - Agent Design

This document describes the juror agent design, stance tracking, and topic analysis used in the AI Trial game.

## 1. Stance Tracking

- Each juror has a hidden `stance_value` range: -100 to +100
  - -100: strongly guilty
  - 0: neutral
  - +100: strongly not guilty
- Final vote: `stance_value > 0` => NOT_GUILTY, otherwise GUILTY

## 2. Topic Weights

Each juror has topic weights that shift stance when arguments match.

Example (content file `content/jurors/*.json`):

```json
{
  "id": "juror_wang",
  "name": "Wang",
  "initial_stance": 0,
  "topic_weights": {
    "technical_responsibility": 15,
    "external_attack": 20,
    "ai_autonomy": -10,
    "emotional_appeal": -5,
    "legal_precedent": 10,
    "victim_position": 5,
    "safety_measures": 12,
    "corporate_responsibility": 8
  }
}
```

Notes:
- The runtime accepts both English topic keys and Chinese aliases.
- Topic weights can be positive or negative.

## 3. Topic Recognition

Agents embed a hidden analysis block in their reply. The server parses it to compute stance shifts.

Example:

```
<!-- ANALYSIS: {"topics": ["technical_responsibility", "external_attack"], "impact": "positive"} -->
```

- `impact` can be `positive`, `negative`, or `neutral`.

## 4. Character Card Structure

```json
{
  "id": "juror_wang",
  "name": "Wang",
  "age": 62,
  "occupation": "Retired Electrical Engineer",
  "portrait": "wang.png",
  "background": "...",
  "personality": ["Rational", "Practical"],
  "speaking_style": "Direct and technical",
  "initial_stance": 0,
  "topic_weights": { "technical_responsibility": 15 },
  "first_message": "..."
}
```

## 5. Prompt Template (Conceptual)

- Background, personality, speaking style
- Current case summary
- Current stance description
- Topic preferences
- Hidden analysis tag requirement

## 6. Stance Labels (Player-Facing)

The player sees only vague labels:
- "Seems to disagree with you"
- "Seems to have some doubts"
- "Neutral attitude"
- "Seems to be considering your viewpoint"
- "Seems to agree with you"

## 7. Voting Settlement

```
verdict = "NOT_GUILTY" if not_guilty_votes >= guilty_votes else "GUILTY"
```

## 8. Future Extensions

- Juror-to-juror influence
- Multi-round juror debates
- Evidence-triggered stance shifts
- Hidden endings based on persuasion path
