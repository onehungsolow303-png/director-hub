# Live Test Matrix

App under test:
- [index.html](C:\Dev\Image generator\index.html)
- [app.js](C:\Dev\Image generator\app.js)
- [styles.css](C:\Dev\Image generator\styles.css)

Audit reference:
- [AUDIT_INSTRUCTION_SHEET.md](C:\Dev\Image generator\AUDIT_INSTRUCTION_SHEET.md)

Purpose:
- run a focused image-quality QA pass against representative real files in [input](C:\Dev\Image generator\input)
- verify preservation of UI quality, manual-control workflow, and split export usefulness

Important note:
- this matrix is prepared from code review plus visual inspection of the source images
- it is the correct next live test plan, but it does not claim browser-executed pass/fail for every case yet

## Test Cases

### Case 1: Clean White UI Sheet
- File:
  - [UI2.1.png](C:\Dev\Image generator\input\UI2.1.png)
- Image type:
  - white background
  - multiple clean UI assets
  - top bar, bottom bar, center panel, portrait frame, small icon buttons
- Goal:
  - remove white background cleanly
  - preserve crisp UI edges
  - split gallery should surface useful assets first
- Recommended setup:
  - `Extraction mode`: `Background removal`
  - `Background tone`: `Light background`
  - `Preset`: `UI Hard`
  - `Preserve original asset colors`: `On`
  - `Use second-pass edge refinement`: `Off` initially
  - `Output format`: `Keep one result image`
- Expected outcome:
  - high-confidence success case
  - likely clean main result
  - split panels should be strong with little junk
- Pass criteria:
  - no visible white fringe on large assets
  - top bar and bottom bar remain full-color
  - small icon buttons do not disappear
  - `Show likely UI only` view should look mostly clean
- Likely tuning:
  - if edges are too soft, lower `Softness`
  - if white halo remains, raise `Threshold` slightly

### Case 2: White UI Sheet With Heavy Bottom Texture
- File:
  - [BananaProAI_com-2026320191551.png](C:\Dev\Image generator\input\BananaProAI_com-2026320191551.png)
- Image type:
  - mostly white background
  - clean central assets
  - heavy decorative rock strip at the bottom
- Goal:
  - preserve intended UI
  - determine whether bottom rock strip is treated as keep-worthy UI or visual junk depending on user intent
- Recommended setup:
  - `Extraction mode`: `Background removal`
  - `Background tone`: `Light background`
  - `Preset`: `UI Balanced`
  - `Preserve original asset colors`: `On`
  - `Output format`: `Split panel result`
- Expected outcome:
  - should succeed technically
  - likely ambiguity on whether the bottom strip is a wanted asset or just decorative background
- Pass criteria:
  - center parchment panel stays intact
  - portrait frame stays intact
  - bottom strip is either preserved cleanly or easy to suppress using gallery filters
- Likely tuning:
  - use `Hide tiny fragments` to suppress scraps
  - use `Sort by usefulness` to push big useful panels upward

### Case 3: Busy Scenic Screenshot With Preserved UI
- File:
  - [Example UI 1.png](C:\Dev\Image generator\input\Example UI 1.png)
- Image type:
  - ornate top bar
  - large scenic cave background
  - bottom chat panel
  - icon strip
  - left portrait/side frame
- Goal:
  - remove scenery while keeping UI untouched
  - preserve top bar, bottom panel, icon strip, and left frame with original color
- Recommended setup:
  - `Extraction mode`: `Multi-point background erase`
  - `Preset`: `UI Balanced`
  - `Preserve original asset colors`: `On`
  - `Use second-pass edge refinement`: `On`
  - click 3-4 background sample points only in scenery
  - use:
    - `Protect Top Bar`
    - `Protect Bottom Bar`
    - `Protect Icon Strip`
  - draw keep boxes over the left frame if needed
  - brush keep over ornate borders
  - add red remove boxes over surviving scenic junk
- Expected outcome:
  - hardest high-value case
  - manual workflow should produce usable UI extraction, but this remains the biggest image-quality risk
- Pass criteria:
  - top bar remains readable and not washed out
  - bottom chat panel remains intact
  - icon strip remains intact
  - scenic fragments can be mostly suppressed from split gallery
  - likely-UI sort/filter makes the gallery manageable
- Known risk:
  - scenic remnants may still survive as false-positive panels
  - this case is the strongest candidate for future `UI frame mode` or foreground-vs-background segmentation

### Case 4: Dark-Mat Multi-Panel Sheet
- File:
  - [BananaProAI_com-2026322123439.png](C:\Dev\Image generator\input\BananaProAI_com-2026322123439.png)
- Image type:
  - two large parchment UI panels on dark background
  - not a scenic screenshot
- Goal:
  - separate the two main panels cleanly
  - avoid destructive dark-background keying
- Recommended setup:
  - prefer `Background removal` only if background is near-flat and clearly separable
  - otherwise use `Tight object crop for dark mats` for single-object extraction
  - if both panels are needed independently, run split workflow or script path after extraction
- Expected outcome:
  - medium-confidence success
  - better fit for crop/split than for aggressive color removal
- Pass criteria:
  - both parchment panels stay full-quality
  - dark backdrop is reduced without chewing panel edges
  - split output favors the two real panels over scraps
- Known risk:
  - dark background close to panel edge tones can still confuse removal logic

### Case 5: Brush-Only Ornate Detail Preservation
- File:
  - use any one of:
    - [Example UI 1.png](C:\Dev\Image generator\input\Example UI 1.png)
    - [UI2.1.png](C:\Dev\Image generator\input\UI2.1.png)
- Image type:
  - thin trim / ornate edge detail preserved primarily by brush marks
- Goal:
  - verify that brush-preserved details now surface in split exports
- Recommended setup:
  - run standard mode for the source
  - intentionally preserve a small ornate edge only with `Brush Keep Edges`
  - do not draw a keep box around that detail
- Expected outcome:
  - should now be supported by brush clustering logic
- Pass criteria:
  - brushed detail survives main result
  - brushed detail can appear as a split candidate
  - gallery labels should identify it as `Brushed UI detail`

## Live Run Checklist

For each case:
1. Load the file.
2. Confirm all manual state resets:
   - background samples
   - keep points
   - keep boxes
   - subtract boxes
   - brush marks
3. Apply the recommended setup.
4. Process once.
5. Record:
   - main preview quality
   - split gallery usefulness
   - whether likely-UI filtering helps
   - whether tiny-fragment filtering helps
   - whether usefulness sort surfaces the right assets
6. If needed, do one manual-control retry using:
   - keep boxes
   - brush keep
   - subtract boxes
7. Mark final status:
   - `Pass`
   - `Pass with tuning`
   - `Needs code improvement`

## Priority Order

Run in this order:
1. [UI2.1.png](C:\Dev\Image generator\input\UI2.1.png)
2. [BananaProAI_com-2026320191551.png](C:\Dev\Image generator\input\BananaProAI_com-2026320191551.png)
3. [Example UI 1.png](C:\Dev\Image generator\input\Example UI 1.png)
4. [BananaProAI_com-2026322123439.png](C:\Dev\Image generator\input\BananaProAI_com-2026322123439.png)
5. brush-only detail check on [Example UI 1.png](C:\Dev\Image generator\input\Example UI 1.png)

## Likely Follow-Up Work

If Case 3 still performs poorly, the next likely code upgrades are:
- dedicated `UI frame mode`
- true foreground `keep` vs background `remove` segmentation
- auto-detection for long top bars, bottom bars, and side rails
- stronger rejection of scenic edge-touching fragments before split export
