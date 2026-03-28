"""Endpoint handlers for /api/extract, /api/batch, and /api/status/:id."""

import os
import threading

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def register(router):
    """Register all extract-related routes on *router*."""
    router.register_post("/api/extract", _handle_extract(router))
    router.register_post("/api/batch", _handle_batch(router))
    router.register_get("/api/status/:id", _handle_status(router))


def _handle_extract(router):
    def _handler(params):
        image = params.get("image")
        if not image:
            return 400, {"error": "Missing required field: image", "code": "NO_IMAGE"}
        preset = params.get("preset", "dark-balanced")
        mode = params.get("mode", "ai-remove")
        output_dir = params.get("output_dir", os.path.join(PROJECT_DIR, "output"))
        settings_override = params.get("settings_override", {})

        job_id = router.jobs.create("extract", {
            "image": image, "preset": preset, "mode": mode,
            "output_dir": output_dir, "settings_override": settings_override
        })
        thread = threading.Thread(
            target=_run_extract_job,
            args=(router, job_id, image, preset, mode, output_dir, settings_override),
            daemon=True,
        )
        thread.start()
        return 202, {"job_id": job_id, "status": "queued"}
    return _handler


def _handle_batch(router):
    def _handler(params):
        images = params.get("images", [])
        if not images:
            return 400, {"error": "Missing required field: images", "code": "NO_IMAGE"}
        preset = params.get("preset", "dark-balanced")
        mode = params.get("mode", "ai-remove")
        ai_source = params.get("ai_source", "comfyui")
        output_dir = params.get("output_dir", os.path.join(PROJECT_DIR, "output", "batch"))

        job_id = router.jobs.create("batch", {
            "images": images, "preset": preset, "mode": mode,
            "ai_source": ai_source, "output_dir": output_dir, "total": len(images)
        })
        thread = threading.Thread(
            target=_run_batch_job,
            args=(router, job_id, images, preset, mode, ai_source, output_dir),
            daemon=True,
        )
        thread.start()
        return 202, {"job_id": job_id, "status": "queued", "total": len(images)}
    return _handler


def _handle_status(router):
    def _handler(params):
        job_id = params.get("_id", "")
        job = router.jobs.get(job_id)
        if not job:
            return 404, {"error": f"Job not found: {job_id}", "code": "JOB_NOT_FOUND"}
        response = {
            "job_id": job["job_id"],
            "status": job["status"],
            "progress": job["progress"],
            "step": job["step"],
            "elapsed_ms": job.get("elapsed_ms", 0),
        }
        if job["status"] == "completed":
            response["results"] = job["results"]
        if job["status"] == "failed":
            response["error"] = job["error"]
            response["code"] = job.get("code")
        return 200, response
    return _handler


def _resolve_image_path(image):
    if image.startswith("data:"):
        return image
    if os.path.isabs(image):
        return image
    return os.path.join(PROJECT_DIR, image)


