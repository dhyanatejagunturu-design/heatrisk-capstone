"""Heat Risk EU dashboard.

Run:  streamlit run app/streamlit_app.py
Reads small precomputed tables from data/processed, never raw satellite data.
"""

import streamlit as st

from heatrisk.config import load_settings

settings = load_settings()

st.set_page_config(page_title="Heat Risk EU", layout="wide")
st.title("Heat Risk EU")
st.caption("Heat-related mortality and urban heat vulnerability in five European countries")

view = st.sidebar.radio("View", ["Regional risk", "City vulnerability"])

if view == "Regional risk":
    country = st.sidebar.selectbox("Country", list(settings["countries"].values()))
    st.subheader(f"Heat thresholds and risk curves: {country}")
    st.info("Risk curves appear here after the Sprint 2 model run.")
else:
    city = st.sidebar.selectbox("City", [c["name"] for c in settings["cities"].values()])
    st.subheader(f"Heat Vulnerability Index: {city}")
    st.info("Vulnerability map appears here after Sprint 3.")

st.sidebar.markdown("---")
st.sidebar.caption("Results describe places, not individuals. 2026 data is provisional.")
