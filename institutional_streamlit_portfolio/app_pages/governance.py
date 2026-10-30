from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math

import pandas as pd
import streamlit as st

from ui import control_warning

from ui import aligned_dataframe, aligned_editor

from learning import explain

from data import QUALITY_GATES
from state import RUN_STAGES, control_package_fingerprint, invalidate_downstream, log_event, session_export, stage_at_least
from ui import metric_row, module_footer, page_header, run_stage_bar


page_header(
    "PROJECT DEMO / REVIEW AND DELIVERY",
    "From calculated value to checked result",
    "This fictional workflow shows how a preparer reviews a fund value, an independent checker approves it and a distribution step records the outcome.",
    ":material/verified_user:",
)
run_stage_bar()
if st.session_state.get("review_notice"):
    st.success(st.session_state.pop("review_notice"))

next_action = {
    "Draft": "Start in the Net Asset Value workbench: calculate a draft value, then clear its reconciliation exceptions.",
    "Calculated": "Open the Net Asset Value and reconciliation workbenches to clear the run before preparer review.",
    "Reconciliation cleared": "Use the Review tab: save the five checks, then complete the preparer review.",
    "Preparer reviewed": "Use the Review tab: make the independent checker decision.",
    "Checker approved": "Use the Distribution tab to simulate delivery of the checked price.",
    "Publication simulated": "The demonstration run is complete. Explore the other tabs or start a new valuation run.",
}
st.info(next_action.get(st.session_state.run_stage, "Review the current run status before continuing."), icon=":material/arrow_forward:")
st.caption("All identities, funds, recipients and records here are synthetic. Actions update only this browser session.")

review_tab, client_tab, distribution_tab, resilience_tab, delivery_tab, log_tab = st.tabs(
    ["Review", "Client timing", "Distribution", "Continuity exercise", "Mission delivery", "Session record"]
)

PREPARERS = [
    "Synthetic Preparer One · Fund accounting",
    "Synthetic Preparer Two · Senior fund accounting",
]
CHECKERS = [
    "Synthetic Checker One · Valuation control",
    "Synthetic Checker Two · Independent oversight",
]

