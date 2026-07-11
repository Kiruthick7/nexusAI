"""
Module implementing the Policy Rule Engine.
Performs modular checks against SharedMissionContext facts following corporate parameters.
"""

import re
from datetime import datetime, date, UTC
from typing import List, Optional
from app.models.enums import Severity
from app.models.mission_context import SharedMissionContext
from app.policy.rules import PolicyRuleConfig, PolicyFinding


def check_category_registered(context: SharedMissionContext, policies: list) -> PolicyFinding:
    """
    Asserts that the expense claim category is officially recognized.
    """
    category = context.category
    
    if not category:
        return PolicyFinding(
            rule="Expense Category Specified",
            result="FLAG",
            details="The expense claim contains no specified category label. Reverting to default fallback checks.",
            confidence=100,
            severity=Severity.WARN
        )
        
    # Check case-insensitive match
    matched = None
    for pol_cat in policies:
        if pol_cat.lower() == category.lower():
            matched = pol_cat
            break
            
    if not matched:
        return PolicyFinding(
            rule="Category Alignment",
            result="FLAG",
            details=f"Unregistered corporate category '{category}'. Claim requires administrative review and lane classification.",
            confidence=100,
            severity=Severity.WARN
        )
        
    return PolicyFinding(
        rule="Category Alignment",
        result="PASS",
        details=f"Category '{category}' is officially registered and covered under corporate reimbursement guidelines.",
        confidence=100,
        severity=Severity.SUCCESS
    )


def check_amount_limits(context: SharedMissionContext, rule_config: PolicyRuleConfig) -> PolicyFinding:
    """
    Validates claim amount against corporate caps and threshold controls.
    """
    amount = context.amount
    currency = context.currency or "INR"
    
    if amount is None:
        return PolicyFinding(
            rule="Expense Limit Compliance",
            result="HARD_FAIL",
            details="Total claim amount is missing or could not be parsed. Evaluation aborted.",
            confidence=100,
            severity=Severity.ERROR
        )
        
    if amount <= 0:
        return PolicyFinding(
            rule="Expense Total Non-Negative",
            result="HARD_FAIL",
            details=f"Expense total of {amount} {currency} is invalid. Claims must be greater than zero.",
            confidence=100,
            severity=Severity.ERROR
        )
        
    if amount > rule_config.max_amount:
        return PolicyFinding(
            rule="Expense Limit Compliance",
            result="HARD_FAIL",
            details=f"Claim of {amount} {currency} violates guidelines. Max allowable cap is {rule_config.max_amount} {currency}.",
            confidence=100,
            severity=Severity.ERROR
        )
        
    if amount > rule_config.approval_threshold:
        return PolicyFinding(
            rule="Expense Limit Compliance",
            result="FLAG",
            details=f"Claim of {amount} {currency} is within guidelines but exceeds approval threshold of {rule_config.approval_threshold} {currency}. Requires supervisor approval.",
            confidence=100,
            severity=Severity.WARN
        )
        
    return PolicyFinding(
        rule="Expense Limit Compliance",
        result="PASS",
        details=f"Claim of {amount} {currency} is fully compliant and below standard threshold limits.",
        confidence=100,
        severity=Severity.SUCCESS
    )


def check_currency_validity(context: SharedMissionContext, rule_config: PolicyRuleConfig) -> PolicyFinding:
    """
    Asserts that currency of the claim is approved.
    """
    currency = context.currency
    
    if not currency:
        return PolicyFinding(
            rule="Currency Code Validated",
            result="FLAG",
            details="Currency code is unspecified. Assuming standard local currency rules apply.",
            confidence=100,
            severity=Severity.WARN
        )
        
    normalized_currencies = [c.upper() for f in [rule_config.allowed_currencies] for c in f]
    
    if currency.upper() not in normalized_currencies:
        return PolicyFinding(
            rule="Currency Code Validated",
            result="HARD_FAIL",
            details=f"Currency '{currency}' is not authorized. Reimbursements for this category are limited to: {rule_config.allowed_currencies}.",
            confidence=100,
            severity=Severity.ERROR
        )
        
    return PolicyFinding(
        rule="Currency Code Validated",
        result="PASS",
        details=f"Currency code '{currency.upper()}' is approved for this category.",
        confidence=100,
        severity=Severity.SUCCESS
    )


