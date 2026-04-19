"""Transform (atx) run, retention, and artifact generation."""
import json
import os
import shutil
import signal
import subprocess
import time
import logging
from pathlib import Path

from fastapi import HTTPException

from config import BASE_DIR
from services import db as db_mod
from services import s3 as s3_mod
from services import bedrock_agent as bedrock_mod

logger = logging.getLogger(__name__)

_current_transform_run: dict | None = None


def analysis_retention_n() -> int:
    raw = os.environ.get("ANALYSIS_RETENTION_N", "").strip()
    if not raw:
        return 5
    try:
        n = int(raw)
        return max(1, n)
    except Exception:
        return 5


def delete_local_analysis_dir(analysis_id: str) -> None:
    analysis_dir = BASE_DIR / analysis_id
    try:
        if analysis_dir.exists() and analysis_dir.is_dir():
            shutil.rmtree(analysis_dir)
            print(f"[retention] deleted local analysis dir: {analysis_dir}")
    except Exception as e:
        print(f"[retention] failed deleting local dir {analysis_dir}: {e}")


def cleanup_old_analyses(repo: str) -> None:
    n = analysis_retention_n()
    repo_runs = db_mod.db_list_runs(repo=repo)
    repo_runs_sorted = sorted(repo_runs, key=lambda x: x.get("created_at", ""), reverse=True)
    to_delete = repo_runs_sorted[n:]
    if not to_delete:
        return
    to_delete_ids = {r.get("analysis_id") for r in to_delete if r.get("analysis_id")}
    for aid in sorted(to_delete_ids):
        if not aid:
            continue
        if s3_mod.s3_enabled():
            s3_mod.delete_s3_prefix(aid)
        else:
            delete_local_analysis_dir(aid)
    db_mod.db_delete_runs(to_delete_ids)
    print(f"[retention] pruned {len(to_delete_ids)} analysis_runs entries for repo={repo!r} (kept {n})")


