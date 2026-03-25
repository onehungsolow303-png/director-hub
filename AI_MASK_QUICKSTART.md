# AI Mask Quickstart

Use this when the browser cleanup leaves:
- white specks
- rough edges
- cut-off borders
- poor extraction on complex UI sheets

## Goal

Use a high-quality external AI matte to drive extraction while keeping:
- original UI pixels
- original canvas size
- original asset positions

## Best Mask Format

Use:
- grayscale PNG
- same width and height as the source image
- black = remove
- white = keep
- gray = soft edge / semi-transparent edge

Avoid:
- binary black/white masks when possible
- regenerated/repainted UI images

## In The App

1. Open [index.html](C:\Dev\Image generator\index.html)
2. Load your source image
3. Set:
   - `Extraction mode` = `AI auto mask (preview)`
4. Click:
   - `Load AI Mask PNG`
5. Load the grayscale mask
6. Set:
   - `Current mask input` = `Imported AI mask`
7. Set:
   - `Preview target` = `Show extracted result`
8. Click:
   - `Process Image`

## Best Starting Settings

Keep these on:
- `Preserve original asset colors in the main preview/export`
- `Clean background halos on semi-transparent edges`

Start with this off:
- `Use second-pass edge refinement`

Use:
- `Output format` = `Keep original layout (same size)`
- `Separated asset export size` = `Keep original canvas size and position`

## If You Need Cleanup

After importing the mask:
- use `Brush Keep Edges` for delicate trim
- use `Brush Remove Junk` for isolated specks
- use `Mask Overlay` to see edits more clearly
- use `Undo Last Brush Edit` if needed

## Downloads

Use:
- `Download Preview PNG` for the current main preview
- `Download Full Sheet PNG` for the original-size full layout
- `Download Mask PNG` for the active mask

## Important

The app is ready to use imported AI masks now.

The app does **not** yet run a local AI segmentation model by itself.

For the full version of this workflow, see:
- [AI_MASK_WORKFLOW_GUIDE.md](C:\Dev\Image generator\AI_MASK_WORKFLOW_GUIDE.md)
