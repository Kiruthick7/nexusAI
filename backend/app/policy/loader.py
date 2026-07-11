"""
Module implementing the reusable corporate policy loader.
Loads YAML configurations from disk, falling back gracefully to robust built-in standards on error.
"""

import os
import yaml
from typing import Dict, Any
from app.core.logger import logger
from app.policy.rules import PolicyRuleConfig

# Path to standard policies configuration
POLICY_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../policies/company_policy.yaml")
)

# Robust fallback controls if disk loader fails
DEFAULT_POLICIES: Dict[str, Dict[str, Any]] = {
    "Travel": {
        "max_amount": 20000.0,
        "receipt_required": True,
        "allowed_currencies": ["INR", "USD", "EUR"],
        "required_fields": ["vendor_name", "date", "amount", "invoice_number"],
        "approval_threshold": 15000.0,
    },
    "Accommodation": {
        "max_amount": 25000.0,
        "receipt_required": True,
        "allowed_currencies": ["INR", "USD", "EUR"],
        "required_fields": ["vendor_name", "date", "amount", "invoice_number"],
        "approval_threshold": 20000.0,
    },
    "Meals": {
        "max_amount": 2500.0,
        "receipt_required": True,
        "allowed_currencies": ["INR", "USD"],
        "required_fields": ["vendor_name", "date", "amount"],
        "approval_threshold": 2000.0,
    },
    "Client Entertainment": {
        "max_amount": 10000.0,
        "receipt_required": True,
        "allowed_currencies": ["INR", "USD"],
        "required_fields": ["vendor_name", "date", "amount"],
        "approval_threshold": 8000.0,
    },
    "Cab": {
        "max_amount": 1500.0,
        "receipt_required": False,
        "allowed_currencies": ["INR", "USD"],
        "required_fields": ["vendor_name", "date", "amount"],
        "approval_threshold": 1000.0,
    },
    "Office Supplies": {
        "max_amount": 5000.0,
        "receipt_required": True,
        "allowed_currencies": ["INR", "USD"],
        "required_fields": ["vendor_name", "date", "amount"],
        "approval_threshold": 4000.0,
    },
    "Medical": {
        "max_amount": 10000.0,
        "receipt_required": True,
        "allowed_currencies": ["INR", "USD"],
        "required_fields": ["vendor_name", "date", "amount"],
        "approval_threshold": 8000.0,
    },
    "Specialist Consultation": {
        "max_amount": 10000.0,
        "receipt_required": True,
        "allowed_currencies": ["INR", "USD"],
        "required_fields": ["vendor_name", "date", "amount"],
        "approval_threshold": 8000.0,
    },
    "Medical/Health": {
        "max_amount": 10000.0,
        "receipt_required": True,
        "allowed_currencies": ["INR", "USD"],
        "required_fields": ["vendor_name", "date", "amount"],
        "approval_threshold": 8000.0,
    },
    "Medical Care": {
        "max_amount": 10000.0,
        "receipt_required": True,
        "allowed_currencies": ["INR", "USD"],
        "required_fields": ["vendor_name", "date", "amount"],
        "approval_threshold": 8000.0,
    },
    "Health Care": {
        "max_amount": 10000.0,
        "receipt_required": True,
        "allowed_currencies": ["INR", "USD"],
        "required_fields": ["vendor_name", "date", "amount"],
        "approval_threshold": 8000.0,
    },
}


def load_policies(file_path: str = POLICY_FILE_PATH) -> Dict[str, PolicyRuleConfig]:
    """
    Reads corporate guidelines from YAML. Falls back to DEFAULT_POLICIES if files are missing or malformed.
    
    Returns:
        Dict[str, PolicyRuleConfig]: Loaded and validated policy model mappings.
    """
    raw_data: Dict[str, Any] = {}
    
    if not os.path.exists(file_path):
        logger.warning(f"[POLICY LOADER] Rules file not found at {file_path}. Activating standard default dictionary fallback.")
        raw_data = DEFAULT_POLICIES
    else:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data or not isinstance(data, dict):
                    logger.warning("[POLICY LOADER] Empty or malformed YAML policy rules document. Activating default fallback.")
                    raw_data = DEFAULT_POLICIES
                else:
                    raw_data = data
                    logger.info(f"[POLICY LOADER] Successfully loaded guidelines for categories: {list(raw_data.keys())} from disk.")
        except Exception as err:
            logger.error(f"[POLICY LOADER] Disk read/parse exception: {str(err)}. Activating standard default dictionary fallback.")
            raw_data = DEFAULT_POLICIES

    # Convert dictionary entries to validated PolicyRuleConfig models
    policies: Dict[str, PolicyRuleConfig] = {}
    for category, fields in raw_data.items():
        try:
            # Normalize category key (e.g. Travel, meals -> title-cased or kept exact)
            # Standardize on exact match or capitalization
            policies[category] = PolicyRuleConfig(**fields)
        except Exception as val_err:
            logger.error(f"[POLICY LOADER] Validation anomaly processing category rules for '{category}': {str(val_err)}")
            # Fallback specifically for this broken category from defaults
            if category in DEFAULT_POLICIES:
                policies[category] = PolicyRuleConfig(**DEFAULT_POLICIES[category])
            else:
                # Absolute minimal fallback
                policies[category] = PolicyRuleConfig(
                    max_amount=5000.0,
                    receipt_required=True,
                    allowed_currencies=["INR", "USD"],
                    required_fields=["vendor_name", "date", "amount"],
                    approval_threshold=4000.0
                )

    return policies