def detect_languages(repo_path: Path) -> dict[str, int]:
    lang_extensions = {
        "JavaScript": [".js", ".jsx", ".mjs"],
        "TypeScript": [".ts", ".tsx"],
        "Python": [".py", ".pyw", ".pyi"],
        "Java": [".java"],
        "Go": [".go"],
        "Rust": [".rs"],
        "C/C++": [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"],
        "C#": [".cs"],
        "Ruby": [".rb"],
        "PHP": [".php"],
        "Swift": [".swift"],
        "Kotlin": [".kt", ".kts"],
        "HTML": [".html", ".htm"],
        "CSS": [".css", ".scss", ".sass"],
        "Shell": [".sh", ".bash", ".zsh"],
        "Markdown": [".md", ".markdown"],
        "JSON": [".json"],
        "YAML": [".yaml", ".yml"],
        "Dockerfile": ["Dockerfile", ".dockerfile"],
    }
    lang_counts: dict[str, int] = {}
    for path in repo_path.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue
        ext = path.suffix.lower()
        name = path.name
        for lang, extensions in lang_extensions.items():
            if ext in extensions or name in extensions:
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
                break
    return lang_counts


def generate_architecture_md(repo_path: Path) -> str:
    lines = ["# Architecture Analysis\n"]
    top_level = sorted(repo_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    dirs = [d for d in top_level if d.is_dir() and not d.name.startswith(".")]
    files = [f for f in top_level if f.is_file() and not f.name.startswith(".")]
    if dirs:
        lines.append("## Directory Structure\n")
        for d in dirs[:25]:
            try:
                file_count = sum(1 for _ in d.rglob("*") if _.is_file())
                lines.append(f"- `{d.name}/` ({file_count} files)")
            except Exception:
                lines.append(f"- `{d.name}/`")
        if len(dirs) > 25:
            lines.append(f"- ... ({len(dirs) - 25} more directories)")
    if files:
        lines.append("\n## Key Files\n")
        for f in files[:20]:
            lines.append(f"- `{f.name}`")
        if len(files) > 20:
            lines.append(f"- ... ({len(files) - 20} more files)")
    lines.append("\n## Module Structure\n")
    important_dirs = ["src", "lib", "app", "components", "pages", "utils", "tests", "test", "__tests__"]
    found_modules = []
    for dir_name in important_dirs:
        dir_path = repo_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            try:
                file_count = sum(1 for _ in dir_path.rglob("*") if _.is_file())
                found_modules.append(f"- `{dir_name}/` ({file_count} files)")
            except Exception:
                found_modules.append(f"- `{dir_name}/`")
    if found_modules:
        lines.extend(found_modules)
    else:
        lines.append("No standard module directories detected.")
    return "\n".join(lines)


def generate_entrypoints_md(repo_path: Path) -> str:
    lines = ["# Entry Points\n"]
    entrypoint_patterns = [
        "index.js", "index.ts", "index.tsx", "index.jsx", "index.mjs",
        "main.js", "main.ts", "main.py", "main.go", "main.rs", "main.java",
        "app.js", "app.ts", "app.tsx", "app.py", "App.jsx", "App.tsx",
        "server.js", "server.ts", "server.py",
        "entrypoint.js", "entrypoint.ts",
    ]
    config_files = [
        "package.json", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml",
        "build.gradle", "setup.py", "pyproject.toml", "composer.json",
    ]
    found_entrypoints = []
    found_configs = []
    for pattern in entrypoint_patterns:
        for path in repo_path.rglob(pattern):
            if path.is_file():
                found_entrypoints.append(str(path.relative_to(repo_path)))
    for pattern in config_files:
        for path in repo_path.rglob(pattern):
            if path.is_file():
                found_configs.append(str(path.relative_to(repo_path)))
    common_dirs = ["src", "lib", "app", "main", "bin", "server"]
    for dir_name in common_dirs:
        dir_path = repo_path / dir_name
        if dir_path.is_dir():
            found_entrypoints.append(f"{dir_name}/")
    if found_entrypoints:
        lines.append("## Main Entry Points\n")
        for entry in sorted(set(found_entrypoints))[:40]:
            lines.append(f"- `{entry}`")
        if len(set(found_entrypoints)) > 40:
            lines.append(f"- ... ({len(set(found_entrypoints)) - 40} more)")
    if found_configs:
        lines.append("\n## Configuration Files\n")
        for config in sorted(set(found_configs))[:20]:
            lines.append(f"- `{config}`")
    if not found_entrypoints and not found_configs:
        lines.append("## Main Entry Points\n")
        lines.append("No standard entry points detected.")
    return "\n".join(lines)


def generate_dependencies_md(repo_path: Path) -> str:
    lines = ["# Dependencies\n"]
    package_json = repo_path / "package.json"
    if package_json.exists():
        try:
            with open(package_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                lines.append("## Node.js Dependencies\n")
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                if deps:
                    lines.append("### Runtime Dependencies\n")
                    for name, version in sorted(deps.items())[:30]:
                        lines.append(f"- `{name}`: {version}")
                    if len(deps) > 30:
                        lines.append(f"- ... ({len(deps) - 30} more)")
                if dev_deps:
                    lines.append("\n### Development Dependencies\n")
                    for name, version in sorted(dev_deps.items())[:30]:
                        lines.append(f"- `{name}`: {version}")
                    if len(dev_deps) > 30:
                        lines.append(f"- ... ({len(dev_deps) - 30} more)")
        except Exception as e:
            lines.append(f"Error parsing package.json: {e}\n")
    requirements_txt = repo_path / "requirements.txt"
    if requirements_txt.exists():
        try:
            with open(requirements_txt, "r", encoding="utf-8") as f:
                deps = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
                if deps:
                    lines.append("\n## Python Dependencies\n")
                    for dep in deps[:50]:
                        lines.append(f"- `{dep}`")
                    if len(deps) > 50:
                        lines.append(f"- ... ({len(deps) - 50} more)")
        except Exception as e:
            lines.append(f"Error parsing requirements.txt: {e}\n")
    for dep_file in ["Cargo.toml", "go.mod", "pom.xml", "build.gradle"]:
        dep_path = repo_path / dep_file
        if dep_path.exists():
            lines.append(f"\n## {dep_file}\n")
            lines.append(f"Found `{dep_file}` but parsing not implemented.")
    if len(lines) == 1:
        lines.append("No standard dependency files found.")
    return "\n".join(lines)


def generate_repo_summary_md(repo_path: Path, repo_name: str, languages: dict[str, int]) -> str:
    lines = ["# Repository Summary\n", "## Repository\n", f"- **Name**: `{repo_name}`\n"]
    if languages:
        lines.append("## Detected Languages\n")
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        total_files = sum(languages.values())
        for lang, count in sorted_langs[:10]:
            percentage = (count / total_files * 100) if total_files > 0 else 0
            lines.append(f"- **{lang}**: {count} files ({percentage:.1f}%)")
        if len(languages) > 10:
            lines.append(f"- ... ({len(languages) - 10} more languages)")
    try:
        total_files = sum(1 for _ in repo_path.rglob("*") if _.is_file() and not _.name.startswith("."))
        total_dirs = sum(1 for _ in repo_path.rglob("*") if _.is_dir() and not _.name.startswith("."))
        lines.append("\n## Statistics\n")
        lines.append(f"- **Total Files**: {total_files}")
        lines.append(f"- **Total Directories**: {total_dirs}")
    except Exception:
        pass
    lines.append("\n## Project Type Indicators\n")
    indicators = []
    if (repo_path / "package.json").exists():
        indicators.append("Node.js project (package.json found)")
    if (repo_path / "requirements.txt").exists() or (repo_path / "setup.py").exists():
        indicators.append("Python project (requirements.txt or setup.py found)")
    if (repo_path / "Cargo.toml").exists():
        indicators.append("Rust project (Cargo.toml found)")
    if (repo_path / "go.mod").exists():
        indicators.append("Go project (go.mod found)")
    if (repo_path / "pom.xml").exists():
        indicators.append("Java/Maven project (pom.xml found)")
    if (repo_path / "Dockerfile").exists():
        indicators.append("Dockerized (Dockerfile found)")
    if (repo_path / ".github").exists():
        indicators.append("GitHub Actions configured (.github found)")
    if (repo_path / "README.md").exists() or (repo_path / "README").exists():
        indicators.append("Documentation present (README found)")
    if indicators:
        for indicator in indicators:
            lines.append(f"- {indicator}")
    else:
        lines.append("- No standard project indicators detected")
    return "\n".join(lines)


def atx_available() -> bool:
    return shutil.which("atx") is not None


def transform_enabled() -> bool:
    return os.environ.get("TRANSFORM_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}


def transform_timeout_seconds() -> int:
    raw = os.environ.get("TRANSFORM_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return 21600
    try:
        value = int(raw)
        return value if value > 0 else 21600
    except Exception:
        return 21600


def get_transform_output_dir() -> str:
    raw = (os.environ.get("TRANSFORM_OUTPUT_DIR", "") or "").strip()
    return raw if raw else "Documentation"


def copy_transform_output(repo_path: Path, analysis_id: str, analysis_dir: Path) -> None:
    output_dir_name = get_transform_output_dir()
    source = repo_path / output_dir_name
    if not source.exists() or not source.is_dir():
        logger.info("Transform output dir not found, skipping copy: %s", source)
        return
    count = 0
    for f in source.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(source)
        storage_name = f"{output_dir_name}/{rel.as_posix()}"
        try:
            content_bytes = f.read_bytes()
            try:
                content_str = content_bytes.decode("utf-8")
                if s3_mod.s3_enabled():
                    ct = "text/markdown; charset=utf-8" if storage_name.lower().endswith(".md") else "text/plain; charset=utf-8"
                    s3_mod.s3_put_bytes(analysis_id, storage_name, content_bytes, content_type=ct)
                else:
                    dest = analysis_dir / output_dir_name / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content_str, encoding="utf-8")
            except UnicodeDecodeError:
                if s3_mod.s3_enabled():
                    s3_mod.s3_put_bytes(analysis_id, storage_name, content_bytes)
                else:
                    dest = analysis_dir / output_dir_name / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(content_bytes)
            count += 1
        except Exception as e:
            logger.warning("Failed to copy Transform output file %s: %s", f, e)
    logger.info("Copied %s Transform output files from %s", count, source)


def tail_last_lines(text: str, max_lines: int = 2000) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[-max_lines:])


def write_transform_failed_log(analysis_id: str, analysis_dir: Path, use_s3: bool, message: str) -> None:
    try:
        if use_s3:
            s3_mod.s3_put_plain_text(analysis_id, "transform_failed.log", message)
        else:
            (analysis_dir / "transform_failed.log").write_text(message, encoding="utf-8")
    except Exception as e:
        logger.warning("Failed to write transform_failed.log: %s", e)


def _handle_transform_signal(signum: int, frame: object) -> None:
    global _current_transform_run
    run = _current_transform_run
    if run is None:
        os._exit(1)
        return
    msg = f"Interrupted by signal {signum}\n"
    try:
        write_transform_failed_log(
            run["analysis_id"],
            run["analysis_dir"],
            run["use_s3"],
            msg,
        )
    except Exception:
        pass
    _current_transform_run = None
    os._exit(1)


def register_transform_signal_handlers() -> None:
    for name in ("SIGTERM", "SIGINT"):
        sig = getattr(signal, name, None)
        if sig is not None:
            try:
                signal.signal(sig, _handle_transform_signal)
            except (ValueError, OSError):
                pass


def run_transform_atx(repo_path: str, timeout_seconds: int) -> dict:
    resp: dict = {
        "ok": False,
        "exit_code": -1,
        "error_type": "exception",
        "output_tail": "",
        "log_path": "transform_failed.log",
        "transform_ran": True,
        "cmd": "",
    }
    if not atx_available():
        resp["error_type"] = "exception"
        resp["output_tail"] = "atx CLI not found on PATH"
        return resp

    env = os.environ.copy()
    env.setdefault("AWS_REGION", "us-east-1")

    def _coerce_text(v) -> str:
        if v is None:
            return ""
        if isinstance(v, bytes):
            try:
                return v.decode("utf-8", errors="replace")
            except Exception:
                return v.decode(errors="replace")
        return str(v)

    try:
        result = subprocess.run(
            [
                "atx",
                "custom",
                "def",
                "exec",
                "-n",
                "AWS/early-access-comprehensive-codebase-analysis",
                "-p",
                repo_path,
                "-x",
                "-t",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )
        stdout = _coerce_text(result.stdout)
        stderr = _coerce_text(result.stderr)
        combined = stdout + ("\n" if stdout and stderr else "") + stderr
        resp["exit_code"] = int(result.returncode)
        if result.returncode == 0:
            resp["ok"] = True
            resp["error_type"] = None
            resp["log_path"] = "transform.log"
            resp["output_tail"] = tail_last_lines(combined, 2000)
            return resp
        resp["error_type"] = "nonzero"
        resp["output_tail"] = tail_last_lines(combined, 2000)
        return resp
    except subprocess.TimeoutExpired as e:
        stdout = _coerce_text(getattr(e, "stdout", None))
        stderr = _coerce_text(getattr(e, "stderr", None))
        combined = stdout + ("\n" if stdout and stderr else "") + stderr
        resp["exit_code"] = -1
        resp["error_type"] = "timeout"
        resp["output_tail"] = tail_last_lines(combined, 2000)
        return resp
    except Exception as e:
        resp["exit_code"] = -1
        resp["error_type"] = "exception"
        resp["output_tail"] = tail_last_lines(str(e), 2000)
        return resp


def get_current_transform_run():
    return _current_transform_run


def set_current_transform_run(run: dict | None) -> None:
    global _current_transform_run
    _current_transform_run = run
