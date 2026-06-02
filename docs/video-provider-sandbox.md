# Video Provider Sandbox

The video provider sandbox is a disabled-by-default contract for future Runway/Pika style integrations.

## Default

```text
VIDEO_PROVIDER_EXTERNAL_CALLS_ENABLED=false
```

When the flag is absent or false:

- Provider submit/poll remains simulated.
- `can_call_external_api=false`.
- `external_api_called=false`.
- No real provider HTTP request is made.

## Keys

Planned provider keys:

```text
RUNWAY_API_KEY
PIKA_API_KEY
```

The API key values are never returned in API responses, job payloads, logs, or readiness metadata. Readiness only reports whether a key is configured.

## Sandbox Modes

- `simulated`: default mode; no external provider calls.
- `blocked_missing_api_key`: feature flag is enabled, but the provider key is absent.
- `sandbox_ready_no_external_call`: feature flag and key are present, but no real provider adapter is enabled yet.
- `manual_or_prompt_export`: manual/prompt export provider; no API key or external call is needed.

## Fake Provider Clients

`video_generation/provider_clients.py` contains fake Runway/Pika clients for adapter contract tests. They return stable normalized shapes, fake provider job IDs, and simulated statuses without using network calls or API keys.

These clients do not replace the public provider submit/poll runtime. They are a tests-first scaffold for future request mapping, polling, timeout, retry, and result-normalization work.

## Future Work

Real provider integration still requires provider-specific request mapping, an HTTP client, timeout/retry policy, polling, error normalization, and result URL normalization. Until that work is implemented, manual export and simulated polling remain the source of truth.
