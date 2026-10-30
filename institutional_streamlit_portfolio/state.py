"""Session-scoped state and lifecycle helpers for the demonstration app."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import date, datetime, timezone
import hashlib
import json
from uuid import uuid4

import streamlit as st

from data import FUNDS, SYNTHETIC_BREAKS, SYNTHETIC_POSITIONS_BY_FUND
from valuation import Valuation


RUN_STAGES = [
    "Draft",
    "Calculated",
    "Reconciliation cleared",
    "Preparer reviewed",
    "Checker approved",
    "Publication simulated",
]
STATE_SCHEMA_VERSION = 5


def _new_run_id() -> str:
    return f"NAV-{date.today():%Y%m%d}-{uuid4().hex[:6].upper()}"


def seed_positions(fund_name: str, valuation_date: date) -> list[dict]:
    """Copy the selected fund's holdings and date its price evidence."""
    if fund_name not in SYNTHETIC_POSITIONS_BY_FUND:
        raise ValueError(f"No synthetic position set exists for {fund_name!r}.")
    positions = deepcopy(SYNTHETIC_POSITIONS_BY_FUND[fund_name])
    for row in positions:
        sample_time = row["Price timestamp"].split(" ", 1)[1]
        row["Price timestamp"] = f"{valuation_date:%Y-%m-%d} {sample_time}"
    return positions


def initialize_session() -> None:
    valuation_date = date.today()
    defaults = {
        "state_schema_version": STATE_SCHEMA_VERSION,
        "context": {
            "fund": FUNDS[0]["Fund"],
            "share_class": FUNDS[0]["Share class"],
            "base_currency": FUNDS[0]["Base currency"],
            "valuation_frequency": FUNDS[0]["Valuation frequency"],
            "valuation_date": valuation_date,
            "policy_version": "Synthetic valuation policy 1.0",
        },
        "run_id": _new_run_id(),
        "run_version": 1,
        "run_stage": "Draft",
        "valuation": asdict(Valuation()),
        "valuation_positions": seed_positions(FUNDS[0]["Fund"], valuation_date),
        "position_editor_version": 0,
        "cash_forecast_inputs": {
            "opening_cash": 18_000_000.0,
            "subscriptions": 5_000_000.0,
            "redemptions": 2_000_000.0,
            "purchase_settlements": 1_326_300.0,
            "sale_settlements": 1_228_000.0,
            "collateral": 350_000.0,
            "minimum_buffer_percent": 2.0,
        },
        "valuation_result": None,
        "valuation_hash": None,
        "last_calculated_inputs": None,
        "breaks": deepcopy(SYNTHETIC_BREAKS),
        "resolutions": {},
        "session_log": [],
        "journal": [],
        "quality_inputs": {
            "stale_price": False,
            "unit_register_received": True,
            "price_source_received": True,
            "cash_reconciled": True,
            "minimum_cash_buffer_percent": 2.0,
        },
        "review_checklist": {
            "sources": False,
            "prices": False,
            "accruals": False,
            "units": False,
            "exceptions": False,
        },
        "preparer": None,
        "checker": None,
        "distribution_channels": [
            {"Recipient": "Transfer-agent unit register", "Purpose": "Apply the approved dealing price", "Status": "Queued"},
            {"Recipient": "Depositary oversight mailbox", "Purpose": "Receive the valuation-review package", "Status": "Queued"},
            {"Recipient": "Synthetic fund-price service", "Purpose": "Demonstrate downstream price publication", "Status": "Queued"},
        ],
        "client_queries": [],
        "delivery_gate_evidence": {},
        "ai_result": None,
        "uat_register": [
            {"Test ID": "UAT-01", "Area": "Source-file completeness", "Owner": "Data owner", "Result": "Passed", "Evidence reference": "EV-001"},
            {"Test ID": "UAT-02", "Area": "Missing-value preservation", "Owner": "Reporting owner", "Result": "Passed", "Evidence reference": "EV-002"},
            {"Test ID": "UAT-03", "Area": "Exception-status mapping", "Owner": "Operations owner", "Result": "In progress", "Evidence reference": ""},
            {"Test ID": "UAT-04", "Area": "Session-record export", "Owner": "Delivery owner", "Result": "Not started", "Evidence reference": ""},
        ],
    }
    if st.session_state.get("state_schema_version") != STATE_SCHEMA_VERSION:
        for key, value in defaults.items():
            st.session_state[key] = deepcopy(value)
    else:
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = deepcopy(value)
    if not st.session_state.session_log:
        log_event("Run initialized", "Created", "System", "Synthetic valuation run created in Draft status.")


