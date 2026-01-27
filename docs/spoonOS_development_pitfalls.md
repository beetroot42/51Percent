# SpoonOS Development Pitfalls (Summary)

This document summarizes recurring integration pitfalls observed while building SpoonOS-based agents.

## 1. Provider Registration

Problem:
- Provider exists but is not registered, causing errors like:
  `Provider 'openai_compatible' not registered`

Fix:
- Ensure providers are registered via the SpoonOS registry mechanism.

## 2. Base URL Formatting

Problem:
- Base URL includes `/chat/completions`, which leads to duplicated paths.

Correct:
```
OPENAI_COMPATIBLE_BASE_URL=https://api.example.com/v1
```

## 3. Environment Isolation

Problem:
- Running with system Python instead of the intended virtual environment.

Fix:
- Activate and use the project venv.

## 4. Encoding Issues on Windows

Problem:
- Files saved in UTF-8 are read using a legacy code page.

Fix:
- Read/write text with `encoding="utf-8"` and keep documentation in ASCII when possible.

## 5. Tool and Prompt Sync

Problem:
- Tool capabilities change but prompts are not updated.

Fix:
- Update prompts whenever tools, parameters, or behaviors change.

## 6. Testing Strategy

- Use layered tests: basic import, unit tests, and integration tests.
- Keep a minimal end-to-end path runnable.
