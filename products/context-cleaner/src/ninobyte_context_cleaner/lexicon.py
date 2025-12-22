"""
Lexicon injection module for ninobyte-context-cleaner.

Provides deterministic, offline lexicon-based substitutions to improve
context quality. Lexicons are loaded from local JSON files only.

Security:
- Reuses path security (canonicalization + traversal blocking)
- No networking
- No shell execution
- Read-only file operations

Pipeline Order (authoritative):
input read → table normalize → lexicon injection → PII redaction → output
"""

import json
import os
import re
from typing import Dict, List, Optional, Tuple

# Reserved token pattern: anything matching [UPPER_CASE_WITH_UNDERSCORES]
# These tokens are protected from lexicon replacement
RESERVED_TOKEN_PATTERN = re.compile(r'\[[A-Z0-9_]+\]')


def is_safe_lexicon_path(path: str) -> Tuple[bool, str]:
    """
    Validate that a lexicon file path is safe for reading.

    Reuses the same security rules as input file validation:
    - Reject paths containing ".." after normalization
    - Path must exist and be a file (not directory)

    Returns:
        (is_safe, error_message)
    """
    # Normalize the path
    normalized = os.path.normpath(path)

    # Reject directory traversal attempts
    if ".." in normalized.split(os.sep):
        return False, "Path traversal not allowed: '..' segments rejected"

    # Check if path exists
    if not os.path.exists(normalized):
        return False, f"Lexicon file not found: {path}"

    # Must be a file, not a directory
    if not os.path.isfile(normalized):
        return False, f"Not a file: {path}"

    return True, ""


def load_lexicon(path: str) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    """
    Load a lexicon from a JSON file.

    Expected format: A single JSON object mapping "from" -> "to"
    Example:
    {
        "Acme Inc": "ACME Incorporated",
        "NYC": "New York City"
    }

    Args:
        path: Path to lexicon JSON file (already validated for safety)

    Returns:
        (lexicon_dict, error_message)
        On success: (dict, None)
        On failure: (None, error_message)
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate structure
        if not isinstance(data, dict):
            return None, "Lexicon must be a JSON object (dict)"

        # Validate all keys and values are strings
        for key, value in data.items():
            if not isinstance(key, str):
                return None, f"Lexicon key must be string, got: {type(key).__name__}"
            if not isinstance(value, str):
                return None, f"Lexicon value must be string, got: {type(value).__name__}"

        return data, None

    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in lexicon file: {e}"
    except IOError as e:
        return None, f"Failed to read lexicon file: {e}"


def get_deterministic_key_order(lexicon: Dict[str, str]) -> List[str]:
    """
    Get lexicon keys in deterministic order for replacement.

    Order rules (for determinism):
    1. Sort by descending key length (longer keys first)
    2. Tie-breaker: lexicographic ascending

    This ensures that longer patterns are matched before shorter ones,
    and the order is stable across runs.

    Args:
        lexicon: The lexicon dictionary

    Returns:
        List of keys in deterministic order
    """
    return sorted(lexicon.keys(), key=lambda k: (-len(k), k))


def find_reserved_tokens(text: str) -> List[Tuple[int, int]]:
    """
    Find all reserved token positions in text.

    Reserved tokens match pattern: [UPPER_CASE_WITH_UNDERSCORES]
    These are protected from lexicon replacement.

    Args:
        text: Input text

    Returns:
        List of (start, end) positions for each reserved token
    """
    return [(m.start(), m.end()) for m in RESERVED_TOKEN_PATTERN.finditer(text)]


def is_position_in_reserved(pos: int, end_pos: int, reserved: List[Tuple[int, int]]) -> bool:
    """
    Check if a position range overlaps with any reserved token.

    Args:
        pos: Start position of potential replacement
        end_pos: End position of potential replacement
        reserved: List of (start, end) reserved token positions

    Returns:
        True if the range overlaps with any reserved token
    """
    for r_start, r_end in reserved:
        # Check for any overlap
        if pos < r_end and end_pos > r_start:
            return True
    return False


class LexiconInjector:
    """
    Deterministic lexicon-based text substitution engine.

    Features:
    - Plain string replacement (no regex in MVP)
    - Deterministic key ordering (by length desc, then lexicographic)
    - Case-sensitive matching
    - Protects reserved bracket tokens from replacement

    Usage:
        injector = LexiconInjector({"NYC": "New York City"})
        result = injector.apply("Visit NYC today!")
    """

    def __init__(self, lexicon: Dict[str, str]):
        """
        Initialize the lexicon injector.

        Args:
            lexicon: Dictionary mapping "from" strings to "to" strings
        """
        self._lexicon = lexicon
        self._ordered_keys = get_deterministic_key_order(lexicon)

    @property
    def rules_count(self) -> int:
        """Return the number of rules in the lexicon."""
        return len(self._lexicon)

    def apply(self, text: str) -> str:
        """
        Apply lexicon substitutions to text.

        Replacement is done in deterministic order:
        1. Longer keys are replaced first
        2. Tie-breaker: lexicographic order

        Reserved tokens (matching [UPPER_CASE]) are protected.

        Args:
            text: Input text

        Returns:
            Text with lexicon substitutions applied
        """
        if not text or not self._lexicon:
            return text

        # Find reserved tokens to protect
        reserved = find_reserved_tokens(text)

        result = text
        offset = 0  # Track position shifts due to replacements

        # Process each key in deterministic order
        for key in self._ordered_keys:
            if not key:  # Skip empty keys
                continue

            replacement = self._lexicon[key]

            # Find all occurrences of this key
            search_pos = 0
            new_result = []
            last_end = 0

            while True:
                pos = result.find(key, search_pos)
                if pos == -1:
                    break

                end_pos = pos + len(key)

                # Check if this occurrence is inside a reserved token
                # We need to recalculate reserved positions for current result
                current_reserved = find_reserved_tokens(result)

                if is_position_in_reserved(pos, end_pos, current_reserved):
                    # Skip this occurrence, it's inside a reserved token
                    search_pos = pos + 1
                    continue

                # Safe to replace
                new_result.append(result[last_end:pos])
                new_result.append(replacement)
                last_end = end_pos
                search_pos = end_pos

            if new_result:
                new_result.append(result[last_end:])
                result = ''.join(new_result)

        return result


def create_lexicon_meta(
    path: str,
    rules_count: int,
    target: str,
    mode: str
) -> str:
    """
    Create the lexicon metadata JSON fragment for JSONL output.

    Args:
        path: Lexicon file path
        rules_count: Number of rules in lexicon
        target: Target stream (input, normalized, both)
        mode: Replacement mode (replace)

    Returns:
        JSON string for lexicon metadata
    """
    import json

    # Only include basename for security (don't expose full path)
    basename = os.path.basename(path)

    meta = {
        "enabled": True,
        "source": "file",
        "path_basename": basename,
        "rules_count": rules_count,
        "target": target,
        "mode": mode,
    }

    # Build with explicit key order
    parts = [
        f'"enabled":{json.dumps(meta["enabled"])}',
        f'"source":{json.dumps(meta["source"])}',
        f'"path_basename":{json.dumps(meta["path_basename"])}',
        f'"rules_count":{json.dumps(meta["rules_count"])}',
        f'"target":{json.dumps(meta["target"])}',
        f'"mode":{json.dumps(meta["mode"])}',
    ]

    return "{" + ",".join(parts) + "}"