with review_tab:
    explain('review')
    st.subheader("Review the current valuation")
    st.caption("The preparer checks the source and exceptions first. The checker then makes a separate decision for this run version.")
    result = st.session_state.valuation_result
    metric_row(
        [
            ("Run and version", f"{st.session_state.run_id} / v{st.session_state.run_version}", "Every decision below applies only to this run version"),
            ("Current lifecycle status", st.session_state.run_stage, "Later decisions are invalidated after material input or exception changes"),
            ("Simulated NAV per unit for distribution", f"EUR {result['distribution_price']:,.4f}" if result else "Not calculated", "Carries the policy-adjusted price when swing pricing triggers"),
        ]
    )
    with st.expander("Technical run fingerprint"):
        st.code(st.session_state.valuation_hash or "Not available")
        st.caption("SHA-256 digest of the current calculation inputs and result; it is not a digital signature.")
    checklist_labels = {
        "sources": "All expected positions, trades, cash and corporate-action sources were received",
        "prices": "Price and foreign-exchange sources and timestamps were reviewed",
        "accruals": "Income, tax, fees, payables and other accruals were reviewed",
        "units": "Share-class units and investor dealing were validated",
        "exceptions": "All run-linked exceptions have a documented resolved or tolerated disposition",
    }
    with st.form("review_checklist_form"):
        updated_checklist = {}
        for key, label in checklist_labels.items():
            updated_checklist[key] = st.checkbox(label, value=st.session_state.review_checklist[key])
        checklist_saved = st.form_submit_button("Save preparer checklist")
    if checklist_saved:
        if updated_checklist != st.session_state.review_checklist and stage_at_least("Preparer reviewed"):
            invalidate_downstream("The preparer checklist changed after review.", keep_calculation=True)
        st.session_state.review_checklist = updated_checklist
        log_event("Preparer checklist saved", "Complete" if all(updated_checklist.values()) else "Incomplete", "Synthetic fund-accounting preparer", f"{sum(updated_checklist.values())} of {len(updated_checklist)} checks selected.")
        st.session_state.review_notice = "Checklist saved. Review eligibility and lifecycle status have been refreshed."
        st.rerun()

    preparer = st.selectbox("Synthetic preparer identity", PREPARERS, index=0)
    ready_for_preparer = st.session_state.run_stage == "Reconciliation cleared" and all(st.session_state.review_checklist.values())
    if not ready_for_preparer and not stage_at_least("Preparer reviewed"):
        control_warning("Preparer review requires Reconciliation cleared status and all five checklist items.")
    if st.button("Mark preparer review complete", type="primary", disabled=not ready_for_preparer):
        st.session_state.preparer = {
            "Actor": preparer,
            "Time (UTC)": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "Run version": st.session_state.run_version,
            "Calculation fingerprint": st.session_state.valuation_hash,
            "Control package fingerprint": control_package_fingerprint(),
        }
        st.session_state.run_stage = "Preparer reviewed"
        log_event("Preparer review completed", "Prepared", preparer, "Checklist completed for the current run version.")
        st.rerun()

    if st.session_state.preparer:
        st.success(f"Prepared by {st.session_state.preparer['Actor']} at {st.session_state.preparer['Time (UTC)']}.")
        checker = st.selectbox("Synthetic independent checker identity", CHECKERS, index=0)
        checker_attests = st.checkbox("Confirm checker review of the current calculation, checklist and exception dispositions represented by the control-package fingerprint.")
        version_mismatch = (
            st.session_state.preparer["Run version"] != st.session_state.run_version
            or st.session_state.preparer["Control package fingerprint"] != control_package_fingerprint()
        )
        if version_mismatch:
            st.error("The preparer record belongs to an earlier run version. Repeat preparer review.")
        elif st.session_state.run_stage == "Preparer reviewed" and not checker_attests:
            st.info("Select the checker review confirmation above to enable independent checker approval.")
        if st.button("Simulate independent checker approval", disabled=st.session_state.run_stage != "Preparer reviewed" or version_mismatch or not checker_attests):
            st.session_state.checker = {
                "Actor": checker,
                "Time (UTC)": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "Run version": st.session_state.run_version,
                "Calculation fingerprint": st.session_state.valuation_hash,
                "Control package fingerprint": control_package_fingerprint(),
            }
            st.session_state.run_stage = "Checker approved"
            log_event("Independent checker approval simulated", "Approved", checker, "Approval applies to the current control-package fingerprint; no identity authentication occurred.")
            st.rerun()
    if st.session_state.checker:
        st.success(f"Checker approval simulated by {st.session_state.checker['Actor']} at {st.session_state.checker['Time (UTC)']}.")

