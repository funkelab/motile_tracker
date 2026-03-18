"""Fixtures and configuration for benchmarks (tests/bench.py).

Kept separate from the main conftest.py to avoid polluting regular test runs.
Import this as a pytest plugin via conftest_file in bench.py, or use
``pytest tests/bench.py --benchmark-enable`` which will auto-discover it.
"""

from pathlib import Path

import ilpy
import napari.utils.colormaps
import pytest
from appdirs import AppDirs
from funtracks.data_model import SolutionTracks

from motile_tracker.data_views.views.tree_view.tree_widget_utils import (
    extract_sorted_tracks,
)
from motile_tracker.example_data import read_ctc_dataset, read_zenodo_dataset
from motile_tracker.motile.backend import SolverParams, build_candidate_graph, solve

# ---------------------------------------------------------------------------
# Gurobi marker handling
# ---------------------------------------------------------------------------


def pytest_collection_modifyitems(config, items):
    marker_expr = config.getoption("-m", default="")
    if marker_expr and "gurobi" in marker_expr:
        return  # user explicitly requested gurobi tests
    skip = pytest.mark.skip(reason="need -m gurobi to run")
    for item in items:
        if "gurobi" in item.keywords:
            item.add_marker(skip)


# ---------------------------------------------------------------------------
# Data loading fixtures (session-scoped, auto-downloads on first run)
# ---------------------------------------------------------------------------

_APPDIR = AppDirs("motile-tracker")
_DATA_DIR = Path(_APPDIR.user_data_dir)


@pytest.fixture(scope="session")
def hela_seg():
    """Uncropped Fluo-N2DL-HeLa segmentation array."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    layers = read_ctc_dataset("Fluo-N2DL-HeLa", _DATA_DIR)
    # layers is [raw_layer_data, seg_layer_data, points_layer_data]
    # seg_layer_data is (array, kwargs, type_str)
    return layers[1][0]


@pytest.fixture(scope="session")
def mouse_seg():
    """Mouse Embryo Membrane segmentation array."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    layers = read_zenodo_dataset(
        "Mouse_Embryo_Membrane", "imaging.tif", "segmentation.tif", _DATA_DIR
    )
    # layers is [raw_layer_data, seg_layer_data]
    return layers[1][0]


@pytest.fixture(scope="session")
def default_params():
    """Default SolverParams matching the run editor defaults."""
    return SolverParams()


# ---------------------------------------------------------------------------
# Candidate graph fixtures (session-scoped, built once)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def hela_cand_graph(hela_seg, default_params):
    """Pre-built candidate graph for HeLa."""
    return build_candidate_graph(hela_seg, default_params)


@pytest.fixture(scope="session")
def mouse_cand_graph(mouse_seg, default_params):
    """Pre-built candidate graph for Mouse Embryo."""
    return build_candidate_graph(mouse_seg, default_params)


# ---------------------------------------------------------------------------
# SCIP solve result fixtures (session-scoped, solved once for UI benchmarks)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def hela_solve_result(hela_seg, default_params, hela_cand_graph):
    """SCIP solve result (nx.DiGraph) for HeLa."""
    return solve(
        default_params,
        hela_seg,
        cand_graph=hela_cand_graph,
        backend=ilpy.Preference.Scip,
    )


@pytest.fixture(scope="session")
def mouse_solve_result(mouse_seg, default_params, mouse_cand_graph):
    """SCIP solve result (nx.DiGraph) for Mouse Embryo."""
    return solve(
        default_params,
        mouse_seg,
        cand_graph=mouse_cand_graph,
        backend=ilpy.Preference.Scip,
    )


@pytest.fixture(scope="session")
def hela_tracks(hela_seg, hela_solve_result):
    """SolutionTracks for HeLa (needed for extract_sorted_tracks)."""
    return SolutionTracks(graph=hela_solve_result, segmentation=hela_seg)


@pytest.fixture(scope="session")
def mouse_tracks(mouse_seg, mouse_solve_result):
    """SolutionTracks for Mouse Embryo."""
    return SolutionTracks(graph=mouse_solve_result, segmentation=mouse_seg)


@pytest.fixture(scope="session")
def colormap():
    """A default CyclicLabelColormap for tree widget rendering."""
    return napari.utils.colormaps.label_colormap(49, seed=0.5, background_value=0)


@pytest.fixture(scope="session")
def hela_track_df(hela_tracks, colormap):
    """Pre-computed track DataFrame for HeLa UI benchmarks."""
    result = extract_sorted_tracks(hela_tracks, colormap)
    return result[0]  # (df, axis_order) -> df


@pytest.fixture(scope="session")
def mouse_track_df(mouse_tracks, colormap):
    """Pre-computed track DataFrame for Mouse Embryo UI benchmarks."""
    result = extract_sorted_tracks(mouse_tracks, colormap)
    return result[0]
