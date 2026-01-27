# Implementation Roadmap: Local Chain Migration

**Specification**: `local-chain-migration-spec.md`
**Ready for Implementation**: ✅ Yes
**Zero-Decision**: ✅ All ambiguities resolved

---

## 📊 Implementation Plan

### Phase 1: Backend Core (Codex)
**Priority**: Critical
**Files**: `start.py`, `backend/.env.example`

**Tasks**:
1. Add `MODE` configuration reading
2. Implement Anvil account auto-injection
3. Refactor supervisor process management
4. Add graceful shutdown handlers

**Estimated Complexity**: Medium
**Dependencies**: None

---

### Phase 2: Frontend Updates (Gemini)
**Priority**: High
**Files**: `frontend/js/game.js`, `frontend/index.html`

**Tasks**:
1. Remove Etherscan URL generation
2. Update network naming (Sepolia → 本地链)
3. Reduce animation duration (9s → 2s)
4. Add infrastructure error handling

**Estimated Complexity**: Low
**Dependencies**: None (can run parallel with Phase 1)

---

### Phase 3: Testing & Validation (Codex)
**Priority**: High
**Files**: `backend/tests/test_local_chain.py` (new)

**Tasks**:
1. Implement PBT property tests
2. Add integration tests for startup flow
3. Verify process cleanup
4. Test transaction speed

**Estimated Complexity**: Medium
**Dependencies**: Phase 1 complete

---

### Phase 4: Documentation (Gemini)
**Priority**: Medium
**Files**: `README.md`, `SETUP_GUIDE.md`

**Tasks**:
1. Update quick start guide
2. Document local vs Sepolia modes
3. Add troubleshooting section
4. Update environment variable docs

**Estimated Complexity**: Low
**Dependencies**: Phases 1-3 complete

---

## 🎯 Key Implementation Points

### Critical Path Items
1. **Account Synchronization** (Phase 1)
   - start.py must inject Anvil default accounts into environment
   - This fixes the "Insufficient Funds" bug identified by Gemini

2. **Process Management** (Phase 1)
   - Replace `os.execvp` with supervisor pattern
   - Ensures clean shutdown and no orphaned processes

3. **Error Handling** (Phase 2)
   - Distinguish Anvil connection errors from logic errors
   - Improves debugging experience

### Quick Wins
- Frontend text updates (5 min)
- Animation duration change (2 min)
- .env.example template (10 min)

### Complex Changes
- Supervisor process management in start.py (2-3 hours)
- PBT test suite (1-2 hours)

---

## 🚀 Execution Strategy

### Option 1: Sequential (Safer)
```
Day 1: Phase 1 (Backend Core)
Day 2: Phase 2 (Frontend) + Phase 3 (Testing)
Day 3: Phase 4 (Documentation) + Final QA
```

### Option 2: Parallel (Faster)
```
Day 1:
  - Codex: Phase 1 (Backend Core)
  - Gemini: Phase 2 (Frontend) in parallel

Day 2:
  - Codex: Phase 3 (Testing)
  - Gemini: Phase 4 (Documentation)

Day 3: Integration testing + QA
```

**Recommendation**: Option 2 (Parallel) - Frontend changes are independent of backend.

---

## ✅ Pre-Implementation Checklist

Before starting implementation, verify:

- [x] All architectural decisions made
- [x] All ambiguities resolved
- [x] Specification document complete
- [x] PBT properties defined
- [x] Error handling rules explicit
- [x] Configuration constraints clear
- [ ] User approval for specification
- [ ] Implementation tasks created
- [ ] Agents assigned to tasks

---

## 📋 Next Steps

1. **User Review**: User reviews `local-chain-migration-spec.md`
2. **Approval**: User confirms specification is correct
3. **Task Assignment**:
   - Codex → Phase 1 + Phase 3
   - Gemini → Phase 2 + Phase 4
4. **Parallel Execution**: Launch both agents simultaneously
5. **Integration**: Merge results and test E2E
6. **Validation**: Run full game flow

---

## 🔗 Related Documents

- Specification: `.claude/tasks/local-chain-migration-spec.md`
- Architecture Analysis: `.claude/tasks/architecture-analysis-local-chain.md`
- Codex Analysis: See session 019bff30-b01b-7853-966a-24bda654bf27
- Gemini Analysis: See session 195ef604-ccd9-4e09-809e-c6af82c5c726

---

**Status**: ⏸️ Awaiting User Approval
**Next Action**: User confirms specification → Begin implementation
