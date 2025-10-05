import utils
import sys
from pathlib import Path

# Add project root to path so tests can import utils directly
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_fx_search_result_empty():
    out = utils.fx_search_result("unknown", {})
    assert out["img_url"] == ""
    assert out["title"] == ""