def _run_extract_job(router, job_id, image, preset, mode, output_dir, settings_override):
    """Run extraction via pool.run_on_page() — all Playwright ops on pool thread."""
    router.jobs.update(job_id, status="processing", progress=0.1, step="Queued for browser worker...")

    def _do_extract(pool):
        page = pool.checkout(timeout=30)
        if page is None:
            router.jobs.update(job_id, status="failed", error="All browser workers busy", code="POOL_EXHAUSTED")
            return
        try:
            pool.reset_page(page)
            router.jobs.update(job_id, progress=0.15, step="Loading image...")

            image_path = _resolve_image_path(image)
            if image_path.startswith("data:"):
                load_result = router.bridge.load_image_base64(page, image_path)
            else:
                load_result = router.bridge.load_image(page, image_path)
            if not load_result.get("loaded"):
                router.jobs.update(job_id, status="failed", error="Failed to load image", code="LOAD_FAILED")
                return

            router.jobs.update(job_id, progress=0.2, step="Applying preset...")
            router.bridge.apply_preset(page, preset)
            if settings_override:
                router.bridge.apply_settings_override(page, settings_override)

            abs_output = os.path.join(PROJECT_DIR, output_dir) if not os.path.isabs(output_dir) else output_dir
            os.makedirs(abs_output, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(image if not image.startswith("data:") else "api_input.png"))[0]

            if mode == "ai-remove":
                router.jobs.update(job_id, progress=0.25, step="Running AI Remove...")
                result = router.bridge.run_ai_remove(page,
                    on_progress=lambda pct, step: router.jobs.update(job_id, progress=0.2 + pct * 0.6, step=step))
            elif mode == "crop":
                page.evaluate("() => { document.querySelector('#bgMode').value = 'crop'; document.querySelector('#bgMode').dispatchEvent(new Event('change')); }")
                result = router.bridge.run_process_image(page)
            else:
                result = router.bridge.run_process_image(page)

            if not result.get("ok"):
                router.jobs.update(job_id, status="failed", error=result.get("error", "Extraction failed"), code="EXTRACTION_FAILED")
                return

            router.jobs.update(job_id, progress=0.85, step="Extracting results...")
            if mode == "ai-remove":
                router.bridge.run_enhance(page)

            results = router.bridge.extract_all_results(page, abs_output, base_name)
            router.jobs.update(job_id, status="completed", progress=1.0, step="Done", results=results)
        except Exception as e:
            import traceback; traceback.print_exc()
            router.jobs.update(job_id, status="failed", error=str(e), code="INTERNAL_ERROR")
        finally:
            pool.checkin(page)

    try:
        router.pool.run_on_page(_do_extract, timeout=180)
    except Exception as e:
        router.jobs.update(job_id, status="failed", error=str(e), code="INTERNAL_ERROR")


def _run_batch_job(router, job_id, images, preset, mode, ai_source, output_dir):
    """Run batch extraction via pool.run_on_page()."""
    router.jobs.update(job_id, status="processing", progress=0.0, step="Starting batch...")

    def _do_batch(pool):
        page = pool.checkout(timeout=30)
        if page is None:
            router.jobs.update(job_id, status="failed", error="All browser workers busy", code="POOL_EXHAUSTED")
            return
        try:
            abs_output = os.path.join(PROJECT_DIR, output_dir) if not os.path.isabs(output_dir) else output_dir
            os.makedirs(abs_output, exist_ok=True)
            completed = []
            per_image_results = {}
            total = len(images)

            for idx, img in enumerate(images):
                pool.reset_page(page)
                pct = idx / total
                router.jobs.update(job_id, progress=pct, step=f"Processing {idx+1}/{total}: {os.path.basename(img)}")
                try:
                    image_path = _resolve_image_path(img)
                    load_result = router.bridge.load_image(page, image_path)
                    if not load_result.get("loaded"):
                        per_image_results[img] = {"error": "Failed to load"}
                        continue
                    router.bridge.apply_preset(page, preset)
                    if mode == "ai-remove":
                        result = router.bridge.run_ai_remove(page)
                    else:
                        result = router.bridge.run_process_image(page)
                    if result.get("ok"):
                        base_name = os.path.splitext(os.path.basename(img))[0]
                        img_results = router.bridge.extract_all_results(page, abs_output, base_name)
                        per_image_results[img] = img_results
                        completed.append(img)
                    else:
                        per_image_results[img] = {"error": result.get("error", "Failed")}
                except Exception as e:
                    per_image_results[img] = {"error": str(e)}

            router.jobs.update(job_id, status="completed", progress=1.0,
                               step=f"Batch complete: {len(completed)}/{total}",
                               results={"completed_images": completed, "per_image": per_image_results})
        except Exception as e:
            import traceback; traceback.print_exc()
            router.jobs.update(job_id, status="failed", error=str(e), code="INTERNAL_ERROR")
        finally:
            pool.checkin(page)

    try:
        router.pool.run_on_page(_do_batch, timeout=600)
    except Exception as e:
        router.jobs.update(job_id, status="failed", error=str(e), code="INTERNAL_ERROR")
