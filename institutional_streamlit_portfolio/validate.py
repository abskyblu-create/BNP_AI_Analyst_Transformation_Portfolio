"""Fast structural and domain validation for the professional Streamlit portfolio.

Run this file from the application directory before starting Streamlit. It
checks source structure and pure domain behavior. Interaction-level checks
remain in test_workflows.py.
"""

from __future__ import annotations

import ast
from datetime import date, datetime
from pathlib import Path
import re

from data import (
    CAPABILITY_PILLARS,
    DELIVERY_STAGES,
    FUNDS,
    GLOSSARY,
    NAV_FOUNDATION_STEPS,
    PROFESSIONAL_PROFILE,
    PROJECTS,
    RECONCILIATION_EVENTS,
    SYNTHETIC_BREAKS,
    SYNTHETIC_POSITIONS,
    SYNTHETIC_POSITIONS_BY_FUND,
    TRADE_SECURITIES_BY_FUND,
    synthetic_trades_for_fund,
)
from domain import (
    anomaly_assessment,
    cash_forecast,
    chunk_plan,
    journal_entry,
    operating_model_route,
    parse_confirmation,
    performance_fee,
)
from valuation import Valuation


ROOT = Path(__file__).resolve().parent

EXPECTED_PAGES = {
    "app_pages/contents.py",
    "app_pages/home.py",
    "app_pages/concepts.py",
    "app_pages/explore.py",
    "app_pages/guided_pipeline.py",
    "app_pages/operating_model.py",
    "app_pages/fund_accounting.py",
    "app_pages/nav_production.py",
    "app_pages/reconciliation.py",
    "app_pages/data_reporting.py",
    "app_pages/ai_controls.py",
    "app_pages/governance.py",
    "app_pages/projects.py",
    "app_pages/glossary.py",
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_source_structure() -> None:
    """Check syntax, registered pages, launcher wiring and scope disclosure."""
    python_files = sorted(ROOT.rglob("*.py"))
    check(bool(python_files), "No Python source files were found.")
    for source in python_files:
        # Some archived, unused views carry a UTF-8 byte-order mark. The
        # active application and those files should still pass syntax checks.
        ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(source))

    app_source = (ROOT / "app.py").read_text(encoding="utf-8-sig")
    registered = set(re.findall(r'st\.Page\("([^\"]+\.py)"', app_source))
    check(EXPECTED_PAGES <= registered, f"Required portfolio pages are not all registered: {sorted(EXPECTED_PAGES - registered)}")
    missing = [page for page in EXPECTED_PAGES if not (ROOT / page).is_file()]
    check(not missing, f"Registered page files are missing: {missing}")
    check("begin_new_run" in app_source, "The shared fund/date context is not connected to new-run state.")
    check("PROFESSIONAL_PROFILE" in app_source, "Portfolio identity is not connected to the application shell.")
    check("if run_workspace:" in app_source, "The valuation context must appear only in relevant workspaces.")
    check("portfolio_acknowledgement" in app_source, "The first-visit scope acknowledgement is missing.")
    check("disabled=not accepted" in app_source, "Portfolio entry must require an explicit acknowledgement.")

    guided_source = (ROOT / "app_pages/guided_pipeline.py").read_text(encoding="utf-8-sig")
    check("Run next stage" in guided_source, "The guided journey needs an explicit sequential action.")
    check("guided_pipeline_completed" in guided_source, "The guided journey does not preserve stage progress.")
    forbidden_guided_inputs = ("st.number_input", "st.slider", "st.selectbox", "st.multiselect", "st.file_uploader", "st.text_input", "st.date_input")
    for widget in forbidden_guided_inputs:
        check(widget not in guided_source, f"The guided journey must not require visitor-supplied inputs: {widget}")

    launcher = (ROOT / "run_windows.bat").read_text(encoding="utf-8").casefold()
    check("requirements.txt" in launcher, "Windows launcher does not install the declared requirements.")
    check("streamlit run app.py" in launcher, "Windows launcher does not start the application entry point.")
    check(".runtime_venv" in launcher, "Windows launcher does not provide its isolated-environment fallback.")

    required_scope_text = ("Synthetic operational workbenches", "No live connectivity, certification or regulatory attestation")
    for statement in required_scope_text:
        check(statement.casefold() in app_source.casefold(), f"Missing application scope disclosure: {statement}")


