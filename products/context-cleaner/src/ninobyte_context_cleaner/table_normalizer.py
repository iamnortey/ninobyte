"""
TableNormalizer - Deterministic table-to-text transformation.

Converts table-like content (pipe tables, CSV, TSV, whitespace-aligned)
into LLM-friendly key:value representation.

Design principles:
- Conservative: Only normalize high-confidence table patterns
- Deterministic: Same input always produces same output
- Non-destructive: Non-table text passes through unchanged
"""

import re
from typing import List, Optional, Tuple


class TableNormalizer:
    """
    Deterministic table normalization engine.

    Detects and converts table-like content into structured text.
    Same input always produces same output.
    """

    # Minimum columns to consider something a table
    MIN_COLUMNS = 2

    # Minimum rows (including header) to consider something a table
    MIN_ROWS = 2

    def __init__(self) -> None:
        """Initialize the TableNormalizer."""
        pass

    def _is_pipe_table_row(self, line: str) -> bool:
        """Check if a line looks like a pipe-delimited table row."""
        stripped = line.strip()
        # Must have at least one internal pipe (not just leading/trailing)
        if '|' not in stripped:
            return False
        # Split and check for multiple cells
        parts = [p.strip() for p in stripped.split('|')]
        # Filter out empty edge cells from leading/trailing pipes
        cells = [p for p in parts if p or parts.index(p) not in (0, len(parts) - 1)]
        # Need content cells (not just separator line)
        content_cells = [c for c in cells if c and not re.match(r'^[-:]+$', c)]
        return len(content_cells) >= self.MIN_COLUMNS or (
            len(cells) >= self.MIN_COLUMNS and all(re.match(r'^[-:]+$', c) for c in cells if c)
        )

    def _is_separator_row(self, line: str) -> bool:
        """Check if line is a table separator (e.g., |---|---|)."""
        stripped = line.strip()
        if '|' not in stripped:
            return False
        parts = [p.strip() for p in stripped.split('|') if p.strip()]
        return all(re.match(r'^[-:]+$', p) for p in parts) and len(parts) >= self.MIN_COLUMNS

    def _parse_pipe_table(self, lines: List[str]) -> Optional[List[List[str]]]:
        """
        Parse a pipe-delimited table into rows of cells.

        Returns None if not a valid table.
        """
        rows: List[List[str]] = []
        separator_found = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if self._is_separator_row(stripped):
                separator_found = True
                continue

            if not self._is_pipe_table_row(stripped):
                # Non-table line encountered
                if rows:
                    break
                continue

            # Parse cells
            parts = stripped.split('|')
            # Handle leading/trailing pipes
            if parts and not parts[0].strip():
                parts = parts[1:]
            if parts and not parts[-1].strip():
                parts = parts[:-1]

            cells = [p.strip() for p in parts]
            if len(cells) >= self.MIN_COLUMNS:
                rows.append(cells)

        # Validate: need header + at least one data row
        if len(rows) >= self.MIN_ROWS:
            return rows
        return None

    def _is_csv_line(self, line: str) -> Tuple[bool, List[str]]:
        """
        Check if a line looks like CSV (comma-separated).

        Returns (is_csv, cells).
        """
        stripped = line.strip()
        if ',' not in stripped:
            return False, []

        # Skip lines that look like our normalized output format
        # This prevents re-processing already normalized content
        if re.match(r'^Row \d+:', stripped):
            return False, []

        # Skip lines that contain key=value patterns (our output format)
        # These have commas but are not CSV data
        if re.search(r'\w+=\S+,\s*\w+=', stripped):
            return False, []

        # Simple CSV parsing (no quoted fields with commas for MVP)
        cells = [c.strip() for c in stripped.split(',')]

        # Heuristic: need multiple non-empty cells
        non_empty = [c for c in cells if c]
        if len(non_empty) >= self.MIN_COLUMNS:
            return True, cells
        return False, []

    def _is_tsv_line(self, line: str) -> Tuple[bool, List[str]]:
        """
        Check if a line looks like TSV (tab-separated).

        Returns (is_tsv, cells).
        """
        stripped = line.strip()
        if '\t' not in stripped:
            return False, []

        cells = [c.strip() for c in stripped.split('\t')]
        non_empty = [c for c in cells if c]
        if len(non_empty) >= self.MIN_COLUMNS:
            return True, cells
        return False, []

    def _parse_delimited_table(
        self, lines: List[str], delimiter: str
    ) -> Optional[List[List[str]]]:
        """
        Parse a delimited table (CSV or TSV).

        Returns None if not a valid table.
        """
        rows: List[List[str]] = []
        expected_cols: Optional[int] = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if delimiter == ',':
                is_match, cells = self._is_csv_line(stripped)
            else:  # tab
                is_match, cells = self._is_tsv_line(stripped)

            if not is_match:
                if rows:
                    break
                continue

            # Check column consistency
            if expected_cols is None:
                expected_cols = len(cells)
            elif len(cells) != expected_cols:
                # Inconsistent columns - not a clean table
                if rows:
                    break
                continue

            rows.append(cells)

        if len(rows) >= self.MIN_ROWS:
            return rows
        return None

    def _format_table_as_text(
        self, rows: List[List[str]], headers: Optional[List[str]] = None
    ) -> str:
        """
        Format parsed table rows as deterministic key:value text.

        If headers provided, uses them as keys. Otherwise uses Col1, Col2, etc.
        """
        if not rows:
            return ""

        # Use first row as headers if not provided
        if headers is None:
            headers = rows[0]
            data_rows = rows[1:]
        else:
            data_rows = rows

        # Sanitize headers: use ColN for empty headers
        clean_headers = []
        for i, h in enumerate(headers):
            if h.strip():
                clean_headers.append(h.strip())
            else:
                clean_headers.append(f"Col{i + 1}")

        # Format each data row
        output_lines = []
        for row_idx, row in enumerate(data_rows, start=1):
            parts = []
            for col_idx, cell in enumerate(row):
                if col_idx < len(clean_headers):
                    key = clean_headers[col_idx]
                else:
                    key = f"Col{col_idx + 1}"
                value = cell.strip() if cell else ""
                parts.append(f"{key}={value}")

            row_text = f"Row {row_idx}: " + ", ".join(parts)
            output_lines.append(row_text)

        return "\n".join(output_lines)

    def _find_and_normalize_pipe_tables(self, text: str) -> str:
        """Find and normalize pipe-delimited tables in text."""
        lines = text.split('\n')
        result_lines: List[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this could be the start of a pipe table
            if self._is_pipe_table_row(line.strip()):
                # Collect potential table lines
                table_lines = [line]
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    stripped = next_line.strip()
                    if stripped and (self._is_pipe_table_row(stripped) or
                                     self._is_separator_row(stripped)):
                        table_lines.append(next_line)
                        j += 1
                    elif not stripped:
                        # Empty line might end table or be internal
                        if j + 1 < len(lines) and self._is_pipe_table_row(lines[j + 1].strip()):
                            table_lines.append(next_line)
                            j += 1
                        else:
                            break
                    else:
                        break

                # Try to parse as table
                parsed = self._parse_pipe_table(table_lines)
                if parsed:
                    # Successfully parsed - normalize it
                    normalized = self._format_table_as_text(parsed)
                    result_lines.append(normalized)
                    i = j
                    continue

            # Not a table line, keep as-is
            result_lines.append(line)
            i += 1

        return '\n'.join(result_lines)

    def _find_and_normalize_csv_tables(self, text: str) -> str:
        """Find and normalize CSV-style tables in text."""
        lines = text.split('\n')
        result_lines: List[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]
            is_csv, _ = self._is_csv_line(line.strip())

            if is_csv:
                # Collect potential CSV lines
                table_lines = [line]
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    is_next_csv, _ = self._is_csv_line(next_line.strip())
                    if is_next_csv:
                        table_lines.append(next_line)
                        j += 1
                    elif not next_line.strip():
                        break
                    else:
                        break

                # Try to parse as CSV table
                parsed = self._parse_delimited_table(table_lines, ',')
                if parsed:
                    normalized = self._format_table_as_text(parsed)
                    result_lines.append(normalized)
                    i = j
                    continue

            result_lines.append(line)
            i += 1

        return '\n'.join(result_lines)

    def _find_and_normalize_tsv_tables(self, text: str) -> str:
        """Find and normalize TSV-style tables in text."""
        lines = text.split('\n')
        result_lines: List[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]
            is_tsv, _ = self._is_tsv_line(line.strip())

            if is_tsv:
                # Collect potential TSV lines
                table_lines = [line]
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    is_next_tsv, _ = self._is_tsv_line(next_line.strip())
                    if is_next_tsv:
                        table_lines.append(next_line)
                        j += 1
                    elif not next_line.strip():
                        break
                    else:
                        break

                # Try to parse as TSV table
                parsed = self._parse_delimited_table(table_lines, '\t')
                if parsed:
                    normalized = self._format_table_as_text(parsed)
                    result_lines.append(normalized)
                    i = j
                    continue

            result_lines.append(line)
            i += 1

        return '\n'.join(result_lines)

    def normalize(self, text: str) -> str:
        """
        Normalize table-like content in text.

        Detects and converts:
        - Pipe tables (| a | b |)
        - CSV-style tables (a,b,c)
        - TSV-style tables (a\\tb\\tc)

        Non-table text passes through unchanged.

        Args:
            text: Input text potentially containing tables

        Returns:
            Text with tables converted to key:value format.
            Output is deterministic: same input always produces same output.
        """
        # Process in order: pipe tables first (most explicit), then TSV, then CSV
        # This order matters because some content could match multiple patterns
        result = self._find_and_normalize_pipe_tables(text)
        result = self._find_and_normalize_tsv_tables(result)
        result = self._find_and_normalize_csv_tables(result)

        return result
