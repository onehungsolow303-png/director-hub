# QA Runbook

Primary references:
- [AUDIT_INSTRUCTION_SHEET.md](C:\Dev\Image generator\AUDIT_INSTRUCTION_SHEET.md)
- [LIVE_TEST_MATRIX.md](C:\Dev\Image generator\LIVE_TEST_MATRIX.md)
- [LIVE_TEST_RESULTS_TEMPLATE.md](C:\Dev\Image generator\LIVE_TEST_RESULTS_TEMPLATE.md)
- [PROJECT_MEMORY.md](C:\Dev\Image generator\PROJECT_MEMORY.md)

App under test:
- [index.html](C:\Dev\Image generator\index.html)
- [app.js](C:\Dev\Image generator\app.js)
- [styles.css](C:\Dev\Image generator\styles.css)

Purpose:
- provide one place to run the app QA cycle
- keep audit criteria, test scenarios, and results aligned
- help future sessions continue work without rediscovering context

## Workflow

1. Read:
- [PROJECT_MEMORY.md](C:\Dev\Image generator\PROJECT_MEMORY.md)
- [AUDIT_INSTRUCTION_SHEET.md](C:\Dev\Image generator\AUDIT_INSTRUCTION_SHEET.md)

2. Execute live image tests from:
- [LIVE_TEST_MATRIX.md](C:\Dev\Image generator\LIVE_TEST_MATRIX.md)

3. Record outcomes in:
- [LIVE_TEST_RESULTS_TEMPLATE.md](C:\Dev\Image generator\LIVE_TEST_RESULTS_TEMPLATE.md)

4. For each failure:
- identify whether it is:
  - setup/tuning only
  - UX clarity issue
  - code bug
  - missing capability

5. If code changes are made:
- update the relevant docs
- run JS syntax check on [app.js](C:\Dev\Image generator\app.js)
- re-test the affected matrix case(s)

## Required checks after any code modification

1. Syntax
- run JS syntax validation on [app.js](C:\Dev\Image generator\app.js)

2. UI state
- confirm buttons disable correctly when no image/result exists
- confirm mode switches do not leave stale manual state
- confirm sampling tools shut down cleanly when switching tools

3. Preview integrity
- confirm original preview overlays still render:
  - background points
  - keep points
  - keep boxes
  - remove boxes
  - brush marks

4. Split gallery integrity
- confirm:
  - likely UI filter works
  - show all panels works
  - tiny fragment threshold works
  - usefulness sort works
  - panel click promotes to main preview

## Recommended test order

1. [UI2.1.png](C:\Dev\Image generator\input\UI2.1.png)
2. [BananaProAI_com-2026320191551.png](C:\Dev\Image generator\input\BananaProAI_com-2026320191551.png)
3. [Example UI 1.png](C:\Dev\Image generator\input\Example UI 1.png)
4. [BananaProAI_com-2026322123439.png](C:\Dev\Image generator\input\BananaProAI_com-2026322123439.png)
5. brush-only detail check on [Example UI 1.png](C:\Dev\Image generator\input\Example UI 1.png)

## Pass / Fail Rules

Mark a case:
- `Pass`
  - no code change needed
- `Pass with tuning`
  - workflow/settings guidance needed, but core logic is acceptable
- `Needs code improvement`
  - repeatable flaw in logic, UI, or exports

## Current highest-risk area

The hardest scenario remains:
- [Example UI 1.png](C:\Dev\Image generator\input\Example UI 1.png)

Why:
- it mixes ornate UI with a textured scenic background
- preservation of UI quality and suppression of scenic fragments are both required

Likely future upgrades if this case still fails:
- dedicated `UI frame mode`
- stronger foreground-vs-background segmentation
- smarter bar/strip/frame detection
- stronger scene-fragment rejection before split export
