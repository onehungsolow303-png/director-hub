"""Split endpoint: POST /api/split"""
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register(router):

    def handle_split(params):
        image = params.get("image") or params.get("image_path")
        if not image:
            return 400, {"error": "Missing required field: image", "code": "NO_IMAGE"}
        min_pixels = params.get("min_pixels", 5000)
        alpha_cutoff = params.get("alpha_cutoff", 220)

        def _do_split(pool):
            page = pool.checkout(timeout=10)
            if page is None:
                return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}
            try:
                pool.reset_page(page)
                abs_image = os.path.join(PROJECT_DIR, image) if not os.path.isabs(image) else image
                router.bridge.load_image(page, abs_image)
                router.bridge.apply_settings_override(page, {
                    "componentPixels": min_pixels,
                    "componentAlpha": alpha_cutoff
                })
                router.bridge.run_process_image(page, timeout_s=30)
                output_dir = params.get("output_dir", "output")
                abs_output = os.path.join(PROJECT_DIR, output_dir) if not os.path.isabs(output_dir) else output_dir
                os.makedirs(abs_output, exist_ok=True)
                base = os.path.splitext(os.path.basename(image))[0]
                panels = router.bridge.extract_panels(page, abs_output, base)
                return 200, {"panels": panels}
            finally:
                pool.checkin(page)

        try:
            return router.pool.run_on_page(_do_split, timeout=60)
        except Exception as e:
            return 500, {"error": str(e), "code": "INTERNAL_ERROR"}

    router.register_post("/api/split", handle_split)
