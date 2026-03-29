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
  // Dark background presets (game screenshots, complex scenic backgrounds)
  "dark-balanced": {
    threshold: 18, softness: 24, alphaFloor: 8, alphaCeiling: 245,
    componentAlpha: 220, componentPixels: 5000, componentPad: 2, objectPad: 12,
    cropTransparent: false, decontaminate: true, tone: "dark",
    edgeCleanupStrength: 65, strongBorderRepair: false, preserveColor: true, secondPass: false,
    aiConfidence: 72, aiMatte: 68, aiSpill: 62, aiInvertMask: false, aiMaskExpand: 0, aiMaskFeather: 0,
    comfyui: { model: "RMBG-2.0", mask_blur: 0, mask_offset: 0, sensitivity: 1.0, process_res: 1024, invert_output: false, refine_foreground: false, background: "Alpha" }
  },
  "dark-soft": {
    threshold: 14, softness: 34, alphaFloor: 4, alphaCeiling: 245,
    componentAlpha: 200, componentPixels: 5000, componentPad: 4, objectPad: 16,
    cropTransparent: false, decontaminate: true, tone: "dark",
    edgeCleanupStrength: 45, strongBorderRepair: false, preserveColor: true, secondPass: false,
    aiConfidence: 68, aiMatte: 72, aiSpill: 55, aiInvertMask: false, aiMaskExpand: 1, aiMaskFeather: 1,
    comfyui: { model: "RMBG-2.0", mask_blur: 1, mask_offset: 0, sensitivity: 0.95, process_res: 1024, invert_output: false, refine_foreground: false, background: "Alpha" }
  },
  "dark-hard": {
    threshold: 24, softness: 16, alphaFloor: 12, alphaCeiling: 238,
    componentAlpha: 228, componentPixels: 7000, componentPad: 2, objectPad: 10,
    cropTransparent: false, decontaminate: true, tone: "dark",
    edgeCleanupStrength: 80, strongBorderRepair: false, preserveColor: false, secondPass: true,
    aiConfidence: 78, aiMatte: 62, aiSpill: 70, aiInvertMask: false, aiMaskExpand: -1, aiMaskFeather: 0,
    comfyui: { model: "RMBG-2.0", mask_blur: 0, mask_offset: 0, sensitivity: 1.0, process_res: 1024, invert_output: false, refine_foreground: false, background: "Alpha" }
  },
  // Light background presets (UI sheets with white/light grey backgrounds)
  "light-balanced": {
    threshold: 12, softness: 20, alphaFloor: 6, alphaCeiling: 248,
    componentAlpha: 220, componentPixels: 5000, componentPad: 2, objectPad: 12,
    cropTransparent: false, decontaminate: true, tone: "light",
    edgeCleanupStrength: 55, strongBorderRepair: true, preserveColor: true, secondPass: false,
    aiConfidence: 72, aiMatte: 68, aiSpill: 45, aiInvertMask: false, aiMaskExpand: 0, aiMaskFeather: 0,
    comfyui: { model: "RMBG-2.0", mask_blur: 0, mask_offset: 0, sensitivity: 0.95, process_res: 1024, invert_output: false, refine_foreground: false, background: "Alpha" }
  },
  "light-soft": {
    threshold: 10, softness: 28, alphaFloor: 2, alphaCeiling: 248,
    componentAlpha: 200, componentPixels: 4000, componentPad: 4, objectPad: 16,
    cropTransparent: false, decontaminate: true, tone: "light",
    edgeCleanupStrength: 40, strongBorderRepair: false, preserveColor: true, secondPass: false,
    aiConfidence: 66, aiMatte: 72, aiSpill: 35, aiInvertMask: false, aiMaskExpand: 1, aiMaskFeather: 1,
    comfyui: { model: "RMBG-2.0", mask_blur: 1, mask_offset: 0, sensitivity: 0.90, process_res: 1024, invert_output: false, refine_foreground: false, background: "Alpha" }
  },
  "light-hard": {
    threshold: 16, softness: 14, alphaFloor: 10, alphaCeiling: 242,
    componentAlpha: 228, componentPixels: 6000, componentPad: 2, objectPad: 10,
    cropTransparent: false, decontaminate: true, tone: "light",
    edgeCleanupStrength: 80, strongBorderRepair: true, preserveColor: false, secondPass: true,
    aiConfidence: 78, aiMatte: 62, aiSpill: 55, aiInvertMask: false, aiMaskExpand: -1, aiMaskFeather: 0,
    comfyui: { model: "RMBG-2.0", mask_blur: 0, mask_offset: 0, sensitivity: 1.0, process_res: 1024, invert_output: false, refine_foreground: false, background: "Alpha" }
  }
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
const batchModeToggle = document.querySelector("#batchModeToggle");
const batchInputFiles = document.querySelector("#batchInputFiles");
const singleFileField = document.querySelector("#singleFileField");
const batchFileField = document.querySelector("#batchFileField");
const batchFileCount = document.querySelector("#batchFileCount");
const batchProgressBlock = document.querySelector("#batchProgressBlock");
const batchProgressLabel = document.querySelector("#batchProgressLabel");
const batchCurrentFile = document.querySelector("#batchCurrentFile");
const batchProgressBar = document.querySelector("#batchProgressBar");
const batchAiSource = document.querySelector("#batchAiSource");
const batchAiSourceField = document.querySelector("#batchAiSourceField");
const comfyuiServer = document.querySelector("#comfyuiServer");
const comfyuiModel = document.querySelector("#comfyuiModel");
const comfyuiConnectButton = document.querySelector("#comfyuiConnectButton");
const comfyuiGenerateMaskButton = document.querySelector("#comfyuiGenerateMaskButton");
const comfyuiStatus = document.querySelector("#comfyuiStatus");
const browserMaskButton = document.querySelector("#browserMaskButton");
const browserMaskStatus = document.querySelector("#browserMaskStatus");
const aiRemoveButton = document.querySelector("#aiRemoveButton");
const aiRemoveStatus = document.querySelector("#aiRemoveStatus");
const comfyuiDot = document.querySelector("#comfyuiDot");
const aiEnhanceBlock = document.querySelector("#aiEnhanceBlock");
const aiEnhanceButton = document.querySelector("#aiEnhanceButton");
const aiEnhanceStatus = document.querySelector("#aiEnhanceStatus");
const aiFinalCanvas = document.querySelector("#aiFinalCanvas");
const aiEnhancedCanvas = document.querySelector("#aiEnhancedCanvas");
const downloadFinalButton = document.querySelector("#downloadFinalButton");
const downloadEnhancedButton = document.querySelector("#downloadEnhancedButton");

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
let importedAiMaskIsInternal = false; // true when mask is from internal detection (has soft edges)
let comfyuiConnected = false;
let onnxSession = null;
let onnxModelLoading = false;
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
let splitPanelFilter = "all";
let splitPanelMinPixels = 0;
let splitPanelSortMode = "useful";
let processedLayoutCanvas = null;
let splitPanelLayoutMode = "crop";
let brushEditHistory = [];
let activeBrushStroke = null;
let batchModeActive = false;
let batchFiles = [];
let batchProcessing = false;
let batchResults = [];
let batchCancelRequested = false;

const MAX_KEEP_BOXES = 24;
const MAX_KEEP_POINTS = 12;
const MAX_BG_SAMPLES = 6;
const DEFAULT_BRUSH_RADIUS = 22;

