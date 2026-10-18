import pandas as pd
from datarescue import detect_issues, inject_failure, profile, repair_safely, run_pipeline


def sample():
    return pd.DataFrame({
        "InvoiceNo": ["536365", "536366", "536367"],
        "StockCode": ["85123A", "71053", "84406B"],
        "Description": ["item a", "item b", "item c"],
        "Quantity": [6, 2, 1],
        "InvoiceDate": ["2010-12-01", "2010-12-01", "2010-12-01"],
        "UnitPrice": [2.55, 3.39, 2.75],
        "CustomerID": [17850.0, 17850.0, 13047.0],
        "Country": ["United Kingdom"] * 3,
    })

def test_profile_counts_rows_and_columns():
    m = profile(sample())
    assert m["rows"] == 3
    assert m["columns"] == 8
    assert m["duplicate_rows"] == 0

def test_detects_schema_drift_as_invalid_numeric():
    broken = inject_failure(sample(), "Schema drift: Quantity becomes text")
    codes = {i.code for i in detect_issues(broken)}
    assert "invalid_numeric" in codes

def test_detects_missing_values():
    broken = inject_failure(sample(), "Missing required values")
    assert any(i.code == "null_values" and i.column == "CustomerID" for i in detect_issues(broken))

def test_detects_duplicate_rows():
    broken = inject_failure(sample(), "Duplicate records")
    assert any(i.code == "duplicate_rows" for i in detect_issues(broken))

def test_numeric_repair_quarantines_bad_value_as_null():
    broken = inject_failure(sample(), "Schema drift: Quantity becomes text")
    repaired, actions = repair_safely(broken, ["Parse numeric columns; quarantine unparseable values as null"])
    assert pd.api.types.is_numeric_dtype(repaired["Quantity"])
    assert repaired["Quantity"].isna().sum() == 1
    assert actions[0]["invalid_values_quarantined_as_null"] == 1

def test_duplicate_repair_removes_exact_duplicate():
    broken = inject_failure(sample(), "Duplicate records")
    repaired, actions = repair_safely(broken, ["Remove exact duplicate rows"])
    assert len(repaired) == 3
    assert actions[0]["rows_removed"] == 1

def test_pipeline_does_not_mutate_source():
    source = sample()
    original = source.copy(deep=True)
    run_pipeline(source, "Duplicate records", ["Remove exact duplicate rows"])
    pd.testing.assert_frame_equal(source, original)

def test_pipeline_reports_pass_when_selected_fixes_clear_demo_issues():
    result, out = run_pipeline(sample(), "Duplicate records", ["Remove exact duplicate rows"])
    assert result.status == "PASS"
    assert len(out) == 3
    assert result.issues_after == []
