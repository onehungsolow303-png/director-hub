# Session History

This file compiles the major project milestones completed so far for the local browser-based UI asset cleanup tool.

## Project identity

- Project type: local browser app for UI asset extraction, cleanup, and workflow planning
- Primary app files:
  - [index.html](C:\Dev\Image generator\index.html)
  - [app.js](C:\Dev\Image generator\app.js)
  - [styles.css](C:\Dev\Image generator\styles.css)

## Phase 1: ComfyUI startup and environment recovery

- Fixed ComfyUI startup blockers caused by missing workspace folders.
- Created expected directories for:
  - `user`
  - `custom_nodes`
  - `models`
  - `input`
  - `output`
  - `temp`
- Resolved a bad user-directory path issue.
- Resolved a missing `custom_nodes` path issue.
- Switched ComfyUI launch behavior away from broken CUDA assumptions and restored startup.
- Installed or reloaded required node packs so the user could begin testing workflows.

## Phase 2: Background removal workflow troubleshooting

- Tested ComfyUI-based background removal.
- Confirmed that generic rembg-style background removal was the wrong tool for flat UI sheets and decorative panel assets.
- Identified that color-based or mask-based extraction was a better fit than subject-removal models for these files.
- Built early manual ComfyUI graph attempts for:
  - image load
  - rembg session
  - save image
- Confirmed those workflows were too fragile for the user’s asset type.

## Phase 3: Scripted extraction fallback

- Created a scripted local extraction tool in:
  - [scripted\remove_black_bg.py](C:\Dev\Image generator\scripted\remove_black_bg.py)
- Added documentation in:
  - [scripted\README.md](C:\Dev\Image generator\scripted\README.md)
- Added tunable background-removal parameters.
- Added split-component export behavior.
- Added tighter defaults for UI-style assets.
- Added batch processing support.
- Added PowerShell launchers and double-click batch files.

## Phase 4: Browser cleanup app

- Expanded [index.html](C:\Dev\Image generator\index.html), [app.js](C:\Dev\Image generator\app.js), and [styles.css](C:\Dev\Image generator\styles.css) into a local browser cleanup app.
- Added image upload, preview, extraction, and PNG export.
- Added support for:
  - dark background removal
  - light background removal
  - split panel detection
  - split panel download
- Added larger preview areas and better gallery behavior.
- Added panel promotion so a gallery item can become the main preview.

## Phase 5: Manual protection and extraction controls

- Added manual keep and removal tools:
  - background sample points
  - UI keep points
  - UI keep boxes
  - scenery remove boxes
  - keep brush
  - remove brush
- Added utility tools:
  - undo last brush edit
  - clear keep boxes
  - clear remove boxes
  - clear brush keep marks
  - clear brush remove marks
- Added quick-protect actions:
  - protect top bar
  - protect bottom bar
  - protect icon strip
- Added auto-detect UI boxes.
- Added bad keep-box erasing.
- Added edge-snapped keep boxes.

## Phase 6: Split gallery and export control

- Added split gallery labeling:
  - likely UI asset
  - protected UI box
  - brushed UI detail
  - possible scenery fragment
- Added gallery filters:
  - show likely UI only
  - show all panels
- Added tiny-fragment hiding threshold.
- Added usefulness sorting.
- Added original-canvas-position exports for separated assets.
- Split behavior now supports:
  - tight crop each asset
  - keep original canvas size and position

## Phase 7: QA and audit infrastructure

- Added project-wide documentation:
  - [AUDIT_INSTRUCTION_SHEET.md](C:\Dev\Image generator\AUDIT_INSTRUCTION_SHEET.md)
  - [LIVE_TEST_MATRIX.md](C:\Dev\Image generator\LIVE_TEST_MATRIX.md)
  - [LIVE_TEST_RESULTS_TEMPLATE.md](C:\Dev\Image generator\LIVE_TEST_RESULTS_TEMPLATE.md)
  - [QA_RUNBOOK.md](C:\Dev\Image generator\QA_RUNBOOK.md)
  - [PROJECT_MEMORY.md](C:\Dev\Image generator\PROJECT_MEMORY.md)
- Created persistent project-memory and QA packet files so the workspace retains context across sessions.
- Ran repeated code audits against current app behavior and fixed:
  - mismatched clear-tool behavior
  - split-gallery state issues
  - event cleanup bugs
  - manual mask path issues

## Phase 8: AI-mask architecture and import path

- Added documentation for future AI-assisted extraction:
  - [AI_EXTRACTION_ARCHITECTURE.md](C:\Dev\Image generator\AI_EXTRACTION_ARCHITECTURE.md)
  - [AI_MASK_WORKFLOW_GUIDE.md](C:\Dev\Image generator\AI_MASK_WORKFLOW_GUIDE.md)
  - [AI_MASK_QUICKSTART.md](C:\Dev\Image generator\AI_MASK_QUICKSTART.md)
- Added AI-ready UI scaffolding for:
  - future AI model family
  - mask confidence
  - matte refinement
  - spill suppression
  - relight/inpaint staging flags
- Added internal mask-layer separation:
  - processed mask
  - manual corrections mask
  - imported AI mask
- Added:
  - `Load AI Mask PNG`
  - `Download Mask PNG`
  - mask preview mode
  - imported-mask-driven extraction path
- Added imported-mask refinement controls:
  - invert mask
  - expand/contract
  - feather
  - combine manual corrections

## Phase 9: Edge cleanup and layout preservation

- Background removal became the preferred working mode for current UI-sheet assets.
- Added stronger edge cleanup logic for light-background sheets:
  - defringe
  - bright speck cleanup
  - opaque edge repair
  - structure-guided edge pull
  - border-neighbor propagation
  - median-style edge repair
- Added:
  - edge cleanup strength
  - strong border edge repair
- Preserved original full-sheet layout as the main result option.
- Preserved separated-asset exports as optional secondary outputs.

## Current state

- The app’s best current path for this user’s assets is:
  - `Background removal`
  - full-sheet transparent result
  - optional split assets
- AI mask mode is structurally ready but still depends on a good imported grayscale matte.
- High-quality local segmentation/matting is the next major architectural upgrade if heuristic cleanup remains insufficient.

## Most recent known next steps

- Continue polishing edge cleanup on the background-removal path.
- Keep full-sheet layout preservation as the primary output.
- Use imported AI masks only when a high-quality matte exists.
- If needed later:
  - integrate real local AI segmentation
  - add alpha matting
  - add spill suppression from matte confidence
