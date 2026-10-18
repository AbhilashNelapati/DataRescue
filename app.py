from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from datarescue import detect_issues, profile, run_pipeline, result_json
from dataset import load_public_dataset, DATASET_URL

st.set_page_config(page_title="DataRescue | Self-healing data pipelines", page_icon="🛟", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.7rem;max-width:1450px}
.hero{padding:1.4rem 1.6rem;border:1px solid rgba(128,128,128,.25);border-radius:18px;background:linear-gradient(120deg,rgba(30,100,90,.15),rgba(50,80,150,.10));margin-bottom:1rem}
.hero h1{margin:0;font-size:2.25rem}.muted{opacity:.75}
</style>
<div class="hero"><h1>🛟 DataRescue</h1><p class="muted">Detect → Diagnose → Repair safely → Verify with evidence</p><p>An auditable self-healing pipeline lab. Repairs run on a working copy; your uploaded/source data is never overwritten.</p></div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Pipeline controls")
    source_mode = st.radio("Data source", ["Public UCI dataset", "Upload my CSV"], help="The public option uses UCI Online Retail; first download requires internet access.")
    uploaded = st.file_uploader("Upload CSV", type=["csv"]) if source_mode == "Upload my CSV" else None
    st.caption("Public dataset: UCI Online Retail · 541,909 transactions")
    st.link_button("Dataset documentation", DATASET_URL)
    st.divider()
    scenario = st.selectbox("Demo failure scenario", ["No injected failure", "Schema drift: Quantity becomes text", "Missing required values", "Duplicate records"])
    repairs = st.multiselect("Allow repairs", ["Parse numeric columns; quarantine unparseable values as null", "Remove exact duplicate rows", "Quarantine rows missing critical fields"], default=[])
    run = st.button("▶ Run pipeline", type="primary", use_container_width=True)
    st.caption("Safety: repairs are opt-in and run on a copy. Review every proposed action.")

try:
    if source_mode == "Upload my CSV":
        if uploaded is None:
            st.info("Upload a CSV in the sidebar to begin.")
            st.stop()
        try:
            source_df = pd.read_csv(uploaded, low_memory=False)
            source_label = f"Uploaded file: {uploaded.name}"
        except Exception as exc:
            st.error(f"Could not parse CSV: {exc}")
            st.stop()
    else:
        with st.spinner("Loading public UCI dataset (cached after first download)…"):
            source_df, source_label = load_public_dataset()
except Exception as exc:
    st.error(str(exc))
    st.info("You can still use the app by selecting 'Upload my CSV' and uploading a CSV downloaded from the official UCI dataset page.")
    st.stop()

st.caption(f"Source: {source_label} · Rows: {len(source_df):,} · Columns: {len(source_df.columns)}")
if len(source_df) > 200_000:
    st.warning("Large dataset detected. Profiling uses the full dataframe; consider uploading a smaller sample for a faster demo.")

if "last_result" not in st.session_state:
    st.session_state.last_result = None