with client_tab:
    explain('delivery')
    st.subheader("Compare submission and distribution timing")
    st.markdown("Change the four times to see whether a client submission or later price distribution misses its cut-off. They are separate delivery steps.", text_alignment="justify")
    valuation_date = st.session_state.context["valuation_date"]
    c1, c2, c3, c4 = st.columns(4)
    submission_cutoff = c1.time_input("Client submission cut-off", value=datetime.strptime("17:00", "%H:%M").time())
    submission_actual = c2.time_input("Client submission actual", value=datetime.strptime("16:52", "%H:%M").time())
    distribution_cutoff = c3.time_input("Price distribution cut-off", value=datetime.strptime("18:00", "%H:%M").time())
    distribution_actual = c4.time_input("Price distribution actual", value=datetime.strptime("18:05", "%H:%M").time())
    submission_variance = int((datetime.combine(valuation_date, submission_actual) - datetime.combine(valuation_date, submission_cutoff)).total_seconds() / 60)
    distribution_variance = int((datetime.combine(valuation_date, distribution_actual) - datetime.combine(valuation_date, distribution_cutoff)).total_seconds() / 60)
    metric_row(
        [
            ("Client submission", "On time" if submission_variance <= 0 else "Late", f"Actual minus cut-off: {submission_variance:+d} minutes"),
            ("Submission variance", f"{submission_variance:+d} min", "Negative means completed before cut-off"),
            ("Price distribution", "On time" if distribution_variance <= 0 else "Late", f"Actual minus cut-off: {distribution_variance:+d} minutes"),
            ("Distribution variance", f"{distribution_variance:+d} min", "Measured separately from client submission"),
        ]
    )
    if st.button("Record cut-off assessment", icon=":material/schedule:"):
        result_text = f"Submission {submission_variance:+d} minutes; distribution {distribution_variance:+d} minutes."
        log_event("Delivery cut-off assessment recorded", "Late" if submission_variance > 0 or distribution_variance > 0 else "On time", "Synthetic operations user", result_text)
        st.success("Cut-off evidence recorded for this session.")

    st.subheader("Client query workflow")
    st.caption("CAM means Client Account Manager. The Client Account Manager coordinates the query; fund operations retains ownership of the financial evidence and response.")
    with st.form("client_query_form"):
        q1, q2, q3 = st.columns(3)
        category = q1.selectbox("Query category", ["Price movement", "Investor dealing", "Reconciliation evidence", "Fee or accrual", "Timeliness", "Other"])
        priority = q2.selectbox("Priority", ["Normal", "High", "Critical"])
        due_date = q3.date_input("Response due date", value=valuation_date + timedelta(days=1))
        query_text = st.text_area("Client question or challenge", placeholder="Describe the question and the evidence requested.")
        query_submitted = st.form_submit_button("Record client query", disabled=not stage_at_least("Checker approved"))
    if query_submitted:
        if len(query_text.strip()) < 20:
            st.error("Provide a specific client question of at least 20 characters.")
        else:
            query_id = f"QRY-{len(st.session_state.client_queries) + 1:03d}"
            st.session_state.client_queries.append({
                "Query ID": query_id,
                "Category": category,
                "Priority": priority,
                "Question": query_text.strip(),
                "Owner": "Client Account Manager",
                "Due date": due_date.isoformat(),
                "Status": "Open",
                "Response": "",
                "Evidence reference": "",
            })
            log_event("Client query recorded", "Open", "Client Account Manager", f"{query_id}; {category}; due {due_date}.")
            st.rerun()
    if not stage_at_least("Checker approved"):
        st.info("Checker approval is required before a client-submission query can be recorded in this workflow.")
    if st.session_state.client_queries:
        aligned_dataframe(pd.DataFrame(st.session_state.client_queries), hide_index=True, width="stretch")
        open_query_ids = [row["Query ID"] for row in st.session_state.client_queries if row["Status"] == "Open"]
        if open_query_ids:
            selected_query = st.selectbox("Open query to resolve", open_query_ids)
            response = st.text_area("Substantive response", key="client_query_response")
            response_evidence = st.text_input("Response evidence reference", key="client_query_evidence")
            if st.button("Resolve client query", icon=":material/task_alt:"):
                if len(response.strip()) < 20 or len(response_evidence.strip()) < 4:
                    st.error("A substantive response and evidence reference are required.")
                else:
                    for row in st.session_state.client_queries:
                        if row["Query ID"] == selected_query:
                            row.update({"Status": "Resolved", "Response": response.strip(), "Evidence reference": response_evidence.strip()})
                    log_event("Client query resolved", "Resolved", "Client Account Manager", f"{selected_query}; evidence {response_evidence.strip()}.")
                    st.rerun()

