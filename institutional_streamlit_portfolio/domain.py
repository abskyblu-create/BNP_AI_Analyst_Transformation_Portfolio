"""Pure domain calculations for the synthetic finance-control simulator."""

from __future__ import annotations

from datetime import date
import hashlib
import json
import math
import re
from typing import Any


def _finite_non_negative(**values: float) -> None:
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("All financial inputs must be finite numbers.")
    invalid = [name for name, value in values.items() if value < 0]
    if invalid:
        raise ValueError(f"These inputs cannot be negative: {', '.join(invalid)}.")


def cash_forecast(
    opening_cash: float,
    subscriptions: float,
    redemptions: float,
    purchase_settlements: float,
    sale_settlements: float,
    collateral: float,
    minimum_buffer_percent: float,
) -> dict[str, float | str]:
    """Project settled cash after known investor and market movements."""
    _finite_non_negative(
        opening_cash=opening_cash,
        subscriptions=subscriptions,
        redemptions=redemptions,
        purchase_settlements=purchase_settlements,
        sale_settlements=sale_settlements,
        collateral=collateral,
        minimum_buffer_percent=minimum_buffer_percent,
    )
    if minimum_buffer_percent > 100:
        raise ValueError("The minimum cash buffer cannot exceed 100%.")
    projected = (
        opening_cash
        + subscriptions
        - redemptions
        - purchase_settlements
        + sale_settlements
        - collateral
    )
    required = opening_cash * minimum_buffer_percent / 100
    headroom = projected - required
    status = "Sufficient" if headroom >= 0 else "Below policy buffer"
    if projected < 0:
        status = "Projected overdraft"
    return {
        "projected_cash": projected,
        "required_buffer": required,
        "buffer_headroom": headroom,
        "status": status,
    }


def daily_fee_accrual(net_assets: float, annual_basis_points: float, days_in_year: int = 365) -> float:
    _finite_non_negative(net_assets=net_assets, annual_basis_points=annual_basis_points)
    if days_in_year not in (360, 365, 366):
        raise ValueError("Days in year must be 360, 365 or 366.")
    return net_assets * annual_basis_points / 10_000 / days_in_year


def performance_fee(
    current_nav_per_unit: float,
    high_water_mark: float,
    hurdle_rate_percent: float,
    performance_fee_rate_percent: float,
    units: float,
) -> dict[str, float]:
    _finite_non_negative(
        current_nav_per_unit=current_nav_per_unit,
        high_water_mark=high_water_mark,
        hurdle_rate_percent=hurdle_rate_percent,
        performance_fee_rate_percent=performance_fee_rate_percent,
        units=units,
    )
    hurdle_level = high_water_mark * (1 + hurdle_rate_percent / 100)
    eligible_per_unit = max(0.0, current_nav_per_unit - hurdle_level)
    fee = eligible_per_unit * units * performance_fee_rate_percent / 100
    return {"hurdle_level": hurdle_level, "eligible_gain_per_unit": eligible_per_unit, "fee": fee}


JOURNAL_TEMPLATES = {
    "Purchase an investment using cash": (
        ("Investment assets", "Debit", "Recognize the acquired investment"),
        ("Cash", "Credit", "Recognize the cash paid at settlement"),
    ),
    "Recognize dividend income receivable": (
        ("Dividend receivable", "Debit", "Recognize the amount due to the fund"),
        ("Dividend income", "Credit", "Recognize income earned by the fund"),
    ),
    "Accrue the management fee": (
        ("Management-fee expense", "Debit", "Recognize the expense for the valuation period"),
        ("Management-fee payable", "Credit", "Recognize the unpaid obligation"),
    ),
    "Record an investor subscription": (
        ("Cash or subscription receivable", "Debit", "Recognize cash received or due"),
        ("Investor capital", "Credit", "Recognize the increase in fund capital"),
    ),
    "Record an investor redemption": (
        ("Investor capital", "Debit", "Recognize the reduction in fund capital"),
        ("Redemption payable", "Credit", "Recognize the obligation to the redeeming investor"),
    ),
}


