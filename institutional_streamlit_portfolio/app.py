from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from data import FUNDS, PROFESSIONAL_PROFILE
from styles import apply_layout
from state import RUN_STAGES, begin_new_run, initialize_session, log_event


APP_DIR = Path(__file__).resolve().parent
DISCLAIMER = "Independent study project. Not affiliated with or endorsed by any financial institution."
ASSET_DIR = APP_DIR / "assets"


st.set_page_config(
    page_title="Institutional Transformation Vault",
    page_icon=":material/account_balance:",
    layout="wide",
    initial_sidebar_state="expanded",
)
initialize_session()
apply_layout()


def _text_size_from_slider() -> None:
    st.session_state.portfolio_text_size = st.session_state.portfolio_text_size_slider


def _text_size_from_number() -> None:
    if st.session_state.portfolio_text_size is None:
        st.session_state.portfolio_text_size = 18
    st.session_state.portfolio_text_size_slider = st.session_state.portfolio_text_size


def _reset_display_size() -> None:
    st.session_state.portfolio_text_size = 18
    st.session_state.portfolio_text_size_slider = 18
    st.session_state.portfolio_content_width = "Full width"

st.logo(ASSET_DIR / "logo.svg", size="large")


pages = {
    "Start here": [
        st.Page("app_pages/home.py", title="Overview", icon=":material/home:", default=True),
        st.Page("app_pages/contents.py", title="Contents & navigation", icon=":material/toc:"),
        st.Page("app_pages/concepts.py", title="How the work fits together", icon=":material/route:"),
        st.Page("app_pages/projects.py", title="Missions", icon=":material/target:"),
        st.Page("app_pages/explore.py", title="Interactive lab", icon=":material/science:"),
        st.Page("app_pages/guided_pipeline.py", title="Guided case", icon=":material/play_arrow:"),
    ],
    "Fund operations": [
        st.Page("app_pages/operating_model.py", title="Business and operating model", icon=":material/hub:"),
        st.Page("app_pages/fund_accounting.py", title="Fund accounting", icon=":material/account_balance_wallet:"),
        st.Page("app_pages/nav_production.py", title="Net Asset Value control room", icon=":material/calculate:"),
        st.Page("app_pages/reconciliation.py", title="Reconciliation workbench", icon=":material/rule:"),
    ],
    "Mission demonstrations": [
        st.Page("app_pages/data_reporting.py", title="Data and Business Intelligence", icon=":material/database:"),
        st.Page("app_pages/ai_controls.py", title="Controlled Artificial Intelligence", icon=":material/memory:"),
        st.Page("app_pages/governance.py", title="Delivery and governance", icon=":material/verified_user:"),
    ],
    "Reference": [
        st.Page("app_pages/glossary.py", title="Glossary and methodology", icon=":material/menu_book:"),
    ],
}
acknowledged = bool(st.session_state.get("portfolio_acknowledgement"))
page = st.navigation(pages, position="hidden")

if not acknowledged:
    st.caption("ANKIT BHATT - PROFESSIONAL PORTFOLIO")
    st.title("Before you explore", icon=":material/fact_check:")
    st.markdown(
        "This site presents documented professional missions and educational examples of "
        "fund administration, data and transformation. Please confirm the scope below.",
        text_alignment="left",
    )
    with st.container(border=True, key="gate_card"):
        st.markdown("**Portfolio use acknowledgement**")
        st.markdown(
            "- Mission descriptions reflect the supplied portfolio and experience documents. "
            "Names, figures, funds and workflows in interactive examples are fictional.\n"
            "- Examples do not connect to a live financial system or execute transactions. "
            "They are educational material, not investment, accounting, legal or regulatory advice.\n"
            "- Do not enter or upload client, confidential, personal or non-public information."
        )
        accepted = st.checkbox(
            "Educational scope understood; only non-confidential example data will be used.",
            key="portfolio_scope_confirmation",
        )
        if st.button("Enter portfolio", type="primary", disabled=not accepted):
            st.session_state.portfolio_acknowledgement = {
                "version": 1,
                "accepted_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            log_event(
                "Portfolio scope acknowledged",
                "Confirmed",
                "Visitor",
                "Educational scope and example-data notice confirmed for this browser session.",
                scope="Portfolio access",
            )
            st.rerun()
    st.caption("This browser-session acknowledgement records the scope notice. It is not identity verification or a legal signature.")
    st.caption(DISCLAIMER)
    st.stop()

