"""Plain-language guides placed beside the fictional exercises they explain."""

import streamlit as st


# Each guide connects vocabulary, an example calculation and its operational impact.
GUIDES = {
    "scope": (
        "A fund is a pooled investment vehicle. A share class is a group of units with its own terms; base currency is the currency used to report this case. The valuation date fixes the point in time being measured.",
        "Acceptance criteria are the outcomes the process must demonstrate, not financial returns. A source, valuation and review must all refer to the same fund, class and date.",
        "This context follows every later stage. Mixing dates or classes could produce a plausible price for the wrong investor population; the final delivery checks return to these original criteria.",
    ),
    "sources": (
        "A source is an input record, such as a trade file or investor register. Lineage means retaining where each value came from. A fingerprint is a calculated digest used to detect a change in content.",
        "The intake checks compare received rows with preserved rows and compare fingerprints. For example, receiving 100 rows but preserving 99 fails the row-count test even if the remaining values look reasonable.",
        "Later calculations consume this preserved pack. Matching counts and fingerprints support completeness and unchanged content during intake; they do not prove the original economic values were correct.",
    ),
    "model": (
        "A dimension describes an entity, such as one fund. A fact records an event, such as one trade. Grain means what one row represents; a key connects related records.",
        "One fund with 20 trades is one fund and 20 trade rows. Missing values, duplicate identifiers, invalid dates and unmatched fund keys are counted as exceptions; zero exceptions means these specified checks passed.",
        "Validated keys let holdings, trades and exceptions join to the right fund. Joining through duplicate fund keys can multiply rows and overstate amounts; correct structure protects every later total.",
    ),
    "positions": (
        "Quantity is the number of units of an investment held; local price is the price in its quoted currency. FX rate to EUR here means euros per unit of local currency. Position value is the resulting holding value in euros.",
        "This simplified model uses quantity × local price × FX rate. For example, 100 shares × USD 50 × EUR 0.90 per USD = EUR 4,500. Sum all position values, then subtract the accounting investment balance to find the roll-up difference.",
        "Higher prices or a higher EUR conversion rate increase this model's investment value and, with other inputs fixed, NAV. Stale prices or a non-zero roll-up difference need review. Real bonds and derivatives can require additional pricing conventions or multipliers.",
    ),
    "reconciliation": (
        "Reconciliation compares records describing the same event or balance. A break is a mismatch; ageing is how long it has remained open. A suspected cause needs evidence before it becomes a confirmed cause. A disposition records the action or decision.",
        "Equal amounts can still have different settlement dates. Amount under investigation measures the case being checked, not automatically a loss. One basis point (bp) is 0.01 percentage point; amount / NAV × 10,000 expresses relative size in bps. Source-estimated NAV impact still needs validation.",
        "A documented date correction may leave NAV unchanged. A correction to an accounting asset or liability changes NAV and requires recalculation. An unresolved run-linked break can block review; unrelated funds' breaks do not automatically block this run. Tolerance acceptance needs the example's limit and evidence.",
    ),
    "nav": (
        "Assets are what the fund owns or is owed; liabilities are what it owes. Net Asset Value (NAV) is the remaining investor ownership value. Units in issue are investor units, not the quantities of securities held.",
        "NAV = assets − liabilities; NAV per unit = NAV / units. EUR 1,000,000 assets − EUR 100,000 liabilities = EUR 900,000 NAV; divided by 9,000 units gives EUR 100 per unit. A subscription of EUR 10,000 at that price buys 100 units, ignoring adjustments and fees.",
        "With units fixed, more asset value raises price and more liabilities lowers it. Issuing units at the appropriate price increases both capital and units; it is not itself investment profit. The price then feeds review and simulated distribution; forecast future cash must not replace current ledger cash in NAV.",
    ),
    "swing": (
        "Net investor flow is subscriptions minus redemptions. A swing threshold is the illustrative dealing-flow level at which a price adjustment can activate; the swing factor is the adjustment size in bps. Distribution price means the price sent onward, not a dividend payment here.",
        "Flow % = absolute net flow / NAV × 100. A EUR 3 million net flow against EUR 500 million NAV is 0.60%. A factor of 20 bps equals 0.20%, or EUR 0.20 on a EUR 100 price when applied.",
        "Under the example rule, a triggered inflow raises the dealing price and an outflow lowers it to illustrate allocating transaction costs to dealing investors. Below the trigger, the factor is not applied. This is a pricing-policy illustration, not investment performance or an extra cash receipt.",
    ),
    "cash": (
        "Ledger cash is the book balance now. Subscriptions bring investor money in; redemptions pay it out. Purchases use cash; sales release cash. Posted collateral reduces available cash but is not automatically an expense or loss.",
        "Projected cash = opening cash + subscriptions − redemptions − purchases + sales − collateral. Required buffer = opening cash × reserve %. Headroom = projected cash − buffer. A EUR 1 million opening balance at 2% requires EUR 20,000; a EUR 150,000 forecast leaves EUR 130,000 headroom.",
        "The reserve is a minimum cushion, not another payment. A positive ending headroom passes this aggregate test; dated cash receipts, payments, currencies and restrictions still matter. Receivables and payables need settlement mapping before adding them to avoid double counting. The liquidity ladder helps show timing; NAV still uses ledger cash.",
    ),
    "reporting": (
        "An event row is one reconciliation observation; a unique fund count counts each fund once. Matched means the relevant records agree. Outstanding Active and Outstanding Hold remain open. Open exposure is an amount needing investigation, not an established loss.",
        "Match rate = matched events / all selected events × 100. Automatic share of matched = automatic matches / matched events × 100: the denominator differs. With 80 matched of 100 events and 60 automatic matches, the rates are 80% and 75%. Average open ageing uses only open cases; on-time share uses the selected event population.",
        "A high match rate can coexist with a large unresolved amount. Review count, money, ageing and deadlines together. Exposure / NAV × 10,000 gives bps: EUR 50,000 / EUR 100 million × 10,000 = 5 bps. Filtering changes the population; source-to-visual checks verify displayed totals tie to its detail, not that all source records are correct.",
    ),
    "anomaly": (
        "An anomaly is a record that fires a documented review rule. Observed days are elapsed time; expected days are the reference. Quarantine separates incomplete or invalid records before business scoring.",
        "Score = 0.3 if observed days exceed expected days, plus 0.7 if a calculation conflicts with its rule. Eight observed days versus five expected days gives 0.3; adding a calculation conflict gives 1.0. Missing required data or invalid dates produces no score.",
        "The score routes work to an analyst. It is not a probability, proof of fraud, loss estimate or automatic accounting correction. A zero score means neither of these rules fired, not that the whole record is verified.",
    ),
    "quality": (
        "A quality gate is a required check with a pass/fail result. User Acceptance Testing (UAT) checks that a changed process behaves as intended. A maker prepares a daily result; a separate checker reviews it.",
        "Readiness combines required gates, test outcomes and review evidence with AND: every required condition must pass. Nine passing gates and one failed required gate still mean not ready. A fingerprint links review to a particular evidence package.",
        "UAT validates the process design; daily review validates this run. Changed inputs or dispositions can invalidate earlier review. Selected identities and recorded references illustrate controls; they do not authenticate real people or prove an external approval occurred.",
    ),
    "delivery": (
        "Client submission sends the result to a client; price diffusion distributes the approved fund price to recipients. A cut-off is a deadline. An acknowledgement records receipt, which is separate from checking the financial result.",
        "Timing variance = actual time − cut-off. A 16:52 submission against 17:00 is −8 minutes, on time; 18:05 against 18:00 is +5 minutes, late. Each channel is checked separately.",
        "A correct price can still be delivered late or fail to reach a recipient. Review approval, current version, open queries and recipient status determine the next action. CAM means Client Account Manager and coordinates communication; this portfolio only simulates delivery.",
    ),
    "journal": (
        "A journal records an accounting event using debit and credit entries. These are accounting sides, not universal synonyms for money in and money out. Their effect depends on the account type.",
        "Buying EUR 100,000 of investments for cash debits investments and credits cash: one asset replaces another, so there is no immediate gain from that exchange alone. Accruing a EUR 1,000 fee debits expense and credits a payable: NAV falls while cash remains unchanged until payment.",
        "Total debits must equal total credits; out-of-balance amount is their absolute difference and should be zero. A balanced journal can still use the wrong account or amount. This session ledger is a separate exercise and does not automatically update the valuation lab.",
    ),
    "fees": (
        "A high-water mark is the reference price used to avoid charging the illustrated performance fee again on recovered performance. The hurdle is an additional required return; eligible units are the units to which the fee example applies.",
        "At the default inputs: EUR 105 × 1.02 = EUR 107.10 hurdle-adjusted reference. EUR 112 − EUR 107.10 = EUR 4.90 eligible gain per unit. EUR 4.90 × 100,000 units × 20% = EUR 98,000. Gain below the reference is floored at zero.",
        "A higher reference reduces the eligible gain; a higher fee rate or more eligible units increases the fee. An accrued fee would increase liabilities and reduce NAV, but this isolated calculator does not book it. Real fee periods, crystallisation and governing terms can differ from this simplified method.",
    ),
    "bps": (
        "Basis points (bps) express small percentages: 1 bp = 0.01 percentage point; 100 bps = 1%; 50 bps = 0.50%.",
        "For a separate annual management-fee example: 50 / 10,000 = 0.005; EUR 100,000,000 × 0.005 = EUR 500,000 a year. One percent is EUR 1 million and half of that is EUR 500,000.",
        "The fee base is the amount specified by the fee terms, not automatically cash. A changing daily base changes the total. This annual management-fee example differs from the performance-fee exercise, which charges a percentage of eligible gains.",
    ),
    "records": (
        "Positions show holdings; trade records show purchases and sales; the general ledger holds accounting entries; bank and custody records provide independent cash and asset evidence; the investor register records units and dealing.",
        "A trade confirmation supports what was agreed; a bank movement supports cash settlement. Those are related but different pieces of evidence. Totals must use consistent fund, currency and valuation dates.",
        "These records connect market activity to accounting balances, cash forecasts and price per unit. A missing register or stale price can block a trustworthy valuation even when the arithmetic itself runs.",
    ),
    "pipeline": (
        "A CSV export is a table stored as text. A master table combines parsed rows; lineage retains the source file, upload instance and source row. A potential duplicate repeats business values but is not automatically an error.",
        "Input rows = sum of rows in successfully read files; master rows should equal that sum. Two files with 100 and 50 rows produce 150 master rows. Rejected files are excluded and must be investigated; equal counts alone do not prove every intended file arrived.",
        "Traceability lets an analyst return from a report to its source. Carry-forward fills missing identifiers only within an upload when justified by the source layout; it must not invent an economic amount. Incorrect fills or deduplication can assign events to the wrong fund or remove real activity.",
    ),
    "missing": (
        "NULL or blank means no value was supplied. Zero is an explicit numerical value. Invalid text is a value that cannot be used under the expected numeric format. Quarantine keeps a defective record out of normal calculation.",
        "A blank amount compared with a verified zero is not a confirmed match. Converting the blank to zero would manufacture agreement. A valid 125.40 can be parsed after checking its format and currency.",
        "Preserving missingness keeps the need for investigation visible. Invented zeroes can distort totals, match rates and anomaly scores; source validation comes before business interpretation.",
    ),
    "parser": (
        "A broker confirmation records agreed trade details. Mandatory fields are required by the selected template; mapped payload is the structured output. Field completeness measures presence, not the truth of the supplied values.",
        "Completeness = mandatory fields found / mandatory fields required × 100. Nine of ten is 90%; even 100% can have a chronology or product-rule error. In the futures sample, 40 contracts × 50 contract size = 2,000 underlying units; × 5,410.25 price = USD 10,820,500 notional exposure, not an upfront payment of that amount. An FX swap exchanges currencies on a near date and reverses the exchange on a later far date; the two leg rates can differ.",
        "The parser maps source fields, checks rules and routes exceptions for review. Product direction, currency and dates affect later settlement interpretation. A complete payload is not an approved trade, and this bounded rule parser does not contact a broker or book a transaction.",
    ),
    "calendar": (
        "Valuation frequency says how often a fund values its assets; the approved schedule supplies the expected completion date. Tolerance is the permitted calendar-day delay in this exercise; the actual date may instead be a forecast.",
        "Variance = actual or forecast date − expected date. Completion on 17 September against 16 September is +1 day; with zero tolerance it is late. A negative result means early and requires checking the same valuation cycle is being compared.",
        "A delay can affect review, client submission and price distribution, but does not itself measure a price error. Batch source issues must be corrected before relying on classifications. This exercise uses calendar days, not a full holiday, business-day and intraday cut-off engine.",
    ),
    "chunks": (
        "A chunk is one smaller output CSV. A manifest lists its source-row range and data-row count. Headers describe columns and are excluded from the data-row count.",
        "Output files = input rows / rows per file, rounded up. With 1,050 rows and 200 per file, there are six files: five of 200 rows and one of 50. Their data-row counts must sum to 1,050; the manifest is an additional file.",
        "Sequential ranges make it possible to check no source row was omitted or assigned twice. Splitting helps downstream size limits; it does not validate financial values or remove legitimate repeated rows. A preview plans the split; uploading a file creates downloadable parts.",
    ),
    "routing": (
        "An operating model assigns work, systems and control ownership across teams. A common platform shares a process; a jurisdiction-specific process handles a local requirement. Standardisation means the product and rules fit the shared approach.",
        "The decision is a rule, not a financial score: a mandatory local requirement takes priority; common-platform support plus standardised rules supports the common route. Other combinations need the displayed readiness review.",
        "The proposed route determines who must supply records, own exceptions and review delivery. It does not remove local obligations or prove a platform is ready; the next control identifies what must be checked before adopting the route.",
    ),
    "stp": (
        "Straight-through processing (STP) means records pass through the defined process without manual handling. The rate describes records, not staff or investment returns.",
        "Manual records = daily volume × (1 − STP rate / 100), rounded to whole records. At 10,000 records, 72% STP leaves 2,800 manual records; 90% leaves 1,000, a potential reduction of 1,800. The reduction metric is floored at zero if the target is worse.",
        "Higher automation can reduce manual volume, but difficult exceptions can still dominate effort. This is not a headcount or cost-saving calculation; time per case, quality and control effectiveness would also be needed.",
    ),
    "review": (
        "A run identifies one valuation cycle; its version identifies the current inputs and decisions. The preparer assembles and checks evidence; the independent checker reviews that same package. A fingerprint detects content changes and is not a digital signature.",
        "Review requires the specified source checks and resolved or tolerated run-linked exceptions. Checker approval applies to the prepared version and package; changing accounting inputs or exception dispositions can make the earlier review stale.",
        "Recalculation after a correction can change price, so the old approval must not authorise the new result. The controls connect valuation and reconciliation to guarded distribution. The identities and approvals here are simulated, without real identity authentication.",
    ),
    "resilience": (
        "Backlog is unfinished work after a disruption. Alternate-site capacity is the share of normal work handled during it. Recovery capacity is total capacity after restoration; only the part above new incoming work clears backlog.",
        "At 1,000 items/day for five days and 60% alternate capacity, backlog = 1,000 × 5 × 40% = 2,000. Recovery at 130% handles 1,300/day, leaving 300/day after 1,000 new arrivals. Catch-up = 2,000 / 300 rounded up = seven days.",
        "More spare capacity shortens catch-up; a longer outage increases backlog. Restoring only 100% capacity would not clear it while arrivals continue. This simplified estimate assumes steady volumes and capacity; recovery priorities describe trade-offs but do not change the formula.",
    ),
    "uat": (
        "A delivery gate is a required decision checkpoint backed by evidence. UAT means User Acceptance Testing: business users test expected outcomes. A test ID identifies a case; an evidence reference points to its result.",
        "Gates satisfied counts selected gates with adequate evidence references. All required gates must pass for the displayed readiness result. A passed UAT row must retain evidence; a completion percentage alone does not replace a test outcome.",
        "These registers explain delivery assurance, separately from the daily valuation approval. A reference is a pointer that must be reviewed, not verification of the referenced document. In this standalone exercise, checking delivery gates does not automatically approve the valuation run.",
    ),
    "audit": (
        "The session activity record lists actions, owners, times and scope. A record chain includes fingerprints so changes can be detected when checked; an evidence package collects the current run's records for review.",
        "Compare the exported run ID, version, calculation and decisions together. A later correction can invalidate an earlier approval even if its activity-log entry remains visible.",
        "The log explains how a result was reached; it does not itself reconcile a balance or approve delivery. This browser-session record is mutable and temporary, not an immutable archive or authenticated signature. Download evidence if you need to retain the example.",
    ),
    "stage_gate": (
        "A stage gate controls movement from one delivery phase to the next. Red-Amber-Green (RAG) is a status judgement; an owner is accountable for follow-up, and a blocker is an unresolved dependency.",
        "This simulator permits advancement only with an adequate owner and evidence reference, no blocker, a non-Red status and a remaining next stage. Amber can advance under this rule; Green alone is not enough without evidence.",
        "Advancing records a delivery decision, not production deployment. Protecting quality, date or cost changes the proposed trade-off in scope, capacity or timing; it does not bypass the gates or automatically calculate savings.",
    ),
    "use_cases": (
        "A use case is a proposed business application. Business and technical owners cover the need and implementation. Completion is a user-entered progress estimate; risk describes exposure, while status describes workflow position.",
        "The board counts rows, rows marked Blocked, rows rated High risk and rows marked Ready for decision. Categories can overlap: a high-risk case may also be blocked, so these counts are not parts that must sum to the total.",
        "The board helps prioritise blockers and next actions. Ready for decision is a recorded status, not independently calculated approval. Neither 100% completion nor a low-risk label proves testing, release or deployment has occurred.",
    ),
}


