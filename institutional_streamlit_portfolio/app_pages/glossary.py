from __future__ import annotations

import pandas as pd
import streamlit as st

from ui import aligned_dataframe

from data import GLOSSARY
from ui import page_header


page_header(
    "REFERENCE / REPORT TERMS",
    "Glossary",
    "Business and technical definitions supporting the missions and interactive analysis. Search a term or abbreviation when you need it.",
    ":material/menu_book:",
)

glossary = pd.DataFrame(
    GLOSSARY,
    columns=["Term", "Short form", "Area", "Meaning"],
)

search_col, area_col = st.columns([2, 1])
with search_col:
    search = st.text_input(
        "Search terms, abbreviations or definitions",
        type="search",
        placeholder="Try CAM, NAV, bps or reconciliation",
    ).strip()
with area_col:
    area = st.selectbox("Area", ["All areas", *sorted(glossary["Area"].unique())])

visible = glossary
if area != "All areas":
    visible = visible[visible["Area"] == area]
if search:
    matches = visible.fillna("").astype(str).agg(" ".join, axis=1)
    visible = visible[matches.str.contains(search, case=False, regex=False)]

st.caption(f"Showing {len(visible)} of {len(glossary)} terms.")
if visible.empty:
    st.info("No term matches those filters. Try a shorter word or choose all areas.")
else:
    aligned_dataframe(
        visible,
        hide_index=True,
        width="stretch",
        height=min(620, 38 * len(visible) + 40),
        column_config={
            "Term": st.column_config.TextColumn(width="medium"),
            "Short form": st.column_config.TextColumn(width="small"),
            "Area": st.column_config.TextColumn(width="small"),
            "Meaning": st.column_config.TextColumn(width="large"),
        },
    )

st.caption(
    "Terminology is selected from the supplied internship presentation and professional-experience report. "
    "Basis points (bps) is included for the valuation workbench."
)
st.info("CAM means Client Account Manager throughout this portfolio.", icon=":material/badge:")
with st.expander("About the examples"):
    st.markdown(
        "The mission descriptions summarize documented experience. Interactive funds, figures, controls and "
        "downloads are fictional learning examples. CAM always means Client Account Manager.",
        text_alignment="justify",
    )
