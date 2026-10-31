"""Chart colours aligned with the active native Streamlit theme.

Global typography, widgets, surfaces and sidebar styling are configured in
``.streamlit/config.toml``. The shared layout function adds scoped paragraph,
table and metric spacing; table-column alignment uses the native column API.
"""

PRIMARY_GREEN = "#007d5a"
DEEP_GREEN = "#153a34"
AMBER = "#c28a3d"
ALERT_RED = "#d25a4a"
MUTED_GREEN = "#6f8f86"

CHART_CATEGORICAL_COLORS = [
    PRIMARY_GREEN,
    DEEP_GREEN,
    AMBER,
    MUTED_GREEN,
    ALERT_RED,
]


def apply_layout() -> None:
    """Presentation adjustments requested for the public portfolio."""
    import streamlit as st

    text_size = int(st.session_state.get("portfolio_text_size", 18))
    text_size = max(12, min(32, text_size))
    content_width = "1100px" if st.session_state.get("portfolio_content_width") == "Reading width" else "100%"
    css = """
    <style>
    html { font-size: 18px !important; }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] {
        font-size: 1rem;
    }
    [data-testid="stMain"] h1 {
        font-size: clamp(2rem, 3.5vw, 2.5rem);
        margin-bottom: 1rem;
        border-bottom: 3px solid #007d5a;
        padding-bottom: 0.65rem;
    }
    [data-testid="stMain"] h2 {
        font-size: 1.9rem;
        background: #deede6;
        border-left: 5px solid #007d5a;
        padding: 0.65rem 0.9rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    [data-testid="stMain"] h3 {
        font-size: 1.55rem;
        margin-top: 1rem;
        margin-bottom: 0.75rem;
        background: #e4efeb;
        border-left: 4px solid #007d5a;
        padding: 0.55rem 0.75rem;
    }
    [data-testid="stMain"] h4 { font-size: 1.25rem; }
    [data-testid="stMain"] input,
    [data-testid="stMain"] textarea,
    [data-testid="stMain"] [data-testid="stTable"] {
        font-size: 1rem;
    }
    [data-testid="stMain"] [data-testid="stTable"] th,
    [data-testid="stMain"] [data-testid="stTable"] td {
        font-size: 1rem;
    }
    [data-testid="stMain"] pre,
    [data-testid="stMain"] pre code {
        font-size: 0.95rem;
        line-height: 1.6;
    }
    [data-testid="stSidebar"] [data-testid="stPageLink"] p {
        font-size: 1rem;
        line-height: 1.5;
    }
    [data-testid="stMainBlockContainer"] {
        max-width: __content_width__;
        margin-left: auto;
        margin-right: auto;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] p {
        text-align: justify;
        line-height: 1.65;
        margin-bottom: 0.8rem;
    }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] li {
        line-height: 1.6;
        margin-bottom: 0.45rem;
    }
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] th,
    [data-testid="stMain"] [data-testid="stMarkdownContainer"] td {
        text-align: center;
        vertical-align: middle;
        padding: 0.75rem 1rem;
    }
    [data-testid="stMetric"] {
        min-height: 7.5rem;
        text-align: center;
    }
    [data-testid="stMetricLabel"] {
        justify-content: center;
        width: 100%;
    }
    [data-testid="stMetricLabel"] p {
        text-align: center !important;
    }
    [data-testid="stMetricValue"] {
        font-size: clamp(1.15rem, 1.7vw, 2rem);
        font-variant-numeric: tabular-nums;
    }
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] > div,
    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] p {
        white-space: normal;
        overflow: visible;
        text-overflow: clip;
        overflow-wrap: anywhere;
        height: auto;
        max-height: none;
    }
    [data-testid="stMetric"] { height: 100%; }
    /* Only the four descriptive cards in the ten-stage NAV control chain. */
    .st-key-nav_control_chain_cards [data-testid="stMetricValue"],
    .st-key-nav_control_chain_cards [data-testid="stMetricValue"] * {
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        text-overflow: clip !important;
        overflow: visible !important;
        height: auto !important;
        max-height: none !important;
        max-width: 100% !important;
        -webkit-line-clamp: unset !important;
    }
    .st-key-nav_control_chain_cards [data-testid="stMetric"] {
        height: auto !important;
    }
    [class*="st-key-calculated_result_"] [data-testid="stMetric"] {
        background: #e0f2fe;
        border: 1px solid #60a5ce;
        border-top: 4px solid #0875a5;
        padding: 1rem;
        border-radius: 8px;
    }
    [class*="st-key-calculated_result_"] [data-testid="stMetricValue"],
    [class*="st-key-calculated_result_"] [data-testid="stMetricValue"] > div {
        color: #075985;
        font-weight: 750;
        font-size: clamp(1.45rem, 2vw, 2.2rem);
    }
    [class*="st-key-calculated_result_"] [data-testid="stMetricLabel"] p {
        color: #0c4a6e;
        font-size: 1.05rem;
        font-weight: 700;
    }
    [class*="st-key-control_failure_"] [data-testid="stMetric"] {
        background: #fee2e2;
        border: 1px solid #dc2626;
        border-top: 4px solid #b91c1c;
        padding: 1rem;
        border-radius: 8px;
    }
    [class*="st-key-control_failure_"] [data-testid="stMetricValue"],
    [class*="st-key-control_failure_"] [data-testid="stMetricLabel"] p {
        color: #991b1b;
        font-weight: 750;
    }
    [data-testid="stTable"] table {
        width: 100%;
        table-layout: fixed;
    }
    [data-testid="stTable"] th,
    [data-testid="stTable"] td {
        white-space: normal;
        overflow-wrap: anywhere;
        word-break: normal;
        text-overflow: clip;
        overflow: visible;
        vertical-align: middle !important;
        text-align: center !important;
        padding: 0.75rem;
        line-height: 1.5;
    }
    [data-testid="stTable"] p {
        text-align: center !important;
        margin-bottom: 0;
    }
    [data-testid="stMain"] [data-testid="stTable"] [data-testid="stMarkdownContainer"],
    [data-testid="stMain"] [data-testid="stTable"] [data-testid="stMarkdownContainer"] p {
        text-align: center !important;
        margin: 0;
        line-height: 1.5;
    }
    [data-testid="stTable"] th {
        font-weight: 700;
        color: #153a34;
    }
    [data-testid="stTable"] thead th {
        background-color: #cfe3d9;
    }
    [data-testid="stTable"] tbody tr:nth-child(odd) td {
        background-color: #f7faf8;
    }
    [data-testid="stTable"] tbody tr:nth-child(even) td {
        background-color: #e6f2f8;
    }
    /* Prose spacing must not shift labels away from their adjacent icons. */
    [data-testid="stMain"] button [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] a [data-testid="stMarkdownContainer"] p {
        margin: 0;
        min-height: 0;
        line-height: 1.35;
        text-align: center;
    }
    [data-testid="stButton"] button,
    [data-testid="stLinkButton"] a {
        align-items: center;
        justify-content: center;
        gap: 0.6rem;
        min-height: 2.75rem;
        padding: 0.65rem 1rem;
    }
    [data-testid="stButton"] button [data-testid="stIconMaterial"],
    [data-testid="stLinkButton"] a [data-testid="stIconMaterial"] {
        display: inline-flex;
        align-items: center;
        line-height: 1;
        flex-shrink: 0;
    }
    .st-key-nav_understand button,
    .st-key-nav_missions button,
    .st-key-nav_analysis button {
        min-height: 3.5rem;
        border-radius: 8px;
        border: 1px solid transparent;
        color: #ffffff;
        transition: filter 150ms ease, box-shadow 150ms ease;
    }
    .st-key-nav_understand button { background-color: #007d5a; }
    .st-key-nav_missions button { background-color: #245b70; }
    .st-key-nav_analysis button { background-color: #795824; }
    .st-key-nav_understand button p,
    .st-key-nav_missions button p,
    .st-key-nav_analysis button p {
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;
    }
    .st-key-navigation_lab button,
    [class*="st-key-navigation_footer_"] button {
        min-height: 3rem;
    }
    .st-key-navigation_lab button p,
    [class*="st-key-navigation_footer_"] button p {
        font-size: 1rem;
        font-weight: 650;
    }
    .st-key-start_guided_case button {
        background: #007d5a;
        color: #ffffff;
        border: 2px solid #005c43;
        min-height: 3.75rem;
        padding: 0.85rem 1.25rem;
        box-shadow: 0 3px 8px rgb(0 92 67 / 20%);
    }
    .st-key-start_guided_case button p {
        color: #ffffff;
        font-size: 1.15rem;
        font-weight: 750;
    }
    .st-key-start_guided_case button:hover {
        background: #005c43;
        color: #ffffff;
        border-color: #004b37;
    }
    .st-key-nav_understand button:hover,
    .st-key-nav_missions button:hover,
    .st-key-nav_analysis button:hover {
        filter: brightness(0.92);
        color: #ffffff;
        border-color: transparent;
    }
    [data-testid="stButton"] button:focus-visible,
    [data-testid="stLinkButton"] a:focus-visible {
        outline: 3px solid #007d5a;
        outline-offset: 3px;
    }
    .st-key-entry_understand > [data-testid="stVerticalBlock"],
    .st-key-entry_missions > [data-testid="stVerticalBlock"],
    .st-key-entry_analysis > [data-testid="stVerticalBlock"] {
        gap: 1rem;
    }
    [data-testid="stTabs"] button [data-testid="stMarkdownContainer"] p {
        font-weight: 700;
        font-size: 1rem;
        white-space: normal;
        overflow-wrap: anywhere;
        line-height: 1.4;
        margin: 0;
        text-align: center;
    }
    [data-testid="stTabs"] [role="tablist"] {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        height: auto;
        overflow: visible;
        padding: 0.3rem 0.2rem 0.8rem;
    }
    [data-testid="stTabs"] [role="tab"] {
        flex: 1 1 10rem;
        min-width: 0;
        max-width: 100%;
        height: auto;
        min-height: 3.2rem;
        padding: 0.75rem 1rem;
        white-space: normal;
        border: 1px solid #789a90;
        border-radius: 8px;
        background: #e4efeb;
        color: #17352f;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: #007d5a;
        color: #ffffff;
        border-color: #153a34;
        box-shadow: inset 0 -4px 0 #153a34;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="false"]:hover {
        background: #cfe3db;
        border-color: #007d5a;
    }
    [data-testid="stTabs"] [role="tab"]:focus-visible {
        outline: 3px solid #245b70;
        outline-offset: 2px;
    }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"],
    [data-testid="stTabs"] [data-baseweb="tab-border"] {
        display: none;
    }
    /* Apply typography to all widget types, including search and date fields. */
    [data-testid="stMain"] [data-testid="stWidgetLabel"],
    [data-testid="stMain"] [data-testid="stWidgetLabel"] p {
        font-size: 1.05rem;
        font-weight: 700;
        color: #153a34;
        line-height: 1.45;
        text-align: left;
    }
    [data-testid="stMain"] [data-testid="stWidgetLabel"] p {
        margin-bottom: 0.35rem;
    }
    [data-testid="stMain"] h1,
    [data-testid="stMain"] h2,
    [data-testid="stMain"] h3,
    [data-testid="stMain"] h4,
    [data-testid="stMain"] h5,
    [data-testid="stMain"] h6 {
        color: #153a34;
        font-weight: 700;
        line-height: 1.35;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        font-size: 1rem;
        font-weight: 700;
    }
    [data-testid="stMain"] [data-testid="stCaptionContainer"] p {
        font-size: 1rem;
        color: #466458;
    }
    /* Current React Aria controls plus compatibility with Base Web controls. */
    [data-testid="stMain"] [data-testid="stSelectbox"] div:has(> input[role="combobox"]),
    [data-testid="stMain"] [data-testid="stMultiSelect"] div:has(> input[role="combobox"]),
    [data-testid="stMain"] [data-testid="stMultiSelect"] [role="group"],
    [data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
        background-color: #cfe3d9;
        border: 2px solid #286650;
        border-radius: 8px;
        min-height: 3.2rem;
        height: auto;
        box-shadow: 0 2px 4px rgb(21 58 52 / 12%);
    }
    [data-testid="stMain"] [data-testid="stSelectbox"] input[role="combobox"],
    [data-testid="stMain"] [data-testid="stMultiSelect"] input[role="combobox"] {
        font-size: 1rem;
        font-weight: 600;
        color: #153a34;
        min-height: 3rem;
    }
    [data-testid="stMain"] [data-testid="stSelectbox"] div:has(> input[role="combobox"]):hover,
    [data-testid="stMain"] [data-testid="stMultiSelect"] [role="group"]:hover {
        background-color: #bedbcf;
        border-color: #007d5a;
    }
    [data-testid="stMain"] [data-testid="stSelectbox"] div:has(> input[role="combobox"]):focus-within,
    [data-testid="stMain"] [data-testid="stMultiSelect"] [role="group"]:focus-within {
        outline: 3px solid #86bba7;
        outline-offset: 2px;
    }
    [data-testid="stMain"] [data-testid="stSelectbox"] button,
    [data-testid="stMain"] [data-testid="stMultiSelect"] button {
        color: #153a34;
    }
    [data-testid="stSelectboxVirtualDropdown"] [role="option"] {
        font-size: 1rem;
        color: #153a34;
    }
    [data-testid="stSelectboxVirtualDropdown"] [role="option"][data-focused] {
        background: #cfe3d9;
    }
    /* Clearly distinguish selectors from surrounding display content. */
    [data-testid="stMain"] [data-testid="stSelectbox"] label p,
    [data-testid="stMain"] [data-testid="stMultiSelect"] label p {
        font-weight: 700;
        color: #153a34;
        margin-bottom: 0.25rem;
        text-align: left;
    }
    [data-testid="stMain"] [data-baseweb="select"] > div:hover {
        border-color: #007d5a;
        background-color: #cfe5da;
    }
    [data-testid="stMain"] [data-baseweb="select"]:focus-within > div {
        border-color: #007d5a;
        outline: 3px solid #98cbb8;
        outline-offset: 2px;
    }
    [data-testid="stMain"] [data-baseweb="select"] svg {
        color: #007d5a;
        min-width: 1.25rem;
        min-height: 1.25rem;
    }
    [data-baseweb="popover"] [role="listbox"] {
        border: 1px solid #477c6b;
        border-radius: 8px;
        background: #ffffff;
        color: #153a34;
    }
    [data-baseweb="popover"] [role="option"] {
        min-height: 2.75rem;
        padding-top: 0.65rem;
        padding-bottom: 0.65rem;
        white-space: normal;
        overflow-wrap: anywhere;
    }
    [data-baseweb="popover"] [role="option"]:hover,
    [data-baseweb="popover"] [role="option"][aria-selected="true"] {
        background: #deede6;
        color: #153a34;
    }
    [data-testid="stMain"] [data-testid="stExpander"] details {
        border: 1px solid #789a90;
        border-radius: 8px;
    }
    [data-testid="stMain"] [data-testid="stExpander"] summary {
        background: #e4efeb;
        min-height: 3rem;
        padding: 0.75rem 1rem;
        border-radius: 7px;
        color: #153a34;
        align-items: center;
    }
    [data-testid="stMain"] [data-testid="stExpander"] summary:hover {
        background: #cfe5da;
    }
    [data-testid="stMain"] [data-testid="stExpander"] summary p {
        margin: 0;
        font-weight: 650;
        text-align: left;
        line-height: 1.4;
    }
    [data-testid="stMain"] [data-testid="stExpander"] summary:focus-visible {
        outline: 3px solid #007d5a;
        outline-offset: 2px;
    }
    .st-key-book_index [data-testid="stPageLink"] a {
        border: none;
        background: transparent;
        padding: 0.45rem 0;
        color: #007d5a;
    }
    .st-key-book_index [data-testid="stPageLink"] p {
        text-align: left !important;
        font-size: 1.15rem;
        font-weight: 650;
    }
    .st-key-book_index [class*="st-key-index_entry_"] {
        padding: 0.35rem 0;
    }
    .st-key-book_index [class*="st-key-index_entry_"] [data-testid="stMarkdownContainer"] p {
        text-align: left;
        margin-bottom: 0.3rem;
    }
    .st-key-book_index [data-testid="stCaptionContainer"] {
        margin-left: 1.8rem;
        margin-bottom: 1rem;
        max-width: 75ch;
    }
    .st-key-book_index h3 {
        font-size: 1.4rem;
        font-weight: 750;
        color: #153a34;
        background: transparent;
        border-left: none;
        border-bottom: 2px solid #007d5a;
        padding: 0 0 0.55rem;
        margin-top: 1.4rem;
    }
    .st-key-book_index [data-testid="stCaptionContainer"] p {
        text-align: left;
        line-height: 1.65;
        color: #294a3d;
    }
    .st-key-book_index [data-testid="stPageLink"] a:hover {
        color: #153a34;
        text-decoration: underline;
    }
    .st-key-navigation_diagram [data-testid="stMarkdownContainer"] p {
        text-align: center;
        margin: 0;
    }
    .st-key-navigation_diagram [data-testid="stPageLink"] a {
        width: 100%;
        white-space: normal;
        background: #deede6;
        color: #153a34;
        padding: 0.8rem;
        border-radius: 6px;
    }
    .st-key-navigation_diagram [data-testid="stPageLink"] p {
        white-space: normal;
        overflow-wrap: anywhere;
        font-weight: 650;
    }
    @media (max-width: 640px) {
        [data-testid="stMainBlockContainer"] { padding-top: 1rem; }
        [data-testid="stMain"] [data-testid="stMarkdownContainer"] p {
            text-align: left;
        }
    }
    </style>
    """
    st.html(css.replace("font-size: 18px", f"font-size: {text_size}px", 1).replace("__content_width__", content_width))
