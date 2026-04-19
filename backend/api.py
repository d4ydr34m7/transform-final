"""HTTP routes for analysis and chat."""
import io
import os
import shutil
import subprocess
import tempfile
import zipfile
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from github import list_user_repos

from config import BASE_DIR
from models import (
    AnalyzeRequest,
    AnalyzeResponse,
    FileListResponse,
    AnalysisMetadata,
    AnalysisListResponse,
    AnalysisChatRequest,
    AnalysisChatResponse,
    ValidationReport,
)
from services import db as db_mod
from services import s3 as s3_mod
from services import bedrock_agent as bedrock_mod
from services import transform as transform_mod

router = APIRouter()
logger = logging.getLogger(__name__)


def _is_safe_file_name(file_name: str) -> bool:
    parts = file_name.replace("\\", "/").split("/")
    if not parts or "" in parts or ".." in parts or "." in parts or ".." in (p.strip() for p in parts):
        return False
    return True


@router.post("/analysis/run", response_model=AnalyzeResponse)
def run_analysis(req: AnalyzeRequest) -> AnalyzeResponse:
    analysis_id = f"analysis-{uuid4().hex[:8]}"
    analysis_dir = BASE_DIR / analysis_id
    if not s3_mod.s3_enabled():
        analysis_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc)
    db_mod.db_insert_run(
        analysis_id=analysis_id,
        repo=req.repo,
        created_at=created_at,
        status="in_progress",
        initiated_by=req.initiated_by,
    )

    repo_url = f"https://github.com/{req.repo}.git"
    temp_dir = None

    try:
        temp_dir = tempfile.mkdtemp(prefix="repo_clone_")
        temp_path = Path(temp_dir)
        clone_cmd = ["git", "clone", "--depth", "1", repo_url, str(temp_path)]
        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=f"Failed to clone repository: {result.stderr}")

        repo_path = temp_path
        repo_name = req.repo.split("/")[-1]
        if (temp_path / repo_name).exists():
            repo_path = temp_path / repo_name

        if transform_mod.transform_enabled():
            transform_mod.set_current_transform_run({
                "analysis_id": analysis_id,
                "analysis_dir": analysis_dir,
                "use_s3": s3_mod.s3_enabled(),
            })
            try:
                timeout_seconds = transform_mod.transform_timeout_seconds()
                logger.info(
                    "Transform start analysis_id=%s repo=%s",
                    analysis_id,
                    req.repo,
                )
                t0 = time.time()
                transform_res = transform_mod.run_transform_atx(str(repo_path), timeout_seconds=timeout_seconds)
                duration_s = int(time.time() - t0)
                logger.info(
                    "Transform done ok=%s exit_code=%s duration_seconds=%s",
                    transform_res.get("ok"),
                    transform_res.get("exit_code"),
                    duration_s,
                )
                log_name = str(
                    transform_res.get("log_path")
                    or ("transform.log" if transform_res.get("ok") else "transform_failed.log")
                )
                log_text = str(transform_res.get("output_tail") or "")
                if not log_text:
                    log_text = (
                        f"Transform produced no output. error_type={transform_res.get('error_type')}, "
                        f"exit_code={transform_res.get('exit_code')}"
                    )
                try:
                    if s3_mod.s3_enabled():
                        s3_mod.s3_put_plain_text(analysis_id, log_name, log_text)
                    else:
                        (analysis_dir / log_name).write_text(log_text, encoding="utf-8")
                except Exception as e:
                    logger.warning("Transform log persist failed analysis_id=%s err=%s", analysis_id, str(e))
                try:
                    transform_mod.copy_transform_output(repo_path, analysis_id, analysis_dir)
                except Exception as e:
                    logger.warning("Transform output copy failed analysis_id=%s err=%s", analysis_id, str(e))
            finally:
                transform_mod.set_current_transform_run(None)
        else:
            logger.info(
                "Transform skipped analysis_id=%s repo=%s (TRANSFORM_ENABLED is false)",
                analysis_id,
                req.repo,
            )

        languages = transform_mod.detect_languages(repo_path)
        architecture_content = transform_mod.generate_architecture_md(repo_path)
        entrypoints_content = transform_mod.generate_entrypoints_md(repo_path)
        dependencies_content = transform_mod.generate_dependencies_md(repo_path)
        repo_summary_content = transform_mod.generate_repo_summary_md(repo_path, repo_name, languages)

        if s3_mod.s3_enabled():
            s3_mod.s3_put_text(analysis_id, "architecture.md", architecture_content)
            s3_mod.s3_put_text(analysis_id, "entrypoints.md", entrypoints_content)
            s3_mod.s3_put_text(analysis_id, "dependencies.md", dependencies_content)
            s3_mod.s3_put_text(analysis_id, "repo_summary.md", repo_summary_content)
        else:
            (analysis_dir / "architecture.md").write_text(architecture_content, encoding="utf-8")
            (analysis_dir / "entrypoints.md").write_text(entrypoints_content, encoding="utf-8")
            (analysis_dir / "dependencies.md").write_text(dependencies_content, encoding="utf-8")
            (analysis_dir / "repo_summary.md").write_text(repo_summary_content, encoding="utf-8")

    except subprocess.TimeoutExpired:
        db_mod.db_update_run_status(analysis_id, "failed")
        raise HTTPException(status_code=408, detail="Repository clone timed out")
    except HTTPException:
        db_mod.db_update_run_status(analysis_id, "failed")
        raise
    except Exception as e:
        db_mod.db_update_run_status(analysis_id, "failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

    db_mod.db_update_run_status(analysis_id, "completed")
    s3_mod.publish_completion_notification(
        analysis_id=analysis_id,
        repo=req.repo,
        status="completed",
        initiated_by=req.initiated_by,
    )
    bedrock_mod.start_kb_ingestion()
    transform_mod.cleanup_old_analyses(req.repo)

    return AnalyzeResponse(analysis_id=analysis_id)


@router.get("/analysis", response_model=AnalysisListResponse)
def list_analyses() -> AnalysisListResponse:
    rows = db_mod.db_list_runs()
    analyses: list[AnalysisMetadata] = []
    for item in rows:
        try:
            created_at = datetime.fromisoformat(str(item["created_at"]))
        except Exception:
            created_at = datetime.now(timezone.utc)
        analyses.append(
            AnalysisMetadata(
                analysis_id=str(item["analysis_id"]),
                repo=str(item["repo"]),
                created_at=created_at,
                status=str(item["status"]),
                initiated_by=item.get("initiated_by"),
            )
        )
    return AnalysisListResponse(analyses=analyses)


@router.get("/analysis/{analysis_id}/files", response_model=FileListResponse)
def list_files(analysis_id: str) -> FileListResponse:
    if s3_mod.s3_enabled():
        files = s3_mod.s3_list_files(analysis_id)
        if not files:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return FileListResponse(files=files)
    analysis_dir = BASE_DIR / analysis_id
    if not analysis_dir.exists():
        raise HTTPException(status_code=404, detail="Analysis not found")
    files = [
        str(f.relative_to(analysis_dir).as_posix())
        for f in analysis_dir.rglob("*")
        if f.is_file()
    ]
    return FileListResponse(files=files)


@router.get("/analysis/{analysis_id}/file")
def get_file(analysis_id: str, path: str):
    file_name = path.strip()
    if not file_name:
        raise HTTPException(status_code=400, detail="Missing path")
    if not _is_safe_file_name(file_name):
        raise HTTPException(status_code=400, detail="Invalid file name")
    if s3_mod.s3_enabled():
        return {"content": s3_mod.s3_get_text(analysis_id, file_name)}
    analysis_dir = BASE_DIR / analysis_id
    if not analysis_dir.exists():
        raise HTTPException(status_code=404, detail="Analysis not found")
    file_path = (analysis_dir / file_name).resolve()
    if not str(file_path).startswith(str(analysis_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return {"content": file_path.read_text(encoding="utf-8")}


@router.get("/analysis/{analysis_id}/download")
def download_analysis(analysis_id: str):
    zip_buffer = io.BytesIO()
    if s3_mod.s3_enabled():
        files = s3_mod.s3_list_files(analysis_id)
        if not files:
            raise HTTPException(status_code=404, detail="Analysis not found")
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for name in files:
                if not _is_safe_file_name(name):
                    continue
                data = s3_mod.s3_get_bytes(analysis_id, name)
                zf.writestr(name, data)
    else:
        analysis_dir = BASE_DIR / analysis_id
        if not analysis_dir.exists():
            raise HTTPException(status_code=404, detail="Analysis not found")
        file_paths = [p for p in analysis_dir.rglob("*") if p.is_file()]
        if not file_paths:
            raise HTTPException(status_code=404, detail="Analysis not found")
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(file_paths, key=lambda x: str(x.relative_to(analysis_dir)).lower()):
                zf.write(p, arcname=str(p.relative_to(analysis_dir).as_posix()))
    zip_bytes = zip_buffer.getvalue()
    filename = f"analysis-{analysis_id}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/analysis/{analysis_id}/chat", response_model=AnalysisChatResponse)
def chat_for_analysis(analysis_id: str, req: AnalysisChatRequest) -> AnalysisChatResponse:
    if not bedrock_mod.bedrock_enabled():
        return AnalysisChatResponse(
            answer="Bedrock chat is disabled. Set BEDROCK_ENABLED=true and configure the agent.",
            sources=[],
            validation_report=None,
        )
    session_id = (req.session_id or "").strip() or analysis_id
    try:
        answer, sources = bedrock_mod.invoke_agent(analysis_id, session_id, req.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Agent chat failed analysis_id=%s: %s", analysis_id, e)
        raise HTTPException(status_code=502, detail=f"Chat failed: {e}")
    return AnalysisChatResponse(
        answer=answer,
        sources=sources,
        validation_report=ValidationReport(passed=True, violations=[]),
    )


@router.get("/repos")
def get_repos():
    return {"repos": list_user_repos()}


transform_mod.register_transform_signal_handlers()
