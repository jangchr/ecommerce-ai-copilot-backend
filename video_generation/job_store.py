"""Lightweight storage backends for video generation jobs."""

from __future__ import annotations

import json
import os
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
