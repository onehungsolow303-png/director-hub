from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image

PRESETS = {
    "ui-balanced": {
        "threshold": 18,
        "softness": 24,
        "alpha_floor": 8,
        "alpha_ceiling": 245,
        "component_alpha_threshold": 220,
        "min_component_pixels": 5000,
        "component_pad": 2,
        "max_components": 2,
        "crop_transparent_bounds": False,
        "decontaminate_black": True,
    },
    "ui-soft": {
        "threshold": 14,
        "softness": 34,
        "alpha_floor": 4,
        "alpha_ceiling": 245,
        "component_alpha_threshold": 200,
        "min_component_pixels": 5000,
        "component_pad": 4,
        "max_components": 2,
        "crop_transparent_bounds": False,
        "decontaminate_black": True,
    },
    "ui-hard": {
        "threshold": 24,
        "softness": 16,
        "alpha_floor": 12,
        "alpha_ceiling": 238,
        "component_alpha_threshold": 228,
        "min_component_pixels": 7000,
        "component_pad": 2,
        "max_components": 2,
        "crop_transparent_bounds": False,
        "decontaminate_black": True,
    },
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SKIP_NAME_PARTS = ("_transparent", "_part_")


def build_alpha(image: Image.Image, threshold: int, softness: int) -> Image.Image:
    rgba = image.convert("RGBA")
    src = rgba.load()
    width, height = rgba.size
    alpha = Image.new("L", (width, height), 0)
    out = alpha.load()

    upper = threshold + max(softness, 1)

    for y in range(height):
        for x in range(width):
            r, g, b, _ = src[x, y]
            brightness = max(r, g, b)

            if brightness <= threshold:
                a = 0
            elif brightness >= upper:
                a = 255
            else:
                a = int(255 * (brightness - threshold) / (upper - threshold))

            out[x, y] = a

    return alpha


def clamp_alpha(alpha: Image.Image, floor: int, ceiling: int) -> Image.Image:
    src = alpha.load()
    width, height = alpha.size
    out = Image.new("L", (width, height), 0)
    dst = out.load()

    for y in range(height):
        for x in range(width):
            a = src[x, y]
            if a <= floor:
                dst[x, y] = 0
            elif a >= ceiling:
                dst[x, y] = 255
            else:
                dst[x, y] = a

    return out


def apply_alpha(
    image: Image.Image,
    alpha: Image.Image,
    decontaminate_black: bool,
) -> Image.Image:
    src = image.convert("RGBA")
    alpha = alpha.convert("L")
    width, height = src.size
    spx = src.load()
    apx = alpha.load()

    out = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dst = out.load()

    for y in range(height):
        for x in range(width):
            r, g, b, _ = spx[x, y]
            a = apx[x, y]

            if a == 0:
                dst[x, y] = (0, 0, 0, 0)
                continue

            if decontaminate_black and a < 255:
                scale = 255.0 / a
                r = min(255, int(round(r * scale)))
                g = min(255, int(round(g * scale)))
                b = min(255, int(round(b * scale)))

            dst[x, y] = (r, g, b, a)

    return out


def crop_to_visible_bounds(
    image: Image.Image, alpha_threshold: int = 1
) -> tuple[Image.Image, tuple[int, int, int, int] | None]:
    rgba = image.convert("RGBA")
    px = rgba.load()
    width, height = rgba.size

    min_x = width
    min_y = height
    max_x = -1
    max_y = -1

    for y in range(height):
        for x in range(width):
            if px[x, y][3] >= alpha_threshold:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if max_x < 0 or max_y < 0:
        return rgba, None

    box = (min_x, min_y, max_x + 1, max_y + 1)
    return rgba.crop(box), box


def find_components(
    alpha: Image.Image, min_pixels: int, alpha_threshold: int
) -> list[tuple[int, int, int, int]]:
    width, height = alpha.size
    px = alpha.load()
    seen = [[False for _ in range(width)] for _ in range(height)]
    boxes: list[tuple[int, int, int, int]] = []

    for y in range(height):
        for x in range(width):
            if seen[y][x] or px[x, y] < alpha_threshold:
                continue

            q = deque([(x, y)])
            seen[y][x] = True
            count = 0
            min_x = max_x = x
            min_y = max_y = y

            while q:
                cx, cy = q.popleft()
                count += 1
                min_x = min(min_x, cx)
                min_y = min(min_y, cy)
                max_x = max(max_x, cx)
                max_y = max(max_y, cy)

                for nx, ny in (
                    (cx - 1, cy),
                    (cx + 1, cy),
                    (cx, cy - 1),
                    (cx, cy + 1),
                ):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    if seen[ny][nx] or px[nx, ny] < alpha_threshold:
                        continue
                    seen[ny][nx] = True
                    q.append((nx, ny))

            if count >= min_pixels:
                boxes.append((min_x, min_y, max_x + 1, max_y + 1))

    boxes.sort(key=lambda box: (box[1], box[0]))
    return boxes


def save_split_images(
    image: Image.Image,
    boxes: list[tuple[int, int, int, int]],
    output_base: Path,
    pad: int,
) -> list[Path]:
    width, height = image.size
    saved: list[Path] = []

    for index, (left, top, right, bottom) in enumerate(boxes, start=1):
        crop_box = (
            max(0, left - pad),
            max(0, top - pad),
            min(width, right + pad),
            min(height, bottom + pad),
        )
        part = image.crop(crop_box)
        out_path = output_base.with_name(f"{output_base.stem}_part_{index:02d}.png")
        part.save(out_path)
        saved.append(out_path)

    return saved


def keep_largest_components(
    boxes: list[tuple[int, int, int, int]], max_components: int
) -> list[tuple[int, int, int, int]]:
    if max_components <= 0 or len(boxes) <= max_components:
        return boxes

    ranked = sorted(
        boxes,
        key=lambda box: (box[2] - box[0]) * (box[3] - box[1]),
        reverse=True,
    )[:max_components]
    return sorted(ranked, key=lambda box: (box[1], box[0]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove near-black backgrounds from UI sheets and export transparent PNGs."
    )
    parser.add_argument("--input", help="Path to a single source image.")
    parser.add_argument("--input-dir", help="Process every image in a folder.")
    parser.add_argument(
        "--output",
        help="Optional output PNG path for single-image mode.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional output directory. Defaults to the source image folder or input-dir.",
    )
    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS.keys()),
        default="ui-balanced",
        help="Starting parameter preset. Default: ui-balanced",
    )
    parser.add_argument("--threshold", type=int, help="Brightness cutoff treated as background.")
    parser.add_argument("--softness", type=int, help="Soft transition above threshold.")
    parser.add_argument("--alpha-floor", type=int, help="Clamp alpha at or below this value to fully transparent.")
    parser.add_argument("--alpha-ceiling", type=int, help="Clamp alpha at or above this value to fully opaque.")
    parser.add_argument(
        "--split-components",
        action="store_true",
        help="Export each disconnected foreground island as its own cropped PNG.",
    )
    parser.add_argument("--min-component-pixels", type=int, help="Ignore tiny components smaller than this many pixels.")
    parser.add_argument("--component-alpha-threshold", type=int, help="Only pixels with alpha at or above this value count for splitting.")
    parser.add_argument("--component-pad", type=int, help="Padding around split component crops.")
    parser.add_argument("--max-components", type=int, help="Keep only the largest N split components. Use 0 to keep all.")
    parser.add_argument(
        "--crop-transparent-bounds",
        action="store_true",
        help="Crop transparent borders from the main saved output.",
    )
    parser.add_argument(
        "--asset-subfolders",
        action="store_true",
        help="When batching, write each image into its own output subfolder.",
    )
    parser.add_argument(
        "--include-processed",
        action="store_true",
        help="When batching, also process files that already look generated, like *_transparent or *_part_*.png.",
    )
    parser.add_argument(
        "--no-decontaminate-black",
        action="store_true",
        help="Disable black-edge cleanup for semi-transparent pixels.",
    )
    return parser.parse_args()


