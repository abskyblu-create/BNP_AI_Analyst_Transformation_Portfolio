from __future__ import annotations

import json
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from ui import result_metric

from ui import control_warning

from ui import aligned_dataframe, aligned_editor

from learning import explain

from data import DELIVERY_STAGES, PROJECTS
from state import log_event
from ui import page_header


page_header(
    "MISSIONS / DOCUMENTED EXPERIENCE",
    "Eight missions, one transformation logic",
    "Choose a mission to see the operational problem, contribution, engineering approach and outcome.",
    ":material/target:",
)

st.caption("Mission descriptions are grounded in the supplied internship presentation and experience report. Optional lab data and controls are fictional.")

search_col, pillar_col = st.columns([2, 1])
query = search_col.text_input(
    "Search missions, tools, controls or outcomes",
    type="search",
    placeholder="Example: reconciliation, Python, User Acceptance Testing",
)
pillars = ["All pillars", *sorted({project["pillar"] for project in PROJECTS})]
pillar = pillar_col.selectbox("Capability pillar", pillars)
visible = [
    project
    for project in PROJECTS
    if (pillar == "All pillars" or project["pillar"] == pillar)
    and query.casefold() in json.dumps(project).casefold()
]

st.caption(f"Showing {len(visible)} of {len(PROJECTS)} missions")
if not visible:
    st.info("No mission matches the current search and pillar filter.")
else:
    overview = pd.DataFrame(
        [
            {
                "ID": project["id"],
                "Mission": project["title"],
                "Scale / result": project["metric"],
                "Capability pillar": project["pillar"],
                "Objective": project["objective"],
            }
            for project in visible
        ]
    )
    with st.expander("Compare all matching missions"):
        aligned_dataframe(overview, hide_index=True, width="stretch")

    selected_id = st.selectbox(
        "Open a mission",
        [project["id"] for project in visible],
        format_func=lambda project_id: f"{project_id} · {next(project['title'] for project in visible if project['id'] == project_id)}",
    )
    project = next(project for project in visible if project["id"] == selected_id)
    with st.container(border=True):
        st.caption(f"{project['id']} · {project['pillar']}")
        st.header(project["title"])
        st.markdown(f":green-badge[{project['metric']}]")
        st.markdown(f"**Why this mission existed:** {project['challenge']}", text_alignment="left")
        st.markdown(f"**Contribution:** {project['objective']}", text_alignment="left")
        st.markdown(f"**What it produced:** {project['evidence'][0]}", text_alignment="left")
        with st.container(horizontal=True):
            st.badge("Documented experience", color="green", icon=":material/work_history:")
            if any("prompt" in tool.casefold() or "language model" in tool.casefold() for tool in project["tools"]):
                st.badge("AI engineering", color="violet", icon=":material/memory:")

    st.subheader("Explore the method, decisions and evidence")
    with st.container():
        st.caption("Tools and methods: " + " · ".join(project["tools"]))
        pipeline_tab, decisions_tab, controls_tab, evidence_tab = st.tabs(
            ["How it worked", "Key decisions", "Controls", "Evidence"]
        )
        with pipeline_tab:
            for index, step in enumerate(project["pipeline"], start=1):
                st.markdown(f"{index}. {step}", text_alignment="left")
        with decisions_tab:
            for decision in project["decisions"]:
                st.markdown(f"- {decision}", text_alignment="left")
        with controls_tab:
            for control in project["controls"]:
                st.markdown(f"- {control}", text_alignment="left")
        with evidence_tab:
            for item in project["evidence"]:
                st.markdown(f"- {item}", text_alignment="left")
            st.caption(f"Key learning: {project['learning']}", text_alignment="left")

st.subheader("Optional: try the ideas yourself")
st.caption("The mission explanation is complete on this page. Open the interactive lab only if you want to test the mechanics with fictional data.")
connections = pd.DataFrame(
    [
        ["P01", "Data and reporting", "Missing-value laboratory and traceable row handling"],
        ["P02", "Data and reporting", "Dimensional modelling and reconciliation KPIs"],
        ["P03", "Artificial Intelligence control lab", "Calendar-aware NAV-delay checks"],
        ["P04", "Artificial Intelligence control lab", "Sequential file chunks and integrity manifest"],
        ["P05", "Artificial Intelligence control lab", "Deterministic derivative and foreign-exchange parser"],
        ["P06", "Governance and resilience", "Use-case register, ownership and review decisions"],
        ["P07", "Data and reporting", "Explainable anomaly scoring and priority bands"],
        ["P08", "Governance and resilience", "Evidence gates, UAT and readiness decisions"],
    ],
    columns=["Case study", "Interactive page", "Implemented evidence"],
)
with st.expander("See the mission-to-lab map"):
    aligned_dataframe(connections, hide_index=True, width="stretch")

