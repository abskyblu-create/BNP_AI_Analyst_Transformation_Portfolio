"""Design tokens and presentation layer for the public portfolio.

Palette, fonts and base widget colours live in ``.streamlit/config.toml``.
This module adds the layout and interaction layer: chapter sections, card
surfaces, button and tab feedback, result states and reduced-motion support.
Chart colours below are shared with Altair charts so data and UI agree.

Colour roles
- Ink / Ledger White: text and surfaces.
- Ledger Green: the theme and primary interactive accent.
- Settlement Blue: supporting accent (links, calculated results, highlights).
- Matched / Break / Pending: result status only, never decoration.
"""

INK = "#0E1A2B"
LEDGER_WHITE = "#F7F9FC"
SLATE = "#5B6B82"
LEDGER_GREEN = "#0B7A5C"
SETTLEMENT_BLUE = "#2F5BFF"
MATCHED = "#0FA47A"
BREAK = "#E5484D"
PENDING = "#F5A524"

# Names kept for existing chart code; values follow the new palette roles.
PRIMARY_GREEN = MATCHED
DEEP_GREEN = INK
AMBER = PENDING
ALERT_RED = BREAK
MUTED_GREEN = SLATE

CHART_CATEGORICAL_COLORS = [LEDGER_GREEN, SETTLEMENT_BLUE, PENDING, "#7FD8B6", BREAK, SLATE, INK]

FAILURE_CELL_STYLE = "background-color: #FDE4E5; color: #9F1F26; font-weight: 700"


