# Autonomous Quality Improvement Loop — Design Spec

## Goal

Build a self-driving orchestrator that iterates through test → analyze → research → fix → retest cycles until the extraction engine's output matches golden reference quality. Two phases: rapid parameter tuning, then structural code changes. Branch-per-attempt ensures main branch only gets better.

## Architecture

```
MASTER (loop orchestrator — drives iterations, makes no code changes)
  ├── test-runner        — runs pytest suite, returns metrics JSON
  ├── research-advisor   — analyzes failures, reads rules, proposes change strategy
  ├── extraction-analyst — implements ONE change per iteration in app.js
  └── quality-checker    — compares before/after metrics, decides cherry-pick or abandon
```

Master orchestrates the loop. It never writes code. It dispatches agents for each step, collects results, logs everything, and decides when to escalate or stop.

## Quality Targets

| Metric | Dark Target | Light Target |
|--------|-------------|--------------|
| Alpha IoU | >= 0.99 | >= 0.998 |
| Alpha MAE | <= 2.0 | <= 0.3 |
| SSIM | >= 0.20 | >= 0.50 |

**Current baseline (2026-03-29):**
| Metric | Dark Current | Light Current |
|--------|-------------|--------------|
| Alpha IoU | 0.977 | 0.997 |
| Alpha MAE | 4.71 | 0.61 |
| SSIM | 0.097 | 0.392 |

## Iteration Caps

| Parameter | Value |
|-----------|-------|
| Phase 1 max iterations | 10 |
| Phase 2 max iterations | 5 |
| Plateau trigger | 3 consecutive no-improvement iterations |
| Total max wall time | No hard cap (user can Ctrl+C) |

## Change Management: Branch-Per-Attempt

```
main (baseline, only improves)
  ├── iter/p1-01  → test → improved? → cherry-pick to main
  ├── iter/p1-02  → test → worse? → abandon, log to what-worked.md
  ├── iter/p1-03  → test → improved? → cherry-pick to main
  ...
  ├── iter/p2-01  → test → improved? → cherry-pick to main
  └── iter/p2-02  → test → worse? → abandon, log to what-worked.md
```

- Each iteration starts a fresh branch from current main
- Tests run on the branch
- If best metric (Alpha IoU average) improved → cherry-pick commit to main
- If worse or no change → leave branch as reference, log failure
- Main branch only ever gets better

---

## Phase 1: Rapid Parameter Tuning

### What Can Change

Only the 51 documented parameters in `buildBlackBorderUiMask` (38) and `buildStructuralUiMask` (13). ONE parameter per iteration.

### Key Parameters (priority order for tuning)

These are the highest-impact parameters based on extraction-engine.md analysis:

**Background Scoring Weights** (control what gets classified as background):
| Parameter | Current | Line | Controls |
|-----------|---------|------|----------|
| Variance weight | 0.35 | ~1790 | How much color variance matters for bg detection |
| Size weight | 0.30 | ~1791 | How much region size matters |
| Edge sides weight | 0.25 | ~1792 | How much edge-touching matters |
| Anti-rectangularity weight | 0.10 | ~1793 | How much irregularity matters |

**Border Detection Thresholds** (control what pixels become borders):
| Parameter | Current | Line | Controls |
|-----------|---------|------|----------|
| gradThreshold clamp min | 25 | ~1582 | Minimum gradient threshold |
| gradThreshold clamp max | 50 | ~1582 | Maximum gradient threshold |
| Dark achromatic maxCh | 55 | ~1616 | Max brightness for dark border pixels |
| Dark achromatic spread | 12 | ~1616 | Max color spread for achromatic |
| distToEdge limit | 2 | ~1616 | How far from edges dark pixels qualify |

**UI Shape Protection** (prevent panels from being classified as bg):
| Parameter | Current | Line | Controls |
|-----------|---------|------|----------|
| Thin bar aspect | 3 | ~1811 | Min aspect ratio for bar detection |
| Thin bar max height | 0.25 | ~1811 | Max height ratio for bar detection |
| Wide bar min width | 0.4 | ~1812 | Min width ratio for wide bar detection |
| Compact panel bounds | 0.05-0.25 | ~1813 | Size bounds for square panel detection |
| Rectangularity threshold | 0.55 | ~1814 | Min rectangularity for shape protection |

**Trapped Background Detection** (remove scenic content trapped inside UI):
| Parameter | Current | Line | Controls |
|-----------|---------|------|----------|
| Variance ratio | 0.45 | ~1853 | Threshold for high-variance signal |
| Rectangularity limit | 0.40 | ~1854 | Threshold for irregular-shape signal |
| Edge density ratio | 0.50 | ~1855 | Threshold for high-detail signal |
| Border contact limit | 0.50 | ~1856 | Threshold for poor-contact signal |
| Signal count (large) | 2 | ~1859 | Signals needed for large regions (>2%) |
| Signal count (small) | 3 | ~1859 | Signals needed for small regions |

