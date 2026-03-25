const stylePresets = {
  fantasy: {
    positive: "game ui kit, fantasy RPG style, {assetType}, {material}, ornate craftsmanship, 2d game art, centered composition, isolated on white background, sharp edges, highly detailed, professional asset sheet",
    negative: "blurry, text, watermark, realistic photo, character, overlapping parts, background clutter, low resolution, messy silhouette"
  },
  scifi: {
    positive: "futuristic game ui, {assetType}, holographic panels, {material}, neon accents, clean geometry, minimalist hud design, centered, isolated on black background, crisp lines, studio quality, high detail",
    negative: "blurry, organic mess, fantasy ornament, text, watermark, low contrast, noisy background, low resolution, distorted proportions"
  },
  pixel: {
    positive: "pixel art game ui asset, {assetType}, {material}, centered, isolated background, limited palette, crisp silhouette, readable shape language, production-ready sprite, sharp edges, game asset sheet",
    negative: "blur, anti-aliased smudge, painterly, photographic, text, watermark, extra objects, fuzzy outline, soft lighting, low resolution"
  },
  clean: {
    positive: "mobile game ui asset, {assetType}, {material}, polished casual style, soft readable shapes, centered, isolated on white background, bright color separation, clean edges, highly detailed, professional",
    negative: "gritty realism, muddy colors, text, watermark, cluttered composition, overlapping, low resolution, background scene, shadows"
  }
};

const checkpoints = {
  juggernautXL: { name: "Juggernaut XL", sampler: "dpmpp_2m_sde", scheduler: "karras", steps: 30, cfg: 6.5, width: 1024, height: 1024, denoise: 1 },
  flux: { name: "Flux", sampler: "euler", scheduler: "simple", steps: 24, cfg: 3.5, width: 1024, height: 1024, denoise: 1 },
  sdxl: { name: "SDXL", sampler: "dpmpp_2m", scheduler: "karras", steps: 28, cfg: 7, width: 1024, height: 1024, denoise: 1 }
};

const removers = {
  essentials: { processNode: "TransparencyBackgroundRemover", nodes: ["ComfyUI Essentials", "TransparencyBackgroundRemover", "Load Image", "Save Image"], tips: ["Set the node to keep alpha transparency.", "If you are doing sprites, enable the sharpest edge mode available."] },
  bria: { processNode: "BRIA RMBG Processor", nodes: ["ComfyUI-BRIA_AI-RMBG", "Load Image", "BRIA RMBG Model Loader", "BRIA RMBG Processor", "Save Image"], tips: ["Use RMBG-1.4 or 2.0 depending on what you installed.", "Save as PNG so the transparent alpha channel survives."] },
  was: { processNode: "Image Rembg", nodes: ["WAS Node Suite", "Load Image", "Image Rembg", "Save Image"], tips: ["Start with isnet-general-use for regular assets.", "Switch to anime or u2net models when outlines need different bias."] },
  ben2: { processNode: "BEN2 Background Removal", nodes: ["BEN2 custom nodes", "Load Image", "BEN2 Background Removal", "Save Image"], tips: ["BEN2 is a strong choice when hair, cloth, or soft edges matter.", "Check output masks for tiny holes before batch exporting."] }
};

const bgPresets = {
  "ui-balanced": { threshold: 18, softness: 24, alphaFloor: 8, alphaCeiling: 245, componentAlpha: 220, componentPixels: 5000, componentPad: 2, objectPad: 12, cropTransparent: false, decontaminate: true, tone: "dark" },
  "ui-soft": { threshold: 14, softness: 34, alphaFloor: 4, alphaCeiling: 245, componentAlpha: 200, componentPixels: 5000, componentPad: 4, objectPad: 16, cropTransparent: false, decontaminate: true, tone: "dark" },
  "ui-hard": { threshold: 24, softness: 16, alphaFloor: 12, alphaCeiling: 238, componentAlpha: 228, componentPixels: 7000, componentPad: 2, objectPad: 10, cropTransparent: false, decontaminate: true, tone: "dark" }
};

const form = document.querySelector("#workflowForm");
const installList = document.querySelector("#installList");
const stepsList = document.querySelector("#stepsList");
const positivePrompt = document.querySelector("#positivePrompt");
const negativePrompt = document.querySelector("#negativePrompt");
const workflowJson = document.querySelector("#workflowJson");
const copyJsonButton = document.querySelector("#copyJsonButton");
const downloadJsonButton = document.querySelector("#downloadJsonButton");
const loadDemoButton = document.querySelector("#loadDemoButton");
const copyChecklistButton = document.querySelector("#copyChecklistButton");

const bgInputFile = document.querySelector("#bgInputFile");
const bgMode = document.querySelector("#bgMode");
const bgPreset = document.querySelector("#bgPreset");
const bgTone = document.querySelector("#bgTone");
const bgLayout = document.querySelector("#bgLayout");
const bgMaskSource = document.querySelector("#bgMaskSource");
const bgPreviewTarget = document.querySelector("#bgPreviewTarget");
const bgPanelLayout = document.querySelector("#bgPanelLayout");
const bgEditorView = document.querySelector("#bgEditorView");
const bgBrushSize = document.querySelector("#bgBrushSize");
const bgMaskOverlay = document.querySelector("#bgMaskOverlay");
const bgAiSource = document.querySelector("#bgAiSource");
const bgAiConfidence = document.querySelector("#bgAiConfidence");
const bgAiMatte = document.querySelector("#bgAiMatte");
const bgAiSpill = document.querySelector("#bgAiSpill");
const bgAiRelight = document.querySelector("#bgAiRelight");
const bgAiInpaint = document.querySelector("#bgAiInpaint");
const bgAiInvertMask = document.querySelector("#bgAiInvertMask");
const bgAiMaskExpand = document.querySelector("#bgAiMaskExpand");
const bgAiMaskFeather = document.querySelector("#bgAiMaskFeather");
const bgAiCombineManual = document.querySelector("#bgAiCombineManual");
const bgThreshold = document.querySelector("#bgThreshold");
const bgSoftness = document.querySelector("#bgSoftness");
const bgAlphaFloor = document.querySelector("#bgAlphaFloor");
const bgAlphaCeiling = document.querySelector("#bgAlphaCeiling");
const bgComponentAlpha = document.querySelector("#bgComponentAlpha");
const bgComponentPixels = document.querySelector("#bgComponentPixels");
const bgComponentPad = document.querySelector("#bgComponentPad");
const bgObjectPad = document.querySelector("#bgObjectPad");
const bgCropTransparent = document.querySelector("#bgCropTransparent");
const bgDecontaminate = document.querySelector("#bgDecontaminate");
const bgEdgeCleanupStrength = document.querySelector("#bgEdgeCleanupStrength");
const bgStrongBorderRepair = document.querySelector("#bgStrongBorderRepair");
const bgPreserveColor = document.querySelector("#bgPreserveColor");
const bgSecondPass = document.querySelector("#bgSecondPass");
const processBgButton = document.querySelector("#processBgButton");
const cancelBgButton = document.querySelector("#cancelBgButton");
const sampleBgButton = document.querySelector("#sampleBgButton");
const sampleKeepButton = document.querySelector("#sampleKeepButton");
const sampleKeepBoxButton = document.querySelector("#sampleKeepBoxButton");
const sampleSubtractBoxButton = document.querySelector("#sampleSubtractBoxButton");
const eraseKeepBoxButton = document.querySelector("#eraseKeepBoxButton");
const autoDetectUiButton = document.querySelector("#autoDetectUiButton");
const clearKeepBoxesButton = document.querySelector("#clearKeepBoxesButton");
const clearSubtractBoxesButton = document.querySelector("#clearSubtractBoxesButton");
const clearBrushKeepButton = document.querySelector("#clearBrushKeepButton");
const clearBrushRemoveButton = document.querySelector("#clearBrushRemoveButton");
const protectTopBarButton = document.querySelector("#protectTopBarButton");
const protectBottomBarButton = document.querySelector("#protectBottomBarButton");
const protectIconStripButton = document.querySelector("#protectIconStripButton");
const brushKeepButton = document.querySelector("#brushKeepButton");
const brushRemoveButton = document.querySelector("#brushRemoveButton");
const downloadBgButton = document.querySelector("#downloadBgButton");
const downloadLayoutButton = document.querySelector("#downloadLayoutButton");
const downloadMaskButton = document.querySelector("#downloadMaskButton");
const aiMaskInput = document.querySelector("#aiMaskInput");
const downloadPanelsButton = document.querySelector("#downloadPanelsButton");
const bgStatus = document.querySelector("#bgStatus");
const maskStatusBlock = document.querySelector("#maskStatusBlock");
const bgSampleMeta = document.querySelector("#bgSampleMeta");
const keepSampleMeta = document.querySelector("#keepSampleMeta");
const keepBoxMeta = document.querySelector("#keepBoxMeta");
const subtractBoxMeta = document.querySelector("#subtractBoxMeta");
const brushKeepMeta = document.querySelector("#brushKeepMeta");
const brushRemoveMeta = document.querySelector("#brushRemoveMeta");
const originalCanvas = document.querySelector("#originalCanvas");
const resultCanvas = document.querySelector("#resultCanvas");
const resultPreviewWrap = document.querySelector("#resultPreviewWrap");
const resultBusy = document.querySelector("#resultBusy");
const originalMeta = document.querySelector("#originalMeta");
const resultMeta = document.querySelector("#resultMeta");
const splitLinks = document.querySelector("#splitLinks");
const showLikelyUiButton = document.querySelector("#showLikelyUiButton");
const showAllPanelsButton = document.querySelector("#showAllPanelsButton");
const splitMinPixels = document.querySelector("#splitMinPixels");
const splitMinPixelsValue = document.querySelector("#splitMinPixelsValue");
const splitSortMode = document.querySelector("#splitSortMode");
const previewStack = document.querySelector("#previewStack");
const undoBrushEditButton = document.querySelector("#undoBrushEditButton");

const thresholdValue = document.querySelector("#thresholdValue");
const softnessValue = document.querySelector("#softnessValue");
const alphaFloorValue = document.querySelector("#alphaFloorValue");
const alphaCeilingValue = document.querySelector("#alphaCeilingValue");
const edgeCleanupValue = document.querySelector("#edgeCleanupValue");
const componentAlphaValue = document.querySelector("#componentAlphaValue");
const componentPixelsValue = document.querySelector("#componentPixelsValue");
const componentPadValue = document.querySelector("#componentPadValue");
const objectPadValue = document.querySelector("#objectPadValue");
const brushSizeValue = document.querySelector("#brushSizeValue");
const maskOverlayValue = document.querySelector("#maskOverlayValue");
const aiConfidenceValue = document.querySelector("#aiConfidenceValue");
const aiMatteValue = document.querySelector("#aiMatteValue");
const aiSpillValue = document.querySelector("#aiSpillValue");
const aiMaskExpandValue = document.querySelector("#aiMaskExpandValue");
const aiMaskFeatherValue = document.querySelector("#aiMaskFeatherValue");

let currentPayload = null;
let loadedImage = null;
let loadedFileName = "asset";
let processedCanvas = null;
let processedPanels = [];
let processedMaskCanvas = null;
let processedMaskAlpha = null;
let manualMaskCanvas = null;
let aiMaskCanvas = null;
let importedAiMaskAlpha = null;
let manualBackgroundColor = null;
let manualBackgroundSamples = [];
let manualKeepSamples = [];
let manualKeepBoxes = [];
let manualSubtractBoxes = [];
let manualKeepBrushPoints = [];
let manualRemoveBrushPoints = [];
let samplingHandler = null;
let samplingMoveHandler = null;
let samplingUpHandler = null;
let samplingModeActive = false;
let samplingTarget = "background";
let cancelProcessingRequested = false;
let isProcessing = false;
let selectedPanelIndex = -1;
let activeKeepBox = null;
let splitPanelFilter = "likely";
let splitPanelMinPixels = 0;
let splitPanelSortMode = "useful";
let processedLayoutCanvas = null;
let splitPanelLayoutMode = "crop";
let brushEditHistory = [];
let activeBrushStroke = null;

const MAX_KEEP_BOXES = 24;
const MAX_KEEP_POINTS = 12;
const MAX_BG_SAMPLES = 6;
const DEFAULT_BRUSH_RADIUS = 22;

function formStateToConfig() {
  const data = new FormData(form);
  return {
    workflowType: data.get("workflowType"),
    style: data.get("style"),
    checkpoint: data.get("checkpoint"),
    remover: data.get("remover"),
    assetType: String(data.get("assetType") || "").trim() || "game ui asset",
    material: String(data.get("material") || "").trim() || "clean material definition",
    batchMode: data.get("batchMode") === "on",
    pixelEdges: data.get("pixelEdges") === "on"
  };
}

function buildPrompts(config) {
  const preset = stylePresets[config.style];
  const checkpoint = checkpoints[config.checkpoint];
  const positiveBase = preset.positive.replace("{assetType}", config.assetType).replace("{material}", config.material);
  const modelHint = checkpoint.name === "Flux" ? "Use concise prompt weighting and avoid overloading commas." : "Use standard CLIP text encoding with asset-first wording.";
  const edgeHint = config.pixelEdges ? " pixel-perfect outline, no fringe, hard alpha edge," : "";
  return { positive: `${positiveBase},${edgeHint} ${modelHint}`, negative: preset.negative };
}

function buildInstallList(config) {
  const remover = removers[config.remover];
  const checkpoint = checkpoints[config.checkpoint];
  const items = ["ComfyUI Manager", `${checkpoint.name} checkpoint`, ...remover.nodes];
  if (config.workflowType !== "background") items.splice(2, 0, "Checkpoint Loader Simple", "CLIP Text Encode", "KSampler", "VAE Decode");
  if (config.batchMode) items.push("Load Images From Path");
  return [...new Set(items)];
}

function buildSteps(config) {
  const remover = removers[config.remover];
  const steps = [];
  if (config.workflowType === "background") {
    steps.push("Add `Load Image`. If you want folder processing, use `Load Images From Path` instead.");
    steps.push(`Connect the image output into \`${remover.processNode}\`.`);
    steps.push("Set the output file type to PNG so transparency stays intact.");
  }
  if (config.workflowType === "ui") {
    steps.push("Load your checkpoint with `Checkpoint Loader Simple`.");
    steps.push("Paste the positive and negative prompts into separate `CLIP Text Encode` nodes.");
    steps.push("Connect those text encoders into `KSampler`, then decode with `VAE Decode`.");
    steps.push("Save the result or keep iterating until the shape language matches your game.");
  }
  if (config.workflowType === "combined") {
    steps.push("Load your checkpoint with `Checkpoint Loader Simple`.");
    steps.push("Use one `CLIP Text Encode` for the positive prompt and one for the negative prompt.");
    steps.push("Run the image through `KSampler`, then `VAE Decode`.");
    steps.push(`Feed the generated image into \`${remover.processNode}\` for alpha cleanup.`);
    steps.push("Save the final image as PNG for engine-friendly transparency.");
  }
  if (config.pixelEdges) steps.push("Turn on the sharpest edge or pixel mode in the remover node to avoid ugly halo pixels.");
  if (config.batchMode) steps.push("Point `Load Images From Path` at your raw asset folder so you can process a whole batch in one run.");
  if (config.checkpoint === "flux") steps.push("Keep Flux prompts tighter than SDXL prompts so the model stays obedient.");
  steps.push(...remover.tips);
  return steps;
}

function buildWorkflowTemplate(config, prompts) {
  const checkpoint = checkpoints[config.checkpoint];
  const remover = removers[config.remover];
  const imageInputNode = config.batchMode ? "Load Images From Path" : "LoadImage";
  const workflow = {};
  if (config.workflowType === "background") {
    workflow["1"] = { class_type: imageInputNode, inputs: config.batchMode ? { path: "C:/replace/with/your/source/folder" } : { image: "replace-with-your-source-image.png" } };
    workflow["2"] = { class_type: remover.processNode, inputs: { image: ["1", 0], edge_mode: config.pixelEdges ? "PIXEL_ART" : "STANDARD" } };
    workflow["3"] = { class_type: "SaveImage", inputs: { filename_prefix: "bg_removed_asset", images: ["2", 0] } };
    return workflow;
  }
  workflow["1"] = { class_type: "CheckpointLoaderSimple", inputs: { ckpt_name: `${checkpoint.name}.safetensors` } };
  workflow["2"] = { class_type: "CLIPTextEncode", inputs: { text: prompts.positive, clip: ["1", 1] } };
  workflow["3"] = { class_type: "CLIPTextEncode", inputs: { text: prompts.negative, clip: ["1", 1] } };
  workflow["4"] = { class_type: "EmptyLatentImage", inputs: { width: checkpoint.width, height: checkpoint.height, batch_size: 1 } };
  workflow["5"] = { class_type: "KSampler", inputs: { seed: 123456789, steps: checkpoint.steps, cfg: checkpoint.cfg, sampler_name: checkpoint.sampler, scheduler: checkpoint.scheduler, denoise: checkpoint.denoise, model: ["1", 0], positive: ["2", 0], negative: ["3", 0], latent_image: ["4", 0] } };
  workflow["6"] = { class_type: "VAEDecode", inputs: { samples: ["5", 0], vae: ["1", 2] } };
  if (config.workflowType === "ui") {
    workflow["7"] = { class_type: "SaveImage", inputs: { filename_prefix: "ui_asset", images: ["6", 0] } };
    return workflow;
  }
  workflow["7"] = { class_type: remover.processNode, inputs: { image: ["6", 0], edge_mode: config.pixelEdges ? "PIXEL_ART" : "STANDARD" } };
  workflow["8"] = { class_type: "SaveImage", inputs: { filename_prefix: "transparent_ui_asset", images: ["7", 0] } };
  return workflow;
}

function renderChecklist(items) { installList.innerHTML = items.map((item) => `<li>${item}</li>`).join(""); }
function renderSteps(steps) { stepsList.innerHTML = steps.map((step) => `<li>${step}</li>`).join(""); }
function refreshOutput(config) {
  const prompts = buildPrompts(config);
  const installItems = buildInstallList(config);
  const steps = buildSteps(config);
  const workflow = buildWorkflowTemplate(config, prompts);
  currentPayload = { config, prompts, installItems, steps, workflow };
  renderChecklist(installItems);
  renderSteps(steps);
  positivePrompt.textContent = prompts.positive;
  negativePrompt.textContent = prompts.negative;
  workflowJson.textContent = JSON.stringify(workflow, null, 2);
}

function setProcessingState(active, message = "Processing image...") {
  isProcessing = active;
  if (bgInputFile) bgInputFile.disabled = active;
  if (bgMode) bgMode.disabled = active;
  if (bgLayout) bgLayout.disabled = active;
  if (bgTone) bgTone.disabled = active;
  if (resultBusy) {
    resultBusy.textContent = message;
    resultBusy.classList.toggle("is-active", active);
  }
  if (resultPreviewWrap) resultPreviewWrap.setAttribute("aria-busy", active ? "true" : "false");
  updateActionStates();
}