run_workspace = page.title in {
    "Fund accounting",
    "Net Asset Value control room",
    "Reconciliation workbench",
    "Delivery and governance",
}


def _context_changed() -> None:
    begin_new_run(st.session_state.global_fund, st.session_state.global_valuation_date)


if "global_fund" not in st.session_state:
    st.session_state.global_fund = st.session_state.context["fund"]
if "global_valuation_date" not in st.session_state:
    st.session_state.global_valuation_date = st.session_state.context["valuation_date"]

with st.sidebar:
    st.image(ASSET_DIR / "logo.svg", width="stretch")
    st.caption("TRANSFORMATION PORTFOLIO")
    st.page_link("app_pages/home.py", label="Overview", icon=":material/home:")
    st.page_link("app_pages/contents.py", label="Contents & navigation", icon=":material/toc:")
    st.page_link("app_pages/concepts.py", label="How it works", icon=":material/route:")
    st.page_link("app_pages/projects.py", label="Missions", icon=":material/target:")
    st.page_link("app_pages/explore.py", label="Interactive lab", icon=":material/science:")
    st.page_link("app_pages/glossary.py", label="Glossary", icon=":material/menu_book:")
    st.markdown("**Display size**")
    st.number_input(
        "Text size (pixels)", min_value=12, max_value=32,
        value=None if "portfolio_text_size" in st.session_state else 18, step=1,
        key="portfolio_text_size", persist_state="session", on_change=_text_size_from_number,
        help="Enter an exact size or use the plus and minus controls. Default: 18 pixels.",
    )
    st.slider(
        "Text size", min_value=12, max_value=32,
        value=None if "portfolio_text_size_slider" in st.session_state else st.session_state.portfolio_text_size, step=1,
        format="%d px", key="portfolio_text_size_slider", persist_state="session",
        on_change=_text_size_from_slider,
        help="Adjust in one-pixel steps. This control stays synchronised with the numeric input.",
    )
    st.segmented_control(
        "Content width", ["Full width", "Reading width"],
        default=None if "portfolio_content_width" in st.session_state else "Full width",
        required=True, width="stretch", wrap=True,
        key="portfolio_content_width", persist_state="session",
        help="Use the available width or a narrower reading layout.",
    )
    st.button("Reset display size", on_click=_reset_display_size, width="stretch")
    if run_workspace:
        st.caption("VALUATION RUN CONTEXT")
        st.selectbox(
            "Synthetic fund",
            [fund["Fund"] for fund in FUNDS],
            key="global_fund",
            on_change=_context_changed,
            persist_state="session",
        )
        st.date_input(
            "Valuation date",
            key="global_valuation_date",
            on_change=_context_changed,
            persist_state="session",
        )
        st.caption("All fund data and workflow actors are fictional. Session actions do not reach an external system.")
    else:
        st.markdown(f"**{PROFESSIONAL_PROFILE['name']}**")
        st.caption("Finance operations · Data & BI · Controlled AI · Delivery")
        st.link_button("LinkedIn", "https://www.linkedin.com/in/ankit-bhatt-4a1631388/", icon=":material/person:", width="stretch")
        st.link_button("Portfolio website", "https://resume-s3th.onrender.com", icon=":material/language:", width="stretch")
        st.link_button("GitHub", "https://github.com/abskyblu-create", icon=":material/code:", width="stretch")

if run_workspace:
    context = st.session_state.context
    top_left, top_mid, top_right = st.columns([2.1, 1.1, 1.1], vertical_alignment="center")
    top_left.caption(
        f"{context['fund']}  ·  {context['share_class']}  ·  {context['base_currency']}  ·  {context['valuation_frequency']} valuation"
    )
    top_mid.caption(f"Run {st.session_state.run_id}  ·  version {st.session_state.run_version}")
    top_right.caption(datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC"))

    with st.container(horizontal=True, vertical_alignment="center"):
        st.badge(st.session_state.run_stage, color="green" if RUN_STAGES.index(st.session_state.run_stage) >= 2 else "blue")
        st.caption(f"Valuation date: {context['valuation_date']:%d %b %Y}  ·  Policy: {context['policy_version']}")

page.run()

with st.container(key="site_footer"):
    st.caption("Professional transformation portfolio · Synthetic operational workbenches · No live connectivity, certification or regulatory attestation")
    st.caption(DISCLAIMER)
