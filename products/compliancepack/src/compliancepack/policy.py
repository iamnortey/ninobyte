"""
CompliancePack Policy Schema and Loader.

Handles JSON policy files with deterministic validation and ordering.

Schema v1:
{
  "schema_version": "1.0",
  "policies": [
    {
      "id": "CP0001",
      "title": "...",
      "severity": "high|medium|low|critical|info",
      "type": "regex|contains",
      "pattern": "...",      // for type=regex
      "needle": "...",       // for type=contains
      "description": "...",
      "sample_limit": 3
    }
  ]
}
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict, Union


class PolicyDict(TypedDict):
    """A single policy definition."""
    id: str
    title: str
    severity: str
    type: str
    pattern: Optional[str]
    needle: Optional[str]
    description: str
    sample_limit: int


class PolicyFileDict(TypedDict):
    """Complete policy file structure."""
    schema_version: str
    policies: List[PolicyDict]


# Valid severity levels in ranking order (highest to lowest)
SEVERITY_LEVELS = ("critical", "high", "medium", "low", "info")

# Valid policy types
POLICY_TYPES = ("regex", "contains")


class PolicyValidationError(Exception):
    """Raised when policy validation fails."""
    pass


def _validate_policy(policy: Dict[str, Any], index: int) -> PolicyDict:
    """
    Validate a single policy entry.

    Args:
        policy: Raw policy dict from JSON
        index: Index in policies array (for error messages)

    Returns:
        Validated PolicyDict

    Raises:
        PolicyValidationError: If validation fails
    """
    # Required fields
    required_fields = ["id", "title", "severity", "type", "description"]
    for field in required_fields:
        if field not in policy:
            raise PolicyValidationError(
                f"Policy at index {index}: missing required field '{field}'"
            )

    # Validate id format (should be like CP0001)
    policy_id = policy["id"]
    if not isinstance(policy_id, str) or not policy_id:
        raise PolicyValidationError(
            f"Policy at index {index}: 'id' must be a non-empty string"
        )

    # Validate severity
    severity = policy["severity"]
    if severity not in SEVERITY_LEVELS:
        raise PolicyValidationError(
            f"Policy '{policy_id}': invalid severity '{severity}'. "
            f"Must be one of: {', '.join(SEVERITY_LEVELS)}"
        )

    # Validate type
    policy_type = policy["type"]
    if policy_type not in POLICY_TYPES:
        raise PolicyValidationError(
            f"Policy '{policy_id}': invalid type '{policy_type}'. "
            f"Must be one of: {', '.join(POLICY_TYPES)}"
        )

    # Validate type-specific fields
    if policy_type == "regex":
        if "pattern" not in policy:
            raise PolicyValidationError(
                f"Policy '{policy_id}': type 'regex' requires 'pattern' field"
            )
        # Validate regex compiles
        try:
            re.compile(policy["pattern"])
        except re.error as e:
            raise PolicyValidationError(
                f"Policy '{policy_id}': invalid regex pattern: {e}"
            )
    elif policy_type == "contains":
        if "needle" not in policy:
            raise PolicyValidationError(
                f"Policy '{policy_id}': type 'contains' requires 'needle' field"
            )

    # Validate sample_limit (optional, default 3)
    sample_limit = policy.get("sample_limit", 3)
    if not isinstance(sample_limit, int) or sample_limit < 1:
        raise PolicyValidationError(
            f"Policy '{policy_id}': 'sample_limit' must be a positive integer"
        )

    return {
        "id": policy["id"],
        "title": policy["title"],
        "severity": policy["severity"],
        "type": policy["type"],
        "pattern": policy.get("pattern"),
        "needle": policy.get("needle"),
        "description": policy["description"],
        "sample_limit": sample_limit,
    }


def load_policy_file(path: Union[str, Path]) -> PolicyFileDict:
    """
    Load and validate a policy file.

    Args:
        path: Path to JSON policy file

    Returns:
        Validated PolicyFileDict with policies sorted by id (deterministic)

    Raises:
        PolicyValidationError: If validation fails
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate schema_version
    if "schema_version" not in data:
        raise PolicyValidationError("Missing 'schema_version' field")

    schema_version = data["schema_version"]
    if schema_version != "1.0":
        raise PolicyValidationError(
            f"Unsupported schema version '{schema_version}'. Only '1.0' is supported."
        )

    # Validate policies array
    if "policies" not in data:
        raise PolicyValidationError("Missing 'policies' field")

    if not isinstance(data["policies"], list):
        raise PolicyValidationError("'policies' must be an array")

    # Validate each policy
    validated_policies: List[PolicyDict] = []
    seen_ids: set = set()

    for i, policy in enumerate(data["policies"]):
        validated = _validate_policy(policy, i)

        # Check for duplicate ids
        if validated["id"] in seen_ids:
            raise PolicyValidationError(
                f"Duplicate policy id: '{validated['id']}'"
            )
        seen_ids.add(validated["id"])

        validated_policies.append(validated)

    # Sort policies by id for deterministic ordering
    validated_policies.sort(key=lambda p: p["id"])

    return {
        "schema_version": schema_version,
        "policies": validated_policies,
    }


def get_severity_rank(severity: str) -> int:
    """
    Get numeric rank for severity (lower = more severe).

    Returns:
        0 for critical, 1 for high, 2 for medium, 3 for low, 4 for info
    """
    try:
        return SEVERITY_LEVELS.index(severity)
    except ValueError:
        return 999  # Unknown severity sorts last
