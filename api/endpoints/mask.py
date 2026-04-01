"""Mask endpoints: POST /api/mask/generate, POST /api/mask/refine"""
import os
import threading
import base64

from api.utils import PROJECT_DIR, resolve_path, resolve_output_dir


def register(router):

    def handle_generate(params):
        image = params.get("image")
        if not image:
            return 400, {"error": "Missing required field: image", "code": "NO_IMAGE"}
        method = params.get("method", "browser")
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
                abs_image = resolve_path(image_path)
                router.bridge.load_image(page, abs_image)
                abs_mask = resolve_path(mask_path)
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
                abs_output = resolve_output_dir(out_dir)
                base = os.path.splitext(os.path.basename(mask_path))[0]
                out_path = os.path.join(abs_output, f"{base}_refined.png")
                router.bridge.save_canvas_to_file(page, "aiMaskCanvas", out_path)
                return 200, {"refined_mask": out_path, "coverage": round(coverage, 4)}
            finally:
                pool.checkin(page)

        try:
            return router.pool.run_on_page(_do_refine, timeout=60)
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
            abs_image = resolve_path(image)
            router.bridge.load_image(page, abs_image)
            router.jobs.update(job_id, progress=0.3, step="Generating mask...")
            page.evaluate("(m) => { const el = document.querySelector('#aiModel'); if (el) el.value = m; }", model)
            result = router.bridge.run_ai_remove(page,
                on_progress=lambda step: router.jobs.update(job_id, progress=0.5, step=step))
            if not result.get("ok"):
                router.jobs.update(job_id, status="failed", error=result.get("error", "Failed"), code="MASK_FAILED")
                return
            abs_output = resolve_output_dir(output_dir)
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
