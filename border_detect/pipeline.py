"""V5+ invert-selection pipeline — ported from app.js buildBlackBorderUiMask.

Full pipeline: border detection → segmentation → background classification →
invert selection → mask building → multi-spectrum cleanup.

This is the single source of truth for border detection. The JS side just
sends the image and receives the final alpha mask.
"""

import cv2
import numpy as np
from scipy import ndimage


def run_pipeline(img_bgr, multi_spectrum_map=None):
    """Run the full v5+ pipeline with optional multi-spectrum cleanup.

    Args:
        img_bgr: (H, W, 3) uint8 BGR image
        multi_spectrum_map: optional (H, W) float32 [0,1] border confidence from ensemble

    Returns:
        alpha: (H, W) uint8 mask — 255=keep, 0=remove, intermediate=feathered edge
    """
    h, w = img_bgr.shape[:2]
    total = h * w
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB).astype(np.float64)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # ── PASS 1: Color gradient map ──
    gradient = _compute_rgb_gradient(rgb, h, w)

    # Adaptive threshold
    median_grad = np.median(gradient)
    grad_threshold = float(np.clip(median_grad * 3, 25, 50))

    # ── PASS 2: Border detection (gradient + dark achromatic) ──
    edges = _compute_edge_strength(gray)
    dist_to_edge = _distance_transform_from_edges(edges, threshold=35)

    is_border = np.zeros((h, w), dtype=np.uint8)

    # Criterion A: color gradient exceeds threshold
    is_border[gradient >= grad_threshold] = 1

    # Criterion B: dark achromatic pixels near contrast edges
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    max_ch = np.maximum(np.maximum(r, g), b)
    min_ch = np.minimum(np.minimum(r, g), b)
    spread = max_ch - min_ch
    dark_achromatic = (max_ch < 55) & (spread <= 12) & (dist_to_edge <= 2)
    is_border[dark_achromatic & (is_border == 0)] = 1

    # Propagate dark borders through adjacent dark pixels (2 passes)
    for _ in range(2):
        prev = is_border.copy()
        dark_eligible = (max_ch < 45) & (spread <= 12) & (is_border == 0)
        # Check if any 4-neighbor is border
        neighbor_border = np.zeros((h, w), dtype=bool)
        neighbor_border[1:, :] |= prev[:-1, :] > 0
        neighbor_border[:-1, :] |= prev[1:, :] > 0
        neighbor_border[:, 1:] |= prev[:, :-1] > 0
        neighbor_border[:, :-1] |= prev[:, 1:] > 0
        is_border[dark_eligible & neighbor_border] = 1

    # Remove tiny border fragments (< 15 connected pixels)
    is_border = _remove_small_components(is_border, min_size=15)

    # ── PASS 2b: Border enhancement ──
    lower_threshold = grad_threshold * 0.5
    is_border = _hysteresis_enhance(is_border, gradient, lower_threshold, passes=4)
    is_border = _gap_bridging(is_border, h, w, max_gap=4)

    # ── Pass 2c: Structural horizontal borders ──
    # Detect continuous horizontal dark runs at top 25% and bottom 35% of image
    is_border = _structural_horizontal_borders(is_border, rgb, h, w)

    # ── PASS 3: Component labeling ──
    # Invert border mask: regions are non-border connected components
    region_mask = (is_border == 0).astype(np.uint8)
    num_labels, labels = cv2.connectedComponents(region_mask, connectivity=4)

    # ── PASS 4: Object metrics ──
    objects = _compute_object_metrics(labels, num_labels, rgb, edges, h, w)

    # ── PASS 5-6: Background identification + secondary backgrounds ──
    bg_labels = _classify_backgrounds(objects, labels, is_border, h, w, total)

    # ── PASS 7: Invert selection ──
    selection = np.zeros((h, w), dtype=np.uint8)
    for obj in objects:
        if obj["label"] not in bg_labels:
            selection[labels == obj["label"]] = 1

    # Include border pixels adjacent to selected regions
    sel_dilated = cv2.dilate(selection, np.ones((3, 3), np.uint8))
    border_near_selection = (is_border > 0) & (sel_dilated > 0)
    selection[border_near_selection] = 1

    # ── PASS 8: Build mask ──
    alpha = np.zeros((h, w), dtype=np.uint8)
    alpha[selection > 0] = 255

    # Remove tiny fragments (< 0.2% of image)
    alpha = _remove_small_alpha_fragments(alpha, min_frac=0.002)

    # Soft edge feathering
    alpha = _feather_edges(alpha, radius=2)

    # Remove floating debris
    alpha = _remove_debris(alpha, h, w)

    # ── Multi-spectrum cleanup pass ──
    if multi_spectrum_map is not None:
        alpha = _multi_spectrum_cleanup(alpha, multi_spectrum_map, rgb, gray, h, w)

    coverage = (alpha > 0).sum() / total
    print(f"  [Pipeline] coverage={coverage*100:.1f}%, "
          f"objects={len(objects)}, bg_regions={len(bg_labels)}")

    return alpha


