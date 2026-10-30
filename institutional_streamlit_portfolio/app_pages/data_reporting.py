from __future__ import annotations

from io import StringIO

import altair as alt
import pandas as pd
import streamlit as st

from ui import control_warning

from ui import readable_chart

from ui import aligned_dataframe, aligned_table

from learning import explain, explain_events

from data import RECONCILIATION_EVENTS
from domain import anomaly_assessment
from styles import ALERT_RED, AMBER, DEEP_GREEN, PRIMARY_GREEN
from ui import definition, metric_row, module_footer, page_header


page_header(
    "PROJECT DEMO / REPORTING AND DATA QUALITY",
    "From reconciliation records to a clear picture",
    "This fictional dataset demonstrates the reporting and data-quality work described in the mission portfolio. Change the filters to see what is matched, what remains open and how the totals are checked.",
    ":material/database:",
)

with st.expander("What does one row represent?"):
    definition(
        "Data grain",
        "A fund appears once in the fund list but can have many reconciliation events. Keeping those two row types separate prevents a report from counting the same fund more than once.",
    )

events = pd.DataFrame(RECONCILIATION_EVENTS)
events["Event date"] = pd.to_datetime(events["Event date"])
fund_dimension = pd.DataFrame(
    {
        "Synthetic fund identifier": [f"FND-{index:03d}" for index in range(1, events["Fund"].nunique() + 1)],
        "Fund": sorted(events["Fund"].unique()),
    }
)
events["Synthetic fund identifier"] = events["Fund"].map(
    fund_dimension.set_index("Fund")["Synthetic fund identifier"]
)

kpi_tab, pipeline_tab, model_tab, quality_tab, anomaly_tab = st.tabs(
    ["Reconciliation view", "Combine CSV files", "Data model", "Missing values", "Anomaly check"]
)

