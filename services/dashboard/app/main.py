"""Streamlit dashboard for AnomX alerts, runs, and system status."""

from __future__ import annotations

import httpx
import streamlit as st
from api_client import DEFAULT_API_URL, ApiClient
from views import render_alerts, render_overview, render_runs


def main() -> None:
    st.set_page_config(page_title="AnomX Dashboard", layout="wide", page_icon="📊")
    st.title("AnomX")
    st.caption(f"API: `{DEFAULT_API_URL}`")

    client = ApiClient()

    try:
        streams_payload = client.get_json("/streams")
    except httpx.HTTPError as exc:
        st.error(f"Cannot reach API: {exc}")
        st.info("Start infrastructure and API: `make docker-up` then `make api`.")
        st.info("Seed data: `make mlops-demo` or `make explain-demo`.")
        return

    streams = streams_payload.get("streams", [])
    stream_names = [str(item["name"]) for item in streams if isinstance(item, dict)]

    tab_overview, tab_alerts, tab_runs = st.tabs(["Overview", "Alerts", "Runs"])

    with tab_overview:
        render_overview(client)

    with tab_alerts:
        render_alerts(client, stream_names)

    with tab_runs:
        render_runs(client, stream_names)


if __name__ == "__main__":
    main()