def check_content_model() -> None:
    """Check the professional narrative and the shared synthetic case pack."""
    required_profile = {"name", "headline", "current_context", "career_foundation", "proposition", "working_pattern"}
    check(required_profile <= PROFESSIONAL_PROFILE.keys(), "Professional profile is missing a narrative field.")
    check(all(PROFESSIONAL_PROFILE[field] for field in required_profile), "Professional profile contains empty content.")
    check(
        PROFESSIONAL_PROFILE["working_pattern"] == ["Understand", "Structure", "Engineer", "Validate", "Communicate", "Deliver"],
        "Professional working pattern should follow the supplied portfolio narrative.",
    )

    pillar_names = [pillar[0] for pillar in CAPABILITY_PILLARS]
    check(
        pillar_names == ["Business understanding", "Project delivery", "Technical engineering", "Communication"],
        "Expected the four documented capability pillars in narrative order.",
    )
    check(all(pillar[1] for pillar in CAPABILITY_PILLARS), "Every capability pillar needs an explanation.")

    check(DELIVERY_STAGES[0] == "Business need", "Delivery chain must begin with the business need.")
    check(DELIVERY_STAGES[-1] == "Business as usual handover", "Delivery chain must end with operational handover.")
    check(len(DELIVERY_STAGES) == len(set(DELIVERY_STAGES)), "Delivery-stage names must be unique.")
    check(
        {"Proof of concept", "User Acceptance Testing", "Production readiness"} <= set(DELIVERY_STAGES),
        "Delivery chain is missing evidence-based stage gates.",
    )

    check(len(FUNDS) == 4, "Expected four synthetic fund contexts.")
    fund_names = [fund["Fund"] for fund in FUNDS]
    check(len(fund_names) == len(set(fund_names)), "Synthetic fund names must be unique.")
    for fund in FUNDS:
        check(
            all(fund.get(field) for field in ("Fund", "Share class", "Base currency", "Valuation frequency")),
            f"Incomplete fund context: {fund}",
        )

    check(len(PROJECTS) == 8, "Expected the eight documented transformation workstreams.")
    project_ids = [project["id"] for project in PROJECTS]
    check(project_ids == [f"P{number:02d}" for number in range(1, 9)], "Project identifiers must cover P01 through P08 in order.")
    required_project_fields = {
        "id",
        "title",
        "pillar",
        "metric",
        "challenge",
        "objective",
        "tools",
        "pipeline",
        "decisions",
        "controls",
        "evidence",
        "learning",
    }
    for project in PROJECTS:
        check(required_project_fields <= project.keys(), f"Project {project.get('id')} is missing required fields.")
        check(
            all(project[field] for field in required_project_fields),
            f"Project {project['id']} contains empty required content.",
        )

    event_ids = [row["Event ID"] for row in RECONCILIATION_EVENTS]
    check(event_ids and len(event_ids) == len(set(event_ids)), "Reporting event identifiers must be nonempty and unique.")
    status_set = {"Matched", "Outstanding Active", "Outstanding Hold"}
    for row in RECONCILIATION_EVENTS:
        check(row["Fund"] in fund_names, f"Reporting event {row['Event ID']} refers to an unknown fund.")
        check(row["Reconciliation status"] in status_set, f"Reporting event {row['Event ID']} has an unknown status.")
        check(row["Amount under investigation (EUR)"] >= 0, f"Reporting event {row['Event ID']} has negative exposure.")
        check(row["Age (days)"] >= 0, f"Reporting event {row['Event ID']} has negative ageing.")
        date.fromisoformat(row["Event date"])

    check(set(SYNTHETIC_POSITIONS_BY_FUND) == set(fund_names), "Every synthetic fund needs its own position set.")
    check(SYNTHETIC_POSITIONS == SYNTHETIC_POSITIONS_BY_FUND[fund_names[0]],
          "The first-fund fixture must remain available for baseline valuation checks.")
    required_position_fields = {
        "Position ID", "Instrument", "Instrument type", "Quantity", "Local price", "Local currency",
        "FX rate to EUR", "Price status", "Price timestamp",
    }
    allowed_types = {"Listed equity", "Government bond", "Corporate bond", "Cash equivalent"}
    signatures = set()
    all_ids = []
    for fund_name, positions in SYNTHETIC_POSITIONS_BY_FUND.items():
        check(bool(positions), f"{fund_name} has no synthetic positions.")
        signatures.add(tuple((row["Instrument"], row["Instrument type"]) for row in positions))
        fund_ids = [row["Position ID"] for row in positions]
        check(len(fund_ids) == len(set(fund_ids)), f"{fund_name} has duplicate position identifiers.")
        all_ids.extend(fund_ids)
        for row in positions:
            check(required_position_fields <= row.keys(), f"Position {row.get('Position ID')} is missing a valuation input.")
            check(row["Instrument type"] in allowed_types,
                  f"Position {row['Position ID']} uses a derivative or unsupported instrument type.")
            check(not re.search(r"\b(future|option|swap|forward|derivative)\b", row["Instrument"], re.IGNORECASE),
                  f"Position {row['Position ID']} uses derivative valuation semantics.")
            check(row["Quantity"] >= 0 and row["Local price"] >= 0 and row["FX rate to EUR"] > 0,
                  f"Position {row['Position ID']} has an invalid quantity, price or foreign-exchange rate.")
            check(row["Price status"] == "Current", f"Default price evidence for {row['Position ID']} should be current.")
            datetime.strptime(row["Price timestamp"], "%Y-%m-%d %H:%M UTC")
            if row["Local currency"] == "EUR":
                check(row["FX rate to EUR"] == 1.0, f"EUR position {row['Position ID']} should not have an FX conversion.")
        position_value = sum(row["Quantity"] * row["Local price"] * row["FX rate to EUR"] for row in positions)
        check(round(position_value, 2) == round(Valuation().portfolio, 2),
              f"{fund_name} position values do not reconcile to the default aggregate portfolio input.")
    check(len(all_ids) == len(set(all_ids)), "Position identifiers must be unique across the synthetic funds.")
    check(len(signatures) == len(fund_names), "Funds should not show identical instrument holdings.")
    by_name = SYNTHETIC_POSITIONS_BY_FUND
    check(all(row["Instrument type"] == "Listed equity" for row in by_name["Aurora Equity Fund"]),
          "The synthetic equity fund should contain equity holdings.")
    check(all(row["Instrument type"] in {"Government bond", "Corporate bond"} for row in by_name["Meridian Bond Fund"]),
          "The synthetic bond fund should contain bond holdings.")
    check(all(row["Instrument type"] == "Listed equity" for row in by_name["Helios Index Fund"]),
          "The synthetic index fund should contain physical equity holdings.")
    check({"Listed equity", "Government bond", "Corporate bond"} <= {row["Instrument type"] for row in by_name["Atlas Multi-Asset Fund"]},
          "The synthetic multi-asset fund should include equity and bond holdings.")

    check(set(TRADE_SECURITIES_BY_FUND) == set(fund_names), "Every fund needs a trade-ledger mapping.")
    trade_ids = []
    for fund_name in fund_names:
        rows = synthetic_trades_for_fund(fund_name)
        position_names = {row["Instrument"] for row in SYNTHETIC_POSITIONS_BY_FUND[fund_name]}
        check(len(rows) == 2, f"{fund_name} needs one illustrative purchase and sale.")
        check(all(row["Fund"] == fund_name and row["Security"] in position_names for row in rows),
              f"{fund_name} has a trade outside its seeded position book.")
        check(all(round(row["Quantity"] * row["Price"], 2) == round(row["Gross amount (EUR)"], 2) for row in rows),
              f"{fund_name} has a trade amount that does not match quantity times price.")
        check(sum(row["Gross amount (EUR)"] for row in rows if row["Side"] == "Buy") == 1_326_300,
              f"{fund_name} purchases do not agree with the baseline cash ladder.")
        check(sum(row["Gross amount (EUR)"] for row in rows if row["Side"] == "Sell") == 1_228_000,
              f"{fund_name} sales do not agree with the baseline cash ladder.")
        trade_ids.extend(row["Trade ID"] for row in rows)
    check(len(trade_ids) == len(set(trade_ids)), "Illustrative trade identifiers must be unique across funds.")

    check(len(NAV_FOUNDATION_STEPS) == 12, "Expected twelve Net Asset Value foundation steps.")
    step_ids = [step[0] for step in NAV_FOUNDATION_STEPS]
    check(step_ids == [f"{number:02d}" for number in range(1, 13)], "Foundation steps must run from 01 to 12.")

    expected_break_fields = {
        "Break ID",
        "Fund",
        "Instrument",
        "Difference type",
        "Fund accounting amount",
        "Custodian amount",
        "Investment manager amount",
        "Source currency",
        "Amount under investigation (EUR)",
        "Impact (basis points)",
        "Age (days)",
        "Workflow status",
        "Severity",
        "Root cause",
        "Control layer",
    }
    break_ids = [item["Break ID"] for item in SYNTHETIC_BREAKS]
    check(len(break_ids) == len(set(break_ids)), "Reconciliation break identifiers must be unique.")
    for item in SYNTHETIC_BREAKS:
        check(expected_break_fields <= item.keys(), f"Break {item.get('Break ID')} is missing required fields.")
        check(item["Fund"] in fund_names, f"Break {item['Break ID']} refers to an unknown fund.")


