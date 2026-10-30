"""Regression tests for the finance domain and Streamlit workflows.

Run from this directory with::

    python -m unittest -v test_workflows.py
"""

from __future__ import annotations

import os
import re
import sys
import unittest
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from data import FUNDS, GLOSSARY, SYNTHETIC_POSITIONS_BY_FUND, synthetic_trades_for_fund  # noqa: E402
from domain import (  # noqa: E402
    anomaly_assessment,
    cash_forecast,
    chunk_plan,
    daily_fee_accrual,
    journal_entry,
    operating_model_route,
    parse_confirmation,
    performance_fee,
    valuation_fingerprint,
)
from streamlit.testing.v1 import AppTest  # noqa: E402
from state import seed_positions  # noqa: E402
from valuation import Valuation  # noqa: E402


class ValuationTests(unittest.TestCase):
    def test_default_net_asset_value_and_price(self):
        result = Valuation().calculate()
        self.assertAlmostEqual(result["nav"], 474_993_493.0)
        self.assertAlmostEqual(result["price"], 118.74837325)
        self.assertEqual(result["distribution_price"], result["price"])
        self.assertEqual(result["direction"], "None")

    def test_swing_direction_and_disable(self):
        for flow, direction, sign in [
            (20_000_000.0, "Upward", 1),
            (-20_000_000.0, "Downward", -1),
        ]:
            with self.subTest(flow=flow):
                valuation = Valuation(flow=flow)
                result = valuation.calculate()
                self.assertTrue(result["triggered"])
                self.assertEqual(result["direction"], direction)
                self.assertAlmostEqual(
                    result["distribution_price"],
                    result["price"] * (1 + sign * 0.002),
                )
                self.assertEqual(
                    replace(valuation, swing=False).calculate()["distribution_price"],
                    result["price"],
                )

    def test_swing_threshold_boundary(self):
        net_assets = Valuation().calculate()["nav"]
        self.assertTrue(Valuation(flow=net_assets * 0.02).calculate()["triggered"])
        self.assertFalse(Valuation(flow=net_assets * 0.02 - 1).calculate()["triggered"])

    def test_invalid_valuation_inputs(self):
        invalid_changes = [
            {"units": 0},
            {"portfolio": -1},
            {"payables": 1_000_000_000},
            {"cash": float("nan")},
            {"threshold": 0},
        ]
        for changes in invalid_changes:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(Valuation(), **changes).calculate()