def explain(key: str) -> None:
    """Keep the connection visible and make deeper terminology available locally."""
    terms, calculation, impact = GUIDES[key]
    st.markdown(f"**Business interpretation and operational impact:** {impact}")
    with st.expander("Definitions and calculation methodology"):
        st.markdown(f"**Key definitions:** {terms}")
        st.markdown(f"**Calculation methodology and worked example:** {calculation}")


def explain_events(rows: list[dict]) -> None:
    """Explain the actual displayed population without inventing trade details."""
    if not rows:
        return
    funds = list(dict.fromkeys(row["Fund"] for row in rows))
    matched = sum(row["Reconciliation status"] == "Matched" for row in rows)
    st.markdown("**Fund count and reconciliation event population**")
    st.markdown(
        "Each fund is a distinct entity linked to multiple reconciliation event records. "
        "An event can be matched automatically, reviewed manually, or remain outstanding. "
        "A reconciliation event does not necessarily represent a subscription, redemption or distinct trade. "
        "The dataset does not identify an underlying instrument or trade for every check."
    )
    for fund in funds:
        count = sum(row["Fund"] == fund for row in rows)
        st.markdown(
            f"**{fund}: 1 fund, {count} event rows.** Each event retains the fund reference to identify "
            "the entity whose records are being reconciled. Counting event records measures "
            "reconciliation activity; counting distinct fund identifiers measures funds."
        )
    st.markdown(
        f"**Displayed population:** {len(funds)} distinct fund(s), {len(rows)} reconciliation events, "
        f"{matched} matched and {len(rows) - matched} open. "
        f"Match rate = {matched} / {len(rows)} × 100 = {matched / len(rows) * 100:.2f}%. "
        "Resolving one outstanding event increases the matched count without adding or removing a fund or event. "
        "Filters determine the displayed event population. Six events per fund is the configured sample population, not a prescribed operational limit."
    )
    explanations = {
        "None": "The check matched; no break type is recorded. The source does not specify the underlying trade or holding.",
        "Settlement-date review": "A settlement-date check was reviewed; the current status records whether it is matched.",
        "Settlement-date mismatch": "Records disagree on when payment and delivery should occur; verify the contractual date.",
        "External confirmation pending": "Independent confirmation is still needed before the check can be closed.",
        "Coupon-accrual variance": "Records differ on bond interest earned so far; check the interest period and calculation.",
        "Coupon period verified": "The interest period was checked; the current status records the outcome.",
        "Income receivable": "An amount of investment income due to the fund needs investigation.",
        "Contract-multiplier mismatch": "Records disagree on a contract's size multiplier, which can affect calculated exposure.",
        "Multiplier corrected": "A contract-size multiplier was corrected; the current status records the outcome.",
        "Position difference": "Records disagree on an investment holding; verify quantity and source records.",
    }
    with st.expander("Event-level scope, status and financial exposure"):
        for row in rows:
            kind = row["Break type"]
            meaning = explanations.get(kind, f"A recorded {kind.lower()} check; consult its supporting evidence for the precise cause.")
            st.markdown(
                f"**{row['Event ID']} · {row['Fund']} · {str(row['Event date'])[:10]}** — "
                f"{meaning} **Status:** {row['Reconciliation status']}; "
                f"**match method:** {row['Match method']}; "
                f"**amount under investigation:** EUR {float(row['Amount under investigation (EUR)']):,.2f}."
            )
        st.caption(
            "Zero amount under investigation means no open amount is recorded here; "
            "it does not mean the original trade or investment was worth zero. "
            "A non-zero amount is under review and is not automatically a loss."
        )
