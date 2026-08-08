"""FastAPI service entrypoint.

Wraps the deterministic pipeline tools (Docs/architecture.md stages 3
and 6) as HTTP endpoints, per the "next concrete build step" flagged in
Docs/tools.md. The Claude tool-runner orchestration layer (the actual
agentic Coordinator described in Docs/harness_design.md) is not part of
this scaffold yet - this is the tool surface it will call.

Run locally from the Scripts/ directory (so `service` resolves as a
package for the relative imports used throughout):

    cd Scripts
    uvicorn service.main:app --reload --port 8000

Then see interactive docs at http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

from .routers import tools as tools_router

app = FastAPI(
    title="Test Case Generation Pipeline - Tool Service",
    description="Deterministic tool endpoints for the connected-car test case generation pipeline. See CLAUDE.md and Docs/architecture.md.",
    version="0.1.0",
)

app.include_router(tools_router.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
