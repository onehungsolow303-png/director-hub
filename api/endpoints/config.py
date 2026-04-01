# api/endpoints/config.py
"""Configuration endpoints: GET /api/presets, POST /api/preset"""


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

    router.register_get("/api/presets", handle_get_presets)
    router.register_post("/api/preset", handle_create_preset)
