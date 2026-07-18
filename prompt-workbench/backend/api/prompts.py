import shutil
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from database.crud import (
    add_favorite,
    create_prompt,
    create_prompt_version,
    delete_prompt,
    get_favorite_count,
    get_favorite_status,
    get_favorites,
    get_prompt,
    get_prompt_version,
    get_prompt_versions,
    get_prompts,
    increment_usage_count,
    is_favorite,
    remove_favorite,
    update_prompt,
    update_prompt_version,
)
from schemas import (
    PromptCreate,
    PromptDetailResponse,
    PromptResponse,
    PromptUpdate,
    PromptVersionCreate,
    PromptVersionResponse,
    PromptVersionUpdate,
)
from services.pattern_recognition import PatternRecognition

router = APIRouter(prefix="/prompts", tags=["skills"])
pattern_recognition = PatternRecognition()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SKILL_STORAGE = PROJECT_ROOT / "skill_folders"
SKILL_STORAGE.mkdir(exist_ok=True)


def _safe_relative_path(path: str) -> Path:
    candidate = Path(path.replace("\\", "/"))
    parts = [part for part in candidate.parts if part not in ("", ".", "..")]
    if not parts:
        raise HTTPException(status_code=400, detail="Invalid upload path")
    return Path(*parts)


def _skill_folder(prompt_id: int) -> Path:
    return SKILL_STORAGE / str(prompt_id)


def _find_skill_markdown(folder: Path) -> Path | None:
    for name in ("SKILL.md", "skill.md", "README.md", "readme.md"):
        matches = list(folder.rglob(name))
        if matches:
            return matches[0]
    return None


def _read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


@router.get("/")
def list_prompts(
    skip: int = 0,
    limit: int = 100,
    scenario: str | None = None,
    tags: list | None = None,
    pattern: str | None = None,
    rating: str | None = None,
    db: Session = Depends(get_db),
):
    if scenario in ("", "undefined"):
        scenario = None
    if pattern in ("", "undefined"):
        pattern = None
    rating_int = None
    if rating not in (None, "", "undefined"):
        try:
            rating_int = int(rating)
        except ValueError:
            rating_int = None

    result = get_prompts(db, skip=skip, limit=limit, scenario=scenario, tags=tags, pattern=pattern, rating=rating_int)
    return {"items": result["items"], "total": result["total"], "skip": skip, "limit": limit}


@router.get("/favorites/list")
def list_favorites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    result = get_favorites(db, skip=skip, limit=limit)
    return {"items": result["items"], "total": result["total"], "skip": skip, "limit": limit}


@router.get("/favorites/count")
def count_favorites(db: Session = Depends(get_db)):
    return {"count": get_favorite_count(db)}


@router.get("/favorites/check")
def check_favorite_batch(prompt_ids: str = "", db: Session = Depends(get_db)):
    if not prompt_ids:
        return {}
    ids = [int(item) for item in prompt_ids.split(",") if item.strip()]
    return get_favorite_status(db, ids)


@router.post("/import-folder", response_model=PromptDetailResponse)
async def import_skill_folder(
    files: list[UploadFile] = File(...),
    title: str | None = Form(None),
    scenario: str = Form("Agent Patterns"),
    tags: str = Form(""),
    model: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    uploaded_names = [file.filename or "" for file in files]
    inferred_title = title or Path(uploaded_names[0].replace("\\", "/")).parts[0]
    prompt = create_prompt(
        db,
        title=inferred_title,
        scenario=scenario,
        content="Imported skill folder. Open the downloaded ZIP or edit this record after upload.",
        tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
        model=model,
        change_note="Imported from folder upload",
    )

    folder = _skill_folder(prompt.id)
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)

    for upload in files:
        relative = _safe_relative_path(upload.filename or "")
        target = folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)

    skill_md = _find_skill_markdown(folder)
    if skill_md:
        content = _read_text(skill_md)
        version = get_prompt_version(db, prompt.current_version_id)
        if version:
            version.content = content
            version.variables = pattern_recognition.extract_variables(content)
            version.change_note = f"Imported from {skill_md.relative_to(folder).as_posix()}"
            prompt.tags = sorted(set(prompt.tags + pattern_recognition.suggest_tags(content) + ["folder-upload"]))
            db.commit()

    return get_prompt(db, prompt.id)


