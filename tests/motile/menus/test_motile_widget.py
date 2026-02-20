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
    with (
        patch(
            "motile_tracker.motile.menus.motile_widget.build_candidate_graph"
        ) as mock_build,
        patch("motile_tracker.motile.menus.motile_widget.solve") as mock_solve,
    ):
        mock_build.return_value = nx.DiGraph()
        mock_solve.return_value = nx.DiGraph()
        worker_fn = widget.solve_with_motile.__wrapped__
        worker_fn(widget, run)
        mock_build.assert_called_once()
        assert mock_build.call_args[0][0] is segmentation_2d
        mock_solve.assert_called_once()

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
    with (
        patch(
            "motile_tracker.motile.menus.motile_widget.build_candidate_graph"
        ) as mock_build,
        patch("motile_tracker.motile.menus.motile_widget.solve") as mock_solve,
    ):
        mock_build.return_value = nx.DiGraph()
        mock_solve.return_value = nx.DiGraph()
        worker_fn = widget.solve_with_motile.__wrapped__
        worker_fn(widget, run2)
        mock_build.assert_called_once()
        assert np.array_equal(mock_build.call_args[0][0], points_data)
        mock_solve.assert_called_once()

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
        patch(
            "motile_tracker.motile.menus.motile_widget.build_candidate_graph"
        ) as mock_build,
        patch("motile_tracker.motile.menus.motile_widget.solve") as mock_solve,
        patch("motile_tracker.motile.menus.motile_widget.show_warning") as mock_warning,
    ):
        mock_build.return_value = nx.DiGraph()
        mock_solve.return_value = nx.DiGraph()
        worker_fn = widget.solve_with_motile.__wrapped__
        worker_fn(widget, run4)
        mock_warning.assert_called_once()
        assert "No tracks found" in mock_warning.call_args[0][0]

    # Test 5: Relabel segmentation when there are duplicate labels
    segmentation_2d[1][10:10, 10:10] = 1  # duplicate value

    run5 = MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="test_run",
        solver_params=SolverParams(),
    )

    with (
        patch(
            "motile_tracker.motile.menus.motile_widget.build_candidate_graph"
        ) as mock_build,
        patch("motile_tracker.motile.menus.motile_widget.solve") as mock_solve,
        patch(
            "motile_tracker.motile.menus.motile_widget.ensure_unique_labels"
        ) as mock_relabel,
    ):
        mock_build.side_effect = [
            ValueError("Duplicate values found among nodes"),
            nx.DiGraph(),
        ]
        mock_solve.return_value = nx.DiGraph()

        relabeled = segmentation_2d.copy()
        relabeled[1][10:10, 10:10] = 100
        mock_relabel.return_value = relabeled

        worker_fn = widget.solve_with_motile.__wrapped__
        worker_fn(widget, run5)

        # build_candidate_graph called twice (once failed, once after relabel)
        assert mock_build.call_count == 2

        # relabel called once
        assert mock_relabel.call_count == 1

        # solve called once with the pre-built graph
        assert mock_solve.call_count == 1
        call_kwargs = mock_solve.call_args[1]
        assert call_kwargs["cand_graph"] is not None

        # solve received the relabeled segmentation
        assert mock_solve.call_args[0][1] is relabeled


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
