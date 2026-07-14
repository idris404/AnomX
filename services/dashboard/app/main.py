"""Streamlit dashboard for AnomX alerts."""

from __future__ import annotations

import os

import httpx
import pandas as pd
import streamlit as st

DEFAULT_API_URL = os.getenv("ANOMX_API_URL", "http://localhost:8000")


def _get_json(path: str) -> dict[str, object]:
    response = httpx.get(f"{DEFAULT_API_URL}{path}", timeout=10.0)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        msg = f"Unexpected API response for {path}"
        raise TypeError(msg)
    return payload


def main() -> None:
    st.set_page_config(page_title="AnomX Dashboard", layout="wide")
    st.title("AnomX — Anomaly Alerts")
    st.caption(f"API: `{DEFAULT_API_URL}`")

    try:
        streams_payload = _get_json("/streams")
    except httpx.HTTPError as exc:
        st.error(f"Cannot reach API: {exc}")
        st.info("Start the API with `make api` after `make explain-demo`.")
        return

    streams = streams_payload.get("streams", [])
    if not streams:
        st.warning("No streams found. Run `make explain-demo` first.")
        return

    stream_names = [str(item["name"]) for item in streams if isinstance(item, dict)]
    selected_stream = st.sidebar.selectbox("Stream", stream_names)
    limit = st.sidebar.slider("Alert limit", min_value=5, max_value=50, value=15)

    alerts_payload = _get_json(f"/streams/{selected_stream}/alerts?limit={limit}")
    alerts = alerts_payload.get("alerts", [])
    if not alerts:
        st.info("No alerts for this stream yet.")
        return

    table_rows = []
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
    selected_alert_id = st.selectbox("Inspect alert", alert_ids)
    if not selected_alert_id:
        return

    detail_payload = _get_json(f"/alerts/{selected_alert_id}")
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


if __name__ == "__main__":
    main()