### Phase 1 Iteration Steps

```
1. MASTER creates branch: git checkout -b iter/p1-{N} main
2. MASTER dispatches test-runner:
   - Run: pytest tests/ -v --tb=short
   - Return: quality_report.json metrics
3. MASTER checks targets:
   - If ALL targets met → DONE (success)
   - If plateau (3 consecutive no-improvement) → escalate to Phase 2
4. MASTER dispatches research-advisor:
   - Input: current metrics, iteration history, what-worked.md, extraction-engine.md
   - Task: identify which metric is furthest from target, which parameter
     most likely to improve it, predict direction (increase/decrease)
   - Output: { parameter, current_value, proposed_value, hypothesis, risk }
5. MASTER dispatches extraction-analyst:
   - Input: research-advisor's recommendation
   - Task: modify EXACTLY ONE parameter in app.js
   - Must: run node --check app.js after edit
   - Output: { file, line, old_value, new_value }
6. MASTER dispatches test-runner:
   - Run full test suite on branch
   - Return: new metrics
7. MASTER dispatches quality-checker:
   - Input: before metrics, after metrics
   - Task: compare Alpha IoU (average of dark + light)
   - Output: { improved: bool, delta, recommendation: "cherry-pick" | "abandon" }
8. MASTER acts on recommendation:
   - If improved: git checkout main && git cherry-pick <commit>
   - If not improved: git checkout main (abandon branch)
9. MASTER logs iteration to what-worked.md and iteration_history.json
10. Loop back to step 1
```

### Iteration Log Format

Append to what-worked.md after each iteration:

```markdown
### Iteration P1-{N}: {parameter_name} {old} → {new} ({date})
- **Hypothesis**: {why this change should help}
- **Dark Alpha IoU**: {before} → {after} ({delta:+/-})
- **Light Alpha IoU**: {before} → {after} ({delta:+/-})
- **Dark SSIM**: {before} → {after}
- **Light SSIM**: {before} → {after}
- **Result**: IMPROVEMENT / NO CHANGE / REGRESSION
- **Keep**: YES (cherry-picked) / NO (branch abandoned)
- **Branch**: iter/p1-{N}
```

---

## Phase 2: Structural Code Changes

### When to Escalate

Phase 2 starts when:
- Phase 1 exhausted (10 iterations), OR
- Phase 1 plateaued (3 consecutive no-improvement iterations)

### What Can Change

Any code within `buildBlackBorderUiMask` or `buildStructuralUiMask` including:
- Adding new detection signals (new metrics, new scoring factors)
- Modifying scoring logic (how signals combine)
- Adding new pipeline stages (e.g., a post-processing cleanup pass)
- Improving existing stages (better border detection, better component labeling)

### What Cannot Change

- The overall invert-selection architecture (identify bg → invert → mask)
- The pipeline order (border → enhance → segment → score → invert → mask)
- Functions outside the detection pipeline (UI code, canvas handling, etc.)
- Any approach listed as "FAILED" in what-worked.md

### Phase 2 Iteration Steps

```
1. MASTER creates branch: git checkout -b iter/p2-{N} main
2. MASTER dispatches test-runner → collect current metrics
3. MASTER checks targets → if met, DONE
4. MASTER dispatches research-advisor with EXPANDED scope:
   - Input: ALL iteration history, full what-worked.md, current metrics,
     quality_report.html (visual diff analysis)
   - Task: analyze patterns across all failed iterations:
     * Which regions consistently fail? (topbar? botbar? portrait? background?)
     * What type of error? (over-removal? under-removal? fragmentation?)
     * What structural limitation prevents parameter tuning from fixing this?
   - Output: { analysis, proposed_code_change, files_affected, risk_assessment }
5. MASTER reviews research and decides go/no-go
6. MASTER dispatches extraction-analyst:
   - Input: research-advisor's proposed code change with full context
   - Task: implement the structural change, following extraction-engine.md rules
   - Must: add parameters (not remove), log values, run syntax check
   - Output: { description, files_changed, new_parameters_added }
7. MASTER dispatches test-runner → new metrics
8. MASTER dispatches quality-checker → improved?
9. Cherry-pick or abandon (same as Phase 1)
10. MASTER logs iteration with full details
11. Loop back to step 1
```

### Phase 2 Iteration Log Format

```markdown
### Iteration P2-{N}: {description} ({date})
- **Change type**: {new signal / modified scoring / new stage / etc.}
- **What was changed**: {description of code change}
- **Files modified**: {list with line ranges}
- **New parameters added**: {list with values}
- **Hypothesis**: {why this structural change should help}
- **Dark Alpha IoU**: {before} → {after} ({delta})
- **Light Alpha IoU**: {before} → {after} ({delta})
- **All metrics**: {full table}
- **Result**: IMPROVEMENT / NO CHANGE / REGRESSION
- **Keep**: YES / NO
- **Branch**: iter/p2-{N}
```

---

