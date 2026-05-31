# Review Collection P0 Baseline

## Current stable baseline

Amazon JP product:

`B0F1T7R51T`

Stable result from main-line collector:

- Background review pages: 3
- Page 1 visible reviews: 12
- Page 2 visible reviews: 23
- Page 3 visible reviews: 9
- Merged unique visible reviews: 32
- Duplicate reviews skipped: 12

## Important finding

The main-line collector can still collect 32 unique visible reviews.

The strict selector experiment is not suitable for main because it reduced the sample to 7 reviews.

## P0 decision

Do not change the Amazon review card selector or duplicate filter until a new approach proves it can preserve the 32-review baseline.

Next improvement should focus on multi-tab targeted sample expansion.
