# Quality Review — 6a689fbe8ea6

## Changes Reviewed

### web/src/views/onboarding/OnboardingView.tsx
- Ternary chain: `done → busy → !pat.trim() → active` — correct precedence; empty-PAT check comes before the active-blue case
- `oklch(30% 0 0)` matches the `busy` gray — consistent disabled appearance
- `oklch(50% 0 0)` for dimmed text provides sufficient contrast against `oklch(30% 0 0)` background
- No logic changes — purely visual styling fix; `disabled` attribute and `handleConnect` guard (`if (!pat.trim()) return`) unchanged

## Issues Found
None.

## Verdict: PASS
