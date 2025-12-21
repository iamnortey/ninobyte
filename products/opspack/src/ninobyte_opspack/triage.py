"""
Incident Triage Module

Provides deterministic, rule-based incident classification and triage recommendations.
No network calls, no shell execution, no file writes.

Security constraints (enforced by design):
- Read-only: All operations are pure functions
- No network: No HTTP clients or API calls
- No shell: No subprocess or os.system
- Deterministic: Same input = same output
"""

from typing import Any, Dict, List, Optional
from .version import __version__

# Output schema version for consumers to track compatibility
TRIAGE_SCHEMA_VERSION = "1.0.0"


# Severity levels (ordered from highest to lowest)
class Severity:
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Classification categories
class Category:
    SECURITY = "security"
    AVAILABILITY = "availability"
    PERFORMANCE = "performance"
    DATA_INTEGRITY = "data_integrity"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


def _classify_severity(incident: Dict[str, Any]) -> str:
    """
    Classify incident severity based on keywords and metrics.

    Rules (in priority order):
    1. Explicit severity field takes precedence
    2. Keywords in title/description
    3. Impact metrics (users_affected, services_affected)
    4. Default to MEDIUM
    """
    # Check for explicit severity
    explicit_severity = incident.get("severity", "").lower()
    if explicit_severity in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW):
        return explicit_severity

    # Keyword analysis
    text = (
        incident.get("title", "") + " " +
        incident.get("description", "") + " " +
        incident.get("summary", "")
    ).lower()

    critical_keywords = ["breach", "data leak", "unauthorized access", "ransomware", "down", "outage", "complete failure"]
    high_keywords = ["degraded", "partial outage", "security vulnerability", "data loss", "timeout", "unresponsive"]
    low_keywords = ["warning", "minor", "cosmetic", "informational"]

    for kw in critical_keywords:
        if kw in text:
            return Severity.CRITICAL

    for kw in high_keywords:
        if kw in text:
            return Severity.HIGH

    for kw in low_keywords:
        if kw in text:
            return Severity.LOW

    # Impact-based classification
    users_affected = incident.get("users_affected", 0)
    services_affected = len(incident.get("affected_services", []))

    if users_affected > 1000 or services_affected >= 3:
        return Severity.CRITICAL
    if users_affected > 100 or services_affected >= 2:
        return Severity.HIGH
    if users_affected > 10 or services_affected >= 1:
        return Severity.MEDIUM

    return Severity.MEDIUM


def _classify_category(incident: Dict[str, Any]) -> str:
    """
    Classify incident category based on keywords and type hints.

    Categories: security, availability, performance, data_integrity, configuration, unknown
    """
    # Check for explicit category
    explicit_category = incident.get("category", "").lower()
    if explicit_category in (Category.SECURITY, Category.AVAILABILITY, Category.PERFORMANCE,
                             Category.DATA_INTEGRITY, Category.CONFIGURATION):
        return explicit_category

    text = (
        incident.get("title", "") + " " +
        incident.get("description", "") + " " +
        incident.get("type", "")
    ).lower()

    # Category keyword mappings
    category_keywords = {
        Category.SECURITY: ["breach", "unauthorized", "vulnerability", "exploit", "attack", "intrusion", "malware", "phishing"],
        Category.AVAILABILITY: ["down", "outage", "unavailable", "unreachable", "crash", "failure", "offline"],
        Category.PERFORMANCE: ["slow", "latency", "timeout", "degraded", "high cpu", "memory", "disk full"],
        Category.DATA_INTEGRITY: ["corrupt", "data loss", "inconsistent", "replication", "backup"],
        Category.CONFIGURATION: ["misconfigur", "config", "setting", "permission", "access denied"],
    }

    for category, keywords in category_keywords.items():
        for kw in keywords:
            if kw in text:
                return category

    return Category.UNKNOWN


