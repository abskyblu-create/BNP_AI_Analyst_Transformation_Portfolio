"""Synthetic content for the institutional transformation portfolio.

The reference ZIP mixes general finance language with institution-specific
names and overloaded abbreviations. This module keeps the operating concepts
but uses complete, neutral terms that stand on their own.
"""

from __future__ import annotations


FUNDS = [
    {"Fund": "Aurora Equity Fund", "Share class": "Institutional EUR Accumulation", "Base currency": "EUR", "Valuation frequency": "Daily"},
    {"Fund": "Meridian Bond Fund", "Share class": "Institutional EUR Distribution", "Base currency": "EUR", "Valuation frequency": "Daily"},
    {"Fund": "Helios Index Fund", "Share class": "Institutional EUR Accumulation", "Base currency": "EUR", "Valuation frequency": "Daily"},
    {"Fund": "Atlas Multi-Asset Fund", "Share class": "Institutional EUR Accumulation", "Base currency": "EUR", "Valuation frequency": "Weekly"},
]


OPERATING_MODELS = {
    "Global standardized model": {
        "definition": "A common process, platform and control framework shared across supported jurisdictions and processing locations.",
        "best_for": "Products and markets already configured on the common operating platform.",
        "ownership": "Global process owner, production hub and independent oversight team.",
        "strength": "Scale, consistent controls and higher straight-through processing potential.",
        "watch": "Local legal, tax and market rules still require explicit configuration.",
    },
    "Jurisdiction-specific local model": {
        "definition": "A dedicated process or platform for a market with specific legal, tax, product or infrastructure requirements.",
        "best_for": "Funds that cannot yet be processed safely through the common global model.",
        "ownership": "Local operations owner with global governance and escalation.",
        "strength": "Closer fit to local rules and market conventions.",
        "watch": "Fragmentation, duplicate controls and lower automation can increase operating cost.",
    },
}


TEAM_FUNCTIONS = {
    "Fund accounting": "Maintains the accounting book, accruals, valuation and Net Asset Value calculation.",
    "Reconciliation control": "Compares internal records with independent custodian and investment-manager records.",
    "Transfer agency": "Maintains the investor register and processes subscriptions, redemptions and unit movements.",
    "Client service": "Coordinates client communication, service review and issue escalation.",
    "Valuation oversight": "Challenges prices, material movements, exceptions and the final valuation package.",
}


PROFESSIONAL_PROFILE = {
    "name": "Ankit Bhatt",
    "headline": "Fund Administration Transformation · Data Engineering · Business Intelligence · Controlled Artificial Intelligence",
    "current_context": "Master's pathway in Data Engineering and Artificial Intelligence, supported by a documented 2025–2026 internship in global Fund Administration transformation.",
    "career_foundation": "More than a decade across financial services, including retail banking, credit assessment, collections, branch operations, customer responsibility and middle-management delivery.",
    "proposition": "Translate financial processes into explicit data rules, working controls, decision-ready reporting and accountable automation.",
    "working_pattern": ["Understand", "Structure", "Engineer", "Validate", "Communicate", "Deliver"],
}


CAPABILITY_PILLARS = [
    ("Business understanding", "Fund Administration, Net Asset Value production, reconciliation, cash and non-cash controls"),
    ("Project delivery", "Requirements, proof of concept, User Acceptance Testing, status governance, blockers and handover"),
    ("Technical engineering", "Power BI, Data Analysis Expressions, Power Query M, Python, data modelling and controlled automation"),
    ("Communication", "Business-to-technical translation, global stakeholder reviews, evidence, decisions and next actions"),
]


DELIVERY_STAGES = [
    "Business need",
    "Business needs document",
    "Operations validation",
    "Business requirements document",
    "Build",
    "Proof of concept",
    "User Acceptance Testing",
    "Production readiness",
    "Business as usual handover",
]


