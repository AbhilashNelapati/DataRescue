"""Core deterministic pipeline, quality checks, diagnosis and safe repairs."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import hashlib
import json
import pandas as pd

EXPECTED_COLUMNS = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]
NUMERIC_COLUMNS = ["Quantity", "UnitPrice", "CustomerID"]

@dataclass
class Issue:
    code: str
    severity: str
    column: str
    count: int
    message: str
    recommendation: str

@dataclass
class PipelineResult:
    status: str
    source_rows: int
    output_rows: int
    issues_before: list[dict[str, Any]]
    issues_after: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    metrics_before: dict[str, Any]
    metrics_after: dict[str, Any]
    source_sha256: str
    output_csv: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def profile(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()) if len(df.columns) else 0,
        "missing_cells": int(df.isna().sum().sum()),
        "missing_by_column": {str(k): int(v) for k, v in df.isna().sum().items()},
        "column_types": {str(k): str(v) for k, v in df.dtypes.items()},
    }


def detect_issues(df: pd.DataFrame) -> list[Issue]:
    issues: list[Issue] = []
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    for col in missing_cols:
        issues.append(Issue("missing_column", "critical", col, 1, f"Required column '{col}' is absent.", "Restore the column from the upstream source or map an explicitly equivalent column. Do not fabricate values."))
    for col in [c for c in EXPECTED_COLUMNS if c in df.columns]:
        n = int(df[col].isna().sum())
        if n:
            issues.append(Issue("null_values", "high" if col in ("InvoiceNo", "Quantity", "UnitPrice") else "medium", col, n, f"{n:,} null value(s) in '{col}'.", "Check source semantics; quarantine or explicitly handle missing values rather than blindly filling them."))
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            converted = pd.to_numeric(df[col], errors="coerce")
            bad = int((converted.isna() & df[col].notna()).sum())
            if bad:
                issues.append(Issue("invalid_numeric", "high", col, bad, f"{bad:,} non-null value(s) in '{col}' cannot be parsed as numeric.", "Convert valid numeric strings and quarantine unparseable rows for review."))
    dup = int(df.duplicated().sum()) if len(df.columns) else 0
    if dup:
        issues.append(Issue("duplicate_rows", "medium", "*", dup, f"{dup:,} exact duplicate row(s).", "Remove exact duplicates only after preserving an audit count; do not deduplicate by invoice alone."))
    if "Quantity" in df.columns:
        q = pd.to_numeric(df["Quantity"], errors="coerce")
        n = int((q < 0).sum())
        if n:
            issues.append(Issue("negative_quantity", "info", "Quantity", n, f"{n:,} negative quantity value(s).", "In Online Retail, negative quantities can represent returns/cancellations; investigate rather than automatically deleting."))
    if "UnitPrice" in df.columns:
        p = pd.to_numeric(df["UnitPrice"], errors="coerce")
        n = int((p < 0).sum())
        if n:
            issues.append(Issue("negative_price", "high", "UnitPrice", n, f"{n:,} negative price value(s).", "Quarantine for business review; negative prices may be special adjustments."))
    return issues


def inject_failure(df: pd.DataFrame, scenario: str) -> pd.DataFrame:
    """Return a modified copy for demo/testing; never mutate original input."""
    out = df.copy(deep=True)
    if scenario == "Schema drift: Quantity becomes text":
        if "Quantity" not in out: raise ValueError("Dataset has no Quantity column")
        out["Quantity"] = out["Quantity"].astype("object")
        if len(out): out.iloc[0, out.columns.get_loc("Quantity")] = "NOT_A_NUMBER"
    elif scenario == "Missing required values":
        if "CustomerID" not in out: raise ValueError("Dataset has no CustomerID column")
        if len(out): out.loc[out.index[:max(1, len(out)//100)], "CustomerID"] = pd.NA
    elif scenario == "Duplicate records":
        if len(out): out = pd.concat([out, out.iloc[[0]].copy()], ignore_index=True)
    elif scenario == "No injected failure":
        pass
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
    return out


def _json_issue(issue: Issue) -> dict[str, Any]:
    return asdict(issue)


def repair_safely(df: pd.DataFrame, selected_repairs: list[str]) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Apply only explicitly selected, reversible demo repairs on a copy."""
    out = df.copy(deep=True)
    actions: list[dict[str, Any]] = []
    if "Parse numeric columns; quarantine unparseable values as null" in selected_repairs:
        for col in NUMERIC_COLUMNS:
            if col in out.columns:
                before = int((pd.to_numeric(out[col], errors="coerce").isna() & out[col].notna()).sum())
                if before:
                    out[col] = pd.to_numeric(out[col], errors="coerce")
                    actions.append({"action": "parse_numeric", "column": col, "invalid_values_quarantined_as_null": before, "status": "applied"})
    if "Remove exact duplicate rows" in selected_repairs:
        before = len(out)
        out = out.drop_duplicates().copy()
        removed = before - len(out)
        actions.append({"action": "drop_exact_duplicates", "rows_removed": int(removed), "status": "applied"})
    if "Quarantine rows missing critical fields" in selected_repairs:
        critical = [c for c in ["InvoiceNo", "Quantity", "UnitPrice"] if c in out.columns]
        before = len(out)
        out = out.dropna(subset=critical).copy() if critical else out
        actions.append({"action": "quarantine_missing_critical", "rows_removed": int(before-len(out)), "columns_checked": critical, "status": "applied"})
    return out, actions


def run_pipeline(source: pd.DataFrame, scenario: str, selected_repairs: list[str]) -> tuple[PipelineResult, pd.DataFrame]:
    if source.empty:
        raise ValueError("The uploaded dataset is empty.")
    raw_bytes = source.to_csv(index=False).encode("utf-8")
    staged = inject_failure(source, scenario)
    issues_before = [_json_issue(i) for i in detect_issues(staged)]
    before_metrics = profile(staged)
    repaired, actions = repair_safely(staged, selected_repairs)
    issues_after = [_json_issue(i) for i in detect_issues(repaired)]
    after_metrics = profile(repaired)
    unresolved_critical = any(i["severity"] == "critical" for i in issues_after)
    status = "PASS" if not issues_after else ("NEEDS REVIEW" if not unresolved_critical else "BLOCKED")
    csv = repaired.to_csv(index=False)
    result = PipelineResult(status, len(source), len(repaired), issues_before, issues_after, actions, before_metrics, after_metrics, sha256_bytes(raw_bytes), csv)
    return result, repaired


def result_json(result: PipelineResult) -> str:
    return json.dumps(asdict(result), indent=2, default=str)