def journal_entry(transaction: str, amount: float, reference: str) -> list[dict[str, Any]]:
    if transaction not in JOURNAL_TEMPLATES:
        raise ValueError("Unknown journal transaction type.")
    _finite_non_negative(amount=amount)
    if amount == 0:
        raise ValueError("Journal amount must be greater than zero.")
    lines = []
    for account, side, explanation in JOURNAL_TEMPLATES[transaction]:
        lines.append(
            {
                "Reference": reference,
                "Transaction": transaction,
                "General ledger account": account,
                "Debit (EUR)": amount if side == "Debit" else 0.0,
                "Credit (EUR)": amount if side == "Credit" else 0.0,
                "Accounting explanation": explanation,
            }
        )
    return lines


def anomaly_assessment(
    source_complete: bool,
    dates_valid: bool,
    observed_days: int,
    expected_days: int,
    calculation_conflict: bool,
) -> dict[str, Any]:
    if observed_days < 0 or expected_days < 0:
        raise ValueError("Elapsed-day inputs cannot be negative.")
    if not source_complete or not dates_valid:
        reasons = []
        if not source_complete:
            reasons.append("required source value is missing")
        if not dates_valid:
            reasons.append("date value or chronology is invalid")
        return {"route": "Data-quality quarantine", "score": None, "band": "Not scored", "reasons": reasons}
    elapsed_exception = observed_days > expected_days
    score = (0.3 if elapsed_exception else 0.0) + (0.7 if calculation_conflict else 0.0)
    band = {0.0: "Normal", 0.3: "Review elapsed timing", 0.7: "Review calculation", 1.0: "Urgent analyst review"}[score]
    reasons = []
    if elapsed_exception:
        reasons.append(f"observed {observed_days} days exceeds expected {expected_days} days")
    if calculation_conflict:
        reasons.append("calculation conflicts with the documented business rule")
    return {"route": "Business anomaly assessment", "score": score, "band": band, "reasons": reasons or ["no anomaly rule fired"]}


def chunk_plan(total_rows: int, rows_per_chunk: int) -> list[dict[str, int | str]]:
    if total_rows <= 0 or rows_per_chunk <= 0:
        raise ValueError("Row count and chunk size must be greater than zero.")
    chunks = []
    for index, start in enumerate(range(1, total_rows + 1, rows_per_chunk), start=1):
        end = min(total_rows, start + rows_per_chunk - 1)
        chunks.append({"Chunk": f"part_{index:03d}", "First source row": start, "Last source row": end, "Data rows": end - start + 1})
    return chunks


def operating_model_route(common_platform_ready: bool, local_rule_requires_dedicated_process: bool, product_standardized: bool) -> dict[str, str]:
    if local_rule_requires_dedicated_process:
        return {"model": "Jurisdiction-specific local model", "reason": "A local legal, tax or market requirement needs a dedicated process.", "next_control": "Document the local requirement and global oversight arrangement."}
    if common_platform_ready and product_standardized:
        return {"model": "Global standardized model", "reason": "The product and jurisdiction are supported by the common platform and control framework.", "next_control": "Confirm fund setup, service-level cut-offs and accountable production team."}
    return {"model": "Transition assessment required", "reason": "The common platform or product configuration is not fully ready, but no mandatory local exception was identified.", "next_control": "Complete a documented gap assessment before assigning the operating model."}


