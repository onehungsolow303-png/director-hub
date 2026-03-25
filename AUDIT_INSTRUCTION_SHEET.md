# Audit Instruction Sheet

App name/type: `Local Cleanup App` for extracting UI assets from mixed-scene screenshots while preserving UI quality.

Purpose: guide an LLM through a final code audit of the browser-based asset cleanup tool implemented around [index.html](C:\Dev\Image generator\index.html), [app.js](C:\Dev\Image generator\app.js), and [styles.css](C:\Dev\Image generator\styles.css).

## Scope
The app’s job is not generic photo background removal. It is a UI-preservation tool for game/mockup screenshots where:

- UI bars, icon strips, side rails, frames, and parchment panels must stay visually intact
- scenery/background should be removed or suppressed
- the user needs manual control when automation fails
- split exports should favor useful UI components over scenic junk

## Core Logic
1. Image lifecycle
- User uploads a local image file.
- App renders the original into an editable preview canvas.
- App resets all prior state on new image load:
  - background samples
  - UI keep points
  - UI keep boxes
  - scenery subtract boxes
  - keep brush points
  - prior result canvases and split panels

2. Extraction modes
- `Background removal`
  - single-sample or auto-sampled color-distance based alpha extraction
- `Tight object crop for dark mats`
  - crop around a main object when the background is a presentation mat
- `Multi-point background erase`
  - seeded from explicit background clicks
  - must prioritize connected background/scenery removal over global color wiping

3. Multi-point background logic
- Background clicks must store both pixel coordinates and sampled RGB.
- Removal should begin from sampled background seeds and expand through connected matching scenery.
- UI that is disconnected from seeded scenery should survive by default.
- Multi-point mode must not feel like a plain chroma key.

4. UI preservation logic
- User must be able to protect UI explicitly with:
  - keep points
  - keep boxes
  - keep brush marks
  - one-click protection presets
- Preserved UI should retain original pixel color whenever possible.
- The app must prefer original source pixels for kept UI over “washed” processed output.

5. Manual protection tools
- `Mark UI Keep Point(s)`
  - click key foreground/UI details to preserve
- `Draw UI Keep Box(es)`
  - drag multiple green boxes around UI regions
- `Brush Keep Edges`
  - paint preservation marks over ornate borders and fragile decorative edges
- `Protect Top Bar`
- `Protect Bottom Bar`
- `Protect Icon Strip`
  - preset helpers that create approximate keep boxes for common UI layouts
- Box drawing should support multiple boxes in one session.

6. Manual removal tools
- `Draw Scenery Remove Box(es)`
  - drag red boxes over scenery junk that should be forcibly removed
- `Erase Bad Keep Box(es)`
  - remove incorrect green protection boxes individually
- `Clear UI Keep Box(es)`
  - clear only green keep boxes
- `Clear Scenery Remove Box(es)`
  - clear only red subtract boxes
- `Clear Brush Keep Marks`
  - clear only brush-preserve marks

7. Edge snapping / box refinement
- Keep boxes should not remain purely raw drag rectangles.
- When possible, a drawn keep box should snap toward nearby non-background content boundaries.
- Preset boxes should also attempt boundary-aware snapping.

8. Processing pipeline expectations
- Pass 1 should be conservative:
  - favor keeping questionable UI pixels
  - avoid damaging preserved UI
- Pass 2 should be more aggressive:
  - refine edges
  - remove weak scenic leftovers
- `Preserve original asset colors in the main preview/export` must bias the main result toward source colors.
- Split panels must be built from original image data plus alpha, not from degraded postprocessed imagery.

9. Result composition
- Main preview should show the preserved output.
- Split panels should show likely useful UI assets, not random scenic fragments.
- If keep boxes/keep points exist in multi-point mode, result composition should prioritize those protected regions.

10. Component filtering
- Component detection must reject likely scene junk:
  - giant edge-touching scenic remnants
  - weak noisy fragments
  - disconnected scenery chunks
- Component selection should favor:
  - top bars
  - bottom bars
  - icon strips
  - framed panels
  - side rails
  - rectangular UI blocks

11. UX state handling
- Buttons must disable when invalid.
- App must clearly communicate readiness and missing prerequisites.
- Multi-point mode must not allow processing before required background samples exist.
- App must show busy/progress state during processing.
- Cancel must work cleanly mid-process.
- Original preview should visually show:
  - background sample markers
  - keep point markers
  - keep boxes
  - subtract boxes
  - keep brush marks

## Technical Stack
Frontend:
- Plain HTML in [index.html](C:\Dev\Image generator\index.html)
- Plain JavaScript in [app.js](C:\Dev\Image generator\app.js)
- Plain CSS in [styles.css](C:\Dev\Image generator\styles.css)

