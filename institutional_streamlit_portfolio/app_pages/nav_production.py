from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from ui import control_warning

from ui import result_metric

from ui import readable_chart

from ui import aligned_dataframe, aligned_editor

from learning import explain

from data import NAV_FOUNDATION_STEPS, synthetic_trades_for_fund
from domain import cash_forecast, valuation_fingerprint
from state import current_fund_breaks, invalidate_downstream, log_event, seed_positions, stage_at_least
from styles import AMBER, PRIMARY_GREEN
from ui import metric_row, module_footer, page_header, run_stage_bar
from valuation import Valuation


page_header(
    "FUND OPERATIONS / NAV EXAMPLE",
    "See how a fund price is prepared",
    "Run a sample Net Asset Value (NAV), inspect the result, then explore the checks behind it.",
    ":material/calculate:",
)
with st.expander("See review status"):
    run_stage_bar()


SCENARIOS = {
    "Baseline inputs": {
        "valuation": asdict(Valuation()),
        "cash": {"opening_cash": 18_000_000.0, "subscriptions": 5_000_000.0, "redemptions": 2_000_000.0, "purchase_settlements": 1_326_300.0, "sale_settlements": 1_228_000.0, "collateral": 350_000.0, "minimum_buffer_percent": 2.0},
        "stale": False,
        "purpose": "A normal day with no swing trigger and a positive projected cash balance.",
    },
    "Large redemption and cash stress": {
        "valuation": {**asdict(Valuation()), "flow": -20_000_000.0},
        "cash": {"opening_cash": 18_000_000.0, "subscriptions": 500_000.0, "redemptions": 20_500_000.0, "purchase_settlements": 1_326_300.0, "sale_settlements": 1_228_000.0, "collateral": 350_000.0, "minimum_buffer_percent": 2.0},
        "stale": False,
        "purpose": "Triggers a downward swing and a projected overdraft so the stated scenario has visible consequences.",
    },
    "Large subscription": {
        "valuation": {**asdict(Valuation()), "flow": 25_000_000.0},
        "cash": {"opening_cash": 18_000_000.0, "subscriptions": 25_500_000.0, "redemptions": 500_000.0, "purchase_settlements": 1_326_300.0, "sale_settlements": 1_228_000.0, "collateral": 350_000.0, "minimum_buffer_percent": 2.0},
        "stale": False,
        "purpose": "Triggers an upward swing under the configured illustrative policy.",
    },
    "Stale-price control failure": {
        "valuation": asdict(Valuation()),
        "cash": {"opening_cash": 18_000_000.0, "subscriptions": 5_000_000.0, "redemptions": 2_000_000.0, "purchase_settlements": 1_326_300.0, "sale_settlements": 1_228_000.0, "collateral": 350_000.0, "minimum_buffer_percent": 2.0},
        "stale": True,
        "purpose": "Keeps the arithmetic valid but blocks readiness because an approved current price is missing.",
    },
    "Accrued-expense stress": {
        "valuation": {**asdict(Valuation()), "expenses": 18_000_000.0},
        "cash": {"opening_cash": 18_000_000.0, "subscriptions": 5_000_000.0, "redemptions": 2_000_000.0, "purchase_settlements": 1_326_300.0, "sale_settlements": 1_228_000.0, "collateral": 350_000.0, "minimum_buffer_percent": 2.0},
        "stale": False,
        "purpose": "Shows how a larger recognized liability reduces total Net Asset Value and Net Asset Value per unit.",
    },
}

def _calculate_and_store(valuation_inputs: dict, cash_inputs: dict) -> None:
    """Apply the same calculation and audit transition to quick and detailed paths."""
    valuation_result = Valuation(**valuation_inputs).calculate()
    forecast_result = cash_forecast(**cash_inputs)
    current_inputs = {"valuation": valuation_inputs, "cash_forecast": cash_inputs}
    previous_inputs = st.session_state.last_calculated_inputs
    if previous_inputs is not None and previous_inputs != current_inputs:
        st.session_state.run_version += 1
        for row in current_fund_breaks():
            if row["Workflow status"] == "Accepted within policy tolerance":
                row["Workflow status"] = "Under investigation"
                st.session_state.resolutions.pop(row["Break ID"], None)
    st.session_state.valuation = valuation_inputs
    st.session_state.cash_forecast_inputs = cash_inputs
    valuation_result["cash_forecast"] = forecast_result
    st.session_state.valuation_result = valuation_result
    st.session_state.last_calculated_inputs = {
        "valuation": valuation_inputs.copy(),
        "cash_forecast": cash_inputs.copy(),
    }
    st.session_state.valuation_hash = valuation_fingerprint(st.session_state.context, current_inputs, valuation_result)
    st.session_state.run_stage = "Calculated"
    st.session_state.preparer = None
    st.session_state.checker = None
    st.session_state.review_checklist = {key: False for key in st.session_state.review_checklist}
    for channel in st.session_state.distribution_channels:
        channel["Status"] = "Queued"
    log_event(
        "Draft Net Asset Value calculated",
        "Calculated",
        "Synthetic fund-accounting preparer",
        f"Simulated Net Asset Value per unit for distribution: EUR {valuation_result['distribution_price']:.4f}.",
        st.session_state.valuation_hash,
    )


