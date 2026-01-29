# Bugfix: Verification Panel Display Issue (Gemini)

**Type**: Bug Fix
**Assigned to**: Gemini
**Priority**: Critical
**Diagnosed by**: Gemini + Claude

---

## Problem Description

The blockchain verification panel (`#verification-panel`) is visible immediately upon page load, appearing alongside the investigation/chat panels. It should only appear after voting is completed.

### Symptoms
- Verification panel shows at page load
- Panel displays loading spinner endlessly (not actually fetching data)
- Panel clutters the layout with other game phases

---

## Root Cause Analysis

**Diagnosis**: CSS is missing a global `.hidden` utility class.

**Evidence**:
- In `frontend/index.html` line 160, `#verification-panel` has class `hidden`
- In `frontend/css/style.css`, `.hidden` is only defined for specific elements:
  - `.phase-section.hidden` (line 50)
  - `.modal.hidden` (line 132)
  - `#loading-overlay.hidden` (line 365)
  - `#error-toast.hidden` (line 695)
- There is NO generic `.hidden { display: none; }` rule
- Result: Browser ignores the `hidden` class for verification panel

---

## Required Fix

### Option A: Add Global `.hidden` Class (Recommended)

**File**: `frontend/css/style.css`

**Location**: Add near the top of the file (after base styles, around line 20)

**Code to Add**:
```css
/* Global utility class for hiding elements */
.hidden {
    display: none !important;
}
```

**Note**: Using `!important` ensures it overrides any element's default display style.

---

### Option B: Add Specific Rule for Verification Panel

**File**: `frontend/css/style.css`

**Location**: After `.verification-panel` styles (around line 388)

**Code to Add**:
```css
.verification-panel.hidden {
    display: none;
}
```

---

## Acceptance Criteria

After fix, verify:

1. **Page Load**:
   - Verification panel is NOT visible on initial page load
   - Only investigation phase content is visible

2. **After Voting**:
   - Verification panel appears after voting completes
   - Panel shows loading spinner while fetching data
   - Panel displays verification data after API response

3. **No Regression**:
   - Other `.hidden` elements still work correctly
   - Modals still hide/show properly
   - Phase sections still toggle correctly

---

## Testing Steps

1. Start the game: `python start.py`
2. Open browser to game URL
3. Verify verification panel is NOT visible
4. Complete investigation phase
5. Complete persuasion phase
6. Trigger voting
7. Verify verification panel appears ONLY after voting completes
8. Verify panel shows correct data

---

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/css/style.css` | +3 lines (add `.hidden` rule) |

**Do NOT modify**:
- `frontend/index.html` (HTML structure is correct)
- `frontend/js/game.js` (JS logic is correct)
- Backend files

---

## Related Issues

This fix also resolves:
- Loading spinner appearing on page load
- Layout clutter with multiple panels visible

---

**Ready for Implementation**: Yes
**Estimated Effort**: 5 minutes
**Risk Level**: Low
