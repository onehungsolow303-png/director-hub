"""Endpoint handlers for /api/extract, /api/batch, and /api/status/:id."""

import os
import threading
import time

# PROJECT_DIR is the repo root (two levels up from this file:
#   api/endpoints/extract.py -> api/endpoints/ -> api/ -> project root)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register(router):
    """Register all extract-related routes on *router*."""
    router.register_post("/api/extract", handle_extract(router))
    router.register_post("/api/batch", handle_batch(router))
    router.register_get("/api/status/:id", handle_status(router))


# ---------------------------------------------------------------------------
# Handler factories — each returns a callable that closes over *router*
# ---------------------------------------------------------------------------

def handle_extract(router):
    """Return a POST /api/extract handler bound to *router*."""

    def _handler(params):
        image = params.get("image")
        if not image:
            return 400, {"error": "Missing required field: image", "code": "BAD_REQUEST"}

        preset = params.get("preset", "default")
        mode = params.get("mode", "remove")
        output_dir = params.get("output_dir") or os.path.join(PROJECT_DIR, "output", "api")
        settings_override = params.get("settings_override") or {}

        job_id = router.jobs.create("extract", {
            "image": image,
            "preset": preset,
            "mode": mode,
            "output_dir": output_dir,
            "settings_override": settings_override,
        })

        t = threading.Thread(
            target=_run_extract_job,
            args=(router, job_id, image, preset, mode, output_dir, settings_override),
            daemon=True,
        )
        t.start()

        return 202, {"job_id": job_id, "status": "pending"}

    return _handler


def handle_batch(router):
    """Return a POST /api/batch handler bound to *router*."""

    def _handler(params):
        images = params.get("images")
        if not images or not isinstance(images, list) or len(images) == 0:
            return 400, {"error": "Missing or empty required field: images (must be a list)", "code": "BAD_REQUEST"}

        preset = params.get("preset", "default")
        mode = params.get("mode", "remove")
        ai_source = params.get("ai_source", "comfyui")
        output_dir = params.get("output_dir") or os.path.join(PROJECT_DIR, "output", "api", "batch")

        job_id = router.jobs.create("batch", {
            "images": images,
            "preset": preset,
            "mode": mode,
            "ai_source": ai_source,
            "output_dir": output_dir,
            "total": len(images),
        })

        t = threading.Thread(
            target=_run_batch_job,
            args=(router, job_id, images, preset, mode, ai_source, output_dir),
            daemon=True,
        )
        t.start()

        return 202, {"job_id": job_id, "status": "pending", "total": len(images)}

    return _handler


def handle_status(router):
    """Return a GET /api/status/:id handler bound to *router*."""

    def _handler(params):
        job_id = params.get("_id")
        job = router.jobs.get(job_id)
        if job is None:
            return 404, {"error": f"Job not found: {job_id}", "code": "NOT_FOUND"}

        response = {
            "job_id": job.get("job_id"),
            "job_type": job.get("job_type"),
            "status": job.get("status"),
            "progress": job.get("progress"),
            "step": job.get("step"),
            "results": job.get("results"),
            "error": job.get("error"),
            "elapsed_ms": job.get("elapsed_ms"),
            "created_at": job.get("created_at"),
        }
        return 200, response

    return _handler


# ---------------------------------------------------------------------------
# Background job: single image extraction
# ---------------------------------------------------------------------------

