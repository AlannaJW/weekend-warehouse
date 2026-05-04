# 02 — Synthetic data generator

The goal: produce CSVs from three "source systems" with enough real-world
quirks that the staging and modeling layers downstream have something to
actually do.

---

## Initial direction

I told Claude to write a Python generator that produces:

- `raw_orders.csv` — e-commerce orders, identified only by email
- `raw_customers.csv` — CRM customer records
- `raw_tier_history.csv` — CRM tier change log (so SCD2 has something to chew on)
- `raw_web_events.csv` — clickstream with anonymous + identified events

with deliberate messiness: inconsistent email casing across sources, ~10%
guest checkouts whose emails don't appear in the CRM, ~30% of customers
having a tier upgrade, anonymous-to-identified stitching in web events,
and a small number of test/refund rows that should be filtered in staging.

## What Claude got right on the first pass

- Schema choices for each source (column names, types, foreign-keyless joins by email).
- Reasonable parameter defaults (2K customers, 8K orders, 30K events).
- Reproducibility via a fixed `random.seed`.
- Putting the case-jittering in a single helper so quirks were applied consistently.

## What I overrode

1. **Removed Faker entirely** (logged in DECISIONS.md #1). The first version
   imported Faker, which (a) added a dependency for no real benefit and
   (b) broke when run in environments without internet access to PyPI.
   Replaced with a built-in name list.

2. **CSV output location**. Claude initially defaulted to dbt's `seeds/`
   folder; I moved it to `data/raw/` so we'd load the data into a real
   BigQuery `raw` dataset, the way actual source data would arrive.
   Logged in DECISIONS.md #2.

3. **Stratified the status quirks instead of layering them.** Claude's
   first draft had separate independent random rolls for "is test?" and
   "is refund?", which let a single row be both. I made them mutually
   exclusive via a single `r = random.random()` check.

## What I'd improve next iteration

- The "anonymous-to-identified stitching" is currently random rather than
  time-ordered. A more realistic generator would emit anonymous events
  *before* identified events under the same `anonymous_id`. For our
  purposes (demonstrating the join, not solving real attribution) it's
  fine, but worth flagging.
