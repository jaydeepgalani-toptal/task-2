# Vendor Shipment Ledger Recovery

This task gives the agent a small Python ETL project in `/workspace/etl` with a fixed CLI entrypoint, realistic CSV exports, and profile metadata. The job is to repair the loader so `./bin/run-load --in data/vendor_exports/ --profiles data/vendor_profiles.yaml --out out/` emits a correct canonical `out/shipments_normalized.csv`. The difficulty is in recovering the intended semantics from messy vendor exports rather than writing a CSV transformer from scratch.

The initial implementation is deliberately wrong in `src/loader/pipeline.py`. It uses a mostly positional interpretation of rows, only a tiny alias map for headers, picks the first date-looking value instead of the profile’s `business_date_field`, searches for a literal `amount` column before falling back to the first numeric-looking cell, parses money with `float(...)` and converts failures to `0.0`, lowercases statuses instead of applying the per-vendor `status_map`, and silently drops rows whose width differs from the first data row. The exported files also contain comment lines, blank rows, `# end of report` markers, and trailing summary rows, so a loader that only “mostly” filters noise still produces bad output.

The data is generated at build time by `task/environment/payload/etl_support/generate_inputs.py`. There are 6 vendors, 10 files each, and 50 valid shipment rows per file for 3000 valid rows total. Each vendor has a different schema style, header order, alias drift, date mix, and amount formatting. The seeded corpus includes the required traps from the spec: non-ISO business dates, DD-MM-YYYY rows with day values above 12, multiple date columns per record so using the wrong one changes monthly aggregates, and 12 valid negative correction rows that must survive as `cancelled`.

The verifier in `task/tests/test_outputs.py` does not inspect the agent’s code. It reruns the fixed CLI from a clean `out/` directory twice, validates the exact header and row count, checks that every date is valid ISO and every status/vendor id is canonical, compares per-vendor monthly counts and totals against oracle-derived aggregates from `/opt/etl_support/expected_aggregates.json`, verifies exactly 12 negative `cancelled` rows, confirms determinism after sorting by `(vendor_id, shipment_id)`, and checks a build-time SHA256 manifest for the protected inputs (`data/vendor_exports/*.csv`, `data/vendor_profiles.yaml`, `bin/run-load`, `pyproject.toml`, `uv.lock`).

Expected solution path:

- Inspect `data/vendor_profiles.yaml` and a few vendor CSVs to see how header aliases, field order, and incidental columns drift between files.
- Replace positional field selection with header-based lookup driven by the profile’s `business_date_field`, `amount_field`, and `status_map`.
- Normalize all amount and date formats robustly, filter noise rows consistently, and keep the negative correction rows.
- Write deterministic canonical output with header `shipment_id,vendor_id,business_date,status,amount_usd`.