function updateSampleMeta() {
  if (bgSampleMeta) bgSampleMeta.textContent = `Background samples: ${manualBackgroundSamples.length}`;
  if (keepSampleMeta) keepSampleMeta.textContent = `UI keep points: ${manualKeepSamples.length}`;
  if (keepBoxMeta) keepBoxMeta.textContent = `UI keep boxes: ${manualKeepBoxes.length}`;
  if (subtractBoxMeta) subtractBoxMeta.textContent = `Scenery remove boxes: ${manualSubtractBoxes.length}`;
  if (brushKeepMeta) brushKeepMeta.textContent = `Brush keep marks: ${manualKeepBrushPoints.length}`;
  if (brushRemoveMeta) brushRemoveMeta.textContent = `Brush remove marks: ${manualRemoveBrushPoints.length}`;
}

function updateMaskStatusBlock() {
  if (!maskStatusBlock) return;
  const source = bgMaskSource ? bgMaskSource.value : "processed";
  const sourceLabel = source === "manual"
    ? "Manual corrections mask"
    : source === "ai"
      ? "Imported AI mask"
      : "Heuristic processed mask";
  const matteLabel = bgMode && bgMode.value === "ai"
    ? importedAiMaskAlpha
      ? [
          "Imported mask refined in-app",
          bgAiInvertMask?.checked ? "invert" : null,
          Number(bgAiMaskExpand?.value || 0) !== 0 ? `expand ${bgAiMaskExpand.value}` : null,
          Number(bgAiMaskFeather?.value || 0) > 0 ? `feather ${bgAiMaskFeather.value}` : null,
          bgAiCombineManual?.checked ? "manual combine" : null
        ].filter(Boolean).join(" | ")
      : "AI matte settings staged, heuristic preview active"
    : bgDecontaminate && bgDecontaminate.checked
      ? "Heuristic edge cleanup active"
      : "No edge cleanup";
  const aiLabel = aiMaskCanvas
    ? "AI hook: External AI mask loaded"
    : source === "ai"
      ? "AI hook: Placeholder only, no local model connected yet"
      : "AI hook: Not connected yet";

  maskStatusBlock.innerHTML = `<strong>Mask pipeline</strong><br>Source: ${sourceLabel}<br>Matte refinement: ${matteLabel}<br>${aiLabel}`;
}

function getIdleGuidanceMessage() {
  if (!loadedImage) return "Upload an image to start.";
  if (bgMode.value === "ai") {
    return `AI auto mask preview mode is ready. Future model family: ${bgAiSource ? bgAiSource.value : "bria"}. Use 'Load AI Mask PNG' plus 'Current mask input = Imported AI mask' if you already have an external matte. The local model hook is not wired yet, so this section currently stages future AI settings. ${getImageWorkHint(loadedImage.width, loadedImage.height)}`;
  }
  if (bgMode.value === "multi" && manualBackgroundSamples.length === 0) {
    return "Multi-point mode: click 'Sample Background Point(s)' and add 3-4 empty background clicks.";
  }
  if (bgMode.value === "multi" && !manualKeepSamples.length && !manualKeepBoxes.length && !manualKeepBrushPoints.length) {
    return `Ready to process. Add UI keep points, keep boxes, or brush marks if you want to protect bars, frames, or icons. ${getImageWorkHint(loadedImage.width, loadedImage.height)}`;
  }
  return `Ready to process. ${getImageWorkHint(loadedImage.width, loadedImage.height)}`;
}

function updateActionStates() {
  const hasImage = Boolean(loadedImage);
  const hasResult = Boolean(processedCanvas);
  const hasPanels = processedPanels.length > 0;
  const samplingAllowed = hasImage && !isProcessing;
  const needsSamples = bgMode && bgMode.value === "multi" && manualBackgroundSamples.length === 0;
  const needsImportedAiMask = bgMode && bgMode.value === "ai" && bgMaskSource && bgMaskSource.value === "ai" && !importedAiMaskAlpha;
  const canProcess = hasImage && !needsSamples && !needsImportedAiMask && !isProcessing;

  if (processBgButton) {
    processBgButton.disabled = !canProcess;
    processBgButton.title = !hasImage
      ? "Upload an image first."
      : needsSamples
        ? "Add 3-4 background sample clicks first."
        : needsImportedAiMask
          ? "Load an AI mask PNG first, or change Current mask input away from Imported AI mask."
        : "";
  }
  if (bgMaskSource) {
    const hasAnyMask = Boolean(processedMaskCanvas || manualMaskCanvas || aiMaskCanvas);
    bgMaskSource.disabled = isProcessing || !hasAnyMask;
    bgMaskSource.title = !hasAnyMask ? "Process an image first so mask sources exist." : "";
  }
  if (bgPreviewTarget) {
    bgPreviewTarget.disabled = isProcessing || !(processedLayoutCanvas || processedMaskCanvas || manualMaskCanvas || aiMaskCanvas);
    bgPreviewTarget.title = !(processedLayoutCanvas || processedMaskCanvas || manualMaskCanvas || aiMaskCanvas)
      ? "Process an image first."
      : "";
  }
  [bgAiSource, bgAiConfidence, bgAiMatte, bgAiSpill, bgAiRelight, bgAiInpaint].forEach((control) => {
    if (!control) return;
    control.disabled = isProcessing || bgMode.value !== "ai";
  });
  [bgAiInvertMask, bgAiMaskExpand, bgAiMaskFeather, bgAiCombineManual].forEach((control) => {
    if (!control) return;
    control.disabled = isProcessing || bgMode.value !== "ai";
  });
  if (cancelBgButton) cancelBgButton.disabled = !isProcessing;
  if (sampleBgButton) {
    sampleBgButton.disabled = !samplingAllowed;
    sampleBgButton.title = !hasImage ? "Upload an image first." : "";
  }
  if (sampleKeepButton) {
    sampleKeepButton.disabled = !samplingAllowed;
    sampleKeepButton.title = !hasImage ? "Upload an image first." : "";
  }
  if (sampleKeepBoxButton) {
    sampleKeepBoxButton.disabled = !samplingAllowed;
    sampleKeepBoxButton.title = !hasImage ? "Upload an image first." : "";
  }
  if (sampleSubtractBoxButton) {
    sampleSubtractBoxButton.disabled = !samplingAllowed;
    sampleSubtractBoxButton.title = !hasImage ? "Upload an image first." : "";
  }
  if (eraseKeepBoxButton) {
    eraseKeepBoxButton.disabled = !samplingAllowed || manualKeepBoxes.length === 0;
    eraseKeepBoxButton.title = manualKeepBoxes.length === 0 ? "No UI keep boxes to erase." : "";
  }
  if (autoDetectUiButton) {
    autoDetectUiButton.disabled = !samplingAllowed;
    autoDetectUiButton.title = !hasImage ? "Upload an image first." : "";
  }
  [protectTopBarButton, protectBottomBarButton, protectIconStripButton, brushKeepButton, brushRemoveButton].forEach((button) => {
    if (!button) return;
    button.disabled = !samplingAllowed;
    button.title = !hasImage ? "Upload an image first." : "";
  });
  if (clearKeepBoxesButton) {
    clearKeepBoxesButton.disabled = isProcessing || manualKeepBoxes.length === 0;
    clearKeepBoxesButton.title = manualKeepBoxes.length === 0 ? "No UI keep boxes to clear." : "";
  }
  if (clearSubtractBoxesButton) {
    clearSubtractBoxesButton.disabled = isProcessing || manualSubtractBoxes.length === 0;
    clearSubtractBoxesButton.title = manualSubtractBoxes.length === 0 ? "No scenery remove boxes to clear." : "";
  }
  if (clearBrushKeepButton) {
    clearBrushKeepButton.disabled = isProcessing || manualKeepBrushPoints.length === 0;
    clearBrushKeepButton.title = manualKeepBrushPoints.length === 0 ? "No brush keep marks to clear." : "";
  }
  if (clearBrushRemoveButton) {
    clearBrushRemoveButton.disabled = isProcessing || manualRemoveBrushPoints.length === 0;
    clearBrushRemoveButton.title = manualRemoveBrushPoints.length === 0 ? "No brush remove marks to clear." : "";
  }
  if (undoBrushEditButton) {
    undoBrushEditButton.disabled = isProcessing || brushEditHistory.length === 0;
    undoBrushEditButton.title = brushEditHistory.length === 0 ? "No brush edits to undo." : "";
  }
  if (downloadBgButton) {
    downloadBgButton.disabled = isProcessing || !hasResult;
    downloadBgButton.title = !hasResult ? "Process an image first." : "";
  }
  if (downloadLayoutButton) {
    downloadLayoutButton.disabled = isProcessing || !processedLayoutCanvas;
    downloadLayoutButton.title = !processedLayoutCanvas ? "Process an image first so the full-sheet result exists." : "";
  }
  if (downloadMaskButton) {
    const hasDownloadableMask = Boolean(processedMaskCanvas || manualMaskCanvas || aiMaskCanvas);
    downloadMaskButton.disabled = isProcessing || !hasDownloadableMask;
    downloadMaskButton.title = !hasDownloadableMask ? "Process an image first or load an AI mask so a mask exists." : "";
  }
  if (downloadPanelsButton) {
    downloadPanelsButton.disabled = isProcessing || !hasPanels;
    downloadPanelsButton.title = !hasPanels ? "Process an image first so split panels exist." : "";
  }
  if (showLikelyUiButton) showLikelyUiButton.disabled = !hasPanels;
  if (showAllPanelsButton) showAllPanelsButton.disabled = !hasPanels;
  if (splitMinPixels) splitMinPixels.disabled = !hasPanels;
  if (splitSortMode) splitSortMode.disabled = !hasPanels;
}

function updateSplitFilterButtons() {
  if (showLikelyUiButton) showLikelyUiButton.classList.toggle("split-filter-button-active", splitPanelFilter === "likely");
  if (showAllPanelsButton) showAllPanelsButton.classList.toggle("split-filter-button-active", splitPanelFilter === "all");
}

function updateSplitPanelThresholdLabel() {
  if (splitMinPixelsValue) splitMinPixelsValue.textContent = String(splitPanelMinPixels);
}

function getImageWorkHint(width, height) {
  const pixels = width * height;
  if (pixels >= 16000000) return "Very large image. Expect roughly 10-20 seconds.";
  if (pixels >= 8000000) return "Large image. Expect roughly 5-10 seconds.";
  if (pixels >= 3000000) return "Medium image. Expect a few seconds.";
  return "Small image. Processing should feel quick.";
}

function copyText(text) { navigator.clipboard.writeText(text).catch(() => {}); }
function updateRangeLabels() {
  if (brushSizeValue) brushSizeValue.textContent = bgBrushSize ? bgBrushSize.value : String(DEFAULT_BRUSH_RADIUS);
  if (maskOverlayValue) maskOverlayValue.textContent = bgMaskOverlay ? bgMaskOverlay.value : "55";
  if (aiConfidenceValue) aiConfidenceValue.textContent = bgAiConfidence ? bgAiConfidence.value : "72";
  if (aiMatteValue) aiMatteValue.textContent = bgAiMatte ? bgAiMatte.value : "68";
  if (aiSpillValue) aiSpillValue.textContent = bgAiSpill ? bgAiSpill.value : "62";
  if (aiMaskExpandValue) aiMaskExpandValue.textContent = bgAiMaskExpand ? bgAiMaskExpand.value : "0";
  if (aiMaskFeatherValue) aiMaskFeatherValue.textContent = bgAiMaskFeather ? bgAiMaskFeather.value : "0";
  if (thresholdValue) thresholdValue.textContent = bgThreshold.value;
  if (softnessValue) softnessValue.textContent = bgSoftness.value;
  if (alphaFloorValue) alphaFloorValue.textContent = bgAlphaFloor.value;
  if (alphaCeilingValue) alphaCeilingValue.textContent = bgAlphaCeiling.value;
  if (edgeCleanupValue) edgeCleanupValue.textContent = bgEdgeCleanupStrength ? bgEdgeCleanupStrength.value : "55";
  if (componentAlphaValue) componentAlphaValue.textContent = bgComponentAlpha.value;
  if (componentPixelsValue) componentPixelsValue.textContent = bgComponentPixels.value;
  if (componentPadValue) componentPadValue.textContent = bgComponentPad.value;
  if (objectPadValue) objectPadValue.textContent = bgObjectPad.value;
}

function getCurrentBrushRadius() {
  return Math.max(4, Number(bgBrushSize ? bgBrushSize.value : DEFAULT_BRUSH_RADIUS) || DEFAULT_BRUSH_RADIUS);
}

function getMaskOverlayAlpha() {
  return Math.max(0, Math.min(1, Number(bgMaskOverlay ? bgMaskOverlay.value : 55) / 100));
}

function startBrushStroke(kind) {
  activeBrushStroke = {
    kind,
    startCount: kind === "keep" ? manualKeepBrushPoints.length : manualRemoveBrushPoints.length
  };
}

function finishBrushStroke() {
  if (!activeBrushStroke) return;
  const target = activeBrushStroke.kind === "keep" ? manualKeepBrushPoints : manualRemoveBrushPoints;
  const added = target.length - activeBrushStroke.startCount;
  if (added > 0) {
    brushEditHistory.push({ kind: activeBrushStroke.kind, count: added });
  }
  activeBrushStroke = null;
}

function clearBrushHistory() {
  brushEditHistory = [];
  activeBrushStroke = null;
}

function undoLastBrushEdit() {
  const last = brushEditHistory.pop();
  if (!last) {
    bgStatus.textContent = "No brush edit to undo.";
    updateActionStates();
    return;
  }
  const target = last.kind === "keep" ? manualKeepBrushPoints : manualRemoveBrushPoints;
  target.splice(Math.max(0, target.length - last.count), last.count);
  updateSampleMeta();
  renderOriginalPreview();
  updateActionStates();
  bgStatus.textContent = `Undid last ${last.kind === "keep" ? "brush keep" : "brush remove"} edit.`;
}

function updateEditorLayout() {
  if (!previewStack) return;
  previewStack.classList.toggle("editor-focus-original", bgEditorView && bgEditorView.value === "focus");
}

function applyPreset(name) {
  const preset = bgPresets[name];
  if (!preset) return;
  bgThreshold.value = preset.threshold;
  bgSoftness.value = preset.softness;
  bgAlphaFloor.value = preset.alphaFloor;
  bgAlphaCeiling.value = preset.alphaCeiling;
  bgComponentAlpha.value = preset.componentAlpha;
  bgComponentPixels.value = preset.componentPixels;
  bgComponentPad.value = preset.componentPad;
  bgObjectPad.value = preset.objectPad;
  bgCropTransparent.checked = preset.cropTransparent;
  bgDecontaminate.checked = preset.decontaminate;
  if (bgEdgeCleanupStrength) bgEdgeCleanupStrength.value = "55";
  if (bgStrongBorderRepair) bgStrongBorderRepair.checked = false;
  bgTone.value = preset.tone;
  updateRangeLabels();
}

function createCanvas(width, height) {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

function createMaskCanvasFromAlpha(alpha, width, height) {
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext("2d");
  const imageData = ctx.createImageData(width, height);
  for (let index = 0; index < alpha.length; index += 1) {
    const value = alpha[index];
    const offset = index * 4;
    imageData.data[offset] = value;
    imageData.data[offset + 1] = value;
    imageData.data[offset + 2] = value;
    imageData.data[offset + 3] = 255;
  }
  ctx.putImageData(imageData, 0, 0);
  return canvas;
}

function alphaFromMaskCanvas(canvas) {
  const ctx = canvas.getContext("2d");
  const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  const alpha = new Uint8ClampedArray(canvas.width * canvas.height);
  for (let index = 0; index < alpha.length; index += 1) {
    const offset = index * 4;
    alpha[index] = Math.max(data[offset], data[offset + 1], data[offset + 2], data[offset + 3]);
  }
  return alpha;
}

function boxBlurAlpha(alpha, width, height, radius) {
  if (radius <= 0) return new Uint8ClampedArray(alpha);
  const result = new Uint8ClampedArray(alpha.length);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      let total = 0;
      let count = 0;
      for (let oy = -radius; oy <= radius; oy += 1) {
        const ny = y + oy;
        if (ny < 0 || ny >= height) continue;
        for (let ox = -radius; ox <= radius; ox += 1) {
          const nx = x + ox;
          if (nx < 0 || nx >= width) continue;
          total += alpha[(ny * width) + nx];
          count += 1;
        }
      }
      result[(y * width) + x] = Math.round(total / Math.max(1, count));
    }
  }
  return result;
}

function dilateAlpha(alpha, width, height, radius) {
  if (radius <= 0) return new Uint8ClampedArray(alpha);
  let current = new Uint8ClampedArray(alpha);
  for (let step = 0; step < radius; step += 1) {
    const next = new Uint8ClampedArray(current);
    for (let y = 1; y < height - 1; y += 1) {
      for (let x = 1; x < width - 1; x += 1) {
        const index = (y * width) + x;
        let value = current[index];
        value = Math.max(
          value,
          current[index - 1],
          current[index + 1],
          current[index - width],
          current[index + width]
        );
        next[index] = value;
      }
    }
    current = next;
  }
  return current;
}

function erodeAlpha(alpha, width, height, radius) {
  if (radius <= 0) return new Uint8ClampedArray(alpha);
  let current = new Uint8ClampedArray(alpha);
  for (let step = 0; step < radius; step += 1) {
    const next = new Uint8ClampedArray(current);
    for (let y = 1; y < height - 1; y += 1) {
      for (let x = 1; x < width - 1; x += 1) {
        const index = (y * width) + x;
        let value = current[index];
        value = Math.min(
          value,
          current[index - 1],
          current[index + 1],
          current[index - width],
          current[index + width]
        );
        next[index] = value;
      }
    }
    current = next;
  }
  return current;
}

function applyManualCorrectionsToAlpha(alpha, width, height, settings) {
  let corrected = new Uint8ClampedArray(alpha);
  if (settings.manualKeepSamples.length) {
    const keepMask = buildKeepMask(width, height, settings.manualKeepSamples, corrected, Math.max(16, settings.componentAlpha - 96));
    for (let i = 0; i < corrected.length; i += 1) {
      if (keepMask[i]) corrected[i] = 255;
    }
  }
  if (settings.manualKeepBoxes.length) {
    const keepMask = new Uint8Array(width * height);
    applyKeepBoxesToMask(keepMask, width, height, settings.manualKeepBoxes);
    for (let i = 0; i < corrected.length; i += 1) {
      if (keepMask[i]) corrected[i] = 255;
    }
  }
  if (settings.manualKeepBrushPoints.length) {
    const keepMask = new Uint8Array(width * height);
    applyBrushPointsToMask(keepMask, width, height, settings.manualKeepBrushPoints);
    for (let i = 0; i < corrected.length; i += 1) {
      if (keepMask[i]) corrected[i] = 255;
    }
  }
  if (settings.manualSubtractBoxes.length) {
    corrected = applySubtractBoxesToAlpha(corrected, width, height, settings.manualSubtractBoxes);
  }
  if (settings.manualRemoveBrushPoints.length) {
    corrected = applyBrushPointsToAlpha(corrected, width, height, settings.manualRemoveBrushPoints, 0);
  }
  return corrected;
}