Runtime:
- Browser-only, local-file compatible
- No mandatory backend
- No required external API

Browser APIs used/expected:
- `CanvasRenderingContext2D`
- `ImageData`
- `File` / file input
- `URL.createObjectURL`
- `Blob`
- download via anchor click
- DOM event listeners for click / drag / mousemove / mouseup / mouseleave

Tooling:
- JS syntax verification was done with local Node runtime
- No bundler requirement
- No framework dependency requirement

Optional future integrations:
- WASM/OpenCV for contour and rectangle detection
- ONNX/WebGPU/WebNN segmentation if moving beyond manual-guided extraction
- Pointer events if tablet/pen brush support becomes important

## Modifications & Advanced Logic
Previously requested advanced behavior that must be preserved in audit:

- larger preview boxes
- split gallery with larger cards
- clickable split cards that promote to main preview
- output format choice:
  - keep one result image
  - use split panel result
- dark/light background support
- multi-pass processing option
- progress overlay with estimated timing
- cancel button
- state-aware controls
- multi-point background erase
- keep UI points
- keep UI boxes
- scenery subtract boxes
- keep brush mode
- preset protect buttons for common UI shapes
- edge-snapped keep boxes
- original-color preservation
- component rejection for scenic junk
- original preview overlays for user guidance

Logic patterns to audit carefully:

- Conservative-first / aggressive-second alpha pipeline
- Connected-region flood-fill from sampled background seeds
- Foreground preservation from original source pixels
- Manual region overrides taking precedence over heuristics
- Deduplication of panel boxes
- Rejection of split panels overlapping subtract regions
- Resetting all transient state on new image load
- Avoiding stale UI state when switching modes

## UI/UX Requirements
Visual direction:
- intentional, readable, utility-focused
- larger preview zones
- larger split-panel gallery cards
- obvious button states
- visible sampling/protection overlays
- clear status messaging

Control expectations:
- one-click protect presets should be easy to reach
- destructive/cleanup actions should be explicit
- sampled counts should always be visible
- user should be able to recover from bad automation with manual tools

Language expectations:
- controls should use plain language, not CV jargon
- status text should explain what the app needs next

## Success Criteria
A perfect build passes this checklist:

1. Upload/reset
- Uploading a new file fully clears all old keep/remove/sample state.
- Original preview redraws correctly every time.

2. Processing stability
- No silent stalls.
- Busy state appears during work.
- Cancel stops cleanly.
- Controls disable and re-enable correctly.

3. Background removal quality
- Multi-point mode removes connected scenery rather than globally nuking colors.
- Preserved UI remains visually close to the source.
- Main result is not washed out when preserve-color mode is enabled.

4. UI preservation
- Keep points protect small UI details.
- Keep boxes protect larger UI sections.
- Brush keep preserves ornate trim and fragile edges.
- Preset protect buttons produce useful initial boxes.
- Edge snapping improves rough box placement.

5. Manual override quality
- Subtract boxes reliably remove scenery junk.
- Bad keep boxes can be removed individually.
- Clear action resets box state predictably.

6. Split export quality
- Split gallery favors actual UI assets.
- Scenic fragments are minimized or rejected.
- Split exports preserve source colors/quality.
- Clicking a split panel promotes it correctly.

7. Mode behavior
- `Background removal`, `Tight object crop`, and `Multi-point background erase` behave distinctly and predictably.
- Multi-point mode requires background samples before process is enabled.

8. Preview correctness
- Original preview shows all overlays accurately.
- Result preview reflects the actual current output.
- Metadata labels update correctly.

9. Code quality
- JS syntax passes.
- No dead controls in HTML that JS does not handle.
- No JS references to missing DOM elements.
- State transitions are centralized and consistent.
- Event listeners do not leak across mode changes.

10. User outcome
- User can preserve top bar, bottom bar, icon strip, and side UI pieces without losing picture quality.
- User can remove scenery while keeping UI assets largely untouched.
- User can iteratively refine tough images without leaving the app.

## Audit Priorities
Order the final code audit like this:

1. State model and mode transitions
2. Sampling / keep / subtract event handling
3. Alpha-generation and connected-region logic
4. Result composition from original pixels
5. Component filtering and split-panel selection
6. Overlay rendering and UX clarity
7. Reset behavior and stale-state prevention
8. Button enable/disable correctness
9. Performance on large images
10. Failure recovery and user control quality

## LLM Audit Directive
When auditing this app, optimize for:

- preserving UI fidelity over aggressive scenery removal
- deterministic user control over opaque automation
- manual override power for hard cases
- alignment between visible controls and actual behavior
- rejection of scenic junk in split exports