def check_controlled_language() -> None:
    """Keep CAM unambiguous and private source material outside the app."""
    cam_entries = [entry for entry in GLOSSARY if entry[1] == "CAM"]
    check(len(cam_entries) == 1, "CAM must have exactly one controlled glossary definition.")
    check(cam_entries[0][0] == "Client Account Manager", "CAM must mean Client Account Manager.")
    check(
        "relationship owner" in cam_entries[0][3].casefold(),
        "The Client Account Manager definition must describe the client-relationship responsibility.",
    )

    private_files = [
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix.casefold() in {".pdf", ".pptx", ".docx", ".zip"}
    ]
    check(not private_files, f"Original professional documents must not be packaged in the application: {private_files}")
    check(not (ROOT / "reference_review").exists(), "Extracted reference-review material must not be packaged in the application.")

    publishable_extensions = {".py", ".md", ".toml", ".txt", ".bat"}
    combined = "\n".join(
        path.read_text(encoding="utf-8-sig", errors="ignore")
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix.casefold() in publishable_extensions and path.name != Path(__file__).name
    )
    blocked_patterns = (
        r"\bBNP\b",
        r"\bUBS\b",
        r"Morgan Stanley",
        r"\bHSBC\b",
        r"BlackRock",
        r"State Street",
        r"Northern Trust",
        r"Temenos",
        r"SimCorp",
        r"Aladdin",
        r"MultiFonds",
    )
    for pattern in blocked_patterns:
        check(not re.search(pattern, combined, flags=re.IGNORECASE), f"Institution-specific term found: {pattern}")

    unsupported_book_terms = (r"\bIBOR\b", r"\bABOR\b", r"\bCBOR\b", r"\b(?:Investment|Accounting|Custody) Book of Record\b")
    for pattern in unsupported_book_terms:
        check(not re.search(pattern, combined, flags=re.IGNORECASE), f"Unsupported source-document terminology found: {pattern}")
    basis_entries = [entry for entry in GLOSSARY if entry[0] == "Basis points"]
    check(len(basis_entries) == 1 and basis_entries[0][1] == "bps", "Basis points must use the short form bps.")

    misleading_claims = (
        r"\bCSSF[- ]certified\b",
        r"\bregulator[- ]approved\b",
        r"\b(?:provides?|creates?|maintains?) an immutable audit (?:trail|archive)\b",
        r"\bofficial statutory report\b",
    )
    for pattern in misleading_claims:
        check(not re.search(pattern, combined, flags=re.IGNORECASE), f"Unsupported assurance claim found: {pattern}")