st.header("Optional: try a delivery decision")
st.markdown("Choose a mission, record an owner and evidence, then see whether it can move to the next stage.", text_alignment="left")
st.caption("This editable register is fictional and stays in your browser session.")

with st.expander("Open the delivery simulator"):
    RAG_OPTIONS = ["Green", "Amber", "Red"]
    STATUS_OPTIONS = ["Idea", "Framed", "Prototype", "In review", "Blocked", "Ready for decision", "Closed"]
    RISK_OPTIONS = ["Low", "Medium", "High"]

    delivery_register = st.session_state.setdefault("delivery_register", {})
    for item in PROJECTS:
        default = {
            "Mission": item["title"],
            "Stage": "Proof of concept",
            "RAG status": "Amber",
            "Owner": "Transformation owner",
            "Target date": date.today() + timedelta(days=14),
            "Blocker": "",
            "Evidence reference": "",
        }
        if item["id"] not in delivery_register:
            delivery_register[item["id"]] = default
        else:
            existing = delivery_register[item["id"]]
            # Preserve an open browser session created before the page text was repaired.
            if "RrG status" in existing and "RAG status" not in existing:
                existing["RAG status"] = existing.pop("RrG status").replace("rmber", "Amber")
            for key, value in default.items():
                existing.setdefault(key, value)

    stage_tab, use_case_tab = st.tabs(["Mission stage-gate control", "Use-case governance board"])

    with stage_tab:
        explain('stage_gate')
        selected_project = st.selectbox(
            "Mission to govern",
            [item["id"] for item in PROJECTS],
            format_func=lambda project_id: f"{project_id} · {next(item['title'] for item in PROJECTS if item['id'] == project_id)}",
            key="delivery_project",
        )
        current = delivery_register[selected_project]
        if current["Stage"] not in DELIVERY_STAGES:
            current["Stage"] = DELIVERY_STAGES[0]
        if current["RAG status"] not in RAG_OPTIONS:
            current["RAG status"] = "Amber"

        st.caption("Current stage: " + current["Stage"])
        with st.form("delivery_gate_form"):
            rag_col, date_col = st.columns(2)
            rag = rag_col.selectbox(
                "Red-Amber-Green status", RAG_OPTIONS, index=RAG_OPTIONS.index(current["RAG status"])
            )
            target = date_col.date_input("Target decision date", value=current["Target date"])
            owner = st.text_input("Accountable owner or role", value=current["Owner"])
            blocker = st.text_area(
                "Current blocker or dependency",
                value=current["Blocker"],
                placeholder="Leave blank only when no material blocker is open.",
            )
            evidence_reference = st.text_input(
                "Evidence reference",
                value=current["Evidence reference"],
                placeholder="Example: UAT-04, decision minutes or approved requirement",
            )
            saved = st.form_submit_button("Save delivery status", type="primary")
        if saved:
            current.update(
                {
                    "RAG status": rag,
                    "Owner": owner.strip(),
                    "Target date": target,
                    "Blocker": blocker.strip(),
                    "Evidence reference": evidence_reference.strip(),
                }
            )
            log_event(
                "Mission delivery status saved",
                rag,
                owner.strip() or "Unassigned",
                f"{selected_project}; {current['Stage']}; target {target}.",
                scope="Delivery portfolio",
            )
            st.success("Delivery status saved in this browser session.")

        current_index = DELIVERY_STAGES.index(current["Stage"])
        can_advance = (
            current_index < len(DELIVERY_STAGES) - 1
            and len(current["Owner"].strip()) >= 3
            and len(current["Evidence reference"].strip()) >= 4
            and not current["Blocker"].strip()
            and current["RAG status"] != "Red"
        )
        if current["RAG status"] == "Red" or current["Blocker"].strip():
            st.error("A blocked or Red mission cannot advance until its blocker is resolved and status reviewed.")
        elif not can_advance and current_index < len(DELIVERY_STAGES) - 1:
            control_warning("Advancement requires an accountable owner and evidence reference.")
        if st.button(
            "Advance to the next controlled stage",
            disabled=not can_advance,
            icon=":material/upgrade:",
        ):
            prior = current["Stage"]
            current["Stage"] = DELIVERY_STAGES[current_index + 1]
            log_event(
                "Mission stage advanced",
                current["Stage"],
                current["Owner"],
                f"{selected_project}: {prior} to {current['Stage']}; evidence {current['Evidence reference']}.",
                scope="Delivery portfolio",
            )
            st.rerun()

        aligned_dataframe(
            pd.DataFrame([{"ID": key, **value} for key, value in delivery_register.items()]),
            hide_index=True,
            width="stretch",
        )

        st.subheader("Cost, time and quality decision")
        priority = st.segmented_control(
            "Constraint requiring protection",
            ["Quality and control", "Delivery date", "Cost capacity"],
            default="Quality and control",
        )
        trade_offs = {
            "Quality and control": "Preserve validation and evidence gates; change timing or capacity if the committed scope cannot pass safely.",
            "Delivery date": "Protect the target date by adding capacity or reducing explicitly agreed scope; record the decision and residual risk.",
            "Cost capacity": "Keep capacity within the agreed envelope; phase scope or revise the date rather than hiding the constraint.",
        }
        st.info(trade_offs[priority])

    with use_case_tab:
        explain('use_cases')
        if "use_case_register" not in st.session_state:
            st.session_state.use_case_register = [
                {
                    "Use case": item["id"],
                    "Problem statement": item["title"],
                    "Business owner": "Business owner",
                    "Technical owner": "Technical owner",
                    "Status": "In review",
                    "Completion (%)": 50,
                    "Risk": "Medium",
                    "Blocker": "",
                    "Next action": "Confirm evidence and decision criteria",
                }
                for item in PROJECTS
            ]
        else:
            for row in st.session_state.use_case_register:
                if "oompletion (%)" in row and "Completion (%)" not in row:
                    row["Completion (%)"] = row.pop("oompletion (%)")

        with st.form("use_case_register_form"):
            edited_register = aligned_editor(
                pd.DataFrame(st.session_state.use_case_register),
                hide_index=True,
                width="stretch",
                num_rows="dynamic",
                key="use_case_editor",
                column_config={
                    "Status": st.column_config.SelectboxColumn(options=STATUS_OPTIONS, required=True),
                    "Completion (%)": st.column_config.ProgressColumn(min_value=0, max_value=100),
                    "Risk": st.column_config.SelectboxColumn(options=RISK_OPTIONS, required=True),
                },
            )
            save_cases = st.form_submit_button("Save use-case governance board")

        blocked = int((edited_register["Status"] == "Blocked").sum()) if not edited_register.empty else 0
        high_risk = int((edited_register["Risk"] == "High").sum()) if not edited_register.empty else 0
        ready = int((edited_register["Status"] == "Ready for decision").sum()) if not edited_register.empty else 0
        with st.container(horizontal=True):
            result_metric("Use cases", len(edited_register), border=True)
            result_metric("Blocked", blocked, border=True, alert=blocked > 0)
            result_metric("High risk", high_risk, border=True, alert=high_risk > 0)
            result_metric("Ready for decision", ready, border=True)

        if save_cases:
            records = edited_register.to_dict("records")
            ids = [str(row.get("Use case") or "").strip() for row in records]
            invalid = any(
                not use_case_id
                or not str(row.get("Problem statement") or "").strip()
                or not str(row.get("Business owner") or "").strip()
                or not str(row.get("Technical owner") or "").strip()
                or not str(row.get("Next action") or "").strip()
                or row.get("Status") not in STATUS_OPTIONS
                or row.get("Risk") not in RISK_OPTIONS
                or pd.isna(row.get("Completion (%)"))
                for use_case_id, row in zip(ids, records)
            )
            if invalid or len(ids) != len(set(ids)):
                st.error("Each use case needs a unique identifier, problem, owners, next action, valid status, risk and completion value.")
            else:
                st.session_state.use_case_register = records
                log_event(
                    "Use-case governance board saved",
                    "Recorded",
                    "Portfolio owner",
                    f"{len(records)} use cases; {blocked} blocked.",
                    scope="Delivery portfolio",
                )
                st.success("Governance board saved in this browser session.")

if st.button("Open glossary and methodology", icon=":material/arrow_forward:"):
    st.switch_page("app_pages/glossary.py")