with st.container(border=True):
    st.markdown("**Start here · one-click example**")
    st.markdown("Run the sample with prepared figures. Then open **Read the result**. You can change the inputs or inspect individual holdings afterward.", text_alignment="left")
    if st.button("Run sample NAV", type="primary", icon=":material/play_arrow:"):
        try:
            _calculate_and_store(st.session_state.valuation.copy(), st.session_state.cash_forecast_inputs.copy())
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    if st.session_state.valuation_result:
        result_metric("Sample NAV per unit", f"EUR {st.session_state.valuation_result['distribution_price']:,.4f}", border=True)

inputs_tab, result_tab, controls_tab, positions_tab, foundation_tab = st.tabs(
    ["Adjust the example", "Read the result", "Review controls", "Explore positions", "How NAV is produced"]
)

with positions_tab:
    explain('positions')
    st.subheader("What makes up the investment value?")
    st.markdown("Change a holding's quantity, price or FX rate, then save the new total to the NAV inputs. This is the detailed route for exploring valuation controls.", text_alignment="left")
    edited_positions = aligned_editor(
        pd.DataFrame(st.session_state.valuation_positions),
        hide_index=True,
        width="stretch",
        num_rows="dynamic",
        key=f"position_valuation_editor_{st.session_state.get('position_editor_version', 0)}",
        column_config={
            "Instrument type": st.column_config.SelectboxColumn(options=["Listed equity", "Government bond", "Corporate bond", "Exchange-Traded Derivative", "Over-the-counter derivative", "Cash equivalent"], required=True),
            "Local currency": st.column_config.SelectboxColumn(options=["EUR", "USD", "GBP", "CHF", "JPY"], required=True),
            "Price status": st.column_config.SelectboxColumn(options=["Current", "Stale", "Missing"], required=True),
            "Quantity": st.column_config.NumberColumn(format="localized", min_value=0.0),
            "Local price": st.column_config.NumberColumn(format="%.6f", min_value=0.0),
            "FX rate to EUR": st.column_config.NumberColumn(format="%.6f", min_value=0.000001),
        },
    )
    valued_positions = edited_positions.copy()
    numeric_columns = ["Quantity", "Local price", "FX rate to EUR"]
    for column in numeric_columns:
        valued_positions[column] = pd.to_numeric(valued_positions[column], errors="coerce")
    position_errors = []
    if valued_positions.empty:
        position_errors.append("At least one position is required.")
    if valued_positions["Position ID"].isna().any() or (valued_positions["Position ID"].astype(str).str.strip() == "").any():
        position_errors.append("Every row needs a position identifier.")
    if valued_positions["Position ID"].duplicated().any():
        position_errors.append("Position identifiers must be unique.")
    if valued_positions["Price timestamp"].isna().any():
        position_errors.append("Every position needs a price timestamp in UTC.")
    price_dates = []
    if not position_errors:
        try:
            price_dates = [
                datetime.strptime(str(value), "%Y-%m-%d %H:%M UTC").date()
                for value in valued_positions["Price timestamp"]
            ]
        except ValueError:
            position_errors.append("Price timestamps must use YYYY-MM-DD HH:MM UTC.")
    if valued_positions[numeric_columns].isna().any().any():
        position_errors.append("Quantity, local price and foreign-exchange rate must be numeric.")
    elif (valued_positions["FX rate to EUR"] <= 0).any():
        position_errors.append("Every foreign-exchange rate must be greater than zero.")
    if not position_errors:
        valued_positions["Local market value"] = valued_positions["Quantity"] * valued_positions["Local price"]
        valued_positions["Base-currency market value (EUR)"] = valued_positions["Local market value"] * valued_positions["FX rate to EUR"]
        portfolio_total = float(valued_positions["Base-currency market value (EUR)"].sum())
        current_prices = sum(
            status == "Current" and source_date == st.session_state.context["valuation_date"]
            for status, source_date in zip(valued_positions["Price status"], price_dates)
        )
        metric_row(
            [
                ("Positions", f"{len(valued_positions):,}", "Position-grain rows in the current roll-up"),
                ("Current prices", f"{current_prices}/{len(valued_positions)}", "Rows explicitly marked current"),
                ("Portfolio market value", f"EUR {portfolio_total:,.2f}", "Quantity × local price × foreign-exchange rate to EUR"),
            ]
        )
        aligned_dataframe(valued_positions, hide_index=True, width="stretch")
    else:
        for error in position_errors:
            st.error(error)
        portfolio_total = 0.0
    if st.button("Use this position roll-up in the NAV", type="primary", icon=":material/sync_alt:", disabled=bool(position_errors)):
        input_columns = [column for column in edited_positions.columns if column in st.session_state.valuation_positions[0]]
        st.session_state.valuation_positions = edited_positions[input_columns].to_dict("records")
        st.session_state.valuation["portfolio"] = portfolio_total
        st.session_state.quality_inputs["stale_price"] = current_prices != len(valued_positions)
        st.session_state.quality_inputs["price_source_received"] = not bool((valued_positions["Price status"] == "Missing").any())
        invalidate_downstream("The position-level valuation roll-up changed the portfolio input; recalculation is required.", keep_calculation=False)
        log_event("Position valuation rolled into NAV inputs", "Recorded", "Synthetic fund-accounting preparer", f"{len(valued_positions)} positions; EUR {portfolio_total:,.2f}.")
        st.rerun()

