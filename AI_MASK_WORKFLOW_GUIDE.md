# AI Mask Workflow Guide

This guide explains how to use a real AI-generated matte with the local cleanup app so you can get cleaner UI extraction than the browser-only heuristic path can provide.

Use this when:
- white specks remain on light-background UI sheets
- ornate borders still look rough after cleanup
- the heuristic extractor keeps cutting off corners or edge details
- you want an external high-precision matte to drive the final extraction

## Goal

Use an external AI mask as the extraction driver while still:
- preserving the original UI pixels
- keeping the original layout and asset positions
- allowing manual keep/remove cleanup inside the browser app

The recommended long-term architecture is:
1. AI segmentation model creates a grayscale matte
2. matte drives alpha extraction
3. original source pixels provide final color
4. manual keep/remove tools refine edge mistakes

## Recommended Mask Type

Best mask format:
- grayscale PNG
- same width and height as the source image
- black = remove
- white = keep
- gray = semi-transparent edge

Best quality target:
- continuous 8-bit alpha matte
- not a harsh binary cutout

Why:
- UI borders often contain soft contamination, glows, anti-aliased edges, and sub-pixel details
- a good grayscale matte preserves those transitions better than a hard black/white mask

## Model Guidance

Recommended style of model:
- Bria RMBG 2.x style foreground extraction
- IS-Net style detail mask
- other high-quality segmentation/matting models that output soft alpha

Important:
- prefer models that output a true matte or high-quality soft mask
- avoid workflows that regenerate the UI art itself

The app should preserve original UI pixels, not repaint them.

## Current App Support

The app already supports:
- importing an external mask PNG
- previewing that mask
- using the imported AI mask as the extraction source
- downloading the current mask
- preserving original layout for the main output
- exporting split assets either as:
  - tight crops
  - original-size transparent canvases with preserved positions

Relevant files:
- [index.html](C:\Dev\Image generator\index.html)
- [app.js](C:\Dev\Image generator\app.js)
- [styles.css](C:\Dev\Image generator\styles.css)

## How To Use An External AI Mask

1. Open [index.html](C:\Dev\Image generator\index.html) in the browser.
2. Load the source image.
3. Set:
   - `Extraction mode` = `AI auto mask (preview)`
4. Click:
   - `Load AI Mask PNG`
5. Choose a grayscale mask file that matches the source image dimensions exactly.
6. Set:
   - `Current mask input` = `Imported AI mask`
7. Choose:
   - `Preview target` = `Show mask preview`
   - to inspect the matte
8. Switch:
   - `Preview target` = `Show extracted result`
9. Click:
   - `Process Image`

At that point the app should use the imported mask to drive:
- the extracted preview
- the full-sheet output
- the split panels

## Best Settings With Imported AI Masks

Start with:
- `Preserve original asset colors in the main preview/export` = On
- `Clean background halos on semi-transparent edges` = On
- `Use second-pass edge refinement` = Off for initial AI-mask testing
- `Output format` = `Keep original layout (same size)`

Why:
- the imported matte should already be doing most of the heavy lifting
- it is best to inspect the imported matte with minimal extra processing first

Then, if needed:
- turn `Use second-pass edge refinement` on
- use manual brush keep/remove for small corrections

## Manual Cleanup On Top Of AI Masks

After loading the AI mask, you can still use:
- `Brush Keep Edges`
- `Brush Remove Junk`
- `Draw UI Keep Box(es)`
- `Draw Scenery Remove Box(es)`

Recommended use:
- use AI mask for the heavy extraction
- use manual tools only for cleanup and correction

Avoid using manual brush edits to redraw the whole mask from scratch.

## Common Failure Modes

### 1. Mask size mismatch

Problem:
- imported mask does not match the image size

Fix:
- export the matte at exactly the same resolution as the source image

### 2. White specks remain

Problem:
- the matte left tiny edge contamination or interior holes

Fix:
- improve the AI matte quality first
- then use `Brush Remove Junk` for isolated defects

### 3. Edges look cut off

Problem:
- matte is too binary or too aggressive

Fix:
- generate a softer grayscale matte
- prefer matting output over hard segmentation output

### 4. Asset looks washed out or repainted

Problem:
- extraction is relying on generated/rebuilt content instead of original pixels

Fix:
- keep original-pixel preservation enabled
- do not use image generation to reconstruct the UI asset itself

## What To Avoid

Avoid using image generation to recreate the extracted UI asset as the primary method.

Why:
- it can drift from the original art
- it can alter border thickness
- it can move or stylize details
- it breaks exact UI fidelity

Generation is appropriate for:
- filling scene holes after removal
- creating replacement backgrounds
- optional relighting/composite workflows

It is not the preferred method for exact asset extraction.

## Future Planned Upgrades

The app is now structurally ready for:
- local AI mask import
- future local segmentation model hookup
- future matting integration

Planned next steps:
1. allow imported AI mask + manual corrections to combine into one result
2. support a real `AI mask` inference path instead of placeholder-only UI
3. add stronger mask-preview diagnostics
4. add optional aggressive border-repair mode for light-background sheets

## Practical Recommendation

For the cleanest current workflow:
1. generate a high-quality grayscale matte externally
2. import it with `Load AI Mask PNG`
3. use `Current mask input = Imported AI mask`
4. keep the preview in original layout
5. only use brushes for final cleanup

That gives the best balance between:
- exact source fidelity
- clean cutout quality
- preserved asset positioning