def _compute_rgb_gradient(rgb, h, w):
    """Max Euclidean color distance to 4-connected neighbors."""
    gradient = np.zeros((h, w), dtype=np.float64)
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        shifted = np.roll(np.roll(rgb, dy, axis=0), dx, axis=1)
        dsq = np.sum((rgb - shifted) ** 2, axis=2)
        gradient = np.maximum(gradient, dsq)
    gradient = np.sqrt(gradient)
    # Zero out edges affected by roll wraparound
    gradient[0, :] = 0; gradient[-1, :] = 0
    gradient[:, 0] = 0; gradient[:, -1] = 0
    return gradient


def _structural_horizontal_borders(is_border, rgb, h, w):
    """Detect continuous horizontal lines of dark pixels at top/bottom of image."""
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    max_ch = np.maximum(np.maximum(r, g), b)
    min_ch = np.minimum(np.minimum(r, g), b)
    spread = max_ch - min_ch
    dark_pixel = (max_ch < 70) & (spread <= 18)

    added = 0
    for y in range(h):
        y_ratio = y / h
        if y_ratio > 0.25 and y_ratio < 0.65:
            continue
        row_dark = dark_pixel[y, :] & (~is_border[y, :].astype(bool))
        # Find longest continuous dark run
        max_run = 0
        current_run = 0
        dark_total = 0
        for x in range(w):
            if row_dark[x]:
                current_run += 1
                dark_total += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 0
        if max_run > w * 0.20 and dark_total > w * 0.25:
            new_borders = row_dark & (~is_border[y, :].astype(bool))
            added += new_borders.sum()
            is_border[y, new_borders] = 1

    if added > 0:
        print(f"  [Pipeline] Structural horizontal borders: +{added} pixels")
    return is_border


def _compute_edge_strength(gray):
    """Sobel gradient magnitude as edge strength map."""
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    return np.sqrt(gx**2 + gy**2)


def _distance_transform_from_edges(edges, threshold=35):
    """Compute distance from each pixel to the nearest strong edge."""
    edge_binary = (edges >= threshold).astype(np.uint8)
    # Invert: distance transform computes distance from 0-pixels
    dist = cv2.distanceTransform(1 - edge_binary, cv2.DIST_L1, 3)
    return dist


def _remove_small_components(binary, min_size=15):
    """Remove connected components smaller than min_size."""
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=4)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] < min_size:
            binary[labels == i] = 0
    return binary


def _hysteresis_enhance(is_border, gradient, lower_threshold, passes=4):
    """Promote weak gradient pixels adjacent to confirmed borders."""
    eligible = (gradient >= lower_threshold) & (is_border == 0)
    for _ in range(passes):
        prev = is_border.copy()
        neighbor_border = np.zeros_like(is_border, dtype=bool)
        neighbor_border[1:, :] |= prev[:-1, :] > 0
        neighbor_border[:-1, :] |= prev[1:, :] > 0
        neighbor_border[:, 1:] |= prev[:, :-1] > 0
        neighbor_border[:, :-1] |= prev[:, 1:] > 0
        promote = eligible & neighbor_border & (is_border == 0)
        is_border[promote] = 1
    return is_border


def _gap_bridging(is_border, h, w, max_gap=4):
    """Bridge horizontal and vertical gaps <= max_gap pixels in border segments."""
    # Horizontal
    for y in range(h):
        row = is_border[y, :]
        last_x = -max_gap - 2
        for x in range(w):
            if row[x]:
                if 1 < x - last_x <= max_gap + 1:
                    is_border[y, last_x + 1:x] = 1
                last_x = x
    # Vertical
    for x in range(w):
        col = is_border[:, x]
        last_y = -max_gap - 2
        for y in range(h):
            if col[y]:
                if 1 < y - last_y <= max_gap + 1:
                    is_border[last_y + 1:y, x] = 1
                last_y = y
    return is_border


