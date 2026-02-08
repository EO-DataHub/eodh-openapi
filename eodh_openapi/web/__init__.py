import os
import os.path

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .. import utils


def create_app(
    title: str,
    base_path: str = "",
    openapi_spec: str = "openapi.json",
    static_dir: str | None = None,
) -> FastAPI:
    static_dir = static_dir or os.path.join(os.path.dirname(__file__), "static")

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

    router = APIRouter(prefix=base_path)

    @router.get("/", include_in_schema=False, response_class=HTMLResponse)
    async def docs(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "title": title,
                "url": f"{base_path}/openapi.json",
            },
        )

    @router.get("/openapi.json", include_in_schema=False, response_class=JSONResponse)
    async def spec() -> utils.OpenAPISpec:
        try:
            return utils.load_file_spec(os.path.join(static_dir, openapi_spec))
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=404,
                detail=f"OpenAPI spec file '{os.path.join(static_dir, openapi_spec)}' not found.",
            ) from e

    @router.get("/health", include_in_schema=False, response_class=JSONResponse)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    return app
