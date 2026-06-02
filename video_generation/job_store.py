"""Lightweight storage backends for video generation jobs."""

from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any


class VideoJobStore:
    mode = "base"

    def create(self, job: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def get(self, job_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def update(self, job_id: str, job: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class InMemoryVideoJobStore(VideoJobStore):
    mode = "memory"

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}

    def create(self, job: dict[str, Any]) -> dict[str, Any]:
        job_id = str(job.get("job_id") or "")
        if not job_id:
            raise ValueError("job_id is required")
        self._jobs[job_id] = deepcopy(job)
        return deepcopy(self._jobs[job_id])

    def get(self, job_id: str) -> dict[str, Any] | None:
        job = self._jobs.get(str(job_id or ""))
        return deepcopy(job) if job is not None else None

    def update(self, job_id: str, job: dict[str, Any]) -> dict[str, Any]:
        safe_job_id = str(job_id or "")
        if not safe_job_id:
            raise ValueError("job_id is required")
        self._jobs[safe_job_id] = deepcopy(job)
        return deepcopy(self._jobs[safe_job_id])

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, int(limit or 20))
        jobs = sorted(
            self._jobs.values(),
            key=lambda item: str(item.get("created_at") or ""),
            reverse=True,
        )
        return deepcopy(jobs[:safe_limit])

    def clear(self) -> None:
        self._jobs.clear()


class FileVideoJobStore(VideoJobStore):
    mode = "file"

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read_jobs(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        jobs = payload.get("jobs") if isinstance(payload, dict) else payload
        if not isinstance(jobs, dict):
            return {}
        return {str(job_id): dict(job) for job_id, job in jobs.items() if isinstance(job, dict)}

    def _write_jobs(self, jobs: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"jobs": jobs}, ensure_ascii=False, indent=2, sort_keys=True)
        temp_path = self.path.with_name(f"{self.path.name}.tmp")
        temp_path.write_text(payload, encoding="utf-8")
        os.replace(temp_path, self.path)

    def create(self, job: dict[str, Any]) -> dict[str, Any]:
        job_id = str(job.get("job_id") or "")
        if not job_id:
            raise ValueError("job_id is required")
        jobs = self._read_jobs()
        jobs[job_id] = deepcopy(job)
        self._write_jobs(jobs)
        return deepcopy(jobs[job_id])

    def get(self, job_id: str) -> dict[str, Any] | None:
        job = self._read_jobs().get(str(job_id or ""))
        return deepcopy(job) if job is not None else None

    def update(self, job_id: str, job: dict[str, Any]) -> dict[str, Any]:
        safe_job_id = str(job_id or "")
        if not safe_job_id:
            raise ValueError("job_id is required")
        jobs = self._read_jobs()
        jobs[safe_job_id] = deepcopy(job)
        self._write_jobs(jobs)
        return deepcopy(jobs[safe_job_id])

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        safe_limit = max(1, int(limit or 20))
        jobs = sorted(
            self._read_jobs().values(),
            key=lambda item: str(item.get("created_at") or ""),
            reverse=True,
        )
        return deepcopy(jobs[:safe_limit])

    def clear(self) -> None:
        self._write_jobs({})


def get_video_job_store() -> VideoJobStore:
    mode = str(os.getenv("VIDEO_JOB_STORE") or "memory").strip().lower()
    if mode == "file":
        return FileVideoJobStore(os.getenv("VIDEO_JOB_STORE_PATH") or ".data/video_jobs.json")
    return InMemoryVideoJobStore()


def _safe_path_hint(path: str | os.PathLike[str] | None) -> str:
    if not path:
        return ""
    candidate = Path(path)
    name = candidate.name
    parent_name = candidate.parent.name
    if parent_name:
        return f".../{parent_name}/{name}"
    return name


def _path_parent_writable(parent: Path) -> bool:
    if not parent.exists() or not parent.is_dir():
        return False
    try:
        with tempfile.NamedTemporaryFile(prefix=".video_job_store_check_", dir=parent, delete=True):
            return True
    except OSError:
        return False


def video_job_storage_diagnostics(
    store: VideoJobStore | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    env_source = env if env is not None else os.environ
    active_store = store if store is not None else get_video_job_store()
    storage_mode = str(getattr(active_store, "mode", "") or "memory")
    is_file_store = storage_mode == "file"
    is_memory_store = storage_mode == "memory"
    configured_mode = str(env_source.get("VIDEO_JOB_STORE") or "memory").strip().lower()
    path_value = str(env_source.get("VIDEO_JOB_STORE_PATH") or "").strip()
    store_path = getattr(active_store, "path", None)
    effective_path = Path(store_path) if store_path is not None else (Path(path_value) if path_value else None)
    path_parent = effective_path.parent if effective_path is not None else None
    path_parent_exists = bool(path_parent and path_parent.exists() and path_parent.is_dir())
    path_writable = bool(path_parent and _path_parent_writable(path_parent))
    path_configured = bool(path_value)
    file_store_configured = is_file_store or configured_mode == "file"
    restart_persistence_enabled = bool(is_file_store and path_configured and path_parent_exists and path_writable)

    warnings: list[str] = []
    if is_memory_store:
        warnings.append("Video jobs use in-memory storage and reset on restart, deploy, or multi-worker routing.")
    if file_store_configured and not path_configured:
        warnings.append("VIDEO_JOB_STORE=file is active or requested, but VIDEO_JOB_STORE_PATH is not explicitly configured.")
    if is_file_store and not path_parent_exists:
        warnings.append("File store parent directory does not exist.")
    if is_file_store and path_parent_exists and not path_writable:
        warnings.append("File store parent directory is not writable.")
    if is_file_store and not restart_persistence_enabled:
        warnings.append("File mode is active, but durable restart persistence is not verified.")
    if restart_persistence_enabled:
        warnings.append("File store path appears writable; restart survival still requires a mounted persistent disk.")

    return {
        "storage_mode": storage_mode,
        "configured_mode": configured_mode,
        "is_file_store": is_file_store,
        "is_memory_store": is_memory_store,
        "file_store_configured": file_store_configured,
        "persistent_storage_required_for_restart_survival": True,
        "restart_persistence_enabled": restart_persistence_enabled,
        "path_configured": path_configured,
        "path_parent_exists": path_parent_exists,
        "path_writable": path_writable,
        "safe_path_hint": _safe_path_hint(effective_path),
        "warnings": warnings,
    }