def _generate_risk_flags(incident: Dict[str, Any], classification: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Generate risk flags based on incident data and classification.
    """
    flags = []

    # Security-related flags
    if classification["category"] == Category.SECURITY:
        flags.append({
            "flag": "SECURITY_INCIDENT",
            "reason": "Incident classified as security-related",
            "action": "Engage security team immediately"
        })

    # Critical severity flag
    if classification["severity"] == Severity.CRITICAL:
        flags.append({
            "flag": "CRITICAL_SEVERITY",
            "reason": "Incident severity is critical",
            "action": "Escalate to on-call leadership"
        })

    # Data-related flags
    if classification["category"] == Category.DATA_INTEGRITY:
        flags.append({
            "flag": "DATA_AT_RISK",
            "reason": "Potential data integrity issue",
            "action": "Verify backup status and data recovery options"
        })

    # High user impact
    users_affected = incident.get("users_affected", 0)
    if users_affected > 500:
        flags.append({
            "flag": "HIGH_USER_IMPACT",
            "reason": f"Affects {users_affected} users",
            "action": "Prepare customer communication"
        })

    # Multiple services affected
    services = incident.get("affected_services", [])
    if len(services) >= 2:
        flags.append({
            "flag": "MULTI_SERVICE_IMPACT",
            "reason": f"Affects {len(services)} services: {', '.join(services[:5])}",
            "action": "Coordinate cross-team response"
        })

    return flags


def _generate_recommended_actions(incident: Dict[str, Any], classification: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Generate ordered list of recommended actions based on triage analysis.
    """
    actions = []
    priority = 1

    # Category-specific actions
    category_actions = {
        Category.SECURITY: [
            {"action": "Isolate affected systems", "rationale": "Prevent further unauthorized access"},
            {"action": "Preserve logs and evidence", "rationale": "Enable forensic investigation"},
            {"action": "Notify security team", "rationale": "Activate incident response protocol"},
        ],
        Category.AVAILABILITY: [
            {"action": "Check service health dashboards", "rationale": "Confirm scope of outage"},
            {"action": "Review recent deployments", "rationale": "Identify potential cause"},
            {"action": "Initiate failover if available", "rationale": "Restore service availability"},
        ],
        Category.PERFORMANCE: [
            {"action": "Check resource utilization", "rationale": "Identify bottleneck"},
            {"action": "Review recent traffic patterns", "rationale": "Detect anomalies"},
            {"action": "Scale resources if needed", "rationale": "Address capacity issues"},
        ],
        Category.DATA_INTEGRITY: [
            {"action": "Stop affected write operations", "rationale": "Prevent further corruption"},
            {"action": "Verify backup integrity", "rationale": "Ensure recovery option"},
            {"action": "Identify affected data scope", "rationale": "Assess impact"},
        ],
        Category.CONFIGURATION: [
            {"action": "Review recent configuration changes", "rationale": "Identify root cause"},
            {"action": "Compare with known-good configuration", "rationale": "Find discrepancies"},
            {"action": "Prepare rollback plan", "rationale": "Enable quick remediation"},
        ],
    }

    # Add category-specific actions
    category = classification["category"]
    if category in category_actions:
        for item in category_actions[category]:
            actions.append({
                "priority": priority,
                "action": item["action"],
                "rationale": item["rationale"]
            })
            priority += 1

    # Universal actions based on severity
    if classification["severity"] in (Severity.CRITICAL, Severity.HIGH):
        actions.append({
            "priority": priority,
            "action": "Establish communication channel",
            "rationale": "Coordinate response team"
        })
        priority += 1

    # Add documentation action
    actions.append({
        "priority": priority,
        "action": "Document timeline and actions taken",
        "rationale": "Support post-incident review"
    })

    return actions


def _extract_evidence(incident: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and organize evidence from incident data.
    """
    evidence = {
        "source_fields_present": [],
        "source_fields_missing": [],
        "extracted_data": {}
    }

    # Expected fields
    expected_fields = [
        "id", "title", "description", "severity", "category", "type",
        "timestamp", "source", "affected_services", "users_affected",
        "reporter", "tags"
    ]

    for field in expected_fields:
        if field in incident and incident[field]:
            evidence["source_fields_present"].append(field)
            # Include actual values for key fields
            if field in ("id", "title", "severity", "category", "timestamp", "source"):
                evidence["extracted_data"][field] = incident[field]
        else:
            evidence["source_fields_missing"].append(field)

    # Include affected services if present
    if "affected_services" in incident:
        evidence["extracted_data"]["affected_services"] = incident["affected_services"]

    # Include user impact if present
    if "users_affected" in incident:
        evidence["extracted_data"]["users_affected"] = incident["users_affected"]

    return evidence


def triage_incident(incident: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform rule-based triage on an incident snapshot.

    Args:
        incident: Dictionary containing incident data. Expected fields:
            - id: Incident identifier
            - title: Short incident title
            - description: Detailed description
            - severity: Optional explicit severity (critical/high/medium/low)
            - category: Optional explicit category
            - timestamp: When incident occurred (ISO 8601)
            - affected_services: List of affected service names
            - users_affected: Number of users impacted
            - source: Origin of the incident report
            - tags: List of tags/labels

    Returns:
        Triage result dictionary conforming to schema version 1.0.0:
        {
            "version": "<schema version>",
            "opspack_version": "<module version>",
            "incident": {...subset of input...},
            "classification": {"severity": "...", "category": "..."},
            "recommended_actions": [...],
            "risk_flags": [...],
            "evidence": {...}
        }

    Guarantees:
        - Pure function (no side effects)
        - Deterministic (same input = same output)
        - No network calls, shell execution, or file writes
    """
    # Build classification
    classification = {
        "severity": _classify_severity(incident),
        "category": _classify_category(incident)
    }

    # Generate risk flags
    risk_flags = _generate_risk_flags(incident, classification)

    # Generate recommended actions
    recommended_actions = _generate_recommended_actions(incident, classification)

    # Extract evidence
    evidence = _extract_evidence(incident)

    # Build incident subset (key fields only)
    incident_subset = {
        "id": incident.get("id"),
        "title": incident.get("title"),
        "timestamp": incident.get("timestamp"),
        "source": incident.get("source")
    }

    return {
        "version": TRIAGE_SCHEMA_VERSION,
        "opspack_version": __version__,
        "incident": incident_subset,
        "classification": classification,
        "recommended_actions": recommended_actions,
        "risk_flags": risk_flags,
        "evidence": evidence
    }