def resolve_settings(args: argparse.Namespace) -> dict[str, int | bool]:
    settings = dict(PRESETS[args.preset])
    overrides = {
        "threshold": args.threshold,
        "softness": args.softness,
        "alpha_floor": args.alpha_floor,
        "alpha_ceiling": args.alpha_ceiling,
        "min_component_pixels": args.min_component_pixels,
        "component_alpha_threshold": args.component_alpha_threshold,
        "component_pad": args.component_pad,
        "max_components": args.max_components,
    }
    for key, value in overrides.items():
        if value is not None:
            settings[key] = value

    if args.crop_transparent_bounds:
        settings["crop_transparent_bounds"] = True
    if args.no_decontaminate_black:
        settings["decontaminate_black"] = False

    return settings


def should_skip_generated(path: Path, include_processed: bool) -> bool:
    if include_processed:
        return False
    lower_name = path.stem.lower()
    return any(part in lower_name for part in SKIP_NAME_PARTS)


def iter_input_files(args: argparse.Namespace) -> list[Path]:
    if bool(args.input) == bool(args.input_dir):
        raise SystemExit("Use exactly one of --input or --input-dir")

    if args.input:
        path = Path(args.input).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"Input file not found: {path}")
        return [path]

    folder = Path(args.input_dir).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise SystemExit(f"Input directory not found: {folder}")

    files = sorted(
        p
        for p in folder.iterdir()
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTENSIONS
        and not should_skip_generated(p, args.include_processed)
    )
    if not files:
        raise SystemExit(f"No supported images found in: {folder}")
    return files


