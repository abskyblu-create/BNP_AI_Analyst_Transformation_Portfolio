from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd
import streamlit as st

from ui import aligned_dataframe

from learning import explain

from state import current_fund_breaks, invalidate_downstream, log_event
from ui import metric_row, module_footer, page_header, run_stage_bar


page_header(
    "FUND OPERATIONS / RECONCILIATION",
    "What happens when records do not agree?",
    "Explore a sample difference, record the evidence and see how that decision affects the NAV review.",
    ":material/rule:",
)
with st.expander("See review status"):
    run_stage_bar()

st.markdown("**Reconciliation procedure:** Select a difference, compare the three source records and record a verified reason and action.", text_alignment="justify")
st.caption("This example compares fund accounting, custodian and investment-manager records. Real source choices depend on the control.")

scope = st.segmented_control("Register scope", ["Current valuation run", "Enterprise demonstration register"], default="Current valuation run")
current_scope = scope == "Current valuation run"
rows = current_fund_breaks() if current_scope else st.session_state.breaks
df = pd.DataFrame(rows)
unresolved_all = [row for row in st.session_state.breaks if row["Workflow status"] not in {"Resolved", "Accepted within policy tolerance"}]
unresolved_current = current_fund_breaks(include_resolved=False)
gross_current = sum(row["Amount under investigation (EUR)"] for row in unresolved_current)
estimated_impact = sum(row["Impact (basis points)"] for row in unresolved_current)
metric_row(
    [
        ("Run-linked open exceptions", str(len(unresolved_current)), "Only these exceptions can block the selected valuation run"),
        ("Gross amount under investigation", f"EUR {gross_current:,.2f}", "Sum of run-linked amounts being investigated; it is not automatically a loss or accounting difference"),
        ("Estimated NAV impact", f"{estimated_impact:.2f} bps", "Illustrative source estimate, requiring analyst validation"),
        ("Enterprise open exceptions", str(len(unresolved_all)), "Open cases across all synthetic funds; unrelated cases do not block this run"),
    ]
)

if df.empty:
    st.info("No cases are available for this scope.")
