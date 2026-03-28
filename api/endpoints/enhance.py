"""Enhance endpoint: POST /api/enhance"""
import base64
import os

from api.utils import PROJECT_DIR, resolve_path, resolve_output_dir


def register(router):

    def handle_enhance(params):
        extracted = params.get("extracted") or params.get("extracted_path")
        original = params.get("original") or params.get("image_path")
        if not extracted or not original:
            return 400, {"error": "Missing required fields: extracted, original", "code": "BAD_REQUEST"}

        def _do_enhance(pool):
            page = pool.checkout(timeout=10)
            if page is None:
                return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}
            try:
                pool.reset_page(page)
                abs_original = resolve_path(original)
                abs_extracted = resolve_path(extracted)
                router.bridge.load_image(page, abs_original)
                with open(abs_extracted, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                page.evaluate("""(dataUrl) => {
                    return new Promise((resolve, reject) => {
                        const img = new Image();
                        img.onload = () => {
                            const c = document.querySelector('#aiFinalCanvas');
                            if (c) { c.width = img.width; c.height = img.height; c.getContext('2d').drawImage(img, 0, 0); }
                            resolve(true);
                        };
                        img.onerror = () => reject('load fail');
                        img.src = dataUrl;
                    });
                }""", f"data:image/png;base64,{data}")
                page.wait_for_timeout(500)
                page.evaluate("() => { const b = document.querySelector('#aiEnhanceBlock'); if (b) b.style.display = 'block'; }")
                result = router.bridge.run_enhance(page)
                if not result.get("ok"):
                    return 500, {"error": "AI Enhance failed", "code": "ENHANCE_FAILED"}
                output_dir = params.get("output_dir", "output")
                abs_output = resolve_output_dir(output_dir)
                base = os.path.splitext(os.path.basename(abs_extracted))[0]
                out_path = os.path.join(abs_output, f"{base}_enhanced.png")
                router.bridge.save_canvas_to_file(page, "aiEnhancedCanvas", out_path)
                return 200, {"enhanced": out_path}
            finally:
                pool.checkin(page)

        try:
            return router.pool.run_on_page(_do_enhance, timeout=90)
        except Exception as e:
            return 500, {"error": str(e), "code": "INTERNAL_ERROR"}

    router.register_post("/api/enhance", handle_enhance)
