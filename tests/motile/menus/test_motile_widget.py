"""Tests for MotileWidget - the main tracking control widget."""

from unittest.mock import MagicMock, patch

import networkx as nx
import numpy as np
import pytest
from funtracks.data_model import SolutionTracks

from motile_tracker.motile.backend import MotileRun, SolverParams
from motile_tracker.motile.menus.motile_widget import MotileWidget


class TestMotileWidgetInitialization:
    """Test MotileWidget initialization."""

    def test_initialization(self, make_napari_viewer):
        """Test MotileWidget creates all components."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Verify viewer is stored
        assert widget.viewer is viewer

        # Verify sub-widgets exist
        assert widget.edit_run_widget is not None
        assert widget.view_run_widget is not None

        # Verify view_run_widget starts hidden
        assert not widget.view_run_widget.isVisible()

    def test_initialization_connects_signals(self, make_napari_viewer):
        """Test MotileWidget connects all signals."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Verify signal connections exist
        # We can't easily test the connections directly, but we can verify the signals exist
        assert hasattr(widget, "solver_update")
        assert hasattr(widget, "new_run")
        assert hasattr(widget.edit_run_widget, "start_run")
        assert hasattr(widget.view_run_widget, "edit_run")


class TestViewRun:
    """Test view_run method."""

    def test_view_run_with_motile_run_shows_viewer(
        self, make_napari_viewer, segmentation_2d, qtbot
    ):
        """Test view_run with MotileRun shows viewer and hides editor."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)
        qtbot.addWidget(widget)
        widget.show()

        # Create a run
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Call view_run
        widget.view_run(run)

        # Verify viewer is shown and editor is hidden
        assert widget.view_run_widget.isVisible()
        assert not widget.edit_run_widget.isVisible()

    def test_view_run_with_solution_tracks_hides_viewer(
        self, make_napari_viewer, graph_2d, segmentation_2d
    ):
        """Test view_run with SolutionTracks (non-MotileRun) hides viewer."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create SolutionTracks (not MotileRun)
        tracks = SolutionTracks(graph=graph_2d, segmentation=segmentation_2d, ndim=3)

        # Call view_run
        widget.view_run(tracks)

        # Verify viewer is hidden
        assert not widget.view_run_widget.isVisible()


class TestEditRun:
    """Test edit_run method."""

    def test_edit_run_with_none_shows_editor(self, make_napari_viewer, qtbot):
        """Test edit_run with None shows editor and hides viewer."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)
        qtbot.addWidget(widget)
        widget.show()

        # Initially show viewer
        widget.view_run_widget.show()

        # Call edit_run with None
        widget.edit_run(None)

        # Verify editor is shown and viewer is hidden
        assert widget.edit_run_widget.isVisible()
        assert not widget.view_run_widget.isVisible()

    def test_edit_run_with_run_loads_params(
        self, make_napari_viewer, segmentation_2d, qtbot
    ):
        """Test edit_run with run loads parameters into editor."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)
        qtbot.addWidget(widget)
        widget.show()

        # Create a run with custom params
        custom_params = SolverParams(max_edge_distance=999.0)
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=custom_params,
        )

        # Mock new_run to verify it's called
        with patch.object(widget.edit_run_widget, "new_run") as mock_new_run:
            widget.edit_run(run)

            # Verify new_run was called with the run
            mock_new_run.assert_called_once_with(run)

        # Verify editor is shown
        assert widget.edit_run_widget.isVisible()