function formStateToConfig() {
  const data = new FormData(form);
  return {
    workflowType: data.get("workflowType"),
    style: data.get("artStyle"),
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
  const aiLabel = comfyuiConnected
    ? "AI hook: ComfyUI connected"
    : aiMaskCanvas
      ? "AI hook: External AI mask loaded"
      : "AI hook: Not connected — use 'Test Connection' or 'Generate AI Mask'";

  maskStatusBlock.innerHTML = `<strong>Mask pipeline</strong><br>Source: ${sourceLabel}<br>Matte refinement: ${matteLabel}<br>${aiLabel}`;
}

function getIdleGuidanceMessage() {
  if (!loadedImage) return "Upload an image to start.";
  if (bgMode.value === "ai") {
    return comfyuiConnected
      ? `AI mode ready. Click 'Generate AI Mask' to run segmentation via ComfyUI, or 'Load AI Mask PNG' for an external matte. ${getImageWorkHint(loadedImage.width, loadedImage.height)}`
      : `AI mode ready. Click 'Generate AI Mask' to connect to ComfyUI and run segmentation, or 'Load AI Mask PNG' for an external matte. ${getImageWorkHint(loadedImage.width, loadedImage.height)}`;
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
  const canProcess = batchModeActive
    ? (batchFiles.length > 0 && !isProcessing)
    : (hasImage && !needsSamples && !needsImportedAiMask && !isProcessing);

  if (processBgButton) {
    processBgButton.disabled = !canProcess;
    processBgButton.textContent = batchModeActive
      ? `Process ${batchFiles.length} Image${batchFiles.length !== 1 ? "s" : ""}`
      : "Process Image";
    processBgButton.title = batchModeActive
      ? (batchFiles.length === 0 ? "Select images first." : "")
      : !hasImage
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
  if (thresholdValue && bgThreshold) thresholdValue.textContent = bgThreshold.value;
  if (softnessValue && bgSoftness) softnessValue.textContent = bgSoftness.value;
  if (alphaFloorValue && bgAlphaFloor) alphaFloorValue.textContent = bgAlphaFloor.value;
  if (alphaCeilingValue && bgAlphaCeiling) alphaCeilingValue.textContent = bgAlphaCeiling.value;
  if (edgeCleanupValue) edgeCleanupValue.textContent = bgEdgeCleanupStrength ? bgEdgeCleanupStrength.value : "55";
  if (componentAlphaValue && bgComponentAlpha) componentAlphaValue.textContent = bgComponentAlpha.value;
  if (componentPixelsValue && bgComponentPixels) componentPixelsValue.textContent = bgComponentPixels.value;
  if (componentPadValue && bgComponentPad) componentPadValue.textContent = bgComponentPad.value;
  if (objectPadValue && bgObjectPad) objectPadValue.textContent = bgObjectPad.value;
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
    if (bgStatus) bgStatus.textContent = "No brush edit to undo.";
    updateActionStates();
    return;
  }
  const target = last.kind === "keep" ? manualKeepBrushPoints : manualRemoveBrushPoints;
  target.splice(Math.max(0, target.length - last.count), last.count);
  updateSampleMeta();
  renderOriginalPreview();
  updateActionStates();
  if (bgStatus) bgStatus.textContent = `Undid last ${last.kind === "keep" ? "brush keep" : "brush remove"} edit.`;
}

function updateEditorLayout() {
  if (!previewStack) return;
  previewStack.classList.toggle("editor-focus-original", bgEditorView && bgEditorView.value === "focus");
}

function applyPreset(name) {
  const preset = bgPresets[name];
  if (!preset) return;
  // Core heuristic settings
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
  bgTone.value = preset.tone;
  // Advanced edge/color settings
  if (bgEdgeCleanupStrength) bgEdgeCleanupStrength.value = String(preset.edgeCleanupStrength ?? 55);
  if (bgStrongBorderRepair) bgStrongBorderRepair.checked = preset.strongBorderRepair ?? true;
  if (bgPreserveColor) bgPreserveColor.checked = preset.preserveColor ?? true;
  if (bgSecondPass) bgSecondPass.checked = preset.secondPass ?? false;
  // AI pipeline settings
  if (bgAiConfidence) bgAiConfidence.value = String(preset.aiConfidence ?? 72);
  if (bgAiMatte) bgAiMatte.value = String(preset.aiMatte ?? 68);
  if (bgAiSpill) bgAiSpill.value = String(preset.aiSpill ?? 62);
  if (bgAiInvertMask) bgAiInvertMask.checked = preset.aiInvertMask ?? false;
  if (bgAiMaskExpand) bgAiMaskExpand.value = String(preset.aiMaskExpand ?? 0);
  if (bgAiMaskFeather) bgAiMaskFeather.value = String(preset.aiMaskFeather ?? 0);
  // ComfyUI model selection from preset
  if (preset.comfyui && comfyuiModel) comfyuiModel.value = preset.comfyui.model;
  updateRangeLabels();
}

function createCanvas(width, height) {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

/**
 * Draw an Image onto a canvas preserving RGB even when alpha=0.
 * ComfyUI outputs masks as RGBA with alpha=0 but data in RGB.
 * Canvas drawImage uses premultiplied alpha, zeroing RGB when alpha=0.
 * This function draws via putImageData (which bypasses premultiplication)
 * by first rendering through a WebGL context configured for unpremultiplied alpha.
 */
function drawImagePreservingRGB(image, canvas) {
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  // Try drawing normally first
  ctx.drawImage(image, 0, 0);
  // Quick check: sample a few pixels to see if data survived
  const testData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  const total = canvas.width * canvas.height;
  const sampleStep = Math.max(1, Math.floor(total / 2000));
  let anyRGB = false;
  for (let i = 0; i < total; i += sampleStep) {
    if (testData[i * 4] > 0 || testData[i * 4 + 1] > 0 || testData[i * 4 + 2] > 0) {
      anyRGB = true;
      break;
    }
  }
  if (anyRGB) return; // Normal path worked fine

  // RGB was destroyed by premultiplied alpha — recover via WebGL
  try {
    const gl = document.createElement("canvas").getContext("webgl2", { premultipliedAlpha: false })
             || document.createElement("canvas").getContext("webgl", { premultipliedAlpha: false });
    if (!gl) return; // No WebGL, can't recover
    gl.canvas.width = image.width;
    gl.canvas.height = image.height;
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
    // Read pixels (unpremultiplied)
    const fb = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    const pixels = new Uint8Array(image.width * image.height * 4);
    gl.readPixels(0, 0, image.width, image.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    gl.deleteTexture(tex);
    gl.deleteFramebuffer(fb);
    // WebGL reads bottom-up; flip vertically
    const rowBytes = image.width * 4;
    const temp = new Uint8Array(rowBytes);
    for (let y = 0; y < Math.floor(image.height / 2); y++) {
      const topOff = y * rowBytes;
      const botOff = (image.height - 1 - y) * rowBytes;
      temp.set(pixels.subarray(topOff, topOff + rowBytes));
      pixels.copyWithin(topOff, botOff, botOff + rowBytes);
      pixels.set(temp, botOff);
    }
    // Set alpha to 255 so future drawImage calls don't destroy RGB again
    for (let i = 3; i < pixels.length; i += 4) pixels[i] = 255;
    const imgData = new ImageData(new Uint8ClampedArray(pixels.buffer), image.width, image.height);
    ctx.putImageData(imgData, 0, 0);
  } catch (_e) {
    // WebGL fallback failed; data stays as-is
  }
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
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  const total = canvas.width * canvas.height;
  const alpha = new Uint8ClampedArray(total);

  // Try RGB first (grayscale mask), then alpha channel, then whichever has data
  let rgbSum = 0, alphaSum = 0;
  const sampleCount = Math.min(total, 5000);
  const step = Math.max(1, Math.floor(total / sampleCount));
  for (let i = 0; i < total; i += step) {
    rgbSum += Math.max(data[i * 4], data[i * 4 + 1], data[i * 4 + 2]);
    alphaSum += data[i * 4 + 3];
  }

  // If RGB has meaningful variation, use it. Otherwise try alpha channel.
  const rgbMean = rgbSum / sampleCount;
  const alphaMean = alphaSum / sampleCount;
  const useAlpha = rgbMean < 1 && alphaMean > 0 && alphaMean < 254;

  for (let index = 0; index < total; index += 1) {
    const offset = index * 4;
    alpha[index] = useAlpha
      ? data[offset + 3]
      : Math.max(data[offset], data[offset + 1], data[offset + 2]);
  }
  return alpha;
}

function boxBlurAlpha(alpha, width, height, radius) {
  if (radius <= 0) return new Uint8ClampedArray(alpha);
  const size = radius * 2 + 1;
  let current = alpha;
  let next = new Uint8ClampedArray(alpha.length);

  // Horizontal pass with running sum
  for (let y = 0; y < height; y += 1) {
    const rowStart = y * width;
    let sum = 0;
    for (let x = -radius; x <= radius; x += 1) {
      sum += current[rowStart + Math.max(0, Math.min(width - 1, x))];
    }
    next[rowStart] = Math.round(sum / size);
    for (let x = 1; x < width; x += 1) {
      sum += current[rowStart + Math.min(width - 1, x + radius)]
           - current[rowStart + Math.max(0, x - radius - 1)];
      next[rowStart + x] = Math.round(sum / size);
    }
  }

  current = next;
  next = new Uint8ClampedArray(alpha.length);

  // Vertical pass with running sum
  for (let x = 0; x < width; x += 1) {
    let sum = 0;
    for (let y = -radius; y <= radius; y += 1) {
      sum += current[Math.max(0, Math.min(height - 1, y)) * width + x];
    }
    next[x] = Math.round(sum / size);
    for (let y = 1; y < height; y += 1) {
      sum += current[Math.min(height - 1, y + radius) * width + x]
           - current[Math.max(0, y - radius - 1) * width + x];
      next[y * width + x] = Math.round(sum / size);
    }
  }

  return next;
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
  // Binarize soft AI masks: AI segmentation models output graduated
  // probability masks; without this step, background pixels with soft
  // values become semi-transparent ghosts instead of being fully removed.
  // Skip for internal detection masks which have intentional soft edges.
  if (!importedAiMaskIsInternal) {
    const threshold = 128;
    for (let i = 0; i < refined.length; i += 1) {
      refined[i] = refined[i] >= threshold ? 255 : 0;
    }
  }
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

  let alpha = new Uint8ClampedArray(width * height);
  for (let i = 0; i < alpha.length; i += 1) {
    alpha[i] = keepMask[i] ? 255 : 0;
  }

  if (settings.manualSubtractBoxes.length) {
    alpha = applySubtractBoxesToAlpha(alpha, width, height, settings.manualSubtractBoxes);
  }
  if (settings.manualRemoveBrushPoints.length) {
    alpha = applyBrushPointsToAlpha(alpha, width, height, settings.manualRemoveBrushPoints, 0);
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
    drawImagePreservingRGB(image, canvas);
    importedAiMaskAlpha = alphaFromMaskCanvas(canvas);
    importedAiMaskIsInternal = false;
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

// --- ComfyUI API Integration ---

function getComfyuiBaseUrl() {
  // Route through local proxy to avoid CORS issues
  // The proxy at /comfyui/* forwards to the actual ComfyUI server
  const origin = window.location.origin;
  if (origin && origin !== "null" && !origin.startsWith("file")) {
    return origin + "/comfyui";
  }
  return (comfyuiServer ? comfyuiServer.value : "http://127.0.0.1:8000").replace(/\/+$/, "");
}

async function testComfyuiConnection() {
  const base = getComfyuiBaseUrl();
  if (comfyuiStatus) comfyuiStatus.textContent = "ComfyUI: connecting...";
  try {
    const response = await fetch(`${base}/system_stats`, { signal: AbortSignal.timeout(5000) });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const stats = await response.json();
    comfyuiConnected = true;
    const device = stats.devices?.[0]?.name || "unknown device";
    if (comfyuiStatus) comfyuiStatus.textContent = `ComfyUI: connected (${device})`;
    if (comfyuiDot) comfyuiDot.style.background = "#4c4";
    updateActionStates();
    return true;
  } catch (error) {
    comfyuiConnected = false;
    if (comfyuiStatus) comfyuiStatus.textContent = `ComfyUI: not connected`;
    if (comfyuiDot) comfyuiDot.style.background = "#c44";
    updateActionStates();
    return false;
  }
}

async function comfyuiUploadImage(imageBlob, filename) {
  const base = getComfyuiBaseUrl();
  const formData = new FormData();
  formData.append("image", imageBlob, filename);
  formData.append("overwrite", "true");
  const response = await fetch(`${base}/upload/image`, { method: "POST", body: formData });
  if (!response.ok) throw new Error(`Upload failed: HTTP ${response.status}`);
  return await response.json();
}

function getActiveComfyuiConfig() {
  const presetName = bgPreset ? bgPreset.value : "dark-balanced";
  const preset = bgPresets[presetName];
  return preset ? preset.comfyui : null;
}

function buildSegmentationWorkflow(inputFilename, modelType, comfyuiConfig) {
  // Build a minimal ComfyUI API workflow for background removal / segmentation
  // Uses ComfyUI-RMBG node pack (1038lab)
  // comfyuiConfig is optional — preset workflow params override defaults
  const config = comfyuiConfig || {};
  const isBiRefNet = modelType.startsWith("BiRefNet");
  const classType = isBiRefNet ? "BiRefNetRMBG" : "RMBG";

  const nodeInputs = isBiRefNet
    ? {
        "model": modelType,
        "image": ["1", 0],
        "mask_blur": config.mask_blur ?? 0,
        "mask_offset": config.mask_offset ?? 0,
        "invert_output": config.invert_output ?? false,
        "refine_foreground": config.refine_foreground ?? false,
        "background": config.background ?? "Alpha",
        "background_color": "#222222"
      }
    : {
        "model": modelType,
        "image": ["1", 0],
        "sensitivity": config.sensitivity ?? 1.0,
        "process_res": config.process_res ?? 1024,
        "mask_blur": config.mask_blur ?? 0,
        "mask_offset": config.mask_offset ?? 0,
        "invert_output": config.invert_output ?? false,
        "refine_foreground": config.refine_foreground ?? false,
        "background": config.background ?? "Alpha",
        "background_color": "#222222"
      };

  return {
    "1": {
      "class_type": "LoadImage",
      "inputs": { "image": inputFilename }
    },
    "2": {
      "class_type": classType,
      "inputs": nodeInputs
    },
    "3": {
      "class_type": "SaveImage",
      "inputs": {
        "filename_prefix": "_aimask_output",
        "images": ["2", 0]
      }
    }
  };
}

async function comfyuiQueueWorkflow(workflow) {
  const base = getComfyuiBaseUrl();
  const clientId = "asset-editor-" + Date.now();
  const body = { prompt: workflow, client_id: clientId };
  const response = await fetch(`${base}/prompt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Queue failed: HTTP ${response.status} — ${text.slice(0, 200)}`);
  }
  const result = await response.json();
  return { promptId: result.prompt_id, clientId };
}

async function comfyuiPollForCompletion(promptId, timeoutMs = 120000) {
  const base = getComfyuiBaseUrl();
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const response = await fetch(`${base}/history/${promptId}`);
    if (response.ok) {
      const history = await response.json();
      if (history[promptId]) {
        const entry = history[promptId];
        if (entry.status?.completed || entry.outputs) {
          return entry;
        }
        if (entry.status?.status_str === "error") {
          throw new Error("ComfyUI workflow execution failed: " + JSON.stringify(entry.status));
        }
      }
    }
    await new Promise(r => setTimeout(r, 1500));
  }
  throw new Error("ComfyUI workflow timed out after " + (timeoutMs / 1000) + "s");
}

function extractOutputImageFilename(historyEntry) {
  const outputs = historyEntry.outputs || {};
  for (const nodeId of Object.keys(outputs)) {
    const nodeOutput = outputs[nodeId];
    if (nodeOutput.images && nodeOutput.images.length > 0) {
      return nodeOutput.images[0];
    }
  }
  throw new Error("No output image found in ComfyUI workflow result");
}

async function comfyuiDownloadImage(imageInfo) {
  const base = getComfyuiBaseUrl();
  const subfolder = imageInfo.subfolder || "";
  const filename = imageInfo.filename;
  const type = imageInfo.type || "output";
  const url = `${base}/view?filename=${encodeURIComponent(filename)}&subfolder=${encodeURIComponent(subfolder)}&type=${encodeURIComponent(type)}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to download mask: HTTP ${response.status}`);
  const blob = await response.blob();
  return blob;
}

async function generateComfyuiMask() {
  if (!loadedImage) {
    if (bgStatus) bgStatus.textContent = "Load a source image first.";
    return;
  }
  if (comfyuiStatus) comfyuiStatus.textContent = "ComfyUI: uploading image...";
  if (bgStatus) bgStatus.textContent = "Generating AI mask via ComfyUI...";

  try {
    // Convert loaded image to blob for upload
    const uploadCanvas = createCanvas(loadedImage.width, loadedImage.height);
    uploadCanvas.getContext("2d").drawImage(loadedImage, 0, 0);
    const blob = await new Promise(resolve => uploadCanvas.toBlob(resolve, "image/png"));
    const uploadFilename = "asset_editor_input.png";

    // Upload
    await comfyuiUploadImage(blob, uploadFilename);
    if (comfyuiStatus) comfyuiStatus.textContent = "ComfyUI: building workflow...";

    // Build and queue workflow
    const modelType = comfyuiModel ? comfyuiModel.value : "BiRefNet";
    const workflow = buildSegmentationWorkflow(uploadFilename, modelType, getActiveComfyuiConfig());
    const { promptId } = await comfyuiQueueWorkflow(workflow);
    if (comfyuiStatus) comfyuiStatus.textContent = "ComfyUI: processing segmentation...";

    // Poll for completion
    const historyEntry = await comfyuiPollForCompletion(promptId);
    if (comfyuiStatus) comfyuiStatus.textContent = "ComfyUI: downloading mask...";

    // Have the server download and save the mask as a local static file
    // This avoids the tainted-canvas problem (browser blocks getImageData on cross-origin images)
    const outputImageInfo = extractOutputImageFilename(historyEntry);
    const saveResp = await fetch("/save-mask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(outputImageInfo)
    });
    if (!saveResp.ok) throw new Error("Failed to save mask locally: " + (await saveResp.text()));

    // Load mask as a true same-origin static file
    const maskImg = new Image();
    await new Promise((resolve, reject) => {
      maskImg.onload = resolve;
      maskImg.onerror = () => reject(new Error("Failed to load local mask file"));
      maskImg.src = "/_temp_mask.png?t=" + Date.now();
    });
    // Draw mask preserving RGB even if alpha=0 (ComfyUI premultiply-alpha issue).
    // The server-side /save-mask also fixes alpha, but this handles cached files.
    const maskCanvas = createCanvas(maskImg.width, maskImg.height);
    drawImagePreservingRGB(maskImg, maskCanvas);

    // Scale to source image size if needed
    let finalMaskCanvas = maskCanvas;
    if (maskCanvas.width !== loadedImage.width || maskCanvas.height !== loadedImage.height) {
      finalMaskCanvas = createCanvas(loadedImage.width, loadedImage.height);
      finalMaskCanvas.getContext("2d", { willReadFrequently: true }).drawImage(maskCanvas, 0, 0, loadedImage.width, loadedImage.height);
    }

    importedAiMaskAlpha = alphaFromMaskCanvas(finalMaskCanvas);

    // Auto-detect polarity: if most pixels are white, mask is inverted
    // (background area is always larger than foreground UI)
    let whiteCount = 0;
    for (let i = 0; i < importedAiMaskAlpha.length; i++) {
      if (importedAiMaskAlpha[i] > 128) whiteCount++;
    }
    const needsInvert = whiteCount > importedAiMaskAlpha.length * 0.5;
    if (needsInvert) {
      for (let i = 0; i < importedAiMaskAlpha.length; i++) {
        importedAiMaskAlpha[i] = 255 - importedAiMaskAlpha[i];
      }
    }

    // Uncheck manual invert since we already auto-corrected
    if (bgAiInvertMask) bgAiInvertMask.checked = false;

    rebuildImportedAiMaskCanvas();
    if (bgMode) bgMode.value = "ai";
    if (bgMaskSource) bgMaskSource.value = "ai";
    if (bgPreviewTarget) bgPreviewTarget.value = "mask";
    syncMainPreviewFromLayout();
    updateActionStates();
    updateMaskStatusBlock();
    comfyuiConnected = true;
    if (comfyuiStatus) comfyuiStatus.textContent = `ComfyUI: mask generated (${modelType}${needsInvert ? ", auto-inverted" : ""})`;
    if (bgStatus) bgStatus.textContent = `AI mask ready. Click 'Process Image' to extract. Mode set to AI auto mask with imported mask.`;

  } catch (error) {
    console.error("ComfyUI mask generation failed:", error);
    if (comfyuiStatus) comfyuiStatus.textContent = `ComfyUI: error — ${error.message}`;
    if (bgStatus) bgStatus.textContent = `ComfyUI mask generation failed: ${error.message}`;
  }
}

// --- Structural Contour Detection Engine ---
// Converts image to a tree of nested shapes (contour hierarchy).
// UI elements form deep trees (panel > button > icon).
// Scenery is flat (no containment). Based on Suzuki-Abe (1985).

function findContoursWithHierarchy(binaryArray, w, h) {
  // Suzuki-Abe border following algorithm.
  // Input: Int16Array where 1 = foreground, 0 = background
  // Output: array of {points, isHole, parent (id), id}
  const F = new Int16Array(binaryArray);
  let nbd = 1;
  let lnbd = 1;
  const contours = [];

  // Clear borders
  for (let i = 0; i < h; i += 1) { F[i * w] = 0; F[i * w + w - 1] = 0; }
  for (let j = 0; j < w; j += 1) { F[j] = 0; F[(h - 1) * w + j] = 0; }

  function neighborToIndex(i0, j0, id) {
    const offsets = [[0,1],[-1,1],[-1,0],[-1,-1],[0,-1],[1,-1],[1,0],[1,1]];
    return [i0 + offsets[id][0], j0 + offsets[id][1]];
  }
  function indexToNeighbor(i0, j0, i, j) {
    const di = i - i0, dj = j - j0;
    if (di===0&&dj===1) return 0; if (di===-1&&dj===1) return 1;
    if (di===-1&&dj===0) return 2; if (di===-1&&dj===-1) return 3;
    if (di===0&&dj===-1) return 4; if (di===1&&dj===-1) return 5;
    if (di===1&&dj===0) return 6; if (di===1&&dj===1) return 7;
    return -1;
  }
  function cwNon0(i0, j0, i, j, offset) {
    const id = indexToNeighbor(i0, j0, i, j);
    for (let k = 0; k < 8; k += 1) {
      const kk = ((-k + id - offset) % 8 + 16) % 8;
      const ij = neighborToIndex(i0, j0, kk);
      if (ij[0] >= 0 && ij[0] < h && ij[1] >= 0 && ij[1] < w && F[ij[0] * w + ij[1]] !== 0) return ij;
    }
    return null;
  }
  function ccwNon0(i0, j0, i, j, offset) {
    const id = indexToNeighbor(i0, j0, i, j);
    for (let k = 0; k < 8; k += 1) {
      const kk = ((k + id + offset) % 8 + 16) % 8;
      const ij = neighborToIndex(i0, j0, kk);
      if (ij[0] >= 0 && ij[0] < h && ij[1] >= 0 && ij[1] < w && F[ij[0] * w + ij[1]] !== 0) return ij;
    }
    return null;
  }

  for (let i = 1; i < h - 1; i += 1) {
    lnbd = 1;
    for (let j = 1; j < w - 1; j += 1) {
      let i2 = 0, j2 = 0;
      if (F[i * w + j] === 0) continue;

      if (F[i * w + j] === 1 && F[i * w + (j - 1)] === 0) {
        nbd += 1; i2 = i; j2 = j - 1;
      } else if (F[i * w + j] >= 1 && F[i * w + j + 1] === 0) {
        nbd += 1; i2 = i; j2 = j + 1;
        if (F[i * w + j] > 1) lnbd = F[i * w + j];
      } else {
        if (F[i * w + j] !== 1) lnbd = Math.abs(F[i * w + j]);
        continue;
      }

      const B = { points: [[j, i]], isHole: (j2 === j + 1), id: nbd, parent: -1 };
      contours.push(B);

      // Find parent based on lnbd
      let B0 = null;
      for (let c = 0; c < contours.length; c += 1) {
        if (contours[c].id === lnbd) { B0 = contours[c]; break; }
      }
      if (B0) {
        B.parent = B0.isHole
          ? (B.isHole ? B0.parent : lnbd)
          : (B.isHole ? lnbd : B0.parent);
      }

      const i1j1 = cwNon0(i, j, i2, j2, 0);
      if (!i1j1) {
        F[i * w + j] = -nbd;
        if (F[i * w + j] !== 1) lnbd = Math.abs(F[i * w + j]);
        continue;
      }

      let i1 = i1j1[0], j1 = i1j1[1];
      i2 = i1; j2 = j1;
      let i3 = i, j3 = j;

      while (true) {
        const i4j4 = ccwNon0(i3, j3, i2, j2, 1);
        if (!i4j4) break;
        const i4 = i4j4[0], j4 = i4j4[1];
        contours[contours.length - 1].points.push([j4, i4]);

        if (F[i3 * w + j3 + 1] === 0) F[i3 * w + j3] = -nbd;
        else if (F[i3 * w + j3] === 1) F[i3 * w + j3] = nbd;

        if (i4 === i && j4 === j && i3 === i1 && j3 === j1) {
          if (F[i * w + j] !== 1) lnbd = Math.abs(F[i * w + j]);
          break;
        }
        i2 = i3; j2 = j3; i3 = i4; j3 = j4;
      }
    }
  }
  return contours;
}

function computeContourFeatures(contour) {
  const pts = contour.points;
  if (pts.length < 3) return { area: 0, perimeter: 0, bbox: null, rectangularity: 0, circularity: 0 };

  // Bounding box
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const p of pts) {
    minX = Math.min(minX, p[0]); maxX = Math.max(maxX, p[0]);
    minY = Math.min(minY, p[1]); maxY = Math.max(maxY, p[1]);
  }
  const bboxW = maxX - minX + 1, bboxH = maxY - minY + 1;
  const bboxArea = bboxW * bboxH;

  // Area (Shoelace formula)
  let area = 0;
  for (let i = 0; i < pts.length; i += 1) {
    const j = (i + 1) % pts.length;
    area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1];
  }
  area = Math.abs(area) / 2;

  // Perimeter
  let perimeter = 0;
  for (let i = 0; i < pts.length; i += 1) {
    const j = (i + 1) % pts.length;
    perimeter += Math.sqrt((pts[j][0] - pts[i][0]) ** 2 + (pts[j][1] - pts[i][1]) ** 2);
  }

  const rectangularity = bboxArea > 0 ? area / bboxArea : 0;
  const circularity = perimeter > 0 ? (4 * Math.PI * area) / (perimeter * perimeter) : 0;

  return {
    area, perimeter, rectangularity, circularity,
    bbox: { left: minX, top: minY, right: maxX + 1, bottom: maxY + 1, width: bboxW, height: bboxH },
    aspectRatio: bboxW / Math.max(1, bboxH)
  };
}

