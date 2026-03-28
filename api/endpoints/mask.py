# api/endpoints/mask.py
"""Mask endpoints: POST /api/mask/generate, POST /api/mask/refine"""
import os
import threading

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register(router):

    def handle_generate(params):
        image_path = params.get("image_path")
        output_path = params.get("output_path")
        model = params.get("model")

        if not image_path:
            return 400, {"error": "Missing required field: image_path", "code": "BAD_REQUEST"}
        if not output_path:
            return 400, {"error": "Missing required field: output_path", "code": "BAD_REQUEST"}

        # Resolve relative paths against PROJECT_DIR
        if not os.path.isabs(image_path):
            image_path = os.path.join(PROJECT_DIR, image_path)
        if not os.path.isabs(output_path):
            output_path = os.path.join(PROJECT_DIR, output_path)

        page = router.pool.checkout(timeout=10)
        if page is None:
            return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}

        job_id = router.jobs.create("mask_generate", {
            "image_path": image_path,
            "output_path": output_path,
            "model": model,
        })
        router.jobs.update(job_id, status="processing", step="queued")

        def _run():
            try:
                router.pool.reset_page(page)

                # Load image
                load_result = router.bridge.load_image(page, image_path)
                if not load_result.get("loaded"):
                    router.jobs.update(job_id, status="failed",
                                       error="Image failed to load", code="LOAD_FAILED")
                    return

                router.jobs.update(job_id, progress=20, step="image_loaded")

                # Apply model override if provided
                if model:
                    router.bridge.apply_settings_override(page, {"aiMaskModel": model})

                router.jobs.update(job_id, progress=40, step="generating_mask")

                # Generate mask via ComfyUI
                gen_result = router.bridge.generate_mask_only(
                    page,
                    on_progress=lambda s: router.jobs.update(job_id, step=s),
                )

                if not gen_result.get("ok"):
                    router.jobs.update(job_id, status="failed",
                                       error=gen_result.get("error", "Mask generation failed"),
                                       code="MASK_FAILED")
                    return

                router.jobs.update(job_id, progress=80, step="saving_mask")

                # Save the mask canvas to file
                # Try processedMaskCanvas, then aiMaskCanvas
                data_url = page.evaluate(
                    """() => {
                        const src = window.processedMaskCanvas || window.aiMaskCanvas
                            || document.querySelector('#aiMaskCanvas');
                        if (!src || src.width === 0) return null;
                        return src.toDataURL('image/png');
                    }"""
                )

                if not data_url:
                    router.jobs.update(job_id, status="failed",
                                       error="No mask canvas available after generation",
                                       code="NO_MASK_CANVAS")
                    return

                import base64
                header, b64_data = data_url.split(",", 1)
                png_bytes = base64.b64decode(b64_data)
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                with open(output_path, "wb") as fh:
                    fh.write(png_bytes)

                router.jobs.update(job_id, status="completed", progress=100,
                                   step="done",
                                   results={"path": output_path, "bytes": len(png_bytes),
                                            "status": gen_result.get("status", "")})
            except Exception as exc:
                import traceback
                traceback.print_exc()
                router.jobs.update(job_id, status="failed", error=str(exc),
                                   code="INTERNAL_ERROR")
            finally:
                router.pool.checkin(page)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return 202, {"job_id": job_id, "status": "processing"}

    def handle_refine(params):
        image_path = params.get("image_path")
        output_path = params.get("output_path")
        settings = params.get("settings", {})

        if not image_path:
            return 400, {"error": "Missing required field: image_path", "code": "BAD_REQUEST"}
        if not output_path:
            return 400, {"error": "Missing required field: output_path", "code": "BAD_REQUEST"}

        # Resolve relative paths against PROJECT_DIR
        if not os.path.isabs(image_path):
            image_path = os.path.join(PROJECT_DIR, image_path)
        if not os.path.isabs(output_path):
            output_path = os.path.join(PROJECT_DIR, output_path)

        page = router.pool.checkout(timeout=10)
        if page is None:
            return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}

        try:
            router.pool.reset_page(page)

            # Load the main image first
            load_result = router.bridge.load_image(page, image_path)
            if not load_result.get("loaded"):
                return 500, {"error": "Image failed to load", "code": "LOAD_FAILED"}

            # Load AI mask via the aiMaskInput file chooser
            mask_path = params.get("mask_path")
            if mask_path:
                if not os.path.isabs(mask_path):
                    mask_path = os.path.join(PROJECT_DIR, mask_path)
                with page.expect_file_chooser() as fc_info:
                    page.click('label[for="aiMaskInput"]')
                fc = fc_info.value
                fc.set_files(mask_path)
                # Wait briefly for mask to load
                page.wait_for_timeout(1000)

            # Apply any settings overrides (expand, feather, invert, etc.)
            if settings:
                router.bridge.apply_settings_override(page, settings)

            # Read coverage via JS helpers
            coverage = page.evaluate(
                """() => {
                    const refined = (typeof getRefinedImportedAiAlpha === 'function')
                        ? getRefinedImportedAiAlpha() : null;
                    const coverage = (typeof getAlphaCoverage === 'function')
                        ? getAlphaCoverage() : null;
                    return { refined: refined !== null, coverage };
                }"""
            )

            # Save the refined mask — try importedAiMaskCanvas or processedMaskCanvas
            save_result = router.bridge.save_canvas_to_file(
                page, "importedAiMaskCanvas", output_path
            )
            if not save_result.get("ok"):
                # Fall back to processedMaskCanvas
                save_result = router.bridge.save_canvas_to_file(
                    page, "processedMaskCanvas", output_path
                )

            return 200, {
                "ok": save_result.get("ok", False),
                "path": output_path,
                "bytes": save_result.get("bytes"),
                "coverage": coverage.get("coverage"),
                "error": save_result.get("error"),
            }

        finally:
            router.pool.checkin(page)

    router.register_post("/api/mask/generate", handle_generate)
    router.register_post("/api/mask/refine", handle_refine)
