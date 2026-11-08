from __future__ import annotations

import streamlit as st

from data import NAV_FOUNDATION_STEPS
from ui import method_flow


with st.container(key="chapter_dark_page_header"):
    st.caption("HOW THE WORK FITS TOGETHER")
    st.title("From a business process to a controlled solution", icon=":material/route:")
    st.markdown(
        "The internship sat between Fund Administration operations and transformation: translating process risks "
        "into data and control rules, engineering reporting or automation, testing results with users and maintaining "
        "stakeholder alignment through delivery."
    )

st.subheader("The complete story in one flow")
with st.container(key="method_line_story"):
    method_flow([
        ("Understand the operation", ""),
        ("find the control point", ""),
        ("structure the data", ""),
        ("engineer the rule, model or prompt", ""),
        ("validate against the source", ""),
        ("communicate the decision", ""),
        ("hand over with evidence", ""),
    ])

concept = st.segmented_control(
    "Choose a concept",
    ["Fund Administration", "NAV lifecycle", "Delivery", "Data & BI", "AI engineering"],
    default="Fund Administration",
    selection_mode="single",
    width="stretch",
)

if concept == "Fund Administration":
    st.header("Fund administration: business framework", icon=":material/account_balance:")
    st.markdown(
        "A fund administrator maintains the accounting record, supports valuation, reconciles independent records, "
        "checks exceptions and prepares controlled information for review and distribution. The goal is a fair and "
        "timely Net Asset Value supported by evidence."
    )
    steps = [
        ("1", "Receive", "Fund rules, trades, cash, positions, prices and foreign-exchange rates."),
        ("2", "Reconcile", "Compare accounting, custodian and investment-manager records."),
        ("3", "Investigate", "Understand breaks, stale prices, cash differences and cut-off risks."),
        ("4", "Control", "Correct or justify, re-check, review and approve."),
        ("5", "Deliver", "Submit the approved result and retain the evidence."),
    ]
elif concept == "NAV lifecycle":
    st.header("How a NAV is produced", icon=":material/calculate:")
    st.markdown(
        "NAV is not one formula in isolation. It is the controlled result of accurate data, correct timing, "
        "reconciliation, review and approval. At its core: **assets − liabilities = net assets**, then "
        "**net assets ÷ units = NAV per unit**."
    )
    steps = [(number, title, explanation) for number, title, explanation in NAV_FOUNDATION_STEPS]
elif concept == "Delivery":
    st.header("How change moved toward production", icon=":material/task_alt:")
    steps = [
        ("1", "Business need", "Define the problem, owner and success criteria."),
        ("2", "Requirements", "Translate the need into testable business and technical rules."),
        ("3", "Proof of concept", "Test feasibility with bounded scope and visible assumptions."),
        ("4", "User Acceptance Testing", "Operations validates expected behavior and records evidence."),
        ("5", "Production readiness", "Resolve blockers, confirm ownership and approve handover."),
        ("6", "Business as usual", "Monitor adoption, controls and improvement actions."),
    ]
elif concept == "Data & BI":
    st.header("How source complexity became decision support", icon=":material/analytics:")
    steps = [
        ("1", "Understand", "Start with the business question and the meaning of each source field."),
        ("2", "Preserve", "Keep raw data, lineage, NULL values and source-row identity."),
        ("3", "Model", "Separate unique fund reference data from repeated operational events."),
        ("4", "Measure", "Build explicit rules for exposure, ageing, timeliness and exceptions."),
        ("5", "Validate", "Reconcile dashboard totals and drill-downs back to source populations."),
        ("6", "Explain", "Show management what happened, why it matters and what needs action."),
    ]
else:
    st.header("AI engineering as controlled engineering", icon=":material/memory:")
    st.markdown(
        "AI engineering supported NAV-delay rechecks and broker-data extraction. Prompts operated as testable "
        "control logic with source boundaries, structured outputs, validation and human sign-off."
    )
    steps = [
        ("1", "Bound the source", "Use explicit anchors, terminus markers and calendar limits; do not invent data."),
        ("2", "Separate stages", "Extract first, then map meaning, validate risk fields and request approval."),
        ("3", "Encode business rules", "Treat daily and non-daily funds differently and validate FX legs independently."),
        ("4", "Preserve context", "Use buffering and controlled mapping knowledge where sequential context matters."),
        ("5", "Re-verify", "Check each output against the source and keep NULL distinct from zero."),
        ("6", "Approve", "Route uncertainty and missing mandatory fields to accountable human review."),
    ]

for number, title, explanation in steps:
    with st.container(border=True, horizontal=True, vertical_alignment="center"):
        st.badge(str(number), color="green")
        st.markdown(f"**{title}** — {explanation}")

st.space("small")
with st.container(border=True):
    st.subheader("Want to see the mechanics?", icon=":material/science:")
    st.markdown("The explanation above is the main experience. Calculations, controls and simulations are optional.")
    if st.button("Open the interactive lab", type="primary", icon=":material/arrow_forward:"):
        st.switch_page("app_pages/explore.py")

st.caption("Professional methods come from the supplied internship presentation. Interactive figures and entities are fictional learning examples.")