function buildContourTree(contours, imageWidth, imageHeight) {
  // Build tree from parent references, compute features, score for UI detection
  const nodes = contours.map((c, i) => {
    const features = computeContourFeatures(c);
    return {
      id: c.id, index: i, isHole: c.isHole, parentId: c.parent,
      children: [], ...features, points: c.points,
      depth: 0, uiScore: 0
    };
  });

  // Build parent-child relationships
  const idToNode = new Map();
  for (const node of nodes) idToNode.set(node.id, node);
  for (const node of nodes) {
    if (node.parentId > 0 && idToNode.has(node.parentId)) {
      idToNode.get(node.parentId).children.push(node);
    }
  }

  // Compute depth
  function setDepth(node, d) {
    node.depth = d;
    for (const child of node.children) setDepth(child, d + 1);
  }
  for (const node of nodes) {
    if (node.parentId <= 0) setDepth(node, 0);
  }

  // Score each node for UI likelihood
  for (const node of nodes) {
    if (!node.bbox || node.area < 100) { node.uiScore = 0; continue; }
    const wRatio = node.bbox.width / imageWidth;
    const hRatio = node.bbox.height / imageHeight;

    // Containment depth: children that also have children
    let maxChildDepth = 0;
    function getMaxDepth(n, d) {
      if (d > maxChildDepth) maxChildDepth = d;
      for (const c of n.children) getMaxDepth(c, d + 1);
    }
    getMaxDepth(node, 0);

    // Sibling repetition: children with similar sizes
    let similarSiblings = 0;
    if (node.children.length >= 2) {
      for (let a = 0; a < node.children.length; a += 1) {
        for (let b = a + 1; b < node.children.length; b += 1) {
          const ca = node.children[a], cb = node.children[b];
          if (ca.bbox && cb.bbox) {
            const wDiff = Math.abs(ca.bbox.width - cb.bbox.width) / Math.max(1, ca.bbox.width);
            const hDiff = Math.abs(ca.bbox.height - cb.bbox.height) / Math.max(1, ca.bbox.height);
            if (wDiff < 0.15 && hDiff < 0.15) similarSiblings += 1;
          }
        }
      }
    }

    // Screen edge proximity
    const edgeDist = Math.min(
      node.bbox.left / imageWidth,
      node.bbox.top / imageHeight,
      (imageWidth - node.bbox.right) / imageWidth,
      (imageHeight - node.bbox.bottom) / imageHeight
    );
    const edgeAffinity = edgeDist < 0.05 ? 1 : edgeDist < 0.15 ? 0.5 : 0;

    // Composite score — require BOTH hierarchy depth AND rectangularity.
    // Cave contours have depth but low rectangularity (<0.3).
    // UI contours have depth AND high rectangularity (>0.6).
    const depthScore = Math.min(maxChildDepth / 3, 1);
    const rectScore = node.rectangularity;
    // Penalize low rectangularity heavily — this is what separates UI from cave
    const rectPenalty = rectScore < 0.4 ? 0.2 : rectScore < 0.6 ? 0.6 : 1.0;
    node.uiScore =
      0.25 * depthScore * rectPenalty +
      0.35 * rectScore +
      0.10 * (1 - Math.min(node.area / (imageWidth * imageHeight * 0.5), 1)) +
      0.10 * Math.min(similarSiblings / 3, 1) +
      0.10 * edgeAffinity +
      0.10 * (node.children.length > 0 && rectScore > 0.5 ? 0.8 : 0);
  }

  return nodes;
}

