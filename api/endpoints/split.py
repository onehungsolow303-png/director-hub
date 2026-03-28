# api/endpoints/split.py
"""Split endpoint: POST /api/split"""
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register(router):

    def handle_split(params):
        image_path = params.get("image_path")
        output_dir = params.get("output_dir")
        base_name = params.get("base_name", "panel")
        settings = params.get("settings", {})

        if not image_path:
            return 400, {"error": "Missing required field: image_path", "code": "BAD_REQUEST"}
        if not output_dir:
            return 400, {"error": "Missing required field: output_dir", "code": "BAD_REQUEST"}

        # Resolve relative paths against PROJECT_DIR
        if not os.path.isabs(image_path):
            image_path = os.path.join(PROJECT_DIR, image_path)
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(PROJECT_DIR, output_dir)

        page = router.pool.checkout(timeout=10)
        if page is None:
            return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}

        try:
            router.pool.reset_page(page)

            # Load image
            load_result = router.bridge.load_image(page, image_path)
            if not load_result.get("loaded"):
                return 500, {"error": "Image failed to load", "code": "LOAD_FAILED"}

            # Apply component/split-related settings (componentPixels, componentAlpha, etc.)
            if settings:
                router.bridge.apply_settings_override(page, settings)

            # Run process image to populate processedPanels
            process_result = router.bridge.run_process_image(page)
            if not process_result.get("ok"):
                return 500, {"error": process_result.get("error", "Processing failed"),
                             "code": "PROCESS_FAILED",
                             "status": process_result.get("status", "")}

            # Extract panels to output_dir
            panels_result = router.bridge.extract_panels(page, output_dir, base_name)

            return 200, {
                "ok": True,
                "count": panels_result.get("count", 0),
                "panels": panels_result.get("panels", []),
                "status": process_result.get("status", ""),
            }

        finally:
            router.pool.checkin(page)

    router.register_post("/api/split", handle_split)
