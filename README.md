# Gut It Out — UI Asset and Object Extractor

A specialized tool for cleanly extracting game UI elements and objects from screenshots while preserving quality, borders, and transparency.

## What it does

- Detects and isolates game UI elements from their background
- Preserves UI borders and fine details intact
- Maintains original size, position, and resolution
- Removes background while keeping UI on transparent background
- Uses multi-spectrum border detection with invert-selection architecture (v5+)

## Run it

Open [index.html](C:\Dev\Image generator\index.html) in a browser. The app opens directly in the browser; the Python server is optional and needed only for Python API endpoints (border detection, extraction).

## QA and continuity

- Git workflow: [GIT_WORKFLOW.md](C:\Dev\Image generator\GIT_WORKFLOW.md)
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

- PNG should be used for transparent exports.
- Browser ONNX (u2netp) provides AI segmentation masks without external dependencies.