with kpi_tab:
    explain('reporting')
    st.subheader("Non-cash reconciliation view")
    st.caption("Start here: choose a fund, location or status. The numbers and charts update from the same 24 fictional event rows.")
    f1, f2, f3 = st.columns(3)
    selected_funds = f1.multiselect("Fund", sorted(events["Fund"].unique()), default=sorted(events["Fund"].unique()))
    selected_locations = f2.multiselect("Processing location", sorted(events["Processing location"].unique()), default=sorted(events["Processing location"].unique()))
    selected_statuses = f3.multiselect("Reconciliation status", sorted(events["Reconciliation status"].unique()), default=sorted(events["Reconciliation status"].unique()))
    filtered = events[
        events["Fund"].isin(selected_funds)
        & events["Processing location"].isin(selected_locations)
        & events["Reconciliation status"].isin(selected_statuses)
    ].copy()

    if filtered.empty:
        control_warning("The current filters return no reconciliation events.")
    else:
        explain_events(filtered.to_dict("records"))
        matched = filtered[filtered["Reconciliation status"] == "Matched"]
        outstanding = filtered[filtered["Reconciliation status"].isin(["Outstanding Active", "Outstanding Hold"])]
        match_rate = len(matched) / len(filtered) * 100
        auto_match_rate = (matched["Match method"] == "Automatic").sum() / len(matched) * 100 if len(matched) else None
        on_time_rate = (filtered["Timeliness"] == "On time").sum() / len(filtered) * 100
        open_amount = outstanding["Amount under investigation (EUR)"].sum()
        average_age = outstanding["Age (days)"].mean() if len(outstanding) else None
        metric_row(
            [
                ("Unique funds", f"{filtered['Synthetic fund identifier'].nunique():,}", "Distinct synthetic fund entities in the filtered event population"),
                ("Event rows", f"{len(filtered):,}", "One row per reconciliation event; this is not a fund count"),
                ("Match rate", f"{match_rate:.1f}%", "Matched events divided by the filtered reconciliation population"),
                ("Automatic share of matched", f"{auto_match_rate:.1f}%" if auto_match_rate is not None else "Not applicable", "Automatically matched events divided by all matched events"),
            ]
        )
        with st.expander("See amount, ageing and timeliness measures"):
            metric_row(
                [
                    ("Outstanding events", f"{len(outstanding):,}", "Outstanding Active plus Outstanding Hold"),
                    ("Amount under investigation", f"EUR {open_amount:,.2f}", "Open amount; it is not automatically a loss"),
                    ("Average open ageing", f"{average_age:.1f} days" if average_age is not None else "Not applicable", "Average age of open events"),
                    ("On-time event share", f"{on_time_rate:.1f}%", "On-time events divided by filtered events"),
                ]
            )

        chart_left, chart_right = st.columns(2, gap="large")
        status_summary = filtered.groupby("Reconciliation status", as_index=False).size().rename(columns={"size": "Events"})
        with chart_left:
            st.markdown("**Population by status**")
            status_chart = alt.Chart(status_summary).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("Events:Q", title="Event rows"),
                y=alt.Y("Reconciliation status:N", sort="-x", title=None),
                color=alt.Color(
                    "Reconciliation status:N",
                    scale=alt.Scale(
                        domain=["Matched", "Outstanding Active", "Outstanding Hold"],
                        range=[PRIMARY_GREEN, AMBER, ALERT_RED],
                    ),
                    legend=None,
                ),
                tooltip=["Reconciliation status", "Events"],
            )
            readable_chart(status_chart, width="stretch")
        with chart_right:
            st.markdown("**Open amount concentration**")
            concentration = outstanding.groupby("Fund", as_index=False)["Amount under investigation (EUR)"].sum()
            if concentration.empty:
                st.info("No outstanding amount is present in the filtered population.")
            else:
                concentration_chart = alt.Chart(concentration).mark_bar(cornerRadiusTopRight=4).encode(
                    x=alt.X("Fund:N", sort="-y", title=None),
                    y=alt.Y("Amount under investigation (EUR):Q", title="EUR"),
                    color=alt.value(PRIMARY_GREEN),
                    tooltip=["Fund", alt.Tooltip("Amount under investigation (EUR):Q", format=",.2f")],
                )
                readable_chart(concentration_chart, width="stretch")

        with st.expander("Explore time trends and source checks"):
            trend = filtered.assign(
                Outcome=filtered["Reconciliation status"].where(filtered["Reconciliation status"] == "Matched", "Outstanding")
            ).groupby(["Event date", "Outcome"], as_index=False).size().rename(columns={"size": "Events"})
            st.markdown("**Matched versus outstanding trend**")
            trend_chart = alt.Chart(trend).mark_line(point=True).encode(
                x=alt.X("Event date:T", title=None),
                y=alt.Y("Events:Q", title="Event rows", axis=alt.Axis(tickMinStep=1)),
                color=alt.Color("Outcome:N", scale=alt.Scale(domain=["Matched", "Outstanding"], range=[PRIMARY_GREEN, ALERT_RED])),
                tooltip=[alt.Tooltip("Event date:T", format="%d %b %Y"), "Outcome", "Events"],
            )
            readable_chart(trend_chart, width="stretch")

            st.markdown("**Timeliness by reconciliation status**")
            timeliness = filtered.groupby(["Reconciliation status", "Timeliness"], as_index=False).size().rename(columns={"size": "Events"})
            timeliness_chart = alt.Chart(timeliness).mark_bar().encode(
                x=alt.X("Events:Q", title="Event rows", stack="zero"),
                y=alt.Y("Reconciliation status:N", title=None),
                color=alt.Color(
                    "Timeliness:N",
                    scale=alt.Scale(domain=["On time", "Late"], range=[DEEP_GREEN, ALERT_RED]),
                ),
                tooltip=["Reconciliation status", "Timeliness", "Events"],
            )
            readable_chart(timeliness_chart, width="stretch")

            st.subheader("Source-to-visual reconciliation")
            grouped_count = int(status_summary["Events"].sum())
            grouped_amount = float(concentration["Amount under investigation (EUR)"].sum())
            checks = pd.DataFrame(
                [
                    ["Filtered detail rows", len(filtered), grouped_count, len(filtered) == grouped_count],
                    ["Distinct fund entities", filtered["Synthetic fund identifier"].nunique(), filtered["Fund"].nunique(), filtered["Synthetic fund identifier"].nunique() == filtered["Fund"].nunique()],
                    ["Open amount (EUR)", round(float(open_amount), 2), round(grouped_amount, 2), round(float(open_amount), 2) == round(grouped_amount, 2)],
                    ["Timeliness event rows", len(filtered), int(timeliness["Events"].sum()), len(filtered) == int(timeliness["Events"].sum())],
                ],
                columns=["Control", "Detail result", "Visual aggregation", "Reconciled"],
            )
            aligned_dataframe(checks, hide_index=True, width="stretch")
            aligned_dataframe(filtered, hide_index=True, width="stretch")
            st.download_button("Download filtered event population", filtered.to_csv(index=False), "reconciliation-kpi-detail.csv", "text/csv", icon=":material/download:")