function buildBlackBorderUiMask(sourceData, width, height) {
  // v5: Border-bounded background subtraction with inverted selection.
  //
  // The user's key insight: detect borders → set as boundaries → select
  // objects → INVERT selection → delete inverted = remove background.
  //
  // Instead of scoring individual objects for "UI-ness" (which misses panels
  // and includes artifacts), we identify the BACKGROUND and INVERT:
  //   everything NOT background = UI selection.
  //
  // This eliminates random pixels because nothing outside a border-bounded
  // region survives — the inversion deletes everything not explicitly selected.
  //
  // Pipeline:
  //   Pass 1 — Color gradient map
  //   Pass 2 — Border detection (gradient + dark achromatic outlines)
  //   Pass 3 — Component labeling (regions between borders)
  //   Pass 4 — Object metrics (color variance, shape, edge contact)
  //   Pass 5 — Background identification (highest variance + most edges + largest)
  //   Pass 6 — Mark ALL secondary background regions
  //   Pass 7 — INVERT: selection = everything NOT background
  //   Pass 8 — Build mask: selection + border pixels, delete everything else

  const data = sourceData.data;
  const total = width * height;

  // ══════════════════════════════════════════════════════════════════════
  // PASS 1: Color gradient map
  // ══════════════════════════════════════════════════════════════════════

  const gradient = new Float32Array(total);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const idx = y * width + x;
      const off = idx * 4;
      const r = data[off], g = data[off + 1], b = data[off + 2];
      let maxDsq = 0;
      if (x > 0)          { const n = off - 4;         const d = (r - data[n]) ** 2 + (g - data[n + 1]) ** 2 + (b - data[n + 2]) ** 2; if (d > maxDsq) maxDsq = d; }
      if (x < width - 1)  { const n = off + 4;         const d = (r - data[n]) ** 2 + (g - data[n + 1]) ** 2 + (b - data[n + 2]) ** 2; if (d > maxDsq) maxDsq = d; }
      if (y > 0)          { const n = off - width * 4;  const d = (r - data[n]) ** 2 + (g - data[n + 1]) ** 2 + (b - data[n + 2]) ** 2; if (d > maxDsq) maxDsq = d; }
      if (y < height - 1) { const n = off + width * 4;  const d = (r - data[n]) ** 2 + (g - data[n + 1]) ** 2 + (b - data[n + 2]) ** 2; if (d > maxDsq) maxDsq = d; }
      gradient[idx] = Math.sqrt(maxDsq);
    }
  }

  // Adaptive threshold from histogram (moderate — between v3 low and v4 high)
  const gradHist = new Uint32Array(256);
  for (let i = 0; i < total; i += 1) gradHist[Math.min(255, Math.round(gradient[i]))] += 1;
  let cumSum = 0, medianGrad = 0;
  for (let i = 0; i < 256; i += 1) { cumSum += gradHist[i]; if (cumSum >= total * 0.5) { medianGrad = i; break; } }
  const gradThreshold = Math.max(25, Math.min(50, medianGrad * 3));

  // ══════════════════════════════════════════════════════════════════════
  // PASS 2: Border detection
  // Dual criteria — catches both color-code boundaries AND black outlines.
  // Uses the PROVEN v3 approach (not v4's over-filtered structural borders).
  // ══════════════════════════════════════════════════════════════════════

  const edges = computeEdgeStrengthMap(sourceData);
  const distToEdge = new Uint8Array(total);
  distToEdge.fill(255);
  for (let i = 0; i < total; i += 1) { if (edges[i] >= 35) distToEdge[i] = 0; }
  for (let y = 1; y < height; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      const idx = y * width + x;
      if (distToEdge[idx] === 0) continue;
      distToEdge[idx] = Math.min(distToEdge[idx], distToEdge[idx - 1] + 1, distToEdge[idx - width] + 1, distToEdge[idx - width - 1] + 1, distToEdge[idx - width + 1] + 1);
    }
  }
  for (let y = height - 2; y >= 0; y -= 1) {
    for (let x = width - 2; x >= 1; x -= 1) {
      const idx = y * width + x;
      if (distToEdge[idx] === 0) continue;
      distToEdge[idx] = Math.min(distToEdge[idx], distToEdge[idx + 1] + 1, distToEdge[idx + width] + 1, distToEdge[idx + width + 1] + 1, distToEdge[idx + width - 1] + 1);
    }
  }

  const isBorder = new Uint8Array(total);
  for (let i = 0; i < total; i += 1) {
    // Criterion A: color gradient exceeds threshold
    if (gradient[i] >= gradThreshold) { isBorder[i] = 1; continue; }
    // Criterion B: dark achromatic pixel near a contrast edge (black outlines)
    const off = i * 4;
    const maxCh = Math.max(data[off], data[off + 1], data[off + 2]);
    if (maxCh < 55 && maxCh - Math.min(data[off], data[off + 1], data[off + 2]) <= 12 && distToEdge[i] <= 2) {
      isBorder[i] = 1;
    }
  }
  // Propagate dark borders through adjacent dark pixels (fills 2-4px outlines)
  for (let pass = 0; pass < 2; pass += 1) {
    const prev = new Uint8Array(isBorder);
    for (let y = 1; y < height - 1; y += 1) {
      for (let x = 1; x < width - 1; x += 1) {
        const idx = y * width + x;
        if (isBorder[idx]) continue;
        const off = idx * 4;
        const maxCh = Math.max(data[off], data[off + 1], data[off + 2]);
        if (maxCh >= 45 || maxCh - Math.min(data[off], data[off + 1], data[off + 2]) > 12) continue;
        if (prev[idx - 1] || prev[idx + 1] || prev[idx - width] || prev[idx + width]) isBorder[idx] = 1;
      }
    }
  }
  // Remove tiny border fragments (< 15 connected)
  const bSeen = new Uint8Array(total);
  for (let i = 0; i < total; i += 1) {
    if (bSeen[i] || !isBorder[i]) continue;
    const comp = []; const bq = [i]; bSeen[i] = 1; let bh2 = 0;
    while (bh2 < bq.length) {
      const ci = bq[bh2++]; comp.push(ci);
      const cx = ci % width, cy = (ci - cx) / width;
      if (cx > 0          && isBorder[ci - 1]     && !bSeen[ci - 1])     { bSeen[ci - 1] = 1;     bq.push(ci - 1); }
      if (cx < width - 1  && isBorder[ci + 1]     && !bSeen[ci + 1])     { bSeen[ci + 1] = 1;     bq.push(ci + 1); }
      if (cy > 0          && isBorder[ci - width]  && !bSeen[ci - width]) { bSeen[ci - width] = 1; bq.push(ci - width); }
      if (cy < height - 1 && isBorder[ci + width]  && !bSeen[ci + width]) { bSeen[ci + width] = 1; bq.push(ci + width); }
    }
    if (comp.length < 15) { for (const pi of comp) isBorder[pi] = 0; }
  }

  // ══════════════════════════════════════════════════════════════════════
  // PASS 2b: Border ENHANCEMENT — add pixels to detected borders
  // Hysteresis: accept weaker gradient pixels IF they're adjacent to
  // confirmed borders (like Canny edge detection's double threshold).
  // Then bridge small gaps between border segments.
  // Then validate: remove false enhancements not near real borders.
  // ══════════════════════════════════════════════════════════════════════

  const lowerThreshold = gradThreshold * 0.5;
  let enhancedCount = 0;
  // Hysteresis: 4 passes — weak gradient pixels adjacent to borders get promoted
  for (let pass = 0; pass < 4; pass += 1) {
    const prev = new Uint8Array(isBorder);
    for (let y = 1; y < height - 1; y += 1) {
      for (let x = 1; x < width - 1; x += 1) {
        const idx = y * width + x;
        if (isBorder[idx]) continue;
        if (gradient[idx] < lowerThreshold) continue;
        if (prev[idx - 1] || prev[idx + 1] || prev[idx - width] || prev[idx + width]) {
          isBorder[idx] = 1;
          enhancedCount += 1;
        }
      }
    }
  }

  // Gap bridging: connect border segments separated by ≤ 4px gaps
  // Horizontal
  for (let y = 0; y < height; y += 1) {
    let lastX = -10;
    for (let x = 0; x < width; x += 1) {
      if (isBorder[y * width + x]) {
        if (x - lastX > 1 && x - lastX <= 5) {
          for (let bx = lastX + 1; bx < x; bx += 1) { isBorder[y * width + bx] = 1; enhancedCount += 1; }
        }
        lastX = x;
      }
    }
  }
  // Vertical
  for (let x = 0; x < width; x += 1) {
    let lastY = -10;
    for (let y = 0; y < height; y += 1) {
      if (isBorder[y * width + x]) {
        if (y - lastY > 1 && y - lastY <= 5) {
          for (let by = lastY + 1; by < y; by += 1) { isBorder[by * width + x] = 1; enhancedCount += 1; }
        }
        lastY = y;
      }
    }
  }

  // Refinement: validate enhanced pixels — remove those not near original borders
  // (prevents noise from the lower threshold leaking into smooth areas)
  const origBorder = new Uint8Array(bSeen); // bSeen marks pixels that were in original borders
  for (let y = 2; y < height - 2; y += 1) {
    for (let x = 2; x < width - 2; x += 1) {
      const idx = y * width + x;
      if (!isBorder[idx] || origBorder[idx]) continue; // skip original borders
      // Check 5x5 neighborhood for original border pixels
      let origNearby = 0;
      for (let dy = -2; dy <= 2; dy += 1) {
        for (let dx = -2; dx <= 2; dx += 1) {
          if (origBorder[(y + dy) * width + (x + dx)]) origNearby += 1;
        }
      }
      if (origNearby < 2) { isBorder[idx] = 0; enhancedCount -= 1; }
    }
  }

  console.log(`[v5+] Border enhancement: +${enhancedCount} pixels (hysteresis + gap bridging)`);

  // ══════════════════════════════════════════════════════════════════════
  // PASS 3: Component labeling (regions between borders)
  // Borders are BOUNDARIES — regions can't cross them.
  // ══════════════════════════════════════════════════════════════════════

  const labels = new Int32Array(total);
  let nextLabel = 1;
  const objects = [];
  for (let i = 0; i < total; i += 1) {
    if (isBorder[i] || labels[i]) continue;
    const obj = {
      label: nextLabel, pixelCount: 0,
      minX: width, maxX: 0, minY: height, maxY: 0,
      touchesTop: false, touchesBottom: false, touchesLeft: false, touchesRight: false,
      sumR: 0, sumG: 0, sumB: 0, sumR2: 0, sumG2: 0, sumB2: 0,
      edgeSum: 0, // interior edge density (high = complex scene content, low = UI fill)
      perimeterCount: 0, borderContactCount: 0
    };
    const q = [i]; labels[i] = nextLabel; let h = 0;
    while (h < q.length) {
      const ci = q[h++]; obj.pixelCount += 1;
      const cx = ci % width, cy = (ci - cx) / width;
      if (cx < obj.minX) obj.minX = cx; if (cx > obj.maxX) obj.maxX = cx;
      if (cy < obj.minY) obj.minY = cy; if (cy > obj.maxY) obj.maxY = cy;
      if (cy === 0) obj.touchesTop = true; if (cy === height - 1) obj.touchesBottom = true;
      if (cx === 0) obj.touchesLeft = true; if (cx === width - 1) obj.touchesRight = true;
      const off = ci * 4;
      obj.sumR += data[off]; obj.sumG += data[off + 1]; obj.sumB += data[off + 2];
      obj.sumR2 += data[off] ** 2; obj.sumG2 += data[off + 1] ** 2; obj.sumB2 += data[off + 2] ** 2;
      obj.edgeSum += edges[ci]; // accumulate interior edge density
      let isP = false, touchesB = false;
      if (cx > 0)          { const ni = ci - 1;     if (isBorder[ni]) { isP = true; touchesB = true; } else if (!labels[ni]) { labels[ni] = nextLabel; q.push(ni); } } else { isP = true; }
      if (cx < width - 1)  { const ni = ci + 1;     if (isBorder[ni]) { isP = true; touchesB = true; } else if (!labels[ni]) { labels[ni] = nextLabel; q.push(ni); } } else { isP = true; }
      if (cy > 0)          { const ni = ci - width;  if (isBorder[ni]) { isP = true; touchesB = true; } else if (!labels[ni]) { labels[ni] = nextLabel; q.push(ni); } } else { isP = true; }
      if (cy < height - 1) { const ni = ci + width;  if (isBorder[ni]) { isP = true; touchesB = true; } else if (!labels[ni]) { labels[ni] = nextLabel; q.push(ni); } } else { isP = true; }
      if (isP) { obj.perimeterCount += 1; if (touchesB) obj.borderContactCount += 1; }
    }
    objects.push(obj); nextLabel += 1;
  }

  // ── Build Region Adjacency Graph (RAG) ──
  // For each border pixel, check which labeled regions it separates.
  // This gives us topology: which regions are neighbors across borders.
  const adjacency = new Map(); // label → Set of neighbor labels
  for (const obj of objects) adjacency.set(obj.label, new Set());
  for (let i = 0; i < total; i += 1) {
    if (!isBorder[i]) continue;
    const cx = i % width, cy = (i - cx) / width;
    const neighbors = new Set();
    if (cx > 0          && labels[i - 1] > 0)     neighbors.add(labels[i - 1]);
    if (cx < width - 1  && labels[i + 1] > 0)     neighbors.add(labels[i + 1]);
    if (cy > 0          && labels[i - width] > 0)  neighbors.add(labels[i - width]);
    if (cy < height - 1 && labels[i + width] > 0)  neighbors.add(labels[i + width]);
    // Connect all pairs of neighbors across this border pixel
    const arr = [...neighbors];
    for (let a = 0; a < arr.length; a += 1) {
      for (let b = a + 1; b < arr.length; b += 1) {
        if (!adjacency.has(arr[a])) adjacency.set(arr[a], new Set());
        if (!adjacency.has(arr[b])) adjacency.set(arr[b], new Set());
        adjacency.get(arr[a]).add(arr[b]);
        adjacency.get(arr[b]).add(arr[a]);
      }
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // PASS 4: Object metrics
  // ══════════════════════════════════════════════════════════════════════

  for (const obj of objects) {
    const n = obj.pixelCount; if (n === 0) continue;
    const mR = obj.sumR / n, mG = obj.sumG / n, mB = obj.sumB / n;
    obj.colorVariance = Math.sqrt(Math.max(0, obj.sumR2 / n - mR * mR) + Math.max(0, obj.sumG2 / n - mG * mG) + Math.max(0, obj.sumB2 / n - mB * mB));
    obj.rectangularity = n / ((obj.maxX - obj.minX + 1) * (obj.maxY - obj.minY + 1));
    obj.borderContactRatio = obj.borderContactCount / Math.max(1, obj.perimeterCount);
    obj.interiorEdgeDensity = obj.edgeSum / (n * 255); // normalized 0-1 (how much internal detail)
    obj.edgeSides = (obj.touchesTop ? 1 : 0) + (obj.touchesBottom ? 1 : 0) + (obj.touchesLeft ? 1 : 0) + (obj.touchesRight ? 1 : 0);
    obj.touchesEdge = obj.edgeSides > 0;
  }

  // ══════════════════════════════════════════════════════════════════════
  // PASS 5: Background identification
  // Background = highest variance + most edge sides + largest size.
  // ══════════════════════════════════════════════════════════════════════

  let maxVar = 0, maxSize = 0;
  for (const obj of objects) {
    if (obj.colorVariance > maxVar) maxVar = obj.colorVariance;
    if (obj.pixelCount > maxSize) maxSize = obj.pixelCount;
  }
  let bgLabel = -1, bestBgScore = -1;
  for (const obj of objects) {
    if (!obj.touchesEdge) continue;
    const bgScore = 0.35 * (maxVar > 0 ? obj.colorVariance / maxVar : 0) +
                    0.30 * (maxSize > 0 ? obj.pixelCount / maxSize : 0) +
                    0.25 * (obj.edgeSides / 4) +
                    0.10 * (1 - obj.rectangularity);
    if (bgScore > bestBgScore) { bestBgScore = bgScore; bgLabel = obj.label; }
  }
  const bgObj = objects.find(o => o.label === bgLabel);
  const bgColorVar = bgObj ? bgObj.colorVariance : 50;
  const bgEdgeDensity = bgObj ? bgObj.interiorEdgeDensity : 0.1;

  // ══════════════════════════════════════════════════════════════════════
  // PASS 6: Mark ALL background-like regions (not just the primary one)
  // Any edge-touching region with similar variance to background = also bg.
  // ══════════════════════════════════════════════════════════════════════

  const bgLabels = new Set();
  if (bgLabel >= 0) bgLabels.add(bgLabel);

  // Helper: check if a region has a UI-like shape (protects bars/panels from bg classification)
  // Must have BOTH UI-like geometry AND UI-like content (low variance or low edge density).
  // High-variance, high-edge-density regions with bar-like shapes are scene strips, not UI.
  function hasUiShape(obj) {
    const bw = obj.maxX - obj.minX + 1, bh = obj.maxY - obj.minY + 1;
    const wR = bw / width, hR = bh / height, asp = bw / Math.max(1, bh);
    const geoMatch = (asp >= 3 && hR <= 0.25) ||          // thin horizontal bar
                     (wR >= 0.4 && hR <= 0.40) ||          // wide bar
                     (wR <= 0.25 && hR <= 0.25 && wR >= 0.05) || // compact square panel
                     (obj.rectangularity >= 0.55);          // highly rectangular
    if (!geoMatch) return false;
    // Content check: UI has low variance OR low interior detail relative to background
    if (obj.colorVariance < bgColorVar * 0.55) return true;           // low variance = UI fill
    if (obj.interiorEdgeDensity < bgEdgeDensity * 0.60) return true;  // smooth interior = UI
    // Edge-touching: protect if EITHER variance or edge density is moderate (not both high)
    if (obj.touchesEdge && (obj.colorVariance < bgColorVar * 0.75 || obj.interiorEdgeDensity < bgEdgeDensity * 0.75)) return true;
    // Both high variance AND high edge density = scene content despite bar-like shape
    return false;
  }

  for (const obj of objects) {
    if (bgLabels.has(obj.label)) continue;

    // PROTECT UI-shaped regions — never classify as secondary background
    if (hasUiShape(obj)) continue;

    // Large, high-variance, edge-touching → secondary background
    if (obj.touchesEdge && obj.colorVariance > bgColorVar * 0.65 && obj.pixelCount > total * 0.01) {
      bgLabels.add(obj.label);
    }
    // Very small fragments touching edge with high variance → background noise
    if (obj.touchesEdge && obj.pixelCount < total * 0.003 && obj.colorVariance > bgColorVar * 0.5) {
      bgLabels.add(obj.label);
    }
    // Non-edge-touching game content fragments (expanded: up to 3% of image)
    if (!obj.touchesEdge && obj.colorVariance > bgColorVar * 0.6 && obj.pixelCount < total * 0.03 && obj.rectangularity < 0.45) {
      bgLabels.add(obj.label);
    }
  }

  // ── Trapped background detector (RAG-enhanced) ──
  // Uses the Region Adjacency Graph for topology-based detection:
  // If a region is SURROUNDED by background/border regions, it's trapped scene content.
  // Falls back to signal-based detection for regions not fully enclosed.
  let trappedCount = 0;
  let ragChanged = true;
  while (ragChanged) {
    ragChanged = false;
    for (const obj of objects) {
      if (bgLabels.has(obj.label)) continue;
      if (obj.touchesEdge) continue;
      if (obj.pixelCount < total * 0.001) continue;

      // Protect UI-shaped regions from ALL trapped bg classification
      if (hasUiShape(obj)) continue;

      // RAG check: are ALL neighbors either background or border?
      const neighbors = adjacency.get(obj.label);
      if (neighbors && neighbors.size > 0) {
        const allNeighborsBg = [...neighbors].every(n => bgLabels.has(n));
        if (allNeighborsBg && obj.colorVariance > bgColorVar * 0.50 && obj.interiorEdgeDensity > bgEdgeDensity * 0.40) {
          // Completely enclosed by background AND has scene-like variance AND complex interior
          bgLabels.add(obj.label);
          trappedCount += 1;
          ragChanged = true;
          continue;
        }
      }

      // Signal-based fallback for regions not fully enclosed by bg
      let bgSignals = 0;
      if (obj.colorVariance > bgColorVar * 0.45) bgSignals += 1;     // high variance
      if (obj.rectangularity < 0.45) bgSignals += 1;                  // irregular or moderate shape
      if (obj.interiorEdgeDensity > bgEdgeDensity * 0.50) bgSignals += 1; // complex interior
      if (obj.borderContactRatio < 0.60) bgSignals += 1;              // not strongly bordered

      // Large trapped regions (>1% of image) need fewer signals
      const minSignals = obj.pixelCount > total * 0.01 ? 2 : 3;

      if (bgSignals >= minSignals) {
        bgLabels.add(obj.label);
        trappedCount += 1;
        ragChanged = true;
      }
    }
  }
  if (trappedCount > 0) console.log(`[v5+ RAG] Trapped background: ${trappedCount} enclosed regions identified as scene content`);

  // ══════════════════════════════════════════════════════════════════════
  // PASS 7: INVERT SELECTION
  // Selection = everything NOT background. This is the core of the
  // "select objects → invert → delete background" workflow.
  // No per-object scoring threshold — if it's not background, it's UI.
  // Small fragments cleaned up after.
  // ══════════════════════════════════════════════════════════════════════

  const selection = new Uint8Array(total);
  for (let i = 0; i < total; i += 1) {
    if (labels[i] > 0 && !bgLabels.has(labels[i])) selection[i] = 1;
  }
  // Also include border pixels between two selected regions or adjacent to selection
  for (let i = 0; i < total; i += 1) {
    if (!isBorder[i] || selection[i]) continue;
    const cx = i % width, cy = (i - cx) / width;
    let adjSelected = 0, adjBg = 0;
    if (cx > 0)          { if (selection[i - 1]) adjSelected++; else if (labels[i - 1] > 0 && bgLabels.has(labels[i - 1])) adjBg++; }
    if (cx < width - 1)  { if (selection[i + 1]) adjSelected++; else if (labels[i + 1] > 0 && bgLabels.has(labels[i + 1])) adjBg++; }
    if (cy > 0)          { if (selection[i - width]) adjSelected++; else if (labels[i - width] > 0 && bgLabels.has(labels[i - width])) adjBg++; }
    if (cy < height - 1) { if (selection[i + width]) adjSelected++; else if (labels[i + width] > 0 && bgLabels.has(labels[i + width])) adjBg++; }
    // Include border if it touches selected AND doesn't only face background
    if (adjSelected > 0 && adjSelected >= adjBg) selection[i] = 1;
  }
  // Propagate through border pixels connected to selection (captures full border thickness)
  const selBorderQ = [];
  for (let i = 0; i < total; i += 1) {
    if (selection[i] && isBorder[i]) selBorderQ.push(i);
  }
  let sbh = 0;
  const selBorderDepth = new Uint8Array(total);
  while (sbh < selBorderQ.length) {
    const ci = selBorderQ[sbh++];
    if (selBorderDepth[ci] >= 6) continue;
    const cx = ci % width, cy = (ci - cx) / width;
    const nd = selBorderDepth[ci] + 1;
    if (cx > 0          && isBorder[ci - 1]     && !selection[ci - 1])     { selection[ci - 1] = 1;     selBorderDepth[ci - 1] = nd;     selBorderQ.push(ci - 1); }
    if (cx < width - 1  && isBorder[ci + 1]     && !selection[ci + 1])     { selection[ci + 1] = 1;     selBorderDepth[ci + 1] = nd;     selBorderQ.push(ci + 1); }
    if (cy > 0          && isBorder[ci - width]  && !selection[ci - width]) { selection[ci - width] = 1; selBorderDepth[ci - width] = nd; selBorderQ.push(ci - width); }
    if (cy < height - 1 && isBorder[ci + width]  && !selection[ci + width]) { selection[ci + width] = 1; selBorderDepth[ci + width] = nd; selBorderQ.push(ci + width); }
  }

  // ══════════════════════════════════════════════════════════════════════
  // PASS 8: Build mask — delete everything outside selection
  // The inverted selection (background) is cut out.
  // Then remove tiny remaining fragments.
  // ══════════════════════════════════════════════════════════════════════

  const alpha = new Uint8ClampedArray(total);
  for (let i = 0; i < total; i += 1) {
    if (selection[i]) alpha[i] = 255;
  }

  // Remove tiny fragments (< 0.2% of image)
  const seen = new Uint8Array(total);
  const minFrag = total * 0.002;
  for (let i = 0; i < total; i += 1) {
    if (seen[i] || !alpha[i]) continue;
    const comp = []; const q2 = [i]; seen[i] = 1; let h2 = 0;
    while (h2 < q2.length) {
      const ci = q2[h2++]; comp.push(ci);
      const cx = ci % width, cy = (ci - cx) / width;
      if (cx > 0          && !seen[ci - 1]     && alpha[ci - 1])     { seen[ci - 1] = 1;     q2.push(ci - 1); }
      if (cx < width - 1  && !seen[ci + 1]     && alpha[ci + 1])     { seen[ci + 1] = 1;     q2.push(ci + 1); }
      if (cy > 0          && !seen[ci - width]  && alpha[ci - width]) { seen[ci - width] = 1; q2.push(ci - width); }
      if (cy < height - 1 && !seen[ci + width]  && alpha[ci + width]) { seen[ci + width] = 1; q2.push(ci + width); }
    }
    if (comp.length < minFrag) { for (const pi of comp) alpha[pi] = 0; }
  }

  // ── Soft edge feathering via distance transform ──
  // Compute distance from each mask-boundary pixel inward, apply graduated alpha
  // at the outermost 2px to create soft edges matching reference quality (1.5% semi-transparent)
  const featherRadius = 2;
  const boundaryDist = new Uint8Array(total);
  boundaryDist.fill(255);
  // Seed: selected pixels adjacent to non-selected pixels (the mask boundary)
  const featherQ = [];
  for (let i = 0; i < total; i += 1) {
    if (!alpha[i]) continue;
    const cx = i % width, cy = (i - cx) / width;
    const hasTransparentNeighbor =
      (cx > 0          && !alpha[i - 1]) ||
      (cx < width - 1  && !alpha[i + 1]) ||
      (cy > 0          && !alpha[i - width]) ||
      (cy < height - 1 && !alpha[i + width]);
    if (hasTransparentNeighbor) { boundaryDist[i] = 0; featherQ.push(i); }
  }
  // BFS inward from boundary to compute distance
  let fh = 0;
  while (fh < featherQ.length) {
    const ci = featherQ[fh++];
    const d = boundaryDist[ci];
    if (d >= featherRadius) continue;
    const cx = ci % width, cy = (ci - cx) / width;
    const nd = d + 1;
    if (cx > 0          && alpha[ci - 1]     && boundaryDist[ci - 1] > nd)     { boundaryDist[ci - 1] = nd;     featherQ.push(ci - 1); }
    if (cx < width - 1  && alpha[ci + 1]     && boundaryDist[ci + 1] > nd)     { boundaryDist[ci + 1] = nd;     featherQ.push(ci + 1); }
    if (cy > 0          && alpha[ci - width]  && boundaryDist[ci - width] > nd) { boundaryDist[ci - width] = nd; featherQ.push(ci - width); }
    if (cy < height - 1 && alpha[ci + width]  && boundaryDist[ci + width] > nd) { boundaryDist[ci + width] = nd; featherQ.push(ci + width); }
  }
  // Apply graduated alpha at boundary: dist 0 = 128, dist 1 = 192, dist 2+ = 255
  const featherAlpha = [128, 192];
  for (let i = 0; i < total; i += 1) {
    if (!alpha[i]) continue;
    if (boundaryDist[i] < featherRadius) {
      alpha[i] = featherAlpha[boundaryDist[i]] || 255;
    }
  }

  const kept = alpha.reduce((s, a) => s + (a > 0 ? 1 : 0), 0);
  const bgCount = [...bgLabels].reduce((s, l) => s + (objects.find(o => o.label === l) || { pixelCount: 0 }).pixelCount, 0);
  console.log(`[v5 InvertSelect] thresh=${gradThreshold}, objects=${objects.length}, ` +
    `bgRegions=${bgLabels.size} (${(bgCount / total * 100).toFixed(1)}% of image), ` +
    `selected=${objects.length - bgLabels.size}, coverage=${(kept / total * 100).toFixed(1)}%`);
  // Log what was classified as background vs UI
  const sorted = [...objects].sort((a, b) => b.pixelCount - a.pixelCount).slice(0, 12);
  for (const o of sorted) {
    if (o.pixelCount < total * 0.001) continue;
    const tag = bgLabels.has(o.label) ? 'BG' : 'UI';
    console.log(`  L${o.label} [${tag}]: sz=${(o.pixelCount / total * 100).toFixed(1)}% ` +
      `cVar=${o.colorVariance.toFixed(0)} rect=${o.rectangularity.toFixed(2)} edges=${o.edgeSides} ` +
      `bContact=${o.borderContactRatio.toFixed(2)} edgeDens=${o.interiorEdgeDensity.toFixed(3)}`);
  }
  return alpha;
}

function buildStructuralUiMask(sourceData, width, height, tone) {
  // Convert image to binary edge map, find contours with hierarchy,
  // score for UI, build alpha mask from high-scoring contours.

  const edges = computeEdgeStrengthMap(sourceData);
  const total = width * height;

  // Create binary image from edge map (threshold + dilate for connectivity)
  const binary = new Int16Array(total);
  const edgeThreshold = 25;
  for (let i = 0; i < total; i += 1) {
    binary[i] = edges[i] >= edgeThreshold ? 1 : 0;
  }
  // Light dilation to close small gaps in borders
  const dilated = new Int16Array(total);
  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      if (binary[y * width + x]) { dilated[y * width + x] = 1; continue; }
      if (binary[(y-1)*width+x] || binary[(y+1)*width+x] ||
          binary[y*width+x-1] || binary[y*width+x+1]) {
        dilated[y * width + x] = 1;
      }
    }
  }

  // Find contours with hierarchy
  const contours = findContoursWithHierarchy(dilated, width, height);

  // Build tree and score
  const nodes = buildContourTree(contours, width, height);

  // Collect UI regions: contours with high UI score AND sufficient size
  const uiThreshold = 0.55;
  const minArea = total * 0.005; // at least 0.5% of image
  const alpha = new Uint8ClampedArray(total);

  // Sort by area descending — larger regions first
  const uiNodes = nodes
    .filter(n => n.uiScore >= uiThreshold && n.area >= minArea && n.bbox)
    .sort((a, b) => b.area - a.area);

  // Fill UI regions into alpha mask
  for (const node of uiNodes) {
    const box = node.bbox;
    for (let y = box.top; y < box.bottom && y < height; y += 1) {
      for (let x = box.left; x < box.right && x < width; x += 1) {
        alpha[y * width + x] = 255;
      }
    }
  }

  // Also keep the existing row density detection as a fallback/supplement
  // for full-width bars that might not form closed contours
  const rowDensity = new Float32Array(height);
  for (let y = 0; y < height; y += 1) {
    let cnt = 0;
    for (let x = 0; x < width; x += 1) {
      if (edges[y * width + x] >= 30) cnt += 1;
    }
    rowDensity[y] = cnt / width;
  }
  const sortedDensity = [...rowDensity].sort((a, b) => a - b);
  const medianDensity = sortedDensity[Math.floor(height * 0.5)];
  const densityThreshold = Math.max(0.04, medianDensity * 2.5);
  for (let y = 0; y < height; y += 1) {
    if (rowDensity[y] >= densityThreshold) {
      for (let x = 0; x < width; x += 1) {
        alpha[y * width + x] = 255;
      }
    }
  }

  // Refine: remove background-colored pixels in the center zone
  const data = sourceData.data;
  let bgR = 0, bgG = 0, bgB = 0, bgCount = 0;
  for (let y = Math.floor(height * 0.3); y < Math.floor(height * 0.6); y += 2) {
    if (rowDensity[y] >= densityThreshold) continue;
    for (let x = Math.floor(width * 0.3); x < Math.floor(width * 0.7); x += 2) {
      const idx = (y * width + x) * 4;
      bgR += data[idx]; bgG += data[idx + 1]; bgB += data[idx + 2]; bgCount += 1;
    }
  }
  if (bgCount > 0) { bgR /= bgCount; bgG /= bgCount; bgB /= bgCount; }
  const colorThreshold = tone === "dark" ? 35 : 60;
  for (let y = Math.floor(height * 0.12); y < Math.floor(height * 0.68); y += 1) {
    for (let x = 0; x < width; x += 1) {
      if (alpha[y * width + x] === 0) continue;
      // Only clean center pixels, keep edges
      if (x > width * 0.15 && x < width * 0.85) {
        const idx = (y * width + x) * 4;
        const dist = Math.sqrt((data[idx]-bgR)**2 + (data[idx+1]-bgG)**2 + (data[idx+2]-bgB)**2);
        if (dist < colorThreshold) alpha[y * width + x] = 0;
      }
    }
  }

  // Disconnect thin vertical connectors
  for (let y = Math.floor(height * 0.12); y < Math.floor(height * 0.68); y += 1) {
    let opaqueInRow = 0;
    for (let x = 0; x < width; x += 1) {
      if (alpha[y * width + x] > 0) opaqueInRow += 1;
    }
    if (opaqueInRow > 0 && opaqueInRow < width * 0.03) {
      for (let x = 0; x < width; x += 1) alpha[y * width + x] = 0;
    }
  }

  // Remove tiny fragments
  const seen = new Uint8Array(total);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const idx = y * width + x;
      if (seen[idx] || alpha[idx] === 0) continue;
      const queue = [idx]; seen[idx] = 1;
      let head = 0, count = 0;
      const pixels = [];
      while (head < queue.length) {
        const ci = queue[head++]; count += 1; pixels.push(ci);
        const cx = ci % width, cy = Math.floor(ci / width);
        if (cx > 0)         { const ni = ci-1;     if (!seen[ni] && alpha[ni]>0) { seen[ni]=1; queue.push(ni); } }
        if (cx < width-1)   { const ni = ci+1;     if (!seen[ni] && alpha[ni]>0) { seen[ni]=1; queue.push(ni); } }
        if (cy > 0)         { const ni = ci-width;  if (!seen[ni] && alpha[ni]>0) { seen[ni]=1; queue.push(ni); } }
        if (cy < height-1)  { const ni = ci+width;  if (!seen[ni] && alpha[ni]>0) { seen[ni]=1; queue.push(ni); } }
      }
      if (count < total * 0.002) {
        for (const pi of pixels) alpha[pi] = 0;
      }
    }
  }

  return alpha;
}

