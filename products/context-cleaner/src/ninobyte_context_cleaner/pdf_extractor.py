"""
PDF text extraction module for ninobyte-context-cleaner.

Provides deterministic text extraction from text-based PDFs.
Requires the optional 'pdf' extra: pip install ninobyte-context-cleaner[pdf]

Security:
- No shell execution
- No network access
- Read-only file operations
- Path validation handled by caller
"""

from typing import Optional, Tuple

# Lazy import flag - we check availability when needed
_PYPDF_AVAILABLE: Optional[bool] = None


def is_pdf_available() -> bool:
    """
    Check if PDF extraction is available.

    Returns:
        True if pypdf is installed, False otherwise
    """
    global _PYPDF_AVAILABLE

    if _PYPDF_AVAILABLE is None:
        try:
            import pypdf  # noqa: F401
            _PYPDF_AVAILABLE = True
        except ImportError:
            _PYPDF_AVAILABLE = False

    return _PYPDF_AVAILABLE


def get_pdf_import_error() -> str:
    """
    Get a helpful error message for missing PDF dependency.

    Returns:
        Error message string with installation instructions
    """
    return (
        "PDF support requires the 'pdf' extra. "
        "Install with: pip install ninobyte-context-cleaner[pdf]"
    )


class PDFExtractor:
    """
    Deterministic text extractor for text-based PDFs.

    Features:
    - Extracts text from all pages in order
    - Normalizes output (consistent newlines, trimmed whitespace)
    - Deterministic: same input PDF -> same output text

    Limitations:
    - Text-based PDFs only (no OCR)
    - Scanned/image PDFs will produce empty or minimal output

    Usage:
        extractor = PDFExtractor()
        text = extractor.extract_from_file("/path/to/document.pdf")
    """

    def __init__(self):
        """
        Initialize the PDF extractor.

        Raises:
            ImportError: If pypdf is not installed
        """
        if not is_pdf_available():
            raise ImportError(get_pdf_import_error())

        # Import here after availability check
        import pypdf
        self._pypdf = pypdf

    def extract_from_file(self, file_path: str) -> str:
        """
        Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file (must be validated by caller)

        Returns:
            Extracted and normalized text

        Raises:
            IOError: If file cannot be read
            pypdf.errors.PdfReadError: If PDF is malformed
        """
        with open(file_path, 'rb') as f:
            return self._extract_from_stream(f)

    def extract_from_bytes(self, data: bytes) -> str:
        """
        Extract text from PDF bytes.

        Args:
            data: Raw PDF bytes

        Returns:
            Extracted and normalized text
        """
        import io
        stream = io.BytesIO(data)
        return self._extract_from_stream(stream)

    def _extract_from_stream(self, stream) -> str:
        """
        Internal: Extract text from a file-like stream.

        Args:
            stream: File-like object (binary mode)

        Returns:
            Extracted and normalized text
        """
        reader = self._pypdf.PdfReader(stream)

        # Extract text from all pages in order
        pages_text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)

        # Join pages with double newline (page break indicator)
        raw_text = "\n\n".join(pages_text)

        # Normalize the output
        return self._normalize_text(raw_text)

    def _normalize_text(self, text: str) -> str:
        """
        Normalize extracted text for deterministic output.

        Normalization rules:
        1. Convert all line endings to Unix-style (\\n)
        2. Strip trailing whitespace from each line
        3. Collapse 3+ consecutive newlines to 2
        4. Strip leading/trailing whitespace from entire text
        5. Ensure single trailing newline

        Args:
            text: Raw extracted text

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Step 1: Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Step 2: Strip trailing whitespace from each line
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # Step 3: Collapse excessive newlines (3+ -> 2)
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')

        # Step 4: Strip leading/trailing whitespace
        text = text.strip()

        # Step 5: Ensure single trailing newline (if non-empty)
        if text:
            text = text + '\n'

        return text


def extract_text_from_pdf(file_path: str) -> Tuple[str, Optional[str]]:
    """
    Convenience function to extract text from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        (extracted_text, error_message)
        On success: (text, None)
        On failure: ("", error_message)
    """
    if not is_pdf_available():
        return "", get_pdf_import_error()

    try:
        extractor = PDFExtractor()
        text = extractor.extract_from_file(file_path)
        return text, None
    except Exception as e:
        return "", f"PDF extraction failed: {e}"
