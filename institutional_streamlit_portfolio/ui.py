"""Shared native Streamlit presentation helpers."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import re

from state import RUN_STAGES


def page_header(section: str, title: str, description: str, icon: str) -> None:
    st.caption(section)
    st.title(title, icon=icon)
    st.markdown(description, text_alignment="justify")
    st.caption("Interactive example · fictional operating data")


def result_metric(label: str, value, *, help: str | None = None, border: bool = True, alert: bool = False):
    """Give significant calculated outputs a consistent visual emphasis."""
    identifier = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    prefix = "control_failure" if alert or _control_cell_style(value) else "calculated_result"
    with st.container(key=f"{prefix}_{identifier}"):
        return st.metric(label, value, help=help, border=border)


def control_warning(body: str, **options):
    """Warnings retain their label while using the required red control colour."""
    options.setdefault("icon", ":material/warning:")
    return st.error(f"**Warning:** {body}", **options)


def _control_cell_style(value) -> str:
    is_failure = value is False or (type(value).__name__ == "bool_" and not value)
    if isinstance(value, str):
        is_failure = bool(re.search(r"\b(failed|blocked|blocking|warning|late|rejected|not met|below policy buffer|projected overdraft|mismatch|breach|stale|open|under investigation|awaiting verification|escalated)\b", value, re.I))
    return "background-color: #fee2e2; color: #991b1b; font-weight: 700" if is_failure else ""


def metric_row(items: list[tuple[str, str, str]]) -> None:
    columns = st.columns(len(items), gap="medium", vertical_alignment="top")
    for column, (label, value, explanation) in zip(columns, items):
        with column:
            alert = False
            if any(term in label.lower() for term in ("open exception", "under investigation", "nav impact", "difference", "mismatch", "variance")):
                match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", str(value))
                if match:
                    number = float(match.group().replace(",", ""))
                    alert = number > 0 if "variance" in label.lower() else abs(number) > 0.005
            result_metric(label, value, help=explanation, border=True, alert=alert)


def _table_options(data, options: dict) -> dict:
    """Apply alignment without changing values, column types or format rules."""
    frame = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    configured = options.get("column_config") or {}
    columns = {}
    for name in frame.columns:
        existing = configured.get(name, {})
        if existing is None:
            columns[name] = None
        else:
            config = {"label": existing} if isinstance(existing, str) else dict(existing)
            config["alignment"] = "center"
            columns[name] = config
    # Preserve index configuration and any columns addressed by position.
    options["column_config"] = {**configured, **columns}
    options.setdefault("hide_index", True)
    options.setdefault("width", "stretch")
    options.setdefault("row_height", 40)
    return options


def aligned_dataframe(data, **options):
    """Render complete cell content with rows that expand to fit the text."""
    frame = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    configured = options.get("column_config") or {}
    visible = [name for name in frame.columns if configured.get(name, {}) is not None]
    order = options.get("column_order")
    if order is not None:
        visible = [name for name in order if name in visible]
    frame = frame[visible]
    formats = {}
    labels = {}
    for name in visible:
        config = configured.get(name) or {}
        if isinstance(config, str):
            labels[name] = config
            config = {}
        elif config.get("label"):
            labels[name] = config["label"]
        number_format = (config.get("type_config") or {}).get("format")
        if pd.api.types.is_numeric_dtype(frame[name]) and not pd.api.types.is_bool_dtype(frame[name]):
            if number_format and "%" in number_format:
                formats[name] = lambda value, pattern=number_format: pattern % value
            elif pd.api.types.is_integer_dtype(frame[name]):
                formats[name] = "{:,.0f}"
            else:
                formats[name] = "{:,.2f}"
    styled = frame.style.format(formats, na_rep="—").set_properties(
        **{"text-align": "center", "white-space": "normal", "overflow-wrap": "anywhere"}
    )
    control_columns = [name for name in visible if any(
        term in str(name).lower() for term in ("status", "result", "assessment", "decision", "passed", "reconciled")
    )]
    if control_columns:
        styled = styled.map(_control_cell_style, subset=control_columns)
    exception_columns = [name for name in visible if str(name) in {
        "Break ID", "Amount under investigation (EUR)", "Impact (basis points)",
    }]
    if "Workflow status" in frame and exception_columns:
        for row_index in frame.index:
            if frame.loc[row_index, "Workflow status"] not in {"Resolved", "Accepted within policy tolerance"}:
                styled = styled.set_properties(subset=pd.IndexSlice[[row_index], exception_columns],
                    **{"background-color": "#fee2e2", "color": "#991b1b", "font-weight": "700"})
    for name in visible:
        if any(term in str(name).lower() for term in ("difference", "variance", "mismatch")) and pd.api.types.is_numeric_dtype(frame[name]):
            styled = styled.map(lambda value: "background-color: #fee2e2; color: #991b1b; font-weight: 700" if pd.notna(value) and abs(value) > 0.005 else "", subset=[name])
    if labels:
        styled = styled.relabel_index([labels.get(name, name) for name in visible], axis="columns")
    return st.table(styled, hide_index=options.get("hide_index", True), width="stretch")


def aligned_editor(data, **options):
    result = st.data_editor(data, **_table_options(data, options))
    # The canvas editor clips cells; a native table provides a fully wrapped
    # reading view without changing editing controls or their returned values.
    st.caption("Complete record content · reflects the values currently shown in the editor")
    aligned_dataframe(result, column_config=options.get("column_config"))
    return result


def aligned_table(data, **options):
    # Native column alignment also keeps compact reference tables consistent.
    return aligned_dataframe(data, **options)


def readable_chart(chart, **options):
    scale = st.session_state.get("portfolio_text_size", 18) / 18
    chart = (
        chart.configure_axis(labelFontSize=round(16 * scale), titleFontSize=round(18 * scale), labelLimit=220)
        .configure_legend(labelFontSize=round(16 * scale), titleFontSize=round(18 * scale))
        .configure_title(fontSize=round(20 * scale))
    )
    return st.altair_chart(chart, **options)


def run_stage_bar() -> None:
    stage = st.session_state.run_stage
    index = RUN_STAGES.index(stage)
    st.progress(index / (len(RUN_STAGES) - 1), text=f"Current run status: {stage} · {index} of {len(RUN_STAGES) - 1} transitions complete")
    st.caption(" → ".join(RUN_STAGES))


def definition(term: str, meaning: str) -> None:
    st.info(f"**{term}.** {meaning}", icon=":material/menu_book:")


def module_footer(module_key: str, next_page: str | None = None, next_label: str | None = None) -> None:
    if next_page and next_label:
        with st.container(border=True, horizontal=True, vertical_alignment="center", key=f"navigation_footer_{module_key}"):
            st.caption("Continue through the connected portfolio workbenches")
            if st.button(next_label, icon=":material/arrow_forward:", key=f"next_{module_key}"):
                st.switch_page(next_page)


def status_badge(status: str) -> None:
    color = {
        "Draft": "gray",
        "Calculated": "blue",
        "Reconciliation cleared": "green",
        "Preparer reviewed": "orange",
        "Checker approved": "green",
        "Publication simulated": "green",
    }.get(status, "gray")
    st.badge(status, color=color)


def money(value: float, currency: str = "EUR", decimals: int = 2) -> str:
    return f"{currency} {value:,.{decimals}f}"