with pipeline_tab:
    explain('pipeline')
    st.subheader("Combine source exports")
    st.markdown("Upload one or more CSV exports. The demo keeps each file and row reference so you can trace every output record back to its source.", text_alignment="justify")
    with st.expander("How source row numbers work"):
        st.caption("Source row counts parsed CSV records, with the header as row 1. A quoted record may span physical lines.")
    uploads = st.file_uploader("Source files", type=["csv"], accept_multiple_files=True, key="source_pipeline_files")
    if not uploads:
        st.info("Upload one or more CSV files to run the pipeline. No file is sent to an external service.")
    else:
        frames = []
        read_log = []
        for upload_index, upload in enumerate(uploads, start=1):
            payload = upload.getvalue()
            decoded = None
            used_encoding = None
            for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
                try:
                    decoded = payload.decode(encoding)
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            try:
                frame = pd.read_csv(StringIO(decoded or ""), dtype=str, keep_default_na=False, na_filter=False)
                reserved = {"Source instance", "Source file", "Source row"}
                collisions = reserved.intersection(frame.columns)
                if collisions:
                    raise ValueError("Source column name conflicts with reserved lineage field(s): " + ", ".join(sorted(collisions)))
                frame.insert(0, "Source row", range(2, len(frame) + 2))
                frame.insert(0, "Source file", upload.name)
                frame.insert(0, "Source instance", upload_index)
                frames.append(frame)
                read_log.append({"Source instance": upload_index, "Source file": upload.name, "Encoding used": used_encoding, "Data rows": len(frame), "Columns": len(frame.columns) - 3, "Status": "Read"})
            except Exception as exc:
                read_log.append({"Source instance": upload_index, "Source file": upload.name, "Encoding used": used_encoding or "Not detected", "Data rows": 0, "Columns": 0, "Status": f"Rejected: {exc}"})
        aligned_dataframe(pd.DataFrame(read_log), hide_index=True, width="stretch")
        rejected_files = len(uploads) - len(frames)
        if rejected_files:
            control_warning(f"{rejected_files} source file(s) were rejected and are excluded from the master table. Review the intake log before using the result.")
        if frames:
            master = pd.concat(frames, ignore_index=True, sort=False).replace("", pd.NA)
            business_columns = [column for column in master.columns if column not in {"Source instance", "Source file", "Source row"}]
            carry_column = st.selectbox("Optional identifier column for justified carry-forward", ["Do not carry values forward", *business_columns])
            if carry_column != "Do not carry values forward":
                missing_before = int(master[carry_column].isna().sum())
                master[carry_column] = master.groupby("Source instance", sort=False)[carry_column].ffill()
                filled = missing_before - int(master[carry_column].isna().sum())
                control_warning(f"Filled {filled} missing {carry_column} value(s) only within each physical upload. Use this control solely where the source layout proves a merged-cell relationship.")
            input_rows = sum(len(frame) for frame in frames)
            duplicate_rows = int(master.drop(columns=["Source instance", "Source file", "Source row"]).duplicated().sum()) if business_columns else 0
            metric_row(
                [
                    ("Files read", f"{len(frames)}/{len(uploads)}", "Successfully parsed source files"),
                    ("Input rows", f"{input_rows:,}", "Sum of parsed data rows"),
                    ("Master rows", f"{len(master):,}", "Rows after unioning the header set"),
                    ("Potential duplicates", f"{duplicate_rows:,}", "Identical business values; source lineage excluded"),
                ]
            )
            if input_rows == len(master):
                st.success("Row-count control passed: every parsed input row appears once in the master table.")
            else:
                st.error("Row-count control failed. Resolve the difference before using the output.")
            aligned_dataframe(master, hide_index=True, width="stretch")
            if business_columns:
                pivot_column = st.selectbox("Build a record-count view by", business_columns)
                pivot = master.groupby(pivot_column, dropna=False).size().reset_index(name="Records").sort_values("Records", ascending=False)
                aligned_dataframe(pivot, hide_index=True, width="stretch")
            st.download_button("Download traceable master data", master.to_csv(index=False), "traceable-master-data.csv", "text/csv", icon=":material/download:")

