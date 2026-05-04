# Prompts log

This directory contains the actual prompts used during the build, in roughly
the order they were issued. They're imperfect on purpose — these are the
real prompts I sent, not retrofitted ones. If you're reviewing this repo,
the prompts give you a sense of how the project was scoped and where AI
was directed vs. given latitude.

Numbering is rough, since some steps involved several back-and-forth turns
that aren't all worth preserving.

| File | Stage |
| --- | --- |
| `01-scoping.md` | Project shape, source systems, modeling decisions |
| `02-data-generator.md` | Generating the synthetic data with deliberate quirks |
| `03-staging-models.md` | First-pass staging models (TODO) |
| `04-scd2-customer.md` | Building `dim_customer` with SCD2 (TODO) |
| `05-tests-and-aggregates.md` | Test suite + `agg_revenue_daily` (TODO) |
| `06-dashboard.md` | Looker Studio chart specifications (TODO) |