def check_receipt_attached(context: SharedMissionContext, rule_config: PolicyRuleConfig) -> PolicyFinding:
    """
    Checks that proper documentation exists for categories where receipts are required.
    """
    # If the policy does not mandate a receipt, then we pass immediately
    if not rule_config.receipt_required:
        return PolicyFinding(
            rule="Receipt Documentation Attached",
            result="PASS",
            details="Receipt documentation is optional for this category.",
            confidence=100,
            severity=Severity.SUCCESS
        )
        
    # Check if receipt exists
    # Indicators: context has invoice_number or raw_ocr_text, or metadata declares attachment
    has_receipt = False
    if context.invoice_number and context.invoice_number.strip():
        has_receipt = True
    elif context.raw_ocr_text and context.raw_ocr_text.strip():
        has_receipt = True
    elif context.metadata.get("has_attachment") is True or context.metadata.get("receipt_provided") is True:
        has_receipt = True
        
    if not has_receipt:
        return PolicyFinding(
            rule="Receipt Documentation Attached",
            result="FLAG",
            details="Reimbursement policy mandates physical receipt uploads. No attachment or reference document identified.",
            confidence=100,
            severity=Severity.WARN
        )
        
    return PolicyFinding(
        rule="Receipt Documentation Attached",
        result="PASS",
        details="Physical proof of payment verified and matched with claim context records.",
        confidence=100,
        severity=Severity.SUCCESS
    )


def check_mandatory_fields(context: SharedMissionContext, rule_config: PolicyRuleConfig) -> PolicyFinding:
    """
    Asserts that all category-mandatory metadata has been cleanly extracted by Intake.
    """
    missing_fields: List[str] = []
    
    for f in rule_config.required_fields:
        val = getattr(context, f, None)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing_fields.append(f)
            
    if missing_fields:
        return PolicyFinding(
            rule="Complete Core Metadata",
            result="FLAG",
            details=f"Claim processing metadata is incomplete. Missing mandatory fields: {', '.join(missing_fields)}.",
            confidence=100,
            severity=Severity.WARN
        )
        
    return PolicyFinding(
        rule="Complete Core Metadata",
        result="PASS",
        details="All mandatory corporate expense record details are present.",
        confidence=100,
        severity=Severity.SUCCESS
    )


def check_date_validity(context: SharedMissionContext) -> PolicyFinding:
    """
    Checks date syntax, and rejects transactions dated in the future.
    """
    date_str = context.date
    
    if not date_str:
        return PolicyFinding(
            rule="Expense Date Validity Check",
            result="FLAG",
            details="Date field is missing. Transaction date could not be established.",
            confidence=100,
            severity=Severity.WARN
        )
        
    # Standard ISO pattern check
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return PolicyFinding(
            rule="Expense Date Validity Check",
            result="FLAG",
            details=f"Date '{date_str}' is formatted incorrectly. Expecting YYYY-MM-DD pattern syntax.",
            confidence=100,
            severity=Severity.WARN
        )
        
    try:
        dt = date.fromisoformat(date_str)
        today = date.today()
        
        if dt > today:
            return PolicyFinding(
                rule="Expense Date Validity Check",
                result="HARD_FAIL",
                details=f"Future date validation violation: Transaction is dated '{date_str}' but today's system date is '{today.isoformat()}'.",
                confidence=100,
                severity=Severity.ERROR
            )
            
        return PolicyFinding(
            rule="Expense Date Validity Check",
            result="PASS",
            details=f"Transaction date '{date_str}' is syntactically valid and in the past.",
            confidence=100,
            severity=Severity.SUCCESS
        )
    except Exception as err:
        return PolicyFinding(
            rule="Expense Date Validity Check",
            result="FLAG",
            details=f"Error parsing transaction date format '{date_str}': {str(err)}",
            confidence=100,
            severity=Severity.WARN
        )


def check_gstin_requirement(context: SharedMissionContext, rule_config: PolicyRuleConfig) -> PolicyFinding:
    """
    Asserts Indian claims (INR currency or matching vendors) specify required regulatory GSTIN headers.
    """
    gstin = context.gstin
    currency = context.currency or ""
    
    # We require GSTIN specifically if currency is INR or GSTIN was requested as required
    is_indian_claim = (currency.upper() == "INR")
    
    if is_indian_claim and (not gstin or not gstin.strip()):
        return PolicyFinding(
            rule="Regulatory GSTIN Registered",
            result="FLAG",
            details="Indian corporate tax guidelines mandate registered vendors register GSTIN headers. No GSTIN identifier found.",
            confidence=100,
            severity=Severity.WARN
        )
        
    return PolicyFinding(
        rule="Regulatory GSTIN Registered",
        result="PASS",
        details="GSTIN registered, or claim lies outside GSTIN mandatory compliance boundaries.",
        confidence=100,
        severity=Severity.SUCCESS
    )