def valuation_fingerprint(context: dict[str, Any], inputs: dict[str, Any], results: dict[str, Any]) -> str:
    canonical = json.dumps({"context": context, "inputs": inputs, "results": results}, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_pairs(text: str) -> tuple[dict[str, str], dict[str, str], list[str]]:
    pairs: dict[str, str] = {}
    source_tokens: dict[str, str] = {}
    duplicates: list[str] = []
    for token in re.split(r"[;\n]+", text):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        normalized_key = key.strip().upper()
        if normalized_key in pairs:
            duplicates.append(normalized_key)
        pairs[normalized_key] = value.strip()
        source_tokens[normalized_key] = token.strip()
    return pairs, source_tokens, duplicates


def parse_confirmation(text: str, product: str) -> dict[str, Any]:
    """Deterministic demonstration parser. It does not call an AI model."""
    raw, source_tokens, duplicates = _parse_pairs(text)
    duplicate_errors = [f"Duplicate source field: {field}." for field in sorted(set(duplicates))]
    if product == "Exchange-Traded Derivative future":
        required = ["REFERENCE", "TRADE_DATE", "SETTLEMENT_DATE", "INSTRUMENT", "CONTRACTS", "CONTRACT_SIZE", "PRICE", "CURRENCY", "DIRECTION"]
        missing = [field for field in required if not raw.get(field)]
        mapped: dict[str, Any] = {field.lower(): raw.get(field) for field in required}
        errors = duplicate_errors.copy()
        try:
            mapped["contracts"] = int(raw["CONTRACTS"])
            mapped["contract_size"] = int(raw["CONTRACT_SIZE"])
            mapped["price"] = float(raw["PRICE"])
            if mapped["contracts"] <= 0 or mapped["contract_size"] <= 0 or mapped["price"] <= 0:
                errors.append("Contracts, contract size and price must be positive.")
            mapped["underlying_units"] = mapped["contracts"] * mapped["contract_size"]
            mapped["notional"] = mapped["underlying_units"] * mapped["price"]
        except (KeyError, ValueError):
            errors.append("Contract quantity, size or price is not numeric.")
        if raw.get("DIRECTION") not in {"BUY", "SELL"}:
            errors.append("Direction must be BUY or SELL.")
        if not re.fullmatch(r"[A-Z]{3}", raw.get("CURRENCY", "")):
            errors.append("Currency must be a three-letter uppercase code.")
        try:
            trade_date = date.fromisoformat(raw["TRADE_DATE"])
            settlement_date = date.fromisoformat(raw["SETTLEMENT_DATE"])
            if settlement_date < trade_date:
                errors.append("Settlement date cannot precede trade date.")
        except (KeyError, ValueError):
            errors.append("Trade and settlement dates must use valid YYYY-MM-DD dates.")
    elif product == "Foreign-exchange swap":
        required = ["REFERENCE", "TRADE_DATE", "NEAR_DIRECTION", "NEAR_CURRENCY", "NEAR_AMOUNT", "NEAR_RATE", "NEAR_DATE", "FAR_DIRECTION", "FAR_CURRENCY", "FAR_AMOUNT", "FAR_RATE", "FAR_DATE"]
        missing = [field for field in required if not raw.get(field)]
        mapped = {field.lower(): raw.get(field) for field in required}
        errors = duplicate_errors.copy()
        try:
            near_amount, far_amount = float(raw["NEAR_AMOUNT"]), float(raw["FAR_AMOUNT"])
            near_rate, far_rate = float(raw["NEAR_RATE"]), float(raw["FAR_RATE"])
            mapped.update(near_amount=near_amount, far_amount=far_amount, near_rate=near_rate, far_rate=far_rate)
            if near_amount <= 0 or far_amount <= 0 or near_rate <= 0 or far_rate <= 0:
                errors.append("Leg amounts and rates must be positive.")
            if near_amount != far_amount:
                errors.append("Near-leg and far-leg base-currency amounts do not agree.")
        except (KeyError, ValueError):
            errors.append("Leg amount or rate is not numeric.")
        if raw.get("NEAR_DIRECTION") not in {"BUY", "SELL"} or raw.get("FAR_DIRECTION") not in {"BUY", "SELL"}:
            errors.append("Both leg directions must be BUY or SELL.")
        elif raw.get("NEAR_DIRECTION") == raw.get("FAR_DIRECTION"):
            errors.append("Near and far legs must have opposite base-currency directions.")
        currencies = [raw.get("NEAR_CURRENCY", ""), raw.get("FAR_CURRENCY", "")]
        if any(not re.fullmatch(r"[A-Z]{3}", currency) for currency in currencies):
            errors.append("Both currencies must use three-letter uppercase codes.")
        elif currencies[0] != currencies[1]:
            errors.append("Near and far legs must identify the same base currency.")
        try:
            trade_date = date.fromisoformat(raw["TRADE_DATE"])
            near_date = date.fromisoformat(raw["NEAR_DATE"])
            far_date = date.fromisoformat(raw["FAR_DATE"])
            if near_date < trade_date:
                errors.append("Near-leg settlement date cannot precede trade date.")
            if far_date <= near_date:
                errors.append("Far-leg settlement date must be after the near-leg date.")
        except (KeyError, ValueError):
            errors.append("Trade and settlement dates must use valid YYYY-MM-DD dates.")
    else:
        raise ValueError("Unknown confirmation product type.")
    evidence = [{"Target field": field.lower(), "Source token": source_tokens.get(field, "<missing>"), "Status": "Found" if field not in missing else "Missing"} for field in required]
    confidence = round((len(required) - len(missing)) / len(required) * 100, 1)
    route = "Eligible for human approval" if not missing and not errors else "Human exception review"
    return {"mapped": mapped, "missing": missing, "errors": errors, "evidence": evidence, "confidence": confidence, "route": route}