def log_event(
    action: str,
    result: str,
    actor: str,
    details: str,
    evidence_hash: str | None = None,
    scope: str = "Valuation run",
) -> None:
    event_run_id = st.session_state.run_id if scope == "Valuation run" else "Not applicable"
    event_version = str(st.session_state.run_version) if scope == "Valuation run" else "Not applicable"
    previous = next(
        (
            row["Record hash"]
            for row in st.session_state.session_log
            if row.get("Run ID") == event_run_id and row.get("Scope") == scope
        ),
        "GENESIS",
    )
    event = {
        "Event ID": f"EVT-{uuid4().hex[:8].upper()}",
        "Time (UTC)": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "Run ID": event_run_id,
        "Version": event_version,
        "Scope": scope,
        "Actor": actor,
        "Action": action,
        "Result": result,
        "Details": details,
        "Evidence hash": evidence_hash or (st.session_state.get("valuation_hash") if scope == "Valuation run" else None) or "Not applicable",
    }
    payload = json.dumps({**event, "Previous record": previous}, sort_keys=True, default=str)
    event["Record hash"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    st.session_state.session_log.insert(0, event)


def current_fund_breaks(include_resolved: bool = True) -> list[dict]:
    rows = [row for row in st.session_state.breaks if row["Fund"] == st.session_state.context["fund"]]
    if include_resolved:
        return rows
    return [row for row in rows if row["Workflow status"] not in {"Resolved", "Accepted within policy tolerance"}]


def stage_at_least(stage: str) -> bool:
    return RUN_STAGES.index(st.session_state.run_stage) >= RUN_STAGES.index(stage)


def invalidate_downstream(reason: str, keep_calculation: bool = True) -> None:
    if not keep_calculation:
        st.session_state.valuation_result = None
        st.session_state.valuation_hash = None
    st.session_state.run_stage = "Calculated" if keep_calculation and st.session_state.valuation_result else "Draft"
    st.session_state.preparer = None
    st.session_state.checker = None
    st.session_state.review_checklist = {key: False for key in st.session_state.review_checklist}
    for channel in st.session_state.distribution_channels:
        channel["Status"] = "Queued"
    st.session_state.client_queries = []
    log_event("Downstream decisions invalidated", "Reset", "System", reason)


def begin_new_run(fund_name: str, valuation_date: date) -> None:
    fund = next(item for item in FUNDS if item["Fund"] == fund_name)
    st.session_state.context = {
        "fund": fund["Fund"],
        "share_class": fund["Share class"],
        "base_currency": fund["Base currency"],
        "valuation_frequency": fund["Valuation frequency"],
        "valuation_date": valuation_date,
        "policy_version": "Synthetic valuation policy 1.0",
    }
    st.session_state.run_id = _new_run_id()
    st.session_state.run_version = 1
    st.session_state.run_stage = "Draft"
    st.session_state.valuation = asdict(Valuation())
    st.session_state.valuation_positions = seed_positions(fund_name, valuation_date)
    st.session_state.position_editor_version = st.session_state.get("position_editor_version", 0) + 1
    st.session_state.cash_forecast_inputs = {
        "opening_cash": 18_000_000.0,
        "subscriptions": 5_000_000.0,
        "redemptions": 2_000_000.0,
        "purchase_settlements": 1_326_300.0,
        "sale_settlements": 1_228_000.0,
        "collateral": 350_000.0,
        "minimum_buffer_percent": 2.0,
    }
    st.session_state.valuation_result = None
    st.session_state.valuation_hash = None
    st.session_state.last_calculated_inputs = None
    st.session_state.breaks = deepcopy(SYNTHETIC_BREAKS)
    st.session_state.resolutions = {}
    st.session_state.quality_inputs = {
        "stale_price": False,
        "unit_register_received": True,
        "price_source_received": True,
        "cash_reconciled": True,
        "minimum_cash_buffer_percent": 2.0,
    }
    st.session_state.preparer = None
    st.session_state.checker = None
    st.session_state.review_checklist = {key: False for key in st.session_state.review_checklist}
    for channel in st.session_state.distribution_channels:
        channel["Status"] = "Queued"
    st.session_state.client_queries = []
    log_event("New valuation context selected", "Created", "System", f"{fund_name}; valuation date {valuation_date.isoformat()}.")


def control_package_fingerprint() -> str | None:
    """Fingerprint the current valuation and the control evidence used for review."""
    if not st.session_state.valuation_result:
        return None
    break_ids = {row["Break ID"] for row in current_fund_breaks()}
    package = {
        "context": st.session_state.context,
        "run_id": st.session_state.run_id,
        "version": st.session_state.run_version,
        "valuation_inputs": st.session_state.valuation,
        "position_valuation": st.session_state.valuation_positions,
        "cash_forecast_inputs": st.session_state.cash_forecast_inputs,
        "valuation_results": st.session_state.valuation_result,
        "source_readiness": st.session_state.quality_inputs,
        "run_linked_breaks": current_fund_breaks(),
        "run_linked_resolutions": {
            key: value for key, value in st.session_state.resolutions.items() if key in break_ids
        },
        "preparer_checklist": st.session_state.review_checklist,
    }
    canonical = json.dumps(package, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def session_export() -> dict:
    result = st.session_state.valuation_result or {}
    run_breaks = current_fund_breaks()
    break_ids = {row["Break ID"] for row in run_breaks}
    run_events = [
        event
        for event in st.session_state.session_log
        if event.get("Run ID") == st.session_state.run_id and event.get("Scope") == "Valuation run"
    ]
    return {
        "scope": "Synthetic, session-scoped demonstration record",
        "portfolio_acknowledgement": st.session_state.get("portfolio_acknowledgement"),
        "context": st.session_state.context,
        "run_id": st.session_state.run_id,
        "version": st.session_state.run_version,
        "status": st.session_state.run_stage,
        "valuation_inputs": st.session_state.valuation,
        "position_valuation": st.session_state.valuation_positions,
        "cash_forecast_inputs": st.session_state.cash_forecast_inputs,
        "valuation_results": result,
        "calculation_fingerprint": st.session_state.valuation_hash,
        "control_package_fingerprint": control_package_fingerprint(),
        "run_linked_breaks": run_breaks,
        "resolutions": {key: value for key, value in st.session_state.resolutions.items() if key in break_ids},
        "preparer": st.session_state.preparer,
        "checker": st.session_state.checker,
        "review_checklist": st.session_state.review_checklist,
        "quality_inputs": st.session_state.quality_inputs,
        "distribution_channels": st.session_state.distribution_channels,
        "client_submission_queries": st.session_state.client_queries,
        "user_acceptance_testing_register": st.session_state.uat_register,
        "delivery_gate_evidence": st.session_state.delivery_gate_evidence,
        "valuation_run_activity": run_events,
    }