// (buildHybridUiMask removed — 187 lines of dead code, superseded by v5)


async function aiRemoveWorkflow() {
  // Turn off batch mode if active — AI Remove works on single images
  if (batchModeToggle && batchModeToggle.checked) {
    batchModeToggle.checked = false;
    batchModeToggle.dispatchEvent(new Event("change"));
  }
  if (!loadedImage) {
    if (aiRemoveStatus) {
      aiRemoveStatus.style.display = "block";
      aiRemoveStatus.textContent = "Upload a single image first (uncheck Batch mode).";
    }
    return;
  }

  if (aiRemoveButton) aiRemoveButton.disabled = true;
  if (aiRemoveStatus) {
    aiRemoveStatus.style.display = "block";
    aiRemoveStatus.textContent = "Step 1/2: Detecting UI regions...";
  }

  try {
    // Build source canvas for analysis
    const sourceCanvas = createCanvas(loadedImage.width, loadedImage.height);
    sourceCanvas.getContext("2d").drawImage(loadedImage, 0, 0);
    const sourceData = sourceCanvas.getContext("2d").getImageData(0, 0, loadedImage.width, loadedImage.height);
    const currentTone = bgTone ? bgTone.value : "dark";

    // Step 1: Generate mask — try black border detection first (exploits thin dark
    // outlines common to game UIs), fall back to structural contour detection
    let hybridAlpha = buildBlackBorderUiMask(sourceData, loadedImage.width, loadedImage.height);
    let borderCoverage = getAlphaCoverage(hybridAlpha);
    if (borderCoverage < 0.02 || borderCoverage > 0.85) {
      console.log(`[AI Remove] Black border coverage ${(borderCoverage*100).toFixed(1)}% — falling back to structural detection`);
      hybridAlpha = buildStructuralUiMask(sourceData, loadedImage.width, loadedImage.height, currentTone);
    } else {
      console.log(`[AI Remove] Black border detection: ${(borderCoverage*100).toFixed(1)}% coverage`);
    }

    // Store as imported AI mask so the rest of the pipeline works
    importedAiMaskAlpha = hybridAlpha;
    importedAiMaskIsInternal = true; // skip binarization — internal mask has intentional soft edges
    rebuildImportedAiMaskCanvas();

    // Set mode to AI with imported mask
    if (bgMode) { bgMode.value = "ai"; bgMode.dispatchEvent(new Event("change")); }
    if (bgMaskSource) { bgMaskSource.value = "ai"; bgMaskSource.dispatchEvent(new Event("change")); }
    if (bgDecontaminate) bgDecontaminate.checked = true;
    if (bgAiInvertMask) bgAiInvertMask.checked = false;
    if (bgAiMaskExpand) bgAiMaskExpand.value = 0;
    if (bgAiMaskFeather) bgAiMaskFeather.value = 0;

    // Validate coverage
    const testSettings = getBgSettings();
    const testAlpha = getRefinedImportedAiAlpha(testSettings);
    const coverage = testAlpha ? getAlphaCoverage(testAlpha) : 0;
    if (coverage < 0.005) {
      // Hybrid mask is empty — fall back to ComfyUI if connected
      if (comfyuiConnected) {
        if (aiRemoveStatus) aiRemoveStatus.textContent = "Hybrid detection found nothing — trying ComfyUI...";
        await generateComfyuiMask();
        if (!importedAiMaskAlpha) throw new Error("Both hybrid and ComfyUI mask generation failed.");
      } else {
        throw new Error("No UI regions detected. Try adjusting the background tone or using manual tools.");
      }
    }

    if (aiRemoveStatus) {
      aiRemoveStatus.textContent = "Step 2/2: Extracting UI with edge protection...";
      aiRemoveStatus.style.color = "var(--accent)";
    }

    // Auto-trigger Process Image
    await processBackgroundImage();

    // Show the extracted result, not the mask preview
    if (bgPreviewTarget) bgPreviewTarget.value = "result";
    syncMainPreviewFromLayout();

    if (aiRemoveStatus) {
      aiRemoveStatus.textContent = "Done. Review results below and download.";
      aiRemoveStatus.style.color = "var(--accent)";
    }

  } catch (error) {
    console.error("AI Remove workflow failed:", error);
    if (aiRemoveStatus) {
      aiRemoveStatus.textContent = `AI Remove failed: ${error.message}`;
      aiRemoveStatus.style.color = "#e44";
    }
  } finally {
    if (aiRemoveButton) aiRemoveButton.disabled = false;
  }
}

// --- AI Enhance (color restoration from original) ---

let lastFinalCanvas = null;
let lastEnhancedCanvas = null;

function showAiEnhanceBlock() {
  if (!aiEnhanceBlock || !processedLayoutCanvas) return;
  aiEnhanceBlock.style.display = "block";
  // Copy final result to the final preview canvas
  const src = processedLayoutCanvas;
  aiFinalCanvas.width = src.width;
  aiFinalCanvas.height = src.height;
  aiFinalCanvas.getContext("2d").drawImage(src, 0, 0);
  lastFinalCanvas = src;
  // Clear enhanced preview
  aiEnhancedCanvas.width = 1;
  aiEnhancedCanvas.height = 1;
  if (downloadEnhancedButton) downloadEnhancedButton.disabled = true;
  if (aiEnhanceStatus) {
    aiEnhanceStatus.textContent = "Click AI Enhance to restore original UI colors at edges.";
    aiEnhanceStatus.style.color = "";
  }
}

function restoreEdgeColorsFromOriginal(finalCanvas, sourceCanvas) {
  const width = finalCanvas.width;
  const height = finalCanvas.height;
  const finalCtx = finalCanvas.getContext("2d");
  const sourceCtx = sourceCanvas.getContext("2d");
  const finalData = finalCtx.getImageData(0, 0, width, height);
  const sourceData = sourceCtx.getImageData(0, 0, width, height);
  const fd = finalData.data;
  const sd = sourceData.data;
  const resultCanvas = createCanvas(width, height);
  const resultCtx = resultCanvas.getContext("2d");
  const resultData = resultCtx.createImageData(width, height);
  const rd = resultData.data;
  const total = width * height;

  // Build distance-to-transparency map using two-pass Chebyshev transform.
  // After binarization most pixels are alpha 0 or 255. Edge pixels (alpha
  // 10-240) barely exist, so the old approach of blending only those pixels
  // produced invisible results. Instead we use the distance map to find
  // opaque pixels NEAR the transparency boundary and restore their colors
  // from the original + add anti-aliased feathering.
  const dist = new Uint8Array(total);
  dist.fill(255);
  for (let i = 0; i < total; i += 1) {
    if (fd[i * 4 + 3] === 0) dist[i] = 0;
  }
  // Forward pass (top-left to bottom-right)
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const idx = y * width + x;
      if (dist[idx] === 0) continue;
      let min = 255;
      if (x > 0) min = Math.min(min, dist[idx - 1]);
      if (y > 0) min = Math.min(min, dist[idx - width]);
      if (x > 0 && y > 0) min = Math.min(min, dist[idx - width - 1]);
      if (x < width - 1 && y > 0) min = Math.min(min, dist[idx - width + 1]);
      dist[idx] = Math.min(dist[idx], min + 1);
    }
  }
  // Backward pass (bottom-right to top-left)
  for (let y = height - 1; y >= 0; y -= 1) {
    for (let x = width - 1; x >= 0; x -= 1) {
      const idx = y * width + x;
      if (dist[idx] === 0) continue;
      let min = dist[idx];
      if (x < width - 1) min = Math.min(min, dist[idx + 1] + 1);
      if (y < height - 1) min = Math.min(min, dist[idx + width] + 1);
      if (x < width - 1 && y < height - 1) min = Math.min(min, dist[idx + width + 1] + 1);
      if (x > 0 && y < height - 1) min = Math.min(min, dist[idx + width - 1] + 1);
      dist[idx] = min;
    }
  }

  const BORDER = 6;   // restore original colors within 6px of edge
  for (let i = 0; i < total; i += 1) {
    const off = i * 4;
    const a = fd[off + 3];
    if (a === 0) {
      rd[off] = 0; rd[off + 1] = 0; rd[off + 2] = 0; rd[off + 3] = 0;
      continue;
    }
    const d = dist[i];
    if (d <= BORDER) {
      // Border zone: use original source RGB for cleanest colors
      rd[off]     = sd[off];
      rd[off + 1] = sd[off + 1];
      rd[off + 2] = sd[off + 2];
      // Graduated anti-aliased feather at outermost pixels
      if (d === 1) rd[off + 3] = 128;
      else if (d === 2) rd[off + 3] = 180;
      else if (d === 3) rd[off + 3] = 210;
      else if (d === 4) rd[off + 3] = 235;
      else rd[off + 3] = 255;
    } else {
      // Interior: blend original colors at moderate distance for
      // overall color fidelity improvement
      const blendDist = 12;
      if (d <= blendDist) {
        const t = (d - BORDER) / (blendDist - BORDER);
        rd[off]     = Math.round(sd[off]     * (1 - t) + fd[off]     * t);
        rd[off + 1] = Math.round(sd[off + 1] * (1 - t) + fd[off + 1] * t);
        rd[off + 2] = Math.round(sd[off + 2] * (1 - t) + fd[off + 2] * t);
      } else {
        rd[off]     = fd[off];
        rd[off + 1] = fd[off + 1];
        rd[off + 2] = fd[off + 2];
      }
      rd[off + 3] = a;
    }
  }

  resultCtx.putImageData(resultData, 0, 0);
  return resultCanvas;
}

