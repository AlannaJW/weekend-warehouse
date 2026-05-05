# Decisions log

A running record of design decisions made during this build, with particular
attention to places where I overrode or modified Claude's first-pass
suggestion. The point is to make the *judgment* visible, not just the code.

Each entry follows the format:

> **Context** — what we were doing
> **AI suggested** — Claude's first-pass output or recommendation
> **I changed it to** — what I shipped
> **Why** — the reasoning

---

## #1 — Drop the `Faker` dependency entirely

**Context.** The synthetic data generator initially imported `Faker` for
realistic names and emails.

**AI suggested.** Adding `Faker>=24.0.0` to `requirements.txt` and using
`fake.unique.email()`, `fake.name()`, `fake.uri_path()`.

**I changed it to.** Removed Faker, replaced with a small inline list of
first names, last names, email domains, and URL segments. Now the generator
has zero external dependencies.

**Why.** Two reasons. (1) The data only needs to be plausible enough to
demonstrate the pipeline patterns; perfectly realistic names add nothing.
(2) A reviewer cloning the repo can run `python generate.py` immediately
without `pip install`. Lower friction for someone evaluating the project,
and one fewer thing that can break in CI.

---

## #2 — Output raw CSVs to `data/raw/`, not dbt's `seeds/`

**Context.** Choosing where the generated CSVs should live.

**AI suggested.** Default Python conventions — putting them next to the
generator, or in dbt's `seeds/` directory.

**I changed it to.** A separate `data/raw/` directory at the repo root,
loaded into BigQuery as proper raw tables.

**Why.** dbt's `seeds/` directory usually has small reference tables
(country codes, holiday calendars) that ship with the dbt project. Treating
30K-row event data as a "seed" would be confusing — they are better put in a `raw`
dataset in BigQuery, loaded and organized how a real source data would be.

---


## #3 — Add `stg_tier_history` instead of reading raw in `dim_customer`

**Context.** Building the staging layer.

**AI suggested.** Skipping `stg_tier_history` because the data is simple and feeds directly into `dim_customer`.

**I changed it to.** Adding `stg_tier_history` for consistency.

**Why.** dbt's layering convention is "one staging model per source, no exceptions, marts only read from staging." Skipping the trivial one introduces a special case that future readers (and future-me) would have to remember. The marginal cost of writing the model is five lines of SQL; the maintainability cost of skipping it compounds over time. Also enables tests on the staged data (uniqueness on `(crm_id, valid_from)` and accepted values on `tier`) that would have nowhere clean to live otherwise.

---

## #4 — Aggregation key for lifetime questions: natural key, not surrogate

**Context.** Building `agg_customer_lifetime` as a per-customer wide aggregate — one row per customer, summarizing lifetime orders, revenue, AOV, etc.

**AI suggested.** Aggregating `fct_orders` by `customer_key` (surrogate key), then LEFT JOINing to `dim_customer` filtered on `is_current = TRUE`.

**The bug.** SCD2 customers have multiple `customer_key` values across tier-history versions, and `fct_orders` rows correctly point to the version active at order time. Aggregating by `customer_key` and then filtering to `is_current = TRUE` silently dropped every order from non-current tier periods. The totals-match test caught a $638K gap between aggregate revenue and `fct_orders` revenue.

**The fix.** Aggregate by `COALESCE(crm_id, customer_key)` — the natural key when present (collapses all SCD2 versions of one customer into a single row), with surrogate-key fallback for guests (who have no natural key but only one version each).

**Why this matters.** SCD2's surrogate key is the correct join target for point-in-time questions ("what tier was the customer when they placed this order?") but the wrong key for lifetime aggregation ("how much has this customer spent across all of time?"). The two question types require different keys; mixing them silently produces wrong totals and no errors.

Fixing this surfaced a second issue; see #5.

---

## #5 — Email as conformed identity for cross-version aggregation

This entry is the second half of the debugging story that began in #4.

**Context.** While fixing entry #4, the totals-match test continued to flag a $559K gap. Investigation showed `fct_orders` had 3,270 rows with `NULL customer_key` because the synthetic data generator allowed orders to occur outside any SCD2 tier-period date range — a real-world data-quality scenario.

**The fix.** Aggregate `fct_orders` by `customer_email` rather than by surrogate or natural key, then join to `dim_customer WHERE is_current = TRUE` on email to enrich with current attributes. Email is the only identifier that's stable across SCD2 versions, present on every order regardless of whether the SCD2 join succeeded, and works uniformly for both real customers and guests.

**Why this matters.** Surrogate keys are correct for point-in-time joins but fragile for lifetime aggregation when the dimension has temporal coverage gaps. Email — once normalized at staging via `LOWER(TRIM(...))` — is a conformed identity that works across SCD2 boundaries, source mismatches, and date-range orphans. This is also why staging-layer email normalization is so important: it pays off in the aggregate layer.

**Acknowledged limitation.** The 3,270 orphan orders in `fct_orders` are a data-quality issue worth flagging in the README's "known limitations" section. A production fix would either constrain order timestamps in the generator or extend the earliest tier-period `valid_from` to cover all of a customer's order history.

---

## #6 — Stack: BigQuery + dbt + Looker Studio

**Context.** Picking the analytical stack at project start.

**Considered.** DuckDB (local, free, modern, but lower resume recognition); Snowflake (free 30-day trial, high recognition, slightly more setup overhead); BigQuery (generous free tier, native Looker Studio integration, broadly recognized).

**Chose.** BigQuery + dbt + Looker Studio.

**Why.** BigQuery's free tier covered the project's scale at zero cost. Looker Studio plugs in natively, simplifying the dashboard layer. The combination is one of the most common stacks at modern data teams, which makes it generalizable to interview discussion. DuckDB would have added a local-portability story at the cost of a less-recognized tool name. Snowflake would have added prestige with no marginal pedagogical value over BigQuery for this project's scope.

---
