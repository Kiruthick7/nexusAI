"""
Module implementing the Evidence Aggregator for the Arbiter Decision Engine.
Consolidates evidence findings, checks for completeness, logs sources, and guarantees crash resilience.
"""

import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional
from app.models.evidence_bundle import EvidenceBundle
from app.models.evidence import Evidence
from app.models.enums import AgentName, Severity
from app.core.logger import logger


class EvidenceAggregator:
    """
    Consolidates parallel specialist reports from EvidenceBundle.
    Ensures safe, graceful handling of missing or incomplete evidence.
    """

    @classmethod
    def aggregate(cls, bundle: EvidenceBundle) -> Dict[str, Any]:
        """
        Gathers evidence from all specialists, tracks sources, latency, and fills in missing blocks.
        
        Args:
            bundle: Consolidated EvidenceBundle from the Planner.
            
        Returns:
            Dict[str, Any] containing aggregated list of active findings, sources, and missing warnings.
        """
        logger.info(f"[ARBITER AGGREGATOR] Commencing evidence aggregation for mission_id={bundle.mission_id}")
        
        findings: List[Evidence] = []
        sources: List[str] = []
        missing_specialists: List[str] = []
        latencies: Dict[str, Optional[int]] = {}
        
        # 1. Harvest Provider Findings
        if bundle.provider_findings:
            findings.append(bundle.provider_findings)
            sources.append(bundle.provider_findings.source)
            # Fetch latency if present in metadata
            lat_val = bundle.provider_findings.metadata.get("latency_ms") if bundle.provider_findings.metadata else None
            latencies["ProviderAgent"] = lat_val
        else:
            missing_specialists.append("ProviderAgent")
            logger.warning(f"[ARBITER AGGREGATOR] ProviderAgent evidence is missing from bundle for mission_id={bundle.mission_id}")

        # 2. Harvest Policy Findings
        if bundle.policy_findings:
            findings.append(bundle.policy_findings)
            sources.append(bundle.policy_findings.source)
            lat_val = bundle.policy_findings.metadata.get("latency_ms") if bundle.policy_findings.metadata else None
            latencies["PolicyAgent"] = lat_val
        else:
            missing_specialists.append("PolicyAgent")
            logger.warning(f"[ARBITER AGGREGATOR] PolicyAgent evidence is missing from bundle for mission_id={bundle.mission_id}")

        # 3. Harvest Pattern Findings
        if bundle.pattern_findings:
            findings.append(bundle.pattern_findings)
            sources.append(bundle.pattern_findings.source)
            lat_val = bundle.pattern_findings.metadata.get("latency_ms") if bundle.pattern_findings.metadata else None
            latencies["PatternAgent"] = lat_val
        else:
            missing_specialists.append("PatternAgent")
            logger.warning(f"[ARBITER AGGREGATOR] PatternAgent evidence is missing from bundle for mission_id={bundle.mission_id}")

        # 4. Handle Missing Critical Elements gracefully to prevent crashes
        missing_warnings: List[Evidence] = []
        for agent_name in missing_specialists:
            enum_agent = AgentName.PROVIDER
            if agent_name == "PolicyAgent":
                enum_agent = AgentName.POLICY
            elif agent_name == "PatternAgent":
                enum_agent = AgentName.PATTERN

            dummy_warning_evidence = Evidence(
                evidence_id=str(uuid.uuid4()),
                mission_id=bundle.mission_id,
                agent=enum_agent,
                source="aggregator_fallback",
                title="Evidence Missing",
                description=f"Adjudication pipeline executed without {agent_name} results.",
                confidence=0,
                severity=Severity.WARN,
                timestamp=datetime.now(UTC),
                metadata={"status": "MISSING", "error": "No specialist output received"}
            )
            missing_warnings.append(dummy_warning_evidence)

        return {
            "mission_id": bundle.mission_id,
            "findings": findings,
            "sources": list(set(sources)),
            "latencies": latencies,
            "missing_specialists": missing_specialists,
            "missing_warnings": missing_warnings,
            "is_complete": len(missing_specialists) == 0
        }