function runAiEnhance() {
  if (!processedLayoutCanvas || !loadedImage) {
    if (aiEnhanceStatus) aiEnhanceStatus.textContent = "Process an image first.";
    return;
  }
  if (aiEnhanceStatus) {
    aiEnhanceStatus.textContent = "Enhancing edge colors...";
    aiEnhanceStatus.style.color = "var(--accent)";
  }

  // Create source canvas from loaded image
  const sourceCanvas = createCanvas(loadedImage.width, loadedImage.height);
  sourceCanvas.getContext("2d").drawImage(loadedImage, 0, 0);

  // Restore edge colors
  const enhanced = restoreEdgeColorsFromOriginal(processedLayoutCanvas, sourceCanvas);
  lastEnhancedCanvas = enhanced;

  // Show in preview
  aiEnhancedCanvas.width = enhanced.width;
  aiEnhancedCanvas.height = enhanced.height;
  aiEnhancedCanvas.getContext("2d").drawImage(enhanced, 0, 0);

  if (downloadEnhancedButton) downloadEnhancedButton.disabled = false;
  if (aiEnhanceStatus) {
    aiEnhanceStatus.textContent = "Color restoration complete. Compare and download.";
    aiEnhanceStatus.style.color = "var(--accent)";
  }
}

// --- Browser ONNX Segmentation ---

const ONNX_MODEL_URL = "u2netp.onnx";
const ONNX_INPUT_SIZE = 320;

async function loadOnnxModel() {
  if (onnxSession) return onnxSession;
  if (onnxModelLoading) return null;
  if (typeof ort === "undefined") {
    if (browserMaskStatus) browserMaskStatus.textContent = "Browser AI: ONNX Runtime not loaded (check internet connection)";
    return null;
  }
  onnxModelLoading = true;
  if (browserMaskStatus) browserMaskStatus.textContent = "Browser AI: downloading model (~5 MB)...";
  try {
    ort.env.wasm.wasmPaths = "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.17.0/dist/";
    onnxSession = await ort.InferenceSession.create(ONNX_MODEL_URL, {
      executionProviders: ["wasm"],
      graphOptimizationLevel: "all"
    });
    if (browserMaskStatus) browserMaskStatus.textContent = "Browser AI: model ready";
    return onnxSession;
  } catch (error) {
    console.error("ONNX model load failed:", error);
    if (browserMaskStatus) browserMaskStatus.textContent = `Browser AI: model load failed — ${error.message}`;
    return null;
  } finally {
    onnxModelLoading = false;
  }
}

function preprocessImageForOnnx(sourceCanvas) {
  const resized = createCanvas(ONNX_INPUT_SIZE, ONNX_INPUT_SIZE);
  const ctx = resized.getContext("2d");
  ctx.drawImage(sourceCanvas, 0, 0, ONNX_INPUT_SIZE, ONNX_INPUT_SIZE);
  const imageData = ctx.getImageData(0, 0, ONNX_INPUT_SIZE, ONNX_INPUT_SIZE);
  const data = imageData.data;
  const floats = new Float32Array(3 * ONNX_INPUT_SIZE * ONNX_INPUT_SIZE);
  const mean = [0.485, 0.456, 0.406];
  const std = [0.229, 0.224, 0.225];
  for (let i = 0; i < ONNX_INPUT_SIZE * ONNX_INPUT_SIZE; i++) {
    floats[i] = (data[i * 4] / 255 - mean[0]) / std[0];
    floats[ONNX_INPUT_SIZE * ONNX_INPUT_SIZE + i] = (data[i * 4 + 1] / 255 - mean[1]) / std[1];
    floats[2 * ONNX_INPUT_SIZE * ONNX_INPUT_SIZE + i] = (data[i * 4 + 2] / 255 - mean[2]) / std[2];
  }
  return new ort.Tensor("float32", floats, [1, 3, ONNX_INPUT_SIZE, ONNX_INPUT_SIZE]);
}

function postprocessOnnxOutput(output, targetWidth, targetHeight) {
  const outputData = output.data;
  const outputH = output.dims[2];
  const outputW = output.dims[3];

  // Sigmoid activation
  const sigmoid = new Float32Array(outputH * outputW);
  for (let i = 0; i < outputH * outputW; i++) {
    sigmoid[i] = 1 / (1 + Math.exp(-outputData[i]));
  }

  // Use a fixed threshold rather than min/max normalization
  // This avoids the problem where models output uniformly high values
  // Sigmoid 0.5 = decision boundary; scale [0,1] directly to [0,255]
  const maskCanvas = createCanvas(outputW, outputH);
  const maskCtx = maskCanvas.getContext("2d");
  const maskData = maskCtx.createImageData(outputW, outputH);
  for (let i = 0; i < outputH * outputW; i++) {
    const v = Math.round(Math.min(1, Math.max(0, sigmoid[i])) * 255);
    maskData.data[i * 4] = v;
    maskData.data[i * 4 + 1] = v;
    maskData.data[i * 4 + 2] = v;
    maskData.data[i * 4 + 3] = 255;
  }
  maskCtx.putImageData(maskData, 0, 0);

  // Scale to original image size
  const scaledCanvas = createCanvas(targetWidth, targetHeight);
  scaledCanvas.getContext("2d").drawImage(maskCanvas, 0, 0, targetWidth, targetHeight);
  return scaledCanvas;
}

async function generateBrowserMask() {
  if (!loadedImage) {
    if (bgStatus) bgStatus.textContent = "Load a source image first.";
    return;
  }
  if (browserMaskStatus) browserMaskStatus.textContent = "Browser AI: loading model...";
  if (bgStatus) bgStatus.textContent = "Running browser-side AI segmentation...";

  try {
    const session = await loadOnnxModel();
    if (!session) return;

    if (browserMaskStatus) browserMaskStatus.textContent = "Browser AI: running inference...";
    const sourceCanvas = createCanvas(loadedImage.width, loadedImage.height);
    sourceCanvas.getContext("2d").drawImage(loadedImage, 0, 0);

    const inputTensor = preprocessImageForOnnx(sourceCanvas);
    const feeds = {};
    const inputName = session.inputNames[0];
    feeds[inputName] = inputTensor;

    const startTime = performance.now();
    const results = await session.run(feeds);
    const elapsed = Math.round(performance.now() - startTime);

    // Use the first output (primary segmentation map)
    const outputName = session.outputNames[0];
    const outputTensor = results[outputName];

    const maskCanvas = postprocessOnnxOutput(outputTensor, loadedImage.width, loadedImage.height);
    importedAiMaskAlpha = alphaFromMaskCanvas(maskCanvas);

    // Auto-detect polarity
    let whiteCount = 0;
    for (let i = 0; i < importedAiMaskAlpha.length; i++) {
      if (importedAiMaskAlpha[i] > 128) whiteCount++;
    }
    const needsInvert = whiteCount > importedAiMaskAlpha.length * 0.5;
    if (needsInvert) {
      for (let i = 0; i < importedAiMaskAlpha.length; i++) {
        importedAiMaskAlpha[i] = 255 - importedAiMaskAlpha[i];
      }
    }
    if (bgAiInvertMask) bgAiInvertMask.checked = false;

    rebuildImportedAiMaskCanvas();
    if (bgMode) bgMode.value = "ai";
    if (bgMaskSource) bgMaskSource.value = "ai";
    if (bgPreviewTarget) bgPreviewTarget.value = "mask";
    syncMainPreviewFromLayout();
    updateActionStates();
    updateMaskStatusBlock();

    if (browserMaskStatus) browserMaskStatus.textContent = `Browser AI: mask generated (${elapsed}ms${needsInvert ? ", auto-inverted" : ""})`;
    if (bgStatus) bgStatus.textContent = `Browser AI mask ready (${elapsed}ms, draft quality). Click 'Process Image' to extract.`;

  } catch (error) {
    console.error("Browser ONNX mask failed:", error);
    if (browserMaskStatus) browserMaskStatus.textContent = `Browser AI: error — ${error.message}`;
    if (bgStatus) bgStatus.textContent = `Browser AI mask failed: ${error.message}`;
  }
}

async function generateBrowserMaskForImage(image) {
  const session = await loadOnnxModel();
  if (!session) throw new Error("ONNX model failed to load");
  const sourceCanvas = createCanvas(image.width, image.height);
  sourceCanvas.getContext("2d").drawImage(image, 0, 0);
  const inputTensor = preprocessImageForOnnx(sourceCanvas);
  const feeds = {};
  feeds[session.inputNames[0]] = inputTensor;
  const results = await session.run(feeds);
  const outputTensor = results[session.outputNames[0]];
  const maskCanvas = postprocessOnnxOutput(outputTensor, image.width, image.height);
  const alpha = alphaFromMaskCanvas(maskCanvas);
  let whiteCount = 0;
  for (let i = 0; i < alpha.length; i += 1) {
    if (alpha[i] > 128) whiteCount += 1;
  }
  if (whiteCount > alpha.length * 0.5) {
    for (let i = 0; i < alpha.length; i += 1) {
      alpha[i] = 255 - alpha[i];
    }
  }
  return alpha;
}

async function generateComfyuiMaskForImage(image, modelType) {
  const uploadCanvas = createCanvas(image.width, image.height);
  uploadCanvas.getContext("2d").drawImage(image, 0, 0);
  const blob = await new Promise(resolve => uploadCanvas.toBlob(resolve, "image/png"));
  const uploadFilename = "asset_editor_batch_" + Date.now() + ".png";
  await comfyuiUploadImage(blob, uploadFilename);
  const workflow = buildSegmentationWorkflow(uploadFilename, modelType, getActiveComfyuiConfig());
  const { promptId } = await comfyuiQueueWorkflow(workflow);
  const historyEntry = await comfyuiPollForCompletion(promptId);
  const outputImageInfo = extractOutputImageFilename(historyEntry);
  const saveResp = await fetch("/save-mask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(outputImageInfo)
  });
  if (!saveResp.ok) throw new Error("Failed to save mask locally: " + (await saveResp.text()));
  const maskImg = new Image();
  await new Promise((resolve, reject) => {
    maskImg.onload = resolve;
    maskImg.onerror = () => reject(new Error("Failed to load local mask file"));
    maskImg.src = "/_temp_mask.png?t=" + Date.now();
  });
  let maskCanvas = createCanvas(maskImg.width, maskImg.height);
  drawImagePreservingRGB(maskImg, maskCanvas);
  if (maskCanvas.width !== image.width || maskCanvas.height !== image.height) {
    const scaled = createCanvas(image.width, image.height);
    scaled.getContext("2d", { willReadFrequently: true }).drawImage(maskCanvas, 0, 0, image.width, image.height);
    maskCanvas = scaled;
  }
  const alpha = alphaFromMaskCanvas(maskCanvas);
  let whiteCount = 0;
  for (let i = 0; i < alpha.length; i += 1) {
    if (alpha[i] > 128) whiteCount += 1;
  }
  if (whiteCount > alpha.length * 0.5) {
    for (let i = 0; i < alpha.length; i += 1) {
      alpha[i] = 255 - alpha[i];
    }
  }
  return alpha;
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

