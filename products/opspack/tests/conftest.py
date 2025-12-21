"""
Pytest configuration and shared fixtures for OpsPack tests.
"""

import sys
from pathlib import Path

# Add src to path for imports - must be done before importing our modules
_src_path = str(Path(__file__).parent.parent / 'src')
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)
