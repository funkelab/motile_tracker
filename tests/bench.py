"""Performance benchmarks for motile_tracker.

Run with:
    uv run pytest tests/bench.py --benchmark-enable -v          # SCIP only
    uv run pytest tests/bench.py --benchmark-enable -v -m gurobi  # Gurobi only
    uv run pytest tests/bench.py --benchmark-enable -m "" -v      # all

Fixtures are defined in tests/bench_conftest.py (auto-discovered as a plugin).
"""

import ilpy
import pytest

from motile_tracker.data_views.views.tree_view.tree_widget_utils import (
    extract_sorted_tracks,
)
from motile_tracker.motile.backend import build_candidate_graph, solve

pytest_plugins = ["bench_conftest"]

# ============================================================================
# Solve benchmarks
# ============================================================================


def test_solve_hela_scip(benchmark, hela_seg, default_params, hela_cand_graph):
    """Benchmark: solve HeLa uncropped with SCIP."""
    benchmark.pedantic(
        solve,
        args=(default_params, hela_seg),
        kwargs={"cand_graph": hela_cand_graph, "backend": ilpy.Preference.Scip},
        rounds=1,
        iterations=1,
    )


@pytest.mark.gurobi
def test_solve_hela_gurobi(benchmark, hela_seg, default_params, hela_cand_graph):
    """Benchmark: solve HeLa uncropped with Gurobi."""
    benchmark.pedantic(
        solve,
        args=(default_params, hela_seg),
        kwargs={"cand_graph": hela_cand_graph, "backend": ilpy.Preference.Gurobi},
        rounds=1,
        iterations=1,
    )


def test_solve_mouse_embryo_scip(
    benchmark, mouse_seg, default_params, mouse_cand_graph
):
    """Benchmark: solve Mouse Embryo with SCIP."""
    benchmark.pedantic(
        solve,
        args=(default_params, mouse_seg),
        kwargs={"cand_graph": mouse_cand_graph, "backend": ilpy.Preference.Scip},
        rounds=1,
        iterations=1,
    )


@pytest.mark.gurobi
def test_solve_mouse_embryo_gurobi(
    benchmark, mouse_seg, default_params, mouse_cand_graph
):
    """Benchmark: solve Mouse Embryo with Gurobi."""
    benchmark.pedantic(
        solve,
        args=(default_params, mouse_seg),
        kwargs={"cand_graph": mouse_cand_graph, "backend": ilpy.Preference.Gurobi},
        rounds=1,
        iterations=1,
    )


# ============================================================================
# Candidate graph construction benchmarks
# ============================================================================


def test_build_cand_graph_hela(benchmark, hela_seg, default_params):
    """Benchmark: build candidate graph for HeLa uncropped."""
    benchmark.pedantic(
        build_candidate_graph,
        args=(hela_seg, default_params),
        rounds=1,
        iterations=1,
    )


def test_build_cand_graph_mouse_embryo(benchmark, mouse_seg, default_params):
    """Benchmark: build candidate graph for Mouse Embryo."""
    benchmark.pedantic(
        build_candidate_graph,
        args=(mouse_seg, default_params),
        rounds=1,
        iterations=1,
    )


# ============================================================================
# UI update benchmarks (use pre-computed SCIP results)
# ============================================================================


def test_ui_extract_sorted_tracks_hela(benchmark, hela_tracks, colormap):
    """Benchmark: extract_sorted_tracks for HeLa."""
    benchmark.pedantic(
        extract_sorted_tracks,
        args=(hela_tracks, colormap),
        rounds=1,
        iterations=1,
    )


def test_ui_extract_sorted_tracks_mouse(benchmark, mouse_tracks, colormap):
    """Benchmark: extract_sorted_tracks for Mouse Embryo."""
    benchmark.pedantic(
        extract_sorted_tracks,
        args=(mouse_tracks, colormap),
        rounds=1,
        iterations=1,
    )
