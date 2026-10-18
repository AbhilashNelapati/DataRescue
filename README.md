# DataRescue — Self-Healing Data Pipeline

**Tagline:** Detect. Diagnose. Repair safely. Verify with evidence.

DataRescue is a Streamlit prototype that profiles a dataset, injects reproducible failure scenarios, diagnoses data-quality issues, applies explicitly selected repairs to a working copy, re-runs checks, and exports an audit report. It uses the public **UCI Online Retail** dataset by default.

> Status: implementation starter. Run the tests and launch locally before claiming the app is verified in your environment. The dashboard uses deterministic, explainable checks; it does not require an LLM. If the buildathon requires OmniRush for all generative AI work, use OmniRush for any permitted agent orchestration and do not add a prohibited external model.

## Dataset

- Name: Online Retail
- Publisher: UCI Machine Learning Repository
- DOI: https://doi.org/10.24432/C5BW33
- Dataset page: https://archive.ics.uci.edu/dataset/352/online+retail
- Published dataset size: 541,909 rows and 6 original features; actual loader schema may combine features and targets.
- License: CC BY 4.0. Credit the UCI Machine Learning Repository and dataset creator Daqing Chen in demos and derivative materials.
- Download is attempted via `ucimlrepo` on first launch and cached as `data/online_retail.csv`. Internet access is needed for the first download. Alternatively download from UCI and upload the CSV through the app.

## Features

- CSV upload and public dataset mode
- Baseline profiling: rows, columns, dtypes, null counts, exact duplicate rows
- Failure injection: numeric column schema drift, missing values, duplicate rows
- Explainable diagnosis rules for missing required columns, nulls, invalid numeric values, duplicates, negative quantities and negative prices
- Explicit, opt-in repairs: parse numeric columns (invalid values become null), remove exact duplicate rows, quarantine rows missing critical fields
- Post-repair validation and unresolved issue list
- Downloads: repaired CSV, JSON audit, Markdown report
- Tests for detectors, repairs and source immutability

## Quick start (Python 3.11 recommended)

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
pytest -q
streamlit run app.py
```

Open the local URL printed by Streamlit, typically http://localhost:8501.

## Docker

```bash
docker compose up --build
```

Then open http://localhost:8501. Dataset cache is stored in `./data`.

## Demo script (3–5 minutes)

1. Launch the app and load the UCI Online Retail dataset.
2. Select **Schema drift: Quantity becomes text**.
3. Select **Parse numeric columns; quarantine unparseable values as null** and run.
4. Show the issue before repair, the action log, the remaining null-value warning, and the downloaded JSON report. Explain that the bad token is not silently guessed; it is converted to null and flagged for review.
5. Run **Duplicate records** with **Remove exact duplicate rows**. Show row count dropping by one and the duplicate check passing.
6. Run **Missing required values** without a repair, then with a repair if desired. Explain that customer ID is not treated as a critical field by the default repair policy because missing customer IDs may be valid in the source dataset.
7. Download the repaired CSV and audit report. Point out the source hash and explicit actions.

## Architecture

```text
Public UCI dataset / uploaded CSV
            |
            v
      Input adapter
            |
            v
  Baseline profiler + hash
            |
            v
 Failure injection (demo) -> Rule-based diagnosis
                                  |
                                  v
                         Explicit repair policy
                                  |
                                  v
                      Isolated working dataframe
                                  |
                                  v
                     Re-profile + quality checks
                                  |
                                  v
                  Streamlit dashboard + audit exports
```

## Safety and known limitations

- No production source is modified; repairs act on a copied dataframe.
- No arbitrary generated Python is executed. Repairs are predefined functions selected by the user.
- A `PASS` means the implemented checks found no remaining issues; it is not a guarantee of business correctness.
- Exact duplicate removal is only safe when the business meaning of a duplicate is understood.
- Negative quantities can represent returns/cancellations in this dataset; they are informational, not auto-deleted.
- A missing required column is a structural blocker. This starter does not fabricate missing columns.
- The source SHA-256 currently hashes a canonical CSV serialization of the loaded source dataframe, not the original download bytes.
- The demo failure injector alters the loaded working copy in memory; it does not change the cached source file.
- This is a local prototype, not a scheduler, distributed orchestrator, or production-grade recovery service.

## Test suite

Run `pytest -q`. Tests cover baseline profiling, schema drift, nulls, duplicates, safe numeric conversion, duplicate removal, source immutability and successful recovery. Do not claim the tests passed until you run them in your own environment or CI.

## Suggested next steps for a competition submission

1. Record an actual clean Docker build and test run in your submission evidence.
2. Add a pipeline dependency graph and stage-level execution logs.
3. Add deterministic benchmark scenarios with expected failure labels and calculate detection precision/recall.
4. Add repair approval and rollback records; do not let an LLM execute arbitrary shell or SQL.
5. Integrate OmniRush only through its official, permitted interface. Document agent sessions, prompts, tool calls and artifacts as the event requires.
6. Verify the current buildathon rules and allowed tools directly before submission; this repository does not claim compliance with unreviewed rules.

## Attribution

Online Retail dataset: Chen, D. (2015). *Online Retail*. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33. Licensed under CC BY 4.0.
