"""A sequential learning journey whose evidence is carried from stage to stage."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json

import pandas as pd
import streamlit as st

from ui import result_metric

from ui import aligned_dataframe

from learning import explain, explain_events

from data import (
    FUNDS,
    PROJECTS,
    QUALITY_GATES,
    RECONCILIATION_EVENTS,
    SYNTHETIC_BREAKS,
    SYNTHETIC_POSITIONS_BY_FUND,
    synthetic_trades_for_fund,
)
from domain import anomaly_assessment, cash_forecast, valuation_fingerprint
from state import log_event
from valuation import Valuation


CASE_FUND = FUNDS[0]
CASE_DATE_ISO = "2026-09-17"
CASE_DATE_DISPLAY = "17 September 2026"
STATE_VERSION = 2


STEPS = [
    {
        "title": "Frame the business need and fund context",
        "what": "The journey fixes one fictional fund, share class, valuation date and learning objective before any data is processed.",
        "why": "A technical result is useful only when the business question, scope and acceptance criteria are clear.",
        "how": "The system loads one prepared case and carries the same context and four acceptance criteria through every later stage.",
        "formula": "Business need → agreed scope → acceptance criteria → controlled execution",
    },
    {
        "title": "Receive every source and preserve lineage",
        "what": "Fund, position, trade, accounting, cash, policy, unit, flow, exception and reporting records enter one controlled case pack.",
        "why": "Every later amount must remain traceable to an identifiable source; a missing value must never be silently turned into zero.",
        "how": "The system copies each prepared source, retains its row identifier, compares row counts and verifies a content fingerprint.",
        "formula": "Source control passes when received rows = preserved rows and received fingerprint = preserved fingerprint",
    },
    {
        "title": "Validate and structure the data model",
        "what": "The fund record is separated from repeated operational events, while identifiers, required fields, dates and policy limits are checked.",
        "why": "One fund can have many events. Mixing row types or accepting incomplete keys can inflate totals and break traceability.",
        "how": "A unique fund dimension links to position, trade, accounting and reconciliation facts through a controlled fund key.",
        "formula": "One fund dimension row → many fact rows; event count is not a fund count",
    },
    {
        "title": "Price and value every position",
        "what": "Each holding is converted from quantity and local price into a value in the fund's base currency.",
        "why": "The aggregate investment balance must be reconstructable from position-level evidence.",
        "how": "The system consumes the validated position facts, applies the supplied price and foreign-exchange (FX) rate, then compares the roll-up with accounting.",
        "formula": "Position value (EUR) = quantity × local price × FX rate to EUR",
    },
    {
        "title": "Build the accounting and cash picture",
        "what": "Investments, ledger cash, receivables, payables and expenses are assembled while expected cash movements are forecast separately.",
        "why": "Ledger cash describes the accounting balance; forecast cash helps operations anticipate settlement and liquidity needs.",
        "how": "The system derives purchases and sales from the validated trades, takes flows and collateral from their source records, and tests the projected cash buffer.",
        "formula": "Forecast cash = opening cash + subscriptions − redemptions − purchases + sales − collateral",
    },
    {
        "title": "Reconcile records and explain the exception",
        "what": "The system compares settlement dates and amounts, identifies the conflicting record, applies the documented authority rule and records a fictional resolution.",
        "why": "Equal amounts can still hide an attribute mismatch that needs evidence, an owner and a recorded disposition.",
        "how": "Data-quality checks run first; the executed trade confirmation determines the contractual date, a transparent rule score routes the exception, and the resolved event is carried into later reporting.",
        "formula": "Anomaly score = 0.3 × elapsed-time rule + 0.7 × calculation-conflict rule",
    },
    {
        "title": "Calculate Net Asset Value and price per unit",
        "what": "The carried-forward position and accounting balances are combined into total assets, liabilities, Net Asset Value and price per unit.",
        "why": "This connects source records and reconciliation evidence to the investor-facing valuation result.",
        "how": "The system calculates the base price, measures investor flow against the illustrative threshold and applies no swing adjustment when the threshold is not met.",
        "formula": "Net Asset Value = assets − liabilities\nPrice per unit = Net Asset Value ÷ units\nFlow % = |net flow| ÷ Net Asset Value × 100",
    },
    {
        "title": "Validate the management reporting result",
        "what": "The post-resolution reconciliation events are converted into match, outstanding and exposure measures.",
        "why": "A dashboard must reconcile to its detail population and must keep fund counts distinct from event counts.",
        "how": "The system consumes both the post-resolution events and Net Asset Value, ties visual totals to detail, measures the remaining exposure in bps and records its owner, due time, blocker and next action.",
        "formula": "Match rate = matched events ÷ all events × 100\nExposure (bps) = open amount ÷ Net Asset Value × 10,000",
    },
    {
        "title": "Run quality gates, change UAT and independent review",
        "what": "Daily-run control gates and maker-checker evidence are evaluated separately from four change-lifecycle User Acceptance Testing (UAT) cases.",
        "why": "Automation needs reproducible evidence and accountable review before a delivery decision.",
        "how": "The system calculates each gate, tests the delivery guard, and checks distinct simulated preparer and checker identities and timestamps against one evidence fingerprint.",
        "formula": "Ready = all run gates passed ∧ change UAT passed ∧ distinct preparer/checker evidence recorded",
    },
    {
        "title": "Submit, distribute and monitor",
        "what": "The reviewed result is packaged for separate simulated client submission and fund-price diffusion controls.",
        "why": "A calculation is complete only when ownership, delivery status, retained evidence and the next monitoring action are visible.",
        "how": "The delivery guard consumes the prior review decision, then compares actual times with cut-offs and records fictional recipient and acknowledgement references. The Client Account Manager coordinates communication while Operations retains the financial evidence.",
        "formula": "Completed journey = controlled result + recorded review + guarded simulated delivery + monitoring evidence",
    },
]


SOURCE_SPECS = [
    ("fund_reference", "Fund reference", "Fund"),
    ("positions", "Position file", "Position ID"),
    ("trades", "Trade ledger", "Trade ID"),
    ("accounting_balances", "Accounting trial balance", "Record ID"),
    ("unit_and_flow_records", "Unit and investor-flow register", "Record ID"),
    ("valuation_policy", "Valuation and reconciliation policy", "Policy ID"),
    ("cash_schedule", "Cash and collateral schedule", "Movement ID"),
    ("break_register", "Exception register", "Break ID"),
    ("settlement_evidence", "Settlement evidence", "Evidence ID"),
    ("reconciliation_events", "Management-reporting events", "Event ID"),
]


def _digest(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _prepared_sources(context: dict[str, str]) -> dict[str, list[dict]]:
    """Build the fictional source pack. Only the receipt stage reads these fixtures."""
    valuation = Valuation()
    fund = context["fund"]
    fund_reference = next(row for row in FUNDS if row["Fund"] == fund)
    positions = [{**deepcopy(row), "Fund": fund} for row in SYNTHETIC_POSITIONS_BY_FUND[fund]]
    trades = deepcopy(synthetic_trades_for_fund(fund))
    events = [deepcopy(row) for row in RECONCILIATION_EVENTS if row["Fund"] == fund]
    raw_break = next(row for row in SYNTHETIC_BREAKS if row["Fund"] == fund)
    break_row = {
        key: deepcopy(value)
        for key, value in raw_break.items()
        if key != "Impact (basis points)"
    }
    break_row["Reconciliation event ID"] = "REC-003"

    return {
        "fund_reference": [
            {
                **deepcopy(fund_reference),
                "Valuation date": context["valuation_date_iso"],
            }
        ],
        "positions": positions,
        "trades": trades,
        "accounting_balances": [
            {"Record ID": "TB-001", "Fund": fund, "Balance": "Investments", "Amount (EUR)": valuation.portfolio},
            {"Record ID": "TB-002", "Fund": fund, "Balance": "Ledger cash", "Amount (EUR)": valuation.cash},
            {"Record ID": "TB-003", "Fund": fund, "Balance": "Receivables", "Amount (EUR)": valuation.receivables},
            {"Record ID": "TB-004", "Fund": fund, "Balance": "Payables", "Amount (EUR)": valuation.payables},
            {"Record ID": "TB-005", "Fund": fund, "Balance": "Accrued expenses", "Amount (EUR)": valuation.expenses},
        ],
        "unit_and_flow_records": [
            {"Record ID": "UNIT-001", "Fund": fund, "Measure": "Units in issue", "Amount": valuation.units, "Unit": "units"},
            {"Record ID": "FLOW-001", "Fund": fund, "Measure": "Subscriptions", "Amount": 5_000_000.0, "Unit": "EUR"},
            {"Record ID": "FLOW-002", "Fund": fund, "Measure": "Redemptions", "Amount": 2_000_000.0, "Unit": "EUR"},
        ],
        "valuation_policy": [
            {
                "Policy ID": "POL-NAV-2026-01",
                "Fund": fund,
                "Swing enabled": valuation.swing,
                "Flow threshold (%)": valuation.threshold,
                "Swing factor (bps)": valuation.bps,
                "Minimum cash buffer (%)": 2.0,
                "Minimum cash buffer base": "Opening ledger cash",
                "Settlement-date authority": "Executed trade confirmation",
                "Exception ageing threshold (days)": 2,
                "Reporting exposure review threshold (bps)": 5.0,
            }
        ],
        "cash_schedule": [
            {"Movement ID": "CASH-001", "Fund": fund, "Movement": "Collateral", "Amount (EUR)": 350_000.0}
        ],
        "break_register": [break_row],
        "settlement_evidence": [
            {
                "Evidence ID": "SET-FA-10421",
                "Break ID": break_row["Break ID"],
                "Fund": fund,
                "Source": "Fund accounting",
                "Amount (EUR)": break_row["Fund accounting amount"],
                "Settlement date": "2026-09-21",
            },
            {
                "Evidence ID": "SET-CUS-10421",
                "Break ID": break_row["Break ID"],
                "Fund": fund,
                "Source": "Custodian",
                "Amount (EUR)": break_row["Custodian amount"],
                "Settlement date": "2026-09-22",
            },
            {
                "Evidence ID": "SET-IM-10421",
                "Break ID": break_row["Break ID"],
                "Fund": fund,
                "Source": "Investment manager",
                "Amount (EUR)": break_row["Investment manager amount"],
                "Settlement date": "2026-09-21",
            },
            {
                "Evidence ID": "SET-CONF-10421",
                "Break ID": break_row["Break ID"],
                "Fund": fund,
                "Source": "Executed trade confirmation",
                "Amount (EUR)": break_row["Investment manager amount"],
                "Settlement date": "2026-09-21",
            },
        ],
        "reconciliation_events": events,
    }


def _context() -> dict[str, str]:
    return {
        "fund": CASE_FUND["Fund"],
        "share_class": CASE_FUND["Share class"],
        "base_currency": CASE_FUND["Base currency"],
        "valuation_date": CASE_DATE_DISPLAY,
        "valuation_date_iso": CASE_DATE_ISO,
    }


def _prior_output(records: list[dict], step_number: int) -> dict:
    if len(records) < step_number or records[step_number - 1].get("step") != step_number:
        raise RuntimeError(f"Stage {step_number:02d} evidence is required before this stage can run.")
    return records[step_number - 1]["output"]


def _date_is_valid(value: object, date_format: str) -> bool:
    try:
        datetime.strptime(str(value), date_format)
        return True
    except (TypeError, ValueError):
        return False


def _named_amount(rows: list[dict], label_key: str, label: str, amount_key: str = "Amount") -> float:
    return float(next(row[amount_key] for row in rows if row[label_key] == label))


def _delivery_allowed(gates: list[dict], acceptance_tests: list[dict]) -> bool:
    return bool(gates and acceptance_tests) and all(row["Result"] == "Passed" for row in gates) and all(
        row["Result"] == "Passed" for row in acceptance_tests
    )


def _execute_step(index: int, records: list[dict]) -> dict:
    """Run exactly one stage and consume only the evidence already produced."""
    if index != len(records) or not 0 <= index < len(STEPS):
        raise RuntimeError("The guided journey must run one stage at a time in order.")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    carried_from: list[int] = []

    if index == 0:
        output = {
            "context": _context(),
            "business_question": "How can controlled source data become an explainable fund valuation and delivery result?",
            "acceptance_criteria": [
                "Every critical input is preserved and traceable.",
                "Position, cash, Net Asset Value and reporting calculations can be reconstructed.",
                "Exceptions have a status, owner and impact assessment.",
                "Independent review is tied to the evidence package and delivery is control-gated.",
            ],
        }

    elif index == 1:
        carried_from = [1]
        sources = _prepared_sources(_prior_output(records, 1)["context"])
        preserved: dict[str, list[dict]] = {}
        inventory = []
        for key, source_name, identifier in SOURCE_SPECS:
            received_rows = sources[key]
            preserved_rows = deepcopy(received_rows)
            preserved[key] = preserved_rows
            integrity_match = _digest(received_rows) == _digest(preserved_rows)
            inventory.append(
                {
                    "Source": source_name,
                    "Rows received": len(received_rows),
                    "Rows preserved": len(preserved_rows),
                    "Row identifier": identifier,
                    "Integrity": "Verified" if integrity_match else "Failed",
                }
            )
        output = {
            "source_inventory": inventory,
            "datasets": preserved,
            "received_rows": sum(row["Rows received"] for row in inventory),
            "preserved_rows": sum(row["Rows preserved"] for row in inventory),
            "source_control_passed": all(
                row["Rows received"] == row["Rows preserved"] and row["Integrity"] == "Verified"
                for row in inventory
            ),
        }

    elif index == 2:
        carried_from = [1, 2]
        receipt = _prior_output(records, 2)
        datasets = deepcopy(receipt["datasets"])
        requirements = {
            "fund_reference": ("Fund", "Share class", "Base currency", "Valuation frequency", "Valuation date"),
            "positions": ("Fund", "Position ID", "Quantity", "Local price", "Local currency", "FX rate to EUR", "Price timestamp"),
            "trades": ("Fund", "Trade ID", "Side", "Gross amount (EUR)", "Settlement"),
            "accounting_balances": ("Fund", "Record ID", "Balance", "Amount (EUR)"),
            "unit_and_flow_records": ("Fund", "Record ID", "Measure", "Amount", "Unit"),
            "valuation_policy": (
                "Fund",
                "Policy ID",
                "Swing enabled",
                "Flow threshold (%)",
                "Swing factor (bps)",
                "Minimum cash buffer (%)",
                "Minimum cash buffer base",
                "Settlement-date authority",
                "Exception ageing threshold (days)",
                "Reporting exposure review threshold (bps)",
            ),
            "cash_schedule": ("Fund", "Movement ID", "Movement", "Amount (EUR)"),
            "break_register": ("Fund", "Break ID", "Reconciliation event ID", "Age (days)"),
            "settlement_evidence": ("Fund", "Evidence ID", "Break ID", "Amount (EUR)", "Settlement date"),
            "reconciliation_events": ("Fund", "Event ID", "Event date", "Reconciliation status"),
        }
        missing_required_values = sum(
            1
            for key, fields in requirements.items()
            for row in datasets[key]
            for field in fields
            if field not in row or row[field] is None or row[field] == ""
        )
        expected_fund = _prior_output(records, 1)["context"]["fund"]
        invalid_fund_keys = sum(
            1
            for rows in datasets.values()
            for row in rows
            if "Fund" in row and row["Fund"] != expected_fund
        )
        duplicate_identifiers = 0
        for key, _source_name, identifier in SOURCE_SPECS:
            values = [row.get(identifier) for row in datasets[key]]
            duplicate_identifiers += len(values) - len(set(values))
        invalid_dates = sum(
            not _date_is_valid(row["Event date"], "%Y-%m-%d") for row in datasets["reconciliation_events"]
        )
        invalid_dates += sum(
            not _date_is_valid(row["Settlement date"], "%Y-%m-%d") for row in datasets["settlement_evidence"]
        )
        invalid_dates += sum(
            not _date_is_valid(row["Price timestamp"], "%Y-%m-%d %H:%M UTC") for row in datasets["positions"]
        )
        policy = datasets["valuation_policy"][0]
        invalid_policy_rules = sum(
            [
                not isinstance(policy["Swing enabled"], bool),
                not 0 < float(policy["Flow threshold (%)"]) <= 100,
                not 0 <= float(policy["Swing factor (bps)"]) <= 1_000,
                not 0 <= float(policy["Minimum cash buffer (%)"]) <= 100,
                policy["Minimum cash buffer base"] != "Opening ledger cash",
                policy["Settlement-date authority"] != "Executed trade confirmation",
                int(policy["Exception ageing threshold (days)"]) <= 0,
                float(policy["Reporting exposure review threshold (bps)"]) <= 0,
            ]
        )
        control_passed = (
            receipt["source_control_passed"]
            and missing_required_values == 0
            and invalid_fund_keys == 0
            and duplicate_identifiers == 0
            and invalid_dates == 0
            and invalid_policy_rules == 0
        )
        output = {
            "model": datasets,
            "fund_dimension_rows": len(datasets["fund_reference"]),
            "position_fact_rows": len(datasets["positions"]),
            "trade_fact_rows": len(datasets["trades"]),
            "reconciliation_fact_rows": len(datasets["reconciliation_events"]),
            "missing_required_values": missing_required_values,
            "invalid_fund_keys": invalid_fund_keys,
            "duplicate_identifiers": duplicate_identifiers,
            "invalid_dates": invalid_dates,
            "invalid_policy_rules": invalid_policy_rules,
            "control_passed": control_passed,
        }

    elif index == 3:
        carried_from = [3]
        structured = _prior_output(records, 3)
        positions = structured["model"]["positions"]
        accounting_rows = structured["model"]["accounting_balances"]
        position_rows = [
            {
                "Position": row["Position ID"],
                "Instrument": row["Instrument"],
                "Quantity": row["Quantity"],
                "Local price": row["Local price"],
                "Currency": row["Local currency"],
                "FX rate to EUR": row["FX rate to EUR"],
                "Value (EUR)": row["Quantity"] * row["Local price"] * row["FX rate to EUR"],
            }
            for row in positions
        ]
        total = sum(row["Value (EUR)"] for row in position_rows)
        expected = _named_amount(accounting_rows, "Balance", "Investments", "Amount (EUR)")
        output = {
            "positions": position_rows,
            "source_position_rows": len(positions),
            "total_position_value_eur": total,
            "expected_portfolio_value_eur": expected,
            "difference_eur": total - expected,
            "control_passed": abs(total - expected) < 0.005,
        }

    elif index == 4:
        carried_from = [3, 4]
        model = _prior_output(records, 3)["model"]
        valued_positions = _prior_output(records, 4)
        accounting_rows = deepcopy(model["accounting_balances"])
        accounting = {row["Balance"]: float(row["Amount (EUR)"]) for row in accounting_rows}
        flows = model["unit_and_flow_records"]
        trades = model["trades"]
        subscriptions = _named_amount(flows, "Measure", "Subscriptions")
        redemptions = _named_amount(flows, "Measure", "Redemptions")
        purchases = sum(float(row["Gross amount (EUR)"]) for row in trades if row["Side"] == "Buy")
        sales = sum(float(row["Gross amount (EUR)"]) for row in trades if row["Side"] == "Sell")
        collateral = _named_amount(model["cash_schedule"], "Movement", "Collateral", "Amount (EUR)")
        policy = model["valuation_policy"][0]
        minimum_buffer = float(policy["Minimum cash buffer (%)"])
        buffer_base = policy["Minimum cash buffer base"]
        forecast = cash_forecast(
            opening_cash=accounting["Ledger cash"],
            subscriptions=subscriptions,
            redemptions=redemptions,
            purchase_settlements=purchases,
            sale_settlements=sales,
            collateral=collateral,
            minimum_buffer_percent=minimum_buffer,
        )
        cash_movements = [
            {"Movement": "Opening ledger cash", "Signed amount (EUR)": accounting["Ledger cash"], "Source": "Accounting trial balance"},
            {"Movement": "Subscriptions", "Signed amount (EUR)": subscriptions, "Source": "Investor-flow register"},
            {"Movement": "Redemptions", "Signed amount (EUR)": -redemptions, "Source": "Investor-flow register"},
            {"Movement": "Purchase settlements", "Signed amount (EUR)": -purchases, "Source": "Validated trade ledger"},
            {"Movement": "Sale settlements", "Signed amount (EUR)": sales, "Source": "Validated trade ledger"},
            {"Movement": "Collateral", "Signed amount (EUR)": -collateral, "Source": "Cash and collateral schedule"},
        ]
        reconstructed_cash = sum(row["Signed amount (EUR)"] for row in cash_movements)
        cash_difference = reconstructed_cash - float(forecast["projected_cash"])
        investment_difference = valued_positions["total_position_value_eur"] - accounting["Investments"]
        output = {
            "accounting_balances": accounting_rows,
            "cash_movements": cash_movements,
            "cash_forecast": forecast,
            "minimum_buffer_percent": minimum_buffer,
            "minimum_buffer_base": buffer_base,
            "investment_rollup_difference_eur": investment_difference,
            "forecast_reconstruction_difference_eur": cash_difference,
            "cash_control_passed": abs(cash_difference) < 0.005 and abs(investment_difference) < 0.005,
            "forecast_substitution": (
                f"EUR {accounting['Ledger cash']:,.2f} + EUR {subscriptions:,.2f} − EUR {redemptions:,.2f} "
                f"− EUR {purchases:,.2f} + EUR {sales:,.2f} − EUR {collateral:,.2f} = EUR {forecast['projected_cash']:,.2f}"
            ),
            "buffer_substitution": (
                f"{minimum_buffer:.2f}% × {_money(accounting['Ledger cash'])} opening ledger cash "
                f"= {_money(float(forecast['required_buffer']))}"
            ),
        }

    elif index == 5:
        carried_from = [3]
        model = _prior_output(records, 3)["model"]
        break_row = deepcopy(model["break_register"][0])
        evidence = deepcopy(model["settlement_evidence"])
        policy = model["valuation_policy"][0]
        source_complete = all(
            row.get("Evidence ID") and row.get("Amount (EUR)") is not None and row.get("Settlement date") and row.get("Source")
            for row in evidence
        )
        dates_valid = all(_date_is_valid(row["Settlement date"], "%Y-%m-%d") for row in evidence)
        settlement_date_conflict = len({row["Settlement date"] for row in evidence}) > 1
        calculation_conflict = len({float(row["Amount (EUR)"]) for row in evidence}) > 1
        authority_name = policy["Settlement-date authority"]
        authority_record = next((row for row in evidence if row["Source"] == authority_name), None)
        accepted_date = authority_record["Settlement date"] if authority_record else None
        conflicting_sources = [
            row["Source"] for row in evidence if accepted_date and row["Settlement date"] != accepted_date
        ]
        expected_days = int(policy["Exception ageing threshold (days)"])
        anomaly = anomaly_assessment(
            source_complete=source_complete,
            dates_valid=dates_valid,
            observed_days=int(break_row["Age (days)"]),
            expected_days=expected_days,
            calculation_conflict=calculation_conflict,
        )
        updated_events = deepcopy(model["reconciliation_events"])
        target_id = break_row["Reconciliation event ID"]
        target = next((row for row in updated_events if row["Event ID"] == target_id), None)
        original_status = target["Reconciliation status"] if target else "Missing event"
        resolution_eligible = bool(
            target is not None
            and anomaly["score"] is not None
            and settlement_date_conflict
            and authority_record
            and conflicting_sources
        )
        if resolution_eligible:
            target.update(
                {
                    "Reconciliation status": "Matched",
                    "Match method": "Manual",
                    "Amount under investigation (EUR)": 0.0,
                    "Age (days)": 0,
                    "Timeliness": "Resolved after review",
                    "Investigation note": f"{authority_name} established {accepted_date} as the contractual settlement date.",
                    "Resolution reference": "RES-10421",
                }
            )
        resolved = target is not None and target["Reconciliation status"] == "Matched"
        output = {
            "break": break_row,
            "settlement_evidence": evidence,
            "source_complete": source_complete,
            "dates_valid": dates_valid,
            "settlement_date_conflict": settlement_date_conflict,
            "calculation_conflict": calculation_conflict,
            "authority_source": authority_name,
            "accepted_settlement_date": accepted_date,
            "conflicting_sources": conflicting_sources,
            "resolution_eligible": resolution_eligible,
            "expected_days": expected_days,
            "anomaly": anomaly,
            "score_substitution": (
                f"0.3 × {int(int(break_row['Age (days)']) > expected_days)} + "
                f"0.7 × {int(calculation_conflict)} = {anomaly['score']:.1f}"
                if anomaly["score"] is not None
                else "Not scored because source data failed validation"
            ),
            "confirmed_cause": break_row["Root cause"],
            "resolution": {
                "Resolution reference": "RES-10421",
                "Owner": "Fictional reconciliation analyst",
                "Authority rule": f"Use {authority_name} for the contractual settlement date.",
                "Action": f"Compared {len(evidence)} records, identified {', '.join(conflicting_sources)}, and recorded {accepted_date} as the accepted date.",
                "Original status": original_status,
                "Final status": "Resolved" if resolved else "Not resolved",
            },
            "resolved_event_id": target_id,
            "updated_events": updated_events,
            "outstanding_before": sum(row["Reconciliation status"] != "Matched" for row in model["reconciliation_events"]),
            "outstanding_after": sum(row["Reconciliation status"] != "Matched" for row in updated_events),
            "final_status": "Resolved for the guided case" if resolved else "Resolution blocked",
        }

    elif index == 6:
        carried_from = [3, 4, 5, 6]
        model = _prior_output(records, 3)["model"]
        position_result = _prior_output(records, 4)
        accounting_result = _prior_output(records, 5)
        reconciliation_result = _prior_output(records, 6)
        balances = {row["Balance"]: float(row["Amount (EUR)"]) for row in accounting_result["accounting_balances"]}
        flows = model["unit_and_flow_records"]
        policy = model["valuation_policy"][0]
        subscriptions = _named_amount(flows, "Measure", "Subscriptions")
        redemptions = _named_amount(flows, "Measure", "Redemptions")
        units = _named_amount(flows, "Measure", "Units in issue")
        net_flow = subscriptions - redemptions
        valuation = Valuation(
            portfolio=position_result["total_position_value_eur"],
            cash=balances["Ledger cash"],
            receivables=balances["Receivables"],
            payables=balances["Payables"],
            expenses=balances["Accrued expenses"],
            units=units,
            flow=net_flow,
            threshold=float(policy["Flow threshold (%)"]),
            bps=int(policy["Swing factor (bps)"]),
            swing=bool(policy["Swing enabled"]),
        )
        result = valuation.calculate()
        expected_assets = valuation.portfolio + valuation.cash + valuation.receivables
        expected_liabilities = valuation.payables + valuation.expenses
        checks = {
            "Assets reconstruct": abs(result["assets"] - expected_assets) < 0.005,
            "Liabilities reconstruct": abs(result["liabilities"] - expected_liabilities) < 0.005,
            "Net Asset Value reconstructs": abs(result["nav"] - (result["assets"] - result["liabilities"])) < 0.005,
            "Price per unit reconstructs": abs(result["price"] - result["nav"] / units) < 0.0000001,
            "Reconciliation result consumed": reconciliation_result["final_status"] == "Resolved for the guided case",
        }
        original_exposure = float(reconciliation_result["break"]["Amount under investigation (EUR)"])
        output = {
            "assets": result["assets"],
            "liabilities": result["liabilities"],
            "nav": result["nav"],
            "units": units,
            "nav_per_unit": result["price"],
            "net_flow": net_flow,
            "flow_percent": result["flow_pct"],
            "illustrative_threshold_percent": valuation.threshold,
            "illustrative_swing_factor_bps": valuation.bps,
            "reporting_exposure_review_threshold_bps": float(policy["Reporting exposure review threshold (bps)"]),
            "swing_triggered": result["triggered"],
            "distribution_price": result["distribution_price"],
            "calculation_checks": checks,
            "calculation_control_passed": all(checks.values()),
            "resolved_exposure_scale_bps": original_exposure / result["nav"] * 10_000,
            "nav_substitution": f"{_money(result['assets'])} − {_money(result['liabilities'])} = {_money(result['nav'])}",
            "price_substitution": f"{_money(result['nav'])} ÷ {units:,.0f} units = EUR {result['price']:,.4f} per unit",
            "flow_substitution": f"|{_money(net_flow)}| ÷ {_money(result['nav'])} × 100 = {result['flow_pct']:.4f}%",
        }

    elif index == 7:
        carried_from = [6, 7]
        reconciliation_result = _prior_output(records, 6)
        valuation_result = _prior_output(records, 7)
        events = deepcopy(reconciliation_result["updated_events"])
        matched = [row for row in events if row["Reconciliation status"] == "Matched"]
        outstanding = [row for row in events if row["Reconciliation status"] != "Matched"]
        detail_total = sum(float(row["Amount under investigation (EUR)"]) for row in outstanding)
        reported_total = sum(
            amount
            for _status, amount in pd.DataFrame(events).groupby("Reconciliation status")["Amount under investigation (EUR)"].sum().items()
            if _status != "Matched"
        )
        exposure_threshold_bps = valuation_result["reporting_exposure_review_threshold_bps"]
        assessments = []
        for row in outstanding:
            exposure_bps = float(row["Amount under investigation (EUR)"]) / valuation_result["nav"] * 10_000
            within_threshold = exposure_bps <= exposure_threshold_bps
            assessments.append(
                {
                    "Event ID": row["Event ID"],
                    "Open exposure (EUR)": row["Amount under investigation (EUR)"],
                    "Exposure to NAV (bps)": exposure_bps,
                    "Illustrative threshold (bps)": exposure_threshold_bps,
                    "Decision": "Monitor below threshold" if within_threshold else "Escalate before delivery",
                    "Owner": "Fictional reconciliation operations team",
                    "Target resolution": "18 September 2026 · 12:00 UTC",
                    "Status": "Controlled follow-up" if within_threshold else "Delivery blocker",
                    "Blocker": "External confirmation pending",
                    "Next action": "Obtain confirmation, validate the amount and reassess accounting impact before closure.",
                }
            )
        source_to_visual = abs(detail_total - reported_total) < 0.005
        output = {
            "funds": len({row["Fund"] for row in events}),
            "event_rows": len(events),
            "event_details": events,
            "matched_events": len(matched),
            "outstanding_events": len(outstanding),
            "match_rate_percent": len(matched) / len(events) * 100 if events else 0.0,
            "outstanding_exposure_eur": reported_total,
            "detail_total_eur": detail_total,
            "source_to_visual_control_passed": source_to_visual,
            "residual_assessments": assessments,
            "all_open_items_assessed": len(assessments) == len(outstanding) and all(
                row["Owner"]
                and row["Target resolution"]
                and row["Status"]
                and row["Blocker"]
                and row["Next action"]
                and row["Decision"]
                for row in assessments
            ),
            "materiality_control_passed": all(row["Status"] == "Controlled follow-up" for row in assessments),
            "match_rate_substitution": f"{len(matched)} matched ÷ {len(events)} events × 100 = {len(matched) / len(events) * 100:.2f}%" if events else "No events",
            "exposure_substitution": f"{_money(reported_total)} ÷ {_money(valuation_result['nav'])} × 10,000 = {reported_total / valuation_result['nav'] * 10_000:.2f} bps",
            "resolved_event_carried_forward": any(
                row["Event ID"] == reconciliation_result["resolved_event_id"] and row["Reconciliation status"] == "Matched"
                for row in events
            ),
        }

    elif index == 8:
        carried_from = list(range(1, 9))
        receipt = _prior_output(records, 2)
        structured = _prior_output(records, 3)
        positions = _prior_output(records, 4)
        accounting = _prior_output(records, 5)
        reconciliation = _prior_output(records, 6)
        valuation = _prior_output(records, 7)
        reporting = _prior_output(records, 8)

        source_ok = receipt["source_control_passed"]
        rules_ok = (
            structured["control_passed"]
            and reconciliation["anomaly"]["score"] is not None
            and reconciliation["settlement_date_conflict"]
            and reconciliation["authority_source"] == "Executed trade confirmation"
            and reconciliation["resolution_eligible"]
        )
        accounting_ok = (
            positions["control_passed"]
            and abs(accounting["investment_rollup_difference_eur"]) < 0.005
            and accounting["cash_control_passed"]
            and valuation["calculation_control_passed"]
            and reconciliation["final_status"] == "Resolved for the guided case"
            and reporting["source_to_visual_control_passed"]
            and reporting["all_open_items_assessed"]
            and reporting["materiality_control_passed"]
        )
        residual = reporting["residual_assessments"][0] if reporting["residual_assessments"] else {}
        operational_controls = [
            {
                "Control": "Residual event follow-up",
                "Owner": residual.get("Owner"),
                "Status": residual.get("Status"),
                "Target": residual.get("Target resolution"),
                "Blocker": residual.get("Blocker"),
                "Next action": residual.get("Next action"),
            },
            {
                "Control": "Run procedure",
                "Owner": "Fictional fund-accounting preparer",
                "Status": "Ready",
                "Target": "Before simulated delivery",
                "Blocker": "None",
                "Next action": "Retain the ten-stage evidence and calculation checks.",
            },
            {
                "Control": "Escalation",
                "Owner": "Fictional operations lead",
                "Status": "Ready",
                "Target": "Immediate if a gate fails",
                "Blocker": "None",
                "Next action": "Stop delivery and route the failed evidence to its named owner.",
            },
            {
                "Control": "Recovery",
                "Owner": "Fictional platform support",
                "Status": "Ready",
                "Target": "On demand",
                "Blocker": "None",
                "Next action": "Restart from the preserved source pack and regenerate the fingerprint.",
            },
        ]
        operational_fields = ("Owner", "Status", "Target", "Blocker", "Next action")
        operational_ok = (
            accounting["cash_forecast"]["status"] == "Sufficient"
            and bool(reconciliation["resolution"]["Owner"])
            and reporting["all_open_items_assessed"]
            and reporting["materiality_control_passed"]
            and all(all(row.get(field) for field in operational_fields) for row in operational_controls)
            and all(row["Status"] in {"Ready", "Controlled follow-up"} for row in operational_controls)
        )

        source_uat = source_ok and receipt["received_rows"] == receipt["preserved_rows"]
        calculation_uat = positions["control_passed"] and accounting["cash_control_passed"] and valuation["calculation_control_passed"]
        exception_uat = (
            reconciliation["settlement_date_conflict"]
            and reconciliation["authority_source"] == "Executed trade confirmation"
            and reporting["resolved_event_carried_forward"]
            and reporting["matched_events"] == 5
        )
        passing_gate_sample = [{"Result": "Passed"} for _ in QUALITY_GATES]
        failed_gate_sample = deepcopy(passing_gate_sample)
        failed_gate_sample[2]["Result"] = "Failed"
        passing_uat_sample = [{"Result": "Passed"} for _ in range(4)]
        guard_blocks_failure = not _delivery_allowed(failed_gate_sample, passing_uat_sample)
        guard_allows_success = _delivery_allowed(passing_gate_sample, passing_uat_sample)
        acceptance_tests = [
            {
                "Test": "UAT-01 · Source lineage",
                "Expected": "All rows and fingerprints are preserved",
                "Actual": f"{receipt['received_rows']} received; {receipt['preserved_rows']} preserved",
                "Result": "Passed" if source_uat else "Failed",
            },
            {
                "Test": "UAT-02 · Calculation reconstruction",
                "Expected": "Position, cash and valuation equations rebuild",
                "Actual": f"Position difference EUR {positions['difference_eur']:,.2f}; cash difference EUR {accounting['forecast_reconstruction_difference_eur']:,.2f}; {sum(valuation['calculation_checks'].values())}/{len(valuation['calculation_checks'])} valuation checks",
                "Result": "Passed" if calculation_uat else "Failed",
            },
            {
                "Test": "UAT-03 · Exception carry-forward",
                "Expected": "The date conflict follows the authority rule and REC-003 becomes matched",
                "Actual": f"Authority: {reconciliation['authority_source']}; {reporting['matched_events']} of {reporting['event_rows']} events matched",
                "Result": "Passed" if exception_uat else "Failed",
            },
            {
                "Test": "UAT-04 · Delivery guard",
                "Expected": "A failed gate blocks; all successful evidence allows",
                "Actual": f"Failure blocked: {guard_blocks_failure}; success allowed: {guard_allows_success}",
                "Result": "Passed" if guard_blocks_failure and guard_allows_success else "Failed",
            },
        ]
        uat_ok = all(row["Result"] == "Passed" for row in acceptance_tests)
        first_four_values = [source_ok, rules_ok, accounting_ok, operational_ok]
        first_four_evidence = [
            f"{receipt['received_rows']} received rows equal {receipt['preserved_rows']} preserved rows across {len(receipt['source_inventory'])} sources.",
            f"Missing values {structured['missing_required_values']}; invalid dates {structured['invalid_dates']}; date conflict detected; authority {reconciliation['authority_source']}.",
            f"Position difference EUR {positions['difference_eur']:,.2f}; cash difference EUR {accounting['forecast_reconstruction_difference_eur']:,.2f}; open exposure {residual.get('Exposure to NAV (bps)', 0):.2f} bps is assessed against policy.",
            f"Cash status {accounting['cash_forecast']['status']}; {len(operational_controls)} owner, target, blocker, status and next-action records validated.",
        ]
        preliminary_gates = [
            {
                "Gate": QUALITY_GATES[i][0],
                "Question": QUALITY_GATES[i][1],
                "Evidence": first_four_evidence[i],
                "Result": "Passed" if first_four_values[i] else "Failed",
            }
            for i in range(4)
        ]
        review_fingerprint = valuation_fingerprint(
            _prior_output(records, 1)["context"],
            {"stage_outputs": [record["output"] for record in records], "operational_controls": operational_controls},
            {"quality_gates": preliminary_gates, "acceptance_tests": acceptance_tests},
        )
        review_prerequisites = all(first_four_values) and uat_ok and len(review_fingerprint) == 64
        preparer = {
            "Role": "Fictional fund-accounting preparer",
            "Actor ID": "SIM-PREPARER-01",
            "Status": "Recorded" if review_prerequisites else "Not recorded",
            "Recorded at": "2026-09-18T08:20:00+00:00" if review_prerequisites else "Not recorded",
            "Evidence package": review_fingerprint,
        }
        checker = {
            "Role": "Fictional independent checker",
            "Actor ID": "SIM-CHECKER-01",
            "Status": "Recorded" if review_prerequisites else "Not recorded",
            "Recorded at": "2026-09-18T08:35:00+00:00" if review_prerequisites else "Not recorded",
            "Evidence package": review_fingerprint,
        }
        independence_checks = {
            "Different actor IDs": preparer["Actor ID"] != checker["Actor ID"],
            "Checker after preparer": review_prerequisites
            and datetime.fromisoformat(checker["Recorded at"]) > datetime.fromisoformat(preparer["Recorded at"]),
            "Same evidence fingerprint": preparer["Evidence package"] == checker["Evidence package"],
        }
        explainability_ok = (
            review_prerequisites
            and preparer["Status"] == "Recorded"
            and checker["Status"] == "Recorded"
            and all(independence_checks.values())
        )
        quality_gates = preliminary_gates + [
            {
                "Gate": QUALITY_GATES[4][0],
                "Question": QUALITY_GATES[4][1],
                "Evidence": f"Four change UAT cases passed; distinct preparer and checker records are tied to fingerprint {review_fingerprint[:12]}…",
                "Result": "Passed" if explainability_ok else "Failed",
            }
        ]
        ready = _delivery_allowed(quality_gates, acceptance_tests) and explainability_ok
        acceptance_criteria = _prior_output(records, 1)["acceptance_criteria"]
        pre_delivery_acceptance = [
            {
                "Acceptance criterion": acceptance_criteria[0],
                "Status": "Met" if source_ok and structured["control_passed"] else "Not met",
            },
            {
                "Acceptance criterion": acceptance_criteria[1],
                "Status": "Met" if calculation_uat and reporting["source_to_visual_control_passed"] else "Not met",
            },
            {
                "Acceptance criterion": acceptance_criteria[2],
                "Status": "Met" if reconciliation["final_status"] == "Resolved for the guided case" and reporting["all_open_items_assessed"] and reporting["materiality_control_passed"] else "Not met",
            },
        ]
        output = {
            "quality_gates": quality_gates,
            "acceptance_tests": acceptance_tests,
            "uat_tests_passed": sum(row["Result"] == "Passed" for row in acceptance_tests),
            "uat_tests_total": len(acceptance_tests),
            "operational_controls": operational_controls,
            "preparer": preparer,
            "checker": checker,
            "independence_checks": independence_checks,
            "control_package_fingerprint": review_fingerprint,
            "fingerprint_scope": "Stages 01–08, four operational-control records, gates 01–04 and four change-lifecycle User Acceptance Testing results",
            "acceptance_criteria": acceptance_criteria,
            "pre_delivery_acceptance": pre_delivery_acceptance,
            "delivery_ready": ready,
            "decision": "Ready for simulated delivery" if ready else "Delivery blocked by failed control evidence",
        }

    else:
        carried_from = [9]
        review = _prior_output(records, 9)
        review_ready = bool(review["delivery_ready"] and review["decision"] == "Ready for simulated delivery")
        delivery_specs = [
            {
                "Control ID": "DEL-CLIENT-001",
                "Process": "Client submission",
                "Cut-off": "2026-09-18T09:00:00+00:00",
                "Actual": "2026-09-18T08:42:00+00:00",
                "Recipient": "Fictional client-reporting mailbox",
                "Acknowledgement": "ACK-CLIENT-001",
            },
            {
                "Control ID": "DEL-PRICE-001",
                "Process": "Fund-price diffusion",
                "Cut-off": "2026-09-18T09:15:00+00:00",
                "Actual": "2026-09-18T08:47:00+00:00",
                "Recipient": "Fictional fund-price service",
                "Acknowledgement": "ACK-PRICE-001",
            },
            {
                "Control ID": "DEL-TA-001",
                "Process": "Transfer Agency unit-register update",
                "Cut-off": "2026-09-18T09:30:00+00:00",
                "Actual": "2026-09-18T08:51:00+00:00",
                "Recipient": "Fictional Transfer Agency register",
                "Acknowledgement": "ACK-TA-001",
            },
        ]
        distribution_controls = []
        for spec in delivery_specs:
            on_time = review_ready and datetime.fromisoformat(spec["Actual"]) <= datetime.fromisoformat(spec["Cut-off"])
            acknowledged = review_ready and bool(spec["Acknowledgement"])
            distribution_controls.append(
                {
                    **spec,
                    "Actual": spec["Actual"] if review_ready else "Not run",
                    "Acknowledgement": spec["Acknowledgement"] if review_ready else "Not issued",
                    "Timeliness": "On time" if on_time else "Not assessed",
                    "Status": "Simulated acknowledgement" if on_time and acknowledged else "Blocked by control decision",
                }
            )
        delivery_control_passed = review_ready and all(
            row["Timeliness"] == "On time" and row["Status"] == "Simulated acknowledgement"
            for row in distribution_controls
        )
        acceptance_results = [
            *review["pre_delivery_acceptance"],
            {
                "Acceptance criterion": review["acceptance_criteria"][3],
                "Status": "Met" if delivery_control_passed else "Not met",
            },
        ]
        output = {
            "delivery_ready": delivery_control_passed,
            "delivery_control_passed": delivery_control_passed,
            "client_submission": "Simulated complete" if delivery_control_passed else "Not submitted",
            "market_diffusion": "Simulated complete" if delivery_control_passed else "Not distributed",
            "cam_role": "Client Account Manager (CAM) coordinates the simulated client communication and follow-up.",
            "distribution_channels": distribution_controls,
            "acceptance_results": acceptance_results,
            "evidence_package": review["control_package_fingerprint"],
            "documented_projects_connected": len(PROJECTS),
            "monitoring_action": "Retain the evidence, monitor the assigned open event and use lessons to improve the next controlled cycle.",
        }

    return {
        "step": index + 1,
        "title": STEPS[index]["title"],
        "completed_at_utc": now,
        "carried_from_stages": carried_from,
        "output": output,
    }


def _money(value: float) -> str:
    return f"EUR {value:,.2f}"


EUR_COLUMN = st.column_config.NumberColumn(format="localized")


def _render_output(index: int, record: dict) -> None:
    output = record["output"]
    stage_guides = {
        0: ("scope",), 1: ("sources",), 2: ("model",), 3: ("positions",),
        5: ("reconciliation", "anomaly"), 6: ("nav", "swing"),
        7: ("reporting",), 8: ("quality",), 9: ("delivery",),
    }
    for guide in stage_guides.get(index, ()):
        explain(guide)
    if record["carried_from_stages"]:
        stages = ", ".join(f"{number:02d}" for number in record["carried_from_stages"])
        st.caption(f"Evidence consumed from completed stage(s): {stages}")

    if index == 0:
        context = output["context"]
        aligned_dataframe(
            pd.DataFrame(
                [
                    ["Fund", context["fund"]],
                    ["Share class", context["share_class"]],
                    ["Base currency", context["base_currency"]],
                    ["Valuation date", context["valuation_date"]],
                    ["Business question", output["business_question"]],
                ],
                columns=["Case element", "Prepared value"],
            ),
            hide_index=True,
            width="stretch",
        )
        st.markdown("**Acceptance criteria carried to the final stage**")
        aligned_dataframe(
            pd.DataFrame(
                [{"Criterion": f"AC-{number:02d}", "Required outcome": text} for number, text in enumerate(output["acceptance_criteria"], 1)]
            ),
            hide_index=True,
            width="stretch",
        )

    elif index == 1:
        aligned_dataframe(pd.DataFrame(output["source_inventory"]), hide_index=True, width="stretch")
        if output["source_control_passed"]:
            st.success(f"Source control passed: {output['received_rows']} received rows = {output['preserved_rows']} preserved rows, with matching fingerprints.")
        else:
            st.error("Source control failed. Later stages must not rely on this source pack.")

    elif index == 2:
        aligned_dataframe(
            pd.DataFrame(
                [
                    ["Fund dimension", output["fund_dimension_rows"], "One row per fund"],
                    ["Position fact", output["position_fact_rows"], "One row per holding"],
                    ["Trade fact", output["trade_fact_rows"], "One row per trade"],
                    ["Reconciliation fact", output["reconciliation_fact_rows"], "One row per event"],
                ],
                columns=["Model table", "Rows", "Grain"],
            ),
            hide_index=True,
            width="stretch",
        )
        checks = pd.DataFrame(
            [
                ["Missing required values", output["missing_required_values"]],
                ["Invalid fund keys", output["invalid_fund_keys"]],
                ["Duplicate identifiers", output["duplicate_identifiers"]],
                ["Invalid dates", output["invalid_dates"]],
                ["Invalid policy rules", output["invalid_policy_rules"]],
            ],
            columns=["Validation check", "Exceptions"],
        )
        aligned_dataframe(checks, hide_index=True, width="stretch")
        (st.success if output["control_passed"] else st.error)(
            "The structured model passed every required-field, key, date, identifier and policy check."
            if output["control_passed"]
            else "The structured model contains validation exceptions."
        )

    elif index == 3:
        aligned_dataframe(
            pd.DataFrame(output["positions"]),
            hide_index=True,
            width="stretch",
            column_config={"Quantity": EUR_COLUMN, "Local price": EUR_COLUMN, "FX rate to EUR": EUR_COLUMN, "Value (EUR)": EUR_COLUMN},
        )
        result_metric("Reconstructed investment value", _money(output["total_position_value_eur"]), border=True)
        (st.success if output["control_passed"] else st.error)(
            f"Position roll-up compared with accounting. Difference: {_money(output['difference_eur'])}."
        )

    elif index == 4:
        st.info(
            "Two questions, two views: accounting shows what the fund owns and owes; "
            "the cash forecast estimates what will be available after the listed movements. "
            "An expected subscription is not confirmation that an investor's money has arrived."
        )
        with st.expander("Investor subscriptions, investment execution and settlement", expanded=True):
            st.markdown(
                "1. **Investors subscribe:** they put money into the fund and receive fund units. "
                "For example, EUR 10,000 at EUR 100 per unit buys 100 units, ignoring fees and pricing adjustments.\n"
                "2. **The manager invests:** the fund uses pooled cash to buy shares, bonds or other assets. "
                "Investors own fund units; the fund holds the underlying investments.\n"
                "3. **Trades settle:** a trade is agreed on trade date; payment and delivery occur on settlement date. "
                "Purchase settlements use cash, while sale settlements bring cash back.\n"
                "4. **Investors redeem:** the fund pays investors who withdraw. The manager plans cash "
                "for withdrawals, trade payments, expenses and a reserve; subscriptions need not all be invested immediately."
            )
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("**Accounting balances**")
            aligned_dataframe(
                pd.DataFrame(output["accounting_balances"])[["Record ID", "Balance", "Amount (EUR)"]],
                hide_index=True,
                width="stretch",
                column_config={"Amount (EUR)": EUR_COLUMN},
            )
        with right:
            st.markdown("**Expected cash movements**")
            aligned_dataframe(
                pd.DataFrame(output["cash_movements"]),
                hide_index=True,
                width="stretch",
                column_config={"Signed amount (EUR)": EUR_COLUMN},
            )
        st.code(output["forecast_substitution"], language=None)
        st.code(output["buffer_substitution"], language=None)
        forecast = output["cash_forecast"]
        a, b, c = st.columns(3)
        with a:
            result_metric("Projected cash", _money(forecast["projected_cash"]), border=True)
        with b:
            result_metric("Required buffer", _money(forecast["required_buffer"]), border=True)
        with c:
            result_metric("Buffer headroom", _money(forecast["buffer_headroom"]), border=True)
        st.badge(f"Forecast buffer test · {forecast['status']}", color="green" if forecast["status"] == "Sufficient" else "red")
        st.caption(
            f"The illustrative {output['minimum_buffer_percent']:.2f}% policy uses {output['minimum_buffer_base'].lower()} as its denominator. "
            "Projected cash supports liquidity planning; ledger cash remains the accounting input to Net Asset Value."
        )
        movements = {row["Movement"]: float(row["Signed amount (EUR)"]) for row in output["cash_movements"]}
        st.markdown(
            f"**Investor-flow analysis:** expected investor subscriptions are {_money(movements['Subscriptions'])}; "
            f"expected redemption payments are {_money(-movements['Redemptions'])}. "
            f"Together they produce a net investor flow of {_money(movements['Subscriptions'] + movements['Redemptions'])}. "
            "The opening cash is an existing book balance, not a measure of all money ever contributed by investors."
        )
        st.markdown(
            f"**Required buffer: minimum liquidity reserve.** This example reserves {output['minimum_buffer_percent']:.2f}% "
            f"of opening ledger cash: {_money(forecast['required_buffer'])}. It is a policy threshold, "
            "not a payment or expense. **Headroom = projected cash minus that minimum**: "
            f"{_money(forecast['buffer_headroom'])}. Positive headroom means the forecast ends above the reserve. "
            "It does not mean the whole surplus is approved for new investment."
        )
        st.caption(
            "This is an illustrative policy, not a universal fund requirement. The forecast sums the listed movements; "
            "it does not prove sufficient cash at every settlement time or in every currency. Expected receipts may be "
            "delayed and cash may be restricted. Bank reconciliation and a dated cash schedule are separate checks."
        )
        with st.expander("Accounting balances and cash-flow definitions"):
            st.markdown(
                "| Term | Meaning and connection to this case |\n"
                "| --- | --- |\n"
                "| Investments | Value of assets held by the fund. These are investments, not spendable bank cash; the previous stage reconstructs their value. |\n"
                "| Ledger cash | Cash recorded in the accounting books. It starts this forecast and remains the cash input to the later NAV calculation. Bank reconciliation checks it against bank records. |\n"
                "| Receivables | Amounts owed to the fund, such as investment income or unsettled sale proceeds. They are assets, but are not yet cash received. |\n"
                "| Payables | Outstanding amounts the fund owes, such as unsettled purchases. |\n"
                "| Accrued expenses | Costs already incurred but not yet paid, such as management, custody or audit fees. They reduce net assets. |\n"
                "| Subscriptions | Expected cash from investors buying fund units; actual receipt needs confirmation. |\n"
                "| Redemptions | Expected payments to investors withdrawing from the fund. |\n"
                "| Purchase / sale settlements | Cash paid for investments bought / cash received for investments sold. Trade agreement and cash settlement can occur on different dates. |\n"
                "| Collateral | Cash posted as security for an obligation. It reduces available cash here, but is not automatically a fee or loss; it may later be released. |\n"
                "| Projected cash | Opening cash plus the signed expected movements shown above. It is an estimate, not a bank-confirmed balance. |\n"
                "| Required buffer / headroom | Minimum reserve under the example policy / the forecast balance left above that minimum. |"
            )
            st.markdown(
                "**Double-counting control:** the accounting table is a balance snapshot; the forecast uses "
                "only the listed expected movements. Do not also subtract all payables and expenses, or add all "
                "receivables, without mapping their settlement dates and checking overlaps with those movements. "
                "The full receivable, payable and expense balances are not separately scheduled in this forecast.\n\n"
                "**Connection to the next stages:** net assets measure investors' ownership value "
                "(assets minus liabilities). Cash forecasting measures expected payment capacity. "
                "Replacing ledger cash with forecast cash in the current NAV could mix accounting dates and count movements twice."
            )
        with st.expander("Basis points (bps) and the EUR 500,000 fee example"):
            st.markdown(
                "**Basis points (bps)** express small percentages: "
                "1 bp = 0.01 percentage point; 100 bps = 1%; 50 bps = 0.50%. "
                f"The {output['minimum_buffer_percent']:.2f}% reserve rate here equals "
                f"{output['minimum_buffer_percent'] * 100:,.0f} bps of opening cash.\n\n"
                "**Separate fee example:** assume an annual management fee of 50 bps on a constant "
                "EUR 100 million fee base. One percent of EUR 100 million is EUR 1 million; "
                "0.50% is half of that, so the annual fee is EUR 500,000."
            )
            st.code("50 bps / 10,000 = 0.005\nEUR 100,000,000 x 0.005 = EUR 500,000 per year", language=None)
            st.markdown(
                "The fee base is the amount specified by the fee terms, often a measure of fund assets; "
                "it is not automatically the cash balance. If fees use changing daily values, the actual annual "
                "total varies. This example explains percentages; it does not calculate the case's accrued expenses.\n\n"
                "Later reporting uses bps to express exposure relative to NAV."
            )

    elif index == 5:
        aligned_dataframe(
            pd.DataFrame(output["settlement_evidence"])[["Evidence ID", "Source", "Amount (EUR)", "Settlement date"]],
            hide_index=True,
            width="stretch",
            column_config={"Amount (EUR)": EUR_COLUMN},
        )
        item = output["break"]
        st.markdown(
            f"**Detected difference:** {item['Difference type']} · **Date conflict found:** {output['settlement_date_conflict']} · "
            f"**Elapsed:** {item['Age (days)']} days · **Expected:** {output['expected_days']} days"
        )
        st.markdown(
            f"**Authority rule:** {output['authority_source']} establishes **{output['accepted_settlement_date']}**. "
            f"Conflicting source: **{', '.join(output['conflicting_sources'])}**."
        )
        st.code(output["score_substitution"], language=None)
        st.markdown(f"**Rule result:** {output['anomaly']['score']:.1f} — {output['anomaly']['band']}")
        st.markdown(f"**Confirmed cause:** {output['confirmed_cause']}", text_alignment="justify")
        aligned_dataframe(pd.DataFrame([output["resolution"]]), hide_index=True, width="stretch")
        (st.success if output["final_status"] == "Resolved for the guided case" else st.error)(
            f"{output['final_status']}. Outstanding events changed from {output['outstanding_before']} to {output['outstanding_after']}; the updated event population now feeds reporting."
        )

    elif index == 6:
        aligned_dataframe(
            pd.DataFrame(
                [
                    ["Total assets", output["assets"]],
                    ["Total liabilities", -output["liabilities"]],
                    ["Net Asset Value", output["nav"]],
                ],
                columns=["Calculation line", "Amount (EUR)"],
            ),
            hide_index=True,
            width="stretch",
            column_config={"Amount (EUR)": EUR_COLUMN},
        )
        a, b, c, d = st.columns(4)
        with a:
            result_metric("Net Asset Value", _money(output["nav"]), border=True)
        with b:
            result_metric("Units in issue", f"{output['units']:,.0f}", border=True)
        with c:
            result_metric("Price per unit", f"EUR {output['nav_per_unit']:,.4f}", border=True)
        with d:
            result_metric("Distribution price", f"EUR {output['distribution_price']:,.4f}", border=True)
        st.code(
            output["nav_substitution"] + "\n" + output["price_substitution"] + "\n" + output["flow_substitution"],
            language=None,
        )
        st.markdown(
            f"The net flow is {_money(output['net_flow'])}, or **{output['flow_percent']:.4f}%** of Net Asset Value. "
            f"It is below the illustrative **{output['illustrative_threshold_percent']:.2f}%** threshold, so the "
            f"**{output['illustrative_swing_factor_bps']} bps** teaching factor is not applied.",
            text_alignment="justify",
        )
        st.caption(
            f"The resolved EUR 1.45 million exposure equals {output['resolved_exposure_scale_bps']:.2f} bps of Net Asset Value as a scale reference; it was a settlement-date exception, not a booked valuation adjustment."
        )

    elif index == 7:
        event_details = output.get("event_details")
        if event_details is None:
            event_details = _prior_output(st.session_state.guided_pipeline_records, 6)["updated_events"]
        explain_events(event_details)
        a, b, c, d = st.columns(4)
        with a:
            result_metric("Unique funds", output["funds"], border=True)
        with b:
            result_metric("Event rows", output["event_rows"], border=True)
        with c:
            result_metric("Match rate", f"{output['match_rate_percent']:.1f}%", border=True)
        with d:
            result_metric("Open exposure", _money(output["outstanding_exposure_eur"]), border=True)
        st.code(output["match_rate_substitution"] + "\n" + output["exposure_substitution"], language=None)
        (st.success if output["source_to_visual_control_passed"] else st.error)(
            f"Source-to-visual control: detail exposure {_money(output['detail_total_eur'])} and reported exposure {_money(output['outstanding_exposure_eur'])}."
        )
        st.markdown("**Remaining open-event assessment**")
        aligned_dataframe(
            pd.DataFrame(output["residual_assessments"]),
            hide_index=True,
            width="stretch",
            column_config={
                "Open exposure (EUR)": EUR_COLUMN,
                "Exposure to NAV (bps)": st.column_config.NumberColumn(format="%.2f"),
                "Illustrative threshold (bps)": st.column_config.NumberColumn(format="%.2f"),
            },
        )

    elif index == 8:
        st.markdown("**Calculated quality gates**")
        aligned_dataframe(pd.DataFrame(output["quality_gates"]), hide_index=True, width="stretch")
        st.markdown("**Operational readiness records**")
        aligned_dataframe(pd.DataFrame(output["operational_controls"]), hide_index=True, width="stretch")
        st.markdown("**Change-lifecycle User Acceptance Testing evidence**")
        st.caption("These four cases validate the automated workflow design; they are separate from the daily maker-checker review below.")
        aligned_dataframe(pd.DataFrame(output["acceptance_tests"]), hide_index=True, width="stretch")
        st.markdown("**Daily-run maker-checker evidence**")
        aligned_dataframe(pd.DataFrame([output["preparer"], output["checker"]]), hide_index=True, width="stretch")
        aligned_dataframe(
            pd.DataFrame(
                [{"Independence check": check, "Result": "Passed" if passed else "Failed"} for check, passed in output["independence_checks"].items()]
            ),
            hide_index=True,
            width="stretch",
        )
        st.code(output["control_package_fingerprint"])
        st.caption("Fingerprint scope: " + output["fingerprint_scope"] + ".")
        (st.success if output["delivery_ready"] else st.error)(output["decision"])

    else:
        a, b = st.columns(2)
        with a:
            result_metric("Client submission", output["client_submission"], border=True)
        with b:
            result_metric("Fund-price diffusion", output["market_diffusion"], border=True)
        aligned_dataframe(pd.DataFrame(output["distribution_channels"]), hide_index=True, width="stretch")
        st.markdown(f"**Client Account Manager:** {output['cam_role']}", text_alignment="justify")
        st.markdown("**Final acceptance-criteria status**")
        aligned_dataframe(pd.DataFrame(output["acceptance_results"]), hide_index=True, width="stretch")
        if output["delivery_ready"]:
            st.success("The end-to-end learning journey is complete. No external system, client or price service was contacted.")
        else:
            st.error("The delivery guard blocked the simulated submission because prior control evidence did not pass.")


def _reset() -> None:
    st.session_state.guided_pipeline_completed = 0
    st.session_state.guided_pipeline_records = []
    log_event(
        "Guided journey restarted",
        "Reset",
        "Portfolio visitor",
        "The prepared learning case returned to stage one.",
        scope="Guided learning journey",
    )


def _normalise_guided_state() -> None:
    if st.session_state.get("guided_pipeline_version") != STATE_VERSION:
        st.session_state.guided_pipeline_version = STATE_VERSION
        st.session_state.guided_pipeline_records = []
    records = st.session_state.get("guided_pipeline_records", [])
    if not isinstance(records, list):
        records = []
    valid_records = []
    for expected_step, record in enumerate(records[: len(STEPS)], start=1):
        if not isinstance(record, dict) or record.get("step") != expected_step or "output" not in record:
            break
        valid_records.append(record)
    st.session_state.guided_pipeline_records = valid_records
    st.session_state.guided_pipeline_completed = len(valid_records)


_normalise_guided_state()
completed = st.session_state.guided_pipeline_completed
records = st.session_state.guided_pipeline_records

st.caption("GUIDED LEARNING / FINANCE OPERATIONS → DATA → CONTROL → DELIVERY")
st.title("One connected journey, one click at a time", icon=":material/route:")
st.markdown(
    "Follow one prepared fictional case from the business question to a reviewed and simulated delivery result. "
    "Every click consumes the evidence created by the previous stages. You do not need to select a fund, move a "
    "slider or enter a financial figure.",
    text_alignment="justify",
)
st.caption("Professional methods and mission themes come from the supplied documents. All case names, figures, calculations and approvals are educational examples.")

st.progress(completed / len(STEPS), text=f"{completed} of {len(STEPS)} stages complete")
if completed:
    st.caption(
        f"Latest completed stage: {completed:02d} · {STEPS[completed - 1]['title']}. "
        "Earlier evidence remains available in the completed-stage panels below."
    )
else:
    st.caption("Start with the business need. Each later stage unlocks only after the previous result is available.")

for index, record in enumerate(records):
    with st.expander(
        f"{index + 1:02d} · {STEPS[index]['title']} · Complete",
        expanded=index == completed - 1,
        icon=":material/check_circle:",
    ):
        step = STEPS[index]
        st.markdown(f"**What happens:** {step['what']}", text_alignment="justify")
        st.markdown(f"**Why it matters:** {step['why']}", text_alignment="justify")
        st.markdown(f"**How it runs:** {step['how']}", text_alignment="justify")
        st.markdown("**Rule or formula**")
        st.code(step["formula"], language=None)
        st.markdown("**Automated result**")
        _render_output(index, record)
        st.caption(f"Completed in this browser session at {record['completed_at_utc']} · educational synthetic case")

if completed < len(STEPS):
    next_step = STEPS[completed]
    with st.container(border=True):
        st.caption(f"NEXT AUTOMATED STAGE · {completed + 1:02d} OF {len(STEPS):02d}")
        st.subheader(next_step["title"])
        st.markdown(next_step["what"], text_alignment="justify")
        if st.button(
            f"Run next stage · {completed + 1:02d}",
            type="primary",
            icon=":material/play_arrow:",
            width="stretch",
        ):
            record = _execute_step(completed, list(records))
            updated_records = [*records, record]
            st.session_state.guided_pipeline_records = updated_records
            st.session_state.guided_pipeline_completed = len(updated_records)
            log_event(
                "Guided stage completed",
                "Completed",
                "Portfolio visitor",
                f"Stage {completed + 1}: {next_step['title']}.",
                scope="Guided learning journey",
            )
            st.rerun()
else:
    st.success("End-to-end journey complete: the prepared case moved from business need to guarded simulated delivery with its calculations and controls visible.")
    export = {
        "scope": "Educational synthetic guided journey; no live processing or authenticated approval",
        "case": records[0]["output"]["context"],
        "completed_stages": completed,
        "records": records,
    }
    st.download_button(
        "Download the completed learning record",
        json.dumps(export, indent=2, default=str),
        "guided-finance-transformation-journey.json",
        "application/json",
        icon=":material/download:",
        width="stretch",
    )
    st.page_link("app_pages/projects.py", label="Connect the journey to the eight documented missions", icon=":material/target:")

if completed and st.button("Restart the guided journey", icon=":material/restart_alt:"):
    _reset()
    st.rerun()

with st.expander("Optional detailed demonstrations"):
    st.markdown(
        "The guided journey is the recommended route. Open a detailed workbench only when you want to inspect "
        "more controls after understanding the complete flow.",
        text_alignment="justify",
    )
    left, middle, right = st.columns(3)
    left.page_link("app_pages/nav_production.py", label="Net Asset Value calculation detail", icon=":material/calculate:")
    middle.page_link("app_pages/data_reporting.py", label="Reporting detail", icon=":material/database:")
    right.page_link("app_pages/ai_controls.py", label="Automation detail", icon=":material/memory:")
