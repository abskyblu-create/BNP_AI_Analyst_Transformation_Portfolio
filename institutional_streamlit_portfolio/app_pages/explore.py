from __future__ import annotations

import streamlit as st


st.caption("OPTIONAL DEEP DIVE")
st.title("Interactive lab", icon=":material/science:")
st.markdown(
    "Open this area when you want to test the calculations, controls and simulations behind the portfolio. "
    "Every case uses fictional data and stays separate from the professional mission evidence."
)

st.subheader("Choose your depth")
mode = st.segmented_control(
    "Exploration mode",
    ["Guided case", "NAV & controls", "Data & AI", "Delivery"],
    default="Guided case",
    width="stretch",
)

if mode == "Guided case":
    title = "Follow one case from source to delivery"
    description = "A ten-stage walkthrough connects data intake, valuation, cash, reconciliation, NAV, reporting, review and controlled delivery."
    destinations = [("Start the guided case", "app_pages/guided_pipeline.py", ":material/play_arrow:")]
elif mode == "NAV & controls":
    title = "Explore the valuation control chain"
    description = "Inspect accounting, NAV construction and reconciliation decisions in separate workbenches."
    destinations = [
        ("Fund accounting", "app_pages/fund_accounting.py", ":material/account_balance_wallet:"),
        ("NAV control room", "app_pages/nav_production.py", ":material/calculate:"),
        ("Reconciliation", "app_pages/reconciliation.py", ":material/rule:"),
    ]
elif mode == "Data & AI":
    title = "Explore reporting and controlled automation"
    description = "Test data-quality rules, reporting logic, prompt patterns and structured extraction controls."
    destinations = [
        ("Data & BI lab", "app_pages/data_reporting.py", ":material/analytics:"),
        ("Controlled AI lab", "app_pages/ai_controls.py", ":material/memory:"),
    ]
else:
    title = "Explore operating-model and delivery decisions"
    description = "Try routing, governance, evidence and readiness decisions with synthetic examples."
    destinations = [
        ("Operating model", "app_pages/operating_model.py", ":material/hub:"),
        ("Delivery & governance", "app_pages/governance.py", ":material/verified_user:"),
    ]

with st.container(border=True):
    st.header(title)
    st.markdown(description)
    with st.container(horizontal=True, key="navigation_lab"):
        for label, page, icon in destinations:
            if st.button(
                label, icon=icon,
                key="start_guided_case" if mode == "Guided case" else page,
                type="primary" if mode == "Guided case" else "secondary",
                width="stretch",
            ):
                st.switch_page(page)

st.info(
    "Start with **How it works** if you want the concepts without calculations. Use this lab only when you want the detailed mechanics.",
    icon=":material/lightbulb:",
)