def check_finance_calculations() -> None:
    """Exercise the central pure calculations with known outcomes."""
    base = Valuation().calculate()
    check(round(base["assets"], 2) == 500_500_000.00, "Default total assets changed unexpectedly.")
    check(round(base["liabilities"], 2) == 25_506_507.00, "Default liabilities changed unexpectedly.")
    check(round(base["nav"], 2) == 474_993_493.00, "Default Net Asset Value changed unexpectedly.")
    check(round(base["price"], 4) == 118.7484, "Default Net Asset Value per unit changed unexpectedly.")
    check(base["distribution_price"] == base["adjusted"], "Simulated distribution price must use the adjusted result.")

    upward = Valuation(flow=3_000_000.0, threshold=0.5, bps=20).calculate()
    downward = Valuation(flow=-3_000_000.0, threshold=0.5, bps=20).calculate()
    check(upward["triggered"] and upward["direction"] == "Upward", "Subscription swing scenario did not trigger upward.")
    check(upward["adjusted"] > upward["price"], "Upward swing must increase the simulated distribution price.")
    check(downward["triggered"] and downward["direction"] == "Downward", "Redemption swing scenario did not trigger downward.")
    check(downward["adjusted"] < downward["price"], "Downward swing must reduce the simulated distribution price.")

    forecast = cash_forecast(
        opening_cash=14_200_000.0,
        subscriptions=5_000_000.0,
        redemptions=2_000_000.0,
        purchase_settlements=1_326_300.0,
        sale_settlements=1_228_000.0,
        collateral=350_000.0,
        minimum_buffer_percent=2.0,
    )
    check(forecast["projected_cash"] == 16_751_700.0, "Cash forecast does not reconcile to known movements.")
    check(forecast["status"] == "Sufficient", "Known cash forecast should remain above its illustrative buffer.")

    journal = journal_entry("Accrue the management fee", 12_500.0, "VAL-TEST")
    check(sum(line["Debit (EUR)"] for line in journal) == 12_500.0, "Journal debit is not balanced.")
    check(sum(line["Credit (EUR)"] for line in journal) == 12_500.0, "Journal credit is not balanced.")

    fee = performance_fee(112.0, 100.0, 5.0, 20.0, 1_000_000.0)
    check(
        fee == {"hurdle_level": 105.0, "eligible_gain_per_unit": 7.0, "fee": 1_400_000.0},
        "Performance-fee result changed unexpectedly.",
    )