class DomainCalculationTests(unittest.TestCase):
    def test_cash_forecast_statuses_and_policy_buffer(self):
        sufficient = cash_forecast(100, 20, 10, 30, 5, 0, 10)
        self.assertEqual(sufficient["projected_cash"], 85)
        self.assertEqual(sufficient["required_buffer"], 10)
        self.assertEqual(sufficient["buffer_headroom"], 75)
        self.assertEqual(sufficient["status"], "Sufficient")

        below_buffer = cash_forecast(100, 0, 85, 0, 0, 0, 20)
        self.assertEqual(below_buffer["status"], "Below policy buffer")
        overdraft = cash_forecast(100, 0, 101, 0, 0, 0, 0)
        self.assertEqual(overdraft["status"], "Projected overdraft")
        with self.assertRaises(ValueError):
            cash_forecast(100, 0, 0, 0, 0, 0, 101)

    def test_fee_calculations(self):
        self.assertAlmostEqual(daily_fee_accrual(365_000, 100), 10.0)
        result = performance_fee(120, 100, 5, 20, 1_000)
        self.assertEqual(result["hurdle_level"], 105)
        self.assertEqual(result["eligible_gain_per_unit"], 15)
        self.assertEqual(result["fee"], 3_000)
        self.assertEqual(performance_fee(104, 100, 5, 20, 1_000)["fee"], 0)

    def test_journal_entry_is_balanced(self):
        lines = journal_entry("Accrue the management fee", 12_500, "JRNL-001")
        self.assertEqual(len(lines), 2)
        self.assertEqual(sum(line["Debit (EUR)"] for line in lines), 12_500)
        self.assertEqual(sum(line["Credit (EUR)"] for line in lines), 12_500)
        self.assertTrue(all(line["Reference"] == "JRNL-001" for line in lines))
        with self.assertRaises(ValueError):
            journal_entry("Accrue the management fee", 0, "JRNL-002")

    def test_anomaly_routes_data_quality_before_business_scoring(self):
        quarantine = anomaly_assessment(False, True, 12, 2, True)
        self.assertEqual(quarantine["route"], "Data-quality quarantine")
        self.assertIsNone(quarantine["score"])

        urgent = anomaly_assessment(True, True, 12, 2, True)
        self.assertEqual(urgent["route"], "Business anomaly assessment")
        self.assertEqual(urgent["score"], 1.0)
        self.assertEqual(urgent["band"], "Urgent analyst review")

    def test_chunk_plan_preserves_all_rows_and_order(self):
        plan = chunk_plan(450, 200)
        self.assertEqual([row["Chunk"] for row in plan], ["part_001", "part_002", "part_003"])
        self.assertEqual(plan[0]["First source row"], 1)
        self.assertEqual(plan[-1]["Last source row"], 450)
        self.assertEqual(plan[-1]["Data rows"], 50)
        self.assertEqual(sum(row["Data rows"] for row in plan), 450)

    def test_operating_model_routing_and_fingerprint(self):
        local = operating_model_route(True, True, True)
        self.assertEqual(local["model"], "Jurisdiction-specific local model")
        global_model = operating_model_route(True, False, True)
        self.assertEqual(global_model["model"], "Global standardized model")
        transition = operating_model_route(False, False, True)
        self.assertEqual(transition["model"], "Transition assessment required")

        context = {"fund": "Aurora Equity Fund", "date": "2026-09-17"}
        inputs = {"portfolio": 100.0}
        results = {"net_asset_value": 100.0}
        first = valuation_fingerprint(context, inputs, results)
        second = valuation_fingerprint(context, inputs, results)
        changed = valuation_fingerprint(context, {"portfolio": 101.0}, results)
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)
        self.assertEqual(len(first), 64)

    def test_confirmation_parser_validates_product_rules(self):
        future = parse_confirmation(
            "REFERENCE=FUT-01;TRADE_DATE=2026-09-17;SETTLEMENT_DATE=2026-09-18;"
            "INSTRUMENT=EURO STOXX 50;CONTRACTS=2;CONTRACT_SIZE=10;PRICE=5000;"
            "CURRENCY=EUR;DIRECTION=BUY",
            "Exchange-Traded Derivative future",
        )
        self.assertEqual(future["route"], "Eligible for human approval")
        self.assertEqual(future["mapped"]["underlying_units"], 20)
        self.assertEqual(future["mapped"]["notional"], 100_000)

        invalid_swap = parse_confirmation(
            "REFERENCE=FX-01;TRADE_DATE=2026-09-17;NEAR_DIRECTION=BUY;"
            "NEAR_CURRENCY=EUR;NEAR_AMOUNT=1000000;NEAR_RATE=1.10;NEAR_DATE=2026-09-20;"
            "FAR_DIRECTION=BUY;FAR_CURRENCY=EUR;FAR_AMOUNT=900000;FAR_RATE=1.11;"
            "FAR_DATE=2026-09-19",
            "Foreign-exchange swap",
        )
        self.assertEqual(invalid_swap["route"], "Human exception review")
        self.assertGreaterEqual(len(invalid_swap["errors"]), 3)

    def test_cam_has_one_controlled_meaning(self):
        cam_entries = [entry for entry in GLOSSARY if entry[1] == "CAM"]
        self.assertEqual(len(cam_entries), 1)
        self.assertEqual(cam_entries[0][0], "Client Account Manager")

    def test_each_fund_trade_ledger_matches_its_holdings_and_cash_ladder(self):
        all_ids = []
        for fund in FUNDS:
            name = fund["Fund"]
            with self.subTest(fund=name):
                positions = {row["Instrument"] for row in SYNTHETIC_POSITIONS_BY_FUND[name]}
                trades = synthetic_trades_for_fund(name)
                self.assertTrue(all(row["Security"] in positions for row in trades))
                self.assertEqual(sum(row["Gross amount (EUR)"] for row in trades if row["Side"] == "Buy"), 1_326_300)
                self.assertEqual(sum(row["Gross amount (EUR)"] for row in trades if row["Side"] == "Sell"), 1_228_000)
                all_ids.extend(row["Trade ID"] for row in trades)
        self.assertEqual(len(all_ids), len(set(all_ids)))