class TestGenerateTracks:
    """Test _generate_tracks method."""

    def test_generate_tracks_sets_status_initializing(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test _generate_tracks sets run status to initializing."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Mock solve_with_motile to prevent actual solving
        with patch.object(widget, "solve_with_motile") as mock_solve:
            mock_worker = MagicMock()
            mock_solve.return_value = mock_worker

            # Call _generate_tracks
            widget._generate_tracks(run)

            # Verify status was set
            assert run.status == "initializing"

            # Verify worker was started
            mock_worker.start.assert_called_once()

    def test_generate_tracks_shows_run_viewer(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test _generate_tracks calls view_run."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Mock solve_with_motile
        with patch.object(widget, "solve_with_motile") as mock_solve:
            mock_worker = MagicMock()
            mock_solve.return_value = mock_worker

            # Mock view_run to verify it's called
            with patch.object(widget, "view_run") as mock_view_run:
                widget._generate_tracks(run)

                # Verify view_run was called
                mock_view_run.assert_called_once_with(run)


class TestSolveWithMotile:
    """Test solve_with_motile method."""

    def test_solve_with_motile_with_segmentation(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test solve_with_motile uses segmentation when provided."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run with segmentation
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Mock the solve function
        with patch("motile_tracker.motile.menus.motile_widget.solve") as mock_solve:
            mock_solve.return_value = nx.DiGraph()

            # Get the worker function (not the decorator)
            worker_fn = widget.solve_with_motile.__wrapped__

            # Call the worker function directly
            worker_fn(widget, run)

            # Verify solve was called with segmentation
            mock_solve.assert_called_once()
            call_args = mock_solve.call_args
            assert call_args[0][1] is segmentation_2d  # input_data argument

    def test_solve_with_motile_with_points(self, make_napari_viewer, segmentation_2d):
        """Test solve_with_motile uses points when provided."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run with points (still need segmentation for MotileRun init, then clear it)
        points_data = np.array([[0, 10, 20], [1, 30, 40]])
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )
        # Set input_points and clear segmentation (points take priority when seg is None)
        run.input_points = points_data
        run.segmentation = None

        # Mock the solve function
        with patch("motile_tracker.motile.menus.motile_widget.solve") as mock_solve:
            mock_solve.return_value = nx.DiGraph()

            # Get the worker function
            worker_fn = widget.solve_with_motile.__wrapped__

            # Call the worker function directly
            worker_fn(widget, run)

            # Verify solve was called with points
            mock_solve.assert_called_once()
            call_args = mock_solve.call_args
            assert np.array_equal(call_args[0][1], points_data)

    def test_solve_with_motile_raises_without_input(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test solve_with_motile raises ValueError without input data."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run with segmentation but then clear it
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )
        # Clear both segmentation and points
        run.segmentation = None
        run.input_points = None

        # Get the worker function
        worker_fn = widget.solve_with_motile.__wrapped__

        # Verify it raises ValueError
        with pytest.raises(ValueError, match="Must have one of input segmentation"):
            worker_fn(widget, run)

    def test_solve_with_motile_shows_warning_for_empty_result(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test solve_with_motile shows warning when no tracks found."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Mock solve to return empty graph
        with patch("motile_tracker.motile.menus.motile_widget.solve") as mock_solve:
            empty_graph = nx.DiGraph()
            mock_solve.return_value = empty_graph

            # Mock show_warning
            with patch(
                "motile_tracker.motile.menus.motile_widget.show_warning"
            ) as mock_warning:
                # Get the worker function
                worker_fn = widget.solve_with_motile.__wrapped__

                # Call the worker function
                worker_fn(widget, run)

                # Verify warning was shown
                mock_warning.assert_called_once()
                assert "No tracks found" in mock_warning.call_args[0][0]


class TestOnSolverEvent:
    """Test _on_solver_event method."""

    def test_on_solver_event_presolve_sets_status(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test _on_solver_event with PRESOLVE event sets status."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Set the run in view_run_widget to avoid AttributeError
        widget.view_run_widget.run = run

        # Create PRESOLVE event
        event_data = {"event_type": "PRESOLVE"}

        # Call _on_solver_event
        widget._on_solver_event(run, event_data)

        # Verify status was set
        assert run.status == "presolving"
        assert run.gaps == []

    def test_on_solver_event_mipsol_sets_status_and_gap(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test _on_solver_event with MIPSOL event sets status and gap."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Set the run in view_run_widget
        widget.view_run_widget.run = run

        # Create MIPSOL event
        event_data = {"event_type": "MIPSOL", "gap": 0.5}

        # Call _on_solver_event
        widget._on_solver_event(run, event_data)

        # Verify status and gap were set
        assert run.status == "solving"
        assert len(run.gaps) == 1
        assert run.gaps[0] == 0.5

    def test_on_solver_event_emits_solver_update(
        self, make_napari_viewer, segmentation_2d, qtbot
    ):
        """Test _on_solver_event emits solver_update signal."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Set the run in view_run_widget
        widget.view_run_widget.run = run

        # Create event
        event_data = {"event_type": "PRESOLVE"}

        # Wait for signal
        with qtbot.waitSignal(widget.solver_update, timeout=1000):
            widget._on_solver_event(run, event_data)

    def test_on_solver_event_appends_gaps(self, make_napari_viewer, segmentation_2d):
        """Test _on_solver_event appends multiple gaps."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Set the run in view_run_widget
        widget.view_run_widget.run = run

        # First MIPSOL event
        event_data1 = {"event_type": "MIPSOL", "gap": 0.5}
        widget._on_solver_event(run, event_data1)

        # Second MIPSOL event
        event_data2 = {"event_type": "MIPSOL", "gap": 0.3}
        widget._on_solver_event(run, event_data2)

        # Verify both gaps were appended
        assert len(run.gaps) == 2
        assert run.gaps[0] == 0.5
        assert run.gaps[1] == 0.3


class TestOnSolveComplete:
    """Test _on_solve_complete method."""

    def test_on_solve_complete_sets_status_done(
        self, make_napari_viewer, segmentation_2d
    ):
        """Test _on_solve_complete sets status to done."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Set the run in view_run_widget
        widget.view_run_widget.run = run

        # Call _on_solve_complete
        widget._on_solve_complete(run)

        # Verify status was set
        assert run.status == "done"

    def test_on_solve_complete_emits_solver_update(
        self, make_napari_viewer, segmentation_2d, qtbot
    ):
        """Test _on_solve_complete emits solver_update signal."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Set the run in view_run_widget
        widget.view_run_widget.run = run

        # Wait for signal
        with qtbot.waitSignal(widget.solver_update, timeout=1000):
            widget._on_solve_complete(run)

    def test_on_solve_complete_emits_new_run(
        self, make_napari_viewer, segmentation_2d, qtbot
    ):
        """Test _on_solve_complete emits new_run signal."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Create a run
        run = MotileRun(
            graph=nx.DiGraph(),
            segmentation=segmentation_2d,
            run_name="test_run",
            solver_params=SolverParams(),
        )

        # Set the run in view_run_widget
        widget.view_run_widget.run = run

        # Wait for signal
        with qtbot.waitSignal(widget.new_run, timeout=1000) as blocker:
            widget._on_solve_complete(run)

        # Verify signal was emitted with correct args
        assert blocker.args[0] is run
        assert blocker.args[1] == "test_run"


class TestTitleWidget:
    """Test _title_widget method."""

    def test_title_widget_creates_label(self, make_napari_viewer):
        """Test _title_widget creates QLabel with rich text."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Call _title_widget
        title = widget._title_widget()

        # Verify it's a QLabel
        from qtpy.QtWidgets import QLabel

        assert isinstance(title, QLabel)

        # Verify it has text
        assert len(title.text()) > 0

        # Verify it has link to motile
        assert "motile" in title.text().lower()

    def test_title_widget_enables_external_links(self, make_napari_viewer):
        """Test _title_widget enables external links."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Call _title_widget
        title = widget._title_widget()

        # Verify external links are enabled
        assert title.openExternalLinks()

    def test_title_widget_enables_word_wrap(self, make_napari_viewer):
        """Test _title_widget enables word wrap."""
        viewer = make_napari_viewer()
        widget = MotileWidget(viewer)

        # Call _title_widget
        title = widget._title_widget()

        # Verify word wrap is enabled
        assert title.wordWrap()
