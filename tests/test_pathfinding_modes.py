import pytest
from test_pathfinding_all import run_all


@pytest.mark.parametrize("mode", ["dense", "sparse"])
def test_pathfinding_modes(mode):
    results = run_all(mode, show_zoom=False)

    # Sanity check on the result structure returned by the harness.
    for algo, metrics in results.items():
        assert isinstance(metrics, dict), f"{algo} should return a dict of metrics"
        assert "msgs" in metrics and "path_len" in metrics and "time" in metrics, f"{algo} missing expected keys"
        assert len(metrics["msgs"]) > 0, f"{algo} returned empty SDM list"
        assert all(m >= 0 for m in metrics["msgs"]), f"{algo} has negative SDM"
