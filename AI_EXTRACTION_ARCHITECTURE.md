# AI Extraction Architecture

## Goal

Upgrade the local cleanup app from heuristic background removal into an AI-assisted extraction workflow that:

- preserves original UI pixels whenever possible
- generates a continuous alpha matte, not a hard binary cutout
- suppresses white/green/background spill on edges
- keeps full-sheet layout exports for position-sensitive UI work
- still allows manual correction after the AI mask is generated

## Core principle

Do **not** use image generation to recreate the UI asset itself as the primary extraction path.

Preferred pipeline:

1. AI segmentation model creates a foreground/background mask
2. Alpha matting refines that mask into an 8-bit alpha matte
3. Spill suppression / defringe removes background color contamination
4. Original source pixels are composited through the matte
5. Manual keep/remove tools refine the result where needed

This keeps the extracted UI faithful to the original artwork.

## Recommended extraction stack

### 1. Primary foreground segmentation

Use a high-precision model such as:

- BRIA RMBG 2.0 or current BRIA-quality equivalent
- IS-Net / DIS-family segmentation
- another UI/object-capable segmentation model that can run locally

Requirements:

- must support local inference
- must output a soft foreground confidence map or mask logits
- should be suitable for small detailed structures, thin bars, ornate corners, and subtle semi-transparent edges

### 2. Alpha matting refinement

Segmentation alone is not enough.

Add a matting/refinement stage that:

- converts the coarse/soft mask into a continuous 8-bit alpha matte
- preserves sub-pixel edge details
- avoids crunchy hard edges
- handles soft glow, anti-aliased borders, light bloom, and faint transparency

This is the right solution for the user’s “pixel-perfect extraction” requirement.

### 3. Spill suppression / defringe

After matting, run edge decontamination using:

- sampled background color
- local interior edge color
- optional model confidence

This stage should remove:

- white fringing from light-background sheets
- green/scene tint on extracted borders
- bright random edge specks

### 4. Manual refinement layer

Keep the current editing affordances and make them operate on the mask layer:

- background sample points
- keep points
- keep boxes
- subtract boxes
- brush keep
- brush remove
- undo brush edit
- mask overlay opacity

This becomes the correction layer on top of AI, not the primary extraction engine.

## Product modes to support

### A. Exact UI extraction

Purpose:

- remove scenery/background from a UI sheet
- preserve original UI colors and position

Output:

- full-sheet cleaned PNG at original dimensions
- optional separated assets
- optional separated assets on full original canvas for position preservation

### B. UI scene removal / cleanup plate

Purpose:

- remove a UI element from a scene
- fill the hole naturally

Method:

- segmentation / mask identifies removed region
- generative inpainting fills the scene gap using surrounding art style

This is a separate stage and should not overwrite the original extracted UI asset.

### C. Re-composite into new background

Purpose:

- place extracted asset/object into a different generated scene

Method:

- preserve extracted foreground
- optionally generate new stage/background
- optionally run relighting / harmonization so the foreground matches the new environment

This should be treated as a compositing workflow, not as the default extraction path.

## UI requirements for AI-assisted mode

Add a future `AI Auto Mask` mode with:

- `Auto Mask Source`
- `Mask Confidence`
- `Matte Refinement`
- `Spill Suppression`
- `Relight for New Scene` (only for re-composite mode)
- `Scene Fill / Inpaint Removed Area` (only for scene-removal mode)

Manual tools should remain visible after AI processing so the user can correct the mask.

## Separation of concerns

### Extraction mode

Should focus on:

- accurate alpha
- preserving original source pixels
- layout-safe output

### Generation / relighting / inpainting mode

Should focus on:

- scene cleanup
- environment replacement
- lighting harmonization

These should be separate workflows in the UX, even if they share some internal mask infrastructure.

## Implementation recommendation

### Phase 1

- keep current browser editor
- formalize editable mask layer
- store AI mask + manual overrides separately

### Phase 2

- add local inference hook for a segmentation model
- feed returned mask into current preview pipeline

### Phase 3

- add matting refinement
- add stronger spill suppression

### Phase 4

- add optional inpainting workflow
- add optional relighting/compositing workflow

## Current app limitations

The current browser-only heuristic pipeline is improving, but it is still limited because:

- it does not use true semantic segmentation
- it does not use dedicated alpha matting
- it relies too much on manual brush corrections for hard cases
- ornate UI over scenic backgrounds is still a known hard case

## Success criteria

A future AI-assisted build is successful when:

- extracted UI borders no longer show obvious white/scene specks
- thin bars and ornate corners survive without heavy manual brushing
- output keeps original sheet size and element positions
- separated asset exports can preserve original positions when desired
- manual correction is still available, but no longer carries the whole extraction burden
