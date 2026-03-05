# conftest.py  (place this in the project root)
# Adds the src/ folder to Python's path so every test file can
# do  "import inventory"  without any extra setup.

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
