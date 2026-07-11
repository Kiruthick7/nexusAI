"""
Module implementing the Pattern Agent's modular behavioral and anomaly detectors.
Provides pure, testable rule checks for duplicates, rapid frequencies, same-day vendor repetition,
weekend transactions, split billing, and near-limit threshold actions.
"""

from datetime import datetime
from typing import List, Dict, Any
from app.models.enums import Severity
from app.pattern.models import PatternFinding


def check_duplicate_invoice(
    current_invoice: str,
    current_amount: float,
    history: List[Dict[str, Any]]
) -> PatternFinding:
    """
    Checks if the active invoice reference matches previous transaction entries.
    
    Identifies direct duplicate claims (identical metadata/sums) or potential invoice
    identifier reuse discrepancies (matching number but conflicting claimed amounts).
    """
    if not current_invoice or current_invoice == "INV-UNKNOWN":
        return PatternFinding(
            pattern_type="duplicate_invoice",
            severity=Severity.SUCCESS,
            result="PASS",
            evidence="Invoice reference identifier is blank or unresolved. Duplicate scan bypassed.",
        )

    for claim in history:
        hist_invoice = claim.get("invoice_number")
        if hist_invoice and hist_invoice.strip().upper() == current_invoice.strip().upper():
            # Match found! Now determine if amounts match or differ
            hist_amount = claim.get("amount", 0.0)
            if abs(hist_amount - current_amount) < 1e-4:
                return PatternFinding(
                    pattern_type="duplicate_invoice",
                    severity=Severity.ERROR,
                    result="HARD_FAIL",
                    evidence=f"Duplicate transaction detected. Invoice number '{current_invoice}' was already claimed in transaction {claim.get('claim_id')} on {claim.get('date')} for {claim.get('currency')} {hist_amount}.",
                    supporting_claims=[claim],
                )
            else:
                return PatternFinding(
                    pattern_type="duplicate_invoice_hash_collision",
                    severity=Severity.ERROR,
                    result="HARD_FAIL",
                    evidence=f"Invoice identifier reuse discrepancy detected. Invoice number '{current_invoice}' was previously claimed in {claim.get('claim_id')} with a conflicting amount of {claim.get('currency')} {hist_amount} (Current: {current_amount}). Possible billing manipulation risk.",
                    supporting_claims=[claim],
                )

    return PatternFinding(
        pattern_type="duplicate_invoice",
        severity=Severity.SUCCESS,
        result="PASS",
        evidence=f"No duplicate matches or collision patterns detected for invoice '{current_invoice}' in historical database.",
    )


def check_claim_frequency(
    current_date_str: str,
    history: List[Dict[str, Any]]
) -> PatternFinding:
    """
    Checks if the member is submitting expense claims at an anomalous frequency.
    
    Triggers a warning if an employee registers more than 3 claims in a rolling 7-day window.
    """
    if not current_date_str:
        return PatternFinding(
            pattern_type="rapid_frequency_pattern",
            severity=Severity.SUCCESS,
            result="PASS",
            evidence="No claim transaction date available. Frequency heuristic bypassed.",
        )

    try:
        current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    except Exception:
        return PatternFinding(
            pattern_type="rapid_frequency_pattern",
            severity=Severity.SUCCESS,
            result="PASS",
            evidence=f"Invalid date format '{current_date_str}'. Frequency heuristic bypassed.",
        )

    # Filter historical claims in rolling 7-day period [current_date - 6 days, current_date]
    rolling_claims = []
    for claim in history:
        hist_date_str = claim.get("date")
        if not hist_date_str:
            continue
        try:
            hist_date = datetime.strptime(hist_date_str, "%Y-%m-%d").date()
            delta_days = (current_date - hist_date).days
            if 0 <= delta_days < 7:
                rolling_claims.append(claim)
        except Exception:
            continue

    total_claims_in_window = len(rolling_claims) + 1  # Include current claim
    if total_claims_in_window > 3:
        return PatternFinding(
            pattern_type="rapid_frequency_pattern",
            severity=Severity.WARN,
            result="FLAG",
            evidence=f"High-frequency claim anomaly. Employee submitted {total_claims_in_window} transactions within a rolling 7-day period (maximum allowed guideline threshold: 3).",
            supporting_claims=rolling_claims,
        )

    return PatternFinding(
        pattern_type="rapid_frequency_pattern",
        severity=Severity.SUCCESS,
        result="PASS",
        evidence=f"Normal claim frequency verified. Count within rolling 7-day window is {total_claims_in_window} (guideline threshold: <= 3).",
    )


def check_vendor_anomaly(
    current_date_str: str,
    current_vendor: str,
    history: List[Dict[str, Any]]
) -> PatternFinding:
    """
    Flags duplicate submissions filed against the same provider/vendor on the same day.
    """
    if not current_date_str or not current_vendor:
        return PatternFinding(
            pattern_type="same_day_vendor_repetition",
            severity=Severity.SUCCESS,
            result="PASS",
            evidence="Missing transaction date or vendor descriptor. Repetition check bypassed.",
        )

    matched_claims = []
    for claim in history:
        hist_date = claim.get("date")
        hist_vendor = claim.get("vendor_name")
        if (
            hist_date == current_date_str
            and hist_vendor
            and hist_vendor.strip().lower() == current_vendor.strip().lower()
        ):
            matched_claims.append(claim)

    if matched_claims:
        return PatternFinding(
            pattern_type="same_day_vendor_repetition",
            severity=Severity.WARN,
            result="FLAG",
            evidence=f"Same-day provider repetition flagged. Employee filed {len(matched_claims) + 1} claims for vendor '{current_vendor}' on the same date ({current_date_str}).",
            supporting_claims=matched_claims,
        )

    return PatternFinding(
        pattern_type="same_day_vendor_repetition",
        severity=Severity.SUCCESS,
        result="PASS",
        evidence=f"No other same-day transactions identified for vendor '{current_vendor}'.",
    )


