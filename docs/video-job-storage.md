# Video Job Storage

Video generation jobs use a small storage abstraction in `video_generation/job_store.py`.

## Default Mode

The default runtime mode is in-memory:

```text
VIDEO_JOB_STORE=memory
```

This is suitable for the public demo and local development. Jobs may reset when the service restarts, redeploys, or runs across multiple workers.

## File Mode

File-backed storage can be enabled without changing public API paths:

```text
VIDEO_JOB_STORE=file
VIDEO_JOB_STORE_PATH=/var/data/video_jobs.json
```

The file store:

- Creates parent directories when needed.
- Handles missing, empty, or corrupt JSON by starting from an empty store instead of crashing.
- Writes a simple inspectable JSON shape with a top-level `jobs` object.
- Uses a temporary file plus replace operation for safer writes.
- Does not store API keys or provider secrets.

## Render Persistent Disk

Render persistence requires mounting a persistent disk to the directory used by `VIDEO_JOB_STORE_PATH`.

Recommended Render-style settings when persistence is desired:

```text
VIDEO_JOB_STORE=file
VIDEO_JOB_STORE_PATH=/var/data/video_jobs.json
```

Mount the persistent disk at `/var/data` or adjust `VIDEO_JOB_STORE_PATH` to match the mounted path.

If no persistent disk is mounted, file mode still works only for the current ephemeral runtime and should not be treated as durable.

## Storage Diagnostics

The app exposes a safe public diagnostic endpoint:

```text
GET /api/v1/video-generation/storage/status
```

It reports:

- `storage_mode`: `memory` or `file`
- Whether file or memory storage is active
- Whether `VIDEO_JOB_STORE_PATH` is configured
- Whether the file-store parent directory exists and appears writable
- Whether restart persistence is currently verified
- A redacted `safe_path_hint`

It does not expose secrets or full sensitive filesystem paths.

## Operator Checklist

### Demo / Default

- Keep `VIDEO_JOB_STORE` unset or set to `memory`.
- Expect jobs to reset on restart, redeploy, or multi-worker routing.
- Verify:

```text
GET /api/v1/video-generation/storage/status
```

Expected default:

```text
storage_mode=memory
restart_persistence_enabled=false
```

### File Mode

1. Configure Render persistent disk manually.
2. Mount the disk to the directory you intend to use, for example `/var/data`.
3. Set environment variables:

```text
VIDEO_JOB_STORE=file
VIDEO_JOB_STORE_PATH=/var/data/video_jobs.json
```

4. Redeploy.
5. Verify:

```text
GET /api/v1/video-generation/storage/status
```

Expected file-mode readiness:

```text
storage_mode=file
path_configured=true
path_parent_exists=true
path_writable=true
restart_persistence_enabled=true
```

6. Create a video job.
7. Restart or redeploy the service.
8. Verify the job still exists through `GET /api/v1/video-generation/jobs`.

Do not claim durable persistence is working until the persistent disk is actually mounted and a restart/redeploy survival check passes.

## Future Production Store

For production-grade multi-worker or provider polling workflows, plan a database-backed store such as Postgres or Redis. The current public API shape does not need to change for that migration.