with inputs_tab:
    explain('nav')
    st.caption("This example treats each fictional fund as one share class. Its assets, liabilities and units refer to that same class.")
    st.subheader("Choose an example day")
    scenario = st.selectbox("Valuation scenario", list(SCENARIOS), key="nav_scenario")
    st.caption(SCENARIOS[scenario]["purpose"])
    if st.button("Apply scenario inputs", icon=":material/tune:"):
        selected = SCENARIOS[scenario]
        st.session_state.valuation = selected["valuation"].copy()
        st.session_state.valuation_positions = seed_positions(
            st.session_state.context["fund"], st.session_state.context["valuation_date"]
        )
        if selected["stale"]:
            st.session_state.valuation_positions[0]["Price status"] = "Stale"
        st.session_state.position_editor_version = st.session_state.get("position_editor_version", 0) + 1
        st.session_state.cash_forecast_inputs = selected["cash"].copy()
        st.session_state.quality_inputs = {
            "stale_price": selected["stale"],
            "unit_register_received": True,
            "price_source_received": True,
            "cash_reconciled": True,
            "minimum_cash_buffer_percent": selected["cash"]["minimum_buffer_percent"],
        }
        invalidate_downstream(f"Scenario applied: {scenario}.", keep_calculation=False)
        st.rerun()

    st.subheader("Adjust the figures")
    st.caption("The prefilled values are ready to calculate. Change only what you want to explore.")
    v = st.session_state.valuation
    cash = st.session_state.cash_forecast_inputs
    with st.form("nav_inputs"):
        assets_col, liability_col = st.columns(2, gap="large")
        with assets_col:
            st.markdown("**Assets and share-class units**")
            portfolio = st.number_input("Investments at current valuation (EUR)", min_value=0.0, value=float(v["portfolio"]), step=1_000_000.0)
            ledger_cash = st.number_input("Cash recognized in the accounting ledger (EUR)", min_value=0.0, value=float(v["cash"]), step=250_000.0)
            receivables = st.number_input("Receivables and accrued income (EUR)", min_value=0.0, value=float(v["receivables"]), step=100_000.0)
            units = st.number_input("Units outstanding for this illustrative share class", min_value=1.0, value=float(v["units"]), step=10_000.0)
        with liability_col:
            st.markdown("**Liabilities and anti-dilution policy**")
            payables = st.number_input("Trade and other payables (EUR)", min_value=0.0, value=float(v["payables"]), step=100_000.0)
            expenses = st.number_input("Accrued fees and other expenses payable (EUR)", min_value=0.0, value=float(v["expenses"]), step=100_000.0)
            swing = st.toggle("Evaluate the illustrative swing-pricing policy", value=bool(v["swing"]))
            threshold = st.slider("Net-dealing trigger as percentage of unswung Net Asset Value", 0.5, 10.0, float(v["threshold"]), 0.1)
            bps = st.slider("Documented swing factor (bps)", 0, 100, int(v["bps"]), 5)

        st.markdown("**Investor dealing and forward cash forecast**")
        c1, c2, c3 = st.columns(3)
        subscriptions = c1.number_input("Subscriptions expected (EUR)", min_value=0.0, value=float(cash["subscriptions"]), step=500_000.0)
        redemptions = c2.number_input("Redemptions expected (EUR)", min_value=0.0, value=float(cash["redemptions"]), step=500_000.0)
        opening_cash = c3.number_input("Opening settled cash (EUR)", min_value=0.0, value=float(cash["opening_cash"]), step=250_000.0)
        c4, c5, c6, c7 = st.columns(4)
        purchases = c4.number_input("Purchase settlements (EUR)", min_value=0.0, value=float(cash["purchase_settlements"]), step=100_000.0)
        sales = c5.number_input("Sale settlements (EUR)", min_value=0.0, value=float(cash["sale_settlements"]), step=100_000.0)
        collateral = c6.number_input("Collateral and margin outflow (EUR)", min_value=0.0, value=float(cash["collateral"]), step=50_000.0)
        buffer = c7.number_input("Illustrative minimum cash buffer (%)", min_value=0.0, max_value=100.0, value=float(cash["minimum_buffer_percent"]), step=0.5)
        submitted = st.form_submit_button("Calculate draft Net Asset Value", type="primary", icon=":material/calculate:", width="stretch")

    with st.expander("Why are there two cash figures?"):
        st.markdown("Ledger cash is an accounting balance. Forecast cash includes expected investor dealing and settlements, so it helps assess liquidity without changing the ledger automatically.", text_alignment="left")
    if submitted:
        valuation_inputs = {
            "portfolio": portfolio,
            "cash": ledger_cash,
            "receivables": receivables,
            "payables": payables,
            "expenses": expenses,
            "units": units,
            "flow": subscriptions - redemptions,
            "threshold": threshold,
            "bps": bps,
            "swing": swing,
        }
        cash_inputs = {
            "opening_cash": opening_cash,
            "subscriptions": subscriptions,
            "redemptions": redemptions,
            "purchase_settlements": purchases,
            "sale_settlements": sales,
            "collateral": collateral,
            "minimum_buffer_percent": buffer,
        }
        try:
            _calculate_and_store(valuation_inputs, cash_inputs)
            st.success("Sample NAV calculated. Open **Read the result** to see what changed.")
        except ValueError as exc:
            st.error(str(exc))

