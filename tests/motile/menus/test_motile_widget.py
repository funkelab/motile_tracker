"""Tests for MotileWidget - the main tracking control widget."""

from unittest.mock import MagicMock, patch

import networkx as nx
import numpy as np
import pytest
from funtracks.data_model import SolutionTracks

from motile_tracker.motile.backend import MotileRun, SolverParams
from motile_tracker.motile.menus.motile_widget import MotileWidget


def test_motile_widget_initialization(make_napari_viewer):
    """Test MotileWidget initialization and signal connections."""
    viewer = make_napari_viewer()
    widget = MotileWidget(viewer)

    # Test 1: Verify all components created
    assert widget.viewer is viewer
    assert widget.edit_run_widget is not None
    assert widget.view_run_widget is not None
    assert not widget.view_run_widget.isVisible()

    # Test 2: Verify signal connections exist
    assert hasattr(widget, "solver_update")
    assert hasattr(widget, "new_run")
    assert hasattr(widget.edit_run_widget, "start_run")
    assert hasattr(widget.view_run_widget, "edit_run")


def test_view_run(make_napari_viewer, graph_2d, segmentation_2d, qtbot):
    """Test view_run method with different track types."""
    viewer = make_napari_viewer()
    widget = MotileWidget(viewer)
    qtbot.addWidget(widget)
    widget.show()

    # Test 1: MotileRun shows viewer and hides editor
    run = MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="test_run",
        solver_params=SolverParams(),
    )
    widget.view_run(run)
    assert widget.view_run_widget.isVisible()
    assert not widget.edit_run_widget.isVisible()

    # Test 2: SolutionTracks (non-MotileRun) hides viewer
    tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)
    widget.view_run(tracks)
    assert not widget.view_run_widget.isVisible()


def test_edit_run(make_napari_viewer, segmentation_2d, qtbot):
    """Test edit_run method."""
    viewer = make_napari_viewer()
    widget = MotileWidget(viewer)
    qtbot.addWidget(widget)
    widget.show()

    # Test 1: edit_run with None shows editor and hides viewer
    widget.view_run_widget.show()
    widget.edit_run(None)
    assert widget.edit_run_widget.isVisible()
    assert not widget.view_run_widget.isVisible()

    # Test 2: edit_run with run loads parameters into editor
    custom_params = SolverParams(max_edge_distance=999.0)
    run = MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="test_run",
        solver_params=custom_params,
    )
    with patch.object(widget.edit_run_widget, "new_run") as mock_new_run:
        widget.edit_run(run)
        mock_new_run.assert_called_once_with(run)
    assert widget.edit_run_widget.isVisible()


def test_generate_tracks(make_napari_viewer, segmentation_2d):
    """Test _generate_tracks method."""
    viewer = make_napari_viewer()
    widget = MotileWidget(viewer)

    run = MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="test_run",
        solver_params=SolverParams(),
    )

    with patch.object(widget, "solve_with_motile") as mock_solve:
        mock_worker = MagicMock()
        mock_solve.return_value = mock_worker

        # Test 1: Sets status to initializing and starts worker
        widget._generate_tracks(run)
        assert run.status == "initializing"
        mock_worker.start.assert_called_once()

    # Test 2: Calls view_run
    with (
        patch.object(widget, "solve_with_motile") as mock_solve,
        patch.object(widget, "view_run") as mock_view_run,
    ):
        mock_worker = MagicMock()
        mock_solve.return_value = mock_worker
        widget._generate_tracks(run)
        mock_view_run.assert_called_once_with(run)


