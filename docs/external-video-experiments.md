# External Video Experiments

Status: manual tracking scaffold.

CrossGrowth can record manual experiments from external video tools such as Gemini, Doubao, Runway, Pika, Kling, Luma, or a manual workflow. CrossGrowth does not call these external APIs in this tracker.

## What Gets Recorded

Each video job can store `external_video_experiments` with:

- tool name
- prompt type
- result URL
- preview URL
- prompt used
- estimated and actual cost notes
- product consistency score
- storyboard following score
- visual quality score
- ad readiness score
- overall score
- notes and failure reason

Scores use a 1-5 scale when provided.

## Boundaries

- This is manual experiment tracking only.
- `external_api_called=false`.
- `cost_incurred_by_crossgrowth=false`.
- Saving an experiment does not change the video job status.
- Manual result handoff remains available separately.
- Real provider API integration still requires pricing review, free-tier/API availability review, API key handling, explicit approval, and separate tests.

## Suggested Evaluation

Use the tracker to compare:

- product consistency
- storyboard following
- visual quality
- ad readiness
- cost and retry behavior
- whether the result is worth paying for at larger volume

The goal is to decide whether a real API integration is worth building before spending on provider calls.
