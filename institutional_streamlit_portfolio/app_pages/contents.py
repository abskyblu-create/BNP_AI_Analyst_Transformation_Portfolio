"""Visible content index, connected business map and navigation guidance."""

import streamlit as st

from ui import page_header


page_header(
    "PORTFOLIO / CONTENTS AND NAVIGATION",
    "Contents & navigation",
    "Select a page title to open it. Choose the topic that interests you; there is no required reading order.",
    ":material/toc:",
)

st.markdown(
    "**First visit:** begin with **How the work fits together** for the business context, "
    "**Missions** for professional experience, or **Guided case** for a complete worked example. "
    "Return to this directory at any time from the sidebar."
)
st.subheader("Content index")
sections = [
    ("Portfolio and professional experience", [
        ("Overview", "home", "Professional profile, contribution and capabilities."),
        ("How the work fits together", "concepts", "How fund operations, data, controls and delivery connect."),
        ("Missions", "projects", "Eight professional missions: objectives, methods and outcomes."),
    ]),
    ("Worked examples", [
        ("Guided case", "guided_pipeline", "One prepared fund through ten connected stages. No financial inputs required."),
        ("Interactive lab", "explore", "Entry points for individual finance, data, automation and delivery exercises."),
    ]),
    ("Fund operations", [
        ("Business and operating model", "operating_model", "Service responsibilities, delivery routes and automation rates."),
        ("Fund accounting", "fund_accounting", "Assets, liabilities, investor units, journals and fee calculations."),
        ("Net Asset Value control room", "nav_production", "Investment valuation, NAV, cash forecasts and readiness controls."),
        ("Reconciliation workbench", "reconciliation", "Compare records, investigate differences and document corrective actions."),
    ]),
    ("Data, automation and delivery", [
        ("Data and Business Intelligence", "data_reporting", "Reporting measures, fund and event counts, CSV preparation and data quality."),
        ("Controlled Artificial Intelligence", "ai_controls", "Confirmation extraction, valuation-date checks and CSV splitting."),
        ("Delivery and governance", "governance", "Review, approval, deadlines, distribution, recovery planning and UAT."),
    ]),
    ("Reference and navigation", [
        ("Glossary and methodology", "glossary", "Search business terminology and abbreviations by subject."),
        ("Contents & navigation", "contents", "You are here. Use this directory to choose another topic."),
    ]),
]

with st.container(key="index_jump"):
    st.markdown(
    "**Go to a section:** [Professional experience](#index-1) | [Worked examples](#index-2) | "
    "[Fund operations](#index-3) | [Data and delivery](#index-4) | [Reference](#index-5)"
    )
with st.container(key="book_index"):
    for chapter, (title, pages) in enumerate(sections, 1):
        with st.container(key=f"index_chapter_{chapter}"):
            st.subheader(f"{chapter:02d}  {title}", anchor=f"index-{chapter}")
            for number, (label, page, description) in enumerate(pages, 1):
                with st.container(key=f"index_entry_{page}"):
                    title_column, description_column = st.columns([2, 3], gap="medium", vertical_alignment="center")
                    with title_column:
                        st.page_link(
                            f"app_pages/{page}.py", label=f"{chapter}.{number}  {label}",
                            disabled=page == "contents", width="stretch",
                        )
                    with description_column:
                        st.markdown(description)

st.subheader("Connected navigation diagram")
st.markdown("**Prefer a visual route:** select any page below. Each column offers a suggested sequence; enter or leave it at any point.")
with st.container(key="navigation_diagram"):
    with st.container(key="diagram_start"):
        st.page_link("app_pages/home.py", label="Overview", icon=":material/home:", width="stretch")
    st.markdown(":material/arrow_downward:", text_alignment="center")
    branches = [
        ("Understand the portfolio", [
            ("How the work fits together", "concepts"),
            ("Business and operating model", "operating_model"),
            ("Missions", "projects"),
        ], "Understand the operation, responsibilities and documented contribution."),
        ("Explore financial operations", [
            ("Interactive lab", "explore"),
            ("Guided case", "guided_pipeline"),
            ("Fund accounting", "fund_accounting"),
            ("NAV control room", "nav_production"),
            ("Reconciliation workbench", "reconciliation"),
        ], "Follow the case or inspect accounting, valuation and exception handling."),
        ("Explore data and delivery", [
            ("Data and Business Intelligence", "data_reporting"),
            ("Controlled Artificial Intelligence", "ai_controls"),
            ("Delivery and governance", "governance"),
        ], "Examine reporting, controlled processing and reviewed delivery."),
    ]
    columns = st.columns(3, gap="medium", vertical_alignment="top")
    for lane, (column, (title, nodes, description)) in enumerate(zip(columns, branches), 1):
        with column, st.container(key=f"diagram_lane_{lane}", height="stretch"):
            st.markdown(f"**{title}**", text_alignment="center")
            for number, (label, page) in enumerate(nodes):
                if number:
                    st.markdown(":material/arrow_downward:", text_alignment="center")
                st.page_link(f"app_pages/{page}.py", label=label, icon=":material/arrow_forward:", width="stretch")
            with st.container(height="stretch"):
                st.caption(description)
            st.markdown(":material/arrow_downward:", text_alignment="center")
    with st.container(key="diagram_end"):
        st.page_link("app_pages/glossary.py", label="Glossary and methodology - available throughout", icon=":material/menu_book:", width="stretch")
st.caption(
    "The arrows indicate suggested navigation, not automatic data transfer. Within the operational workflow, "
    "accounting corrections return to valuation for recalculation before renewed review. "
    "Return to Contents & navigation from the sidebar to select another route."
)

st.markdown(
    "**Within each page:** the green tab identifies the current view; select another tab to see its activity. "
    "Supporting panels contain definitions or evidence. **Workflow continuity:** the Guided case is self-contained; "
    "the NAV, reconciliation and governance workbenches share a separate valuation run."
)
