import os
import os.path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


def create_app(
    title: str,
    base_path: str = "/",
    openapi_spec: str = "openapi.json",
    static_dir: str = None,
) -> FastAPI:
    static_dir = static_dir or os.path.join(os.path.dirname(__file__), "static")

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.mount(static_dir, StaticFiles(directory=static_dir), name="static")

    templates = Jinja2Templates(
        directory=os.path.join(os.path.dirname(__file__), "templates")
    )

    router = APIRouter(prefix=base_path)

    @router.get("/", include_in_schema=False, response_class=HTMLResponse)
    async def docs(request: Request):
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "title": title,
                "url": f"{base_path}/openapi.json",
            },
        )

    @router.get("/openapi.json", include_in_schema=False, response_class=FileResponse)
    async def spec():
        return FileResponse(path=os.path.join(static_dir, openapi_spec))

    app.include_router(router)
    return app