if run:
    try:
        with st.spinner("Profiling, diagnosing, applying approved repairs and verifying…"):
            result, output_df = run_pipeline(source_df, scenario, repairs)
        st.session_state.last_result = {"result": result_json(result), "output": output_df.to_csv(index=False), "scenario": scenario, "source_label": source_label, "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as exc:
        st.error(f"Pipeline failed safely: {exc}")

saved = st.session_state.last_result
if saved:
    payload = json.loads(saved["result"])
    st.subheader("Run result")
    a,b,c,d = st.columns(4)
    a.metric("Status", payload["status"])
    b.metric("Input rows", f"{payload['source_rows']:,}")
    c.metric("Output rows", f"{payload['output_rows']:,}", delta=f"{payload['output_rows']-payload['source_rows']:+,}")
    d.metric("Issues before → after", f"{len(payload['issues_before'])} → {len(payload['issues_after'])}")
    if payload["status"] == "PASS": st.success("All implemented checks passed. This does not prove every business rule is correct.")
    elif payload["status"] == "BLOCKED": st.error("Critical structural issue remains. Output must not be treated as production-ready.")
    else: st.warning("Some quality issues remain. Review the unresolved issues before using the output.")
    tab1,tab2,tab3,tab4 = st.tabs(["Overview", "Issue diagnosis", "Repair audit", "Download artifacts"])
    with tab1:
        left,right = st.columns(2)
        with left:
            st.markdown("**Before repair**")
            st.json(payload["metrics_before"])
        with right:
            st.markdown("**After repair**")
            st.json(payload["metrics_after"])
        issues = payload["issues_before"]
        if issues:
            chart_df = pd.DataFrame(issues)
            fig = px.bar(chart_df, x="column", y="count", color="severity", hover_data=["code", "message"], title="Detected issue counts (before repair)")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("No issues detected by the current rule set.")
        st.markdown("**Output preview**")
        st.dataframe(pd.read_csv(__import__('io').StringIO(saved["output"])).head(100), use_container_width=True)
    with tab2:
        st.markdown("**Detected before repair**")
        st.dataframe(pd.DataFrame(payload["issues_before"]) if payload["issues_before"] else pd.DataFrame(columns=["code","severity","column","count","message","recommendation"]), use_container_width=True)
        st.markdown("**Still unresolved after repair**")
        st.dataframe(pd.DataFrame(payload["issues_after"]) if payload["issues_after"] else pd.DataFrame(columns=["code","severity","column","count","message","recommendation"]), use_container_width=True)
        st.caption("Diagnosis is rule-based and explainable in this starter version; no generative AI is required for deterministic checks.")
    with tab3:
        st.write(f"**Scenario:** {saved['scenario']}")
        st.write(f"**Run time (UTC):** {saved['timestamp']}")
        st.write(f"**Source SHA-256:** `{payload['source_sha256']}`")
        st.dataframe(pd.DataFrame(payload["actions"]) if payload["actions"] else pd.DataFrame([{"action":"No repair selected", "status":"no-op"}]), use_container_width=True)
        st.markdown("**Safety policy**: original dataframe is copied; repair choices are explicit; every run is re-profiled; unresolved issues remain visible.")
    with tab4:
        st.download_button("Download repaired CSV", saved["output"], file_name="datarescue_output.csv", mime="text/csv")
        st.download_button("Download audit report (JSON)", saved["result"], file_name="datarescue_audit.json", mime="application/json")
        report_md = f"# DataRescue Run Report\n\n- Status: {payload['status']}\n- Source: {saved['source_label']}\n- Scenario: {saved['scenario']}\n- Run time UTC: {saved['timestamp']}\n- Source SHA-256: {payload['source_sha256']}\n- Input rows: {payload['source_rows']}\n- Output rows: {payload['output_rows']}\n- Issues before: {len(payload['issues_before'])}\n- Issues after: {len(payload['issues_after'])}\n\n## Actions\n\n" + "\n".join(f"- {a}" for a in payload['actions']) + "\n\n## Remaining issues\n\n" + "\n".join(f"- {i['severity']} / {i['code']} / {i['column']}: {i['message']}" for i in payload['issues_after'])
        st.download_button("Download run report (Markdown)", report_md, file_name="datarescue_report.md", mime="text/markdown")
else:
    st.subheader("Baseline profile")
    metrics = profile(source_df)
    a,b,c,d = st.columns(4)
    a.metric("Rows", f"{metrics['rows']:,}")
    b.metric("Columns", metrics["columns"])
    c.metric("Missing cells", f"{metrics['missing_cells']:,}")
    d.metric("Exact duplicate rows", f"{metrics['duplicate_rows']:,}")
    st.markdown("### Preview")
    st.dataframe(source_df.head(100), use_container_width=True)
    st.markdown("### Start a reproducible demo")
    st.write("1. Choose a failure scenario in the sidebar. 2. Select the repair actions you want to allow. 3. Click **Run pipeline**. 4. Inspect the remaining issues and download the audit report.")

st.divider()
st.caption("DataRescue prototype · UCI Online Retail dataset · Deterministic checks and explicit repair policies · Not a production scheduler")
