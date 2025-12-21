"""
Module entry point for python -m ninobyte_opspack
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
