# Live Test Results Template

Use with:
- [LIVE_TEST_MATRIX.md](C:\Dev\Image generator\LIVE_TEST_MATRIX.md)
- [AUDIT_INSTRUCTION_SHEET.md](C:\Dev\Image generator\AUDIT_INSTRUCTION_SHEET.md)

App under test:
- [index.html](C:\Dev\Image generator\index.html)
- [app.js](C:\Dev\Image generator\app.js)
- [styles.css](C:\Dev\Image generator\styles.css)

Result status options:
- `Pass`
- `Pass with tuning`
- `Needs code improvement`

---

## Case 1: Clean White UI Sheet

File:
- [UI2.1.png](C:\Dev\Image generator\input\UI2.1.png)

Run setup:
- Extraction mode: `Background removal`
- Background tone: `Light background`
- Preset: `UI Hard`
- Preserve original asset colors: `On`
- Second-pass edge refinement: `Off` initially
- Output format: `Keep one result image`

Observed outcome:
- Main preview: Top bar, center panel, and portrait/frame panel preserved cleanly. Bottom stone bar still missing from the main result. White border contamination was still visible along some edges before the halo-cleanup fix.
- Split gallery: Useful assets surfaced correctly. Top bar, center panel, and portrait/frame panel exported as likely UI assets.
- Likely UI filter: Helpful. Kept the gallery focused on real UI assets.
- Tiny fragment filter: Not needed yet for this case.
- Usefulness sort: Helpful. Surfaced the strongest UI pieces first.

Pass criteria check:
- White fringe removed: No, still visible before halo-cleanup fix
- Top bar preserved: Yes
- Bottom bar preserved: No
- Small icons preserved: Partially; tiny icon buttons were not surfaced prominently in the shown result

Final status:
- `Needs re-test after code fix`

Notes:
- Tested with:
  - `UI Hard`
  - `Light background`
  - `Preserve original asset colors = On`
  - `Second-pass edge refinement = Off`
  - `Split Alpha Cutoff = 200`
  - `Minimum Split Size = 3000`
- Large asset preservation is good.
- The bottom bar remains the main gap for this case.

Follow-up action:
- Re-test after the preserve-color halo cleanup change and then re-evaluate bottom-strip preservation.

---

## Case 2: White UI Sheet With Heavy Bottom Texture

File:
- [BananaProAI_com-2026320191551.png](C:\Dev\Image generator\input\BananaProAI_com-2026320191551.png)

Run setup:
- Extraction mode: `Background removal`
- Background tone: `Light background`
- Preset: `UI Balanced`
- Preserve original asset colors: `On`
- Second-pass edge refinement: `Off` initially
- Output format: `Split panel result`

Observed outcome:
- Main preview: Top bar, center panel, and portrait frame preserved. Bottom rock strip was removed from the main result. White edge contamination was still visible along some preserved borders before the halo-cleanup fix.
- Split gallery: Surfaced three useful UI assets cleanly. No obvious junk fragments in the shown result.
- Did the bottom strip feel like wanted UI or junk: In this run it behaved more like removable decorative background than required UI.

Pass criteria check:
- Center parchment panel preserved: Yes
- Portrait frame preserved: Yes
- Bottom strip handled acceptably: Yes for a cleanup-focused interpretation

Final status:
- `Needs re-test after code fix`

Notes:
- This case behaved better than Case 1.
- The heavy bottom texture did not pollute the split gallery.
- The app made a reasonable choice by preserving the key UI assets and dropping the decorative strip from the main result.

Follow-up action:
- Re-test after the preserve-color halo cleanup change to confirm the white edge issue is actually resolved.

---

## Case 3: Busy Scenic Screenshot With Preserved UI

File:
- [Example UI 1.png](C:\Dev\Image generator\input\Example UI 1.png)

Run setup:
- Extraction mode: `Multi-point background erase`
- Preset: `UI Balanced`
- Preserve original asset colors: `On`
- Second-pass edge refinement: `On`
- Background sample count: `3-4`
- Used Protect Top Bar:
- Used Protect Bottom Bar:
- Used Protect Icon Strip:
- Used keep boxes:
- Used brush keep:
- Used subtract boxes:

Observed outcome:
- Main preview:
- Split gallery:
- Likely UI filter:
- Tiny fragment filter:
- Usefulness sort:

Pass criteria check:
- Top bar readable and intact:
- Bottom panel preserved:
- Icon strip preserved:
- Left frame preserved:
- Scenic junk mostly suppressed:

Final status:
- ``

Notes:
- 

Follow-up action:
- 

---

## Case 4: Dark-Mat Multi-Panel Sheet

File:
- [BananaProAI_com-2026322123439.png](C:\Dev\Image generator\input\BananaProAI_com-2026322123439.png)

Run setup:
- Extraction mode: `Tight object crop for dark mats` or careful `Background removal`
- Background tone: `Dark background`
- Preset: `UI Balanced`
- Preserve original asset colors: `On`
- Second-pass edge refinement: `Off` initially
- Output format: `Keep one result image`

Observed outcome:
- Main preview:
- Split gallery:
- Two main panels surfaced cleanly:

Pass criteria check:
- Panel 1 quality preserved:
- Panel 2 quality preserved:
- Dark backdrop handled acceptably:

Final status:
- ``

Notes:
- 

Follow-up action:
- 

---

## Case 5: Brush-Only Ornate Detail Preservation

File:
- [Example UI 1.png](C:\Dev\Image generator\input\Example UI 1.png)

Run setup:
- Extraction mode: `Multi-point background erase` or matching source mode
- Preserve original asset colors: `On`
- Second-pass edge refinement: `On`
- Detail preserved only with brush:

Observed outcome:
- Main preview:
- Split gallery:
- Did brushed detail appear as a panel:
- Was it labeled `Brushed UI detail`:

Pass criteria check:
- Brushed detail survived main result:
- Brushed detail exported as split candidate:

Final status:
- ``

Notes:
- 

Follow-up action:
- 

---

## Summary

Overall result:
- 

Strongest success case:
- 

Weakest case:
- 

Most useful controls:
- 

Most confusing controls:
- 

Next code changes to prioritize:
- 