with distribution_tab:
    explain('delivery')
    st.subheader("Simulate price delivery")
    st.caption("Choose an outcome, then publish after checker approval. No message is sent outside this app.")
    channels = pd.DataFrame(st.session_state.distribution_channels)
    aligned_dataframe(channels, hide_index=True, width="stretch")
    failure_target = st.selectbox("Publication outcome", ["All recipients acknowledge", *[f"Fail: {row['Recipient']}" for row in st.session_state.distribution_channels]])
    approval_current = bool(
        st.session_state.checker
        and st.session_state.checker.get("Control package fingerprint") == control_package_fingerprint()
    )
    open_client_queries = [row for row in st.session_state.client_queries if row["Status"] == "Open"]
    approved = st.session_state.run_stage in {"Checker approved", "Publication simulated"} and approval_current and not open_client_queries
    if st.button("Simulate price publication", type="primary", disabled=not approved):
        failed_recipient = failure_target.removeprefix("Fail: ") if failure_target.startswith("Fail: ") else None
        for row in st.session_state.distribution_channels:
            row["Status"] = "Failed" if row["Recipient"] == failed_recipient else "Acknowledged"
        if failed_recipient:
            st.session_state.run_stage = "Checker approved"
            log_event("Price publication simulated", "Partial failure", "Synthetic distribution service", f"No acknowledgement from {failed_recipient}.")
        else:
            st.session_state.run_stage = "Publication simulated"
            log_event("Price publication simulated", "Acknowledged", "Synthetic distribution service", "All three synthetic recipients acknowledged; no data was transmitted externally.")
        st.rerun()
    failed = [row for row in st.session_state.distribution_channels if row["Status"] == "Failed"]
    if failed:
        st.error(f"Publication remains incomplete: {failed[0]['Recipient']} failed.")
        if st.button("Retry failed recipient", icon=":material/refresh:", disabled=not approved):
            for row in failed:
                row["Status"] = "Acknowledged"
            st.session_state.run_stage = "Publication simulated"
            log_event("Failed publication recipient retried", "Acknowledged", "Synthetic distribution service", failed[0]["Recipient"])
            st.rerun()
    elif st.session_state.run_stage == "Publication simulated":
        st.success("All synthetic recipients acknowledged the current version. Nothing was transmitted outside this app.")
    if not approved:
        if open_client_queries:
            st.info("Resolve all open client queries before price distribution can be simulated.")
        else:
            st.info("Checker approval is required before publication can be simulated.")

with resilience_tab:
    explain('resilience')
    st.subheader("Business continuity exercise")
    st.markdown("Change the workload and recovery capacity to see how quickly an illustrative backlog can be cleared after a disruption.", text_alignment="justify")
    a, b, c = st.columns(3)
    daily_volume = a.number_input("Critical daily work items", min_value=1, value=1_000, step=100)
    outage_days = b.number_input("Disruption duration (days)", min_value=1, value=5, step=1)
    alternate_capacity = c.slider("Alternate-site capacity during disruption (%)", 0, 100, 60, 5)
    recovery_capacity = st.slider("Total processing capacity after restoration (%)", 101, 200, 130, 5)
    backlog = math.ceil(daily_volume * outage_days * (1 - alternate_capacity / 100))
    extra_daily = daily_volume * (recovery_capacity / 100 - 1)
    recovery_days = math.ceil(backlog / extra_daily) if extra_daily else 0
    metric_row(
        [
            ("Work processed during disruption", f"{daily_volume * outage_days - backlog:,}", "Based on alternate-site capacity"),
            ("Backlog after disruption", f"{backlog:,}", "Critical items not completed during the disruption"),
            ("Estimated catch-up time", f"{recovery_days} days", "Backlog divided by capacity above normal incoming volume"),
        ]
    )
    priority = st.segmented_control("Recovery priority", ["Client and regulatory cut-offs", "Accounting and reconciliation controls", "Cost containment"], default="Client and regulatory cut-offs")
    implications = {
        "Client and regulatory cut-offs": "Prioritize daily valuation and time-critical deliverables; expect higher short-term staffing and oversight cost.",
        "Accounting and reconciliation controls": "Preserve quality gates and independent checks; some lower-priority deliverables may be delayed.",
        "Cost containment": "Use phased recovery and standard work allocation; backlog clears more slowly and requires explicit risk acceptance.",
    }
    st.info(implications[priority])

