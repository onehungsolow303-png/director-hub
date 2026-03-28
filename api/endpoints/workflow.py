"""Workflow endpoints: POST /api/workflow/build, GET /api/workflow/templates"""
import json
import os

from api.utils import PROJECT_DIR


def register(router):

    def handle_build(params):
        def _do_build(pool):
            page = pool.checkout(timeout=10)
            if page is None:
                return 503, {"error": "All browser workers busy", "code": "POOL_EXHAUSTED"}
            try:
                pool.reset_page(page)
                page.evaluate("() => { const tabs = document.querySelectorAll('.tab-btn'); if (tabs[1]) tabs[1].click(); }")
                page.wait_for_timeout(500)
                result = router.bridge.build_workflow(page, params)
                if "error" in result:
                    return 500, {"error": result["error"], "code": "WORKFLOW_BUILD_FAILED"}
                install_list = page.evaluate("""() => {
                    const items = document.querySelectorAll('#installList li');
                    return Array.from(items).map(li => li.textContent.trim());
                }""")
                steps = page.evaluate("""() => {
                    const items = document.querySelectorAll('#stepsList li');
                    return Array.from(items).map(li => li.textContent.trim());
                }""")
                result["install_list"] = install_list
                result["steps"] = steps
                return 200, result
            finally:
                pool.checkin(page)

        try:
            return router.pool.run_on_page(_do_build, timeout=15)
        except Exception as e:
            return 500, {"error": str(e), "code": "INTERNAL_ERROR"}

    def handle_templates(params):
        templates = []
        for f in os.listdir(PROJECT_DIR):
            if f.startswith("starter-workflow-") and f.endswith(".json"):
                name = f.replace("starter-workflow-", "").replace(".json", "")
                templates.append({"name": name, "file": f})
        return 200, {"templates": templates}

    router.register_post("/api/workflow/build", handle_build)
    router.register_get("/api/workflow/templates", handle_templates)