with model_tab:
    explain('model')
    st.subheader("One fund can have many events")
    st.markdown("Choose a fund below to see how one fund record links to several reconciliation events. This is the reporting model behind the first tab.", text_alignment="justify")
    st.caption("Fund reference → unique fund dimension → repeated reconciliation events → management reporting view")
    dimensions = st.columns(4)
    for column, title, key, purpose in zip(
        dimensions,
        ["Fund dimension", "Date dimension", "Client dimension", "Location dimension"],
        ["Fund identifier", "Calendar date", "Client identifier", "Location identifier"],
        ["One row per fund", "One row per reporting date", "One row per synthetic client segment", "One row per processing location"],
    ):
        with column, st.container(border=True, height="stretch"):
            st.markdown(f"**{title}**")
            st.caption(f"Unique key: {key}")
            st.markdown(purpose, text_alignment="justify")
    st.markdown("**One-to-many filter direction ↓**")
    with st.container(border=True):
        st.subheader("Reconciliation event fact")
        st.markdown("One row per observed event, with fund, date, client and location keys plus status, match method, ageing, timeliness and amount under investigation.", text_alignment="justify")
    st.subheader("Inspect the fund-to-event relationship")
    st.caption("The four identifiers below are generated only for this synthetic demonstration. A production model must use a validated fund-master identifier.")
    aligned_dataframe(fund_dimension, hide_index=True, width="stretch")
    model_fund = st.selectbox("Fund dimension member", fund_dimension["Fund"].tolist())
    model_fund_id = fund_dimension.loc[fund_dimension["Fund"] == model_fund, "Synthetic fund identifier"].iloc[0]
    model_events = events[events["Synthetic fund identifier"] == model_fund_id]
    explain_events(model_events.to_dict("records"))
    metric_row(
        [
            ("Dimension rows", "1", "One unique fund entity is selected"),
            ("Linked event rows", f"{len(model_events):,}", "Repeated reconciliation events linked by the synthetic fund identifier"),
        ]
    )
    aligned_dataframe(model_events, hide_index=True, width="stretch")
    if fund_dimension["Synthetic fund identifier"].is_unique and events["Synthetic fund identifier"].notna().all():
        st.success("Model control passed: each synthetic fund key is unique and every event resolves to one fund dimension row.")
    else:
        st.error("Model control failed: investigate duplicate fund keys or events without a fund match.")
    dictionary = pd.DataFrame(
        [
            ["Fund identifier", "Text", "Fund dimension", "Stable key for one fund", "Use an authoritative source key in production"],
            ["Event date", "Date", "Date dimension", "Date the event was observed", "Reject invalid dates"],
            ["Reconciliation status", "Controlled text", "Event fact", "Matched, Outstanding Active or Outstanding Hold", "Use an approved value list"],
            ["Amount under investigation", "Decimal", "Event fact", "Base-currency amount attached to an open case", "Retain source amount and currency separately in production"],
            ["Age in days", "Integer", "Derived measure", "Elapsed days while an event remains open", "Do not replace a missing start date with zero"],
        ],
        columns=["Field", "Type", "Table", "Business meaning", "Control"],
    )
    aligned_dataframe(dictionary, hide_index=True, width="stretch")