def _compute_object_metrics(labels, num_labels, rgb, edges, h, w):
    """Compute per-region metrics: variance, rectangularity, edge contact, etc."""
    objects = []
    for label_id in range(1, num_labels):
        mask = labels == label_id
        pixel_count = mask.sum()
        if pixel_count == 0:
            continue

        ys, xs = np.where(mask)
        min_x, max_x = xs.min(), xs.max()
        min_y, max_y = ys.min(), ys.max()

        # Color variance
        region_rgb = rgb[mask]
        mean_rgb = region_rgb.mean(axis=0)
        var_rgb = ((region_rgb - mean_rgb) ** 2).mean(axis=0)
        color_variance = float(np.sqrt(var_rgb.sum()))

        # Rectangularity
        bbox_area = (max_x - min_x + 1) * (max_y - min_y + 1)
        rectangularity = float(pixel_count / bbox_area) if bbox_area > 0 else 0

        # Edge touches
        touches_top = int(min_y) == 0
        touches_bottom = int(max_y) == h - 1
        touches_left = int(min_x) == 0
        touches_right = int(max_x) == w - 1
        edge_sides = int(touches_top) + int(touches_bottom) + int(touches_left) + int(touches_right)

        # Interior edge density
        edge_density = float(edges[mask].mean() / 255.0) if pixel_count > 0 else 0

        # Border contact ratio (approximate: perimeter pixels touching border)
        dilated = cv2.dilate(mask.astype(np.uint8), np.ones((3, 3), np.uint8))
        perimeter = dilated.astype(np.int32) - mask.astype(np.int32)
        perimeter_count = max(1, (perimeter > 0).sum())
        # We don't have isBorder at this scope — approximate with gradient
        border_contact = 0.5  # default

        objects.append({
            "label": label_id,
            "pixel_count": int(pixel_count),
            "min_x": int(min_x), "max_x": int(max_x),
            "min_y": int(min_y), "max_y": int(max_y),
            "color_variance": color_variance,
            "rectangularity": rectangularity,
            "edge_sides": edge_sides,
            "touches_edge": edge_sides > 0,
            "touches_top": touches_top,
            "touches_bottom": touches_bottom,
            "touches_left": touches_left,
            "touches_right": touches_right,
            "edge_density": edge_density,
            "border_contact": border_contact,
        })

    return objects


def _classify_backgrounds(objects, labels, is_border, h, w, total):
    """Identify background regions using v5+ scoring."""
    if not objects:
        return set()

    max_var = max(o["color_variance"] for o in objects) if objects else 1
    max_size = max(o["pixel_count"] for o in objects) if objects else 1

    # Find primary background
    bg_label = -1
    best_score = -1
    bg_obj = None
    for obj in objects:
        if not obj["touches_edge"]:
            continue
        score = (0.35 * (obj["color_variance"] / max_var if max_var > 0 else 0) +
                 0.30 * (obj["pixel_count"] / max_size if max_size > 0 else 0) +
                 0.25 * (obj["edge_sides"] / 4) +
                 0.10 * (1 - obj["rectangularity"]))
        if score > best_score:
            best_score = score
            bg_label = obj["label"]
            bg_obj = obj

    bg_labels = set()
    if bg_label >= 0:
        bg_labels.add(bg_label)

    bg_var = bg_obj["color_variance"] if bg_obj else 50
    bg_edge_density = bg_obj["edge_density"] if bg_obj else 0.1

    # UI shape check
    def has_ui_shape(obj):
        bw = obj["max_x"] - obj["min_x"] + 1
        bh = obj["max_y"] - obj["min_y"] + 1
        w_r = bw / w
        h_r = bh / h
        asp = bw / max(1, bh)
        is_thin_bar = asp >= 3 and h_r <= 0.25
        is_wide_bar = w_r >= 0.4 and h_r <= 0.40
        is_compact = w_r <= 0.25 and h_r <= 0.25 and w_r >= 0.05
        is_rect = obj["rectangularity"] >= 0.55
        bar_needs_edge = (is_thin_bar or is_wide_bar) and not obj["touches_top"] and not obj["touches_bottom"]
        geo = ((is_thin_bar or is_wide_bar) and not bar_needs_edge) or is_compact or is_rect
        if not geo:
            return False
        if obj["color_variance"] < bg_var * 0.55:
            return True
        if obj["edge_density"] < bg_edge_density * 0.60:
            return True
        if obj["touches_edge"] and (obj["color_variance"] < bg_var * 0.75 or obj["edge_density"] < bg_edge_density * 0.75):
            return True
        return False

    # Secondary backgrounds
    for obj in objects:
        if obj["label"] in bg_labels or has_ui_shape(obj):
            continue
        touches_side_only = (obj["touches_left"] or obj["touches_right"]) and not obj["touches_top"] and not obj["touches_bottom"]
        var_thresh = 0.40 if touches_side_only else 0.65

        if obj["touches_edge"] and obj["color_variance"] > bg_var * var_thresh and obj["pixel_count"] > total * 0.01:
            bg_labels.add(obj["label"])
            continue
        if touches_side_only and obj["color_variance"] > bg_var * 0.30 and obj["pixel_count"] > total * 0.005:
            bg_labels.add(obj["label"])
            continue
        if obj["touches_edge"] and obj["pixel_count"] < total * 0.003 and obj["color_variance"] > bg_var * 0.5:
            bg_labels.add(obj["label"])
            continue
        if not obj["touches_edge"] and obj["color_variance"] > bg_var * 0.6 and obj["pixel_count"] < total * 0.03 and obj["rectangularity"] < 0.45:
            bg_labels.add(obj["label"])

    # Trapped background (simplified — no RAG, use signal-based detection)
    for obj in objects:
        if obj["label"] in bg_labels or obj["touches_edge"] or obj["pixel_count"] < total * 0.001:
            continue
        if has_ui_shape(obj):
            continue
        signals = 0
        if obj["color_variance"] > bg_var * 0.45:
            signals += 1
        if obj["rectangularity"] < 0.45:
            signals += 1
        if obj["edge_density"] > bg_edge_density * 0.50:
            signals += 1
        if obj["border_contact"] < 0.60:
            signals += 1
        min_signals = 2 if obj["pixel_count"] > total * 0.01 else 3
        if signals >= min_signals:
            bg_labels.add(obj["label"])

    return bg_labels


