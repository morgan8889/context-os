# Spec Review — 6a689fbe8ea6

## Changes Reviewed

### web/src/views/onboarding/OnboardingView.tsx
- Adds `!pat.trim()` case to button background ternary: `oklch(30% 0 0)` (muted dark gray)
- Sets text color to `oklch(50% 0 0)` when PAT is empty — visually communicates disabled state
- HTML `disabled` attribute was already correct; this aligns visual appearance with DOM state

## Spec Compliance
- Button is now visually muted (dark gray, dimmed text) when no PAT is entered
- Becomes blue and active only after user types a token — matches expected UX

## Verdict: PASS
