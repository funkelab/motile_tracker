"""Fixtures for the benchmark suite.

Runs under pytest's default (prepend) import mode, which puts this directory on
sys.path, so ``synthetic_data`` is importable by bare name here and in the bench
modules. The parent ``tests/conftest.py`` autouse ``reset_tracks_viewer`` fixture
clears the TracksViewer singleton around every test, so each benchmark builds its
own viewer/app; mutating benchmarks additionally use freshly-generated tracks.
"""

from __future__ import annotations

import os

import pytest
from synthetic_data import PRESETS, generate_synthetic_tracks

from motile_tracker.application_menus import StartupWidget
from motile_tracker.data_views import TreeWidget
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer

# Preset selectable via env var for quick local runs, e.g. MT_BENCH_PRESET=small.
BENCH_PARAMS = PRESETS[os.environ.get("MT_BENCH_PRESET", "large")]


@pytest.fixture(scope="session")
def bench_params():
    return BENCH_PARAMS


@pytest.fixture(scope="session")
def shared_tracks(bench_params):
    """Session-scoped tracks for READ-ONLY benchmarks (never mutate these)."""
    return generate_synthetic_tracks(bench_params)


@pytest.fixture
def fresh_tracks(bench_params):
    """Freshly-generated tracks for MUTATING benchmarks (delete/add/undo/redo)."""
    return generate_synthetic_tracks(bench_params)


@pytest.fixture
def build_app(make_napari_viewer):
    """Return a builder: tracks -> (viewer, tracks_viewer, tree_widget).

    Uses make_napari_viewer so the viewer is torn down by napari's fixture.
    """

    def _build(tracks):
        viewer = make_napari_viewer()
        StartupWidget(viewer, mode="editing")
        tv = TracksViewer.get_instance(viewer)
        tv.tracks_list.add_tracks(tracks, "synthetic")
        tree_widget = viewer.window._qt_window.findChild(TreeWidget)
        return viewer, tv, tree_widget

    return _build