function getCanvasCoords(canvas, event) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  return {
    x: Math.max(0, Math.min(canvas.width - 1, Math.floor((event.clientX - rect.left) * scaleX))),
    y: Math.max(0, Math.min(canvas.height - 1, Math.floor((event.clientY - rect.top) * scaleY)))
  };
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
  if (sampleBgButton) sampleBgButton.textContent = "Sample BG";
  if (sampleKeepButton) sampleKeepButton.textContent = "Keep Point";
  if (sampleKeepBoxButton) sampleKeepBoxButton.textContent = "Keep Box";
  if (sampleSubtractBoxButton) sampleSubtractBoxButton.textContent = "Remove Box";
  if (eraseKeepBoxButton) eraseKeepBoxButton.textContent = "Erase Keep Box";
  if (brushKeepButton) brushKeepButton.textContent = "Brush Keep";
  if (brushRemoveButton) brushRemoveButton.textContent = "Brush Remove";
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
  if (sampleBgButton) sampleBgButton.textContent = target === "background" ? "Stop Sampling" : "Sample BG";
  if (sampleKeepButton) sampleKeepButton.textContent = target === "keep" ? "Stop Marking" : "Keep Point";
  if (sampleKeepBoxButton) sampleKeepBoxButton.textContent = target === "keep-box" ? "Stop Drawing" : "Keep Box";
  if (sampleSubtractBoxButton) sampleSubtractBoxButton.textContent = target === "subtract-box" ? "Stop Drawing" : "Remove Box";
  if (eraseKeepBoxButton) eraseKeepBoxButton.textContent = target === "erase-box" ? "Stop Erasing" : "Erase Keep Box";
  if (brushKeepButton) brushKeepButton.textContent = target === "brush-keep" ? "Stop Brushing" : "Brush Keep";
  if (brushRemoveButton) brushRemoveButton.textContent = target === "brush-remove" ? "Stop Brushing" : "Brush Remove";
  originalCanvas.classList.add("sampling-active");
  samplingModeActive = true;
  if (target === "erase-box") {
    samplingHandler = (event) => {
      const sample = getCanvasCoords(originalCanvas, event);
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
      const sample = getCanvasCoords(originalCanvas, event);
      activeKeepBox = { left: sample.x, top: sample.y, right: sample.x, bottom: sample.y };
      renderOriginalPreview();
    };
    samplingMoveHandler = (event) => {
      if (!activeKeepBox) return;
      const sample = getCanvasCoords(originalCanvas, event);
      activeKeepBox.right = sample.x;
      activeKeepBox.bottom = sample.y;
      renderOriginalPreview();
    };
    samplingUpHandler = (event) => {
      if (!activeKeepBox) return;
      const sample = getCanvasCoords(originalCanvas, event);
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
      const sample = getCanvasCoords(originalCanvas, event);
      activeKeepBox = { left: sample.x, top: sample.y, right: sample.x, bottom: sample.y };
      renderOriginalPreview();
    };
    samplingMoveHandler = (event) => {
      if (!activeKeepBox) return;
      const sample = getCanvasCoords(originalCanvas, event);
      activeKeepBox.right = sample.x;
      activeKeepBox.bottom = sample.y;
      renderOriginalPreview();
    };
    samplingUpHandler = (event) => {
      if (!activeKeepBox) return;
      const sample = getCanvasCoords(originalCanvas, event);
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
      const sample = getCanvasCoords(originalCanvas, event);
      manualKeepBrushPoints.push({ x: sample.x, y: sample.y, radius: getCurrentBrushRadius() });
      updateSampleMeta();
      renderOriginalPreview();
      updateActionStates();
    };
    samplingMoveHandler = (event) => {
      if ((event.buttons & 1) !== 1) return;
      const sample = getCanvasCoords(originalCanvas, event);
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
      const sample = getCanvasCoords(originalCanvas, event);
      manualRemoveBrushPoints.push({ x: sample.x, y: sample.y, radius: getCurrentBrushRadius() });
      updateSampleMeta();
      renderOriginalPreview();
      updateActionStates();
    };
    samplingMoveHandler = (event) => {
      if ((event.buttons & 1) !== 1) return;
      const sample = getCanvasCoords(originalCanvas, event);
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
  const isWideBar = widthRatio >= 0.5 && heightRatio <= 0.35;
  const isThinVertical = aspect <= 0.35 && widthRatio <= 0.16;
  const isCompactPanel = widthRatio >= 0.1 && heightRatio >= 0.08 && heightRatio <= 0.55;
  const isLargePanel = widthRatio >= 0.3 && heightRatio >= 0.15;
  const likelyUi = sourceType !== "auto" || isThinHorizontal || isWideBar || isThinVertical || isCompactPanel || isLargePanel;
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
        alpha[i] = 128 + Math.round((Math.sqrt(minDistanceSq) / Math.max(1, edgeBand)) * 127);
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

function applySpillSuppression(imageData, alpha, backgroundSamples, strength) {
  if (!strength || strength <= 0 || !backgroundSamples.length) return;
  const { width, height, data } = imageData;
  const total = width * height;
  const factor = Math.min(1, strength / 100);

  const bgR = backgroundSamples[0].r;
  const bgG = backgroundSamples[0].g;
  const bgB = backgroundSamples[0].b;

  for (let i = 0; i < total; i += 1) {
    const a = alpha[i];
    if (a === 0 || a === 255) continue;
    const offset = i * 4;
    if (data[offset + 3] === 0) continue;

    const alphaRatio = a / 255;
    const r = data[offset];
    const g = data[offset + 1];
    const b = data[offset + 2];

    // Unpremultiply: recover true foreground color by removing background contribution
    const cleanR = Math.min(255, Math.max(0, Math.round((r - bgR * (1 - alphaRatio)) / Math.max(0.01, alphaRatio))));
    const cleanG = Math.min(255, Math.max(0, Math.round((g - bgG * (1 - alphaRatio)) / Math.max(0.01, alphaRatio))));
    const cleanB = Math.min(255, Math.max(0, Math.round((b - bgB * (1 - alphaRatio)) / Math.max(0.01, alphaRatio))));

    // Channel-limit clamp: prevent background-dominant channel from exceeding average of others
    const avgClean = (cleanR + cleanG + cleanB) / 3;
    const bgMax = Math.max(bgR, bgG, bgB);
    const bgDominantR = bgR === bgMax && bgR > bgG + 20 && bgR > bgB + 20;
    const bgDominantG = bgG === bgMax && bgG > bgR + 20 && bgG > bgB + 20;
    const bgDominantB = bgB === bgMax && bgB > bgR + 20 && bgB > bgG + 20;

    let finalR = cleanR;
    let finalG = cleanG;
    let finalB = cleanB;
    if (bgDominantR && cleanR > avgClean * 1.2) finalR = Math.round(Math.min(cleanR, (cleanG + cleanB) / 2));
    if (bgDominantG && cleanG > avgClean * 1.2) finalG = Math.round(Math.min(cleanG, (cleanR + cleanB) / 2));
    if (bgDominantB && cleanB > avgClean * 1.2) finalB = Math.round(Math.min(cleanB, (cleanR + cleanG) / 2));

    // Blend by spill strength and how close pixel is to the edge (lower alpha = more spill likely)
    const edgeWeight = Math.max(0, Math.min(1, (240 - a) / 160));
    const blend = factor * edgeWeight;
    data[offset]     = Math.round(r * (1 - blend) + finalR * blend);
    data[offset + 1] = Math.round(g * (1 - blend) + finalG * blend);
    data[offset + 2] = Math.round(b * (1 - blend) + finalB * blend);
  }
}

function computeEdgeStrengthMap(imageData) {
  const { width, height, data } = imageData;
  const strength = new Uint8ClampedArray(width * height);
  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      const idx = (y * width + x) * 4;
      const lIdx = idx - 4;
      const rIdx = idx + 4;
      const tIdx = idx - width * 4;
      const bIdx = idx + width * 4;
      let gx = 0;
      let gy = 0;
      for (let c = 0; c < 3; c += 1) {
        gx += Math.abs(data[rIdx + c] - data[lIdx + c]);
        gy += Math.abs(data[bIdx + c] - data[tIdx + c]);
      }
      strength[y * width + x] = Math.min(255, Math.round(Math.sqrt(gx * gx + gy * gy)));
    }
  }
  return strength;
}

function dilateEdgeMap(strength, width, height, radius) {
  const dilated = new Uint8ClampedArray(strength.length);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      let maxVal = strength[y * width + x];
      for (let dy = -radius; dy <= radius; dy += 1) {
        const ny = y + dy;
        if (ny < 0 || ny >= height) continue;
        for (let dx = -radius; dx <= radius; dx += 1) {
          const nx = x + dx;
          if (nx < 0 || nx >= width) continue;
          if (dx * dx + dy * dy > radius * radius) continue;
          const val = strength[ny * width + nx];
          if (val > maxVal) maxVal = val;
        }
      }
      dilated[y * width + x] = maxVal;
    }
  }
  return dilated;
}

function applyEdgeProtectionToAlpha(alpha, edgeStrength, width, height, minEdge, maxEdge, boundaryRadius) {
  // Build a boundary map: pixels within boundaryRadius of a foreground pixel (alpha >= 200)
  const total = width * height;
  const nearForeground = new Uint8Array(total);
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const i = y * width + x;
      if (alpha[i] < 200) continue;
      // Mark all neighbors within radius as near-foreground
      for (let dy = -boundaryRadius; dy <= boundaryRadius; dy += 1) {
        const ny = y + dy;
        if (ny < 0 || ny >= height) continue;
        for (let dx = -boundaryRadius; dx <= boundaryRadius; dx += 1) {
          const nx = x + dx;
          if (nx < 0 || nx >= width) continue;
          nearForeground[ny * width + nx] = 1;
        }
      }
    }
  }

  const protected_ = new Uint8ClampedArray(alpha);
  const range = Math.max(1, maxEdge - minEdge);
  for (let i = 0; i < total; i += 1) {
    if (alpha[i] >= 255) continue;
    // Only protect pixels near the AI foreground boundary
    if (!nearForeground[i]) continue;
    const raw = edgeStrength[i];
    if (raw <= minEdge) continue;
    const edgeAlpha = Math.round(Math.min(1, (raw - minEdge) / range) * 255);
    if (edgeAlpha > protected_[i]) {
      protected_[i] = edgeAlpha;
    }
  }
  return protected_;
}

function buildLocalBackgroundColors(imageData, alpha, width, height, radius) {
  const { data } = imageData;
  const total = width * height;
  const localBg = new Float32Array(total * 3);
  for (let i = 0; i < total; i += 1) {
    const a = alpha[i];
    if (a === 0 || a === 255) continue;
    const x = i % width;
    const y = Math.floor(i / width);
    let sumR = 0, sumG = 0, sumB = 0, count = 0;
    for (let dy = -radius; dy <= radius; dy += 1) {
      const ny = y + dy;
      if (ny < 0 || ny >= height) continue;
      for (let dx = -radius; dx <= radius; dx += 1) {
        const nx = x + dx;
        if (nx < 0 || nx >= width) continue;
        const ni = ny * width + nx;
        if (alpha[ni] !== 0) continue;
        const offset = ni * 4;
        sumR += data[offset];
        sumG += data[offset + 1];
        sumB += data[offset + 2];
        count += 1;
      }
    }
    if (count > 0) {
      localBg[i * 3] = sumR / count;
      localBg[i * 3 + 1] = sumG / count;
      localBg[i * 3 + 2] = sumB / count;
    } else {
      localBg[i * 3] = -1;
    }
  }
  return localBg;
}

function applyLocalSpillSuppression(imageData, alpha, localBg, width, height) {
  const { data } = imageData;
  const total = width * height;
  for (let i = 0; i < total; i += 1) {
    const a = alpha[i];
    if (a === 0 || a === 255) continue;
    if (localBg[i * 3] < 0) continue;
    const offset = i * 4;
    if (data[offset + 3] === 0) continue;
    const bgR = localBg[i * 3];
    const bgG = localBg[i * 3 + 1];
    const bgB = localBg[i * 3 + 2];
    const alphaRatio = Math.max(0.01, a / 255);
    const r = data[offset];
    const g = data[offset + 1];
    const b = data[offset + 2];
    const cleanR = Math.min(255, Math.max(0, Math.round((r - bgR * (1 - alphaRatio)) / alphaRatio)));
    const cleanG = Math.min(255, Math.max(0, Math.round((g - bgG * (1 - alphaRatio)) / alphaRatio)));
    const cleanB = Math.min(255, Math.max(0, Math.round((b - bgB * (1 - alphaRatio)) / alphaRatio)));
    const edgeWeight = Math.max(0, Math.min(1, (240 - a) / 160));
    data[offset]     = Math.round(r * (1 - edgeWeight) + cleanR * edgeWeight);
    data[offset + 1] = Math.round(g * (1 - edgeWeight) + cleanG * edgeWeight);
    data[offset + 2] = Math.round(b * (1 - edgeWeight) + cleanB * edgeWeight);
  }
}

