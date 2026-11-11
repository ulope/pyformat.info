import sys
from pathlib import Path

from main import content_modules


# Content modules that use syntax this Python version can't parse
# (test_content_py3NN.py needs Python 3.NN) are not collected.
collect_ignore = [
    path.name
    for path, version in content_modules(Path(__file__).parent)
    if version and sys.version_info < version
]