with delivery_tab:
    explain('uat')
    st.subheader("Test a mission delivery decision")
    st.caption("Select each completed gate and enter an evidence reference. This is a fictional register for exploring the delivery process.")
    gate_values = []
    for index, (name, explanation) in enumerate(QUALITY_GATES, start=1):
        gate_column, evidence_column = st.columns([1.4, 1])
        checked = gate_column.checkbox(f"Gate {index}: {name}", help=explanation, key=f"delivery_gate_{index}")
        evidence = evidence_column.text_input(
            f"Gate {index} evidence reference",
            value=st.session_state.delivery_gate_evidence.get(name, ""),
            placeholder="Document or test reference",
            key=f"delivery_gate_evidence_{index}",
        )
        st.session_state.delivery_gate_evidence[name] = evidence.strip()
        gate_values.append(checked and len(evidence.strip()) >= 4)
        if checked and len(evidence.strip()) < 4:
            st.caption(f"Gate {index} needs an evidence reference before it counts as satisfied.")
    metric_row(
        [
            ("Gates satisfied", f"{sum(gate_values)}/{len(gate_values)}", "Selected gates with evidence references"),
            ("Readiness", "Ready for decision" if all(gate_values) else "Evidence incomplete", "All gates must have evidence before a production decision"),
        ]
    )
    st.subheader("User Acceptance Testing register")
    edited = aligned_editor(
        pd.DataFrame(st.session_state.uat_register),
        hide_index=True,
        width="stretch",
        num_rows="dynamic",
        key="uat_editor",
        column_config={
            "Result": st.column_config.SelectboxColumn(options=["Not started", "In progress", "Passed", "Failed", "Blocked"], required=True),
        },
    )
    if st.button("Save User Acceptance Testing register"):
        errors = []
        if edited.empty:
            errors.append("Keep at least one User Acceptance Testing case.")
        identifiers = edited["Test ID"].fillna("").astype(str).str.strip()
        if identifiers.eq("").any() or identifiers.duplicated().any():
            errors.append("Every test needs a unique, nonempty identifier.")
        for column in ("Area", "Owner", "Result"):
            if edited[column].fillna("").astype(str).str.strip().eq("").any():
                errors.append(f"Every test needs a {column.lower()}.")
        passed_without_evidence = (
            edited["Result"].eq("Passed")
            & edited["Evidence reference"].fillna("").astype(str).str.strip().eq("")
        )
        if passed_without_evidence.any():
            errors.append("A passed test requires an evidence reference.")
        if errors:
            for error in errors:
                st.error(error)
        else:
            st.session_state.uat_register = edited.to_dict("records")
            log_event("User Acceptance Testing register saved", "Recorded", "Delivery owner", f"{len(edited)} test rows.", scope="Delivery assurance")
            st.success("Register saved in this browser session.")

with log_tab:
    explain('audit')
    st.subheader("Session activity record")
    st.caption("Each scope uses a SHA-256 record chain so edits become visible in its export. Session state remains mutable and is not an immutable audit archive or digital signature.")
    log_df = pd.DataFrame(st.session_state.session_log)
    aligned_dataframe(log_df, hide_index=True, width="stretch")
    payload = json.dumps(session_export(), indent=2, default=str)
    st.download_button("Download current valuation-run evidence package", payload, f"{st.session_state.run_id}-evidence-package.json", "application/json", icon=":material/download:")

module_footer("governance", "app_pages/projects.py", "Continue to mission evidence")