@router.get("/{prompt_id}", response_model=PromptDetailResponse)
def get_prompt_detail(prompt_id: int, db: Session = Depends(get_db)):
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Skill not found")
    return prompt


@router.post("/", response_model=PromptDetailResponse)
def create_new_prompt(prompt: PromptCreate, db: Session = Depends(get_db)):
    variables = pattern_recognition.extract_variables(prompt.content)
    suggested_tags = pattern_recognition.suggest_tags(prompt.content)
    result = create_prompt(
        db,
        title=prompt.title,
        scenario=prompt.scenario,
        content=prompt.content,
        tags=sorted(set(prompt.tags + suggested_tags)),
        model=prompt.model,
        change_note=prompt.change_note,
    )
    version = get_prompt_version(db, result.current_version_id)
    if version:
        version.variables = variables
        db.commit()
    return result


@router.put("/{prompt_id}", response_model=PromptResponse)
def update_existing_prompt(prompt_id: int, prompt: PromptUpdate, db: Session = Depends(get_db)):
    result = update_prompt(db, prompt_id, **prompt.dict(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="Skill not found")
    return result


@router.delete("/{prompt_id}")
def delete_existing_prompt(prompt_id: int, db: Session = Depends(get_db)):
    success = delete_prompt(db, prompt_id)
    folder = _skill_folder(prompt_id)
    if folder.exists():
        shutil.rmtree(folder)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"message": "Skill deleted successfully"}


@router.get("/{prompt_id}/download.zip")
def download_skill_folder(prompt_id: int, db: Session = Depends(get_db)):
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Skill not found")

    folder = _skill_folder(prompt_id)
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
        version = get_prompt_version(db, prompt.current_version_id) if prompt.current_version_id else None
        (folder / "SKILL.md").write_text(version.content if version else prompt.title, encoding="utf-8")

    zip_path = SKILL_STORAGE / f"{prompt_id}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in folder.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(folder))

    safe_title = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in prompt.title).strip("-") or "skill"
    return FileResponse(zip_path, media_type="application/zip", filename=f"{safe_title}.zip")


@router.post("/{prompt_id}/copy")
def copy_prompt(prompt_id: int, db: Session = Depends(get_db)):
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Skill not found")
    increment_usage_count(db, prompt_id)
    version = get_prompt_version(db, prompt.current_version_id) if prompt.current_version_id else None
    return {"success": True, "content": version.content if version else ""}


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionResponse])
def list_prompt_versions(prompt_id: int, db: Session = Depends(get_db)):
    return get_prompt_versions(db, prompt_id)


@router.post("/{prompt_id}/versions", response_model=PromptVersionResponse)
def create_new_version(prompt_id: int, version: PromptVersionCreate, db: Session = Depends(get_db)):
    result = create_prompt_version(db, prompt_id, version.content, version.change_note)
    if not result:
        raise HTTPException(status_code=404, detail="Skill not found")
    result.variables = pattern_recognition.extract_variables(version.content)
    db.commit()
    return result


@router.put("/{prompt_id}/versions/{version_id}", response_model=PromptVersionResponse)
def update_existing_version(
    prompt_id: int,
    version_id: int,
    version: PromptVersionUpdate,
    db: Session = Depends(get_db),
):
    result = update_prompt_version(db, version_id, **version.dict(exclude_unset=True))
    if not result or result.prompt_id != prompt_id:
        raise HTTPException(status_code=404, detail="Version not found")
    if version.content:
        result.variables = pattern_recognition.extract_variables(version.content)
        db.commit()
    return result


@router.post("/{prompt_id}/favorite")
def toggle_favorite(prompt_id: int, db: Session = Depends(get_db)):
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Skill not found")
    if is_favorite(db, prompt_id):
        remove_favorite(db, prompt_id)
        return {"success": True, "is_favorite": False, "message": "已取消收藏"}
    add_favorite(db, prompt_id)
    return {"success": True, "is_favorite": True, "message": "已收藏"}


@router.get("/{prompt_id}/favorite")
def check_favorite(prompt_id: int, db: Session = Depends(get_db)):
    prompt = get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"is_favorite": is_favorite(db, prompt_id)}
