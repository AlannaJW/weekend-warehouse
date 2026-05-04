# Setup guide — BigQuery + dbt

One-time setup for running this project on the Google Cloud free tier.
Time required: about 15 minutes if it's your first time, 5 if you've done
it before.

---

## 1. Create a GCP project

1. Go to <https://console.cloud.google.com>.
2. Click the project dropdown at the top, then **New Project**.
3. Name it something like `weekend-warehouse`. Note the auto-generated
   **Project ID** (it'll look like `weekend-warehouse-123456`) — you'll
   need this for `profiles.yml`.
4. Make sure billing is enabled on the project. The BigQuery free tier is
   generous (1 TB queried per month, 10 GB storage), but BigQuery requires
   a billing account to be attached even when usage stays free. You will
   not be charged for this project at the volumes we're working with.

## 2. Enable the BigQuery API

1. In the search bar at the top of the console, type "BigQuery API".
2. Click **Enable**.

## 3. Create the raw and marts datasets

In the BigQuery console (search "BigQuery" in the top bar):

1. Click your project name on the left.
2. Click the three-dot menu → **Create dataset**.
3. Name it `raw`. Choose region `US` (must match what's in `profiles.yml`).
4. Click **Create dataset**.
5. Repeat for `marts`. Use the same region.
6. Repeat for `staging`. Same region.

(dbt will manage the contents of `staging` and `marts` going forward; you
just need the empty datasets to exist.)

## 4. Load the source CSVs into the `raw` dataset

Two options.

**Option A — BigQuery console (no install required, slow but visual):**

1. Open the `raw` dataset.
2. Click **Create table**.
3. Source: **Upload**, file: `data/raw/raw_orders.csv`, format: CSV.
4. Destination table: `raw_orders`.
5. Schema: **Auto detect** ✓.
6. Advanced options → **Skip leading rows: 1** (the header).
7. Click **Create table**.
8. Repeat for `raw_customers.csv`, `raw_tier_history.csv`, `raw_web_events.csv`.

**Option B — `bq` CLI (faster if you're loading more than once):**

```bash
# Install gcloud CLI if you haven't: https://cloud.google.com/sdk/docs/install
gcloud auth login
gcloud config set project YOUR-PROJECT-ID

bq load --autodetect --skip_leading_rows=1 \
   raw.raw_orders        data/raw/raw_orders.csv
bq load --autodetect --skip_leading_rows=1 \
   raw.raw_customers     data/raw/raw_customers.csv
bq load --autodetect --skip_leading_rows=1 \
   raw.raw_tier_history  data/raw/raw_tier_history.csv
bq load --autodetect --skip_leading_rows=1 \
   raw.raw_web_events    data/raw/raw_web_events.csv
```

After this you should see four tables under `raw/` in the BigQuery
console.

## 5. Create a service account for dbt

1. In the GCP console, go to **IAM & Admin → Service accounts**.
2. Click **Create service account**.
3. Name: `dbt-bigquery`. Click **Create and continue**.
4. Grant the role **BigQuery Admin** (this is broad but appropriate for a
   solo project; in a real team you'd scope it tighter).
5. Click **Done**.
6. On the service account list, click the new account, go to the **Keys**
   tab, click **Add key → Create new key → JSON**.
7. Save the downloaded JSON file somewhere outside this repo. Note the
   absolute path.

⚠️ **Never commit this JSON file.** The repo's `.gitignore` excludes
`*.json` to help. Treat it like a password.

## 6. Install dbt and configure profiles

```bash
# In a fresh virtualenv or globally — dbt + the BigQuery adapter
pip install dbt-bigquery

# Copy the example profiles config
mkdir -p ~/.dbt
cp dbt_project/profiles.yml.example ~/.dbt/profiles.yml

# Edit ~/.dbt/profiles.yml and replace:
#   - YOUR-GCP-PROJECT-ID with your project ID
#   - keyfile path with the absolute path to the JSON file from step 5
```

## 7. Verify the connection

```bash
cd dbt_project
dbt deps      # installs dbt_utils
dbt debug     # confirms the BigQuery connection works
```

If `dbt debug` ends with "All checks passed!" you're ready to build models.

---

## Troubleshooting

**"Permission denied" on BigQuery operations.**
Re-check that the service account has **BigQuery Admin** role on the
project. Roles propagate within a minute; if it still fails after a wait,
re-download the key.

**"Default project not set"**
In `profiles.yml`, the `project` field must match your GCP Project ID
*exactly*, including any auto-appended numbers.

**`dbt deps` complains about packages.yml.**
Make sure you're running it from inside `dbt_project/`, not from the repo
root.