else:
    display_columns = ["Break ID", "Fund", "Instrument", "Difference type", "Source currency", "Amount under investigation (EUR)", "Impact (basis points)", "Age (days)", "Workflow status", "Severity"]
    aligned_dataframe(
        df[display_columns],
        hide_index=True,
        width="stretch",
        column_config={
            "Amount under investigation (EUR)": st.column_config.NumberColumn(format="localized"),
            "Impact (basis points)": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.download_button("Download visible reconciliation register", df.to_csv(index=False), "reconciliation-register.csv", "text/csv", icon=":material/download:")

st.subheader("Resolve a sample difference")
explain('reconciliation')
st.caption("Compare the amounts, then document what you verified.")
if not current_scope:
    st.info("The enterprise register is read-only. Select the relevant fund in the navigation rail to record a disposition within its own valuation run.", icon=":material/lock:")
if rows:
    selected_id = st.selectbox("Exception identifier", [row["Break ID"] for row in rows], key="recon_selected_break")
    item = next(row for row in st.session_state.breaks if row["Break ID"] == selected_id)
    with st.container(border=True):
        st.markdown(f"**{item['Fund']} · {item['Instrument']}**")
        st.caption(f"{item['Difference type']} · {item['Control layer']} · {item['Severity']} severity")
        source_df = pd.DataFrame(
            [
                ["Fund-accounting record", item["Fund accounting amount"]],
                ["Custodian record", item["Custodian amount"]],
                ["Investment-manager record", item["Investment manager amount"]],
            ],
            columns=["Compared source", f"Amount ({item['Source currency']})"],
        )
        aligned_dataframe(source_df, hide_index=True, width="stretch")
        st.markdown(f"**Suspected cause:** {item['Root cause']}")
        st.caption("A suspected cause becomes a confirmed cause only after the analyst obtains supporting evidence.")
        if selected_id in st.session_state.resolutions:
            st.success("A disposition has been recorded for this session.")
            st.json(st.session_state.resolutions[selected_id], expanded=True)

    disposition = st.selectbox(
        "Proposed disposition",
        [
            "Confirm matched after evidence",
            "Accept within documented policy tolerance",
            "Post accounting correction and require recalculation",
            "Request correction from an external source",
            "Escalate and place the valuation on hold",
        ],
    )
    with st.form("resolution_form"):
        confirmed_cause = st.text_area("Confirmed root cause", placeholder="State what happened, which record was wrong and why.")
        action = st.text_area("Corrective or follow-up action", placeholder="Describe the action performed or requested and the verification required.")
        a, b, c = st.columns(3)
        owner = a.selectbox("Accountable owner", ["Fund-accounting preparer", "Reconciliation analyst", "Custodian liaison", "Investment-manager liaison", "Valuation controller"])
        evidence = b.text_input("Evidence reference", placeholder="Example: CASE-204 / statement page 3")
        policy_reference = c.text_input("Tolerance or procedure reference", placeholder="Required for tolerance acceptance")
        adjustment_target = "No accounting adjustment"
        adjustment_direction = "No change"
        adjustment_amount = 0.0
        if disposition == "Post accounting correction and require recalculation":
            adjustment_target = st.selectbox("Accounting input to correct", ["Investments", "Ledger cash", "Receivables and accrued income", "Payables", "Accrued fees and other expenses"])
            adjustment_direction = st.segmented_control("Correction direction", ["Increase", "Decrease"], default="Increase")
            adjustment_amount = st.number_input("Absolute correction amount (EUR)", min_value=0.01, value=1_000.0, step=500.0)
        submitted = st.form_submit_button("Record disposition", type="primary", icon=":material/fact_check:", disabled=not current_scope)

    if submitted:
        errors = []
        if len(confirmed_cause.strip()) < 20:
            errors.append("Provide a specific confirmed cause of at least 20 characters.")
        if len(action.strip()) < 20:
            errors.append("Provide a specific action of at least 20 characters.")
        if len(evidence.strip()) < 4:
            errors.append("Provide an evidence reference.")
        if disposition == "Accept within documented policy tolerance":
            if item["Impact (basis points)"] > 0.50:
                errors.append("This case exceeds the demonstration tolerance of 0.50 basis points and cannot be accepted through this route.")
            if len(policy_reference.strip()) < 4:
                errors.append("Tolerance acceptance requires a documented policy reference.")
        adjustment_key = None
        signed_adjustment = 0.0
        if disposition == "Post accounting correction and require recalculation":
            adjustment_key = {
                "Investments": "portfolio",
                "Ledger cash": "cash",
                "Receivables and accrued income": "receivables",
                "Payables": "payables",
                "Accrued fees and other expenses": "expenses",
            }[adjustment_target]
            signed_adjustment = adjustment_amount if adjustment_direction == "Increase" else -adjustment_amount
            if st.session_state.valuation[adjustment_key] + signed_adjustment < 0:
                errors.append("The correction would make the selected accounting balance negative.")
        if errors:
            for error in errors:
                st.error(error)
        else:
            new_status = {
                "Confirm matched after evidence": "Resolved",
                "Accept within documented policy tolerance": "Accepted within policy tolerance",
                "Post accounting correction and require recalculation": "Resolved",
                "Request correction from an external source": "Awaiting verification",
                "Escalate and place the valuation on hold": "Escalated",
            }[disposition]
            for row in st.session_state.breaks:
                if row["Break ID"] == selected_id:
                    row["Workflow status"] = new_status
            record = {
                "Run ID": st.session_state.run_id,
                "Run version at decision": st.session_state.run_version,
                "Recorded at (UTC)": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "Disposition": disposition,
                "Status": new_status,
                "Confirmed cause": confirmed_cause.strip(),
                "Action": action.strip(),
                "Owner": owner,
                "Evidence reference": evidence.strip(),
                "Procedure reference": policy_reference.strip(),
                "Accounting adjustment": {"Target": adjustment_target, "Direction": adjustment_direction, "Signed amount (EUR)": signed_adjustment},
            }
            st.session_state.resolutions[selected_id] = record
            if disposition == "Post accounting correction and require recalculation":
                before = st.session_state.valuation[adjustment_key]
                st.session_state.valuation[adjustment_key] = before + signed_adjustment
                record["Accounting adjustment"].update({"Before (EUR)": before, "After (EUR)": st.session_state.valuation[adjustment_key]})
                invalidate_downstream(f"Accounting correction from {selected_id} changed {adjustment_target}; recalculation is required.", keep_calculation=False)
            else:
                invalidate_downstream(f"Reconciliation disposition for {selected_id} changed to {new_status}.", keep_calculation=True)
            log_event("Reconciliation disposition recorded", new_status, owner, f"{selected_id}; {disposition}; evidence {evidence.strip()}.")
            st.success("Disposition recorded and later lifecycle decisions invalidated where applicable.")
            st.rerun()

    if item["Workflow status"] in {"Resolved", "Accepted within policy tolerance"}:
        if st.button("Reopen this exception", icon=":material/replay:", disabled=not current_scope):
            item["Workflow status"] = "Under investigation"
            invalidate_downstream(f"Reconciliation exception {selected_id} was reopened.", keep_calculation=True)
            log_event("Reconciliation exception reopened", "Open", "Reconciliation analyst", selected_id)
            st.rerun()

st.subheader("Scenario injection")
st.caption("Add one run-linked exception to test how later review is invalidated.")
if st.button("Inject a synthetic stale-price exception", icon=":material/add_alert:", disabled=not current_scope):
    new_id = f"BRK-{uuid4().hex[:6].upper()}"
    st.session_state.breaks.append(
        {
            "Break ID": new_id,
            "Fund": st.session_state.context["fund"],
            "Instrument": "Synthetic listed equity",
            "Difference type": "Price tolerance breach",
            "Source currency": "EUR",
            "Fund accounting amount": 2_450_000.0,
            "Custodian amount": 2_380_000.0,
            "Investment manager amount": 2_450_000.0,
            "Amount under investigation (EUR)": 70_000.0,
            "Impact (basis points)": 0.75,
            "Age (days)": 1,
            "Workflow status": "Open",
            "Severity": "Critical",
            "Root cause": "The accounting price differs from the independent source beyond the configured tolerance.",
            "Control layer": "Accounting price versus independent market-data source",
        }
    )
    st.session_state.quality_inputs["stale_price"] = True
    invalidate_downstream(f"New run-linked exception {new_id} was created.", keep_calculation=True)
    log_event("Synthetic exception injected", "Open", "System", new_id)
    st.rerun()

if not current_fund_breaks(include_resolved=False):
    st.success("All run-linked exceptions have a resolved or accepted disposition. Return to Net Asset Value production to confirm the remaining source-readiness controls.")
    st.page_link("app_pages/nav_production.py", label="Return to readiness controls", icon=":material/calculate:")

module_footer("reconciliation", "app_pages/data_reporting.py", "Continue to data and reporting")