with quality_tab:
    explain('missing')
    st.subheader("A missing value is different from zero")
    st.markdown("Assess an incoming value and its proposed treatment. Zero is a measured value; blank means no value was supplied. Mixing them can make a false match.", text_alignment="justify")
    sample = st.segmented_control("Incoming value", ["Blank / NULL", "Verified 0.00", "Invalid text", "Valid 125.40"], default="Blank / NULL")
    treatment = st.selectbox("Proposed transformation", ["Preserve missing value", "Convert to zero", "Reject or quarantine", "Parse as a number"])
    outcomes = {
        ("Blank / NULL", "Preserve missing value"): ("Correct", "The absence remains visible and downstream logic can route it for investigation."),
        ("Blank / NULL", "Convert to zero"): ("Control failure", "The transformation invents a verified economic value and may create a false match."),
        ("Verified 0.00", "Parse as a number"): ("Correct", "The explicit zero remains a usable business observation."),
        ("Invalid text", "Reject or quarantine"): ("Correct", "The source defect is separated from the business-anomaly population."),
        ("Valid 125.40", "Parse as a number"): ("Correct", "The value can be used after format and currency validation."),
    }
    status, explanation = outcomes.get((sample, treatment), ("Review needed", "This treatment does not fit the selected source state. Preserve meaning before calculating a metric."))
    if status == "Correct":
        st.success(explanation)
    elif status == "Control failure":
        st.error(explanation)
    else:
        control_warning(explanation)

with anomaly_tab:
    explain('anomaly')
    st.subheader("Check a reconciliation exception")
    st.caption("Start with the source checks, then enter the observed and expected days. Valid records receive a transparent rule score from 0.0 to 1.0.")
    with st.form("anomaly_form"):
        a, b = st.columns(2)
        complete = a.checkbox("Required source fields are complete", value=True)
        dates = b.checkbox("Dates parse and follow a valid chronology", value=True)
        c, d = st.columns(2)
        observed = c.number_input("Observed elapsed days", min_value=0, value=8, step=1)
        expected = d.number_input("Expected elapsed days", min_value=0, value=5, step=1)
        conflict = st.checkbox("Calculation conflicts with the documented rule", value=False)
        assessed = st.form_submit_button("Assess record", type="primary")
    if assessed:
        result = anomaly_assessment(complete, dates, observed, expected, conflict)
        if result["score"] is None:
            st.error(f"Route: {result['route']}. " + "; ".join(result["reasons"]))
        else:
            metric_row(
                [
                    ("Anomaly score", f"{result['score']:.1f}", "0.3 for elapsed-time anomaly plus 0.7 for calculation conflict"),
                    ("Priority interpretation", result["band"], "A transparent decision-table result"),
                    ("Processing route", result["route"], "Valid data proceeds to business review"),
                ]
            )
            st.markdown("**Reasoning:** " + "; ".join(result["reasons"]), text_alignment="justify")
    with st.expander("See how the score is calculated"):
        aligned_table(pd.DataFrame([
            ["Data-quality gate", "Required value missing or invalid date", "Do not score; quarantine"],
            ["Elapsed-time rule", "Observed days exceed expected days", "+0.3"],
            ["Calculation-consistency rule", "Documented calculation rule conflicts", "+0.7"],
            ["Combined", "Both business checks fire", "1.0"],
        ], columns=["Stage", "Condition", "Outcome"]))

module_footer("data_reporting", "app_pages/ai_controls.py", "Continue to Controlled Artificial Intelligence")
