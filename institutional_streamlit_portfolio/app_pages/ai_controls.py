from __future__ import annotations

import csv
from datetime import date
from io import BytesIO, StringIO
import re
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import streamlit as st

from ui import control_warning

from ui import aligned_dataframe

from learning import explain

from domain import chunk_plan, parse_confirmation
from state import log_event
from ui import metric_row, module_footer, page_header


SCHEDULE_COLUMNS = [
    "Fund",
    "Valuation frequency",
    "Valuation date",
    "Expected completion date",
    "Actual or forecast completion date",
    "Tolerance (calendar days)",
    "Schedule evidence reference",
]
SCHEDULE_FREQUENCIES = {"Daily", "Weekly", "Monthly", "Quarterly"}
SCHEDULE_EXAMPLE = (
    ",".join(SCHEDULE_COLUMNS)
    + "\nAurora Equity Fund,Daily,2026-09-15,2026-09-16,2026-09-17,0,Approved NAV calendar section 4.2\n"
    + "Meridian Bond Fund,Monthly,2026-08-31,2026-09-02,2026-09-02,0,August valuation timetable row 8\n"
)


def assess_schedule_manifest(source: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [column for column in SCHEDULE_COLUMNS if column not in source.columns]
    if missing_columns:
        raise ValueError("Missing required columns: " + ", ".join(missing_columns))
    if source.empty:
        raise ValueError("The schedule manifest has a header but no data rows.")
    if len(source) > 10_000:
        raise ValueError("The schedule manifest exceeds the 10,000-row limit.")
    assessments = []
    for row_number, (_, row) in enumerate(source.iterrows(), start=2):
        values = {column: str(row[column]).strip() for column in SCHEDULE_COLUMNS}
        issues = []
        if not values["Fund"]:
            issues.append("Fund name is required")
        if values["Valuation frequency"] not in SCHEDULE_FREQUENCIES:
            issues.append("Frequency must be Daily, Weekly, Monthly or Quarterly")
        if not values["Schedule evidence reference"]:
            issues.append("Approved schedule evidence reference is required")
        parsed_dates = {}
        for column in ("Valuation date", "Expected completion date", "Actual or forecast completion date"):
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", values[column]):
                    raise ValueError
                parsed_dates[column] = date.fromisoformat(values[column])
            except ValueError:
                issues.append(f"{column} must be an ISO date (YYYY-MM-DD)")
        try:
            tolerance = int(values["Tolerance (calendar days)"])
            if tolerance < 0:
                raise ValueError
        except ValueError:
            tolerance = None
            issues.append("Tolerance must be a nonnegative whole number of calendar days")
        if len(parsed_dates) == 3:
            valuation_date = parsed_dates["Valuation date"]
            if parsed_dates["Expected completion date"] < valuation_date:
                issues.append("Expected completion precedes the valuation date")
            if parsed_dates["Actual or forecast completion date"] < valuation_date:
                issues.append("Actual or forecast completion precedes the valuation date")
        variance = (
            (parsed_dates["Actual or forecast completion date"] - parsed_dates["Expected completion date"]).days
            if len(parsed_dates) == 3 else None
        )
        if issues:
            assessment = "Source review required"
        elif variance > tolerance:
            assessment = "Late — human review"
        elif variance < 0:
            assessment = "Early — verify valuation cycle"
        else:
            assessment = "Within supplied tolerance"
        assessments.append({
            "Source row": row_number,
            **values,
            "Calendar variance (days)": variance,
            "Assessment": assessment,
            "Control issue": "; ".join(issues),
        })
    return pd.DataFrame(assessments)


def read_csv_rows(raw: bytes) -> tuple[list[str], list[list[str]]]:
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("The file exceeds the 10 MB in-memory limit.")
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Use a UTF-8 encoded comma-separated value file.") from exc
    try:
        reader = csv.reader(StringIO(decoded, newline=""), strict=True)
        header = next(reader, None)
        if not header or not any(cell.strip() for cell in header):
            raise ValueError("The file needs a nonempty header row.")
        rows = []
        for row_number, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise ValueError(f"Row {row_number} has {len(row)} fields; the header has {len(header)}.")
            rows.append(row)
    except csv.Error as exc:
        raise ValueError(f"Invalid quoted comma-separated values: {exc}") from exc
    if not rows:
        raise ValueError("The file contains a header but no data rows.")
    return header, rows


def csv_bytes(rows: list[list[str]]) -> bytes:
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


page_header(
    "PROJECT DEMOS / CONTROLLED AUTOMATION",
    "Controlled automation scenarios",
    "Use the examples below to see how a confirmation is checked, a valuation delay is flagged or a large CSV file is split. All examples use fictional data.",
    ":material/memory:",
)

parser_tab, calendar_tab, chunker_tab = st.tabs(
    ["Read a confirmation", "Check a valuation date", "Split a CSV file"]
)

SAMPLES = {
    "Exchange-Traded Derivative future": "REFERENCE=DEMO-ETD-99401; TRADE_DATE=2026-08-14; SETTLEMENT_DATE=2026-08-16; INSTRUMENT=INDEX_FUTURE_DEC26; CONTRACTS=40; CONTRACT_SIZE=50; PRICE=5410.25; CURRENCY=USD; DIRECTION=BUY",
    "Foreign-exchange swap": "REFERENCE=DEMO-FX-773; TRADE_DATE=2026-08-14; NEAR_DIRECTION=SELL; NEAR_CURRENCY=EUR; NEAR_AMOUNT=5000000; NEAR_RATE=1.0850; NEAR_DATE=2026-08-16; FAR_DIRECTION=BUY; FAR_CURRENCY=EUR; FAR_AMOUNT=5000000; FAR_RATE=1.0892; FAR_DATE=2026-11-16",
}

with parser_tab:
    explain('parser')
    st.subheader("Read a broker confirmation")
    st.caption("Start: choose a product, edit the sample text if you wish, then run the extraction. This demo uses fixed parsing rules; it does not call an AI model or external service.")
    product = st.segmented_control("Product template", list(SAMPLES), default=list(SAMPLES)[0], key="ai_product")
    source_text = st.text_area("Source confirmation text", value=SAMPLES[product], height=150, key=f"source_{product}")
    if st.button("Run controlled extraction", type="primary", icon=":material/play_arrow:"):
        try:
            parsed = parse_confirmation(source_text, product)
            st.session_state.ai_result = {"product": product, "source": source_text, "output": parsed}
            log_event("Controlled confirmation extraction run", parsed["route"], "Automation laboratory user", f"Template: {product}; field completeness: {parsed['confidence']}%.", scope="Automation laboratory")
        except ValueError as exc:
            st.error(str(exc))
    stored_result = st.session_state.get("ai_result")
    result = (
        stored_result.get("output")
        if isinstance(stored_result, dict) and stored_result.get("product") == product and stored_result.get("source") == source_text
        else None
    )
    if stored_result and result is None:
        st.info("The template or source text changed. Run the extraction again to create a matching result.")
    if result:
        with st.expander("How the extraction works"):
            st.markdown("1. Read only named fields from the source text.\n2. Map the fields using the selected product's rules.\n3. Check required values and dates.\n4. Show the output or explain why it needs review.", text_alignment="justify")
        metric_row(
            [
                ("Field-completeness score", f"{result['confidence']:.1f}%", "Percentage of mandatory template fields found; it is not model confidence"),
                ("Missing mandatory fields", str(len(result["missing"])), "Fields absent from the bounded source"),
                ("Validation errors", str(len(result["errors"])), "Product or chronology rules that failed"),
                ("Route", result["route"], "Every output still requires a human operating decision"),
            ]
        )
        if result["errors"] or result["missing"]:
            st.error("; ".join(result["errors"] + [f"Missing {field}" for field in result["missing"]]))
        else:
            st.success("The structured result is eligible for human approval in this demonstration.")
        with st.expander("Inspect source evidence and mapped fields"):
            left, right = st.columns([1.2, 1], gap="large")
            with left:
                st.subheader("Field-level evidence")
                aligned_dataframe(pd.DataFrame(result["evidence"]), hide_index=True, width="stretch")
            with right:
                st.subheader("Mapped payload")
                st.json(result["mapped"], expanded=True)

with calendar_tab:
    explain('calendar')
    st.subheader("Check a Net Asset Value completion date")
    st.markdown("Select a valuation frequency, then compare the expected date with the actual or forecast date. The expected date must come from an approved fund schedule.", text_alignment="justify")
    frequency = st.selectbox("Valuation frequency", ["Daily", "Weekly", "Monthly", "Quarterly"])
    schedule_guidance = {
        "Daily": "Source the expected date from the next valid fund business day after the valuation point.",
        "Weekly": "Source the expected date from the fund's named weekly valuation weekday and holiday calendar.",
        "Monthly": "Source the expected date from the month-end or stated monthly valuation rule.",
        "Quarterly": "Source the expected date from the governing quarterly valuation schedule.",
    }
    st.caption(schedule_guidance[frequency])
    schedule_reference = st.text_input(
        "Approved schedule evidence reference",
        value="Demonstration calendar — replace with the approved fund timetable",
        help="Name the fund calendar, document section or controlled schedule row that supplies the expected date.",
    )
    expected_date = st.date_input("Expected valuation completion date", value=date(2026, 9, 16), key="expected_nav_date")
    actual_date = st.date_input("Actual or forecast completion date", value=date(2026, 9, 17), key="actual_nav_date")
    grace_days = st.number_input("Documented calendar-day tolerance", min_value=0, value=0, step=1)
    delta = (actual_date - expected_date).days
    assessment = "Late" if delta > grace_days else "Early — verify cycle" if delta < 0 else "Within tolerance"
    metric_row(
        [
            ("Calendar variance", f"{delta:+d} days", "Actual or forecast date minus the explicit expected date"),
            ("Frequency", frequency, "Determines how the expected schedule should be sourced"),
            ("Assessment", assessment, "Uses the user-supplied calendar-day tolerance"),
        ]
    )
    if not schedule_reference.strip():
        st.error("Enter the approved schedule evidence reference before relying on this assessment.")
    elif actual_date < expected_date:
        st.info("The actual or forecast date precedes the expected date. Confirm that both dates refer to the same valuation cycle.")
    elif delta > grace_days:
        control_warning(f"Potential delay: route the record for human review with schedule evidence: {schedule_reference.strip()}.")
    else:
        st.success(f"No delay under the supplied expected date and tolerance. Schedule evidence: {schedule_reference.strip()}.")
    st.caption("A production checker would also apply the relevant business-day calendar, holidays, cut-off time and fund-specific exceptions.")

    with st.expander("Check several valuations from a CSV file"):
        st.markdown("Upload a CSV schedule when you want to check several valuations at once. Each row must include its expected date and evidence reference.", text_alignment="justify")
        st.download_button(
            "Download example schedule manifest",
            SCHEDULE_EXAMPLE.encode("utf-8"),
            "nav-schedule-example.csv",
            "text/csv",
            icon=":material/download:",
        )
        schedule_file = st.file_uploader("Upload a schedule manifest", type=["csv"], key="nav_schedule_manifest")
        if schedule_file is not None:
            try:
                if schedule_file.size > 10 * 1024 * 1024:
                    raise ValueError("The schedule manifest exceeds the 10 MB in-memory limit.")
                source_manifest = pd.read_csv(
                    BytesIO(schedule_file.getvalue()),
                    dtype=str,
                    keep_default_na=False,
                    na_filter=False,
                    encoding="utf-8-sig",
                )
                reviewed_manifest = assess_schedule_manifest(source_manifest)
                late_count = int((reviewed_manifest["Assessment"] == "Late — human review").sum())
                source_issues = int((reviewed_manifest["Assessment"] == "Source review required").sum())
                metric_row([
                    ("Valuations reviewed", f"{len(reviewed_manifest):,}", "One source manifest row per valuation"),
                    ("Potential delays", f"{late_count:,}", "Beyond the supplied calendar-day tolerance"),
                    ("Source issues", f"{source_issues:,}", "Incomplete or inconsistent source records"),
                ])
                aligned_dataframe(reviewed_manifest, hide_index=True, width="stretch")
                st.download_button(
                    "Download assessed schedule",
                    reviewed_manifest.to_csv(index=False).encode("utf-8"),
                    "nav-schedule-assessment.csv",
                    "text/csv",
                    icon=":material/download:",
                )
            except (ValueError, UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
                st.error(f"The schedule manifest could not be assessed: {exc}")

with chunker_tab:
    explain('chunks')
    st.subheader("Split a CSV file into smaller parts")
    st.caption("Start with the sample row count, or upload your own CSV. The download includes a manifest so you can check that every input row appears in exactly one part.")
    uploaded = st.file_uploader("Upload a comma-separated value file", type=["csv"], help="The file is processed in memory and is not sent to an external service.")
    rows_per_chunk = st.number_input("Data rows per output file", min_value=1, value=200, step=50)
    if uploaded is None:
        total_rows = st.number_input("Or preview a plan for this many rows", min_value=1, value=1_000, step=100)
        plan = pd.DataFrame(chunk_plan(int(total_rows), int(rows_per_chunk)))
        metric_row(
            [
                ("Input rows", f"{int(total_rows):,}", "Illustrative data rows, excluding the header"),
                ("Output files", f"{len(plan):,}", "Ceiling of rows divided by rows per file"),
                ("Rows reconciled", f"{int(plan['Data rows'].sum()):,}", "Must equal the input row count"),
            ]
        )
        aligned_dataframe(plan, hide_index=True, width="stretch")
    else:
        try:
            header, rows = read_csv_rows(uploaded.getvalue())
            plan = pd.DataFrame(chunk_plan(len(rows), int(rows_per_chunk)))
            safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", uploaded.name.rsplit(".", 1)[0]).strip("._") or "source"
            buffer = BytesIO()
            with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
                for index, start in enumerate(range(0, len(rows), int(rows_per_chunk)), start=1):
                    part = rows[start : start + int(rows_per_chunk)]
                    archive.writestr(f"{safe_stem}_part_{index:03d}.csv", csv_bytes([header, *part]))
                archive.writestr("chunk_manifest.csv", plan.to_csv(index=False))
            buffer.seek(0)
            metric_row(
                [
                    ("Input rows", f"{len(rows):,}", "Rows parsed from the uploaded file"),
                    ("Output files", f"{len(plan):,}", "Data chunks; a separate manifest is also included"),
                    ("Rows reconciled", f"{int(plan['Data rows'].sum()):,}", "Sum of output data rows"),
                ]
            )
            aligned_dataframe(plan, hide_index=True, width="stretch")
            st.download_button("Download chunks and manifest", buffer.getvalue(), "sequential-chunks.zip", "application/zip", icon=":material/download:")
            st.success("Every parsed data row is assigned to exactly one sequential chunk. Field text, order and duplicate headers are retained; comma-separated value quoting and byte layout may be normalized.")
        except ValueError as exc:
            st.error(f"The file could not be parsed as comma-separated values: {exc}")

module_footer("ai_controls", "app_pages/governance.py", "Continue to governance and resilience")