def _run_extract_job(router, job_id, image, preset, mode, output_dir, settings_override):
    """Run a single-image extraction job in a background thread."""
    page = None
    try:
        router.jobs.update(job_id, status="processing", step="checkout_page", progress=5)

        page = router.pool.checkout(timeout=30)
        if page is None:
            router.jobs.update(
                job_id,
                status="failed",
                error="Pool exhausted: no browser page available",
                code="POOL_EXHAUSTED",
            )
            return

        # Resolve image path
        image_resolved = _resolve_image_path(image)

        # Reset page to a clean state
        router.jobs.update(job_id, step="reset_page", progress=10)
        router.pool.reset_page(page)

        # Load image (base64 data URL or file path)
        router.jobs.update(job_id, step="load_image", progress=15)
        if image_resolved.startswith("data:"):
            load_result = router.bridge.load_image_base64(page, image_resolved)
        else:
            load_result = router.bridge.load_image(page, image_resolved)

        if not load_result.get("loaded"):
            router.jobs.update(
                job_id,
                status="failed",
                error=f"Failed to load image: {load_result}",
                code="LOAD_ERROR",
            )
            return

        # Apply preset
        router.jobs.update(job_id, step="apply_preset", progress=20)
        _apply_preset_safe(router, page, preset)

        # Apply settings overrides (if any)
        if settings_override:
            router.jobs.update(job_id, step="apply_settings", progress=25)
            router.bridge.apply_settings_override(page, settings_override)

        # Run the appropriate extraction mode
        if mode == "ai-remove":
            router.jobs.update(job_id, step="ai_remove", progress=30)
            ai_result = router.bridge.run_ai_remove(
                page,
                on_progress=lambda s: router.jobs.update(job_id, step=f"ai_remove: {s}"),
            )
            if not ai_result.get("ok"):
                router.jobs.update(
                    job_id,
                    status="failed",
                    error=ai_result.get("error", "AI remove failed"),
                    code="AI_REMOVE_ERROR",
                )
                return

            # Enhance after ai-remove
            router.jobs.update(job_id, step="enhance", progress=65)
            enhance_result = router.bridge.run_enhance(page)
            if not enhance_result.get("ok"):
                # Non-fatal — log but continue
                router.jobs.update(job_id, step="enhance_skipped")

        elif mode == "crop":
            router.jobs.update(job_id, step="process_image", progress=30)
            proc_result = router.bridge.run_process_image(
                page,
                on_progress=lambda s: router.jobs.update(job_id, step=f"process: {s}"),
            )
            if not proc_result.get("ok"):
                router.jobs.update(
                    job_id,
                    status="failed",
                    error=proc_result.get("error", "Process image failed"),
                    code="PROCESS_ERROR",
                )
                return

        else:
            # Default: heuristic removal ("remove" / "multi" / any other mode)
            router.jobs.update(job_id, step="process_image", progress=30)
            proc_result = router.bridge.run_process_image(
                page,
                on_progress=lambda s: router.jobs.update(job_id, step=f"process: {s}"),
            )
            if not proc_result.get("ok"):
                router.jobs.update(
                    job_id,
                    status="failed",
                    error=proc_result.get("error", "Process image failed"),
                    code="PROCESS_ERROR",
                )
                return

        # Extract all results to output_dir
        router.jobs.update(job_id, step="extract_results", progress=80)
        base_name = f"job_{job_id}"
        extraction = router.bridge.extract_all_results(page, output_dir, base_name)

        router.jobs.update(
            job_id,
            status="completed",
            progress=100,
            step="done",
            results={
                "output_dir": output_dir,
                "base_name": base_name,
                "image_dims": load_result,
                "extraction": extraction,
            },
        )

    except Exception as exc:
        import traceback
        router.jobs.update(
            job_id,
            status="failed",
            error=f"{type(exc).__name__}: {exc}",
            code="INTERNAL_ERROR",
        )
        traceback.print_exc()

    finally:
        if page is not None:
            router.pool.checkin(page)


# ---------------------------------------------------------------------------
# Background job: batch extraction
# ---------------------------------------------------------------------------

