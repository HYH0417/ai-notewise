import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import ab_test_router, config_router, prompts_router, search_router
from database import init_db

init_db()

app = FastAPI(title="Agent Skills Library", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prompts_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(ab_test_router, prefix="/api")
app.include_router(config_router, prefix="/api")

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


def frontend_page(filename: str) -> FileResponse:
    return FileResponse(os.path.join(frontend_dir, filename))


if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")

    @app.get("/")
    async def root():
        return frontend_page("index.html")

    @app.get("/prompts")
    async def prompts_page():
        return frontend_page("prompts.html")

    @app.get("/prompt-detail")
    async def prompt_detail_page():
        return frontend_page("prompt-detail.html")

    @app.get("/prompt-edit")
    async def prompt_edit_page():
        return frontend_page("prompt-edit.html")

    @app.get("/favorites")
    async def favorites_page():
        return frontend_page("favorites.html")

    @app.get("/help")
    async def help_page():
        return frontend_page("help.html")

    @app.get("/settings")
    async def settings_page():
        return frontend_page("settings.html")

    @app.get("/ab-test")
    async def ab_test_page():
        return frontend_page("ab-test.html")