with result_tab:
    explain('swing')
    if not st.session_state.valuation_result:
        st.info("Select **Run sample NAV** above, or adjust the figures and calculate in the first tab.")
    else:
        r = st.session_state.valuation_result
        metric_row(
            [
                ("Total assets", f"EUR {r['assets']/1_000_000:,.3f}m", "Investments plus ledger cash plus receivables and accrued income"),
                ("Total liabilities", f"EUR {r['liabilities']/1_000_000:,.3f}m", "Payables plus accrued fees and other expenses"),
                ("Total Net Asset Value", f"EUR {r['nav']/1_000_000:,.3f}m", "Total assets less total liabilities"),
                ("Simulated NAV per unit for distribution", f"EUR {r['distribution_price']:,.4f}", "Unswung Net Asset Value per unit, adjusted only if the configured swing policy triggers"),
            ]
        )
        st.caption("Assets less liabilities determine total NAV. Divide by units to get the unswung price; the sample policy may then adjust the simulated distribution price.")
        bridge = pd.DataFrame(
            {
                "Component": ["Investments", "Ledger cash", "Receivables and accrued income", "Payables", "Accrued fees and expenses"],
                "Amount (EUR)": [st.session_state.valuation["portfolio"], st.session_state.valuation["cash"], st.session_state.valuation["receivables"], -st.session_state.valuation["payables"], -st.session_state.valuation["expenses"]],
            }
        )
        chart = alt.Chart(bridge).mark_bar().encode(
            x=alt.X("Amount (EUR):Q", title="Contribution to Net Asset Value (EUR)"),
            y=alt.Y("Component:N", sort=None, title=None),
            color=alt.condition(alt.datum["Amount (EUR)"] < 0, alt.value(AMBER), alt.value(PRIMARY_GREEN)),
            tooltip=["Component", alt.Tooltip("Amount (EUR):Q", format=",.2f")],
        )
        readable_chart(chart, width="stretch")
        if r["triggered"]:
            control_warning(f"The example swing policy applies a {r['direction'].lower()} adjustment of {st.session_state.valuation['bps']} bps. The simulated price is EUR {r['distribution_price']:,.4f}.")
        else:
            st.success("The example swing policy did not trigger. The simulated price equals the unswung price.")
        with st.expander("See the calculation and swing rule"):
            st.latex(r"NAV = Investments + Cash + Receivables - Payables - Accrued\ expenses")
            st.latex(r"NAV\ per\ unit = \frac{NAV}{validated\ units\ outstanding}")
            st.markdown(f"Unswung NAV per unit: **EUR {r['price']:,.4f}**. Net dealing is **{r['flow_pct']:.2f}%** of unswung NAV; this example triggers at **{st.session_state.valuation['threshold']:.2f}%**.")
            st.caption("This is a user-configured teaching rule, not a universal regulatory threshold. A basis point is 0.01%; the plural abbreviation is bps.")
        forecast = r["cash_forecast"]
        st.subheader("Cash forecast and liquidity ladder")
        explain('cash')
        metric_row(
            [
                ("Projected settled cash", f"EUR {forecast['projected_cash']:,.2f}", "Opening cash plus subscriptions, less redemptions and purchases, plus sales, less collateral"),
                ("Illustrative buffer", f"EUR {forecast['required_buffer']:,.2f}", "User-configured percentage of opening settled cash"),
                ("Headroom after buffer", f"EUR {forecast['buffer_headroom']:,.2f}", "Projected cash less the illustrative buffer"),
                ("Forecast status", str(forecast["status"]), "A forecast signal, not a ledger balance or regulatory compliance conclusion"),
            ]
        )
        with st.expander("See the synthetic trades behind the forecast"):
            aligned_dataframe(
                pd.DataFrame(synthetic_trades_for_fund(st.session_state.context["fund"])),
                hide_index=True,
                width="stretch",
            )