class FundPositionSeedTests(unittest.TestCase):
    def test_each_fund_has_distinct_positions_with_the_same_default_value(self):
        valuation_date = date(2026, 9, 21)
        self.assertEqual(set(SYNTHETIC_POSITIONS_BY_FUND), {fund["Fund"] for fund in FUNDS})
        signatures = set()
        for fund in FUNDS:
            with self.subTest(fund=fund["Fund"]):
                positions = seed_positions(fund["Fund"], valuation_date)
                signatures.add(tuple(row["Instrument"] for row in positions))
                value = sum(
                    row["Quantity"] * row["Local price"] * row["FX rate to EUR"]
                    for row in positions
                )
                self.assertAlmostEqual(value, Valuation().portfolio)
                self.assertTrue(all(row["Price timestamp"].startswith(valuation_date.isoformat()) for row in positions))
                self.assertTrue(all(row["Price status"] == "Current" for row in positions))
                self.assertTrue(all("derivative" not in row["Instrument type"].lower() for row in positions))
        self.assertEqual(len(signatures), len(FUNDS))

    def test_seeding_returns_independent_copies_and_rejects_unknown_fund(self):
        valuation_date = date(2026, 9, 21)
        first = seed_positions(FUNDS[0]["Fund"], valuation_date)
        first[0]["Quantity"] = 0
        second = seed_positions(FUNDS[0]["Fund"], valuation_date)
        self.assertEqual(second[0]["Quantity"], 1_500_000.0)
        self.assertEqual(second[0]["Position ID"], "POS-001")
        with self.assertRaises(ValueError):
            seed_positions("Unknown synthetic fund", valuation_date)


class AcknowledgementGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_working_directory = Path.cwd()
        os.chdir(APP_DIR)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.original_working_directory)

    def test_first_visit_requires_an_explicit_scope_acknowledgement(self):
        app = AppTest.from_file(APP_DIR / "app.py", default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertTrue(any(title.value == "Before you explore" for title in app.title))
        enter_button = next(button for button in app.button if button.label == "Enter portfolio")
        self.assertTrue(enter_button.disabled)
        confirmation = next(
            checkbox
            for checkbox in app.checkbox
            if checkbox.label
            == "Educational scope understood; only non-confidential example data will be used."
        )
        confirmation.check()
        app.run()
        next(button for button in app.button if button.label == "Enter portfolio").click()
        app.run()
        self.assertFalse(app.exception)
        self.assertIn("portfolio_acknowledgement", app.session_state)
        self.assertTrue(any("From business understanding" in title.value for title in app.title))


class StreamlitWorkflowTests(unittest.TestCase):
    PAGE_NAMES = [
        "home",
        "concepts",
        "explore",
        "guided_pipeline",
        "operating_model",
        "fund_accounting",
        "nav_production",
        "reconciliation",
        "data_reporting",
        "ai_controls",
        "governance",
        "projects",
        "glossary",
    ]

    CHECKLIST_LABELS = [
        "All expected positions, trades, cash and corporate-action sources were received",
        "Price and foreign-exchange sources and timestamps were reviewed",
        "Income, tax, fees, payables and other accruals were reviewed",
        "Share-class units and investor dealing were validated",
        "All run-linked exceptions have a documented resolved or tolerated disposition",
    ]

    @classmethod
    def setUpClass(cls):
        cls.original_working_directory = Path.cwd()
        os.chdir(APP_DIR)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.original_working_directory)

    def setUp(self):
        self.app = AppTest.from_file(APP_DIR / "app.py", default_timeout=30).run()
        self.assert_no_app_exception()
        self.widget(
            "checkbox",
            "Educational scope understood; only non-confidential example data will be used.",
        ).check()
        self.app.run()
        self.assert_no_app_exception()
        self.widget("button", "Enter portfolio").click()
        self.app.run()
        self.assert_no_app_exception()

    def assert_no_app_exception(self):
        self.assertFalse(self.app.exception, msg=f"Unexpected Streamlit exception: {self.app.exception}")

    def page(self, name: str):
        self.app.switch_page(f"app_pages/{name}.py").run()
        self.assert_no_app_exception()
        return self.app

    def widget(self, collection: str, label: str):
        widgets = getattr(self.app, collection)
        try:
            return next(widget for widget in widgets if widget.label == label)
        except StopIteration as exc:
            available = [getattr(widget, "label", "<unlabelled>") for widget in widgets]
            raise AssertionError(
                f"No {collection} labelled {label!r}; available labels: {available}"
            ) from exc

    def click(self, label: str):
        self.widget("button", label).click()
        self.app.run()
        self.assert_no_app_exception()
        return self.app

    def calculate_baseline(self):
        self.page("nav_production")
        self.click("Calculate draft Net Asset Value")
        self.assertEqual(self.app.session_state["run_stage"], "Calculated")
        self.assertIsNotNone(self.app.session_state["valuation_result"])
        return self.app

    def resolve_current_exception(self):
        self.page("reconciliation")
        self.widget("text_area", "Confirmed root cause").set_value(
            "The custodian confirmation used the adjacent settlement date."
        )
        self.widget("text_area", "Corrective or follow-up action").set_value(
            "The analyst verified the corrected confirmation against the trade record."
        )
        self.widget("text_input", "Evidence reference").set_value("CASE-10421")
        self.widget("button", "Record disposition").click()
        self.app.run()
        self.assert_no_app_exception()
        current_break = next(
            row for row in self.app.session_state["breaks"] if row["Break ID"] == "BRK-10421"
        )
        self.assertEqual(current_break["Workflow status"], "Resolved")

    def test_every_registered_page_renders(self):
        for name in self.PAGE_NAMES:
            with self.subTest(page=name):
                self.page(name)

    def test_enterprise_exception_can_open_editable_run(self):
        self.page("reconciliation")
        self.widget("segmented_control", "Register scope").set_value("Enterprise demonstration register")
        self.app.run()
        self.assertTrue(self.widget("button", "Record disposition").disabled)
        self.click("Open selected exception in its valuation run")
        self.assertEqual(self.widget("segmented_control", "Register scope").value, "Current valuation run")
        self.assertFalse(self.widget("button", "Record disposition").disabled)
        self.resolve_current_exception()
        self.assertTrue(any("Disposition saved" in message.value for message in self.app.success))

    def test_all_four_exception_cases_remain_visible_and_date_conflict_is_explicit(self):
        self.page("reconciliation")
        self.assertEqual(len(self.app.session_state["breaks"]), 4)
        overview = self.app.table[0].value
        self.assertEqual(set(overview["Break ID"]), {"BRK-10421", "BRK-10422", "BRK-10423", "BRK-10424"})
        for actual, expected in zip(overview["Monetary difference (EUR)"], [0, 1400, 3200000, 0.45]):
            self.assertAlmostEqual(actual, expected)
        self.assertTrue(any("custodian confirmation is one day later" in message.value for message in self.app.error))
        self.click("Inspect all fund exceptions")
        self.widget("selectbox", "Exception identifier").select("BRK-10422")
        self.app.run()
        self.assert_no_app_exception()
        self.assertTrue(self.widget("button", "Record disposition").disabled)
        self.click("Open selected exception in its valuation run")
        self.assertEqual(self.app.session_state["context"]["fund"], "Meridian Bond Fund")
        self.assertFalse(self.widget("button", "Record disposition").disabled)

    def test_accounting_correction_cannot_be_posted_twice(self):
        self.page("reconciliation")
        self.widget("selectbox", "Proposed disposition").select("Post accounting correction and require recalculation")
        self.app.run()
        before = self.app.session_state["valuation"]["portfolio"]
        self.resolve_current_exception()
        self.assertEqual(self.app.session_state["valuation"]["portfolio"], before + 1_000)
        self.click("Record disposition")
        self.assertEqual(self.app.session_state["valuation"]["portfolio"], before + 1_000)
        self.assertTrue(any("cannot be posted twice" in message.value for message in self.app.error))

    def test_guided_pipeline_builds_the_case_one_automatic_stage_at_a_time(self):
        self.page("guided_pipeline")
        self.assertEqual(self.app.session_state["guided_pipeline_completed"], 0)
        self.assertFalse(self.app.main.number_input)
        self.assertFalse(self.app.main.slider)
        self.assertFalse(self.app.main.selectbox)
        self.assertFalse(self.app.multiselect)
        self.assertFalse(self.app.file_uploader)
        self.assertFalse(self.app.text_input)
        self.assertFalse(self.app.date_input)

        for step in range(1, 11):
            self.click(f"Run next stage · {step:02d}")
            self.assertEqual(self.app.session_state["guided_pipeline_completed"], step)
            self.assertEqual(len(self.app.session_state["guided_pipeline_records"]), step)

        records = self.app.session_state["guided_pipeline_records"]
        self.assertTrue(records[1]["output"]["source_control_passed"])
        self.assertEqual(len(records[1]["output"]["source_inventory"]), 10)
        self.assertEqual(records[1]["output"]["received_rows"], records[1]["output"]["preserved_rows"])
        self.assertTrue(records[2]["output"]["control_passed"])
        self.assertEqual(records[3]["output"]["difference_eur"], 0.0)
        self.assertTrue(records[4]["output"]["cash_control_passed"])
        self.assertEqual(records[4]["output"]["minimum_buffer_base"], "Opening ledger cash")
        self.assertEqual(records[5]["output"]["anomaly"]["score"], 0.3)
        self.assertTrue(records[5]["output"]["settlement_date_conflict"])
        self.assertEqual(records[5]["output"]["authority_source"], "Executed trade confirmation")
        self.assertEqual(records[5]["output"]["conflicting_sources"], ["Custodian"])
        resolved_event = next(
            row for row in records[5]["output"]["updated_events"] if row["Event ID"] == "REC-003"
        )
        self.assertEqual(resolved_event["Reconciliation status"], "Matched")
        self.assertAlmostEqual(records[6]["output"]["nav"], 474_993_493.0)
        self.assertFalse(records[6]["output"]["swing_triggered"])
        self.assertEqual(records[7]["output"]["matched_events"], 5)
        self.assertEqual(records[7]["output"]["outstanding_events"], 1)
        self.assertEqual(records[7]["output"]["outstanding_exposure_eur"], 210_000.0)
        self.assertTrue(records[7]["output"]["source_to_visual_control_passed"])
        self.assertTrue(records[7]["output"]["materiality_control_passed"])
        self.assertLessEqual(
            records[7]["output"]["residual_assessments"][0]["Exposure to NAV (bps)"],
            records[7]["output"]["residual_assessments"][0]["Illustrative threshold (bps)"],
        )
        self.assertTrue(all(row["Result"] == "Passed" for row in records[8]["output"]["quality_gates"]))
        self.assertEqual(records[8]["output"]["uat_tests_passed"], 4)
        self.assertEqual(len(records[8]["output"]["control_package_fingerprint"]), 64)
        self.assertNotEqual(records[8]["output"]["preparer"]["Actor ID"], records[8]["output"]["checker"]["Actor ID"])
        self.assertTrue(all(records[8]["output"]["independence_checks"].values()))
        self.assertEqual(records[8]["output"]["decision"], "Ready for simulated delivery")
        self.assertTrue(records[9]["output"]["delivery_ready"])
        self.assertTrue(records[9]["output"]["delivery_control_passed"])
        self.assertTrue(all(row["Timeliness"] == "On time" for row in records[9]["output"]["distribution_channels"]))
        self.assertTrue(all(row["Acknowledgement"].startswith("ACK-") for row in records[9]["output"]["distribution_channels"]))
        self.assertEqual(
            records[9]["output"]["evidence_package"],
            records[8]["output"]["control_package_fingerprint"],
        )
        self.assertTrue(all(row["Status"] == "Met" for row in records[9]["output"]["acceptance_results"]))
        self.assertEqual(records[9]["output"]["documented_projects_connected"], 8)

    def test_guided_delivery_guard_blocks_failed_prior_evidence(self):
        self.page("guided_pipeline")
        for step in range(1, 9):
            self.click(f"Run next stage · {step:02d}")

        records = list(self.app.session_state["guided_pipeline_records"])
        records[3]["output"]["control_passed"] = False
        self.app.session_state["guided_pipeline_records"] = records

        self.click("Run next stage · 09")
        review = self.app.session_state["guided_pipeline_records"][8]["output"]
        self.assertFalse(review["delivery_ready"])
        self.assertEqual(review["decision"], "Delivery blocked by failed control evidence")
        self.assertTrue(any(row["Result"] == "Failed" for row in review["quality_gates"]))

        self.click("Run next stage · 10")
        delivery = self.app.session_state["guided_pipeline_records"][9]["output"]
        self.assertFalse(delivery["delivery_ready"])
        self.assertEqual(delivery["client_submission"], "Not submitted")
        self.assertTrue(all(row["Status"] == "Blocked by control decision" for row in delivery["distribution_channels"]))

    def test_scenario_drives_swing_and_liquidity_results(self):
        self.page("nav_production")
        self.widget("selectbox", "Valuation scenario").select("Large redemption and cash stress")
        self.click("Apply scenario inputs")
        self.assertEqual(self.app.session_state["run_stage"], "Draft")
        self.assertIsNone(self.app.session_state["valuation_result"])

        self.click("Calculate draft Net Asset Value")
        result = self.app.session_state["valuation_result"]
        self.assertTrue(result["triggered"])
        self.assertEqual(result["direction"], "Downward")
        self.assertLess(result["distribution_price"], result["price"])
        self.assertEqual(result["cash_forecast"]["status"], "Projected overdraft")

    def test_stale_price_scenario_blocks_review_at_position_source(self):
        self.page("nav_production")
        self.widget("selectbox", "Valuation scenario").select("Stale-price control failure")
        self.click("Apply scenario inputs")
        self.assertEqual(self.app.session_state["valuation_positions"][0]["Price status"], "Stale")
        self.click("Calculate draft Net Asset Value")
        self.assertTrue(self.app.session_state["quality_inputs"]["stale_price"])
        self.assertTrue(any("current prices" in error.value.lower() for error in self.app.error))

    def test_manual_investment_balance_requires_position_rollup_agreement(self):
        self.page("nav_production")
        self.widget("number_input", "Investments at current valuation (EUR)").set_value(476_000_000.0)
        self.click("Calculate draft Net Asset Value")
        self.assertEqual(self.app.session_state["run_stage"], "Calculated")
        self.assertTrue(any("position-level valuation roll-up" in error.value for error in self.app.error))

    def test_valuation_date_change_starts_a_new_run_and_redates_price_sources(self):
        self.calculate_baseline()
        old_run_id = self.app.session_state["run_id"]
        new_date = self.app.session_state["context"]["valuation_date"] + timedelta(days=1)
        self.widget("date_input", "Valuation date").set_value(new_date)
        self.app.run()
        self.assert_no_app_exception()
        self.assertNotEqual(self.app.session_state["run_id"], old_run_id)
        self.assertEqual(self.app.session_state["run_stage"], "Draft")
        self.assertTrue(
            all(row["Price timestamp"].startswith(new_date.isoformat())
                for row in self.app.session_state["valuation_positions"])
        )

    def test_fund_change_and_scenario_reseed_matching_holdings(self):
        self.page("nav_production")
        original_instruments = [row["Instrument"] for row in self.app.session_state["valuation_positions"]]
        self.widget("selectbox", "Synthetic fund").select("Meridian Bond Fund")
        self.app.run()
        self.assert_no_app_exception()
        self.assertEqual(self.app.session_state["context"]["fund"], "Meridian Bond Fund")
        bond_positions = self.app.session_state["valuation_positions"]
        self.assertNotEqual([row["Instrument"] for row in bond_positions], original_instruments)
        self.assertTrue(all("bond" in row["Instrument type"].lower() for row in bond_positions))
        self.assertTrue(all(row["Price timestamp"].startswith(self.app.session_state["context"]["valuation_date"].isoformat())
                            for row in bond_positions))

        self.click("Apply scenario inputs")
        self.assertEqual([row["Instrument"] for row in self.app.session_state["valuation_positions"]],
                         [row["Instrument"] for row in bond_positions])

    def test_invalid_calculation_preserves_last_valid_snapshot(self):
        self.calculate_baseline()
        previous_inputs = dict(self.app.session_state["valuation"])
        previous_result = dict(self.app.session_state["valuation_result"])
        previous_version = self.app.session_state["run_version"]

        self.widget("number_input", "Trade and other payables (EUR)").set_value(1_000_000_000.0)
        self.widget("button", "Calculate draft Net Asset Value").click()
        self.app.run()
        self.assert_no_app_exception()
        self.assertTrue(self.app.error)
        self.assertEqual(self.app.session_state["valuation"], previous_inputs)
        self.assertEqual(self.app.session_state["valuation_result"], previous_result)
        self.assertEqual(self.app.session_state["run_version"], previous_version)

    def test_full_lifecycle_and_recalculation_invalidation(self):
        self.calculate_baseline()
        self.resolve_current_exception()

        self.page("nav_production")
        self.click("Confirm reconciliation and source readiness")
        self.assertEqual(self.app.session_state["run_stage"], "Reconciliation cleared")

        self.page("governance")
        for label in self.CHECKLIST_LABELS:
            self.widget("checkbox", label).check()
        self.widget("button", "Save preparer checklist").click()
        self.app.run()
        self.assert_no_app_exception()
        self.assertTrue(all(self.app.session_state["review_checklist"].values()))

        self.click("Mark preparer review complete")
        self.assertEqual(self.app.session_state["run_stage"], "Preparer reviewed")
        self.assertIsNotNone(self.app.session_state["preparer"])

        self.widget(
            "checkbox",
            "Confirm checker review of the current calculation, checklist and exception dispositions represented by the control-package fingerprint.",
        ).check()
        self.app.run()
        self.assert_no_app_exception()
        self.assertFalse(self.widget("button", "Simulate independent checker approval").disabled)
        self.click("Simulate independent checker approval")
        self.assertEqual(self.app.session_state["run_stage"], "Checker approved")
        self.assertNotEqual(
            self.app.session_state["preparer"]["Actor"],
            self.app.session_state["checker"]["Actor"],
        )

        self.click("Simulate price publication")
        self.assertEqual(self.app.session_state["run_stage"], "Publication simulated")
        self.assertTrue(
            all(
                channel["Status"] == "Acknowledged"
                for channel in self.app.session_state["distribution_channels"]
            )
        )

        approved_version = self.app.session_state["run_version"]
        self.page("nav_production")
        self.widget("number_input", "Investments at current valuation (EUR)").set_value(476_000_000.0)
        self.widget("button", "Calculate draft Net Asset Value").click()
        self.app.run()
        self.assert_no_app_exception()
        self.assertEqual(self.app.session_state["run_stage"], "Calculated")
        self.assertEqual(self.app.session_state["run_version"], approved_version + 1)
        self.assertIsNone(self.app.session_state["preparer"])
        self.assertIsNone(self.app.session_state["checker"])
        self.assertTrue(
            all(
                channel["Status"] == "Queued"
                for channel in self.app.session_state["distribution_channels"]
            )
        )

    def test_project_search_and_glossary_are_resilient(self):
        self.page("projects")
        self.widget("text_input", "Search missions, tools, controls or outcomes").set_value(
            "no-such-workstream"
        )
        self.app.run()
        self.assert_no_app_exception()
        self.assertTrue(self.app.info)

        self.page("glossary")
        self.widget("text_input", "Search terms, abbreviations or definitions").set_value("CAM")
        self.app.run()
        self.assert_no_app_exception()
        self.assertTrue(
            any("CAM means Client Account Manager" in element.value for element in self.app.info)
        )

    def test_contents_index_exposes_all_pages_without_disclosure_panels(self):
        self.page("contents")
        expected_labels = {
            "Overview", "Contents & navigation", "How the work fits together", "Missions",
            "Interactive lab", "Guided case", "Business and operating model", "Fund accounting",
            "Net Asset Value control room", "Reconciliation workbench", "Data and Business Intelligence",
            "Controlled Artificial Intelligence", "Delivery and governance", "Glossary and methodology",
        }
        labels = {re.sub(r"^\d+\.\d+\s+", "", link.proto.label) for link in self.app.get("page_link")}
        self.assertTrue(expected_labels <= labels, expected_labels - labels)
        headings = [heading.value for heading in self.app.subheader]
        self.assertLess(headings.index("Content index"), headings.index("Connected navigation diagram"))
        self.assertFalse(self.app.expander)
        self.assertFalse(self.app.tabs)
        sidebar_labels = [link.proto.label for link in self.app.sidebar.get("page_link")]
        self.assertEqual(sidebar_labels[:2], ["Overview", "Contents & navigation"])
        self.page("home")
        self.assertTrue(any(
            "Contents & navigation" in link.proto.label
            for link in self.app.main.get("page_link")
        ))

    def test_display_preferences_persist_without_changing_valuation_run(self):
        run_id = self.app.session_state["run_id"]
        self.widget("slider", "Text size").set_value(15)
        self.widget("segmented_control", "Content width").set_value("Reading width")
        self.app.run()
        self.assert_no_app_exception()
        self.page("contents")
        self.assertEqual(self.widget("slider", "Text size").value, 15)
        self.assertEqual(self.widget("number_input", "Text size (pixels)").value, 15)
        self.assertEqual(self.widget("segmented_control", "Content width").value, "Reading width")
        self.assertEqual(self.app.session_state["run_id"], run_id)
        self.widget("number_input", "Text size (pixels)").set_value(27)
        self.app.run()
        self.assert_no_app_exception()
        self.page("data_reporting")
        self.assertEqual(self.widget("slider", "Text size").value, 27)
        self.click("Reset display size")
        self.assertEqual(self.widget("number_input", "Text size (pixels)").value, 18)
        self.assertEqual(self.widget("slider", "Text size").value, 18)
        self.assertEqual(self.widget("segmented_control", "Content width").value, "Full width")


if __name__ == "__main__":
    unittest.main(verbosity=2)
