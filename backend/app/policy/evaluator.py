"""
Module integrating the Policy Rule Engine with the SharedMissionContext.
Sequentially runs checks, emits live SSE telemetry logs, and gathers findings into consolidated Evidence payloads.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List
from app.models.enums import AgentName, Severity, AgentStatus
from app.models.mission_context import SharedMissionContext
from app.models.evidence import Evidence
from app.policy.loader import load_policies
from app.policy.rules import PolicyRuleConfig, PolicyFinding
from app.policy.engine import (
    check_category_registered,
    check_amount_limits,
    check_currency_validity,
    check_receipt_attached,
    check_mandatory_fields,
    check_date_validity,
    check_gstin_requirement
)
from app.core.event_publisher import (
    publish_policy_loading_rules,
    publish_policy_rule_checked
)


class PolicyEvaluator:
    """
    Evaluates claims context facts against enterprise rules using our modular engine.
    """
    def __init__(self):
        # Read default guidelines
        self.policies = load_policies()

    async def evaluate_claim(self, mission_id: str, context: SharedMissionContext) -> Evidence:
        """
        Sequentially runs corporate policies against context facts and returns unified Evidence.
        
        Args:
            mission_id: The active tracking mission identifier.
            context: Compiled SharedMissionContext facts from the Intake Agent.
            
        Returns:
            Evidence: The unified consolidated verification outcome.
        """
        # 1. Publish progressive rules loading telemetry
        await publish_policy_loading_rules(mission_id)
        
        findings: List[PolicyFinding] = []
        
        # 2. Check if category is officially registered
        cat_finding = check_category_registered(context, list(self.policies.keys()))
        findings.append(cat_finding)
        await publish_policy_rule_checked(
            mission_id=mission_id,
            rule=cat_finding.rule,
            result=cat_finding.result,
            details=cat_finding.details
        )
        
        # 3. Retrieve relevant rule config matching category
        category = context.category
        rule_config: Optional[PolicyRuleConfig] = None
        
        if category:
            # Case-insensitive lookup match
            for pol_cat, config in self.policies.items():
                if pol_cat.lower() == category.lower():
                    rule_config = config
                    break
                    
        if not rule_config:
            # Use minimal standard fallback config for basic limit checks
            rule_config = PolicyRuleConfig(
                max_amount=5000.0,
                receipt_required=True,
                allowed_currencies=["INR", "USD"],
                required_fields=["vendor_name", "date", "amount"],
                approval_threshold=4000.0
            )
            
        # 4. Run remaining rule controls sequentially
        # Limit check
        limit_finding = check_amount_limits(context, rule_config)
        findings.append(limit_finding)
        await publish_policy_rule_checked(
            mission_id=mission_id,
            rule=limit_finding.rule,
            result=limit_finding.result,
            details=limit_finding.details
        )
        
        # Currency check
        curr_finding = check_currency_validity(context, rule_config)
        findings.append(curr_finding)
        await publish_policy_rule_checked(
            mission_id=mission_id,
            rule=curr_finding.rule,
            result=curr_finding.result,
            details=curr_finding.details
        )
        
        # Receipt check
        rec_finding = check_receipt_attached(context, rule_config)
        findings.append(rec_finding)
        await publish_rule_checked_helper(mission_id, rec_finding)
        
        # Mandatory fields check
        mnd_finding = check_mandatory_fields(context, rule_config)
        findings.append(mnd_finding)
        await publish_rule_checked_helper(mission_id, mnd_finding)
        
        # Date validity check
        dt_finding = check_date_validity(context)
        findings.append(dt_finding)
        await publish_rule_checked_helper(mission_id, dt_finding)
        
        # GSTIN check
        gst_finding = check_gstin_requirement(context, rule_config)
        findings.append(gst_finding)
        await publish_rule_checked_helper(mission_id, gst_finding)
        
        # 5. Compile aggregate outcomes and establish consolidated severity
        severity = Severity.SUCCESS
        status = AgentStatus.SUCCESS
        description = "Corporate audit complete. Expense transaction is compliant with all policy parameters."
        
        # Determine consolidated severity status based on findings
        hard_fails = [f for f in findings if f.result == "HARD_FAIL"]
        flags = [f for f in findings if f.result == "FLAG"]
        
        if hard_fails:
            severity = Severity.ERROR
            status = AgentStatus.ERROR
            description = f"Corporate audit failed. Transaction violates policy guidelines: {hard_fails[0].details}"
        elif flags:
            severity = Severity.WARN
            status = AgentStatus.WARNING
            description = f"Corporate audit warning flags raised: {flags[0].details}"
            
        # Standardized confidence
        confidence = 100
        if hard_fails:
            confidence = 100
        elif flags:
            confidence = 90
            
        # Serialize findings list for storage in metadata
        serialized_findings = [f.model_dump(mode="json") for f in findings]
        
        evidence = Evidence(
            evidence_id=str(uuid.uuid4()),
            mission_id=mission_id,
            agent=AgentName.POLICY,
            source="rule_engine",
            title="Policy Audit Evaluation Completed",
            description=description,
            confidence=confidence,
            severity=severity,
            timestamp=datetime.now(UTC),
            metadata={
                "category": context.category,
                "amount": context.amount,
                "currency": context.currency,
                "findings": serialized_findings,
                "hard_fail_count": len(hard_fails),
                "flag_count": len(flags),
                "finding": "COMPLIANT" if severity == Severity.SUCCESS else ("REJECTED" if severity == Severity.ERROR else "WARNING")
            }
        )
        
        return evidence


async def publish_rule_checked_helper(mission_id: str, finding: PolicyFinding):
    """
    Sub-utility helping trigger progressive logs cleanly.
    """
    await publish_policy_rule_checked(
        mission_id=mission_id,
        rule=finding.rule,
        result=finding.result,
        details=finding.details
    )


# Singleton evaluator instance
policy_evaluator = PolicyEvaluator()