with controls_tab:
    if st.session_state.get("readiness_notice"):
        st.success(st.session_state.pop("readiness_notice"))
    explain('quality')
    st.subheader("Source-readiness controls")
    st.markdown("These controls apply to the current run and version. Saving a change invalidates any later review or approval.", text_alignment="left")
    qi = st.session_state.quality_inputs
    with st.form("quality_inputs_form"):
        prices = st.checkbox("Approved price source received for the valuation point", value=qi["price_source_received"])
        units_ready = st.checkbox("Transfer-agent unit register received and validated", value=qi["unit_register_received"])
        cash_ready = st.checkbox("Ledger cash reconciled to the bank or custodian record", value=qi["cash_reconciled"])
        stale = st.checkbox("At least one required security price is stale or unavailable", value=qi["stale_price"])
        quality_saved = st.form_submit_button("Save source-readiness assessment")
    if quality_saved:
        updated = {**qi, "price_source_received": prices, "unit_register_received": units_ready, "cash_reconciled": cash_ready, "stale_price": stale}
        if updated != qi:
            st.session_state.quality_inputs = updated
            invalidate_downstream("Source-readiness assessment changed after calculation.", keep_calculation=True)
        st.session_state.readiness_notice = "Source-readiness assessment saved. Lifecycle status and review eligibility have been refreshed."
        st.rerun()

    issues = []
    if not st.session_state.valuation_result:
        issues.append("Draft Net Asset Value has not been calculated.")
    position_total = sum(
        float(row["Quantity"]) * float(row["Local price"]) * float(row["FX rate to EUR"])
        for row in st.session_state.valuation_positions
    )
    if abs(st.session_state.valuation["portfolio"] - position_total) > 0.01:
        issues.append("The investment balance does not agree with the saved position-level valuation roll-up.")
    if not st.session_state.quality_inputs["price_source_received"] or st.session_state.quality_inputs["stale_price"]:
        issues.append("Approved current prices are incomplete or stale.")
    if any(
        row["Price status"] != "Current"
        or datetime.strptime(row["Price timestamp"], "%Y-%m-%d %H:%M UTC").date() != st.session_state.context["valuation_date"]
        for row in st.session_state.valuation_positions
    ):
        issues.append("The saved position-level prices are not all current for the selected valuation date.")
    if not st.session_state.quality_inputs["unit_register_received"]:
        issues.append("Validated share-class units are missing.")
    if not st.session_state.quality_inputs["cash_reconciled"]:
        issues.append("Ledger cash has not been reconciled.")
    unresolved = current_fund_breaks(include_resolved=False)
    if unresolved:
        issues.append(f"{len(unresolved)} run-linked reconciliation exception(s) remain open.")
    if st.session_state.valuation_result and st.session_state.valuation_result["cash_forecast"]["status"] != "Sufficient":
        issues.append(f"The cash forecast status is {st.session_state.valuation_result['cash_forecast']['status'].lower()}.")

    if issues:
        st.error("Before review, address:\n\n" + "\n".join(f"- {issue}" for issue in issues), icon=":material/block:")
        if unresolved and st.button("Open reconciliation controls", icon=":material/rule:"):
            st.switch_page("app_pages/reconciliation.py")
    else:
        st.success("Calculation, source data, cash forecast and run-linked reconciliation are ready for preparer review.")
        if st.button("Confirm reconciliation and source readiness", type="primary", disabled=stage_at_least("Reconciliation cleared")):
            st.session_state.run_stage = "Reconciliation cleared"
            log_event("Reconciliation and source readiness confirmed", "Ready for preparer review", "Synthetic fund-accounting preparer", "All run-linked readiness controls were clear for the current version.")
            st.rerun()
    st.page_link("app_pages/governance.py", label="Continue to preparer and checker review", icon=":material/verified_user:")

