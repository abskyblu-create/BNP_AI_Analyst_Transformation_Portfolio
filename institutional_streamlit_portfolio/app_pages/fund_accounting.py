from __future__ import annotations

from uuid import uuid4

import pandas as pd
import streamlit as st

from ui import aligned_dataframe

from learning import explain

from domain import JOURNAL_TEMPLATES, journal_entry, performance_fee
from state import log_event
from ui import metric_row, module_footer, page_header


page_header(
    "FUND OPERATIONS / ACCOUNTING",
    "How fund accounting builds Net Asset Value",
    "Change assets, liabilities or units to see how the price per unit moves. The other tabs show a journal example and the records behind it.",
    ":material/account_balance_wallet:",
)

foundation, journal, mathematics, systems = st.tabs(
    ["NAV calculation", "Journal entries", "Fee calculation", "Source records"]
)

with foundation:
    explain('nav')
    st.markdown("**Net Asset Value (NAV) = assets − liabilities.** Divide by the units in the share class to get NAV per unit.")
    assets = st.number_input("Illustrative total assets (EUR)", min_value=0.0, value=500_500_000.0, step=500_000.0)
    liabilities = st.number_input("Illustrative total liabilities (EUR)", min_value=0.0, value=25_506_507.0, step=100_000.0)
    units = st.number_input("Units outstanding for this illustrative share class", min_value=1.0, value=4_000_000.0, step=10_000.0)
    net_assets = assets - liabilities
    if net_assets <= 0:
        st.error("Net assets must be positive to calculate a meaningful Net Asset Value per unit.")
    else:
        metric_row(
            [
                ("Total assets", f"EUR {assets:,.2f}", "Investments, cash, receivables and other recognized assets"),
                ("Total liabilities", f"EUR {liabilities:,.2f}", "Payables, accrued fees and other recognized obligations"),
                ("Total Net Asset Value", f"EUR {net_assets:,.2f}", "Total assets less total liabilities"),
                ("Net Asset Value per unit", f"EUR {net_assets / units:,.4f}", "Illustrative single-share-class calculation"),
            ]
        )
    with st.expander("What makes fund accounting different?"):
        left, right = st.columns(2, gap="large")
        with left, st.container(border=True):
            st.subheader("Company accounting")
            st.markdown("Measures a company's assets, liabilities, revenue and profit over reporting periods.", text_alignment="justify")
        with right, st.container(border=True):
            st.subheader("Fund accounting")
            st.markdown("Values an investor-owned pool at each valuation point, including investments, cash, income, expenses and units.", text_alignment="justify")
        st.caption("The general ledger (GL) holds the accounting entries behind these balances. Each journal's debits and credits must balance.")

with journal:
    explain('journal')
    st.subheader("See how one event is recorded")
    st.markdown("Choose an event and post it to this session's example ledger. It is separate from the NAV calculation.", text_alignment="justify")
    with st.form("journal_form"):
        transaction = st.selectbox("Accounting event", list(JOURNAL_TEMPLATES))
        amount = st.number_input("Amount (EUR)", min_value=0.01, value=100_000.0, step=10_000.0)
        reference = st.text_input("Source or evidence reference", value=f"DOC-{uuid4().hex[:6].upper()}")
        submitted = st.form_submit_button("Post illustrative journal", type="primary", icon=":material/post_add:")
    if submitted:
        try:
            lines = journal_entry(transaction, amount, reference.strip())
            st.session_state.journal.extend(lines)
            log_event("Illustrative journal posted", "Recorded", "Portfolio visitor", f"{transaction}; EUR {amount:,.2f}; reference {reference.strip()}.", scope="Accounting laboratory")
            st.success("Balanced journal added to the session ledger.")
        except ValueError as exc:
            st.error(str(exc))
    if st.session_state.journal:
        journal_df = pd.DataFrame(st.session_state.journal)
        aligned_dataframe(
            journal_df,
            hide_index=True,
            width="stretch",
            column_config={
                "Debit (EUR)": st.column_config.NumberColumn(format="localized"),
                "Credit (EUR)": st.column_config.NumberColumn(format="localized"),
            },
        )
        debits = journal_df["Debit (EUR)"].sum()
        credits = journal_df["Credit (EUR)"].sum()
        metric_row(
            [
                ("Cumulative debits", f"EUR {debits:,.2f}", "Sum of illustrative debit lines"),
                ("Cumulative credits", f"EUR {credits:,.2f}", "Sum of illustrative credit lines"),
                ("Out-of-balance amount", f"EUR {abs(debits - credits):,.2f}", "Must be zero for a balanced general ledger"),
            ]
        )
        if st.button("Clear illustrative journal", icon=":material/restart_alt:"):
            st.session_state.journal = []
            log_event("Illustrative journal cleared", "Reset", "Portfolio visitor", "Session journal returned to empty state.", scope="Accounting laboratory")
            st.rerun()

with mathematics:
    explain('fees')
    explain('bps')
    st.subheader("Illustrative performance fee")
    st.caption("Change the inputs to see a high-water-mark example. A real fund's documents determine its fee method.")
    a, b, c = st.columns(3)
    current_price = a.number_input("Current Net Asset Value per unit", min_value=0.0, value=112.0, step=0.5)
    high_water_mark = b.number_input("High-water mark per unit", min_value=0.0, value=105.0, step=0.5)
    hurdle = c.number_input("Illustrative hurdle rate (%)", min_value=0.0, value=2.0, step=0.25)
    d, e = st.columns(2)
    rate = d.number_input("Performance-fee rate (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
    fee_units = e.number_input("Eligible units", min_value=0.0, value=100_000.0, step=5_000.0)
    result = performance_fee(current_price, high_water_mark, hurdle, rate, fee_units)
    metric_row(
        [
            ("Hurdle-adjusted reference", f"EUR {result['hurdle_level']:,.4f}", "High-water mark increased by the illustrative hurdle"),
            ("Eligible gain per unit", f"EUR {result['eligible_gain_per_unit']:,.4f}", "Positive excess over the hurdle-adjusted reference"),
            ("Illustrative performance fee", f"EUR {result['fee']:,.2f}", "Eligible gain multiplied by units and fee rate"),
        ]
    )
    with st.expander("Show the formula"):
        st.latex(r"Fee = \max(0, NAV_t - HWM(1+h)) \times units \times fee\ rate")

with systems:
    explain('records')
    st.subheader("Where the numbers come from")
    st.caption("The accounting record is checked against independent positions, cash, investor units and approved prices.")
    records = pd.DataFrame(
        [
            ["Investment-manager records", "Positions, orders and portfolio instructions", "Trade and position completeness"],
            ["Fund-accounting records", "General ledger, accruals and valuation records", "Balanced journals, accruals and Net Asset Value"],
            ["Custodian records", "Independent asset, settlement and cash records", "Position, transaction and cash confirmation"],
            ["Transfer-agent register", "Investor holdings, subscriptions, redemptions and units", "Validated units outstanding and dealing activity"],
            ["Market-data sources", "Security prices, foreign-exchange rates and reference data", "Approved source, timestamp and stale-price checks"],
        ],
        columns=["Record", "Purpose", "Control question"],
    )
    aligned_dataframe(records, hide_index=True, width="stretch")
    st.caption("For each source, the owner, valuation cut-off and reconciliation link must be clear.")

module_footer("fund_accounting", "app_pages/nav_production.py", "Continue to Net Asset Value production")