function buildProcessedBackgroundFromAlpha(sourceCanvas, sourceData, alpha, settings, backgroundSamples) {
  // AI mode: apply edge protection + local spill cleanup
  if (settings.mode === "remove" && settings.decontaminate && importedAiMaskAlpha) {
    const edgeStrength = computeEdgeStrengthMap(sourceData);
    const dilatedEdges = dilateEdgeMap(edgeStrength, sourceCanvas.width, sourceCanvas.height, 3);
    alpha = applyEdgeProtectionToAlpha(alpha, dilatedEdges, sourceCanvas.width, sourceCanvas.height, 30, 120, 6);
  }

  const resultData = applyAlphaToImage(
    sourceData,
    alpha,
    settings.decontaminate,
    backgroundSamples[0],
    settings.componentAlpha,
    settings.preserveColor
  );

  // AI mode: apply local background-aware spill suppression
  if (settings.decontaminate && importedAiMaskAlpha) {
    const localBg = buildLocalBackgroundColors(sourceData, alpha, sourceCanvas.width, sourceCanvas.height, 4);
    applyLocalSpillSuppression(resultData, alpha, localBg, sourceCanvas.width, sourceCanvas.height);
  }

  if (settings.aiSpill > 0 && backgroundSamples.length) {
    applySpillSuppression(resultData, alpha, backgroundSamples, settings.aiSpill);
  }
  if (settings.decontaminate) {
    const isAiDetectedMask = !!(importedAiMaskAlpha);
    const cleanupPasses = isAiDetectedMask ? (importedAiMaskIsInternal ? 2 : 1)
      : settings.edgeCleanupStrength >= 80 ? 3
      : settings.edgeCleanupStrength >= 45 ? 2
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
  // Zero out rejected components using per-pixel labels — avoids
  // destroying accepted components whose bounding boxes overlap.
  const componentLabels = rawBoxes._labels;
  if (rejected.length > 0 && boxes.length > 0 && importedAiMaskAlpha && componentLabels) {
    // Only clean up if some components were accepted — don't blank the entire result
    const rejectedLabels = new Set(rejected.map(b => b.label));
    const rd = resultData.data;
    const total = sourceCanvas.width * sourceCanvas.height;
    for (let i = 0; i < total; i += 1) {
      if (rejectedLabels.has(componentLabels[i])) {
        const idx = i * 4;
        rd[idx] = 0; rd[idx + 1] = 0; rd[idx + 2] = 0; rd[idx + 3] = 0;
      }
    }
    fullLayoutCanvas.getContext("2d").putImageData(resultData, 0, 0);
  }
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
  let autoPanelSourceBoxes = settings.mode === "multi" && (settings.manualKeepSamples.length || settings.manualKeepBoxes.length || settings.manualKeepBrushPoints.length)
    ? boxes.filter((box) =>
      settings.manualKeepSamples.some((sample) => sample.x >= box.left && sample.x < box.right && sample.y >= box.top && sample.y < box.bottom)
      || settings.manualKeepBoxes.some((keepBox) => {
        const normalized = normalizeBox(keepBox);
        return !(normalized.right <= box.left || normalized.left >= box.right || normalized.bottom <= box.top || normalized.top >= box.bottom);
      })
      || settings.manualKeepBrushPoints.some((point) => point.x >= box.left && point.x < box.right && point.y >= box.top && point.y < box.bottom))
    : boxes;
  // If no boxes were accepted but we have rejected full-image components,
  // use those for splitting into individual UI panels.
  if (autoPanelSourceBoxes.length === 0 && rejected.length > 0) {
    autoPanelSourceBoxes = rejected.filter(r => r.count > settings.componentPixels);
  }
  // Split large components at horizontal gaps to separate top bar from
  // bottom bar. Scans for rows with very few opaque pixels within a box.
  const splitAutoPanels = [];
  for (const box of autoPanelSourceBoxes) {
    const boxH = box.bottom - box.top;
    if (boxH > sourceCanvas.height * 0.25) {
      const boxW = box.right - box.left;
      const gapThreshold = boxW * 0.05;
      const bands = [];
      let bandStart = box.top;
      let inGap = false;
      for (let y = box.top; y < box.bottom; y += 1) {
        let count = 0;
        for (let x = box.left; x < box.right; x += 1) {
          if (alpha[y * sourceCanvas.width + x] >= settings.componentAlpha) count += 1;
        }
        const isGap = count < gapThreshold;
        if (isGap && !inGap) {
          if (y - bandStart > 10) bands.push({ top: bandStart, bottom: y });
          inGap = true;
        }
        if (!isGap && inGap) { bandStart = y; inGap = false; }
      }
      if (!inGap && box.bottom - bandStart > 10) bands.push({ top: bandStart, bottom: box.bottom });
      if (bands.length > 1) {
        for (const band of bands) {
          let minX = sourceCanvas.width, maxX = 0, pixCount = 0;
          for (let y = band.top; y < band.bottom; y += 1) {
            for (let x = box.left; x < box.right; x += 1) {
              if (alpha[y * sourceCanvas.width + x] >= settings.componentAlpha) {
                minX = Math.min(minX, x); maxX = Math.max(maxX, x); pixCount += 1;
              }
            }
          }
          if (pixCount >= Math.min(settings.componentPixels, 500)) {
            splitAutoPanels.push({
              left: minX, top: band.top, right: maxX + 1, bottom: band.bottom,
              width: maxX - minX + 1, height: band.bottom - band.top,
              area: (maxX - minX + 1) * (band.bottom - band.top), count: pixCount,
              solidity: pixCount / Math.max(1, (maxX - minX + 1) * (band.bottom - band.top)),
              edgeTouches: box.edgeTouches, sourceType: box.sourceType
            });
          }
        }
      } else {
        splitAutoPanels.push(box);
      }
    } else {
      splitAutoPanels.push(box);
    }
  }
  // Phase 2: Vertical gap splitting — within each horizontal band, scan
  // columns for gaps to separate individual objects (portrait frame, chat
  // panel, button row). Same approach as horizontal splitting.
  const vertSplitPanels = [];
  for (const band of splitAutoPanels) {
    const bandW = band.right - band.left;
    const bandH = band.bottom - band.top;
    // Only vertically split wide bands (> 40% of image width)
    if (bandW > sourceCanvas.width * 0.4) {
      const vGapThreshold = bandH * 0.08;
      const cols = [];
      let colStart = band.left;
      let inVGap = false;
      for (let x = band.left; x <= band.right; x += 1) {
        let count = 0;
        if (x < band.right) {
          for (let y = band.top; y < band.bottom; y += 1) {
            if (alpha[y * sourceCanvas.width + x] >= settings.componentAlpha) count += 1;
          }
        }
        const isVGap = x >= band.right || count < vGapThreshold;
        if (isVGap && !inVGap) {
          if (x - colStart > 15) cols.push({ left: colStart, right: x });
          inVGap = true;
        }
        if (!isVGap && inVGap) { colStart = x; inVGap = false; }
      }
      if (cols.length > 1) {
        for (const col of cols) {
          let minY = band.bottom, maxY = band.top, pixCount = 0;
          for (let y = band.top; y < band.bottom; y += 1) {
            for (let x = col.left; x < col.right; x += 1) {
              if (alpha[y * sourceCanvas.width + x] >= settings.componentAlpha) {
                minY = Math.min(minY, y); maxY = Math.max(maxY, y); pixCount += 1;
              }
            }
          }
          if (pixCount >= Math.min(settings.componentPixels, 300)) {
            const ow = col.right - col.left, oh = maxY - minY + 1;
            vertSplitPanels.push({
              left: col.left, top: minY, right: col.right, bottom: maxY + 1,
              width: ow, height: oh, area: ow * oh, count: pixCount,
              solidity: pixCount / Math.max(1, ow * oh),
              edgeTouches: band.edgeTouches, sourceType: band.sourceType
            });
          }
        }
      } else {
        vertSplitPanels.push(band);
      }
    } else {
      vertSplitPanels.push(band);
    }
  }
  const finalAutoPanels = vertSplitPanels.length > 0 ? vertSplitPanels : autoPanelSourceBoxes;
  const manualPanelBoxes = settings.mode === "multi" && settings.manualKeepBoxes.length
    ? getManualKeepPanelBoxes(sourceCanvas.width, sourceCanvas.height, settings.manualKeepBoxes, settings.componentPad)
    : [];
  const brushPanelBoxes = settings.mode === "multi" && settings.manualKeepBrushPoints.length
    ? getBrushPanelBoxes(sourceCanvas.width, sourceCanvas.height, settings.manualKeepBrushPoints, settings.componentPad)
    : [];
  const panelSourceBoxes = [
    ...finalAutoPanels.map((box) => ({ ...box, sourceType: box.sourceType || "auto" })),
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
  // Per-pixel component labels: 0 = no component, 1+ = component index
  const labels = new Uint16Array(width * height);
  const boxes = [];
  let nextLabel = 1;
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const startIndex = y * width + x;
      if (seen[startIndex] || alpha[startIndex] < alphaThreshold) continue;
      const queue = [startIndex];
      seen[startIndex] = 1;
      const currentLabel = nextLabel++;
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
        const ci = queue[head++];
        const cx = ci % width;
        const cy = (ci - cx) / width;
        count += 1;
        labels[ci] = currentLabel;
        minX = Math.min(minX, cx);
        minY = Math.min(minY, cy);
        maxX = Math.max(maxX, cx);
        maxY = Math.max(maxY, cy);
        if (cx === 0) touchesLeft = true;
        if (cy === 0) touchesTop = true;
        if (cx === width - 1) touchesRight = true;
        if (cy === height - 1) touchesBottom = true;
        if (cx > 0)           { const ni = ci - 1;     if (!seen[ni] && alpha[ni] >= alphaThreshold) { seen[ni] = 1; queue.push(ni); } }
        if (cx < width - 1)   { const ni = ci + 1;     if (!seen[ni] && alpha[ni] >= alphaThreshold) { seen[ni] = 1; queue.push(ni); } }
        if (cy > 0)           { const ni = ci - width;  if (!seen[ni] && alpha[ni] >= alphaThreshold) { seen[ni] = 1; queue.push(ni); } }
        if (cy < height - 1)  { const ni = ci + width;  if (!seen[ni] && alpha[ni] >= alphaThreshold) { seen[ni] = 1; queue.push(ni); } }
      }
      if (count >= minPixels) {
        const boxWidth = maxX - minX + 1;
        const boxHeight = maxY - minY + 1;
        const area = boxWidth * boxHeight;
        boxes.push({
          label: currentLabel,
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
  const result = boxes.slice(0, 8);
  result._labels = labels;
  return result;
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
    // Wide horizontal strips (bars, toolbars) naturally have low solidity because
    // they span full width but contain discrete UI elements with gaps between them.
    const isWideHorizontalStrip = widthRatio > 0.5 && heightRatio < 0.40;
    const probablySceneFragment = isWideHorizontalStrip ? false :
      (isHuge && edgeHeavy && box.solidity < 0.7) ||
      (box.edgeTouches >= 3 && box.solidity < 0.82) ||
      (heightRatio > 0.55 && widthRatio < 0.2) ||
      (widthRatio > 0.55 && heightRatio > 0.55) ||
      (box.solidity < 0.35) ||
      (box.solidity < 0.55 && !isHorizontalBar && !isVerticalBar && !isPanelLike);

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
      (!probablySceneFragment && isDenseEnough && (isHorizontalBar || isVerticalBar || isPanelLike || isWideHorizontalStrip));

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
function loadImageFromFile(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error("Failed to load " + file.name)); };
    img.src = url;
  });
}

function toggleBatchMode(active) {
  batchModeActive = active;
  if (singleFileField) singleFileField.style.display = active ? "none" : "";
  if (batchFileField) batchFileField.style.display = active ? "" : "none";
  if (batchFileCount) batchFileCount.style.display = active ? "" : "none";
  if (batchAiSourceField) batchAiSourceField.style.display = active ? "" : "none";
  if (batchProgressBlock) batchProgressBlock.style.display = "none";
  if (!active) {
    batchFiles = [];
    batchResults = [];
    if (batchFileCount) batchFileCount.textContent = "No files selected.";
    if (batchInputFiles) batchInputFiles.value = "";
  }
  const multiOption = bgMode ? bgMode.querySelector('option[value="multi"]') : null;
  if (multiOption) multiOption.disabled = active;
  if (active && bgMode && bgMode.value === "multi") bgMode.value = "remove";
  updateActionStates();
}

async function processBatchImages() {
  if (!batchFiles.length) {
    if (bgStatus) bgStatus.textContent = "No batch files selected.";
    return;
  }

  const aiSource = batchAiSource ? batchAiSource.value : "browser";
  const modelType = comfyuiModel ? comfyuiModel.value : "BiRefNet-general";

  if (aiSource === "comfyui") {
    const connected = await testComfyuiConnection();
    if (!connected) {
      if (bgStatus) bgStatus.textContent = "ComfyUI connection failed. Check the server or switch to another mode.";
      return;
    }
  }

  const settings = getBgSettings();
  settings.manualBackgroundColor = null;
  settings.manualBackgroundSamples = [];
  settings.manualKeepSamples = [];
  settings.manualKeepBoxes = [];
  settings.manualSubtractBoxes = [];
  settings.manualKeepBrushPoints = [];
  settings.manualRemoveBrushPoints = [];

  batchProcessing = true;
  batchCancelRequested = false;
  cancelProcessingRequested = false;
  batchResults = [];
  if (batchProgressBlock) batchProgressBlock.style.display = "";
  if (batchProgressBar) batchProgressBar.style.width = "0%";
  setProcessingState(true, "Starting batch...");

  const total = batchFiles.length;

  for (let i = 0; i < total; i += 1) {
    if (batchCancelRequested || cancelProcessingRequested) {
      if (bgStatus) bgStatus.textContent = `Batch canceled after ${i} of ${total} images.`;
      break;
    }

    const file = batchFiles[i];
    const fileName = file.name.replace(/\.[^.]+$/, "");
    const progressPct = Math.round((i / total) * 100);
    if (batchProgressBar) batchProgressBar.style.width = progressPct + "%";
    if (batchProgressLabel) batchProgressLabel.textContent = `Batch: ${i + 1} / ${total}`;
    if (batchCurrentFile) batchCurrentFile.textContent = file.name;

    try {
      // Load image
      const image = await loadImageFromFile(file);
      loadedImage = image;

      const sourceCanvas = createCanvas(image.width, image.height);
      sourceCanvas.getContext("2d").drawImage(image, 0, 0);
      const sourceData = sourceCanvas.getContext("2d").getImageData(0, 0, sourceCanvas.width, sourceCanvas.height);
      const backgroundSamples = [sampleBackgroundColor(sourceData, settings.tone)];
      let processed;

      if (aiSource === "direct") {
        // Direct background removal — no AI mask
        if (bgStatus) bgStatus.textContent = `Batch ${i + 1}/${total}: removing background — ${file.name}...`;
        setProcessingState(true, `Batch ${i + 1}/${total}: removing BG — ${file.name}`);

        processed = settings.mode === "crop"
          ? processObjectCrop(sourceCanvas, sourceData, settings, backgroundSamples[0])
          : await processBackgroundRemoval(sourceCanvas, sourceData, settings, backgroundSamples, (percent) => {
              if (bgStatus) bgStatus.textContent = `Batch ${i + 1}/${total}: ${file.name} — ${percent}%`;
              setProcessingState(true, `Batch ${i + 1}/${total}: ${file.name} — ${percent}%`);
            });
      } else {
        // Two-pass: AI mask then background removal
        // Pass 1: Generate AI mask
        if (bgStatus) bgStatus.textContent = `Batch ${i + 1}/${total}: generating AI mask for ${file.name}...`;
        setProcessingState(true, `Batch ${i + 1}/${total}: AI mask — ${file.name}`);

        let maskAlpha;
        if (aiSource === "comfyui") {
          maskAlpha = await generateComfyuiMaskForImage(image, modelType);
        } else {
          maskAlpha = await generateBrowserMaskForImage(image);
        }

        if (batchCancelRequested || cancelProcessingRequested) {
          if (bgStatus) bgStatus.textContent = `Batch canceled after ${i} of ${total} images.`;
          break;
        }

        // Pass 2: Background removal using the AI mask
        if (bgStatus) bgStatus.textContent = `Batch ${i + 1}/${total}: extracting ${file.name}...`;
        setProcessingState(true, `Batch ${i + 1}/${total}: extracting — ${file.name}`);

        importedAiMaskAlpha = maskAlpha;
        const aiSettings = { ...settings, mode: "ai", maskSource: "ai" };
        const refinedAlpha = refineImportedAiMaskAlpha(importedAiMaskAlpha, image.width, image.height, aiSettings);

        processed = buildProcessedBackgroundFromAlpha(
          sourceCanvas,
          sourceData,
          refinedAlpha,
          { ...aiSettings, mode: "remove", decontaminate: true },
          backgroundSamples
        );
      }

      batchResults.push({ fileName, canvas: processed.layoutCanvas || processed.canvas });
      downloadCanvas(processed.layoutCanvas || processed.canvas, `${fileName}_extracted.png`);

      drawImageOnCanvas(resultCanvas, processed.layoutCanvas || processed.canvas);
      if (resultMeta) resultMeta.textContent = `Batch ${i + 1}/${total}: ${fileName}`;

      // Reset per-image mask state
      importedAiMaskAlpha = null;
      aiMaskCanvas = null;

      await new Promise(r => setTimeout(r, 50));
    } catch (err) {
      console.error(`Batch error on ${file.name}:`, err);
      if (bgStatus) bgStatus.textContent = `Error on ${file.name}: ${err.message}. Continuing...`;
      importedAiMaskAlpha = null;
      aiMaskCanvas = null;
      await new Promise(r => setTimeout(r, 500));
    }
  }

  if (batchProgressBar) batchProgressBar.style.width = "100%";
  if (batchProgressLabel) batchProgressLabel.textContent = `Batch: ${batchResults.length} / ${total} complete`;
  if (batchCurrentFile) batchCurrentFile.textContent = "";
  if (!batchCancelRequested && !cancelProcessingRequested) {
    if (bgStatus) bgStatus.textContent = `Batch complete. ${batchResults.length} of ${total} images processed and downloaded.`;
  }
  batchProcessing = false;
  cancelProcessingRequested = false;
  setProcessingState(false);
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
    // Show AI Enhance block and auto-run enhance after AI mode processing
    if (settings.mode === "ai" && importedAiMaskAlpha) {
      showAiEnhanceBlock();
      runAiEnhance();
    }
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
  form.artStyle.value = "fantasy";
  form.checkpoint.value = "juggernautXL";
  form.remover.value = "essentials";
  form.assetType.value = "ornate inventory button";
  form.material.value = "ornate gold border, carved stone backing, glowing rune core";
  form.batchMode.checked = false;
  form.pixelEdges.checked = false;
  refreshOutput(formStateToConfig());
});

bgPreset.addEventListener("change", () => applyPreset(bgPreset.value));
// Auto-switch to matching balanced preset when tone changes
bgTone.addEventListener("change", () => {
  const tone = bgTone.value;
  const currentPreset = bgPreset.value;
  if (tone === "dark" && currentPreset.startsWith("light-")) {
    bgPreset.value = currentPreset.replace("light-", "dark-");
    applyPreset(bgPreset.value);
  } else if (tone === "light" && currentPreset.startsWith("dark-")) {
    bgPreset.value = currentPreset.replace("dark-", "light-");
    applyPreset(bgPreset.value);
  }
});
[bgThreshold, bgSoftness, bgAlphaFloor, bgAlphaCeiling, bgEdgeCleanupStrength, bgComponentAlpha, bgComponentPixels, bgComponentPad, bgObjectPad].forEach((input) => { if (input) input.addEventListener("input", updateRangeLabels); });
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
if (batchModeToggle) {
  batchModeToggle.addEventListener("change", () => toggleBatchMode(batchModeToggle.checked));
}
if (batchInputFiles) {
  batchInputFiles.addEventListener("change", (event) => {
    batchFiles = Array.from(event.target.files || []);
    if (batchFileCount) {
      batchFileCount.textContent = batchFiles.length
        ? `${batchFiles.length} image${batchFiles.length === 1 ? "" : "s"} selected.`
        : "No files selected.";
    }
    updateActionStates();
  });
}
processBgButton.addEventListener("click", () => {
  if (batchModeActive) {
    processBatchImages();
  } else {
    processBackgroundImage();
  }
});
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
    if (batchProcessing) {
      batchCancelRequested = true;
      cancelProcessingRequested = true;
      bgStatus.textContent = "Batch cancel requested. Finishing current image...";
      return;
    }
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
    brushEditHistory = brushEditHistory.filter(entry => entry.kind !== "keep");
    activeBrushStroke = null;
    updateSampleMeta();
    renderOriginalPreview();
    updateActionStates();
    bgStatus.textContent = "Cleared brush keep marks.";
  });
}
if (clearBrushRemoveButton) {
  clearBrushRemoveButton.addEventListener("click", () => {
    manualRemoveBrushPoints = [];
    brushEditHistory = brushEditHistory.filter(entry => entry.kind !== "remove");
    activeBrushStroke = null;
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
if (comfyuiConnectButton) {
  comfyuiConnectButton.addEventListener("click", testComfyuiConnection);
}
if (comfyuiGenerateMaskButton) {
  comfyuiGenerateMaskButton.addEventListener("click", generateComfyuiMask);
}
if (browserMaskButton) {
  browserMaskButton.addEventListener("click", generateBrowserMask);
}
if (aiRemoveButton) {
  aiRemoveButton.addEventListener("click", aiRemoveWorkflow);
}
if (aiEnhanceButton) {
  aiEnhanceButton.addEventListener("click", runAiEnhance);
}
if (downloadFinalButton) {
  downloadFinalButton.addEventListener("click", () => {
    if (lastFinalCanvas) downloadCanvas(lastFinalCanvas, `${loadedFileName}_final.png`);
  });
}
if (downloadEnhancedButton) {
  downloadEnhancedButton.addEventListener("click", () => {
    if (lastEnhancedCanvas) downloadCanvas(lastEnhancedCanvas, `${loadedFileName}_enhanced.png`);
  });
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
bgStatus.textContent = "Upload an image, select background tone, then click AI Remove.";

// Auto-connect to ComfyUI on page load (silent)
testComfyuiConnection().catch(() => {});
updateActionStates();
updateSplitFilterButtons();
updateSplitPanelThresholdLabel();
updateEditorLayout();
updateMaskStatusBlock();