def make_output_path(
    input_path: Path,
    args: argparse.Namespace,
    output_dir: Path | None,
) -> Path:
    if args.output and not args.input_dir:
        return Path(args.output).expanduser().resolve()

    base_dir = output_dir if output_dir else input_path.parent
    if args.asset_subfolders:
        base_dir = base_dir / input_path.stem
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / f"{input_path.stem}_transparent.png"


def process_image(
    input_path: Path,
    output_path: Path,
    settings: dict[str, int | bool],
    split_components: bool,
) -> None:
    source = Image.open(input_path)
    alpha = build_alpha(
        source,
        threshold=int(settings["threshold"]),
        softness=int(settings["softness"]),
    )
    alpha = clamp_alpha(
        alpha,
        floor=int(settings["alpha_floor"]),
        ceiling=int(settings["alpha_ceiling"]),
    )
    result = apply_alpha(
        source,
        alpha,
        decontaminate_black=bool(settings["decontaminate_black"]),
    )
    if bool(settings["crop_transparent_bounds"]):
        result, _ = crop_to_visible_bounds(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path)
    print(f"Saved transparent image: {output_path}")

    if split_components:
        boxes = find_components(
            alpha,
            min_pixels=int(settings["min_component_pixels"]),
            alpha_threshold=int(settings["component_alpha_threshold"]),
        )
        boxes = keep_largest_components(boxes, int(settings["max_components"]))
        if not boxes:
            print("No foreground components found for splitting.")
            return
        saved = save_split_images(
            result,
            boxes,
            output_path,
            pad=int(settings["component_pad"]),
        )
        print("Saved split components:")
        for path in saved:
            print(f"  {path}")


def main() -> None:
    args = parse_args()
    settings = resolve_settings(args)
    inputs = iter_input_files(args)
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None

    for input_path in inputs:
        output_path = make_output_path(input_path, args, output_dir)
        process_image(
            input_path,
            output_path,
            settings=settings,
            split_components=args.split_components,
        )


if __name__ == "__main__":
    main()