## Data Flow

```
                    ┌──────────────────────┐
                    │   iteration_history   │
                    │   .json (append)      │
                    └──────────┬───────────┘
                               │
┌──────────┐    ┌──────────┐  │  ┌───────────────┐    ┌──────────────┐
│ pytest    │───▶│ quality  │──┴─▶│ what-worked   │◀───│ research     │
│ suite     │    │ report   │     │ .md (append)  │    │ advisor      │
│ (36 tests)│    │ .json    │     └───────────────┘    └──────────────┘
└──────────┘    └──────────┘                                  │
                                                              ▼
                                                     ┌──────────────┐
                                                     │ extraction   │
                                                     │ analyst      │
                                                     │ (modifies    │
                                                     │  app.js)     │
                                                     └──────────────┘
```

### Files Read/Written Per Iteration

| File | Read | Written |
|------|------|---------|
| `tests/reports/quality_report.json` | quality-checker | test-runner |
| `tests/reports/quality_report.html` | research-advisor (P2) | test-runner |
| `.claude/rules/what-worked.md` | research-advisor | master |
| `.claude/rules/extraction-engine.md` | research-advisor, extraction-analyst | — |
| `app.js` | extraction-analyst | extraction-analyst |
| `tests/reports/iteration_history.json` | master | master |

### iteration_history.json Schema

```json
{
  "baseline": {
    "date": "2026-03-29",
    "dark_alpha_iou": 0.977,
    "light_alpha_iou": 0.997,
    "dark_ssim": 0.097,
    "light_ssim": 0.392,
    "dark_alpha_mae": 4.71,
    "light_alpha_mae": 0.61
  },
  "targets": {
    "dark_alpha_iou": 0.99,
    "light_alpha_iou": 0.998,
    "dark_alpha_mae": 2.0,
    "light_alpha_mae": 0.3,
    "dark_ssim": 0.20,
    "light_ssim": 0.50
  },
  "iterations": [
    {
      "id": "p1-01",
      "phase": 1,
      "parameter": "bgVarianceWeight",
      "old_value": 0.35,
      "new_value": 0.40,
      "hypothesis": "Increasing variance weight helps identify dark scene backgrounds",
      "metrics_before": { "dark_alpha_iou": 0.977, "light_alpha_iou": 0.997 },
      "metrics_after": { "dark_alpha_iou": 0.981, "light_alpha_iou": 0.996 },
      "improved": true,
      "kept": true,
      "branch": "iter/p1-01"
    }
  ],
  "best_so_far": {
    "dark_alpha_iou": 0.981,
    "light_alpha_iou": 0.997
  }
}
```

---

## Orchestrator Implementation

The loop runs as a single Python script (`tests/quality_loop.py`) invoked from the CLI. It dispatches Claude Code subagents for each role. The orchestrator itself:

1. Manages git branches (create, cherry-pick, checkout)
2. Reads/writes iteration_history.json
3. Appends to what-worked.md
4. Dispatches agents via subprocess or the Agent tool
5. Tracks plateau detection (consecutive no-improvement counter)
6. Decides phase transitions

### Entry Point

```bash
.venv/Scripts/python.exe tests/quality_loop.py
```

Or invoked by the master agent directly using the Agent tool chain.

### Stopping Conditions

The loop stops when ANY of these are true:
1. All quality targets met (success)
2. Phase 1 max iterations reached AND Phase 2 max iterations reached
3. User interrupts (Ctrl+C)

On stop, the orchestrator prints a final summary:
- Starting metrics vs ending metrics
- Total iterations run (Phase 1 + Phase 2)
- Changes kept vs abandoned
- Remaining gap to targets
- Recommended next steps

---

## Safety Guardrails

1. **Main branch protection**: Main only receives cherry-picked improvements. Never force-pushed.
2. **Syntax validation**: `node --check app.js` runs after every edit. If syntax fails, iteration aborts.
3. **No retry of failed approaches**: Research-advisor MUST read what-worked.md before proposing. If an approach was previously marked FAILED/REGRESSION, it cannot be retried.
4. **One change per iteration**: extraction-analyst makes exactly one parameter change (P1) or one code change (P2). Multiple changes in one iteration are rejected.
5. **Test suite must complete**: If pytest crashes or times out, iteration is abandoned.
6. **Light preset protection**: If a change improves dark but degrades light Alpha IoU by more than 0.005, the change is abandoned. Light presets are already near-target and must not regress.
7. **Architecture preservation**: The v5+ invert-selection architecture cannot be replaced. Only enhanced.

---

## Success Criteria

The loop is considered successful when:
- Dark Alpha IoU >= 0.99 AND Light Alpha IoU >= 0.998
- OR significant progress made (>50% of gap closed) with clear next steps documented

The loop is considered complete (even if targets not fully met) when:
- All iterations exhausted
- Final report written with findings and recommendations
- What-worked.md updated with all iteration results
- Main branch contains only net-positive changes