function refineImportedAiMaskAlpha(alpha, width, height, settings) {
  let refined = new Uint8ClampedArray(alpha);
  if (settings.aiInvertMask) {
    for (let i = 0; i < refined.length; i += 1) {
      refined[i] = 255 - refined[i];
    }
  }
  if (settings.aiMaskExpand > 0) {
    refined = dilateAlpha(refined, width, height, settings.aiMaskExpand);
  } else if (settings.aiMaskExpand < 0) {
    refined = erodeAlpha(refined, width, height, Math.abs(settings.aiMaskExpand));
  }
  if (settings.aiMaskFeather > 0) {
    refined = boxBlurAlpha(refined, width, height, settings.aiMaskFeather);
  }
  if (settings.aiCombineManual) {
    refined = applyManualCorrectionsToAlpha(refined, width, height, settings);
  }
  return refined;
}

function getRefinedImportedAiAlpha(settings = getBgSettings()) {
  if (!loadedImage || !importedAiMaskAlpha) return null;
  return refineImportedAiMaskAlpha(importedAiMaskAlpha, loadedImage.width, loadedImage.height, settings);
}

function getAlphaCoverage(alpha, cutoff = 8) {
  if (!alpha || !alpha.length) return 0;
  let kept = 0;
  for (let i = 0; i < alpha.length; i += 1) {
    if (alpha[i] > cutoff) kept += 1;
  }
  return kept / alpha.length;
}

function rebuildImportedAiMaskCanvas() {
  const refined = getRefinedImportedAiAlpha();
  if (!loadedImage || !refined) return false;
  aiMaskCanvas = createMaskCanvasFromAlpha(refined, loadedImage.width, loadedImage.height);
  return true;
}

function refreshImportedAiMaskPreview() {
  if (!rebuildImportedAiMaskCanvas()) return false;
  if (bgMaskSource?.value === "ai" || bgPreviewTarget?.value === "mask") {
    syncMainPreviewFromLayout();
  }
  updateMaskStatusBlock();
  updateActionStates();
  return true;
}

function buildManualMaskCanvas(width, height, settings) {
  const keepMask = new Uint8Array(width * height);
  if (settings.manualKeepSamples.length) {
    const fakeAlpha = new Uint8ClampedArray(width * height).fill(255);
    let seeded = buildKeepMask(width, height, settings.manualKeepSamples, fakeAlpha, 1);
    for (let i = 0; i < keepMask.length; i += 1) keepMask[i] = seeded[i];
  }
  if (settings.manualKeepBoxes.length) {
    applyKeepBoxesToMask(keepMask, width, height, settings.manualKeepBoxes);
  }
  if (settings.manualKeepBrushPoints.length) {
    applyBrushPointsToMask(keepMask, width, height, settings.manualKeepBrushPoints);
  }

  const alpha = new Uint8ClampedArray(width * height);
  for (let i = 0; i < alpha.length; i += 1) {
    alpha[i] = keepMask[i] ? 255 : 0;
  }

  if (settings.manualSubtractBoxes.length) {
    applySubtractBoxesToAlpha(alpha, width, height, settings.manualSubtractBoxes);
  }
  if (settings.manualRemoveBrushPoints.length) {
    applyBrushPointsToAlpha(alpha, width, height, settings.manualRemoveBrushPoints, 0);
  }

  return createMaskCanvasFromAlpha(alpha, width, height);
}

function handleAiMaskInput(event) {
  const [file] = event.target.files || [];
  if (!file) return;
  if (!loadedImage) {
    bgStatus.textContent = "Load a source image first, then import the AI mask PNG.";
    if (aiMaskInput) aiMaskInput.value = "";
    return;
  }

  const url = URL.createObjectURL(file);
  const image = new Image();
  image.onload = () => {
    if (image.width !== loadedImage.width || image.height !== loadedImage.height) {
      bgStatus.textContent = `AI mask size mismatch. Expected ${loadedImage.width}x${loadedImage.height}, got ${image.width}x${image.height}.`;
      URL.revokeObjectURL(url);
      if (aiMaskInput) aiMaskInput.value = "";
      return;
    }

    const canvas = createCanvas(image.width, image.height);
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0);
    importedAiMaskAlpha = alphaFromMaskCanvas(canvas);
    rebuildImportedAiMaskCanvas();
    if (bgMaskSource) bgMaskSource.value = "ai";
    if (bgPreviewTarget) bgPreviewTarget.value = "mask";
    syncMainPreviewFromLayout();
    updateActionStates();
    updateMaskStatusBlock();
    bgStatus.textContent = "Loaded AI mask PNG. Set 'Current mask input' to 'Imported AI mask' to drive extraction from this matte.";
    URL.revokeObjectURL(url);
    if (aiMaskInput) aiMaskInput.value = "";
  };
  image.onerror = () => {
    bgStatus.textContent = "Could not read that AI mask image.";
    URL.revokeObjectURL(url);
    if (aiMaskInput) aiMaskInput.value = "";
  };
  image.src = url;
}

function drawImageOnCanvas(canvas, image) {
  const ctx = canvas.getContext("2d");
  canvas.width = image.width;
  canvas.height = image.height;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(image, 0, 0);
}

function syncMainPreviewFromLayout() {
  if (bgPreviewTarget && bgPreviewTarget.value === "mask" && (processedMaskCanvas || manualMaskCanvas || aiMaskCanvas)) {
    let chosenMask = processedMaskCanvas || manualMaskCanvas;
    if (bgMaskSource) {
      if (bgMaskSource.value === "manual") chosenMask = manualMaskCanvas || processedMaskCanvas;
      else if (bgMaskSource.value === "ai") chosenMask = aiMaskCanvas || processedMaskCanvas || manualMaskCanvas;
      else chosenMask = processedMaskCanvas || manualMaskCanvas;
    }
    if (chosenMask) {
      processedCanvas = chosenMask;
      drawImageOnCanvas(resultCanvas, chosenMask);
      resultMeta.textContent = `Mask preview | ${chosenMask.width} x ${chosenMask.height}`;
      return;
    }
  }

  if (!processedLayoutCanvas && !processedCanvas) {
    resultMeta.textContent = "No result yet";
    return;
  }

  if (bgLayout.value === "sheet" && processedLayoutCanvas) {
    selectedPanelIndex = -1;
    processedCanvas = processedLayoutCanvas;
    drawImageOnCanvas(resultCanvas, processedLayoutCanvas);
    resultMeta.textContent = `${processedLayoutCanvas.width} x ${processedLayoutCanvas.height}`;
    return;
  }

  if (bgLayout.value === "split" && processedPanels.length) {
    const safeIndex = Math.max(0, Math.min(selectedPanelIndex >= 0 ? selectedPanelIndex : 0, processedPanels.length - 1));
    selectedPanelIndex = safeIndex;
    processedCanvas = getPanelDisplayCanvas(processedPanels[safeIndex]);
    drawImageOnCanvas(resultCanvas, processedCanvas);
    resultMeta.textContent = `Panel ${safeIndex + 1} | ${processedCanvas.width} x ${processedCanvas.height}`;
    return;
  }

  if (processedLayoutCanvas) {
    processedCanvas = processedLayoutCanvas;
    drawImageOnCanvas(resultCanvas, processedLayoutCanvas);
    resultMeta.textContent = `${processedLayoutCanvas.width} x ${processedLayoutCanvas.height}`;
  }
}

function normalizeBox(box) {
  return {
    left: Math.min(box.left, box.right),
    top: Math.min(box.top, box.bottom),
    right: Math.max(box.left, box.right),
    bottom: Math.max(box.top, box.bottom)
  };
}

