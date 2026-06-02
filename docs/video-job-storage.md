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

## Future Production Store

For production-grade multi-worker or provider polling workflows, plan a database-backed store such as Postgres or Redis. The current public API shape does not need to change for that migration.