with foundation_tab:
    explain('records')
    st.subheader("Ten-stage Net Asset Value control chain")
    control_chain = {
        "01 Fund setup": ("Client implementation and application support", "Fund rules, calendar, share class and approved sources", "Configuration completeness and ownership", "Production-ready fund reference"),
        "02 Transactions": ("Transaction operations", "Trades, investor dealing and cash movements", "Trade capture, cut-off and settlement validation", "Booked transaction population"),
        "03 Pricing": ("Pricing and valuation operations", "Security prices and foreign-exchange rates", "Source, timestamp, staleness and override controls", "Approved valuation inputs"),
        "04 Reconciliation": ("Reconciliation control", "Accounting, custodian and investment-manager records", "Matched population, breaks, ageing and evidence", "Cleared or escalated differences"),
        "05 Pre-NAV checks": ("Fund-accounting preparer", "Source-readiness and exception flags", "Reviewable warnings versus blocking exceptions", "Decision to proceed or investigate"),
        "06 Simulation": ("Fund accounting", "Controlled positions, cash, accruals and units", "Draft calculation and reasonableness review", "Draft Net Asset Value"),
        "07 Accounting": ("Fund accounting", "Validated adjustments and journal entries", "Balanced ledger and rerun controls", "Accounting Net Asset Value package"),
        "08 Control and sign-off": ("Independent valuation control", "Calculation, breaks, evidence and checklist", "Maker-checker authorization", "Approved package"),
        "09 Client submission": ("Client Account Manager and operations", "Approved price and evidence package", "Submission cut-off, queries and acknowledgement", "Client-acknowledged submission"),
        "10 Price distribution": ("Controlled distribution service", "Approved simulated price", "Recipient status, retry and retention", "Acknowledged downstream release"),
    }
    selected_stage = st.selectbox("Inspect a control-chain stage", list(control_chain))
    owner, stage_input, control, output = control_chain[selected_stage]
    with st.container(key="nav_control_chain_cards"):
        metric_row(
            [
                ("Accountable function", owner, "Illustrative operating ownership"),
                ("Required input", stage_input, "Information needed before the stage can run"),
                ("Control", control, "Evidence or decision applied at the stage"),
                ("Output", output, "Result passed to the next stage"),
            ]
        )
    exception_type = st.segmented_control("Stage outcome", ["Clear", "Reviewable warning", "Blocking exception"], default="Clear")
    if exception_type == "Clear":
        st.success("The stage can pass its controlled output forward.")
    elif exception_type == "Reviewable warning":
        control_warning("The stage may proceed only after a named reviewer records evidence and a justification under the applicable policy.")
    else:
        st.error("The workflow stops. Investigate the cause, correct the source or accounting record, re-run the control and obtain approval before release.")
    with st.expander("Expanded twelve-step technical valuation model"):
        for number, title, explanation in NAV_FOUNDATION_STEPS:
            st.markdown(f"**{number} · {title}** — {explanation}")

module_footer("nav_production", "app_pages/reconciliation.py", "Continue to reconciliation controls")
