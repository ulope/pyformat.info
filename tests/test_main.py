import sys

import pytest

from main import get_content


@pytest.mark.xfail(sys.version_info < (3, 3), reason="Because 2.7")
def test_collect():
    assert len(list(get_content())) == 8
