"""Dashboard view modules."""

from __future__ import annotations

from typing import Any

import httpx
import pandas as pd
import streamlit as st
from api_client import ApiClient


def render_overview(client: ApiClient) -> None:
    st.subheader("System status")

    col_live, col_ready = st.columns(2)
    with col_live:
        try:
            live = client.get_json("/health")
            st.success(f"Liveness: **{live.get('status', 'unknown')}**")
            st.caption(f"Service `{live.get('service')}` v{live.get('version')}")
        except httpx.HTTPError as exc:
            st.error(f"Liveness check failed: {exc}")

    with col_ready:
        try:
            response = httpx.get(f"{client.base_url}/health/ready", timeout=10.0)
            ready = response.json()
            if response.status_code == 200:
                st.success(f"Readiness: **{ready.get('status', 'unknown')}**")
            else:
                st.warning(f"Readiness: **{ready.get('status', 'degraded')}**")
            checks = ready.get("checks", {})
            if isinstance(checks, dict):
                for name, check in checks.items():
                    if not isinstance(check, dict):
                        continue
                    latency = check.get("latency_ms")
                    suffix = f" ({latency} ms)" if latency is not None else ""
                    if check.get("status") == "ok":
                        st.caption(f"{name}: ok{suffix}")
                    else:
                        st.caption(f"{name}: {check.get('detail', 'error')}")
        except httpx.HTTPError as exc:
            st.error(f"Readiness check failed: {exc}")

    st.divider()
    st.subheader("Streams")

    streams_payload = client.get_json("/streams")
    streams = streams_payload.get("streams", [])
    if not streams:
        st.info("No streams yet. Run `make mlops-demo` or `make explain-demo`.")
        return

    rows: list[dict[str, Any]] = []
    for item in streams:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "stream": item.get("name"),
                "alerts": item.get("alert_count", 0),
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("Prometheus metrics (preview)", expanded=False):
        try:
            metrics_text = client.get_text("/metrics")
            preview = "\n".join(metrics_text.splitlines()[:20])
            st.code(preview, language="text")
        except httpx.HTTPError as exc:
            st.warning(f"Could not fetch /metrics: {exc}")


def render_alerts(client: ApiClient, stream_names: list[str]) -> None:
    if not stream_names:
        st.info("No streams available.")
        return

    selected_stream = st.selectbox("Stream", stream_names, key="alerts_stream")
    limit = st.slider("Alert limit", min_value=5, max_value=50, value=15, key="alerts_limit")

    alerts_payload = client.get_json(f"/streams/{selected_stream}/alerts?limit={limit}")
    alerts = alerts_payload.get("alerts", [])
    if not alerts:
        st.info("No alerts for this stream yet.")
        return

    table_rows: list[dict[str, Any]] = []
    for alert in alerts:
        if not isinstance(alert, dict):
            continue
        table_rows.append(
            {
                "observed_at": alert.get("observed_at"),
                "score": alert.get("score"),
                "summary": alert.get("summary"),
                "alert_id": alert.get("alert_id"),
            }
        )

    df = pd.DataFrame(table_rows)
    st.subheader(f"Alerts — {selected_stream}")
    st.dataframe(df, use_container_width=True, hide_index=True)

    alert_ids = [str(row["alert_id"]) for row in table_rows]
    selected_alert_id = st.selectbox("Inspect alert", alert_ids, key="alert_detail")
    if not selected_alert_id:
        return

    detail_payload = client.get_json(f"/alerts/{selected_alert_id}")
    alert = detail_payload.get("alert")
    if not isinstance(alert, dict):
        st.error("Unexpected alert detail payload.")
        return

    st.subheader("Why this alert?")
    st.markdown(f"**Summary:** {alert.get('summary', 'N/A')}")

    metric_cols = st.columns(3)
    metric_cols[0].metric("Score", f"{float(alert.get('score', 0)):.3f}")
    if alert.get("ensemble_threshold") is not None:
        metric_cols[1].metric("Ensemble threshold", f"{float(alert['ensemble_threshold']):.3f}")
    if alert.get("value") is not None:
        metric_cols[2].metric("Observed value", f"{float(alert['value']):.2f}")

    st.markdown("**Rules**")
    for rule in alert.get("rules", []):
        st.write(f"- {rule}")

    contributions = alert.get("feature_contributions") or {}
    if contributions:
        st.markdown("**Feature contributions**")
        st.json(contributions)

    detectors = alert.get("detectors") or []
    if detectors:
        st.markdown("**Per-detector breakdown**")
        for detector in detectors:
            if not isinstance(detector, dict):
                continue
            with st.expander(str(detector.get("detector", "detector")), expanded=False):
                st.write(detector.get("summary", ""))
                for rule in detector.get("rules", []):
                    st.write(f"- {rule}")


def render_runs(client: ApiClient, stream_names: list[str]) -> None:
    if not stream_names:
        st.info("No streams available.")
        return

    selected_stream = st.selectbox("Stream", stream_names, key="runs_stream")
    limit = st.slider("Run limit", min_value=5, max_value=50, value=10, key="runs_limit")

    runs_payload = client.get_json(f"/streams/{selected_stream}/runs?limit={limit}")
    runs = runs_payload.get("runs", [])
    if not runs:
        st.info("No pipeline runs recorded for this stream.")
        return

    table_rows: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        metadata = run.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        table_rows.append(
            {
                "started_at": run.get("started_at"),
                "run_type": run.get("run_type"),
                "status": run.get("status"),
                "records_written": run.get("records_written"),
                "observations_scored": run.get("observations_scored"),
                "alerts_created": run.get("alerts_created"),
                "mlflow_run_id": metadata.get("mlflow_run_id"),
                "run_id": run.get("run_id"),
            }
        )

    st.subheader(f"Pipeline runs — {selected_stream}")
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    mlflow_ids = [
        str(row["mlflow_run_id"])
        for row in table_rows
        if row.get("mlflow_run_id") not in (None, "")
    ]
    if mlflow_ids:
        st.caption(
            "MLflow UI: `uv run mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db`"
        )
