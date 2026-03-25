# Project Memory

Project:
- local browser-based UI asset cleanup tool

Core files:
- [index.html](C:\Dev\Image generator\index.html)
- [app.js](C:\Dev\Image generator\app.js)
- [styles.css](C:\Dev\Image generator\styles.css)

Supporting docs:
- [GIT_WORKFLOW.md](C:\Dev\Image generator\GIT_WORKFLOW.md)
- [SESSION_HISTORY.md](C:\Dev\Image generator\SESSION_HISTORY.md)
- [AUDIT_INSTRUCTION_SHEET.md](C:\Dev\Image generator\AUDIT_INSTRUCTION_SHEET.md)
- [LIVE_TEST_MATRIX.md](C:\Dev\Image generator\LIVE_TEST_MATRIX.md)
- [LIVE_TEST_RESULTS_TEMPLATE.md](C:\Dev\Image generator\LIVE_TEST_RESULTS_TEMPLATE.md)
- [QA_RUNBOOK.md](C:\Dev\Image generator\QA_RUNBOOK.md)
- [AI_EXTRACTION_ARCHITECTURE.md](C:\Dev\Image generator\AI_EXTRACTION_ARCHITECTURE.md)
- [AI_MASK_WORKFLOW_GUIDE.md](C:\Dev\Image generator\AI_MASK_WORKFLOW_GUIDE.md)
- [AI_MASK_QUICKSTART.md](C:\Dev\Image generator\AI_MASK_QUICKSTART.md)

User priorities:
- preserve UI asset quality above all
- scenery/background removal should not destroy top bars, bottom bars, icon strips, or ornate frame details
- user wants manual control when automation is unreliable
- split gallery should help surface useful UI assets first
- app should keep getting cleaned up and hardened after each change

Implemented capabilities:
- background removal
- tight object crop for dark mats
- multi-point background erase
- keep points
- keep boxes
- keep brush marks
- subtract scenery boxes
- protect top bar / bottom bar / icon strip
- auto-detect UI boxes
- edge-snapped keep boxes
- preserve original asset colors
- second-pass edge refinement
- split gallery:
  - click to promote
  - likely UI filter
  - show all panels
  - hide tiny fragments threshold
  - sort by usefulness / size / source type
  - likely-fragment warning badges

Known hard case:
- [Example UI 1.png](C:\Dev\Image generator\input\Example UI 1.png)

Why it is hard:
- ornate UI over a busy scenic background
- user wants scenery removed while UI remains untouched

Current likely next upgrades if quality is still insufficient:
- dedicated UI frame mode
- true foreground keep vs background remove segmentation
- auto-detection for top bars, bottom bars, side rails, and framed blocks
- stronger rejection of scenic remnants in split exports

Current strategic direction:
- move from heuristic-only extraction toward AI segmentation + alpha matting
- preserve original UI pixels instead of regenerating the asset itself
- keep generative inpainting / relighting as separate workflows, not the default extraction path
- imported AI mask workflow is now documented and should be treated as the preferred high-quality extraction path until local model inference is added

Important maintenance rule:
- after any modification:
  - verify syntax on [app.js](C:\Dev\Image generator\app.js)
  - check for secondary improvements
  - update docs if behavior changed