function renderOriginalPreview() {
  if (!loadedImage) {
    const ctx = originalCanvas.getContext("2d");
    ctx.clearRect(0, 0, originalCanvas.width, originalCanvas.height);
    return;
  }
  drawImageOnCanvas(originalCanvas, loadedImage);
  const ctx = originalCanvas.getContext("2d");
  const overlayAlpha = getMaskOverlayAlpha();

  for (const sample of manualBackgroundSamples) {
    ctx.beginPath();
    ctx.arc(sample.x, sample.y, 10, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(212, 47, 69, 0.72)";
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#fff6f1";
    ctx.stroke();
  }

  for (const sample of manualKeepSamples) {
    ctx.beginPath();
    ctx.arc(sample.x, sample.y, 10, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(40, 167, 69, 0.72)";
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#f7fff7";
    ctx.stroke();
  }

  const boxesToDraw = activeKeepBox ? [...manualKeepBoxes, normalizeBox(activeKeepBox)] : manualKeepBoxes;
  for (const box of boxesToDraw) {
    const normalized = normalizeBox(box);
    const width = Math.max(1, normalized.right - normalized.left);
    const height = Math.max(1, normalized.bottom - normalized.top);
    ctx.fillStyle = `rgba(40, 167, 69, ${0.22 * overlayAlpha})`;
    ctx.fillRect(normalized.left, normalized.top, width, height);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "rgba(40, 167, 69, 0.9)";
    ctx.strokeRect(normalized.left, normalized.top, width, height);
  }

  for (const box of manualSubtractBoxes) {
    const normalized = normalizeBox(box);
    const width = Math.max(1, normalized.right - normalized.left);
    const height = Math.max(1, normalized.bottom - normalized.top);
    ctx.fillStyle = `rgba(212, 47, 69, ${0.24 * overlayAlpha})`;
    ctx.fillRect(normalized.left, normalized.top, width, height);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "rgba(212, 47, 69, 0.92)";
    ctx.strokeRect(normalized.left, normalized.top, width, height);
  }

  for (const point of manualKeepBrushPoints) {
    ctx.beginPath();
    ctx.arc(point.x, point.y, point.radius || getCurrentBrushRadius(), 0, Math.PI * 2);
    ctx.fillStyle = `rgba(80, 200, 120, ${0.34 * overlayAlpha})`;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = "rgba(80, 200, 120, 0.85)";
    ctx.stroke();
  }

  for (const point of manualRemoveBrushPoints) {
    ctx.beginPath();
    ctx.arc(point.x, point.y, point.radius || getCurrentBrushRadius(), 0, Math.PI * 2);
    ctx.fillStyle = `rgba(212, 47, 69, ${0.34 * overlayAlpha})`;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = "rgba(212, 47, 69, 0.9)";
    ctx.stroke();
  }
}

function getBgSettings() {
  return {
    mode: bgMode.value,
    layout: bgLayout.value,
    maskSource: bgMaskSource ? bgMaskSource.value : "processed",
    previewTarget: bgPreviewTarget ? bgPreviewTarget.value : "result",
    panelLayout: bgPanelLayout.value,
    threshold: Number(bgThreshold.value),
    softness: Number(bgSoftness.value),
    alphaFloor: Number(bgAlphaFloor.value),
    alphaCeiling: Number(bgAlphaCeiling.value),
    componentAlpha: Number(bgComponentAlpha.value),
    componentPixels: Number(bgComponentPixels.value),
    componentPad: Number(bgComponentPad.value),
    objectPad: Number(bgObjectPad.value),
    tone: bgTone.value,
    cropTransparent: bgCropTransparent.checked,
    decontaminate: bgDecontaminate.checked,
    edgeCleanupStrength: Number(bgEdgeCleanupStrength ? bgEdgeCleanupStrength.value : 55),
    strongBorderRepair: Boolean(bgStrongBorderRepair && bgStrongBorderRepair.checked),
    preserveColor: bgPreserveColor.checked,
    secondPass: bgSecondPass.checked,
    aiSource: bgAiSource ? bgAiSource.value : "bria",
    aiConfidence: Number(bgAiConfidence ? bgAiConfidence.value : 72),
    aiMatte: Number(bgAiMatte ? bgAiMatte.value : 68),
    aiSpill: Number(bgAiSpill ? bgAiSpill.value : 62),
    aiRelight: Boolean(bgAiRelight && bgAiRelight.checked),
    aiInpaint: Boolean(bgAiInpaint && bgAiInpaint.checked),
    aiInvertMask: Boolean(bgAiInvertMask && bgAiInvertMask.checked),
    aiMaskExpand: Number(bgAiMaskExpand ? bgAiMaskExpand.value : 0),
    aiMaskFeather: Number(bgAiMaskFeather ? bgAiMaskFeather.value : 0),
    aiCombineManual: Boolean(!bgAiCombineManual || bgAiCombineManual.checked),
    manualBackgroundColor,
    manualBackgroundSamples: [...manualBackgroundSamples],
    manualKeepSamples: [...manualKeepSamples],
    manualKeepBoxes: manualKeepBoxes.map((box) => ({ ...box })),
    manualSubtractBoxes: manualSubtractBoxes.map((box) => ({ ...box })),
    manualKeepBrushPoints: manualKeepBrushPoints.map((point) => ({ ...point })),
    manualRemoveBrushPoints: manualRemoveBrushPoints.map((point) => ({ ...point }))
  };
}

function getPanelDisplayCanvas(panel) {
  if (!panel) return null;
  return splitPanelLayoutMode === "full" && panel.fullCanvas ? panel.fullCanvas : panel.canvas;
}

function getCanvasPixel(canvas, event) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const x = Math.max(0, Math.min(canvas.width - 1, Math.floor((event.clientX - rect.left) * scaleX)));
  const y = Math.max(0, Math.min(canvas.height - 1, Math.floor((event.clientY - rect.top) * scaleY)));
  const data = canvas.getContext("2d").getImageData(x, y, 1, 1).data;
  return { x, y, r: data[0], g: data[1], b: data[2] };
}

function stopSamplingMode() {
  if (samplingHandler) {
    originalCanvas.removeEventListener("click", samplingHandler);
    originalCanvas.removeEventListener("mousedown", samplingHandler);
    samplingHandler = null;
  }
  if (samplingMoveHandler) {
    originalCanvas.removeEventListener("mousemove", samplingMoveHandler);
    samplingMoveHandler = null;
  }
  if (samplingUpHandler) {
    originalCanvas.removeEventListener("mouseup", samplingUpHandler);
    originalCanvas.removeEventListener("mouseleave", samplingUpHandler);
    samplingUpHandler = null;
  }
  finishBrushStroke();
  samplingModeActive = false;
  samplingTarget = "background";
  activeKeepBox = null;
  if (sampleBgButton) sampleBgButton.textContent = "Start Sampling Background Points";
  if (sampleKeepButton) sampleKeepButton.textContent = "Mark UI Keep Point(s)";
  if (sampleKeepBoxButton) sampleKeepBoxButton.textContent = "Draw UI Keep Box(es)";
  if (sampleSubtractBoxButton) sampleSubtractBoxButton.textContent = "Draw Scenery Remove Box(es)";
  if (eraseKeepBoxButton) eraseKeepBoxButton.textContent = "Erase Bad Keep Box(es)";
  if (brushKeepButton) brushKeepButton.textContent = "Brush Keep Edges";
  if (brushRemoveButton) brushRemoveButton.textContent = "Brush Remove Junk";
  originalCanvas.classList.remove("sampling-active");
  renderOriginalPreview();
  updateActionStates();
}

function startSamplingMode(target) {
  if (!loadedImage) {
    bgStatus.textContent = "Upload an image first.";
    return;
  }
  if (samplingModeActive && samplingTarget === target) {
    stopSamplingMode();
    bgStatus.textContent = target === "keep"
      ? `Stopped marking UI keep points. ${manualKeepSamples.length} point${manualKeepSamples.length === 1 ? "" : "s"} saved.`
      : target === "keep-box"
        ? `Stopped drawing UI keep boxes. ${manualKeepBoxes.length} box${manualKeepBoxes.length === 1 ? "" : "es"} saved.`
      : target === "subtract-box"
        ? `Stopped drawing scenery remove boxes. ${manualSubtractBoxes.length} box${manualSubtractBoxes.length === 1 ? "" : "es"} saved.`
      : target === "brush-keep"
        ? `Stopped brushing keep edges. ${manualKeepBrushPoints.length} brush point${manualKeepBrushPoints.length === 1 ? "" : "s"} saved.`
      : target === "brush-remove"
        ? `Stopped brushing remove marks. ${manualRemoveBrushPoints.length} brush point${manualRemoveBrushPoints.length === 1 ? "" : "s"} saved.`
      : target === "erase-box"
        ? "Stopped erasing UI keep boxes."
      : bgMode.value === "multi"
        ? `Stopped sampling. ${manualBackgroundSamples.length} background point${manualBackgroundSamples.length === 1 ? "" : "s"} saved.`
        : "Stopped sampling background.";
    return;
  }
  stopSamplingMode();
  samplingTarget = target;
  bgStatus.textContent = target === "keep"
    ? "Click UI parts you want protected: top bars, bottom bars, icon strips, side rails, or frames."
    : target === "keep-box"
      ? `Drag one or more boxes around UI regions you want protected, like top bars, bottom panels, icon strips, or frames. You can add up to ${MAX_KEEP_BOXES} boxes.`
    : target === "subtract-box"
      ? `Drag red boxes over scenery junk you want force-removed. These boxes subtract from the final result.`
      : target === "brush-keep"
        ? "Paint green keep marks over ornate edges or decorative UI details you want preserved."
      : target === "brush-remove"
        ? "Paint red remove marks over fringe, white specks, or junk you want force-erased."
      : target === "erase-box"
        ? "Click a green keep box on the Original preview to remove it."
      : bgMode.value === "multi"
        ? "Click 3-4 empty background spots in the Original preview, then stop sampling."
        : "Click one background spot in the Original preview.";
  if (sampleBgButton) sampleBgButton.textContent = bgMode.value === "multi" ? "Stop Sampling Background Points" : "Stop Sampling";
  if (sampleKeepButton) sampleKeepButton.textContent = target === "keep" ? "Stop Marking UI Keep Points" : "Mark UI Keep Point(s)";
  if (sampleKeepBoxButton) sampleKeepBoxButton.textContent = target === "keep-box" ? "Stop Drawing UI Keep Box(es)" : "Draw UI Keep Box(es)";
  if (sampleSubtractBoxButton) sampleSubtractBoxButton.textContent = target === "subtract-box" ? "Stop Drawing Scenery Remove Box(es)" : "Draw Scenery Remove Box(es)";
  if (eraseKeepBoxButton) eraseKeepBoxButton.textContent = target === "erase-box" ? "Stop Erasing Keep Box(es)" : "Erase Bad Keep Box(es)";
  if (brushKeepButton) brushKeepButton.textContent = target === "brush-keep" ? "Stop Brushing Keep Edges" : "Brush Keep Edges";
  if (brushRemoveButton) brushRemoveButton.textContent = target === "brush-remove" ? "Stop Brushing Remove Marks" : "Brush Remove Junk";
  originalCanvas.classList.add("sampling-active");
  samplingModeActive = true;
  if (target === "erase-box") {
    samplingHandler = (event) => {
      const sample = getCanvasPixel(originalCanvas, event);
      for (let i = manualKeepBoxes.length - 1; i >= 0; i -= 1) {
        const box = normalizeBox(manualKeepBoxes[i]);
        if (sample.x >= box.left && sample.x <= box.right && sample.y >= box.top && sample.y <= box.bottom) {
          manualKeepBoxes.splice(i, 1);
          updateSampleMeta();
          renderOriginalPreview();
          updateActionStates();
          bgStatus.textContent = `Removed a UI keep box. ${manualKeepBoxes.length} box${manualKeepBoxes.length === 1 ? "" : "es"} remain.`;
          return;
        }
      }
      bgStatus.textContent = "That click did not hit a keep box. Click inside a green box to remove it.";
    };
    originalCanvas.addEventListener("click", samplingHandler);
    return;
  }
  if (target === "keep-box") {
    samplingHandler = (event) => {
      const sample = getCanvasPixel(originalCanvas, event);
      activeKeepBox = { left: sample.x, top: sample.y, right: sample.x, bottom: sample.y };
      renderOriginalPreview();
    };
    samplingMoveHandler = (event) => {
      if (!activeKeepBox) return;
      const sample = getCanvasPixel(originalCanvas, event);
      activeKeepBox.right = sample.x;
      activeKeepBox.bottom = sample.y;
      renderOriginalPreview();
    };
    samplingUpHandler = (event) => {
      if (!activeKeepBox) return;
      const sample = getCanvasPixel(originalCanvas, event);
      activeKeepBox.right = sample.x;
      activeKeepBox.bottom = sample.y;
      const imageData = originalCanvas.getContext("2d").getImageData(0, 0, originalCanvas.width, originalCanvas.height);
      const box = snapBoxToNearbyContent(activeKeepBox, imageData, getBackgroundSamples(getBgSettings(), imageData));
      if ((box.right - box.left) >= 12 && (box.bottom - box.top) >= 12) {
        if (manualKeepBoxes.length < MAX_KEEP_BOXES) {
          manualKeepBoxes.push(box);
        } else {
          manualKeepBoxes[manualKeepBoxes.length - 1] = box;
        }
        bgStatus.textContent = `Added UI keep box ${manualKeepBoxes.length}. Draw more boxes for other UI assets or stop box mode.`;
      }
      activeKeepBox = null;
      updateSampleMeta();
      renderOriginalPreview();
    };
    originalCanvas.addEventListener("mousedown", samplingHandler);
    originalCanvas.addEventListener("mousemove", samplingMoveHandler);
    originalCanvas.addEventListener("mouseup", samplingUpHandler);
    originalCanvas.addEventListener("mouseleave", samplingUpHandler);
    return;
  }
  if (target === "subtract-box") {
    samplingHandler = (event) => {
      const sample = getCanvasPixel(originalCanvas, event);
      activeKeepBox = { left: sample.x, top: sample.y, right: sample.x, bottom: sample.y };
      renderOriginalPreview();
    };
    samplingMoveHandler = (event) => {
      if (!activeKeepBox) return;
      const sample = getCanvasPixel(originalCanvas, event);
      activeKeepBox.right = sample.x;
      activeKeepBox.bottom = sample.y;
      renderOriginalPreview();
    };
    samplingUpHandler = (event) => {
      if (!activeKeepBox) return;
      const sample = getCanvasPixel(originalCanvas, event);
      activeKeepBox.right = sample.x;
      activeKeepBox.bottom = sample.y;
      const box = normalizeBox(activeKeepBox);
      if ((box.right - box.left) >= 12 && (box.bottom - box.top) >= 12) {
        manualSubtractBoxes.push(box);
        bgStatus.textContent = `Added scenery remove box ${manualSubtractBoxes.length}. Draw more red boxes or stop subtract mode.`;
      }
      activeKeepBox = null;
      updateSampleMeta();
      renderOriginalPreview();
    };
    originalCanvas.addEventListener("mousedown", samplingHandler);
    originalCanvas.addEventListener("mousemove", samplingMoveHandler);
    originalCanvas.addEventListener("mouseup", samplingUpHandler);
    originalCanvas.addEventListener("mouseleave", samplingUpHandler);
    return;
  }
  if (target === "brush-keep") {
    samplingHandler = (event) => {
      startBrushStroke("keep");
      const sample = getCanvasPixel(originalCanvas, event);
      manualKeepBrushPoints.push({ x: sample.x, y: sample.y, radius: getCurrentBrushRadius() });
      updateSampleMeta();
      renderOriginalPreview();
      updateActionStates();
    };
    samplingMoveHandler = (event) => {
      if ((event.buttons & 1) !== 1) return;
      const sample = getCanvasPixel(originalCanvas, event);
      manualKeepBrushPoints.push({ x: sample.x, y: sample.y, radius: getCurrentBrushRadius() });
      updateSampleMeta();
      renderOriginalPreview();
    };
    samplingUpHandler = () => {
      finishBrushStroke();
      bgStatus.textContent = `Painted keep edges. ${manualKeepBrushPoints.length} brush point${manualKeepBrushPoints.length === 1 ? "" : "s"} saved.`;
      updateActionStates();
    };
    originalCanvas.addEventListener("mousedown", samplingHandler);
    originalCanvas.addEventListener("mousemove", samplingMoveHandler);
    originalCanvas.addEventListener("mouseup", samplingUpHandler);
    originalCanvas.addEventListener("mouseleave", samplingUpHandler);
    return;
  }
  if (target === "brush-remove") {
    samplingHandler = (event) => {
      startBrushStroke("remove");
      const sample = getCanvasPixel(originalCanvas, event);
      manualRemoveBrushPoints.push({ x: sample.x, y: sample.y, radius: getCurrentBrushRadius() });
      updateSampleMeta();
      renderOriginalPreview();
      updateActionStates();
    };
    samplingMoveHandler = (event) => {
      if ((event.buttons & 1) !== 1) return;
      const sample = getCanvasPixel(originalCanvas, event);
      manualRemoveBrushPoints.push({ x: sample.x, y: sample.y, radius: getCurrentBrushRadius() });
      updateSampleMeta();
      renderOriginalPreview();
    };
    samplingUpHandler = () => {
      finishBrushStroke();
      bgStatus.textContent = `Painted remove marks. ${manualRemoveBrushPoints.length} brush point${manualRemoveBrushPoints.length === 1 ? "" : "s"} saved.`;
      updateActionStates();
    };
    originalCanvas.addEventListener("mousedown", samplingHandler);
    originalCanvas.addEventListener("mousemove", samplingMoveHandler);
    originalCanvas.addEventListener("mouseup", samplingUpHandler);
    originalCanvas.addEventListener("mouseleave", samplingUpHandler);
    return;
  }
  samplingHandler = (event) => {
    const sample = getCanvasPixel(originalCanvas, event);
    const nextSample = { x: sample.x, y: sample.y, r: sample.r, g: sample.g, b: sample.b };
    if (target === "keep") {
      if (manualKeepSamples.length < MAX_KEEP_POINTS) {
        manualKeepSamples.push(nextSample);
      } else {
        manualKeepSamples[manualKeepSamples.length - 1] = nextSample;
      }
      updateSampleMeta();
      updateActionStates();
      renderOriginalPreview();
      bgStatus.textContent = `Added UI keep point ${manualKeepSamples.length}. Click more UI or stop marking keep points.`;
      return;
    }
    manualBackgroundColor = { r: sample.r, g: sample.g, b: sample.b };
    if (bgMode.value === "multi") {
      if (manualBackgroundSamples.length < MAX_BG_SAMPLES) {
        manualBackgroundSamples.push(nextSample);
      } else {
        manualBackgroundSamples[manualBackgroundSamples.length - 1] = nextSample;
      }
      updateSampleMeta();
      updateActionStates();
      renderOriginalPreview();
      bgStatus.textContent = `Added background sample ${manualBackgroundSamples.length}. Click more empty background or stop sampling.`;
      return;
    }
    bgStatus.textContent = `Sampled background color rgb(${sample.r}, ${sample.g}, ${sample.b}). Click Process Image.`;
    stopSamplingMode();
  };
  originalCanvas.addEventListener("click", samplingHandler);
}

function handleSampleBackgroundMode() {
  startSamplingMode("background");
}

function handleSampleKeepMode() {
  startSamplingMode("keep");
}

function handleSampleKeepBoxMode() {
  startSamplingMode("keep-box");
}

function handleEraseKeepBoxMode() {
  startSamplingMode("erase-box");
}

function handleBrushKeepMode() {
  startSamplingMode("brush-keep");
}

function handleBrushRemoveMode() {
  startSamplingMode("brush-remove");
}

function handleAutoDetectUiBoxes() {
  if (!loadedImage) {
    bgStatus.textContent = "Upload an image first.";
    return;
  }
  stopSamplingMode();
  const ctx = originalCanvas.getContext("2d");
  const imageData = ctx.getImageData(0, 0, originalCanvas.width, originalCanvas.height);
  const detected = autoDetectUiBoxesFromImage(imageData);
  if (!detected.length) {
    bgStatus.textContent = "Could not auto-detect likely UI boxes on this image.";
    return;
  }

  for (const box of detected) {
    if (manualKeepBoxes.length < MAX_KEEP_BOXES) {
      manualKeepBoxes.push(box);
    } else {
      break;
    }
  }

  const deduped = [];
  const seen = new Set();
  for (const box of manualKeepBoxes) {
    const normalized = normalizeBox(box);
    const key = `${normalized.left}:${normalized.top}:${normalized.right}:${normalized.bottom}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(normalized);
  }
  manualKeepBoxes = deduped.slice(0, MAX_KEEP_BOXES);
  updateSampleMeta();
  renderOriginalPreview();
  updateActionStates();
  bgStatus.textContent = `Auto-detected ${detected.length} likely UI box${detected.length === 1 ? "" : "es"}. Adjust with draw/erase box mode if needed.`;
}

function addPresetKeepBoxes(kind) {
  if (!loadedImage) {
    bgStatus.textContent = "Upload an image first.";
    return;
  }
  const ctx = originalCanvas.getContext("2d");
  const imageData = ctx.getImageData(0, 0, originalCanvas.width, originalCanvas.height);
  const bounds = findVisibleBoundsFromImageData(imageData);
  const { left, top, width, height } = bounds;
  const candidates = [];

  if (kind === "top") {
    candidates.push({
      left: left + Math.round(width * 0.01),
      top: top + Math.round(height * 0.005),
      right: left + Math.round(width * 0.985),
      bottom: top + Math.round(height * 0.10)
    });
  } else if (kind === "bottom") {
    candidates.push({
      left: left + Math.round(width * 0.01),
      top: top + Math.round(height * 0.74),
      right: left + Math.round(width * 0.985),
      bottom: top + Math.round(height * 0.995)
    });
  } else if (kind === "icons") {
    candidates.push({
      left: left + Math.round(width * 0.62),
      top: top + Math.round(height * 0.72),
      right: left + Math.round(width * 0.985),
      bottom: top + Math.round(height * 0.995)
    });
  }

  const bgSettings = getBgSettings();
  const backgroundSamples = getBackgroundSamples(bgSettings, imageData);
  for (const candidate of candidates) {
    const snapped = snapBoxToNearbyContent(candidate, imageData, backgroundSamples);
    manualKeepBoxes.push(snapped);
  }
  manualKeepBoxes = manualKeepBoxes.slice(0, MAX_KEEP_BOXES);
  updateSampleMeta();
  renderOriginalPreview();
  updateActionStates();
  bgStatus.textContent = `Added ${kind === "icons" ? "icon strip" : `${kind} bar`} protection box.`;
}

function sampleBackgroundColor(imageData, tone) {
  const { width, height, data } = imageData;
  const marginX = Math.max(1, Math.floor(width * 0.08));
  const marginY = Math.max(1, Math.floor(height * 0.08));
  const samples = [];
  function pushPixel(x, y) {
    const offset = (y * width + x) * 4;
    samples.push({ r: data[offset], g: data[offset + 1], b: data[offset + 2], brightness: (data[offset] + data[offset + 1] + data[offset + 2]) / 3 });
  }
  for (let y = 0; y < marginY; y += 4) {
    for (let x = 0; x < width; x += 4) {
      pushPixel(x, y);
      pushPixel(x, height - 1 - y);
    }
  }
  for (let y = marginY; y < height - marginY; y += 4) {
    for (let x = 0; x < marginX; x += 4) {
      pushPixel(x, y);
      pushPixel(width - 1 - x, y);
    }
  }
  samples.sort((a, b) => tone === "light" ? b.brightness - a.brightness : a.brightness - b.brightness);
  const chosen = samples.slice(0, Math.max(12, Math.floor(samples.length * 0.08)));
  const total = chosen.reduce((acc, sample) => ({ r: acc.r + sample.r, g: acc.g + sample.g, b: acc.b + sample.b }), { r: 0, g: 0, b: 0 });
  return { r: Math.round(total.r / chosen.length), g: Math.round(total.g / chosen.length), b: Math.round(total.b / chosen.length) };
}

function getColorDistanceSq(r, g, b, sample) {
  const dr = r - sample.r;
  const dg = g - sample.g;
  const db = b - sample.b;
  return dr * dr + dg * dg + db * db;
}

function getColorDistance(r, g, b, sample) {
  return Math.sqrt(getColorDistanceSq(r, g, b, sample));
}

function getBackgroundSamples(settings, imageData) {
  if (settings.mode === "multi" && settings.manualBackgroundSamples.length) {
    return settings.manualBackgroundSamples.slice(0, 4);
  }
  return [settings.manualBackgroundColor || sampleBackgroundColor(imageData, settings.tone)];
}

function buildKeepMask(width, height, keepSamples, alpha, alphaThreshold) {
  const keepMask = new Uint8Array(width * height);
  if (!keepSamples.length) return keepMask;
  const queue = [];
  for (const sample of keepSamples) {
    const index = sample.y * width + sample.x;
    if (index < 0 || index >= keepMask.length) continue;
    if (alpha[index] > alphaThreshold && !keepMask[index]) {
      keepMask[index] = 1;
      queue.push(index);
    }
  }
  let head = 0;
  while (head < queue.length) {
    const index = queue[head++];
    const x = index % width;
    const y = Math.floor(index / width);
    const neighbors = [
      x > 0 ? index - 1 : -1,
      x < width - 1 ? index + 1 : -1,
      y > 0 ? index - width : -1,
      y < height - 1 ? index + width : -1
    ];
    for (const next of neighbors) {
      if (next < 0 || keepMask[next] || alpha[next] <= alphaThreshold) continue;
      keepMask[next] = 1;
      queue.push(next);
    }
  }
  return keepMask;
}

function applyKeepBoxesToMask(keepMask, width, height, boxes) {
  for (const rawBox of boxes) {
    const box = normalizeBox(rawBox);
    const left = Math.max(0, Math.min(width - 1, box.left));
    const top = Math.max(0, Math.min(height - 1, box.top));
    const right = Math.max(left + 1, Math.min(width, box.right));
    const bottom = Math.max(top + 1, Math.min(height, box.bottom));
    for (let y = top; y < bottom; y += 1) {
      for (let x = left; x < right; x += 1) {
        keepMask[y * width + x] = 1;
      }
    }
  }
  return keepMask;
}

function applyBrushPointsToMask(keepMask, width, height, points) {
  for (const point of points) {
    const radius = point.radius || getCurrentBrushRadius();
    const radiusSq = radius * radius;
    const minX = Math.max(0, point.x - radius);
    const maxX = Math.min(width - 1, point.x + radius);
    const minY = Math.max(0, point.y - radius);
    const maxY = Math.min(height - 1, point.y + radius);
    for (let y = minY; y <= maxY; y += 1) {
      for (let x = minX; x <= maxX; x += 1) {
        const dx = x - point.x;
        const dy = y - point.y;
        if ((dx * dx) + (dy * dy) <= radiusSq) {
          keepMask[y * width + x] = 1;
        }
      }
    }
  }
  return keepMask;
}

function applyBrushPointsToAlpha(alpha, width, height, points, value = 0) {
  for (const point of points) {
    const radius = point.radius || getCurrentBrushRadius();
    const radiusSq = radius * radius;
    const minX = Math.max(0, point.x - radius);
    const maxX = Math.min(width - 1, point.x + radius);
    const minY = Math.max(0, point.y - radius);
    const maxY = Math.min(height - 1, point.y + radius);
    for (let y = minY; y <= maxY; y += 1) {
      for (let x = minX; x <= maxX; x += 1) {
        const dx = x - point.x;
        const dy = y - point.y;
        if ((dx * dx) + (dy * dy) <= radiusSq) {
          alpha[y * width + x] = value;
        }
      }
    }
  }
  return alpha;
}

function getManualKeepPanelBoxes(width, height, keepBoxes, pad) {
  return keepBoxes.map((box) => clampBox(normalizeBox(box), width, height, pad));
}

function findMaskComponentBoxes(mask, width, height, minPixels = 90) {
  const seen = new Uint8Array(width * height);
  const boxes = [];
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const startIndex = y * width + x;
      if (seen[startIndex] || mask[startIndex] === 0) continue;
      const queue = [startIndex];
      seen[startIndex] = 1;
      let head = 0;
      let count = 0;
      let minX = x;
      let minY = y;
      let maxX = x;
      let maxY = y;
      while (head < queue.length) {
        const index = queue[head++];
        const cx = index % width;
        const cy = Math.floor(index / width);
        count += 1;
        minX = Math.min(minX, cx);
        minY = Math.min(minY, cy);
        maxX = Math.max(maxX, cx);
        maxY = Math.max(maxY, cy);
        const neighbors = [
          cx > 0 ? index - 1 : -1,
          cx < width - 1 ? index + 1 : -1,
          cy > 0 ? index - width : -1,
          cy < height - 1 ? index + width : -1
        ];
        for (const next of neighbors) {
          if (next < 0 || seen[next] || mask[next] === 0) continue;
          seen[next] = 1;
          queue.push(next);
        }
      }
      if (count >= minPixels) {
        boxes.push({ left: minX, top: minY, right: maxX + 1, bottom: maxY + 1, count });
      }
    }
  }
  return boxes;
}

function getBrushPanelBoxes(width, height, brushPoints, pad) {
  if (!brushPoints.length) return [];
  const brushMask = new Uint8Array(width * height);
  applyBrushPointsToMask(brushMask, width, height, brushPoints);
  const minPixels = Math.max(90, Math.round((getCurrentBrushRadius() * getCurrentBrushRadius()) * 0.35));
  return findMaskComponentBoxes(brushMask, width, height, minPixels).map((box) => clampBox(box, width, height, pad));
}

function classifyPanelFromBox(box, width, height, sourceType = "auto") {
  const boxWidth = Math.max(1, box.right - box.left);
  const boxHeight = Math.max(1, box.bottom - box.top);
  const widthRatio = boxWidth / Math.max(1, width);
  const heightRatio = boxHeight / Math.max(1, height);
  const aspect = boxWidth / Math.max(1, boxHeight);
  const isThinHorizontal = aspect >= 4 && heightRatio <= 0.18;
  const isThinVertical = aspect <= 0.35 && widthRatio <= 0.16;
  const isCompactPanel = widthRatio >= 0.1 && widthRatio <= 0.75 && heightRatio >= 0.08 && heightRatio <= 0.45;
  const likelyUi = sourceType !== "auto" || isThinHorizontal || isThinVertical || isCompactPanel;
  let label = "Likely UI asset";
  if (sourceType === "keep-box") label = "Protected UI box";
  else if (sourceType === "brush") label = "Brushed UI detail";
  else if (sourceType === "auto" && !likelyUi) label = "Possible scenery fragment";

  return {
    sourceType,
    likelyUi,
    label,
    aspect: Number(aspect.toFixed(2))
  };
}

function getPanelUsefulnessScore(panel) {
  const width = panel.canvas.width;
  const height = panel.canvas.height;
  const area = width * height;
  const aspect = width / Math.max(1, height);
  let score = 0;

  if (panel.likelyUi) score += 1200;
  if (panel.sourceType === "keep-box") score += 900;
  else if (panel.sourceType === "brush") score += 700;
  else if (panel.sourceType === "auto") score += 250;

  if (aspect >= 4 || aspect <= 0.35) score += 240;
  else if (aspect >= 2 || aspect <= 0.6) score += 120;

  if (area >= 900000) score += 180;
  else if (area >= 240000) score += 110;
  else if (area >= 60000) score += 50;

  return score;
}

function sortPanelsForGallery(panels) {
  const sourceRank = { "keep-box": 0, "brush": 1, "auto": 2 };
  const sorted = [...panels];
  sorted.sort((a, b) => {
    if (splitPanelSortMode === "area") {
      return (b.panel.canvas.width * b.panel.canvas.height) - (a.panel.canvas.width * a.panel.canvas.height);
    }
    if (splitPanelSortMode === "source") {
      return (sourceRank[a.panel.sourceType] ?? 9) - (sourceRank[b.panel.sourceType] ?? 9)
        || (b.panel.canvas.width * b.panel.canvas.height) - (a.panel.canvas.width * a.panel.canvas.height);
    }
    return getPanelUsefulnessScore(b.panel) - getPanelUsefulnessScore(a.panel)
      || (b.panel.canvas.width * b.panel.canvas.height) - (a.panel.canvas.width * a.panel.canvas.height);
  });
  return sorted;
}

function snapBoxToNearbyContent(box, imageData, backgroundSamples) {
  if (!backgroundSamples.length) return normalizeBox(box);
  const normalized = normalizeBox(box);
  const { width, height, data } = imageData;
  const margin = 24;
  const searchLeft = Math.max(0, normalized.left - margin);
  const searchTop = Math.max(0, normalized.top - margin);
  const searchRight = Math.min(width, normalized.right + margin);
  const searchBottom = Math.min(height, normalized.bottom + margin);
  const threshold = 26;

  function rowForegroundRatio(y) {
    let hits = 0;
    for (let x = searchLeft; x < searchRight; x += 2) {
      const offset = (y * width + x) * 4;
      let minDistance = Number.POSITIVE_INFINITY;
      for (const sample of backgroundSamples) {
        const candidate = getColorDistance(data[offset], data[offset + 1], data[offset + 2], sample);
        if (candidate < minDistance) minDistance = candidate;
      }
      if (minDistance > threshold) hits += 1;
    }
    return hits / Math.max(1, Math.ceil((searchRight - searchLeft) / 2));
  }

  function colForegroundRatio(x) {
    let hits = 0;
    for (let y = searchTop; y < searchBottom; y += 2) {
      const offset = (y * width + x) * 4;
      let minDistance = Number.POSITIVE_INFINITY;
      for (const sample of backgroundSamples) {
        const candidate = getColorDistance(data[offset], data[offset + 1], data[offset + 2], sample);
        if (candidate < minDistance) minDistance = candidate;
      }
      if (minDistance > threshold) hits += 1;
    }
    return hits / Math.max(1, Math.ceil((searchBottom - searchTop) / 2));
  }

  let top = normalized.top;
  for (let y = searchTop; y < normalized.bottom; y += 1) {
    if (rowForegroundRatio(y) >= 0.18) {
      top = y;
      break;
    }
  }
  let bottom = normalized.bottom;
  for (let y = searchBottom - 1; y >= normalized.top; y -= 1) {
    if (rowForegroundRatio(y) >= 0.18) {
      bottom = y + 1;
      break;
    }
  }
  let left = normalized.left;
  for (let x = searchLeft; x < normalized.right; x += 1) {
    if (colForegroundRatio(x) >= 0.12) {
      left = x;
      break;
    }
  }
  let right = normalized.right;
  for (let x = searchRight - 1; x >= normalized.left; x -= 1) {
    if (colForegroundRatio(x) >= 0.12) {
      right = x + 1;
      break;
    }
  }

  return normalizeBox({ left, top, right, bottom });
}

function applySubtractBoxesToAlpha(alpha, width, height, boxes) {
  for (const rawBox of boxes) {
    const box = normalizeBox(rawBox);
    const left = Math.max(0, Math.min(width - 1, box.left));
    const top = Math.max(0, Math.min(height - 1, box.top));
    const right = Math.max(left + 1, Math.min(width, box.right));
    const bottom = Math.max(top + 1, Math.min(height, box.bottom));
    for (let y = top; y < bottom; y += 1) {
      for (let x = left; x < right; x += 1) {
        alpha[y * width + x] = 0;
      }
    }
  }
  return alpha;
}

function findVisibleBoundsFromImageData(imageData, alphaThreshold = 8) {
  const { width, height, data } = imageData;
  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const alpha = data[(y * width + x) * 4 + 3];
      if (alpha < alphaThreshold) continue;
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    }
  }
  if (maxX < 0) return { left: 0, top: 0, right: width, bottom: height, width, height };
  return { left: minX, top: minY, right: maxX + 1, bottom: maxY + 1, width: maxX - minX + 1, height: maxY - minY + 1 };
}

function autoDetectUiBoxesFromImage(imageData) {
  const bounds = findVisibleBoundsFromImageData(imageData);
  const { left, top, width, height } = bounds;
  const boxes = [];

  if (width < 120 || height < 120) return boxes;

  boxes.push({
    left: left + Math.round(width * 0.01),
    top: top + Math.round(height * 0.01),
    right: left + Math.round(width * 0.985),
    bottom: top + Math.round(height * 0.095)
  });

  boxes.push({
    left: left + Math.round(width * 0.015),
    top: top + Math.round(height * 0.76),
    right: left + Math.round(width * 0.98),
    bottom: top + Math.round(height * 0.995)
  });

  boxes.push({
    left: left + Math.round(width * 0.0),
    top: top + Math.round(height * 0.68),
    right: left + Math.round(width * 0.16),
    bottom: top + Math.round(height * 0.995)
  });

  boxes.push({
    left: left + Math.round(width * 0.62),
    top: top + Math.round(height * 0.72),
    right: left + Math.round(width * 0.985),
    bottom: top + Math.round(height * 0.99)
  });

  return boxes
    .map((box) => normalizeBox(box))
    .filter((box) => (box.right - box.left) >= 24 && (box.bottom - box.top) >= 24);
}

async function buildFloodFillAlphaData(imageData, settings, backgroundSamples, onProgress) {
  const { width, height, data } = imageData;
  const total = width * height;
  const alpha = new Uint8ClampedArray(total);
  alpha.fill(255);

  const visited = new Uint8Array(total);
  const queue = new Int32Array(total);
  let head = 0;
  let tail = 0;

  const seedThreshold = Math.max(24, Math.round(settings.threshold * 2 + settings.softness * 1.4 + 12));

  for (const sample of backgroundSamples) {
    const index = sample.y * width + sample.x;
    if (visited[index]) continue;
    visited[index] = 1;
    queue[tail++] = index;
    alpha[index] = 0;
  }

  const neighbors = [-1, 1, -width, width];
  const yieldEvery = 220000;
  let processed = 0;

  while (head < tail) {
    if (cancelProcessingRequested) throw new Error("Processing canceled.");
    const index = queue[head++];
    const x = index % width;
    const y = Math.floor(index / width);
    processed += 1;

    for (const delta of neighbors) {
      const next = index + delta;
      if (delta === -1 && x === 0) continue;
      if (delta === 1 && x === width - 1) continue;
      if (delta === -width && y === 0) continue;
      if (delta === width && y === height - 1) continue;
      if (visited[next]) continue;

      const offset = next * 4;
      let minDistanceSq = Number.POSITIVE_INFINITY;
      for (const sample of backgroundSamples) {
        const candidateSq = getColorDistanceSq(data[offset], data[offset + 1], data[offset + 2], sample);
        if (candidateSq < minDistanceSq) minDistanceSq = candidateSq;
      }

      if (Math.sqrt(minDistanceSq) <= seedThreshold) {
        visited[next] = 1;
        alpha[next] = 0;
        queue[tail++] = next;
      }
    }

    if (processed % yieldEvery === 0) {
      if (onProgress) onProgress(Math.round((head / Math.max(1, tail)) * 100));
      await new Promise((resolve) => setTimeout(resolve, 0));
    }
  }

  const edgeBand = Math.max(6, Math.round(settings.softness * 0.6));
  const edgeBandSq = edgeBand * edgeBand;
  const chunkSize = 180000;
  for (let start = 0; start < total; start += chunkSize) {
    if (cancelProcessingRequested) throw new Error("Processing canceled.");
    const end = Math.min(total, start + chunkSize);
    for (let i = start; i < end; i += 1) {
      if (alpha[i] === 0) continue;
      const x = i % width;
      const y = Math.floor(i / width);
      let touchesBackground = false;
      if (x > 0 && alpha[i - 1] === 0) touchesBackground = true;
      else if (x < width - 1 && alpha[i + 1] === 0) touchesBackground = true;
      else if (y > 0 && alpha[i - width] === 0) touchesBackground = true;
      else if (y < height - 1 && alpha[i + width] === 0) touchesBackground = true;
      if (!touchesBackground) continue;

      const offset = i * 4;
      let minDistanceSq = Number.POSITIVE_INFINITY;
      for (const sample of backgroundSamples) {
        const candidateSq = getColorDistanceSq(data[offset], data[offset + 1], data[offset + 2], sample);
        if (candidateSq < minDistanceSq) minDistanceSq = candidateSq;
      }

      if (minDistanceSq <= edgeBandSq) {
        alpha[i] = Math.max(alpha[i], 128 + Math.round((Math.sqrt(minDistanceSq) / Math.max(1, edgeBand)) * 127));
      }
    }
    if (onProgress) onProgress(100);
    await new Promise((resolve) => setTimeout(resolve, 0));
  }

  return alpha;
}

async function buildAlphaData(imageData, settings, backgroundSamples, onProgress) {
  if (settings.mode === "multi" && backgroundSamples.length && Number.isFinite(backgroundSamples[0].x) && Number.isFinite(backgroundSamples[0].y)) {
    return buildFloodFillAlphaData(imageData, settings, backgroundSamples, onProgress);
  }
  const conservativeThreshold = settings.secondPass
    ? Math.max(0, Math.round(settings.threshold * 0.68))
    : settings.threshold;
  const conservativeSoftness = settings.secondPass
    ? Math.max(1, Math.round(settings.softness * 1.25))
    : settings.softness;
  const lowerAlphaFloor = settings.secondPass
    ? Math.max(0, settings.alphaFloor - 6)
    : settings.alphaFloor;
  const { alphaCeiling } = settings;
  const upper = conservativeThreshold + Math.max(conservativeSoftness, 1);
  const thresholdSq = conservativeThreshold * conservativeThreshold;
  const upperSq = upper * upper;
  const alpha = new Uint8ClampedArray(imageData.width * imageData.height);
  const src = imageData.data;
  const chunkSize = 180000;
  for (let start = 0; start < alpha.length; start += chunkSize) {
    if (cancelProcessingRequested) throw new Error("Processing canceled.");
    const end = Math.min(alpha.length, start + chunkSize);
    for (let i = start; i < end; i += 1) {
      const offset = i * 4;
      let distanceSq = Number.POSITIVE_INFINITY;
      for (const sample of backgroundSamples) {
        const candidateSq = getColorDistanceSq(src[offset], src[offset + 1], src[offset + 2], sample);
        if (candidateSq < distanceSq) distanceSq = candidateSq;
      }
      let value = 0;
      if (distanceSq <= thresholdSq) value = 0;
      else if (distanceSq >= upperSq) value = 255;
      else value = Math.round(255 * (Math.sqrt(distanceSq) - conservativeThreshold) / (upper - conservativeThreshold));
      if (settings.secondPass && value < 255) {
        value = Math.min(255, Math.round(value * 1.08));
      }
      if (value <= lowerAlphaFloor) value = 0;
      if (value >= alphaCeiling) value = 255;
      alpha[i] = value;
    }
    if (onProgress) onProgress(Math.round((end / alpha.length) * 100));
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  return alpha;
}

async function refineAlphaData(alpha, width, height, settings, onProgress) {
  const refined = new Uint8ClampedArray(alpha.length);
  const rowChunk = 48;
  for (let startY = 0; startY < height; startY += rowChunk) {
    if (cancelProcessingRequested) throw new Error("Processing canceled.");
    const endY = Math.min(height, startY + rowChunk);
    for (let y = startY; y < endY; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const index = y * width + x;
        const current = alpha[index];
        if (current === 0 || current === 255) {
          refined[index] = current;
          continue;
        }

        let total = current;
        let count = 1;
        let solidNeighbors = current >= settings.componentAlpha ? 1 : 0;
        let emptyNeighbors = current <= settings.alphaFloor ? 1 : 0;
        let strongEmptyNeighbors = current <= Math.max(2, settings.alphaFloor >> 1) ? 1 : 0;

        for (let ny = Math.max(0, y - 1); ny <= Math.min(height - 1, y + 1); ny += 1) {
          for (let nx = Math.max(0, x - 1); nx <= Math.min(width - 1, x + 1); nx += 1) {
            if (nx === x && ny === y) continue;
            const neighbor = alpha[ny * width + nx];
            total += neighbor;
            count += 1;
            if (neighbor >= settings.componentAlpha) solidNeighbors += 1;
            if (neighbor <= settings.alphaFloor) emptyNeighbors += 1;
            if (neighbor <= Math.max(2, settings.alphaFloor >> 1)) strongEmptyNeighbors += 1;
          }
        }

        let value = Math.round(total / count);
        if (solidNeighbors >= 5) value = Math.max(value, Math.min(255, current + 20));
        if (emptyNeighbors >= 6) value = Math.min(value, Math.max(0, current - 38));
        if (strongEmptyNeighbors >= 5) value = Math.min(value, Math.max(0, current - 64));
        if (current < settings.componentAlpha && solidNeighbors <= 2 && emptyNeighbors >= 4) {
          value = Math.min(value, Math.max(0, current - 52));
        }
        if (value <= settings.alphaFloor) value = 0;
        if (value >= settings.alphaCeiling) value = 255;
        refined[index] = value;
      }
    }
    if (onProgress) onProgress(Math.round((endY / height) * 100));
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  return refined;
}

function applyAlphaToImage(imageData, alpha, decontaminate, backgroundSample, alphaSnap = 220, preserveColor = false) {
  const result = new ImageData(imageData.width, imageData.height);
  const src = imageData.data;
  const dst = result.data;
  for (let i = 0; i < alpha.length; i += 1) {
    const offset = i * 4;
    const a = alpha[i];
    if (a === 0) {
      dst[offset] = 0;
      dst[offset + 1] = 0;
      dst[offset + 2] = 0;
      dst[offset + 3] = 0;
      continue;
    }
    let r = src[offset];
    let g = src[offset + 1];
    let b = src[offset + 2];
    if (decontaminate && a > 0 && a < 255) {
      const alphaRatio = Math.max(0.01, a / 255);
      const cleanR = Math.min(255, Math.max(0, Math.round((r - backgroundSample.r * (1 - alphaRatio)) / alphaRatio)));
      const cleanG = Math.min(255, Math.max(0, Math.round((g - backgroundSample.g * (1 - alphaRatio)) / alphaRatio)));
      const cleanB = Math.min(255, Math.max(0, Math.round((b - backgroundSample.b * (1 - alphaRatio)) / alphaRatio)));

      if (preserveColor) {
        const edgeBlend = Math.max(0, Math.min(1, (240 - a) / 120));
        r = Math.round((r * (1 - edgeBlend)) + (cleanR * edgeBlend));
        g = Math.round((g * (1 - edgeBlend)) + (cleanG * edgeBlend));
        b = Math.round((b * (1 - edgeBlend)) + (cleanB * edgeBlend));
      } else {
        r = cleanR;
        g = cleanG;
        b = cleanB;
      }
    }
    dst[offset] = r;
    dst[offset + 1] = g;
    dst[offset + 2] = b;
    dst[offset + 3] = a >= alphaSnap ? 255 : a;
  }
  return result;
}

function buildProcessedBackgroundFromAlpha(sourceCanvas, sourceData, alpha, settings, backgroundSamples) {
  const resultData = applyAlphaToImage(
    sourceData,
    alpha,
    settings.decontaminate,
    backgroundSamples[0],
    settings.componentAlpha,
    settings.preserveColor
  );
  if (settings.decontaminate) {
    const cleanupPasses = settings.edgeCleanupStrength >= 80
      ? 3
      : settings.edgeCleanupStrength >= 45
        ? 2
        : 1;
    for (let pass = 0; pass < cleanupPasses; pass += 1) {
      defringeImageData(resultData, backgroundSamples[0]);
      scrubBrightSpecks(resultData, backgroundSamples[0]);
      repairOpaqueEdgePixels(resultData, backgroundSamples[0]);
    }
    if (settings.tone === "light") {
      const lightRepairPasses = settings.edgeCleanupStrength >= 80
        ? 3
        : settings.edgeCleanupStrength >= 45
          ? 2
          : 1;
      for (let pass = 0; pass < lightRepairPasses; pass += 1) {
        structureGuidedEdgePull(resultData, backgroundSamples[0]);
        removeOpaqueOutlierSpecks(resultData, backgroundSamples[0]);
        propagateBorderNeighborColors(resultData, backgroundSamples[0]);
        medianRepairLightEdges(resultData, backgroundSamples[0]);
      }
      if (settings.strongBorderRepair) {
        repairOpaqueEdgePixels(resultData, backgroundSamples[0]);
        structureGuidedEdgePull(resultData, backgroundSamples[0]);
        propagateBorderNeighborColors(resultData, backgroundSamples[0]);
        medianRepairLightEdges(resultData, backgroundSamples[0]);
        removeOpaqueOutlierSpecks(resultData, backgroundSamples[0]);
      }
    }
  }
  const fullLayoutCanvas = createCanvas(sourceCanvas.width, sourceCanvas.height);
  fullLayoutCanvas.getContext("2d").putImageData(resultData, 0, 0);
  const layoutCanvas = settings.cropTransparent ? cropToVisibleCanvas(fullLayoutCanvas) : fullLayoutCanvas;
  let resultCanvasLocal = layoutCanvas;
  const rawBoxes = findComponentBoxes(alpha, sourceCanvas.width, sourceCanvas.height, settings.componentPixels, settings.componentAlpha);
  const { accepted: boxes, rejected } = filterComponentBoxes(
    rawBoxes,
    sourceCanvas.width,
    sourceCanvas.height,
    settings.manualKeepSamples,
    settings.manualKeepBoxes,
    settings.manualKeepBrushPoints
  );
  let keepMask = buildKeepMask(
    sourceCanvas.width,
    sourceCanvas.height,
    settings.manualKeepSamples,
    alpha,
    Math.max(24, settings.componentAlpha - 72)
  );
  if (settings.manualKeepBoxes.length) {
    keepMask = applyKeepBoxesToMask(keepMask, sourceCanvas.width, sourceCanvas.height, settings.manualKeepBoxes);
  }
  if (settings.manualKeepBrushPoints.length) {
    keepMask = applyBrushPointsToMask(keepMask, sourceCanvas.width, sourceCanvas.height, settings.manualKeepBrushPoints);
  }
  if (settings.mode === "multi" && (settings.manualKeepSamples.length || settings.manualKeepBoxes.length || settings.manualKeepBrushPoints.length)) {
    resultCanvasLocal = compositeKeepMask(
      resultData,
      alpha,
      keepMask,
      sourceCanvas.width,
      sourceCanvas.height,
      settings.componentAlpha
    );
    if (settings.cropTransparent) resultCanvasLocal = cropToVisibleCanvas(resultCanvasLocal);
  } else if (boxes.length) {
    resultCanvasLocal = compositeAcceptedBoxes(
      resultData,
      alpha,
      boxes,
      sourceCanvas.width,
      sourceCanvas.height,
      settings.componentAlpha
    );
    if (settings.cropTransparent) resultCanvasLocal = cropToVisibleCanvas(resultCanvasLocal);
  }
  const autoPanelSourceBoxes = settings.mode === "multi" && (settings.manualKeepSamples.length || settings.manualKeepBoxes.length || settings.manualKeepBrushPoints.length)
    ? boxes.filter((box) =>
      settings.manualKeepSamples.some((sample) => sample.x >= box.left && sample.x < box.right && sample.y >= box.top && sample.y < box.bottom)
      || settings.manualKeepBoxes.some((keepBox) => {
        const normalized = normalizeBox(keepBox);
        return !(normalized.right <= box.left || normalized.left >= box.right || normalized.bottom <= box.top || normalized.top >= box.bottom);
      })
      || settings.manualKeepBrushPoints.some((point) => point.x >= box.left && point.x < box.right && point.y >= box.top && point.y < box.bottom))
    : boxes;
  const manualPanelBoxes = settings.mode === "multi" && settings.manualKeepBoxes.length
    ? getManualKeepPanelBoxes(sourceCanvas.width, sourceCanvas.height, settings.manualKeepBoxes, settings.componentPad)
    : [];
  const brushPanelBoxes = settings.mode === "multi" && settings.manualKeepBrushPoints.length
    ? getBrushPanelBoxes(sourceCanvas.width, sourceCanvas.height, settings.manualKeepBrushPoints, settings.componentPad)
    : [];
  const panelSourceBoxes = [
    ...autoPanelSourceBoxes.map((box) => ({ ...box, sourceType: "auto" })),
    ...manualPanelBoxes.map((box) => ({ ...box, sourceType: "keep-box" })),
    ...brushPanelBoxes.map((box) => ({ ...box, sourceType: "brush" }))
  ];
  const seenPanelKeys = new Set();
  const uniquePanelBoxes = panelSourceBoxes.filter((box) => {
    const key = `${box.left}:${box.top}:${box.right}:${box.bottom}`;
    if (seenPanelKeys.has(key)) return false;
    const overlapsSubtract = settings.manualSubtractBoxes.some((subtractBox) => {
      const normalized = normalizeBox(subtractBox);
      return !(normalized.right <= box.left || normalized.left >= box.right || normalized.bottom <= box.top || normalized.top >= box.bottom);
    });
    if (overlapsSubtract) return false;
    seenPanelKeys.add(key);
    return true;
  });
  const panels = uniquePanelBoxes.map((box) => {
    const paddedBox = clampBox(box, sourceCanvas.width, sourceCanvas.height, settings.componentPad);
    const classification = classifyPanelFromBox(paddedBox, sourceCanvas.width, sourceCanvas.height, box.sourceType || "auto");
    return {
      canvas: buildMaskedCropFromOriginal(resultData, alpha, paddedBox, settings.componentAlpha),
      fullCanvas: buildMaskedFullCanvasFromOriginal(resultData, alpha, paddedBox, settings.componentAlpha),
      label: classification.label,
      likelyUi: classification.likelyUi,
      sourceType: classification.sourceType,
      aspect: classification.aspect
    };
  });
  return {
    canvas: resultCanvasLocal,
    layoutCanvas,
    maskCanvas: createMaskCanvasFromAlpha(alpha, sourceCanvas.width, sourceCanvas.height),
    alpha,
    panels,
    status: panels.length
      ? `Done. Kept ${panels.length} UI component${panels.length === 1 ? "" : "s"} and rejected ${rejected.length} rough fragment${rejected.length === 1 ? "" : "s"}.`
      : "Done. No distinct split panels were found.",
  };
}

function defringeImageData(imageData, backgroundSample) {
  const { width, height, data } = imageData;
  const source = new Uint8ClampedArray(data);
  const backgroundLuma = ((backgroundSample.r * 0.2126) + (backgroundSample.g * 0.7152) + (backgroundSample.b * 0.0722));

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const index = y * width + x;
      const offset = index * 4;
      const alpha = source[offset + 3];
      if (alpha === 0) continue;

      let touchesOuterEdge = false;
      const neighbors = [
        x > 0 ? index - 1 : -1,
        x < width - 1 ? index + 1 : -1,
        y > 0 ? index - width : -1,
        y < height - 1 ? index + width : -1
      ];
      for (const neighbor of neighbors) {
        if (neighbor < 0) {
          touchesOuterEdge = true;
          break;
        }
        if (source[(neighbor * 4) + 3] < 245) {
          touchesOuterEdge = true;
          break;
        }
      }
      if (!touchesOuterEdge) continue;

      let sumR = 0;
      let sumG = 0;
      let sumB = 0;
      let samples = 0;
      for (let dy = -3; dy <= 3; dy += 1) {
        for (let dx = -3; dx <= 3; dx += 1) {
          if (dx === 0 && dy === 0) continue;
          const nx = x + dx;
          const ny = y + dy;
          if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue;
          const neighborOffset = ((ny * width) + nx) * 4;
          const neighborAlpha = source[neighborOffset + 3];
          if (neighborAlpha < 250) continue;
          const neighborDistance = getColorDistance(
            source[neighborOffset],
            source[neighborOffset + 1],
            source[neighborOffset + 2],
            backgroundSample
          );
          if (neighborDistance < 26) continue;
          sumR += source[neighborOffset];
          sumG += source[neighborOffset + 1];
          sumB += source[neighborOffset + 2];
          samples += 1;
        }
      }
      if (samples < 2) continue;

      const avgR = Math.round(sumR / samples);
      const avgG = Math.round(sumG / samples);
      const avgB = Math.round(sumB / samples);
      const avgDistance = getColorDistance(avgR, avgG, avgB, backgroundSample);
      const srcDistance = getColorDistance(source[offset], source[offset + 1], source[offset + 2], backgroundSample);
      const srcLuma = ((source[offset] * 0.2126) + (source[offset + 1] * 0.7152) + (source[offset + 2] * 0.0722));
      const avgLuma = ((avgR * 0.2126) + (avgG * 0.7152) + (avgB * 0.0722));
      const looksBackgroundLike = srcDistance < Math.max(28, avgDistance * 0.72);
      const looksTooBright = srcLuma > avgLuma + 10 && srcLuma > backgroundLuma - 12;
      const matteContaminated = looksBackgroundLike || looksTooBright;
      const edgeBlend = matteContaminated
        ? (alpha >= 245 ? 1 : alpha >= 192 ? 0.94 : 0.82)
        : (alpha >= 245 ? 0.9 : alpha >= 192 ? 0.78 : 0.62);

      data[offset] = Math.round((source[offset] * (1 - edgeBlend)) + (avgR * edgeBlend));
      data[offset + 1] = Math.round((source[offset + 1] * (1 - edgeBlend)) + (avgG * edgeBlend));
      data[offset + 2] = Math.round((source[offset + 2] * (1 - edgeBlend)) + (avgB * edgeBlend));
    }
  }

  return imageData;
}

function scrubBrightSpecks(imageData, backgroundSample) {
  const { width, height, data } = imageData;
  const source = new Uint8ClampedArray(data);

  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      const index = y * width + x;
      const offset = index * 4;
      const alpha = source[offset + 3];
      if (alpha < 235) continue;

      const srcDistance = getColorDistance(source[offset], source[offset + 1], source[offset + 2], backgroundSample);
      if (srcDistance > 26) continue;

      let transparentNeighbors = 0;
      let sumR = 0;
      let sumG = 0;
      let sumB = 0;
      let samples = 0;

      for (let dy = -1; dy <= 1; dy += 1) {
        for (let dx = -1; dx <= 1; dx += 1) {
          if (dx === 0 && dy === 0) continue;
          const neighborOffset = (((y + dy) * width) + (x + dx)) * 4;
          const neighborAlpha = source[neighborOffset + 3];
          if (neighborAlpha < 80) {
            transparentNeighbors += 1;
            continue;
          }
          const neighborDistance = getColorDistance(
            source[neighborOffset],
            source[neighborOffset + 1],
            source[neighborOffset + 2],
            backgroundSample
          );
          if (neighborDistance < 28) continue;
          sumR += source[neighborOffset];
          sumG += source[neighborOffset + 1];
          sumB += source[neighborOffset + 2];
          samples += 1;
        }
      }

      if (transparentNeighbors < 2 || samples < 3) continue;

      data[offset] = Math.round(sumR / samples);
      data[offset + 1] = Math.round(sumG / samples);
      data[offset + 2] = Math.round(sumB / samples);
    }
  }

  return imageData;
}

function repairOpaqueEdgePixels(imageData, backgroundSample) {
  const { width, height, data } = imageData;
  const source = new Uint8ClampedArray(data);

  const isOuterEdgePixel = (x, y) => {
    const index = y * width + x;
    const offset = index * 4;
    if (source[offset + 3] < 235) return false;
    const neighbors = [
      x > 0 ? ((index - 1) * 4) + 3 : -1,
      x < width - 1 ? ((index + 1) * 4) + 3 : -1,
      y > 0 ? ((index - width) * 4) + 3 : -1,
      y < height - 1 ? ((index + width) * 4) + 3 : -1
    ];
    return neighbors.some((alphaOffset) => alphaOffset < 0 || source[alphaOffset] < 180);
  };

  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      if (!isOuterEdgePixel(x, y)) continue;

      const index = y * width + x;
      const offset = index * 4;
      const srcR = source[offset];
      const srcG = source[offset + 1];
      const srcB = source[offset + 2];
      const srcDistance = getColorDistance(srcR, srcG, srcB, backgroundSample);

      let sumR = 0;
      let sumG = 0;
      let sumB = 0;
      let samples = 0;

      for (let radius = 1; radius <= 5; radius += 1) {
        for (let dy = -radius; dy <= radius; dy += 1) {
          for (let dx = -radius; dx <= radius; dx += 1) {
            if (Math.abs(dx) !== radius && Math.abs(dy) !== radius) continue;
            const nx = x + dx;
            const ny = y + dy;
            if (nx < 1 || ny < 1 || nx >= width - 1 || ny >= height - 1) continue;
            if (isOuterEdgePixel(nx, ny)) continue;

            const neighborIndex = ny * width + nx;
            const neighborOffset = neighborIndex * 4;
            const neighborAlpha = source[neighborOffset + 3];
            if (neighborAlpha < 245) continue;

            const neighborDistance = getColorDistance(
              source[neighborOffset],
              source[neighborOffset + 1],
              source[neighborOffset + 2],
              backgroundSample
            );
            if (neighborDistance < 30) continue;

            sumR += source[neighborOffset];
            sumG += source[neighborOffset + 1];
            sumB += source[neighborOffset + 2];
            samples += 1;
          }
        }
        if (samples >= 6) break;
      }

      if (samples < 3) continue;

      const avgR = Math.round(sumR / samples);
      const avgG = Math.round(sumG / samples);
      const avgB = Math.round(sumB / samples);
      const candidateDistance = getColorDistance(avgR, avgG, avgB, backgroundSample);
      const drift = getColorDistance(srcR, srcG, srcB, { r: avgR, g: avgG, b: avgB });
      const currentLuma = (srcR * 0.2126) + (srcG * 0.7152) + (srcB * 0.0722);
      const candidateLuma = (avgR * 0.2126) + (avgG * 0.7152) + (avgB * 0.0722);
      const contaminated = srcDistance < Math.max(32, candidateDistance * 0.75)
        || drift > 22
        || Math.abs(currentLuma - candidateLuma) > 18;

      if (!contaminated) continue;

      const blend = srcDistance < 24 ? 1 : drift > 34 ? 0.92 : 0.82;
      data[offset] = Math.round((srcR * (1 - blend)) + (avgR * blend));
      data[offset + 1] = Math.round((srcG * (1 - blend)) + (avgG * blend));
      data[offset + 2] = Math.round((srcB * (1 - blend)) + (avgB * blend));
    }
  }

  return imageData;
}

function structureGuidedEdgePull(imageData, backgroundSample) {
  const { width, height, data } = imageData;
  const source = new Uint8ClampedArray(data);
  const directions = [
    { dx: -1, dy: 0, inwardX: 1, inwardY: 0 },
    { dx: 1, dy: 0, inwardX: -1, inwardY: 0 },
    { dx: 0, dy: -1, inwardX: 0, inwardY: 1 },
    { dx: 0, dy: 1, inwardX: 0, inwardY: -1 }
  ];

  const getOffset = (x, y) => ((y * width) + x) * 4;

  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      const offset = getOffset(x, y);
      const alpha = source[offset + 3];
      if (alpha < 235) continue;

      const srcR = source[offset];
      const srcG = source[offset + 1];
      const srcB = source[offset + 2];
      const srcDistance = getColorDistance(srcR, srcG, srcB, backgroundSample);

      let sumR = 0;
      let sumG = 0;
      let sumB = 0;
      let samples = 0;
      let exposedSides = 0;

      for (const direction of directions) {
        const edgeX = x + direction.dx;
        const edgeY = y + direction.dy;
        const edgeOffset = getOffset(edgeX, edgeY);
        if (source[edgeOffset + 3] >= 180) continue;
        exposedSides += 1;

        for (let step = 1; step <= 8; step += 1) {
          const sampleX = x + (direction.inwardX * step);
          const sampleY = y + (direction.inwardY * step);
          if (sampleX < 1 || sampleY < 1 || sampleX >= width - 1 || sampleY >= height - 1) break;
          const sampleOffset = getOffset(sampleX, sampleY);
          const sampleAlpha = source[sampleOffset + 3];
          if (sampleAlpha < 245) continue;

          const sampleDistance = getColorDistance(
            source[sampleOffset],
            source[sampleOffset + 1],
            source[sampleOffset + 2],
            backgroundSample
          );
          if (sampleDistance < 28) continue;

          sumR += source[sampleOffset];
          sumG += source[sampleOffset + 1];
          sumB += source[sampleOffset + 2];
          samples += 1;
          break;
        }
      }

      if (exposedSides === 0 || samples < 1) continue;

      const avgR = Math.round(sumR / samples);
      const avgG = Math.round(sumG / samples);
      const avgB = Math.round(sumB / samples);
      const candidateDistance = getColorDistance(avgR, avgG, avgB, backgroundSample);
      const drift = getColorDistance(srcR, srcG, srcB, { r: avgR, g: avgG, b: avgB });
      const srcLuma = (srcR * 0.2126) + (srcG * 0.7152) + (srcB * 0.0722);
      const avgLuma = (avgR * 0.2126) + (avgG * 0.7152) + (avgB * 0.0722);
      const looksBackgroundLike = srcDistance < Math.max(30, candidateDistance * 0.78);
      const lumaMismatch = Math.abs(srcLuma - avgLuma) > 12;
      if (!looksBackgroundLike && !lumaMismatch && drift < 16) continue;

      const blend = exposedSides >= 2 ? 1 : looksBackgroundLike ? 0.94 : 0.82;
      data[offset] = Math.round((srcR * (1 - blend)) + (avgR * blend));
      data[offset + 1] = Math.round((srcG * (1 - blend)) + (avgG * blend));
      data[offset + 2] = Math.round((srcB * (1 - blend)) + (avgB * blend));
    }
  }

  return imageData;
}

function removeOpaqueOutlierSpecks(imageData, backgroundSample) {
  const { width, height, data } = imageData;
  const source = new Uint8ClampedArray(data);

  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      const offset = ((y * width) + x) * 4;
      if (source[offset + 3] < 235) continue;

      const srcDistance = getColorDistance(source[offset], source[offset + 1], source[offset + 2], backgroundSample);
      if (srcDistance > 34) continue;

      let strongNeighbors = 0;
      let sumR = 0;
      let sumG = 0;
      let sumB = 0;

      for (let dy = -1; dy <= 1; dy += 1) {
        for (let dx = -1; dx <= 1; dx += 1) {
          if (dx === 0 && dy === 0) continue;
          const neighborOffset = ((((y + dy) * width) + (x + dx)) * 4);
          if (source[neighborOffset + 3] < 235) continue;
          const neighborDistance = getColorDistance(
            source[neighborOffset],
            source[neighborOffset + 1],
            source[neighborOffset + 2],
            backgroundSample
          );
          if (neighborDistance < 42) continue;
          strongNeighbors += 1;
          sumR += source[neighborOffset];
          sumG += source[neighborOffset + 1];
          sumB += source[neighborOffset + 2];
        }
      }

      if (strongNeighbors < 5) continue;

      data[offset] = Math.round(sumR / strongNeighbors);
      data[offset + 1] = Math.round(sumG / strongNeighbors);
      data[offset + 2] = Math.round(sumB / strongNeighbors);
    }
  }

  return imageData;
}

function propagateBorderNeighborColors(imageData, backgroundSample) {
  const { width, height, data } = imageData;
  const source = new Uint8ClampedArray(data);
  const getOffset = (x, y) => ((y * width) + x) * 4;

  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      const offset = getOffset(x, y);
      if (source[offset + 3] < 235) continue;

      let touchesTransparency = false;
      for (let dy = -1; dy <= 1 && !touchesTransparency; dy += 1) {
        for (let dx = -1; dx <= 1; dx += 1) {
          if (dx === 0 && dy === 0) continue;
          if (source[getOffset(x + dx, y + dy) + 3] < 180) {
            touchesTransparency = true;
            break;
          }
        }
      }
      if (!touchesTransparency) continue;

      const srcDistance = getColorDistance(source[offset], source[offset + 1], source[offset + 2], backgroundSample);
      if (srcDistance > 44) continue;

      let sumR = 0;
      let sumG = 0;
      let sumB = 0;
      let samples = 0;

      for (let dy = -1; dy <= 1; dy += 1) {
        for (let dx = -1; dx <= 1; dx += 1) {
          if (dx === 0 && dy === 0) continue;
          const neighborOffset = getOffset(x + dx, y + dy);
          if (source[neighborOffset + 3] < 235) continue;
          const neighborDistance = getColorDistance(
            source[neighborOffset],
            source[neighborOffset + 1],
            source[neighborOffset + 2],
            backgroundSample
          );
          if (neighborDistance < 44) continue;
          sumR += source[neighborOffset];
          sumG += source[neighborOffset + 1];
          sumB += source[neighborOffset + 2];
          samples += 1;
        }
      }

      if (samples < 3) continue;

      const avgR = Math.round(sumR / samples);
      const avgG = Math.round(sumG / samples);
      const avgB = Math.round(sumB / samples);
      data[offset] = avgR;
      data[offset + 1] = avgG;
      data[offset + 2] = avgB;
    }
  }

  return imageData;
}

function median(values) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

function medianRepairLightEdges(imageData, backgroundSample) {
  const { width, height, data } = imageData;
  const source = new Uint8ClampedArray(data);
  const getOffset = (x, y) => ((y * width) + x) * 4;

  for (let y = 2; y < height - 2; y += 1) {
    for (let x = 2; x < width - 2; x += 1) {
      const offset = getOffset(x, y);
      const alpha = source[offset + 3];
      if (alpha < 235) continue;

      let touchesTransparency = false;
      for (let dy = -1; dy <= 1 && !touchesTransparency; dy += 1) {
        for (let dx = -1; dx <= 1; dx += 1) {
          if (dx === 0 && dy === 0) continue;
          if (source[getOffset(x + dx, y + dy) + 3] < 180) {
            touchesTransparency = true;
            break;
          }
        }
      }
      if (!touchesTransparency) continue;

      const srcR = source[offset];
      const srcG = source[offset + 1];
      const srcB = source[offset + 2];
      const srcDistance = getColorDistance(srcR, srcG, srcB, backgroundSample);

      const rs = [];
      const gs = [];
      const bs = [];

      for (let dy = -2; dy <= 2; dy += 1) {
        for (let dx = -2; dx <= 2; dx += 1) {
          if (dx === 0 && dy === 0) continue;
          const neighborOffset = getOffset(x + dx, y + dy);
          const neighborAlpha = source[neighborOffset + 3];
          if (neighborAlpha < 245) continue;
          const neighborDistance = getColorDistance(
            source[neighborOffset],
            source[neighborOffset + 1],
            source[neighborOffset + 2],
            backgroundSample
          );
          if (neighborDistance < 46) continue;
          rs.push(source[neighborOffset]);
          gs.push(source[neighborOffset + 1]);
          bs.push(source[neighborOffset + 2]);
        }
      }

      if (rs.length < 5) continue;

      const medR = median(rs);
      const medG = median(gs);
      const medB = median(bs);
      const candidateDistance = getColorDistance(medR, medG, medB, backgroundSample);
      const drift = getColorDistance(srcR, srcG, srcB, { r: medR, g: medG, b: medB });

      if (srcDistance > Math.max(42, candidateDistance * 0.85) && drift < 18) continue;

      const blend = srcDistance < 28 ? 1 : drift > 24 ? 0.88 : 0.72;
      data[offset] = Math.round((srcR * (1 - blend)) + (medR * blend));
      data[offset + 1] = Math.round((srcG * (1 - blend)) + (medG * blend));
      data[offset + 2] = Math.round((srcB * (1 - blend)) + (medB * blend));
    }
  }

  return imageData;
}

function cropToVisibleCanvas(canvas, alphaThreshold = 1) {
  const imageData = canvas.getContext("2d").getImageData(0, 0, canvas.width, canvas.height).data;
  let minX = canvas.width;
  let minY = canvas.height;
  let maxX = -1;
  let maxY = -1;
  for (let y = 0; y < canvas.height; y += 1) {
    for (let x = 0; x < canvas.width; x += 1) {
      const offset = (y * canvas.width + x) * 4;
      if (imageData[offset + 3] >= alphaThreshold) {
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
      }
    }
  }
  if (maxX < 0) return canvas;
  const cropped = createCanvas(maxX - minX + 1, maxY - minY + 1);
  cropped.getContext("2d").drawImage(canvas, minX, minY, cropped.width, cropped.height, 0, 0, cropped.width, cropped.height);
  return cropped;
}

function clampBox(box, width, height, pad) {
  return { left: Math.max(0, box.left - pad), top: Math.max(0, box.top - pad), right: Math.min(width, box.right + pad), bottom: Math.min(height, box.bottom + pad) };
}

function cropBoxFromCanvas(canvas, box) {
  const cropped = createCanvas(box.right - box.left, box.bottom - box.top);
  cropped.getContext("2d").drawImage(canvas, box.left, box.top, cropped.width, cropped.height, 0, 0, cropped.width, cropped.height);
  return cropped;
}

function buildMaskedCropFromOriginal(imageData, alpha, box, alphaSnap = 220) {
  const width = box.right - box.left;
  const height = box.bottom - box.top;
  const cropped = createCanvas(width, height);
  const croppedData = new ImageData(width, height);
  const dst = croppedData.data;
  const src = imageData.data;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const srcX = box.left + x;
      const srcY = box.top + y;
      const srcIndex = srcY * imageData.width + srcX;
      const srcOffset = srcIndex * 4;
      const dstOffset = (y * width + x) * 4;
      const a = Math.max(src[srcOffset + 3], alpha[srcIndex] >= alphaSnap ? 255 : alpha[srcIndex]);

      dst[dstOffset] = src[srcOffset];
      dst[dstOffset + 1] = src[srcOffset + 1];
      dst[dstOffset + 2] = src[srcOffset + 2];
      dst[dstOffset + 3] = a;
    }
  }

  cropped.getContext("2d").putImageData(croppedData, 0, 0);
  return cropped;
}

function buildMaskedFullCanvasFromOriginal(imageData, alpha, box, alphaSnap = 220) {
  const fullCanvas = createCanvas(imageData.width, imageData.height);
  const fullData = new ImageData(imageData.width, imageData.height);
  const dst = fullData.data;
  const src = imageData.data;

  for (let y = box.top; y < box.bottom; y += 1) {
    for (let x = box.left; x < box.right; x += 1) {
      const index = y * imageData.width + x;
      const offset = index * 4;
      const a = Math.max(src[offset + 3], alpha[index] >= alphaSnap ? 255 : alpha[index]);
      if (a === 0) continue;
      dst[offset] = src[offset];
      dst[offset + 1] = src[offset + 1];
      dst[offset + 2] = src[offset + 2];
      dst[offset + 3] = a;
    }
  }

  fullCanvas.getContext("2d").putImageData(fullData, 0, 0);
  return fullCanvas;
}

function compositeAcceptedBoxes(imageData, alpha, boxes, width, height, alphaSnap = 220) {
  const composite = createCanvas(width, height);
  const compositeData = new ImageData(width, height);
  const dst = compositeData.data;
  const src = imageData.data;

  for (const box of boxes) {
    for (let y = box.top; y < box.bottom; y += 1) {
      for (let x = box.left; x < box.right; x += 1) {
        const index = y * width + x;
        const offset = index * 4;
        const a = Math.max(src[offset + 3], alpha[index] >= alphaSnap ? 255 : alpha[index]);
        if (a === 0) continue;
        dst[offset] = src[offset];
        dst[offset + 1] = src[offset + 1];
        dst[offset + 2] = src[offset + 2];
        dst[offset + 3] = a;
      }
    }
  }

  composite.getContext("2d").putImageData(compositeData, 0, 0);
  return composite;
}

function compositeKeepMask(imageData, alpha, keepMask, width, height, alphaSnap = 220) {
  const composite = createCanvas(width, height);
  const compositeData = new ImageData(width, height);
  const dst = compositeData.data;
  const src = imageData.data;

  for (let index = 0; index < keepMask.length; index += 1) {
    if (!keepMask[index]) continue;
    const offset = index * 4;
    const a = Math.max(src[offset + 3], alpha[index] >= alphaSnap ? 255 : alpha[index]);
    if (a === 0) continue;
    dst[offset] = src[offset];
    dst[offset + 1] = src[offset + 1];
    dst[offset + 2] = src[offset + 2];
    dst[offset + 3] = a;
  }

  composite.getContext("2d").putImageData(compositeData, 0, 0);
  return composite;
}

function findObjectBounds(imageData, settings, backgroundSample) {
  const { width, height, data } = imageData;
  const rowCounts = new Uint32Array(height);
  const colCounts = new Uint32Array(width);
  const cutoff = settings.threshold + Math.max(6, Math.round(settings.softness * 0.35));
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const offset = (y * width + x) * 4;
      const distance = getColorDistance(data[offset], data[offset + 1], data[offset + 2], backgroundSample);
      if (distance >= cutoff) {
        rowCounts[y] += 1;
        colCounts[x] += 1;
      }
    }
  }
  const minRowPixels = Math.max(8, Math.floor(width * 0.015));
  const minColPixels = Math.max(8, Math.floor(height * 0.015));
  let top = 0;
  while (top < height && rowCounts[top] < minRowPixels) top += 1;
  let bottom = height - 1;
  while (bottom >= 0 && rowCounts[bottom] < minRowPixels) bottom -= 1;
  let left = 0;
  while (left < width && colCounts[left] < minColPixels) left += 1;
  let right = width - 1;
  while (right >= 0 && colCounts[right] < minColPixels) right -= 1;
  if (top >= bottom || left >= right) {
    const fallbackPad = Math.round(Math.min(width, height) * 0.08);
    return { left: fallbackPad, top: fallbackPad, right: Math.max(fallbackPad + 1, width - fallbackPad), bottom: Math.max(fallbackPad + 1, height - fallbackPad) };
  }
  return { left, top, right: right + 1, bottom: bottom + 1 };
}

function processObjectCrop(sourceCanvas, sourceData, settings, backgroundSample) {
  const paddedBox = clampBox(findObjectBounds(sourceData, settings, backgroundSample), sourceCanvas.width, sourceCanvas.height, settings.objectPad);
  const cropped = cropBoxFromCanvas(sourceCanvas, paddedBox);
  const croppedData = cropped.getContext("2d").getImageData(0, 0, cropped.width, cropped.height);
  const alpha = new Uint8ClampedArray(cropped.width * cropped.height);
  for (let index = 0; index < alpha.length; index += 1) {
    alpha[index] = croppedData.data[index * 4 + 3];
  }
  return {
    canvas: cropped,
    layoutCanvas: cropped,
    maskCanvas: createMaskCanvasFromAlpha(alpha, cropped.width, cropped.height),
    alpha,
    panels: [{ canvas: cropped }],
    status: "Done. Tight object crop created."
  };
}

function findComponentBoxes(alpha, width, height, minPixels, alphaThreshold) {
  const seen = new Uint8Array(width * height);
  const boxes = [];
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const startIndex = y * width + x;
      if (seen[startIndex] || alpha[startIndex] < alphaThreshold) continue;
      const queue = [[x, y]];
      seen[startIndex] = 1;
      let head = 0;
      let count = 0;
      let minX = x;
      let minY = y;
      let maxX = x;
      let maxY = y;
      let touchesLeft = false;
      let touchesTop = false;
      let touchesRight = false;
      let touchesBottom = false;
      while (head < queue.length) {
        const [cx, cy] = queue[head++];
        count += 1;
        minX = Math.min(minX, cx);
        minY = Math.min(minY, cy);
        maxX = Math.max(maxX, cx);
        maxY = Math.max(maxY, cy);
        if (cx === 0) touchesLeft = true;
        if (cy === 0) touchesTop = true;
        if (cx === width - 1) touchesRight = true;
        if (cy === height - 1) touchesBottom = true;
        const neighbors = [[cx - 1, cy], [cx + 1, cy], [cx, cy - 1], [cx, cy + 1]];
        for (const [nx, ny] of neighbors) {
          if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue;
          const index = ny * width + nx;
          if (seen[index] || alpha[index] < alphaThreshold) continue;
          seen[index] = 1;
          queue.push([nx, ny]);
        }
      }
      if (count >= minPixels) {
        const boxWidth = maxX - minX + 1;
        const boxHeight = maxY - minY + 1;
        const area = boxWidth * boxHeight;
        boxes.push({
          left: minX,
          top: minY,
          right: maxX + 1,
          bottom: maxY + 1,
          area,
          count,
          width: boxWidth,
          height: boxHeight,
          solidity: count / Math.max(1, area),
          edgeTouches: Number(touchesLeft) + Number(touchesTop) + Number(touchesRight) + Number(touchesBottom)
        });
      }
    }
  }
  boxes.sort((a, b) => b.area - a.area);
  return boxes.slice(0, 8);
}

function filterComponentBoxes(boxes, width, height, keepSamples = [], keepBoxes = [], keepBrushPoints = []) {
  const totalArea = width * height;
  const accepted = [];
  const rejected = [];

  for (const box of boxes) {
    const widthRatio = box.width / width;
    const heightRatio = box.height / height;
    const areaRatio = box.area / totalArea;
    const isHuge = areaRatio > 0.24 || (widthRatio > 0.78 && heightRatio > 0.48);
    const isHorizontalBar = widthRatio >= 0.28 && heightRatio <= 0.18;
    const isVerticalBar = heightRatio >= 0.2 && widthRatio <= 0.18;
    const isPanelLike = widthRatio >= 0.12 && widthRatio <= 0.82 && heightRatio >= 0.08 && heightRatio <= 0.42;
    const isDenseEnough = box.solidity >= 0.12;
    const edgeHeavy = box.edgeTouches >= 2;
    const probablySceneFragment =
      (isHuge && edgeHeavy && box.solidity < 0.7) ||
      (box.edgeTouches >= 3 && box.solidity < 0.82) ||
      (heightRatio > 0.55 && widthRatio < 0.2) ||
      (widthRatio > 0.55 && heightRatio > 0.55);

    const keepPointInside = keepSamples.some((sample) => (
      sample.x >= box.left && sample.x < box.right && sample.y >= box.top && sample.y < box.bottom
    ));
    const keepBoxInside = keepBoxes.some((keepBox) => {
      const normalized = normalizeBox(keepBox);
      return !(normalized.right <= box.left || normalized.left >= box.right || normalized.bottom <= box.top || normalized.top >= box.bottom);
    });
    const keepBrushInside = keepBrushPoints.some((point) => (
      point.x >= box.left && point.x < box.right && point.y >= box.top && point.y < box.bottom
    ));

    const keep =
      keepPointInside ||
      keepBoxInside ||
      keepBrushInside ||
      !probablySceneFragment &&
      isDenseEnough &&
      (isHorizontalBar || isVerticalBar || isPanelLike);

    if (keep) accepted.push(box);
    else rejected.push(box);
  }

  accepted.sort((a, b) => {
    const aShape = (a.width / Math.max(1, a.height) > 2.4 || a.height / Math.max(1, a.width) > 2.8) ? 1 : 0;
    const bShape = (b.width / Math.max(1, b.height) > 2.4 || b.height / Math.max(1, b.width) > 2.8) ? 1 : 0;
    return (bShape - aShape) || (b.count - a.count);
  });

  return { accepted: accepted.slice(0, 8), rejected };
}

async function processBackgroundRemoval(sourceCanvas, sourceData, settings, backgroundSamples, onProgress) {
  let alpha = await buildAlphaData(sourceData, settings, backgroundSamples, onProgress
    ? (percent) => onProgress(settings.secondPass ? Math.round(percent * 0.72) : percent)
    : undefined);
  if (settings.secondPass) {
    alpha = await refineAlphaData(alpha, sourceCanvas.width, sourceCanvas.height, settings, onProgress
      ? (percent) => onProgress(72 + Math.round(percent * 0.28))
      : undefined);
  }
  if (settings.manualSubtractBoxes.length) {
    alpha = applySubtractBoxesToAlpha(alpha, sourceCanvas.width, sourceCanvas.height, settings.manualSubtractBoxes);
  }
  if (settings.manualRemoveBrushPoints.length) {
    alpha = applyBrushPointsToAlpha(alpha, sourceCanvas.width, sourceCanvas.height, settings.manualRemoveBrushPoints, 0);
  }
  return buildProcessedBackgroundFromAlpha(sourceCanvas, sourceData, alpha, settings, backgroundSamples);
}
function downloadCanvas(canvas, fileName) {
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    link.click();
    URL.revokeObjectURL(url);
  }, "image/png");
}

function promotePanelToMain(index) {
  if (index < 0 || index >= processedPanels.length || bgLayout.value !== "split") return;
  selectedPanelIndex = index;
  processedCanvas = getPanelDisplayCanvas(processedPanels[index]);
  drawImageOnCanvas(resultCanvas, processedCanvas);
  resultMeta.textContent = `Panel ${index + 1} | ${processedCanvas.width} x ${processedCanvas.height}`;
  renderSplitLinks();
}

function renderSplitLinks() {
  if (!processedPanels.length) {
    splitLinks.innerHTML = "No split panels exported yet.";
    splitLinks.classList.add("empty-state");
    updateSplitFilterButtons();
    updateSplitPanelThresholdLabel();
    return;
  }
  const filteredPanels = splitPanelFilter === "likely"
    ? processedPanels
        .map((panel, index) => ({ panel, index }))
        .filter(({ panel }) => panel.likelyUi)
    : processedPanels.map((panel, index) => ({ panel, index }));
  const sizeFilteredPanels = filteredPanels.filter(({ panel }) => (panel.canvas.width * panel.canvas.height) >= splitPanelMinPixels);
  const sortedPanels = sortPanelsForGallery(sizeFilteredPanels);

  if (!filteredPanels.length) {
    splitLinks.innerHTML = "No likely UI panels matched the current filter. Switch to 'Show all panels' to inspect everything.";
    splitLinks.classList.add("empty-state");
    updateSplitFilterButtons();
    updateSplitPanelThresholdLabel();
    return;
  }
  if (!sizeFilteredPanels.length) {
    splitLinks.innerHTML = `All panels are below the current fragment filter (${splitPanelMinPixels} px). Lower the threshold or switch to 'Show all panels'.`;
    splitLinks.classList.add("empty-state");
    updateSplitFilterButtons();
    updateSplitPanelThresholdLabel();
    return;
  }

  splitLinks.classList.remove("empty-state");
  splitLinks.innerHTML = "";
  sortedPanels.forEach(({ panel, index }) => {
    const card = document.createElement("div");
    const displayCanvas = getPanelDisplayCanvas(panel);
    card.className = `split-card${index === selectedPanelIndex ? " split-card-active" : ""}${panel.likelyUi ? "" : " split-card-warning"}`;
    if (bgLayout.value === "split") {
      card.addEventListener("click", () => promotePanelToMain(index));
    }

    const header = document.createElement("div");
    header.className = "split-card-head";
    const labelWrap = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = `Panel ${index + 1}`;
    const meta = document.createElement("span");
    meta.className = "split-card-meta";
    meta.textContent = `${displayCanvas.width} x ${displayCanvas.height}`;
    const badge = document.createElement("span");
    badge.className = `split-card-badge${panel.likelyUi ? "" : " split-card-badge-warning"}`;
    badge.textContent = panel.label || "Panel";
    labelWrap.append(title, meta);
    labelWrap.append(badge);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "ghost-button split-download";
    button.textContent = "Download";
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      downloadCanvas(displayCanvas, `${loadedFileName}_panel_${String(index + 1).padStart(2, "0")}.png`);
    });

    header.append(labelWrap, button);
    const previewWrap = document.createElement("div");
    previewWrap.className = "split-card-preview checkerboard";
    const previewCanvas = createCanvas(displayCanvas.width, displayCanvas.height);
    drawImageOnCanvas(previewCanvas, displayCanvas);
    previewWrap.append(previewCanvas);
    card.append(header, previewWrap);
    splitLinks.append(card);
  });
  updateSplitFilterButtons();
  updateSplitPanelThresholdLabel();
}

async function processBackgroundImage() {
  if (!loadedImage) {
    bgStatus.textContent = "Upload an image first.";
    return;
  }
  const settings = getBgSettings();
  if (settings.mode === "ai" && settings.maskSource === "ai" && !importedAiMaskAlpha) {
    bgStatus.textContent = "AI mode is set to Imported AI mask, but no AI mask PNG is loaded yet. Click 'Load AI Mask PNG' first, or switch Current mask input to Processed mask.";
    updateActionStates();
    return;
  }
  if (settings.mode === "multi" && !settings.manualBackgroundSamples.length) {
    bgStatus.textContent = "Multi-point mode needs 3-4 background clicks first.";
    return;
  }

  const workHint = getImageWorkHint(loadedImage.width, loadedImage.height);
  const baseMessage = settings.mode === "crop"
    ? `Finding the object bounds... ${workHint}`
    : settings.mode === "ai"
      ? `Preparing AI mask preview with ${settings.aiSource} settings... ${workHint}`
    : settings.mode === "multi"
      ? `Processing image with ${settings.manualBackgroundSamples.length} background sample${settings.manualBackgroundSamples.length === 1 ? "" : "s"}... ${workHint}`
      : `Processing image... ${workHint}`;

  cancelProcessingRequested = false;
  stopSamplingMode();
  bgStatus.textContent = baseMessage;
  setProcessingState(true, baseMessage);

  try {
    await new Promise((resolve) => setTimeout(resolve, 0));
    const sourceCanvas = createCanvas(loadedImage.width, loadedImage.height);
    const sourceCtx = sourceCanvas.getContext("2d");
    sourceCtx.drawImage(loadedImage, 0, 0);
    const sourceData = sourceCtx.getImageData(0, 0, sourceCanvas.width, sourceCanvas.height);
    const backgroundSamples = getBackgroundSamples(settings, sourceData);
    const aiCoverage = settings.mode === "ai" && settings.maskSource === "ai"
      ? getAlphaCoverage(getRefinedImportedAiAlpha(settings))
      : null;
    if (settings.mode === "ai" && settings.maskSource === "ai" && (aiCoverage === null || aiCoverage < 0.001)) {
      bgStatus.textContent = "The imported AI mask is effectively empty after the current settings. Try turning off Invert, lowering Feather, or loading a different matte.";
      setProcessingState(false);
      return;
    }

    const processed = settings.mode === "crop"
      ? processObjectCrop(sourceCanvas, sourceData, settings, backgroundSamples[0])
      : settings.mode === "ai" && settings.maskSource === "ai" && aiMaskCanvas
        ? buildProcessedBackgroundFromAlpha(
            sourceCanvas,
            sourceData,
            getRefinedImportedAiAlpha(settings) || alphaFromMaskCanvas(aiMaskCanvas),
            {
              ...settings,
              mode: "remove",
              decontaminate: true
            },
            backgroundSamples
          )
      : settings.mode === "ai" && settings.maskSource === "manual" && manualMaskCanvas
        ? buildProcessedBackgroundFromAlpha(
            sourceCanvas,
            sourceData,
            alphaFromMaskCanvas(manualMaskCanvas),
            {
              ...settings,
              mode: "remove",
              decontaminate: true
            },
            backgroundSamples
          )
      : settings.mode === "ai"
        ? await processBackgroundRemoval(sourceCanvas, sourceData, {
            ...settings,
            mode: "remove",
            threshold: Math.max(8, Math.round(settings.threshold * (settings.aiConfidence / 72))),
            softness: Math.max(6, Math.round(settings.softness * (settings.aiMatte / 68))),
            decontaminate: true
          }, backgroundSamples, (percent) => {
            const message = `${baseMessage} ${percent}%`;
            bgStatus.textContent = message;
            setProcessingState(true, message);
          })
      : await processBackgroundRemoval(sourceCanvas, sourceData, settings, backgroundSamples, (percent) => {
          const message = `${baseMessage} ${percent}%`;
          bgStatus.textContent = message;
          setProcessingState(true, message);
        });

    processedPanels = processed.panels;
    processedLayoutCanvas = processed.layoutCanvas || processed.canvas;
    processedMaskCanvas = processed.maskCanvas || null;
    processedMaskAlpha = processed.alpha || null;
    manualMaskCanvas = buildManualMaskCanvas(sourceCanvas.width, sourceCanvas.height, settings);
    splitPanelLayoutMode = bgPanelLayout ? bgPanelLayout.value : "crop";
    selectedPanelIndex = settings.layout === "split" && processedPanels.length ? 0 : -1;
    syncMainPreviewFromLayout();
    renderSplitLinks();
    bgStatus.textContent = settings.mode === "ai"
      ? settings.maskSource === "ai" && aiMaskCanvas
        ? `${processed.status} Imported AI mask is driving the extracted result.`
        : settings.maskSource === "manual" && manualMaskCanvas
          ? `${processed.status} Manual correction mask is driving the extracted result.`
          : `${processed.status} AI auto mask is currently using the heuristic preview path until a local segmentation model is connected.`
      : processed.status;
    updateMaskStatusBlock();
  } catch (error) {
    if ((error.message || "") === "Processing canceled.") {
      bgStatus.textContent = "Processing canceled.";
    } else {
      console.error(error);
      bgStatus.textContent = `Processing failed: ${error.message || error}`;
    }
  } finally {
    cancelProcessingRequested = false;
    setProcessingState(false);
  }
}

function handleFileInput(event) {
  const [file] = event.target.files || [];
  if (!file) return;
  loadedFileName = file.name.replace(/\.[^.]+$/, "");
  const url = URL.createObjectURL(file);
  const image = new Image();
  image.onload = () => {
    loadedImage = image;
    renderOriginalPreview();
    originalMeta.textContent = `${loadedImage.width} x ${loadedImage.height}`;
    bgStatus.textContent = getIdleGuidanceMessage();
    resultMeta.textContent = "No result yet";
    processedCanvas = null;
    processedLayoutCanvas = null;
    processedMaskCanvas = null;
    processedMaskAlpha = null;
    manualMaskCanvas = null;
    aiMaskCanvas = null;
    importedAiMaskAlpha = null;
    processedPanels = [];
    selectedPanelIndex = -1;
    manualBackgroundColor = null;
    manualBackgroundSamples = [];
    manualKeepSamples = [];
    manualKeepBoxes = [];
    manualSubtractBoxes = [];
    manualKeepBrushPoints = [];
    manualRemoveBrushPoints = [];
    clearBrushHistory();
    updateSampleMeta();
    stopSamplingMode();
    renderSplitLinks();
    updateActionStates();
    updateMaskStatusBlock();
    URL.revokeObjectURL(url);
  };
  image.src = url;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  refreshOutput(formStateToConfig());
});

copyJsonButton.addEventListener("click", () => {
  if (!currentPayload) return;
  copyText(JSON.stringify(currentPayload.workflow, null, 2));
});

copyChecklistButton.addEventListener("click", () => {
  if (!currentPayload) return;
  copyText(currentPayload.installItems.join("\n"));
});

downloadJsonButton.addEventListener("click", () => {
  if (!currentPayload) return;
  const blob = new Blob([JSON.stringify(currentPayload.workflow, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "comfyui-workflow-template.json";
  link.click();
  URL.revokeObjectURL(url);
});

loadDemoButton.addEventListener("click", () => {
  form.workflowType.value = "combined";
  form.style.value = "fantasy";
  form.checkpoint.value = "juggernautXL";
  form.remover.value = "essentials";
  form.assetType.value = "ornate inventory button";
  form.material.value = "ornate gold border, carved stone backing, glowing rune core";
  form.batchMode.checked = false;
  form.pixelEdges.checked = false;
  refreshOutput(formStateToConfig());
});

bgPreset.addEventListener("change", () => applyPreset(bgPreset.value));
[bgThreshold, bgSoftness, bgAlphaFloor, bgAlphaCeiling, bgEdgeCleanupStrength, bgComponentAlpha, bgComponentPixels, bgComponentPad, bgObjectPad].forEach((input) => input.addEventListener("input", updateRangeLabels));
[bgAiConfidence, bgAiMatte, bgAiSpill].forEach((input) => {
  if (input) input.addEventListener("input", updateRangeLabels);
});
[bgAiMaskExpand, bgAiMaskFeather].forEach((input) => {
  if (input) {
    input.addEventListener("input", () => {
      updateRangeLabels();
      refreshImportedAiMaskPreview();
    });
  }
});
[bgAiInvertMask, bgAiCombineManual].forEach((input) => {
  if (input) {
    input.addEventListener("change", () => {
      refreshImportedAiMaskPreview();
    });
  }
});
bgLayout.addEventListener("change", () => {
  if (processedLayoutCanvas || processedPanels.length) {
    syncMainPreviewFromLayout();
    renderSplitLinks();
  }
});
  if (bgMaskSource) {
    bgMaskSource.addEventListener("change", () => {
      if (processedLayoutCanvas || processedMaskCanvas || manualMaskCanvas || aiMaskCanvas) {
        syncMainPreviewFromLayout();
      }
      updateMaskStatusBlock();
    });
  }
if (bgPreviewTarget) {
  bgPreviewTarget.addEventListener("change", () => {
    if (processedLayoutCanvas || processedMaskCanvas || manualMaskCanvas || aiMaskCanvas) {
      syncMainPreviewFromLayout();
    }
    updateMaskStatusBlock();
  });
}
if (bgPanelLayout) {
  bgPanelLayout.addEventListener("change", () => {
    splitPanelLayoutMode = bgPanelLayout.value;
    if (processedLayoutCanvas || processedPanels.length) {
      syncMainPreviewFromLayout();
      renderSplitLinks();
    }
  });
}

bgMode.addEventListener("change", () => {
  stopSamplingMode();
  if (bgMode.value !== "multi") {
    manualBackgroundSamples = [];
    manualKeepSamples = [];
    manualKeepBoxes = [];
    manualSubtractBoxes = [];
    manualKeepBrushPoints = [];
    manualRemoveBrushPoints = [];
    clearBrushHistory();
    updateSampleMeta();
  }
  bgStatus.textContent = getIdleGuidanceMessage();
  updateActionStates();
});

bgInputFile.addEventListener("change", handleFileInput);
processBgButton.addEventListener("click", processBackgroundImage);
if (bgEditorView) {
  bgEditorView.addEventListener("change", updateEditorLayout);
}
if (bgBrushSize) {
  bgBrushSize.addEventListener("input", () => {
    updateRangeLabels();
    renderOriginalPreview();
  });
}
if (bgMaskOverlay) {
  bgMaskOverlay.addEventListener("input", () => {
    updateRangeLabels();
    renderOriginalPreview();
  });
}
if (cancelBgButton) {
  cancelBgButton.addEventListener("click", () => {
    if (!isProcessing) {
      bgStatus.textContent = "Nothing is currently processing.";
      return;
    }
    cancelProcessingRequested = true;
    bgStatus.textContent = "Cancel requested. Finishing the current chunk...";
    setProcessingState(true, "Cancel requested...");
  });
}
sampleBgButton.addEventListener("click", handleSampleBackgroundMode);
if (sampleKeepButton) sampleKeepButton.addEventListener("click", handleSampleKeepMode);
if (sampleKeepBoxButton) sampleKeepBoxButton.addEventListener("click", handleSampleKeepBoxMode);
if (sampleSubtractBoxButton) sampleSubtractBoxButton.addEventListener("click", () => startSamplingMode("subtract-box"));
if (eraseKeepBoxButton) eraseKeepBoxButton.addEventListener("click", handleEraseKeepBoxMode);
if (autoDetectUiButton) autoDetectUiButton.addEventListener("click", handleAutoDetectUiBoxes);
if (protectTopBarButton) protectTopBarButton.addEventListener("click", () => addPresetKeepBoxes("top"));
if (protectBottomBarButton) protectBottomBarButton.addEventListener("click", () => addPresetKeepBoxes("bottom"));
if (protectIconStripButton) protectIconStripButton.addEventListener("click", () => addPresetKeepBoxes("icons"));
if (brushKeepButton) brushKeepButton.addEventListener("click", handleBrushKeepMode);
if (brushRemoveButton) brushRemoveButton.addEventListener("click", handleBrushRemoveMode);
if (clearKeepBoxesButton) {
  clearKeepBoxesButton.addEventListener("click", () => {
    manualKeepBoxes = [];
    activeKeepBox = null;
    updateSampleMeta();
    renderOriginalPreview();
    updateActionStates();
    bgStatus.textContent = "Cleared UI keep boxes.";
  });
}
if (clearSubtractBoxesButton) {
  clearSubtractBoxesButton.addEventListener("click", () => {
    manualSubtractBoxes = [];
    updateSampleMeta();
    renderOriginalPreview();
    updateActionStates();
    bgStatus.textContent = "Cleared scenery remove boxes.";
  });
}
if (clearBrushKeepButton) {
  clearBrushKeepButton.addEventListener("click", () => {
    manualKeepBrushPoints = [];
    clearBrushHistory();
    updateSampleMeta();
    renderOriginalPreview();
    updateActionStates();
    bgStatus.textContent = "Cleared brush keep marks.";
  });
}
if (clearBrushRemoveButton) {
  clearBrushRemoveButton.addEventListener("click", () => {
    manualRemoveBrushPoints = [];
    clearBrushHistory();
    updateSampleMeta();
    renderOriginalPreview();
    updateActionStates();
    bgStatus.textContent = "Cleared brush remove marks.";
  });
}
if (undoBrushEditButton) {
  undoBrushEditButton.addEventListener("click", undoLastBrushEdit);
}
if (showLikelyUiButton) {
  showLikelyUiButton.addEventListener("click", () => {
    splitPanelFilter = "likely";
    renderSplitLinks();
  });
}
if (showAllPanelsButton) {
  showAllPanelsButton.addEventListener("click", () => {
    splitPanelFilter = "all";
    renderSplitLinks();
  });
}
if (splitMinPixels) {
  splitMinPixels.addEventListener("input", () => {
    splitPanelMinPixels = Number(splitMinPixels.value);
    updateSplitPanelThresholdLabel();
    renderSplitLinks();
  });
}
if (splitSortMode) {
  splitSortMode.addEventListener("change", () => {
    splitPanelSortMode = splitSortMode.value;
    renderSplitLinks();
  });
}

downloadBgButton.addEventListener("click", () => {
  if (!processedCanvas) {
    bgStatus.textContent = "Process an image first so there is something to download.";
    return;
  }
  const suffix = bgLayout.value === "split"
    ? "_preview_panel_browser.png"
    : bgMode.value === "crop"
      ? "_cropped_browser.png"
      : "_transparent_browser.png";
  downloadCanvas(processedCanvas, `${loadedFileName}${suffix}`);
  bgStatus.textContent = "Downloaded the current preview PNG.";
});

if (downloadLayoutButton) {
  downloadLayoutButton.addEventListener("click", () => {
    if (!processedLayoutCanvas) {
      bgStatus.textContent = "Process an image first so the full-sheet result exists.";
      return;
    }
    const suffix = bgMode.value === "crop" ? "_cropped_full_sheet.png" : "_transparent_full_sheet.png";
    downloadCanvas(processedLayoutCanvas, `${loadedFileName}${suffix}`);
    bgStatus.textContent = "Downloaded the full-sheet PNG.";
  });
}

if (downloadMaskButton) {
  downloadMaskButton.addEventListener("click", () => {
    let maskCanvasToDownload = processedMaskCanvas || manualMaskCanvas || aiMaskCanvas;
    if (bgMaskSource?.value === "manual") {
      maskCanvasToDownload = manualMaskCanvas || processedMaskCanvas || aiMaskCanvas;
    } else if (bgMaskSource?.value === "ai") {
      maskCanvasToDownload = aiMaskCanvas || processedMaskCanvas || manualMaskCanvas;
    }
    if (!maskCanvasToDownload) {
      bgStatus.textContent = "Process an image first or load an AI mask so a downloadable mask exists.";
      return;
    }
    const suffix = bgMaskSource?.value === "manual"
      ? "_manual_mask.png"
      : bgMaskSource?.value === "ai"
        ? "_ai_mask.png"
        : "_mask.png";
    downloadCanvas(maskCanvasToDownload, `${loadedFileName}${suffix}`);
    bgStatus.textContent = "Downloaded the current mask PNG.";
  });
}

if (aiMaskInput) {
  aiMaskInput.addEventListener("change", handleAiMaskInput);
}

downloadPanelsButton.addEventListener("click", async () => {
  if (!processedPanels.length) {
    bgStatus.textContent = "Process an image first so split panels exist.";
    return;
  }
  for (let index = 0; index < processedPanels.length; index += 1) {
    const panelCanvas = getPanelDisplayCanvas(processedPanels[index]);
    downloadCanvas(panelCanvas, `${loadedFileName}_panel_${String(index + 1).padStart(2, "0")}.png`);
    await new Promise((resolve) => setTimeout(resolve, 160));
  }
});

applyPreset(bgPreset.value);
refreshOutput(formStateToConfig());
renderSplitLinks();
updateRangeLabels();
updateSampleMeta();
setProcessingState(false);
bgStatus.textContent = getIdleGuidanceMessage();
updateActionStates();
updateSplitFilterButtons();
updateSplitPanelThresholdLabel();
updateEditorLayout();
updateMaskStatusBlock();