def test_solve_with_motile(make_napari_viewer, segmentation_2d):
    """Test solve_with_motile method with different inputs."""
    viewer = make_napari_viewer()
    widget = MotileWidget(viewer)

    # Test 1: Uses segmentation when provided
    run = MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="test_run",
        solver_params=SolverParams(),
    )
    with patch("motile_tracker.motile.menus.motile_widget.solve") as mock_solve:
        mock_solve.return_value = nx.DiGraph()
        worker_fn = widget.solve_with_motile.__wrapped__
        worker_fn(widget, run)
        mock_solve.assert_called_once()
        call_args = mock_solve.call_args
        assert call_args[0][1] is segmentation_2d

    # Test 2: Uses points when provided
    points_data = np.array([[0, 10, 20], [1, 30, 40]])
    run2 = MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="test_run",
        solver_params=SolverParams(),
    )
    run2.input_points = points_data
    run2.segmentation = None
    with patch("motile_tracker.motile.menus.motile_widget.solve") as mock_solve:
        mock_solve.return_value = nx.DiGraph()
        worker_fn = widget.solve_with_motile.__wrapped__
        worker_fn(widget, run2)
        mock_solve.assert_called_once()
        call_args = mock_solve.call_args
        assert np.array_equal(call_args[0][1], points_data)

    # Test 3: Raises ValueError without input data
    run3 = MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="test_run",
        solver_params=SolverParams(),
    )
    run3.segmentation = None
    run3.input_points = None
    worker_fn = widget.solve_with_motile.__wrapped__
    with pytest.raises(ValueError, match="Must have one of input segmentation"):
        worker_fn(widget, run3)

    # Test 4: Shows warning for empty result
    run4 = MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="test_run",
        solver_params=SolverParams(),
    )
    with (
        patch("motile_tracker.motile.menus.motile_widget.solve") as mock_solve,
        patch("motile_tracker.motile.menus.motile_widget.show_warning") as mock_warning,
    ):
        mock_solve.return_value = nx.DiGraph()
        worker_fn = widget.solve_with_motile.__wrapped__
        worker_fn(widget, run4)
        mock_warning.assert_called_once()
        assert "No tracks found" in mock_warning.call_args[0][0]


def test_on_solver_event(make_napari_viewer, segmentation_2d, qtbot):
    """Test _on_solver_event method."""
    viewer = make_napari_viewer()
    widget = MotileWidget(viewer)

    run = MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="test_run",
        solver_params=SolverParams(),
    )
    widget.view_run_widget.run = run

    # Test 1: PRESOLVE event sets status
    event_data = {"event_type": "PRESOLVE"}
    widget._on_solver_event(run, event_data)
    assert run.status == "presolving"
    assert run.gaps == []

    # Test 2: MIPSOL event sets status and gap
    event_data = {"event_type": "MIPSOL", "gap": 0.5}
    widget._on_solver_event(run, event_data)
    assert run.status == "solving"
    assert len(run.gaps) == 1
    assert run.gaps[0] == 0.5

    # Test 3: Appends multiple gaps
    event_data2 = {"event_type": "MIPSOL", "gap": 0.3}
    widget._on_solver_event(run, event_data2)
    assert len(run.gaps) == 2
    assert run.gaps[0] == 0.5
    assert run.gaps[1] == 0.3

    # Test 4: Emits solver_update signal
    event_data = {"event_type": "MIPSOL", "gap": 0.1}
    with qtbot.waitSignal(widget.solver_update, timeout=1000):
        widget._on_solver_event(run, event_data)


def test_on_solve_complete(make_napari_viewer, segmentation_2d, qtbot):
    """Test _on_solve_complete method."""
    viewer = make_napari_viewer()
    widget = MotileWidget(viewer)

    run = MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="test_run",
        solver_params=SolverParams(),
    )
    widget.view_run_widget.run = run

    # Test 1: Sets status to done
    widget._on_solve_complete(run)
    assert run.status == "done"

    # Test 2: Emits solver_update signal
    with qtbot.waitSignal(widget.solver_update, timeout=1000):
        widget._on_solve_complete(run)

    # Test 3: Emits new_run signal with correct args
    with qtbot.waitSignal(widget.new_run, timeout=1000) as blocker:
        widget._on_solve_complete(run)
    assert blocker.args[0] is run
    assert blocker.args[1] == "test_run"


def test_title_widget(make_napari_viewer):
    """Test _title_widget method."""
    from qtpy.QtWidgets import QLabel

    viewer = make_napari_viewer()
    widget = MotileWidget(viewer)
    title = widget._title_widget()

    # Test 1: Creates QLabel with rich text
    assert isinstance(title, QLabel)
    assert len(title.text()) > 0
    assert "motile" in title.text().lower()

    # Test 2: Enables external links
    assert title.openExternalLinks()

    # Test 3: Enables word wrap
    assert title.wordWrap()
