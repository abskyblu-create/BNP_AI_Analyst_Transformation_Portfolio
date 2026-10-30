from __future__ import annotations

import pandas as pd
import streamlit as st

from ui import result_metric

from ui import aligned_table

from learning import explain

from data import OPERATING_MODELS, TEAM_FUNCTIONS
from domain import operating_model_route
from ui import metric_row, module_footer, page_header


page_header(
    "FUND OPERATIONS / OPERATING MODEL",
    "How fund services are organized",
    "Choose where a fund process should run, then see the people and controls behind the decision.",
    ":material/hub:",
)

st.caption("Start with the routing exercise. Open the sections below when you want more context.")
st.subheader("Choose a delivery route")
explain('routing')
with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    common_ready = c1.checkbox("Common platform supports the jurisdiction", value=True)
    product_standard = c2.checkbox("Product and accounting rules are standardized", value=True)
    local_required = c3.checkbox("A local rule requires a dedicated process", value=False)
    route = operating_model_route(common_ready, local_required, product_standard)
    result_metric("Recommended route", route["model"], border=True)
    st.markdown(route["reason"], text_alignment="justify")
    st.caption(f"Next check: {route['next_control']}")

with st.expander("Compare the operating models"):
    st.caption("An operating model connects people, processes, systems and controls across locations.")
    left, right = st.columns(2, gap="large")
    for container, (name, details) in zip((left, right), OPERATING_MODELS.items()):
        with container, st.container(border=True):
            st.subheader(name)
            st.markdown(details["definition"], text_alignment="justify")
            st.markdown(f"**Best fit:** {details['best_for']}", text_alignment="justify")
            st.markdown(f"**Control owner:** {details['ownership']}", text_alignment="justify")
            st.caption(f"Strength: {details['strength']}")
            st.caption(f"Watch for: {details['watch']}")

with st.expander("Who does what in a fund service?"):
    roles = [
    ("Management company", "Governs the fund and its delegates within the applicable legal structure and governing documents."),
    ("Investment manager", "Makes investment decisions within the mandate and supplies trade and position information."),
    ("Fund administrator", "Maintains the accounting record and prepares the valuation package under the delegated mandate."),
    ("Transfer agent", "Maintains the investor register and processes subscriptions, redemptions and unit ownership."),
    ("Depositary and custodian", "Provides oversight and safekeeping functions and independent asset and cash records; exact responsibilities depend on the arrangement."),
    ("Client Account Manager (CAM)", "Coordinates client communication, service reviews, requests and escalation across operational teams."),
    ]
    selected_role = st.selectbox("Explore a role", [name for name, _ in roles])
    st.info(dict(roles)[selected_role], icon=":material/person_search:")
    aligned_table(pd.DataFrame(TEAM_FUNCTIONS.items(), columns=["Function", "Primary responsibility"]))

with st.expander("Straight-through processing analysis"):
    explain('stp')
    st.caption("Change the automation rate to see how many records might still need manual handling. This is a volume illustration, not a staffing estimate.")
    a, b, c = st.columns(3)
    daily_volume = a.number_input("Daily records", min_value=1, value=10_000, step=500)
    current_rate = b.slider("Current straight-through processing rate (%)", 0.0, 100.0, 72.0, 0.5)
    target_rate = c.slider("Target straight-through processing rate (%)", 0.0, 100.0, 90.0, 0.5)
    current_manual = round(daily_volume * (1 - current_rate / 100))
    target_manual = round(daily_volume * (1 - target_rate / 100))
    metric_row(
        [
            ("Manual now", f"{current_manual:,}", "Estimated records requiring manual handling now"),
            ("Manual at target", f"{target_manual:,}", "Estimated records requiring manual handling at the target rate"),
            ("Potential reduction", f"{max(0, current_manual - target_manual):,}", "Illustrative record volume reduction"),
        ]
    )

module_footer("operating_model", "app_pages/fund_accounting.py", "Continue to fund accounting")
