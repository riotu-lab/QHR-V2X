import pytest
from test_pathfinding_all import run_all


@pytest.mark.parametrize("mode", ["dense", "sparse"])
def test_pathfinding_modes(mode):
    # results = run_all(mode)
    results = run_all(mode, show_zoom=False)

    # ✅ Optional: sanity check to ensure the result structure is valid
    for algo, metrics in results.items():
        assert isinstance(metrics, dict), f"{algo} should return a dict of metrics"
        assert "msgs" in metrics and "path_len" in metrics and "time" in metrics, f"{algo} missing expected keys"
        assert len(metrics["msgs"]) > 0, f"{algo} returned empty SDM list"
        assert all(m >= 0 for m in metrics["msgs"]), f"{algo} has negative SDM"
        
# import pytest
# from test_pathfinding_all import run_all

# @pytest.mark.parametrize("mode", ["dense", "sparse"])
# def test_pathfinding_modes(mode):
#     results = run_all(mode)

#     # ✅ Optional: Sanity check and sorted output
#     sorted_keys = sorted(results.keys())  # e.g., ['astar', 'astar_quantum', 'bellman_ford', ...]
    
#     for algo in sorted_keys:
#         metrics = results[algo]
#         assert isinstance(metrics, dict), f"{algo} should return a dict of metrics"
#         assert "msgs" in metrics and "path_len" in metrics and "time" in metrics, f"{algo} missing expected keys"
#         assert len(metrics["msgs"]) > 0, f"{algo} returned empty SDM list"
#         assert all(m >= 0 for m in metrics["msgs"]), f"{algo} has negative SDM"
#         print(f"✅ {algo.upper()} passed basic checks")