_CSS = """
<style>
:root {
    --ink: #0E1A2B;
    --ink-2: #17263B;
    --ledger: #F7F9FC;
    --surface: #FFFFFF;
    --tint: #EDF4F1;
    --line: #D6E2DD;
    --line-strong: #B5C9C1;
    --slate: #5B6B82;
    --blue: #0B7A5C;
    --blue-deep: #08624A;
    --blue-soft: #7FD8B6;
    --green-bright: #12B886;
    --sky: #2F5BFF;
    --sky-deep: #2448D8;
    --matched: #0FA47A;
    --break: #E5484D;
    --pending: #F5A524;
    --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
    --shadow-1: 0 1px 2px rgb(14 26 43 / 4%), 0 2px 8px rgb(14 26 43 / 4%);
    --shadow-2: 0 2px 4px rgb(14 26 43 / 5%), 0 12px 32px rgb(14 26 43 / 9%);
}
html { font-size: 18px !important; }

/* ---------- Page frame ---------- */
[data-testid="stMainBlockContainer"] {
    max-width: __content_width__;
    margin-left: auto;
    margin-right: auto;
    padding-top: 4.5rem;
    padding-bottom: 3rem;
}
[data-testid="stMain"] [data-testid="stMarkdownContainer"] { font-size: 1rem; }
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p {
    text-align: left;
    line-height: 1.65;
    margin-bottom: 0.8rem;
}
[data-testid="stMain"] [data-testid="stMarkdownContainer"] li {
    line-height: 1.6;
    margin-bottom: 0.45rem;
}
[data-testid="stMain"] [data-testid="stCaptionContainer"],
[data-testid="stMain"] [data-testid="stCaptionContainer"] * { opacity: 1 !important; }
[data-testid="stMain"] [data-testid="stCaptionContainer"] p {
    font-size: 0.95rem;
    color: var(--slate);
    letter-spacing: 0.01em;
}

/* ---------- Type ---------- */
[data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3,
[data-testid="stMain"] h4, [data-testid="stMain"] h5, [data-testid="stMain"] h6 {
    color: var(--ink);
    text-wrap: balance;
    hyphens: manual;
}
[data-testid="stMain"] :is(h1, h2, h3, h4, h5, h6),
[data-testid="stMain"] :is(h1, h2, h3, h4, h5, h6) * {
    overflow-wrap: normal !important;
    word-break: normal !important;
}
[data-testid="stMain"] h1 {
    font-size: clamp(2.2rem, 4.4vw, 3.6rem);
    line-height: 1.02;
    letter-spacing: -0.035em;
    margin-bottom: 1rem;
}
[data-testid="stMain"] h2 {
    font-size: clamp(1.6rem, 2.6vw, 2.1rem);
    line-height: 1.12;
    letter-spacing: -0.025em;
    margin-top: 1.8rem;
    margin-bottom: 0.9rem;
}
[data-testid="stMain"] h3 {
    font-size: clamp(1.15rem, 1.55vw, 1.4rem);
    line-height: 1.2;
    letter-spacing: -0.015em;
    margin-top: 0.8rem;
    margin-bottom: 0.6rem;
}
[data-testid="stMain"] h4 { font-size: 1.2rem; letter-spacing: -0.01em; }
[data-testid="stMain"] input,
[data-testid="stMain"] textarea,
[data-testid="stMain"] [data-testid="stTable"] { font-size: 1rem; }
[data-testid="stMain"] pre,
[data-testid="stMain"] pre code { font-size: 0.95rem; line-height: 1.6; }

/* ---------- Chapters: keyed containers become full sections ---------- */
[class*="st-key-chapter_"] {
    border-radius: 28px;
    padding: clamp(1.4rem, 3.2vw, 3rem);
    margin: 0.4rem 0 1.2rem;
}
[class*="st-key-chapter_tint"] { background: var(--tint); }
[class*="st-key-chapter_dark"], .st-key-chapter_hero {
    /* Ink chapter with a faint ledger grid — the squared paper of fund accounting. */
    background-color: #0B201C;
    background-image:
        radial-gradient(120% 90% at 100% 0%, rgb(18 184 134 / 26%) 0%, transparent 55%),
        radial-gradient(70% 90% at 0% 100%, rgb(47 91 255 / 14%) 0%, transparent 60%),
        linear-gradient(rgb(255 255 255 / 3.5%) 1px, transparent 1px),
        linear-gradient(90deg, rgb(255 255 255 / 3.5%) 1px, transparent 1px),
        linear-gradient(180deg, #0D2622 0%, #08171A 100%);
    background-size: auto, auto, 32px 32px, 32px 32px, auto;
    color: #E8EEF8;
    box-shadow: 0 24px 60px rgb(8 23 26 / 26%);
}
[class*="st-key-chapter_dark"] :is(h1, h2, h3, h4, p, li, span, label),
.st-key-chapter_hero :is(h1, h2, h3, h4, p, li, span, label) { color: #E8EEF8; }
[class*="st-key-chapter_dark"] [data-testid="stCaptionContainer"] p,
.st-key-chapter_hero [data-testid="stCaptionContainer"] p { color: #A9C7BD; }
[class*="st-key-chapter_dark"] strong,
.st-key-chapter_hero strong { color: #FFFFFF; }
.st-key-chapter_hero [data-testid="stCaptionContainer"] p {
    letter-spacing: 0.14em;
    font-weight: 600;
    font-size: 0.8rem;
}
.st-key-chapter_hero h1,
[class*="st-key-chapter_dark"] h1 {
    color: #FFFFFF;
    font-size: clamp(2.1rem, 3.3vw, 3.25rem);
}
[class*="st-key-chapter_dark"] [data-testid="stIconMaterial"] { color: var(--blue-soft); }
.st-key-chapter_hero { padding-top: clamp(1.6rem, 3.6vw, 3.4rem); }

/* ---------- Card surfaces ---------- */
/* Entry cards lead somewhere, so they are raised and react to the pointer. */
[class*="st-key-entry_"] {
    background: var(--surface);
    border-radius: 18px;
    box-shadow: var(--shadow-1);
    transition: transform 260ms var(--ease-out), box-shadow 260ms var(--ease-out), border-color 200ms ease;
}
[class*="st-key-entry_"]:hover,
[class*="st-key-entry_"]:focus-within {
    transform: translateY(-4px);
    box-shadow: var(--shadow-2);
    border-color: var(--blue-soft);
}

/* ---------- Buttons and links ---------- */
[data-testid="stMain"] button [data-testid="stMarkdownContainer"] p,
[data-testid="stMain"] a [data-testid="stMarkdownContainer"] p {
    margin: 0;
    min-height: 0;
    line-height: 1.35;
    text-align: center;
    max-width: none;
}
[data-testid="stButton"] button,
[data-testid="stLinkButton"] a,
[data-testid="stFormSubmitButton"] button {
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    min-height: 2.75rem;
    padding: 0.65rem 1.2rem;
    font-weight: 600;
    transition: transform 180ms var(--ease-out), box-shadow 180ms var(--ease-out),
                background-color 180ms ease, border-color 180ms ease, color 180ms ease;
}
[data-testid="stButton"] button:hover,
[data-testid="stLinkButton"] a:hover,
[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgb(11 122 92 / 18%);
}
[data-testid="stButton"] button:active,
[data-testid="stLinkButton"] a:active,
[data-testid="stFormSubmitButton"] button:active {
    transform: translateY(0) scale(0.98);
    box-shadow: none;
}
[data-testid="stButton"] button [data-testid="stIconMaterial"],
[data-testid="stLinkButton"] a [data-testid="stIconMaterial"] {
    display: inline-flex;
    align-items: center;
    line-height: 1;
    flex-shrink: 0;
    transition: transform 220ms var(--ease-out);
}
[data-testid="stButton"] button:hover [data-testid="stIconMaterial"] { transform: translateX(3px); }
[data-testid="stMain"] button:focus-visible,
[data-testid="stMain"] a:focus-visible,
[data-testid="stSidebar"] button:focus-visible,
[data-testid="stSidebar"] a:focus-visible,
[data-testid="stMain"] [role="tab"]:focus-visible,
[data-testid="stMain"] summary:focus-visible {
    outline: 3px solid var(--blue) !important;
    outline-offset: 3px;
}
[data-testid="stSidebar"] button:focus-visible,
[data-testid="stSidebar"] a:focus-visible { outline-color: var(--blue-soft) !important; }

/* Overview entry buttons: one primary, two calm secondary. */
.st-key-nav_understand button,
.st-key-nav_missions button,
.st-key-nav_analysis button { min-height: 3.4rem; }
.st-key-nav_understand button p,
.st-key-nav_missions button p,
.st-key-nav_analysis button p { font-size: 1.02rem; font-weight: 650; }
.st-key-nav_missions button,
.st-key-nav_analysis button {
    background: #0B201C;
    border-color: #0B201C;
    color: #FFFFFF;
}
.st-key-nav_missions button p,
.st-key-nav_analysis button p { color: #FFFFFF; }
.st-key-nav_missions button:hover,
.st-key-nav_analysis button:hover {
    background: #13302A;
    border-color: #13302A;
    color: #FFFFFF;
    box-shadow: 0 6px 18px rgb(11 32 28 / 30%);
}
.st-key-navigation_lab button,
[class*="st-key-navigation_footer_"] button { min-height: 3rem; }
.st-key-navigation_lab button p,
[class*="st-key-navigation_footer_"] button p { font-size: 1rem; font-weight: 650; }
.st-key-start_guided_case button {
    background: var(--blue);
    color: #FFFFFF;
    border: none;
    min-height: 3.75rem;
    padding: 0.85rem 1.6rem;
    box-shadow: 0 10px 28px rgb(11 122 92 / 30%);
}
.st-key-start_guided_case button p { color: #FFFFFF; font-size: 1.15rem; font-weight: 700; }
.st-key-start_guided_case button:hover {
    background: var(--blue-deep);
    color: #FFFFFF;
    box-shadow: 0 14px 34px rgb(11 122 92 / 38%);
}
.st-key-entry_understand > [data-testid="stVerticalBlock"],
.st-key-entry_missions > [data-testid="stVerticalBlock"],
.st-key-entry_analysis > [data-testid="stVerticalBlock"] { gap: 1rem; }

/* Light link buttons inside dark chapters. */
[class*="st-key-chapter_dark"] [data-testid="stLinkButton"] a {
    background: rgb(255 255 255 / 6%);
    border-color: rgb(255 255 255 / 22%);
    color: #FFFFFF;
}
[class*="st-key-chapter_dark"] [data-testid="stLinkButton"] a:hover {
    background: rgb(255 255 255 / 12%);
    border-color: var(--blue-soft);
}

/* ---------- Tabs: segmented, ink selection ---------- */
[data-testid="stTabs"] [role="tablist"] {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    height: auto;
    overflow: visible;
    padding: 0.35rem;
    background: var(--tint);
    border-radius: 18px;
    margin-bottom: 0.8rem;
}
[data-testid="stTabs"] [role="tab"] {
    flex: 1 1 10rem;
    min-width: 0;
    max-width: 100%;
    height: auto;
    min-height: 3rem;
    padding: 0.7rem 1rem;
    white-space: normal;
    border: 1px solid transparent;
    border-radius: 14px;
    background: transparent;
    color: var(--ink);
    transition: background-color 220ms var(--ease-out), color 220ms ease, box-shadow 220ms ease;
}
[data-testid="stTabs"] button [data-testid="stMarkdownContainer"] p {
    font-weight: 650;
    font-size: 0.98rem;
    white-space: normal;
    overflow-wrap: anywhere;
    line-height: 1.35;
    margin: 0;
    text-align: center;
}
[data-testid="stTabs"] [role="tab"][aria-selected="false"]:hover {
    background: var(--surface);
    box-shadow: var(--shadow-1);
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: var(--blue);
    color: #FFFFFF;
    box-shadow: 0 6px 16px rgb(11 122 92 / 28%);
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p { color: #FFFFFF; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }
[data-testid="stTabs"] [role="tabpanel"] { animation: panel-in 320ms var(--ease-out); }

/* ---------- Inputs and selects ---------- */
[data-testid="stMain"] [data-testid="stWidgetLabel"],
[data-testid="stMain"] [data-testid="stWidgetLabel"] p {
    font-size: 1rem;
    font-weight: 650;
    color: var(--ink);
    line-height: 1.45;
    text-align: left;
}
[data-testid="stMain"] [data-testid="stWidgetLabel"] p { margin-bottom: 0.3rem; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { font-size: 0.95rem; font-weight: 650; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    border-radius: 10px;
    transition: background-color 180ms ease, transform 180ms var(--ease-out);
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
    background: rgb(95 211 168 / 12%);
    transform: translateX(2px);
}
[data-testid="stSidebar"] [data-testid="stPageLink"] p { font-size: 1rem; line-height: 1.5; }
[data-testid="stMain"] [data-testid="stSelectbox"] div:has(> input[role="combobox"]),
[data-testid="stMain"] [data-testid="stMultiSelect"] div:has(> input[role="combobox"]),
[data-testid="stMain"] [data-testid="stMultiSelect"] [role="group"],
[data-testid="stMain"] [data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
    background-color: var(--surface);
    border: 1.5px solid var(--line-strong);
    border-radius: 12px;
    min-height: 3.1rem;
    height: auto;
    box-shadow: var(--shadow-1);
    transition: border-color 180ms ease, box-shadow 180ms ease;
}
[data-testid="stMain"] [data-testid="stSelectbox"] input[role="combobox"],
[data-testid="stMain"] [data-testid="stMultiSelect"] input[role="combobox"] {
    font-size: 1rem;
    font-weight: 500;
    color: var(--ink);
    min-height: 2.9rem;
}
[data-testid="stMain"] [data-testid="stSelectbox"] div:has(> input[role="combobox"]):hover,
[data-testid="stMain"] [data-testid="stMultiSelect"] [role="group"]:hover,
[data-testid="stMain"] [data-baseweb="select"] > div:hover { border-color: var(--blue); }
[data-testid="stMain"] [data-testid="stSelectbox"] div:has(> input[role="combobox"]):focus-within,
[data-testid="stMain"] [data-testid="stMultiSelect"] [role="group"]:focus-within,
[data-testid="stMain"] [data-baseweb="select"]:focus-within > div {
    border-color: var(--blue);
    box-shadow: 0 0 0 4px rgb(11 122 92 / 16%);
}
[data-testid="stMain"] [data-testid="stSelectbox"] button,
[data-testid="stMain"] [data-testid="stMultiSelect"] button,
[data-testid="stMain"] [data-baseweb="select"] svg { color: var(--blue-deep); }
[data-testid="stSelectboxVirtualDropdown"] [role="option"] { font-size: 1rem; color: var(--ink); }
[data-testid="stSelectboxVirtualDropdown"] [role="option"][data-focused] { background: #E3F5EE; }
[data-testid="stMain"] [data-testid="stSelectbox"] label p,
[data-testid="stMain"] [data-testid="stMultiSelect"] label p {
    font-weight: 650;
    color: var(--ink);
    margin-bottom: 0.25rem;
    text-align: left;
}
[data-baseweb="popover"] [role="listbox"] {
    border: 1px solid var(--line);
    border-radius: 14px;
    background: var(--surface);
    color: var(--ink);
    box-shadow: var(--shadow-2);
}
[data-baseweb="popover"] [role="option"] {
    min-height: 2.75rem;
    padding-top: 0.65rem;
    padding-bottom: 0.65rem;
    white-space: normal;
    overflow-wrap: anywhere;
}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [role="option"][aria-selected="true"] { background: #E3F5EE; color: var(--ink); }

/* ---------- Expanders ---------- */
[data-testid="stMain"] [data-testid="stExpander"] details {
    border: 1px solid var(--line);
    border-radius: 16px;
    background: var(--surface);
    box-shadow: var(--shadow-1);
    overflow: hidden;
}
[data-testid="stMain"] [data-testid="stExpander"] summary {
    min-height: 3rem;
    padding: 0.8rem 1.1rem;
    color: var(--ink);
    align-items: center;
    transition: background-color 180ms ease;
}
[data-testid="stMain"] [data-testid="stExpander"] summary:hover { background: var(--tint); }
[data-testid="stMain"] [data-testid="stExpander"] summary p {
    margin: 0;
    font-weight: 650;
    text-align: left;
    line-height: 1.4;
}
[data-testid="stMain"] [data-testid="stExpander"] details[open] > div { animation: panel-in 300ms var(--ease-out); }

/* ---------- Tables ---------- */
[data-testid="stMain"] [data-testid="stMarkdownContainer"] th,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] td {
    text-align: center;
    vertical-align: middle;
    padding: 0.75rem 1rem;
}
[data-testid="stTable"] table {
    width: 100%;
    table-layout: fixed;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 14px;
    overflow: hidden;
    font-variant-numeric: tabular-nums;
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
    font-size: 1rem;
    border-color: var(--line);
}
[data-testid="stTable"] p { text-align: center !important; margin-bottom: 0; }
[data-testid="stMain"] [data-testid="stTable"] [data-testid="stMarkdownContainer"],
[data-testid="stMain"] [data-testid="stTable"] [data-testid="stMarkdownContainer"] p {
    text-align: center !important;
    margin: 0;
    line-height: 1.5;
}
[data-testid="stTable"] th { font-weight: 650; color: var(--ink); }
[data-testid="stTable"] thead th { background-color: #E3EFEA; }
[data-testid="stTable"] tbody tr:nth-child(odd) td { background-color: var(--surface); }
[data-testid="stTable"] tbody tr:nth-child(even) td { background-color: #F4F8F6; }

/* ---------- Metrics ---------- */
[data-testid="stMetric"] { min-height: 7.5rem; height: 100%; text-align: center; }
[data-testid="stMetricLabel"] { justify-content: center; width: 100%; }
[data-testid="stMetricLabel"] p { text-align: center !important; color: var(--slate); }
[data-testid="stMetricValue"] {
    font-size: clamp(1.15rem, 1.7vw, 2rem);
    font-family: "Bricolage Grotesque", "IBM Plex Sans", sans-serif;
    font-weight: 700;
    letter-spacing: -0.02em;
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
.st-key-nav_control_chain_cards [data-testid="stMetric"] { height: auto !important; }

/* Calculated results arrive with a short rise — motion that answers an action. */
[class*="st-key-calculated_result_"] [data-testid="stMetric"] {
    background: linear-gradient(180deg, #EEF2FF 0%, #FFFFFF 100%);
    border: 1px solid #C9D5FF;
    border-top: 4px solid var(--sky);
    padding: 1rem;
    border-radius: 16px;
    animation: result-in 520ms var(--ease-out) both;
}
[class*="st-key-calculated_result_"] [data-testid="stMetricValue"],
[class*="st-key-calculated_result_"] [data-testid="stMetricValue"] > div {
    color: var(--sky-deep);
    font-weight: 800;
    font-size: clamp(1.45rem, 2vw, 2.2rem);
}
[class*="st-key-calculated_result_"] [data-testid="stMetricLabel"] p {
    color: var(--ink);
    font-size: 1.02rem;
    font-weight: 650;
}
[class*="st-key-control_failure_"] [data-testid="stMetric"] {
    background: #FDE4E5;
    border: 1px solid #F3A6A9;
    border-top: 4px solid var(--break);
    padding: 1rem;
    border-radius: 16px;
    animation: break-flash 900ms var(--ease-out) 1 both;
}
[class*="st-key-control_failure_"] [data-testid="stMetricValue"],
[class*="st-key-control_failure_"] [data-testid="stMetricLabel"] p {
    color: #9F1F26;
    font-weight: 750;
}

/* ---------- Contents page ---------- */
/* Section jump links become a row of pills. */
.st-key-index_jump p { line-height: 2.6 !important; max-width: none !important; color: transparent; font-size: 0.95rem; }
.st-key-index_jump p strong { color: var(--ink); margin-right: 0.4rem; }
.st-key-index_jump a {
    display: inline-block;
    padding: 0.35rem 0.95rem;
    margin: 0 0.15rem;
    border-radius: 999px;
    background: var(--surface);
    border: 1px solid var(--line);
    color: var(--ink) !important;
    font-weight: 600;
    line-height: 1.5;
    text-decoration: none;
    box-shadow: var(--shadow-1);
    transition: background-color 180ms ease, color 180ms ease, border-color 180ms ease, transform 200ms var(--ease-out);
}
.st-key-index_jump a:hover { background: var(--blue); border-color: var(--blue); color: #FFFFFF !important; transform: translateY(-1px); }

/* Each chapter is a card; entries are rows that light up on approach. */
.st-key-book_index { gap: 1.1rem; }
[class*="st-key-index_chapter_"] {
    background: var(--surface);
    border: 1px solid #E1E7F0;
    border-radius: 22px;
    padding: 1.4rem 1.6rem 0.9rem;
    box-shadow: var(--shadow-1);
    gap: 0.2rem;
    scroll-margin-top: 4rem;
}
.st-key-book_index h3 {
    font-size: clamp(1.3rem, 2vw, 1.6rem) !important;
    letter-spacing: -0.02em;
    color: var(--ink);
    padding: 0 0 0.9rem !important;
    margin: 0 0 0.3rem !important;
    border-bottom: 1px solid var(--line);
}
.st-key-book_index [class*="st-key-index_entry_"] {
    padding: 0.55rem 0.9rem;
    margin: 0 -0.9rem;
    border-radius: 14px;
    border-bottom: 1px solid #EEF2F8;
    transition: background-color 200ms ease;
}
.st-key-book_index [class*="st-key-index_entry_"]:last-child { border-bottom: none; }
.st-key-book_index [class*="st-key-index_entry_"]:hover { background: #EEF8F4; }
.st-key-book_index [data-testid="stPageLink"] a {
    border: none;
    background: transparent;
    padding: 0.3rem 0;
    color: var(--ink);
    transition: color 160ms ease, transform 220ms var(--ease-out);
}
.st-key-book_index [class*="st-key-index_entry_"]:hover [data-testid="stPageLink"] a { color: var(--blue-deep); transform: translateX(4px); }
.st-key-book_index [data-testid="stPageLink"] a:not([aria-disabled="true"]) * { color: inherit !important; }
.st-key-book_index [data-testid="stPageLink"] a,
.st-key-book_index [data-testid="stPageLink"] a * { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }
.st-key-book_index [data-testid="stPageLink"] p {
    text-align: left !important;
    font-family: "Bricolage Grotesque", "IBM Plex Sans", sans-serif;
    font-size: 1.12rem;
    font-weight: 700;
    letter-spacing: -0.01em;
}
.st-key-book_index [class*="st-key-index_entry_"] [data-testid="stMarkdownContainer"] p {
    text-align: left;
    margin: 0;
    color: var(--slate);
    line-height: 1.55;
}

/* Navigation diagram: start node, three lanes, end node. */
.st-key-navigation_diagram { gap: 0.6rem; }
.st-key-navigation_diagram [data-testid="stMarkdownContainer"] p { text-align: center; margin: 0; max-width: none; }
.st-key-navigation_diagram [data-testid="stMarkdownContainer"] [data-testid="stIconMaterial"] {
    color: var(--blue) !important;
    font-size: 1.35rem !important;
    line-height: 1 !important;
    width: auto !important;
    height: auto !important;
}
.st-key-navigation_diagram [data-testid="stMarkdownContainer"] p:has([data-testid="stIconMaterial"]) { line-height: 1.6 !important; min-height: 1.6rem; }
[class*="st-key-diagram_lane_"] > [data-testid="stElementContainer"] { margin-top: 0 !important; }
.st-key-navigation_diagram [data-testid="stElementContainer"]:not(:has(a)):not(:has(strong)):not(:has([data-testid="stCaptionContainer"])) {
    min-height: 1.9rem !important;
    height: auto !important;
    overflow: visible !important;
    display: flex;
    align-items: center;
    justify-content: center;
}
.st-key-diagram_start [data-testid="stPageLink"] a,
.st-key-diagram_end [data-testid="stPageLink"] a {
    justify-content: center;
    background: #0B201C;
    border: 1px solid #0B201C;
    border-radius: 16px;
    padding: 0.95rem 1.2rem;
    box-shadow: 0 10px 28px rgb(14 26 43 / 22%);
    transition: transform 220ms var(--ease-out), box-shadow 220ms var(--ease-out);
}
.st-key-diagram_start [data-testid="stPageLink"] p,
.st-key-diagram_end [data-testid="stPageLink"] p,
.st-key-diagram_start [data-testid="stIconMaterial"],
.st-key-diagram_end [data-testid="stIconMaterial"] { color: #FFFFFF !important; font-weight: 650; }
.st-key-diagram_start [data-testid="stPageLink"] a:hover,
.st-key-diagram_end [data-testid="stPageLink"] a:hover { transform: translateY(-2px); box-shadow: 0 16px 36px rgb(14 26 43 / 30%); }
[class*="st-key-diagram_lane_"] {
    background: var(--tint);
    border-radius: 22px;
    padding: 1.1rem 1rem 0.8rem;
    gap: 0.35rem;
}
[class*="st-key-diagram_lane_"] > div:first-child p strong {
    display: block;
    font-family: "Bricolage Grotesque", "IBM Plex Sans", sans-serif;
    font-size: 1.05rem;
    letter-spacing: -0.01em;
    color: var(--ink);
    padding-bottom: 0.5rem;
}
[class*="st-key-diagram_lane_"] [data-testid="stPageLink"] a {
    width: 100%;
    justify-content: flex-start;
    background: var(--surface);
    border: 1px solid #DDE4EF;
    border-radius: 14px;
    padding: 0.8rem 1rem;
    box-shadow: var(--shadow-1);
    transition: border-color 180ms ease, box-shadow 220ms var(--ease-out), transform 220ms var(--ease-out);
}
[class*="st-key-diagram_lane_"] [data-testid="stPageLink"] p {
    white-space: normal;
    overflow-wrap: normal;
    text-align: left !important;
    font-weight: 650;
    color: var(--ink);
}
[class*="st-key-diagram_lane_"] [data-testid="stPageLink"] [data-testid="stIconMaterial"] { color: var(--blue); }
[class*="st-key-diagram_lane_"] [data-testid="stPageLink"] a:hover {
    border-color: var(--blue);
    box-shadow: 0 10px 24px rgb(11 122 92 / 16%);
    transform: translateY(-2px);
}
[class*="st-key-diagram_lane_"] [data-testid="stCaptionContainer"] p { text-align: center; color: var(--slate); padding-top: 0.4rem; }

/* ---------- Footer ---------- */
.st-key-site_footer {
    border-top: 1px solid var(--line);
    margin-top: 2.5rem;
    padding-top: 1.1rem;
}
.st-key-site_footer [data-testid="stCaptionContainer"] p { font-size: 0.88rem; margin: 0 0 0.3rem; }

/* ---------- Hero: full-bleed photograph behind the headline ---------- */
.st-key-chapter_hero {
    /* The photograph is painted here too, so it is visible instantly, before the 3D layer mounts. */
    background:
        linear-gradient(90deg, rgb(8 23 26 / 74%) 0%, rgb(8 23 26 / 50%) 26%, rgb(8 23 26 / 12%) 44%, rgb(8 23 26 / 0%) 56%),
        linear-gradient(180deg, rgb(8 23 26 / 0%) 70%, rgb(9 26 27 / 100%) 98%),
        url("app/static/portfolio_hero.webp") center / cover no-repeat,
        #0D2622 !important;
    position: relative;
    overflow: hidden;
    min-height: 580px;
    justify-content: center;
    padding: clamp(2rem, 4.5vw, 4.2rem) !important;
    box-shadow: 0 30px 60px -20px rgb(8 23 26 / 45%);
}
.st-key-hero_backdrop {
    position: absolute !important;
    inset: 0;
    z-index: 0;
    margin: 0 !important;
}
.st-key-chapter_hero [data-testid="stHorizontalBlock"] {
    position: relative;
    z-index: 1;
    pointer-events: none;
}
.st-key-chapter_hero [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child { pointer-events: auto; }
.st-key-chapter_hero h1 { text-shadow: 0 2px 24px rgb(5 10 20 / 60%), 0 1px 3px rgb(5 10 20 / 45%); }
.st-key-chapter_hero [data-testid="stMarkdownContainer"] p { font-size: 1rem; color: #D5DEEC; text-shadow: 0 1px 10px rgb(5 10 20 / 75%), 0 1px 2px rgb(5 10 20 / 55%); }

/* ---------- Overview: premium light sections ---------- */
/* Contribution: a statement band. */
.st-key-contribution_card {
    position: relative;
    overflow: hidden;
    border: none !important;
    border-radius: 26px !important;
    padding: clamp(1.6rem, 3.4vw, 2.8rem) clamp(1.6rem, 3.4vw, 3rem) !important;
    background:
        radial-gradient(60% 120% at 100% 0%, rgb(18 184 134 / 12%) 0%, transparent 60%),
        linear-gradient(135deg, #FFFFFF 0%, #F4FAF7 100%);
    box-shadow: 0 18px 50px -24px rgb(8 23 26 / 28%);
    margin-top: 0.6rem;
    gap: 0.9rem;
}
.st-key-contribution_card::before {
    content: "";
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 6px;
    background: linear-gradient(180deg, var(--green-bright), var(--blue-deep));
}
.st-key-contribution_card h3 {
    font-size: 1.02rem !important;
    color: var(--blue-deep) !important;
    letter-spacing: 0.01em;
    margin: 0 !important;
}
.st-key-contribution_card [data-testid="stMarkdownContainer"] p {
    font-family: "Bricolage Grotesque", "IBM Plex Sans", sans-serif;
    font-size: clamp(1.35rem, 2.3vw, 2rem) !important;
    font-weight: 700;
    line-height: 1.22 !important;
    letter-spacing: -0.022em;
    color: var(--ink);
    margin: 0 !important;
}
.st-key-contribution_card [data-testid="stHorizontalBlock"] { gap: 0.6rem !important; flex-wrap: wrap; }
.stMarkdownBadge {
    font-family: "IBM Plex Sans", sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 0 !important;
    padding: 0.42rem 0.95rem !important;
    border-radius: 999px !important;
    background: #FFFFFF !important;
    color: var(--blue-deep) !important;
    border: 1px solid #BFE3D4;
    box-shadow: 0 2px 6px rgb(8 23 26 / 6%);
}

/* Section headings on the Overview read as chapter titles. */
.st-key-section_explore > [data-testid="stElementContainer"] h3,
.st-key-chapter_tint_capability > [data-testid="stElementContainer"] h3 {
    font-size: clamp(1.7rem, 2.8vw, 2.4rem) !important;
    letter-spacing: -0.03em;
    margin: 0.4rem 0 0.2rem !important;
}
.st-key-section_explore { margin-top: 1.6rem; gap: 1rem; }

/* Contents link: a slim bar that lifts on approach. */
.st-key-contents_card {
    background: var(--surface);
    border-radius: 18px;
    padding: 0.9rem 1.2rem !important;
    box-shadow: var(--shadow-1);
    transition: transform 260ms var(--ease-out), box-shadow 260ms var(--ease-out), border-color 200ms ease;
}
.st-key-contents_card:hover { transform: translateY(-2px); box-shadow: var(--shadow-2); border-color: var(--blue-soft); }
.st-key-contents_card [data-testid="stPageLink"] p { font-weight: 650; font-size: 1.08rem; color: var(--ink); }
.st-key-contents_card [data-testid="stPageLink"] [data-testid="stIconMaterial"] { color: var(--blue); }

/* Entry cards: generous, with an icon chip and a footer button. */
[class*="st-key-entry_"] {
    background: linear-gradient(180deg, #FFFFFF 0%, #FAFCFB 100%);
    border-radius: 24px !important;
    padding: 1.6rem 1.5rem 1.4rem !important;
    box-shadow: 0 1px 2px rgb(8 23 26 / 4%), 0 14px 36px -22px rgb(8 23 26 / 30%);
}
[class*="st-key-entry_"] h3 { font-size: clamp(1.3rem, 1.8vw, 1.6rem) !important; }
[class*="st-key-entry_"] [data-testid="stMarkdownContainer"] p { color: #3E4F64; font-size: 1.02rem; line-height: 1.6; }
[class*="st-key-entry_"] button [data-testid="stMarkdownContainer"] p { color: #FFFFFF !important; font-size: 1rem; }
[class*="st-key-entry_"] h3 [data-testid="stIconMaterial"],
[class*="st-key-pillar_"] h3 [data-testid="stIconMaterial"],
.st-key-contribution_card h3 [data-testid="stIconMaterial"] {
    color: var(--blue) !important;
    background: #E3F5EE;
    border-radius: 12px;
    padding: 0.35rem;
    font-size: 1.25rem !important;
    width: auto !important;
    height: auto !important;
    margin-right: 0.35rem;
}
.st-key-contribution_card h3 [data-testid="stIconMaterial"] { padding: 0.25rem; font-size: 1rem !important; border-radius: 9px; }

/* Capability pillars. */
.st-key-chapter_tint_capability {
    background:
        radial-gradient(70% 90% at 0% 0%, rgb(18 184 134 / 9%) 0%, transparent 60%),
        linear-gradient(180deg, #EEF5F2 0%, #E8F1EC 100%) !important;
    gap: 1.1rem;
}
[class*="st-key-pillar_"] {
    position: relative;
    overflow: hidden;
    background: #FFFFFF;
    border: 1px solid #DCE9E3 !important;
    border-radius: 22px !important;
    padding: 1.5rem 1.3rem !important;
    box-shadow: 0 14px 34px -24px rgb(8 23 26 / 35%);
    gap: 0.8rem;
}
[class*="st-key-pillar_"]::after {
    content: "";
    position: absolute;
    left: 1.3rem; right: 1.3rem; top: 0;
    height: 3px;
    border-radius: 0 0 3px 3px;
    background: linear-gradient(90deg, var(--green-bright), var(--blue));
    opacity: 0.85;
}
[class*="st-key-pillar_"] h3 { font-size: 1.2rem !important; line-height: 1.25 !important; }
[class*="st-key-pillar_"] [data-testid="stCaptionContainer"] p { color: #44556A !important; font-size: 0.98rem !important; line-height: 1.65; }

/* The method line becomes a quiet statement band. */
.st-key-method_line, .st-key-method_line_story {
    background: #FFFFFF;
    border-radius: 24px;
    padding: 1.8rem 1.6rem 1.6rem;
    border: 1px solid #DCE9E3;
    box-shadow: 0 14px 34px -24px rgb(8 23 26 / 35%);
}

/* Entry cards: an accent line draws across the top when the card is approached. */
[class*="st-key-entry_"] { position: relative; overflow: hidden; }
[class*="st-key-entry_"]::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--blue), var(--blue-soft));
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 420ms var(--ease-out);
}
[class*="st-key-entry_"]:hover::before,
[class*="st-key-entry_"]:focus-within::before { transform: scaleX(1); }

/* The method line reads as a statement, not a footnote. */
.st-key-method_line p {
    font-size: clamp(1.1rem, 1.6vw, 1.35rem) !important;
    line-height: 1.85 !important;
    max-width: none !important;
    color: var(--slate);
}


/* ---------- Reading progress ---------- */
.read-progress {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 3px;
    z-index: 999990;
    background: linear-gradient(90deg, var(--blue), var(--blue-soft));
    transform-origin: left;
    transform: scaleX(0);
    pointer-events: none;
}
@supports (animation-timeline: scroll()) {
    .read-progress { animation: read-grow linear both; animation-timeline: scroll(nearest block); }
}
@keyframes read-grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }



@media (max-width: 900px) {
    .st-key-chapter_hero { min-height: 0; }
    .st-key-hero_backdrop { position: relative !important; inset: auto; margin: 0.75rem 0 0 !important; width: 100%; border-radius: 18px; overflow: hidden; }
}

/* ---------- Metrics never truncate their values ---------- */
[data-testid="stMetricValue"] *,
[data-testid="stMetricLabel"] * {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    -webkit-line-clamp: unset !important;
}
[data-testid="stMetricValue"] { line-height: 1.15; }
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * { overflow-wrap: normal !important; word-break: normal !important; }
[class*="st-key-calculated_result_"] [data-testid="stMetricValue"],
[class*="st-key-calculated_result_"] [data-testid="stMetricValue"] > div {
    font-size: clamp(0.98rem, 1.2vw, 1.5rem) !important;
    overflow-wrap: normal !important;
    word-break: normal !important;
}
[class*="st-key-calculated_result_"] [data-testid="stMetric"],
[class*="st-key-control_failure_"] [data-testid="stMetric"] {
    box-shadow: 0 14px 30px -22px rgb(8 23 26 / 40%);
}

/* ---------- Glossary: readable reference table ---------- */
.st-key-glossary_table [data-testid="stTable"] table { table-layout: auto; }
.st-key-glossary_table [data-testid="stTable"] th:nth-child(4),
.st-key-glossary_table [data-testid="stTable"] td:nth-child(4) { width: 52%; text-align: left !important; }
.st-key-glossary_table [data-testid="stTable"] td:nth-child(4) p { text-align: left !important; }
.st-key-glossary_table [data-testid="stTable"] td:nth-child(1) p { text-align: left !important; }
.st-key-glossary_table [data-testid="stTable"] td:nth-child(1) {
    text-align: left !important;
    font-weight: 650;
    color: var(--ink);
}
.st-key-glossary_table [data-testid="stTable"] td:nth-child(2) {
    font-weight: 700;
    color: var(--blue-deep);
    letter-spacing: 0.02em;
}
.st-key-glossary_table [data-testid="stTable"] th:nth-child(1) { text-align: left !important; }
.st-key-glossary_table [data-testid="stTable"] tbody tr { transition: background-color 160ms ease; }
.st-key-glossary_table [data-testid="stTable"] tbody tr:hover td { background-color: #E8F5EF !important; }

/* ---------- Page-level supporting text inside dark headers ---------- */
.st-key-chapter_dark_page_header [data-testid="stMarkdownContainer"] p { color: #D5E3DD; font-size: 1.04rem; }

/* ---------- Entry screen: the button reacts the instant the box is ticked ---------- */
/* Visual only: the button's real enabled state still comes from the checkbox value on rerun. */
.st-key-gate_card:has(input[type="checkbox"]:checked) [data-testid="stButton"] button {
    background: var(--blue) !important;
    border-color: var(--blue) !important;
    color: #FFFFFF !important;
    opacity: 1 !important;
    box-shadow: 0 8px 22px rgb(11 122 92 / 28%);
    transition: none !important;
}
.st-key-gate_card [data-testid="stButton"] { opacity: 1 !important; }
.st-key-gate_card:has(input[type="checkbox"]:checked) [data-testid="stButton"] button p { color: #FFFFFF !important; }

/* ---------- Motion ---------- */
@keyframes panel-in {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: none; }
}
@keyframes result-in {
    from { opacity: 0; transform: translateY(10px) scale(0.98); }
    to { opacity: 1; transform: none; }
}
@keyframes break-flash {
    0% { box-shadow: 0 0 0 0 rgb(229 72 77 / 55%); }
    100% { box-shadow: 0 0 0 14px rgb(229 72 77 / 0%); }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 1ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 1ms !important;
    }
    [class*="st-key-entry_"]:hover { transform: none; }
    .read-progress { display: none; }
    [class*="st-key-chapter_dark"]::before, [class*="st-key-chapter_dark"]::after { animation: none !important; }
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"] { padding-top: 4rem; }
    [class*="st-key-chapter_"] { border-radius: 20px; }
}
</style>
"""


def apply_layout() -> None:
    """Inject the presentation layer, honouring the visitor's display settings."""
    import streamlit as st

    text_size = int(st.session_state.get("portfolio_text_size", 18))
    text_size = max(12, min(32, text_size))
    content_width = "1100px" if st.session_state.get("portfolio_content_width") == "Reading width" else "100%"
    st.html(
        '<div class="read-progress" aria-hidden="true"></div>' + _CSS.replace("font-size: 18px", f"font-size: {text_size}px", 1).replace("__content_width__", content_width)
    )
