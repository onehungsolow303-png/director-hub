# Debug Skill

Structured debugging workflow. Follow these steps in order — do not skip ahead.

## Steps

1. **Reproduce** — Read the relevant code and run it to confirm the issue. Capture the exact error message or incorrect output.

2. **Isolate** — Add diagnostic logging (`console.log` for JS, `print` for Python) to trace actual values at each step of the pipeline. Run again and share output. Do NOT change functional code yet.

3. **Identify root cause** — Based on the traced values, identify exactly where the behavior diverges from expectation. State the root cause clearly before proposing any fix.

4. **Minimal fix** — Propose the smallest change that fixes the root cause. Explain what it changes and why. Show the diff before applying.

5. **Verify** — Run the code again to confirm the fix works and output matches expectation.

6. **Check adjacents** — Look for the same bug pattern in related code. If the mask polarity was wrong in one place, check all mask consumers.

## Rules

- Never apply speculative fixes without completing steps 1-3 first.
- If a fix introduces a new bug, restart from step 1 — do not stack fixes.
- For canvas/image issues, always log: image dimensions, channel count, value ranges (min/max), and cross-origin status.