def _remove_small_alpha_fragments(alpha, min_frac=0.002):
    """Remove connected alpha regions smaller than min_frac of total pixels."""
    total = alpha.shape[0] * alpha.shape[1]
    min_size = int(total * min_frac)
    binary = (alpha > 0).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=4)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] < min_size:
            alpha[labels == i] = 0
    return alpha


def _feather_edges(alpha, radius=2):
    """Apply soft edge feathering at mask boundaries."""
    # Find boundary pixels (opaque pixels adjacent to transparent)
    opaque = (alpha > 0).astype(np.uint8)
    eroded = cv2.erode(opaque, np.ones((3, 3), np.uint8))
    boundary = opaque - eroded

    # Distance from boundary inward
    inner = (opaque > 0).astype(np.uint8)
    dist = cv2.distanceTransform(inner, cv2.DIST_L1, 3)

    # Apply graduated alpha at boundary
    feather_values = [128, 192]
    for d, val in enumerate(feather_values):
        mask = (dist > d) & (dist <= d + 1) & (alpha > 0)
        alpha[mask] = min(val, alpha[mask].max()) if mask.any() else val

    return alpha


def _remove_debris(alpha, h, w):
    """Remove semi-transparent pixels not near any fully opaque pixel."""
    opaque = (alpha == 255).astype(np.uint8)
    # Dilate opaque region by 3px
    dilated = cv2.dilate(opaque, np.ones((7, 7), np.uint8))
    # Remove semi-transparent pixels outside dilated opaque zone
    debris = (alpha > 0) & (alpha < 255) & (dilated == 0)
    alpha[debris] = 0
    return alpha


