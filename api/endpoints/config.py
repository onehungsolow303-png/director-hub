# api/endpoints/config.py
"""Configuration endpoints: GET /api/presets, POST /api/preset, GET /api/comfyui/status"""
import json
import urllib.request
import urllib.error


def register(router):
    _presets_cache = {"data": None}

    def _get_presets():
        if _presets_cache["data"] is None:
            def _read(pool):
                page = pool.checkout(timeout=10)
                if page is None:
                    return {}
                try:
                    return router.bridge.get_presets(page)
                finally:
                    pool.checkin(page)
            try:
                _presets_cache["data"] = router.pool.run_on_page(_read, timeout=15)
            except Exception:
                return {}
        return _presets_cache["data"] or {}

    router.bridge.get_presets_cached = _get_presets

    def handle_get_presets(params):
        presets = _get_presets()
        combined = {**presets, **router._custom_presets}
        return 200, {"presets": combined, "default": "dark-balanced"}

    def handle_create_preset(params):
        name = params.get("name")
        settings = params.get("settings")
        if not name:
            return 400, {"error": "Missing required field: name", "code": "BAD_REQUEST"}
        if not settings:
            return 400, {"error": "Missing required field: settings", "code": "BAD_REQUEST"}
        router._custom_presets[name] = settings
        return 200, {"ok": True, "name": name}

    def handle_comfyui_status(params):
        try:
            req = urllib.request.Request("http://127.0.0.1:8000/system_stats")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                system = data.get("system", {})
                devices = data.get("devices", [{}])
                gpu_name = devices[0].get("name", "unknown") if devices else "unknown"
                return 200, {
                    "connected": True,
                    "port": 8000,
                    "version": system.get("comfyui_version", "unknown"),
                    "gpu": gpu_name,
                    "ram_free_gb": round(system.get("ram_free", 0) / 1e9, 1),
                    "python_version": system.get("python_version", "unknown")
                }
        except Exception:
            return 200, {"connected": False, "port": 8000, "error": "ComfyUI not reachable"}

    router.register_get("/api/presets", handle_get_presets)
    router.register_post("/api/preset", handle_create_preset)
    router.register_get("/api/comfyui/status", handle_comfyui_status)
