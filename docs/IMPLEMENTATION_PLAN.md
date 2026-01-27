# AI Trial - Implementation Plan

This plan reflects the current SpoonOS ReAct-based agent architecture.

## Timeline (Reference)

- Day 1: Contracts + backend skeleton
- Day 2: Juror agents + full API
- Day 3: Frontend + integration
- Day 4-5: Content creation and polish

## Day 1: Contracts + Backend Skeleton

- Implement and test `JuryVoting.sol`
- Create `VotingTool` for chain interaction
- Add basic FastAPI endpoints

## Day 2: Juror Agents + API

- Implement SpoonOS juror agents (`SpoonJurorAgent`)
- Implement `AgentManager`
- Complete API endpoints: `/chat`, `/jurors`, `/phase`, `/vote`

## Day 3: Frontend + Integration

- Build investigation, persuasion, and verdict screens
- Wire frontend to backend API
- End-to-end testing

## Content Scope (Minimum)

- Dossier: 1
- Evidence: 3
- Witnesses: 2
- Jurors: 3

## Risks

- LLM rate limits: use smaller model or caching if needed
- Port conflicts: adjust `SERVER_PORT`
- Configuration issues: verify `.env` values