def check_workflow_helpers() -> None:
    """Check deterministic routes used by interactive control demonstrations."""
    quarantine = anomaly_assessment(False, True, observed_days=8, expected_days=5, calculation_conflict=True)
    check(
        quarantine["route"] == "Data-quality quarantine" and quarantine["score"] is None,
        "Invalid source data must not receive an anomaly score.",
    )
    urgent = anomaly_assessment(True, True, observed_days=8, expected_days=5, calculation_conflict=True)
    check(
        urgent["score"] == 1.0 and urgent["band"] == "Urgent analyst review",
        "Combined anomaly rules should produce the urgent review band.",
    )

    chunks = chunk_plan(total_rows=1_001, rows_per_chunk=250)
    check(len(chunks) == 5, "Chunk plan should contain five sequential parts.")
    check(sum(int(chunk["Data rows"]) for chunk in chunks) == 1_001, "Chunk plan lost or duplicated rows.")
    check(
        chunks[0]["First source row"] == 1 and chunks[-1]["Last source row"] == 1_001,
        "Chunk boundaries do not cover the full source.",
    )

    global_route = operating_model_route(True, False, True)
    local_route = operating_model_route(True, True, True)
    check(
        global_route["model"] == "Global standardized model",
        "Supported standardized product should use the global model.",
    )
    check(
        local_route["model"] == "Jurisdiction-specific local model",
        "Mandatory local rule must select the local model.",
    )

    confirmation = parse_confirmation(
        "REFERENCE=ETD-01;TRADE_DATE=2026-09-17;SETTLEMENT_DATE=2026-09-18;"
        "INSTRUMENT=Equity index future;CONTRACTS=10;CONTRACT_SIZE=50;PRICE=4200;"
        "CURRENCY=EUR;DIRECTION=BUY",
        "Exchange-Traded Derivative future",
    )
    check(
        confirmation["route"] == "Eligible for human approval",
        "Complete confirmation should reach human approval review.",
    )
    check(
        confirmation["mapped"]["notional"] == 2_100_000.0,
        "Derivative notional mapping changed unexpectedly.",
    )


def main() -> None:
    checks = (
        ("Source structure and page registration", check_source_structure),
        ("Portfolio content model", check_content_model),
        ("Controlled language and scope", check_controlled_language),
        ("Finance calculations", check_finance_calculations),
        ("Workflow helpers", check_workflow_helpers),
    )
    for label, validation in checks:
        validation()
        print(f"PASS  {label}")

    print("\nVALIDATION PASSED")
    print(f"Pages: {len(EXPECTED_PAGES)}")
    print(f"Missions: {len(PROJECTS)}")
    print(f"Net Asset Value foundation steps: {len(NAV_FOUNDATION_STEPS)}")
    print(f"Default Net Asset Value per unit: EUR {Valuation().calculate()['price']:.4f}")


if __name__ == "__main__":
    main()
