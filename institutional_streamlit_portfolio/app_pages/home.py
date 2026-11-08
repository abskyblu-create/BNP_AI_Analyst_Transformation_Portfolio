"""Executive landing page for the professional transformation portfolio."""

from __future__ import annotations

import streamlit as st

from data import CAPABILITY_PILLARS, PROFESSIONAL_PROFILE, PROJECTS
from hero import glass_hero


METHOD_FLOW = [
    ("Understand", "the business"),
    ("Structure", "the data and rules"),
    ("Engineer", "the solution"),
    ("Validate", "against evidence"),
    ("Communicate", "the result"),
    ("Deliver", "with ownership"),
]

with st.container(key="chapter_hero"):
    text_col, _ = st.columns([1.05, 1], gap="large")
    with text_col:
        st.caption("ANKIT BHATT  /  FINANCE OPERATIONS × DATA × CONTROLLED AI")
        st.title("From business understanding to engineered transformation")
        st.markdown(
            "A professional portfolio from an **AI Analyst internship within Global Fund Administration transformation "
            "and the Data Office**. Eight missions connect financial operations with Data & BI, Python, AI engineering, "
            "controlled AI and cross-functional delivery. Concept explanations come first; calculations and simulations "
            "remain available as an optional deep dive."
        )
    with st.container(key="hero_backdrop"):
        glass_hero(METHOD_FLOW, label="One repeatable transformation method")

with st.container(border=True, key="contribution_card"):
    st.subheader("Contribution to the organisation", icon=":material/person:")
    st.markdown(
        "Translated financial operations problems into governed datasets, decision-ready reporting, "
        "controlled AI workflows and visible delivery evidence."
    )
    with st.container(horizontal=True):
        st.badge("Fund Administration", color="gray")
        st.badge("Data & BI", color="gray")
        st.badge("Python", color="gray")
        st.badge("AI engineering", color="gray")
        st.badge("UAT & governance", color="gray")

with st.container(key="section_explore"):
    st.subheader("Choose how you want to explore")
    with st.container(border=True, key="contents_card"):
        st.page_link("app_pages/contents.py", label="Contents & navigation — full index, process map and reading routes", icon=":material/toc:")
        st.caption("Review the available pages and their contents, then open a topic directly or follow a recommended route.")
    left, middle, right = st.columns(3, gap="large")
    with left, st.container(border=True, height="stretch", key="entry_understand"):
        st.subheader("Understand", icon=":material/route:")
        with st.container(height="stretch"):
            st.markdown("Review the business context, NAV control chain, delivery lifecycle, data model and AI-engineering methodology.")
        if st.button("How the work fits together", type="primary", icon=":material/arrow_forward:", width="stretch", key="nav_understand"):
            st.switch_page("app_pages/concepts.py")
    with middle, st.container(border=True, height="stretch", key="entry_missions"):
        st.subheader("See the missions", icon=":material/target:")
        with st.container(height="stretch"):
            st.markdown(f"Explore {len(PROJECTS)} documented missions: business problem, contribution, method, controls and outcome.")
        if st.button("Explore the missions", icon=":material/arrow_forward:", width="stretch", key="nav_missions"):
            st.switch_page("app_pages/projects.py")
    with right, st.container(border=True, height="stretch", key="entry_analysis"):
        st.subheader("Interactive analysis", icon=":material/science:")
        with st.container(height="stretch"):
            st.markdown("Open the optional NAV calculations, reconciliation controls, data experiments and delivery simulations.")
        if st.button("Open the interactive lab", icon=":material/arrow_forward:", width="stretch", key="nav_analysis"):
            st.switch_page("app_pages/explore.py")

with st.container(key="chapter_tint_capability"):
    st.subheader("The capability behind the work")
    cols = st.columns(4)
    icons = [":material/account_balance:", ":material/task_alt:", ":material/analytics:", ":material/groups:"]
    for index, (column, (title, description), icon) in enumerate(zip(cols, CAPABILITY_PILLARS, icons)):
        with column, st.container(border=True, height="stretch", key=f"pillar_{index}"):
            st.subheader(title, icon=icon)
            st.caption(description)

with st.container(key="chapter_dark_links"):
    st.subheader("Professional links", icon=":material/link:")
    with st.container(horizontal=True):
        st.link_button("LinkedIn", "https://www.linkedin.com/in/ankit-bhatt-4a1631388/", icon=":material/person:")
        st.link_button("Portfolio website", "https://resume-s3th.onrender.com", icon=":material/language:")
        st.link_button("GitHub", "https://github.com/abskyblu-create", icon=":material/code:")

    st.caption(PROFESSIONAL_PROFILE["proposition"])
