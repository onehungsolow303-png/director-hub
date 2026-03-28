# api/endpoints/enhance.py
"""Enhance endpoint: POST /api/enhance"""
import base64
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register(router):

    def handle_enhance(params):
        image_path = params.get("image_path")
        extracted_path = params.get("extracted_path")
        output_path = params.get("output_path")

        if not image_path:
            return 400, {"error": "Missing required field: image_path", "code": "BAD_REQUEST"}
        if not extracted_path:
            return 400, {"error": "Missing required field: extracted_path", "code": "BAD_REQUEST"}
        if not output_path:
            return 400, {"error": "Missing required field: output_path", "code": "BAD_REQUEST"}

        # Resolve relative paths against PROJECT_DIR
        if not os.path.isabs(image_path):
            image_path = os.path.join(PROJECT_DIR, image_path)
        if not os.path.isabs(extracted_path):
            extracted_path = os.path.join(PROJECT_DIR, extracted_path)
        if not os.path.isabs(output_path):
            output_path = os.path.join(PROJECT_DIR, output_path)

        page = router.pool.checkout(timeout=10)
        if page is None:
            return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}

        try:
            router.pool.reset_page(page)

            # Load the original image
            load_result = router.bridge.load_image(page, image_path)
            if not load_result.get("loaded"):
                return 500, {"error": "Original image failed to load", "code": "LOAD_FAILED"}

            # Read the extracted image and inject it as base64 into #aiFinalCanvas
            with open(extracted_path, "rb") as fh:
                raw = fh.read()
            b64 = base64.b64encode(raw).decode("ascii")
            mime = "image/png"
            if extracted_path.lower().endswith((".jpg", ".jpeg")):
                mime = "image/jpeg"
            data_url = f"data:{mime};base64,{b64}"

            inject_result = page.evaluate(
                """(dataUrl) => {
                    return new Promise((resolve, reject) => {
                        const img = new Image();
                        img.onload = () => {
                            const canvas = document.querySelector('#aiFinalCanvas');
                            if (!canvas) {
                                resolve({ ok: false, error: 'aiFinalCanvas not found' });
                                return;
                            }
                            canvas.width = img.width;
                            canvas.height = img.height;
                            canvas.getContext('2d').drawImage(img, 0, 0);
                            resolve({ ok: true, width: img.width, height: img.height });
                        };
                        img.onerror = () => reject(new Error('Failed to load extracted image'));
                        img.src = dataUrl;
                    });
                }""",
                data_url,
            )

            if not inject_result.get("ok"):
                return 500, {"error": inject_result.get("error", "Failed to inject extracted image"),
                             "code": "INJECT_FAILED"}

            # Show the enhance block so the button is accessible
            page.evaluate(
                """() => {
                    const block = document.querySelector('#aiEnhanceBlock')
                        || document.querySelector('.ai-enhance-section');
                    if (block) {
                        block.style.display = '';
                        block.classList.remove('hidden');
                    }
                }"""
            )

            # Run enhance
            enhance_result = router.bridge.run_enhance(page)
            if not enhance_result.get("ok"):
                return 500, {"error": enhance_result.get("error", "Enhance failed"),
                             "code": "ENHANCE_FAILED",
                             "status": enhance_result.get("status", "")}

            # Save the enhanced canvas
            save_result = router.bridge.save_canvas_to_file(page, "aiEnhancedCanvas", output_path)
            if not save_result.get("ok"):
                return 500, {"error": save_result.get("error", "Failed to save enhanced canvas"),
                             "code": "SAVE_FAILED"}

            return 200, {
                "ok": True,
                "path": output_path,
                "bytes": save_result.get("bytes"),
                "width": enhance_result.get("width"),
                "height": enhance_result.get("height"),
            }

        finally:
            router.pool.checkin(page)

    router.register_post("/api/enhance", handle_enhance)
