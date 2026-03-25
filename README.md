# ComfyUI Asset Editor Builder

This is a lightweight offline starter app for planning ComfyUI workflows for:

- background removal
- game UI generation
- combined generate-and-cutout pipelines

## What it does

- asks plain-language setup questions
- lists the exact node names to install
- generates model-specific positive and negative prompts
- exports a ComfyUI API workflow JSON template

## Run it

Open [index.html](C:\Dev\Image generator\index.html) in a browser.

## QA and continuity

- Session history: [SESSION_HISTORY.md](C:\Dev\Image generator\SESSION_HISTORY.md)
- Audit spec: [AUDIT_INSTRUCTION_SHEET.md](C:\Dev\Image generator\AUDIT_INSTRUCTION_SHEET.md)
- Live test plan: [LIVE_TEST_MATRIX.md](C:\Dev\Image generator\LIVE_TEST_MATRIX.md)
- Live test results sheet: [LIVE_TEST_RESULTS_TEMPLATE.md](C:\Dev\Image generator\LIVE_TEST_RESULTS_TEMPLATE.md)
- Combined runbook: [QA_RUNBOOK.md](C:\Dev\Image generator\QA_RUNBOOK.md)
- Persistent project memory: [PROJECT_MEMORY.md](C:\Dev\Image generator\PROJECT_MEMORY.md)
- AI extraction roadmap: [AI_EXTRACTION_ARCHITECTURE.md](C:\Dev\Image generator\AI_EXTRACTION_ARCHITECTURE.md)
- AI mask workflow guide: [AI_MASK_WORKFLOW_GUIDE.md](C:\Dev\Image generator\AI_MASK_WORKFLOW_GUIDE.md)
- AI mask quickstart: [AI_MASK_QUICKSTART.md](C:\Dev\Image generator\AI_MASK_QUICKSTART.md)

## Notes

- The exported JSON is an API-style workflow template, not a full saved canvas layout from the ComfyUI UI.
- Custom-node class names can vary slightly between packs. The app keeps those visible so you can swap the exact node if your install uses a different internal name.
- PNG should be used for transparent exports.