# Event-grain reporting population used by the management-reporting workbench.
# It is deliberately richer than the run-linked exception register so that
# entity counts, match rates, trends, ageing and concentration can be tested.
RECONCILIATION_EVENTS = [
    {"Event ID": "REC-001", "Event date": "2026-09-08", "Fund": "Aurora Equity Fund", "Client segment": "Institutional", "Processing location": "Global hub A", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
    {"Event ID": "REC-002", "Event date": "2026-09-09", "Fund": "Aurora Equity Fund", "Client segment": "Institutional", "Processing location": "Global hub A", "Reconciliation status": "Matched", "Match method": "Manual", "Break type": "Settlement-date review", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Recorded"},
    {"Event ID": "REC-003", "Event date": "2026-09-10", "Fund": "Aurora Equity Fund", "Client segment": "Institutional", "Processing location": "Global hub A", "Reconciliation status": "Outstanding Active", "Match method": "Not matched", "Break type": "Settlement-date mismatch", "Amount under investigation (EUR)": 1_450_000.0, "Age (days)": 4, "Timeliness": "Late", "Investigation note": "Recorded"},
    {"Event ID": "REC-004", "Event date": "2026-09-11", "Fund": "Aurora Equity Fund", "Client segment": "Institutional", "Processing location": "Global hub B", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
    {"Event ID": "REC-005", "Event date": "2026-09-12", "Fund": "Aurora Equity Fund", "Client segment": "Institutional", "Processing location": "Global hub B", "Reconciliation status": "Outstanding Hold", "Match method": "Not matched", "Break type": "External confirmation pending", "Amount under investigation (EUR)": 210_000.0, "Age (days)": 6, "Timeliness": "Late", "Investigation note": "Missing"},
    {"Event ID": "REC-006", "Event date": "2026-09-13", "Fund": "Aurora Equity Fund", "Client segment": "Institutional", "Processing location": "Global hub A", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
    {"Event ID": "REC-007", "Event date": "2026-09-08", "Fund": "Meridian Bond Fund", "Client segment": "Insurance", "Processing location": "Global hub B", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
    {"Event ID": "REC-008", "Event date": "2026-09-09", "Fund": "Meridian Bond Fund", "Client segment": "Insurance", "Processing location": "Global hub B", "Reconciliation status": "Outstanding Active", "Match method": "Not matched", "Break type": "Coupon-accrual variance", "Amount under investigation (EUR)": 1_400.0, "Age (days)": 1, "Timeliness": "On time", "Investigation note": "Recorded"},
    {"Event ID": "REC-009", "Event date": "2026-09-10", "Fund": "Meridian Bond Fund", "Client segment": "Insurance", "Processing location": "Global hub B", "Reconciliation status": "Matched", "Match method": "Manual", "Break type": "Coupon period verified", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Recorded"},
    {"Event ID": "REC-010", "Event date": "2026-09-11", "Fund": "Meridian Bond Fund", "Client segment": "Insurance", "Processing location": "Global hub C", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
    {"Event ID": "REC-011", "Event date": "2026-09-12", "Fund": "Meridian Bond Fund", "Client segment": "Insurance", "Processing location": "Global hub C", "Reconciliation status": "Outstanding Active", "Match method": "Not matched", "Break type": "Income receivable", "Amount under investigation (EUR)": 84_000.0, "Age (days)": 2, "Timeliness": "Late", "Investigation note": "Recorded"},
    {"Event ID": "REC-012", "Event date": "2026-09-13", "Fund": "Meridian Bond Fund", "Client segment": "Insurance", "Processing location": "Global hub B", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
    {"Event ID": "REC-013", "Event date": "2026-09-08", "Fund": "Helios Index Fund", "Client segment": "Pension", "Processing location": "Global hub C", "Reconciliation status": "Outstanding Hold", "Match method": "Not matched", "Break type": "Contract-multiplier mismatch", "Amount under investigation (EUR)": 3_200_000.0, "Age (days)": 12, "Timeliness": "Late", "Investigation note": "Recorded"},
    {"Event ID": "REC-014", "Event date": "2026-09-09", "Fund": "Helios Index Fund", "Client segment": "Pension", "Processing location": "Global hub C", "Reconciliation status": "Matched", "Match method": "Manual", "Break type": "Multiplier corrected", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "Late", "Investigation note": "Recorded"},
    {"Event ID": "REC-015", "Event date": "2026-09-10", "Fund": "Helios Index Fund", "Client segment": "Pension", "Processing location": "Global hub C", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
    {"Event ID": "REC-016", "Event date": "2026-09-11", "Fund": "Helios Index Fund", "Client segment": "Pension", "Processing location": "Global hub A", "Reconciliation status": "Outstanding Active", "Match method": "Not matched", "Break type": "Position difference", "Amount under investigation (EUR)": 620_000.0, "Age (days)": 3, "Timeliness": "Late", "Investigation note": "Missing"},
    {"Event ID": "REC-017", "Event date": "2026-09-12", "Fund": "Helios Index Fund", "Client segment": "Pension", "Processing location": "Global hub A", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
    {"Event ID": "REC-018", "Event date": "2026-09-13", "Fund": "Helios Index Fund", "Client segment": "Pension", "Processing location": "Global hub C", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
    {"Event ID": "REC-019", "Event date": "2026-09-08", "Fund": "Atlas Multi-Asset Fund", "Client segment": "Wholesale", "Processing location": "Global hub A", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
    {"Event ID": "REC-020", "Event date": "2026-09-09", "Fund": "Atlas Multi-Asset Fund", "Client segment": "Wholesale", "Processing location": "Global hub A", "Reconciliation status": "Outstanding Active", "Match method": "Not matched", "Break type": "Rounding difference", "Amount under investigation (EUR)": 0.45, "Age (days)": 2, "Timeliness": "On time", "Investigation note": "Recorded"},
    {"Event ID": "REC-021", "Event date": "2026-09-10", "Fund": "Atlas Multi-Asset Fund", "Client segment": "Wholesale", "Processing location": "Global hub A", "Reconciliation status": "Matched", "Match method": "Manual", "Break type": "Rounding verified", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Recorded"},
    {"Event ID": "REC-022", "Event date": "2026-09-11", "Fund": "Atlas Multi-Asset Fund", "Client segment": "Wholesale", "Processing location": "Global hub B", "Reconciliation status": "Outstanding Hold", "Match method": "Not matched", "Break type": "Cash statement pending", "Amount under investigation (EUR)": 510_000.0, "Age (days)": 5, "Timeliness": "Late", "Investigation note": "Recorded"},
    {"Event ID": "REC-023", "Event date": "2026-09-12", "Fund": "Atlas Multi-Asset Fund", "Client segment": "Wholesale", "Processing location": "Global hub B", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
    {"Event ID": "REC-024", "Event date": "2026-09-13", "Fund": "Atlas Multi-Asset Fund", "Client segment": "Wholesale", "Processing location": "Global hub A", "Reconciliation status": "Matched", "Match method": "Automatic", "Break type": "None", "Amount under investigation (EUR)": 0.0, "Age (days)": 0, "Timeliness": "On time", "Investigation note": "Not required"},
]


PROJECTS = [
    {
        "id": "P01", "title": "Data engineering and transformation", "pillar": "Data engineering",
        "metric": "43 → 21 fields · ~51% rationalization",
        "challenge": "Global operational information was fragmented across emails and spreadsheets, limiting consistency, traceability and dependable downstream analysis.",
        "objective": "Converted fragmented sources into a master dataset and rationalized 43 source fields to 21 usable fields while preserving business meaning and lineage.",
        "tools": ["Python", "Comma-separated value and spreadsheet processing", "Validation rules"],
        "pipeline": ["Source intake", "Header recognition", "Controlled value carry-forward", "Standardization", "Quality validation", "Management metrics"],
        "decisions": ["Preserve a missing value separately from a verified zero", "Retain source-file and source-row lineage", "Quarantine structurally invalid rows"],
        "controls": ["Row-count reconciliation", "Duplicate detection", "Encoding fallback", "No silent row loss"],
        "evidence": ["A master dataset with ~51% field rationalization", "Improved consistency and traceability", "More usable input for downstream analysis"],
        "learning": "Analytical and Artificial Intelligence logic becomes reliable only after source-data structure and meaning are stabilized.",
    },
    {
        "id": "P02", "title": "Power BI and reconciliation analytics", "pillar": "Data and business intelligence",
        "metric": "4 dimensions · 5+ KPIs",
        "challenge": "Reconciliation information needed a dependable management view across Fund, Client, Location and Date without inflated counts or ambiguous totals.",
        "objective": "Built reconciliation analytics across four dimensions, with 5+ KPIs covering matching, ageing, exposure, timeliness and automation levels.",
        "tools": ["Power BI", "Power Query M", "Data Analysis Expressions", "Dimensional star schema"],
        "pipeline": ["Fund reference master", "Conformed fund dimension", "Reconciliation event fact", "Business-rule layer", "Measures", "Management views"],
        "decisions": ["One dimension row per fund", "One fact row per reconciliation event", "Single-direction one-to-many filtering"],
        "controls": ["Unique-fund versus event-count reconciliation", "Date-quality gates", "Missing-value controls", "Measure lineage"],
        "evidence": ["Decision-ready analytics across four dimensions", "Visibility into 5+ operational KPIs", "Improved analysis of matching and exceptions"],
        "learning": "A clear semantic model prevents more reporting errors than an expanding library of measures can repair.",
    },
    {
        "id": "P03", "title": "AI engineering and LLM automation", "pillar": "Automation and Artificial Intelligence",
        "metric": "10,000+ records · ~5 minutes per batch",
        "challenge": "NAV-delay review had to handle large record populations and different valuation calendars without unreliable generic rules or invented dates.",
        "objective": "Designed deterministic NAV-delay checks using structured prompting and calendar-aware rules, enabling faster and more consistent exception review.",
        "tools": ["AI engineering", "Large Language Model", "Calendar-aware rules", "Structured outputs"],
        "pipeline": ["Classify valuation frequency", "Apply daily or non-daily logic", "Bound the supplied records", "Run structured prompt checks", "Re-verify outputs", "Route exceptions for review"],
        "decisions": ["Use different rules for daily and non-daily funds", "Never extrapolate outside the supplied calendar", "Keep outputs deterministic and reviewable"],
        "controls": ["Anchor and terminus boundaries", "Explicit NULL rules", "Source re-verification", "Human sign-off"],
        "evidence": ["10,000+ records processed in controlled batches", "Approximately five minutes per batch", "Faster and more consistent exception review"],
        "learning": "AI engineering becomes operational engineering when rules, boundaries, output structure and approval are explicit.",
    },
    {
        "id": "P04", "title": "Python and GUI tool development", "pillar": "Data engineering",
        "metric": "4,500–5,000+ rows per dataset",
        "challenge": "Large datasets needed to be divided into processing batches without manual copy-paste, lost rows, duplicates or broken sequence.",
        "objective": "Developed a reusable Python GUI chunking utility that created sequential batches while preserving record order, continuity and data integrity.",
        "tools": ["Python", "Desktop GUI", "Windows batch launcher", "Integrity validation"],
        "pipeline": ["Select input file", "Read schema and rows", "Choose batch size", "Split sequentially", "Repeat headers", "Reconcile outputs"],
        "decisions": ["Never split a physical record", "Preserve source order", "Name outputs with explicit sequence boundaries"],
        "controls": ["Input-to-output row count", "Duplicate detection", "Boundary continuity", "Repeatable manifest"],
        "evidence": ["Reusable utility for 4,500–5,000+ row datasets", "Sequential processing batches", "Preserved order and data integrity"],
        "learning": "A small utility creates operational value when usability and integrity controls are designed together.",
    },
    {
        "id": "P05", "title": "Financial process automation", "pillar": "Automation and Artificial Intelligence",
        "metric": "2 LLM-enabled workstreams",
        "challenge": "ETD and FX records arrived in heterogeneous formats with product-specific fields, legs, direction and mapping requirements.",
        "objective": "Contributed to ETD extraction and injection and FX reconciliation and matching, using AI engineering to standardize data for controlled downstream processing.",
        "tools": ["Specialized agent prompts", "Dynamic Knowledge Base", "Explainable Artificial Intelligence", "Schema validation"],
        "pipeline": ["Receive broker data", "Extract fields", "Map business meaning", "Validate product rules", "Inject or match records", "Request approval"],
        "decisions": ["Separate extraction from semantic mapping", "Validate each FX leg independently", "Use modular prompts"],
        "controls": ["Field-level evidence", "Direction and leg validation", "Mandatory-field checks", "Human approval"],
        "evidence": ["Two controlled LLM-enabled workstreams", "Standardized ETD and FX data", "Traceable extraction, injection, reconciliation and matching"],
        "learning": "Specialized prompt stages are easier to test, explain and govern than one monolithic prompt.",
    },
    {
        "id": "P06", "title": "AI governance and global stakeholder management", "pillar": "Governance and delivery",
        "metric": "5 weeks · 8 → ~24 participants/use cases · 9 countries",
        "challenge": "AI ideas across locations needed a shared review rhythm, visible ownership and targeted support to progress consistently.",
        "objective": "Supported weekly reviews, one-to-one troubleshooting and prompt refinement across France, UK, Germany, Luxembourg, Italy, Spain, Portugal, Poland and India.",
        "tools": ["Weekly governance reviews", "Prompt refinement", "One-to-one troubleshooting", "Shared use-case register"],
        "pipeline": ["Register use cases", "Frame problems", "Review prompts and proofs of concept", "Record blockers", "Provide one-to-one support", "Agree next actions"],
        "decisions": ["Maintain one source of truth", "Match support to each blocker", "Require evidence before progression"],
        "controls": ["Weekly decision record", "Named owners", "Open-risk follow-up", "Prompt-review criteria"],
        "evidence": ["Five-week governance cycle", "Growth from 8 to approximately 24 participants/use cases", "Coordination across nine countries"],
        "learning": "Scaling AI depends on governance, communication and hands-on support as much as the model or prompt.",
    },
    {
        "id": "P07", "title": "Anomaly detection and risk prioritization", "pillar": "Data and business intelligence",
        "metric": "0–1 anomaly index · multiple business checks",
        "challenge": "A binary exception flag could not distinguish data defects from abnormal patterns or focus reviewers on the most important records.",
        "objective": "Developed rule-based anomaly scoring from 0 to 1 using multiple business checks to rank records by severity.",
        "tools": ["Business decision tables", "Weighted scoring", "Power BI", "Explainable rules"],
        "pipeline": ["Run data-quality gate", "Apply business checks", "Calculate components", "Produce 0–1 index", "Assign priority", "Analyst review"],
        "decisions": ["Stop scoring when mandatory data is invalid", "Keep every check visible", "Rank severity rather than use an unexplained flag"],
        "controls": ["Score-component lineage", "Source-defect quarantine", "0–1 range validation", "Analyst review"],
        "evidence": ["Explainable 0–1 anomaly index", "Risk-ranked review population", "More focused review of higher-priority exceptions"],
        "learning": "Risk scoring is useful only when reviewers can reconstruct every signal behind the priority.",
    },
    {
        "id": "P08", "title": "Cross-functional mission delivery", "pillar": "Governance and delivery",
        "metric": "6 stakeholder groups · requirements → UAT → delivery",
        "challenge": "Transformation missions crossed business, operational and technical teams and required shared requirements, evidence and implementation ownership.",
        "objective": "Coordinated Operations, APS, BAU, IT, Transformation and SMEs from requirements and feasibility through UAT and operational implementation.",
        "tools": ["Requirements management", "User Acceptance Testing", "Red-Amber-Green governance", "Stakeholder coordination"],
        "pipeline": ["Clarify business need", "Validate requirements and feasibility", "Coordinate build or proof of concept", "Track UAT", "Resolve blockers", "Support delivery"],
        "decisions": ["Separate technical completion from readiness", "Name owners and target dates", "Re-plan when evidence changes"],
        "controls": ["Requirement-to-test traceability", "Six-group ownership", "Blocker and status review", "Business acceptance"],
        "evidence": ["Coordination across six stakeholder groups", "Traceable path from requirements to UAT and delivery", "Visible ownership and readiness"],
        "learning": "Cross-functional delivery succeeds when technical work, evidence and stakeholder decisions move together.",
    },
]


NAV_FOUNDATION_STEPS = [
    ("01", "Fund rules and valuation policy", "Confirm valuation frequency, base currency, dealing cut-off, pricing sources, fee rules and control ownership."),
    ("02", "Trade and position capture", "Load settled positions, unsettled trades and security-reference data at the valuation point."),
    ("03", "Cash and investor dealing", "Reconcile bank cash and capture subscriptions, redemptions and settlement forecasts."),
    ("04", "Corporate actions and income", "Recognize dividends, coupons, interest, tax and other receivables supported by entitlement records."),
    ("05", "Market valuation", "Apply approved security prices and foreign-exchange rates using the fund's pricing policy."),
    ("06", "Liabilities and expense accruals", "Recognize payables, fees, tax and other obligations attributable to the fund."),
    ("07", "Three-way reconciliation", "Compare fund-accounting, custodian and investment-manager records and assess unresolved differences."),
    ("08", "Net asset calculation", "Aggregate assets, deduct liabilities and divide by validated units outstanding."),
    ("09", "Anti-dilution assessment", "Apply the documented swing-pricing policy only when net dealing exceeds the configured threshold."),
    ("10", "Reasonableness and tolerance review", "Challenge material movements, stale prices, liquidity, accruals and reconciliation impacts."),
    ("11", "Maker-checker authorization", "A preparer assembles the package and an independent checker approves the evidence."),
    ("12", "Controlled distribution and retention", "Distribute the approved price to authorized recipients and retain acknowledgements and evidence."),
]


SYNTHETIC_POSITIONS_BY_FUND = {
    "Aurora Equity Fund": [
        {"Position ID": "POS-001", "Instrument": "European large-cap equity basket", "Instrument type": "Listed equity", "Quantity": 1_500_000.0, "Local price": 100.0, "Local currency": "EUR", "FX rate to EUR": 1.0, "Price status": "Current", "Price timestamp": "2026-09-17 18:00 UTC"},
        {"Position ID": "POS-002", "Instrument": "United States quality-equity basket", "Instrument type": "Listed equity", "Quantity": 1_000_000.0, "Local price": 120.0, "Local currency": "USD", "FX rate to EUR": 0.92, "Price status": "Current", "Price timestamp": "2026-09-17 21:00 UTC"},
        {"Position ID": "POS-003", "Instrument": "Euro small-cap equity basket", "Instrument type": "Listed equity", "Quantity": 1_698_000.0, "Local price": 100.0, "Local currency": "EUR", "FX rate to EUR": 1.0, "Price status": "Current", "Price timestamp": "2026-09-17 18:00 UTC"},
        {"Position ID": "POS-004", "Instrument": "United Kingdom dividend-equity basket", "Instrument type": "Listed equity", "Quantity": 400_000.0, "Local price": 100.0, "Local currency": "GBP", "FX rate to EUR": 1.12, "Price status": "Current", "Price timestamp": "2026-09-17 16:30 UTC"},
    ],
    "Meridian Bond Fund": [
        {"Position ID": "MER-001", "Instrument": "Euro sovereign-bond basket units", "Instrument type": "Government bond", "Quantity": 1_800_000.0, "Local price": 100.0, "Local currency": "EUR", "FX rate to EUR": 1.0, "Price status": "Current", "Price timestamp": "2026-09-17 18:00 UTC"},
        {"Position ID": "MER-002", "Instrument": "Euro investment-grade credit basket units", "Instrument type": "Corporate bond", "Quantity": 1_352_000.0, "Local price": 100.0, "Local currency": "EUR", "FX rate to EUR": 1.0, "Price status": "Current", "Price timestamp": "2026-09-17 18:00 UTC"},
        {"Position ID": "MER-003", "Instrument": "United States Treasury-bond basket units", "Instrument type": "Government bond", "Quantity": 1_000_000.0, "Local price": 125.0, "Local currency": "USD", "FX rate to EUR": 0.92, "Price status": "Current", "Price timestamp": "2026-09-17 21:00 UTC"},
        {"Position ID": "MER-004", "Instrument": "United Kingdom sovereign-bond basket units", "Instrument type": "Government bond", "Quantity": 400_000.0, "Local price": 100.0, "Local currency": "GBP", "FX rate to EUR": 1.12, "Price status": "Current", "Price timestamp": "2026-09-17 16:30 UTC"},
    ],
    "Helios Index Fund": [
        {"Position ID": "HEL-001", "Instrument": "Euro broad-market index equity basket", "Instrument type": "Listed equity", "Quantity": 2_000_000.0, "Local price": 100.0, "Local currency": "EUR", "FX rate to EUR": 1.0, "Price status": "Current", "Price timestamp": "2026-09-17 18:00 UTC"},
        {"Position ID": "HEL-002", "Instrument": "United States broad-market index equity basket", "Instrument type": "Listed equity", "Quantity": 1_500_000.0, "Local price": 100.0, "Local currency": "USD", "FX rate to EUR": 0.92, "Price status": "Current", "Price timestamp": "2026-09-17 21:00 UTC"},
        {"Position ID": "HEL-003", "Instrument": "United Kingdom index equity basket", "Instrument type": "Listed equity", "Quantity": 800_000.0, "Local price": 100.0, "Local currency": "GBP", "FX rate to EUR": 1.12, "Price status": "Current", "Price timestamp": "2026-09-17 16:30 UTC"},
        {"Position ID": "HEL-004", "Instrument": "Euro small-cap index equity basket", "Instrument type": "Listed equity", "Quantity": 474_000.0, "Local price": 100.0, "Local currency": "EUR", "FX rate to EUR": 1.0, "Price status": "Current", "Price timestamp": "2026-09-17 18:00 UTC"},
    ],
    "Atlas Multi-Asset Fund": [
        {"Position ID": "ATL-001", "Instrument": "European diversified equity basket", "Instrument type": "Listed equity", "Quantity": 1_200_000.0, "Local price": 100.0, "Local currency": "EUR", "FX rate to EUR": 1.0, "Price status": "Current", "Price timestamp": "2026-09-17 18:00 UTC"},
        {"Position ID": "ATL-002", "Instrument": "United States diversified equity basket", "Instrument type": "Listed equity", "Quantity": 1_000_000.0, "Local price": 100.0, "Local currency": "USD", "FX rate to EUR": 0.92, "Price status": "Current", "Price timestamp": "2026-09-17 21:00 UTC"},
        {"Position ID": "ATL-003", "Instrument": "Euro sovereign-bond basket units", "Instrument type": "Government bond", "Quantity": 1_500_000.0, "Local price": 100.0, "Local currency": "EUR", "FX rate to EUR": 1.0, "Price status": "Current", "Price timestamp": "2026-09-17 18:00 UTC"},
        {"Position ID": "ATL-004", "Instrument": "Euro investment-grade credit basket units", "Instrument type": "Corporate bond", "Quantity": 1_000_000.0, "Local price": 100.0, "Local currency": "EUR", "FX rate to EUR": 1.0, "Price status": "Current", "Price timestamp": "2026-09-17 18:00 UTC"},
        {"Position ID": "ATL-005", "Instrument": "Euro short-term money-market fund units", "Instrument type": "Cash equivalent", "Quantity": 130_000.0, "Local price": 100.0, "Local currency": "EUR", "FX rate to EUR": 1.0, "Price status": "Current", "Price timestamp": "2026-09-17 18:00 UTC"},
    ],
}

# Retained for callers that need the first fund's default fixture.
SYNTHETIC_POSITIONS = SYNTHETIC_POSITIONS_BY_FUND[FUNDS[0]["Fund"]]


SYNTHETIC_TRADES = [
    {"Trade ID": "TRD-24091", "Security": "European equity basket", "Side": "Buy", "Quantity": 1500, "Price": 884.20, "Gross amount (EUR)": 1_326_300, "Settlement": "T+2", "Status": "Matched"},
    {"Trade ID": "TRD-24092", "Security": "Industrial equity basket", "Side": "Sell", "Quantity": 2000, "Price": 614.00, "Gross amount (EUR)": 1_228_000, "Settlement": "T+2", "Status": "Settlement queued"},
]


TRADE_SECURITIES_BY_FUND = {
    "Aurora Equity Fund": ("European large-cap equity basket", "Euro small-cap equity basket"),
    "Meridian Bond Fund": ("Euro sovereign-bond basket units", "Euro investment-grade credit basket units"),
    "Helios Index Fund": ("Euro broad-market index equity basket", "United States broad-market index equity basket"),
    "Atlas Multi-Asset Fund": ("Euro sovereign-bond basket units", "European diversified equity basket"),
}


def synthetic_trades_for_fund(fund_name: str) -> list[dict]:
    """Return a fund-appropriate illustrative trade ledger for the cash ladder."""
    securities = TRADE_SECURITIES_BY_FUND[fund_name]
    fund_code = "".join(word[0] for word in fund_name.split()[:3]).upper()
    return [
        {
            **trade,
            "Trade ID": f"TRD-{fund_code}-{index:03d}",
            "Fund": fund_name,
            "Security": securities[index - 1],
        }
        for index, trade in enumerate(SYNTHETIC_TRADES, start=1)
    ]


SYNTHETIC_BREAKS = [
    {"Break ID": "BRK-10421", "Fund": "Aurora Equity Fund", "Instrument": "Foreign-exchange forward", "Difference type": "Settlement-date mismatch", "Source currency": "EUR", "Fund accounting amount": 1_450_000.0, "Custodian amount": 1_450_000.0, "Investment manager amount": 1_450_000.0, "Amount under investigation (EUR)": 1_450_000.0, "Impact (basis points)": 0.61, "Age (days)": 4, "Workflow status": "Under investigation", "Severity": "High", "Root cause": "The accounting record and custodian confirmation use adjacent settlement dates.", "Control layer": "Trade record versus custodian confirmation"},
    {"Break ID": "BRK-10422", "Fund": "Meridian Bond Fund", "Instrument": "Government bond", "Difference type": "Coupon-accrual variance", "Source currency": "EUR", "Fund accounting amount": 82_300.0, "Custodian amount": 80_900.0, "Investment manager amount": 82_300.0, "Amount under investigation (EUR)": 1_400.0, "Impact (basis points)": 0.03, "Age (days)": 1, "Workflow status": "Open", "Severity": "Medium", "Root cause": "The custodian used a different day-count period for the coupon accrual.", "Control layer": "General ledger versus custody income record"},
    {"Break ID": "BRK-10423", "Fund": "Helios Index Fund", "Instrument": "Equity index future", "Difference type": "Contract-multiplier mismatch", "Source currency": "EUR", "Fund accounting amount": 10_820_500.0, "Custodian amount": 7_620_500.0, "Investment manager amount": 10_820_500.0, "Amount under investigation (EUR)": 3_200_000.0, "Impact (basis points)": 0.67, "Age (days)": 12, "Workflow status": "Escalated", "Severity": "Critical", "Root cause": "The source confirmation was loaded without the contract-size multiplier.", "Control layer": "Derivative sub-ledger versus broker and custodian records"},
    {"Break ID": "BRK-10424", "Fund": "Atlas Multi-Asset Fund", "Instrument": "Spot foreign exchange", "Difference type": "Rounding difference", "Source currency": "EUR", "Fund accounting amount": 1_202_425.45, "Custodian amount": 1_202_425.00, "Investment manager amount": 1_202_425.45, "Amount under investigation (EUR)": 0.45, "Impact (basis points)": 0.00, "Age (days)": 2, "Workflow status": "Open", "Severity": "Low", "Root cause": "The records round the converted amount at different decimal precision.", "Control layer": "Cash ledger versus bank statement"},
]


QUALITY_GATES = [
    ("Source-record integrity", "Every critical amount is linked to an identifiable source and valuation date."),
    ("Business-rule validation", "Missing values, date boundaries, product rules and tolerances are tested explicitly."),
    ("Accounting and reconciliation", "The accounting equation balances and unresolved differences are assessed for valuation impact."),
    ("Operational readiness", "Owners, procedures, escalation paths and recovery arrangements are documented."),
    ("Explainability and independent approval", "Automated outputs can be reconstructed and a qualified reviewer records a decision."),
]


GLOSSARY = [
    ("Net Asset Value", "NAV", "Fund operations", "Fund assets less liabilities at a valuation point; the result underpins the price per unit."),
    ("Fund Administration", "FA", "Fund operations", "The service that maintains fund accounting, valuations and related operational reporting."),
    ("Client Account Manager", "CAM", "Fund operations", "The client-relationship owner who supports business implementation, fund setup and coordination with Operations."),
    ("Transfer Agency", "TA", "Fund operations", "The function that maintains investor records and processes subscriptions and redemptions."),
    ("Global Operating Model", "GOM", "Fund operations", "The shared operating model used across participating fund-administration locations."),
    ("Local Operating Model", "LOM", "Fund operations", "A local operating setup used where processes or systems differ from the global model."),
    ("Straight-Through Processing", "STP", "Fund operations", "Processing without manual intervention; the STP rate is straight-through items divided by eligible items."),
    ("Assets Under Administration", "AUA", "Fund operations", "Assets for which administration or servicing is provided."),
    ("Assets Under Management", "AUM", "Fund operations", "Assets managed on behalf of investors; distinct from assets under administration."),
    ("Reconciliation", "REC", "Fund operations", "Comparison of records to find and resolve differences before reporting or valuation."),
    ("Ageing", "", "Fund operations", "How long a reconciliation item has remained open."),
    ("Timeliness", "", "Fund operations", "Whether a process or delivery met its deadline or cut-off."),
    ("Exchange-Traded Derivative", "ETD", "Instruments", "An exchange-traded contract, such as a future or option, whose contract terms affect data mapping."),
    ("Foreign Exchange", "FX", "Instruments", "Currency transactions whose legs and direction need to be mapped correctly."),
    ("Over-the-Counter", "OTC", "Instruments", "A transaction negotiated outside an exchange."),
    ("Basis points", "bps", "Simulation unit", "A unit for small percentage changes. One basis point (bps) equals 0.01% and is used in the valuation example's swing factor."),
    ("Business Change Management", "BCM", "Delivery", "The change-management function involved in defining and coordinating business requirements."),
    ("BND change document", "BND", "Delivery", "An internal change-flow document prepared by Business Change Management and validated by Operations before the BRD stage."),
    ("Business Requirement Document", "BRD", "Delivery", "The detailed requirements document used to guide development and testing."),
    ("Proof of Concept", "POC", "Delivery", "A limited test of whether a proposed solution is feasible."),
    ("User Acceptance Testing", "UAT", "Delivery", "Business users test the solution against agreed requirements before production readiness."),
    ("Business As Usual", "BAU", "Delivery", "The recurring operating process after a change is handed over."),
    ("Red-Amber-Green status", "RAG", "Delivery", "A delivery-status convention: on track, at risk or blocked."),
    ("Key Performance Indicator", "KPI", "Delivery", "A defined measure used to monitor a process or result."),
    ("Quarterly Action Plan", "QAP", "Delivery", "A quarterly set of priorities, deliverables, owners and progress reviews."),
    ("Business Continuity Plan", "BCP", "Controls", "Arrangements to sustain or recover critical operations during a disruption."),
    ("Risk and Control Self-Assessment", "RCSA", "Controls", "A process for assessing risks and controls and tracking needed improvements."),
    ("Data Quality", "DQ", "Data and AI", "Checks that source records are complete, valid and suitable for later reporting or automation."),
    ("Data Analysis Expressions", "DAX", "Data and AI", "The formula language used for Power BI measures."),
    ("Power Query M", "M", "Data and AI", "The language used to transform data in Power Query."),
    ("Star schema", "", "Data and AI", "A reporting model with a central event table linked to descriptive dimension tables."),
    ("NULL", "", "Data and AI", "A missing, unknown or inapplicable value; it is not a verified zero."),
    ("Large Language Model", "LLM", "Data and AI", "A language model used in the documented experiments for an independent recheck or structured extraction."),
    ("Dynamic Knowledge Base", "DKB", "Data and AI", "Session-level mapping knowledge used in the documented broker-data automation design."),
    ("Explainable Artificial Intelligence", "XAI", "Data and AI", "Traceability from an automated output back to its source, mapping and checks."),
]


SKILLS = [
    ("Fund administration and valuation", 88, "Accounting lifecycle, reconciliations, cut-offs and valuation controls"),
    ("Data architecture and business intelligence", 86, "Dimensional modeling, Power BI, Data Analysis Expressions and Power Query M"),
    ("Python engineering", 80, "Integrity-preserving data utilities and repeatable operational tooling"),
    ("Controlled Artificial Intelligence design", 84, "Bounded extraction, specialized stages, mapping context and explainability"),
    ("Governance and User Acceptance Testing", 82, "Evidence, blockers, ownership, readiness and escalation"),
    ("Business and technical communication", 79, "Translating operational problems into rules, designs and decisions"),
]
