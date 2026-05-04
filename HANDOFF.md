# Handoff notes

This file captures context that lives in chat history rather than in the
codebase, so a fresh AI session (or a future me) can pick up the project
without re-deriving decisions.

If you're an AI session reading this, start by also reading: `README.md`,
`DECISIONS.md`, `prompts/01-scoping.md`, and `prompts/02-data-generator.md`.

---

## Where we are right now

**Done:**
- Synthetic data generator written, verified, producing 4 CSVs with the
  expected quirks (`data_generator/generate.py`).
- Repo scaffolding: `README.md`, `DECISIONS.md`, `.gitignore`,
  `prompts/` with the scoping and data-generator prompts logged.
- dbt project skeleton: `dbt_project/dbt_project.yml`,
  `dbt_project/profiles.yml.example`, `dbt_project/packages.yml`.
- BigQuery setup guide: `docs/setup.md`.

**Not yet done:**
- BigQuery + GCP setup (manual, per `docs/setup.md`).
- `dbt deps` and `dbt debug` to confirm connection.
- Staging models (3): `stg_orders`, `stg_customers`, `stg_web_events`.
- Marts: `dim_customer` (SCD2), `dim_date`, `fct_orders`.
- Tests + `agg_revenue_daily`.
- Looker Studio dashboard.
- Architecture diagram saved to `docs/architecture.svg`.
- Final README pass + LinkedIn-ready writeup paragraph.

The original task list (still useful as a checklist):

1. ~~Scaffold repo and write synthetic data generator~~ ✓
2. ~~Write README skeleton with AI-workflow framing~~ ✓
3. **Set up BigQuery + dbt connection** ← here
4. Build staging models
5. Build core marts: fct_orders, dim_customer (SCD2), dim_date
6. Add tests and aggregation table
7. Build Looker Studio dashboard
8. Generate architecture diagram and finalize docs

---

## Decisions made in chat that aren't in the codebase yet

### Data sizing — bump just before BigQuery upload

The current generator produces ~42K rows total (2K customers, 8K orders,
30K events, 2.4K tier rows). That's plenty for demonstrating patterns but
small enough that a recruiter glance might undervalue it. Plan: **right
before uploading to BigQuery, bump `N_ORDERS` to 500K and `N_EVENTS` to
2M**, regenerate the CSVs, then upload. The script handles it; the change
is one block in `data_generator/generate.py`.

Why we delayed it: smaller data = faster local iteration while we build
and test models. Once we know everything works, bumping size costs nothing.

### Stack pinned: BigQuery + dbt + Looker Studio

We considered DuckDB and Snowflake. BigQuery won because:
- Free tier is sufficient for the project.
- Higher resume recognition than DuckDB.
- Looker Studio plugs in natively, simplifying the dashboard step.
- DECISIONS.md doesn't have an entry for this — worth adding one.

### Identity resolution strategy

Customers across sources (`raw_customers`, `raw_orders`, `raw_web_events`)
share only email, and emails are case-jittered. The plan:
1. Normalize email to `LOWER(TRIM(email))` in every staging model.
2. In `dim_customer`, use the CRM as authoritative — guest checkouts
   (orders with emails not in CRM) get attributed to a synthetic
   "guest_<email>" customer key.
3. Web events stitch to customers via normalized email when present;
   anonymous-only events stay unattributed in fact tables.

### SCD2 approach

Build `dim_customer` from a snapshot of `raw_customers` joined to a derived
view of `raw_tier_history` that adds `valid_to` (the next row's
`valid_from`, or `9999-12-31` for the latest) and `is_current` (boolean).
The CRM-side attributes (region, acquisition_channel) don't change in our
data, so SCD2 only really needs to track `tier`. Document that in the
model header — it's a deliberate simplification.

### Filtering policy in staging

`stg_orders` filters `status = 'test'` rows entirely. Refunded rows are
*kept* (with negative amounts) so net revenue calculations work, but they
should be excluded by tests like row-count uniqueness on order_id.

### Test priorities

When we build tests, prioritize in this order (if time runs short):
1. `unique` and `not_null` on every primary key.
2. `relationships` from `fct_orders.customer_sk` to `dim_customer.customer_sk`.
3. `accepted_values` on `status`, `tier`, `channel` columns.
4. `dbt_utils.unique_combination_of_columns` on `(customer_sk, valid_from)`
   in `dim_customer`.
5. Custom test: every order's `net_amount = gross_amount - discount_amount`
   (within a small float tolerance).

### Dashboard charts (if you get there)

Three charts is enough. Suggested:
1. Daily net revenue, last 90 days, line chart.
2. Net revenue by acquisition channel, current vs. previous quarter, bar.
3. Customer count by tier (current snapshot), stacked bar by region.

---

## Recommended first prompt for Claude Code

Once you're in Claude Code with the project open:

> Read `HANDOFF.md`, `README.md`, `DECISIONS.md`, `prompts/01-scoping.md`,
> and `prompts/02-data-generator.md`. Walk me through the project state
> in 10 lines or less, then ask me one clarifying question before we start
> on the next task (BigQuery setup).

This forces a context check before any new work, which is good practice
and also gives you a chance to correct any misreading before code is
written.

---

## What to update as you go

- `DECISIONS.md` — every time you push back on an AI suggestion.
  Aim for ~6 total entries by the end.
- `prompts/0N-*.md` — one file per major build stage. Keep them short
  (the prompts you actually used + a note on what worked / didn't).
- `README.md` project-status checklist — tick items off as you finish.

---

## Things easy to get wrong

- **Service-account JSON in the repo.** `.gitignore` excludes `*.json`,
  but double-check before your first push. If it slips in, rotate the
  key in GCP immediately.
- **Mixing dataset locations.** The `raw`, `staging`, and `marts`
  datasets must all be in the same BigQuery region (US). Cross-region
  joins fail loudly.
- **`dbt seeds/` confusion.** Do NOT put the generated CSVs there. They
  go in `data/raw/` and get loaded via `bq load` per `docs/setup.md`.
- **Schema name collisions.** `dbt_project.yml` sets `staging` and
  `marts` as the schemas. Make sure your BigQuery datasets match these
  names exactly, or change `dbt_project.yml` to whatever you named them.

---

## Time budget remaining

Original plan was ~10 hours total. So far we've spent maybe 1.5 hours on
scoping + scaffolding + data generator + docs. Realistic remaining budget:

- BigQuery setup: 30 min
- Staging models: 1 hour
- Marts (incl. SCD2): 2 hours
- Tests + aggregate: 1 hour
- Dashboard: 1.5 hours
- Diagram + final polish: 1 hour
- Buffer: 1.5 hours

If you hit hour 9 with the dashboard not yet built, drop the dashboard
and write a "what I'd build next" section in the README instead. The
core dbt project + tests + docs is the resume-grade artifact; the
dashboard is the cherry on top.
