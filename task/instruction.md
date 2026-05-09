The logistics finance team has an ETL job that loads vendor shipment ledger CSVs from data/vendor_exports/ and writes a normalized output to out/shipments_normalized.csv. After a recent vendor portal export change, the job still completes without crashing, but downstream reconciliation rejects many rows and per-vendor monthly totals no longer tie out.

The workspace contains the ETL project at /workspace/etl/ with a fixed entrypoint and CLI. Diagnose what the loader is doing wrong, fix it, and confirm that a clean rerun produces canonical normalized output.

Run command:

./bin/run-load --in data/vendor_exports/ --profiles data/vendor_profiles.yaml --out out/
Treat the vendor exports and profile metadata as production inputs. Do not modify them, tests, package metadata, helper scripts, or configuration files. The deliverable is out/shipments_normalized.csv.

You may repair parsing, schema mapping, value normalization, or output assembly however you prefer. The entrypoint name and CLI signature are fixed. Do not hardcode the final row set, fabricate data, or fill missing values with placeholders. The output must reflect the vendor exports after correct normalization.

The verifier reruns the documented command from a clean out/ directory and grades the resulting CSV against the canonical shape and per-vendor expected aggregates derived from the same source data.