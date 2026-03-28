"""Mask endpoints: POST /api/mask/generate, POST /api/mask/refine"""
import os
import threading
import base64

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register(router):

    def handle_generate(params):
        image = params.get("image")
        if not image:
            return 400, {"error": "Missing required field: image", "code": "NO_IMAGE"}
        method = params.get("method", "comfyui")
        model = params.get("model", "BiRefNet-general")
        output_dir = params.get("output_dir", "output")

        job_id = router.jobs.create("mask", {"image": image, "method": method, "model": model})
        thread = threading.Thread(
            target=_run_mask_job,
            args=(router, job_id, image, method, model, output_dir),
            daemon=True,
        )
        thread.start()
        return 202, {"job_id": job_id, "status": "queued"}

    def handle_refine(params):
        mask_path = params.get("mask")
        image_path = params.get("image")
        if not mask_path or not image_path:
            return 400, {"error": "Missing required fields: mask, image", "code": "BAD_REQUEST"}

        def _do_refine(pool):
            page = pool.checkout(timeout=10)
            if page is None:
                return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}
            try:
                pool.reset_page(page)
                abs_image = os.path.join(PROJECT_DIR, image_path) if not os.path.isabs(image_path) else image_path
                router.bridge.load_image(page, abs_image)
                abs_mask = os.path.join(PROJECT_DIR, mask_path) if not os.path.isabs(mask_path) else mask_path
                page.evaluate("() => document.querySelector('.card.closed')?.classList.remove('closed')")
                with page.expect_file_chooser() as fc:
                    page.click('label[for="aiMaskInput"]')
                fc.value.set_files(abs_mask)
                page.wait_for_timeout(1000)
                overrides = {}
                if "expand" in params: overrides["aiMaskExpand"] = params["expand"]
                if "feather" in params: overrides["aiMaskFeather"] = params["feather"]
                if "invert" in params: overrides["aiInvertMask"] = params["invert"]
                if overrides:
                    router.bridge.apply_settings_override(page, overrides)
                    page.wait_for_timeout(500)
                coverage = page.evaluate("""() => {
                    const settings = getBgSettings();
                    const refined = getRefinedImportedAiAlpha(settings);
                    if (!refined) return 0;
                    return getAlphaCoverage(refined);
                }""")
                out_dir = params.get("output_dir", "output")
                abs_output = os.path.join(PROJECT_DIR, out_dir) if not os.path.isabs(out_dir) else out_dir
                os.makedirs(abs_output, exist_ok=True)
                base = os.path.splitext(os.path.basename(mask_path))[0]
                out_path = os.path.join(abs_output, f"{base}_refined.png")
                router.bridge.save_canvas_to_file(page, "aiMaskCanvas", out_path)
                return 200, {"refined_mask": out_path, "coverage": round(coverage, 4)}
            finally:
                pool.checkin(page)

        try:
            return router.pool.run_on_page(_do_refine, timeout=30)
        except Exception as e:
            return 500, {"error": str(e), "code": "INTERNAL_ERROR"}

    router.register_post("/api/mask/generate", handle_generate)
    router.register_post("/api/mask/refine", handle_refine)


def _run_mask_job(router, job_id, image, method, model, output_dir):
    router.jobs.update(job_id, status="processing", progress=0.1, step="Acquiring worker...")

    def _do_mask(pool):
        page = pool.checkout(timeout=30)
        if page is None:
            router.jobs.update(job_id, status="failed", error="Workers busy", code="POOL_EXHAUSTED")
            return
        try:
            pool.reset_page(page)
            abs_image = os.path.join(PROJECT_DIR, image) if not os.path.isabs(image) else image
            router.bridge.load_image(page, abs_image)
            router.jobs.update(job_id, progress=0.3, step="Generating mask...")
            page.evaluate(f"() => {{ const m = document.querySelector('#comfyuiModel'); if (m) m.value = '{model}'; }}")
            result = router.bridge.generate_mask_only(page)
            if not result.get("ok"):
                router.jobs.update(job_id, status="failed", error=result.get("error", "Failed"), code="MASK_FAILED")
                return
            abs_output = os.path.join(PROJECT_DIR, output_dir) if not os.path.isabs(output_dir) else output_dir
            os.makedirs(abs_output, exist_ok=True)
            base = os.path.splitext(os.path.basename(image))[0]
            mask_path = os.path.join(abs_output, f"{base}_mask.png")
            router.bridge.save_canvas_to_file(page, "aiMaskCanvas", mask_path)
            router.jobs.update(job_id, status="completed", progress=1.0, results={
                "mask": mask_path, "coverage": result.get("coverage", 0),
                "auto_inverted": result.get("auto_inverted", False)
            })
        except Exception as e:
            import traceback; traceback.print_exc()
            router.jobs.update(job_id, status="failed", error=str(e), code="INTERNAL_ERROR")
        finally:
            pool.checkin(page)

    try:
        router.pool.run_on_page(_do_mask, timeout=180)
    except Exception as e:
        router.jobs.update(job_id, status="failed", error=str(e), code="INTERNAL_ERROR")
