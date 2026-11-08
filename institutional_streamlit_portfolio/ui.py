"""Shared native Streamlit presentation helpers."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import re

from state import RUN_STAGES


def page_header(section: str, title: str, description: str, icon: str) -> None:
    # Each page opens on a dark chapter, matching the Overview hero.
    with st.container(key="chapter_dark_page_header"):
        st.caption(section)
        st.title(title, icon=icon)
        st.markdown(description)
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
    return "background-color: #FDE4E5; color: #9F1F26; font-weight: 700" if is_failure else ""


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
        open_rows = ~frame["Workflow status"].isin({"Resolved", "Accepted within policy tolerance"})
        highlight = "background-color: #FDE4E5; color: #9F1F26; font-weight: 700"
        # One vectorised pass instead of one Styler call per row.
        styled = styled.apply(
            lambda column: [highlight if is_open else "" for is_open in open_rows.loc[column.index]],
            subset=exception_columns,
        )
    for name in visible:
        if any(term in str(name).lower() for term in ("difference", "variance", "mismatch")) and pd.api.types.is_numeric_dtype(frame[name]):
            styled = styled.map(lambda value: "background-color: #FDE4E5; color: #9F1F26; font-weight: 700" if pd.notna(value) and abs(value) > 0.005 else "", subset=[name])
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
    # The chart definitions are fixed in code, so full schema validation on every rerun is
    # pure overhead (it dominated chart cost). Render the same spec without re-validating.
    spec = chart.to_dict(validate=False)
    return st.vega_lite_chart(spec=spec, **options)


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


def method_flow(steps: list[tuple[str, str]]) -> None:
    """Render an ordered method as connected numbered steps (static HTML, no script)."""
    from html import escape

    items = "".join(
        f'<li class="mf-step" style="--i:{index}"><span class="mf-node">{index + 1:02d}</span>'
        f'<span class="mf-text"><strong>{escape(verb)}</strong>{(" " + escape(rest)) if rest else ""}</span></li>'
        for index, (verb, rest) in enumerate(steps)
    )
    st.html(f'<ol class="mf" style="--n:{len(steps)}" aria-label="Method steps">{items}</ol>' + _METHOD_FLOW_CSS)


_METHOD_FLOW_CSS = """
<style>
.mf {
    --mf-green: #0B7A5C; --mf-bright: #12B886; --mf-blue: #2F5BFF;
    list-style: none; margin: 0; padding: 0.4rem 0 0;
    display: grid; grid-template-columns: repeat(var(--n, 6), minmax(0, 1fr)); gap: 0.5rem;
    position: relative;
}
.mf::before {
    content: ""; position: absolute; left: 4%; right: 4%; top: 1.95rem; height: 2px;
    background: #D6E8E0; border-radius: 2px;
}
.mf::after {
    content: ""; position: absolute; left: 4%; right: 4%; top: 1.95rem; height: 2px;
    background: linear-gradient(90deg, var(--mf-bright), var(--mf-green) 60%, var(--mf-blue));
    border-radius: 2px; transform-origin: left; transform: scaleX(0);
    animation: mf-draw 1600ms cubic-bezier(0.22, 1, 0.36, 1) 300ms forwards;
}
.mf-step {
    position: relative; z-index: 1;
    display: flex; flex-direction: column; align-items: center; text-align: center; gap: 0.75rem;
    padding: 0 0.2rem;
    animation: mf-rise 700ms cubic-bezier(0.22, 1, 0.36, 1) backwards;
    animation-delay: calc(250ms + var(--i) * 140ms);
}
.mf-node {
    width: 3.9rem; height: 3.9rem; border-radius: 50%;
    display: grid; place-items: center;
    font-family: "Bricolage Grotesque", "IBM Plex Sans", sans-serif;
    font-weight: 700; font-size: 1.05rem; letter-spacing: 0.02em; color: var(--mf-green);
    background: #FFFFFF;
    border: 2px solid #CBE6DA;
    box-shadow: 0 0 0 6px #EEF5F2, 0 10px 24px -12px rgb(8 23 26 / 35%);
    transition: transform 260ms cubic-bezier(0.22, 1, 0.36, 1), background-color 220ms ease,
                color 220ms ease, border-color 220ms ease, box-shadow 260ms ease;
}
.mf-step:hover .mf-node {
    transform: translateY(-4px) scale(1.06);
    background: var(--mf-green); color: #FFFFFF; border-color: var(--mf-green);
    box-shadow: 0 0 0 6px #EEF5F2, 0 16px 30px -12px rgb(11 122 92 / 55%);
}
.mf-step:last-child .mf-node { background: var(--mf-green); color: #FFFFFF; border-color: var(--mf-green); }
.mf-text {
    font-family: "IBM Plex Sans", sans-serif; font-size: 0.92rem; line-height: 1.4; color: #4A5B6E;
    overflow-wrap: normal; word-break: normal;
}
.mf-text strong {
    display: block;
    font-family: "Bricolage Grotesque", "IBM Plex Sans", sans-serif;
    font-size: clamp(0.98rem, 1.15vw, 1.15rem); font-weight: 700; letter-spacing: -0.015em; color: #0E1A2B;
    margin-bottom: 0.15rem;
}
@keyframes mf-draw { to { transform: scaleX(1); } }
@keyframes mf-rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@media (max-width: 1100px) {
    .mf { grid-template-columns: 1fr; gap: 0.6rem; }
    .mf::before, .mf::after { left: 1.95rem; right: auto; top: 1rem; bottom: 1rem; width: 2px; height: auto; }
    .mf::after { transform-origin: top; transform: scaleY(0); animation-name: mf-draw-v; }
    .mf-step { flex-direction: row; text-align: left; gap: 1rem; }
    @keyframes mf-draw-v { to { transform: scaleY(1); } }
}
@media (prefers-reduced-motion: reduce) {
    .mf::after { animation: none; transform: none; }
    .mf-step { animation: none; }
}
</style>
"""