def _multi_spectrum_cleanup(alpha, ms_map, rgb, gray, h, w):
    """Multi-strategy cleanup of v5+ mask using multi-spectrum analysis.

    Strategies:
    1. Dark scene detection — dark, low-saturation pixels far from UI borders
    2. Color outlier detection — pixels whose color doesn't match nearby UI
    3. Texture mismatch — regions with scene-like texture (high edge density)
    4. Border proximity — opaque pixels far from any multi-spectrum border
    """
    total = h * w
    opaque_mask = alpha > 128

    if opaque_mask.sum() == 0:
        return alpha

    # Precompute shared data
    ms_borders = (ms_map > 0.3).astype(np.uint8)
    ms_dilated = cv2.dilate(ms_borders, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
    gray_f = gray.astype(np.float64)

    # ── Strategy 1: Dark scene pixels ──
    # Game scenes between UI bars are typically very dark (cave, dungeon).
    # UI panels have visible content (text, icons) or lighter fills.
    # Dark pixels (<40 brightness) that are NOT part of a border are likely scene.
    near_border = cv2.dilate(ms_borders, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    dark_scene = opaque_mask & (gray < 40) & (near_border == 0)

    # But protect dark UI fills (e.g., dark panel interiors) — they're enclosed by borders
    # Use distance to nearest transparent pixel: deep interior dark = UI, edge dark = scene
    opaque_u8 = opaque_mask.astype(np.uint8)
    dist_from_edge = cv2.distanceTransform(opaque_u8, cv2.DIST_L2, 5)
    # Dark pixels near the edge of the mask (within 15px of transparent) are scene leakage
    dark_scene_edge = dark_scene & (dist_from_edge < 15)

    # ── Strategy 2: Color outlier detection ──
    # For each opaque pixel, compare its color to the median color of nearby opaque pixels.
    # Pixels that don't match their neighborhood are artifacts.
    if rgb.dtype != np.float64:
        rgb_f = rgb.astype(np.float64)
    else:
        rgb_f = rgb
    local_r = cv2.blur(rgb_f[:,:,0] * opaque_mask, (25, 25))
    local_g = cv2.blur(rgb_f[:,:,1] * opaque_mask, (25, 25))
    local_b = cv2.blur(rgb_f[:,:,2] * opaque_mask, (25, 25))
    local_count = cv2.blur(opaque_mask.astype(np.float64), (25, 25))
    local_count = np.maximum(local_count, 1)
    local_r /= local_count; local_g /= local_count; local_b /= local_count
    color_diff = np.sqrt(
        (rgb_f[:,:,0] - local_r)**2 +
        (rgb_f[:,:,1] - local_g)**2 +
        (rgb_f[:,:,2] - local_b)**2
    )
    # Pixels very different from their local neighborhood color
    color_outlier = opaque_mask & (color_diff > 40) & (ms_dilated == 0)

    # ── Strategy 3: Texture mismatch (high local edge density = scene) ──
    edges = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)**2 + cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)**2
    edge_mag = np.sqrt(edges)
    local_edge = cv2.blur(edge_mag, (21, 21))
    # UI panels are smooth (low edge density), scenes are textured (high edge density)
    opaque_edge_median = np.median(local_edge[opaque_mask]) if opaque_mask.sum() > 0 else 10
    high_texture = opaque_mask & (local_edge > opaque_edge_median * 2.0) & (ms_dilated == 0)

    # ── Strategy 4: Variance-based (original, relaxed threshold) ──
    local_mean = cv2.blur(gray_f, (15, 15))
    local_sq_mean = cv2.blur(gray_f ** 2, (15, 15))
    local_var = np.maximum(local_sq_mean - local_mean ** 2, 0)
    median_var = np.median(local_var[opaque_mask])
    high_variance = opaque_mask & (ms_dilated == 0) & (local_var > median_var * 1.2)

    # ── Combine: vote across strategies ──
    # Each strategy contributes a vote. Pixels with 2+ votes are removed.
    votes = (dark_scene_edge.astype(np.int32) +
             color_outlier.astype(np.int32) +
             high_texture.astype(np.int32) +
             high_variance.astype(np.int32))

    suspicious = votes >= 2

    # Remove suspicious regions — allow larger regions now (up to 10% of image)
    suspicious_u8 = suspicious.astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(suspicious_u8, connectivity=4)
    removed = 0
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < total * 0.10:  # remove up to 10% regions
            alpha[labels == i] = 0
            removed += area

    # ── Also remove isolated dark strips not caught by voting ──
    # Dark pixels near the mask edge that aren't near MS borders = scene leakage.
    # Protect deep interior dark pixels (panel fills, leather textures).
    opaque_after = (alpha > 128).astype(np.uint8)
    dist_interior = cv2.distanceTransform(opaque_after, cv2.DIST_L2, 5)
    dark_remaining = (alpha > 128) & (gray < 45) & (ms_dilated == 0) & (dist_interior < 20)
    dark_u8 = dark_remaining.astype(np.uint8)
    n_dark, dark_labels, dark_stats, _ = cv2.connectedComponentsWithStats(dark_u8, connectivity=4)
    dark_removed = 0
    for i in range(1, n_dark):
        area = dark_stats[i, cv2.CC_STAT_AREA]
        if area > 100 and area < total * 0.10:
            region_mask = dark_labels == i
            region_mean_brightness = gray[region_mask].mean()
            if region_mean_brightness < 40:
                alpha[region_mask] = 0
                dark_removed += area

    total_removed = removed + dark_removed
    if total_removed > 0:
        print(f"  [MS Cleanup] Removed {total_removed} pixels ({total_removed/total*100:.1f}%): "
              f"{removed} by voting, {dark_removed} dark strips")

    return alpha
