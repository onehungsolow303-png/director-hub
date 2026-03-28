# api/router.py
"""URL routing and request handling for /api/* endpoints."""
import json
import traceback


class APIRouter:
    def __init__(self, job_manager, pool, bridge):
        self.jobs = job_manager
        self.pool = pool
        self.bridge = bridge
        self._routes_get = {}
        self._routes_post = {}
        self._custom_presets = {}

    def register_get(self, path, handler):
        self._routes_get[path] = handler

    def register_post(self, path, handler):
        self._routes_post[path] = handler

    def handle_request(self, handler, method, path, body=None):
        path = path.split("?")[0].rstrip("/")
        params = {}
        if body and method == "POST":
            try:
                params = json.loads(body) if body else {}
            except json.JSONDecodeError:
                return 400, {"error": "Invalid JSON body", "code": "BAD_REQUEST"}
        routes = self._routes_get if method == "GET" else self._routes_post
        if path in routes:
            try:
                return routes[path](params)
            except Exception as e:
                traceback.print_exc()
                return 500, {"error": str(e), "code": "INTERNAL_ERROR"}
        for route_path, route_handler in routes.items():
            if ":id" in route_path:
                prefix = route_path.split(":id")[0]
                if path.startswith(prefix) and len(path) > len(prefix):
                    params["_id"] = path[len(prefix):]
                    try:
                        return route_handler(params)
                    except Exception as e:
                        traceback.print_exc()
                        return 500, {"error": str(e), "code": "INTERNAL_ERROR"}
        return 404, {"error": f"Unknown API endpoint: {path}", "code": "NOT_FOUND"}

    def send_json(self, handler, status_code, data):
        body = json.dumps(data).encode()
        handler.send_response(status_code)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