def _run_batch_job(router, job_id, images, preset, mode, ai_source, output_dir):
    """Run a batch extraction job in a background thread."""
    page = None
    try:
        router.jobs.update(job_id, status="processing", step="checkout_page", progress=2)

        page = router.pool.checkout(timeout=30)
        if page is None:
            router.jobs.update(
                job_id,
                status="failed",
                error="Pool exhausted: no browser page available",
                code="POOL_EXHAUSTED",
            )
            return

        total = len(images)
        completed_images = []
        per_image_results = {}

        for idx, image in enumerate(images):
            image_label = f"image_{idx:03d}"
            progress_base = int((idx / total) * 90)

            try:
                router.jobs.update(
                    job_id,
                    step=f"processing {image_label} ({idx + 1}/{total})",
                    progress=progress_base + 2,
                )

                # Reset page for each image
                router.pool.reset_page(page)

                # Resolve and load image
                image_resolved = _resolve_image_path(image)
                if image_resolved.startswith("data:"):
                    load_result = router.bridge.load_image_base64(page, image_resolved)
                else:
                    load_result = router.bridge.load_image(page, image_resolved)

                if not load_result.get("loaded"):
                    per_image_results[image_label] = {
                        "ok": False,
                        "error": f"Failed to load image: {load_result}",
                        "image": image,
                    }
                    continue

                # Apply preset
                _apply_preset_safe(router, page, preset)

                # Run extraction
                if mode == "ai-remove":
                    proc_result = router.bridge.run_ai_remove(page)
                    if proc_result.get("ok"):
                        router.bridge.run_enhance(page)
                else:
                    proc_result = router.bridge.run_process_image(page)

                if not proc_result.get("ok"):
                    per_image_results[image_label] = {
                        "ok": False,
                        "error": proc_result.get("error", "Processing failed"),
                        "image": image,
                    }
                    continue

                # Save results for this image
                image_output_dir = os.path.join(output_dir, image_label)
                base_name = f"batch_{job_id}_{image_label}"
                extraction = router.bridge.extract_all_results(page, image_output_dir, base_name)

                per_image_results[image_label] = {
                    "ok": True,
                    "image": image,
                    "output_dir": image_output_dir,
                    "base_name": base_name,
                    "image_dims": load_result,
                    "extraction": extraction,
                }
                completed_images.append(image_label)

            except Exception as img_exc:
                per_image_results[image_label] = {
                    "ok": False,
                    "error": f"{type(img_exc).__name__}: {img_exc}",
                    "image": image,
                }

        router.jobs.update(
            job_id,
            status="completed",
            progress=100,
            step="done",
            results={
                "total": total,
                "completed": len(completed_images),
                "failed": total - len(completed_images),
                "completed_images": completed_images,
                "per_image": per_image_results,
                "output_dir": output_dir,
            },
        )

    except Exception as exc:
        import traceback
        router.jobs.update(
            job_id,
            status="failed",
            error=f"{type(exc).__name__}: {exc}",
            code="INTERNAL_ERROR",
        )
        traceback.print_exc()

    finally:
        if page is not None:
            router.pool.checkin(page)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_image_path(image):
    """Resolve *image* to an absolute path or return a data URL as-is."""
    if image.startswith("data:"):
        return image
    if os.path.isabs(image):
        return image
    return os.path.join(PROJECT_DIR, image)


def _apply_preset_safe(router, page, preset_name):
    """Apply *preset_name* to *page*, falling back gracefully if not found."""
    try:
        # Try built-in presets via AppBridge first
        result = router.bridge.apply_preset(page, preset_name)
        if result.get("ok"):
            return result

        # Fall back to custom presets stored on the router
        custom = router._custom_presets.get(preset_name)
        if custom:
            return router.bridge.apply_settings_override(page, custom)

        # Try to get presets from the cached bridge callable
        try:
            presets = router.bridge.get_presets_cached()
            if preset_name in presets:
                return router.bridge.apply_settings_override(page, presets[preset_name])
        except AttributeError:
            pass  # get_presets_cached not available

        return result  # Return the original (failed) result — not fatal
    except Exception:
        return {"ok": False, "error": "preset apply raised an exception"}