def check_weekend_submission(current_date_str: str) -> PatternFinding:
    """
    Identifies corporate claim transactions executed on weekends (Saturday/Sunday).
    """
    if not current_date_str:
        return PatternFinding(
            pattern_type="weekend_activity",
            severity=Severity.SUCCESS,
            result="PASS",
            evidence="Date parameter absent. Weekend check bypassed.",
        )

    try:
        date_obj = datetime.strptime(current_date_str, "%Y-%m-%d").date()
        # Saturday=5, Sunday=6
        weekday = date_obj.weekday()
        if weekday in (5, 6):
            day_name = "Saturday" if weekday == 5 else "Sunday"
            return PatternFinding(
                pattern_type="weekend_activity",
                severity=Severity.WARN,
                result="FLAG",
                evidence=f"Weekend transaction anomaly. This expense occurred on a weekend ({day_name}, {current_date_str}), which deviates from standard business week cycles.",
            )
        else:
            return PatternFinding(
                pattern_type="weekend_activity",
                severity=Severity.SUCCESS,
                result="PASS",
                evidence=f"Transaction executed during typical weekday operations ({date_obj.strftime('%A')}, {current_date_str}).",
            )
    except Exception:
        return PatternFinding(
            pattern_type="weekend_activity",
            severity=Severity.SUCCESS,
            result="PASS",
            evidence=f"Invalid date format '{current_date_str}'. Weekend activity check bypassed.",
        )


def check_split_billing(
    current_date_str: str,
    current_vendor: str,
    current_amount: float,
    current_category: str,
    history: List[Dict[str, Any]],
    max_amount: float
) -> PatternFinding:
    """
    Detects split billing behavior.
    
    Checks if multiple transactions submitted on the same day for the same vendor are each
    individually compliant but collectively exceed the single reimbursement threshold limit.
    """
    if not current_date_str or not current_vendor or not current_amount or not current_category:
        return PatternFinding(
            pattern_type="split_billing_pattern",
            severity=Severity.SUCCESS,
            result="PASS",
            evidence="Incomplete transaction details. Split-billing scan bypassed.",
        )

    # Filter same-day, same-vendor, same-category claims in history
    matched_claims = []
    for claim in history:
        hist_date = claim.get("date")
        hist_vendor = claim.get("vendor_name")
        hist_category = claim.get("category")
        if (
            hist_date == current_date_str
            and hist_vendor
            and hist_vendor.strip().lower() == current_vendor.strip().lower()
            and hist_category
            and hist_category.strip().lower() == current_category.strip().lower()
        ):
            matched_claims.append(claim)

    if not matched_claims:
        return PatternFinding(
            pattern_type="split_billing_pattern",
            severity=Severity.SUCCESS,
            result="PASS",
            evidence=f"No other same-day, same-vendor claims found for '{current_vendor}'. Split-billing pattern cleared.",
        )

    # Verify if every single transaction is individually under or equal to max_amount
    is_individual_compliant = current_amount <= max_amount and all(
        c.get("amount", 0.0) <= max_amount for c in matched_claims
    )

    # Sum matching items
    total_sum = current_amount + sum(c.get("amount", 0.0) for c in matched_claims)

    if is_individual_compliant and total_sum > max_amount:
        return PatternFinding(
            pattern_type="split_billing_pattern",
            severity=Severity.ERROR,
            result="HARD_FAIL",
            evidence=f"Split-billing violation flagged. Employee submitted {len(matched_claims) + 1} same-day, same-vendor claims under category '{current_category}'. While each individual transaction (Current: {current_amount}) falls under the single reimbursement limit ({max_amount}), the cumulative total sum is {total_sum}, exceeding the corporate threshold. Possible limit-evasion pattern.",
            supporting_claims=matched_claims,
        )

    return PatternFinding(
        pattern_type="split_billing_pattern",
        severity=Severity.SUCCESS,
        result="PASS",
        evidence=f"Same-day cumulative sum with vendor '{current_vendor}' is {total_sum} (Category limit: {max_amount}). Split-billing pattern cleared.",
    )


def check_near_limit(
    current_amount: float,
    max_amount: float
) -> PatternFinding:
    """
    Flags claim amounts that sit suspiciously close to the category reimbursement ceiling.
    
    Flags transaction items that are within 95% to 100% of the maximum limit.
    """
    if not current_amount or not max_amount or max_amount <= 0.0:
        return PatternFinding(
            pattern_type="near_limit_activity",
            severity=Severity.SUCCESS,
            result="PASS",
            evidence="Incomplete amount parameters. Near-limit evaluation bypassed.",
        )

    threshold = 0.95 * max_amount
    if threshold <= current_amount <= max_amount:
        percent = (current_amount / max_amount) * 100
        return PatternFinding(
            pattern_type="near_limit_activity",
            severity=Severity.WARN,
            result="FLAG",
            evidence=f"Near-limit ceiling flagged. Claim of {current_amount} sits at {percent:.1f}% of the maximum allowable limit ({max_amount}) for this category. High risk of padded billing.",
        )

    return PatternFinding(
        pattern_type="near_limit_activity",
        severity=Severity.SUCCESS,
        result="PASS",
        evidence=f"Claim of {current_amount} is safely below the near-limit zone (< 95% of category threshold {max_amount}).",
    )
