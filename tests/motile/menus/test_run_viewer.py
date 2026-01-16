from unittest.mock import patch

import networkx as nx
import pytest
from qtpy.QtWidgets import QPushButton

from motile_tracker.motile.backend import MotileRun, SolverParams
from motile_tracker.motile.menus.run_viewer import RunViewer


@pytest.fixture
def run_viewer(qtbot):
    """Fixture for creating a RunViewer widget."""
    widget = RunViewer()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def sample_run(segmentation_2d):
    """Fixture for creating a sample MotileRun."""
    return MotileRun(
        graph=nx.DiGraph(),
        segmentation=segmentation_2d,
        run_name="test_run",
        solver_params=SolverParams(),
    )


class TestRunViewerInitialization:
    """Test RunViewer initialization."""

    def test_initialization(self, run_viewer):
        """Test RunViewer creates all components."""
        assert run_viewer.run is None
        assert run_viewer.params_widget is not None
        assert run_viewer.solver_label is not None
        assert run_viewer.gap_plot is not None

    def test_initial_title(self, run_viewer):
        """Test RunViewer has correct initial title."""
        assert run_viewer.title() == "Run Viewer"

    def test_has_edit_run_signal(self, run_viewer):
        """Test RunViewer has edit_run signal."""
        assert hasattr(run_viewer, "edit_run")


class TestUpdateRun:
    """Test update_run method."""

    def test_update_run_sets_run(self, run_viewer, sample_run):
        """Test update_run stores the run."""
        run_viewer.update_run(sample_run)
        assert run_viewer.run is sample_run

    def test_update_run_updates_title(self, run_viewer, sample_run):
        """Test update_run updates the title with run name and time."""
        run_viewer.update_run(sample_run)

        title = run_viewer.title()
        assert "Run Viewer: test_run" in title
        # Check that time is included (format: mm/dd/yy, HH:MM:SS)
        assert "(" in title and ")" in title

    def test_update_run_emits_params_signal(self, run_viewer, sample_run, qtbot):
        """Test update_run emits params_widget.new_params signal."""
        with qtbot.waitSignal(run_viewer.params_widget.new_params, timeout=1000):
            run_viewer.update_run(sample_run)

    def test_update_run_calls_solver_event_update(self, run_viewer, sample_run):
        """Test update_run calls solver_event_update."""
        with patch.object(run_viewer, "solver_event_update") as mock_update:
            run_viewer.update_run(sample_run)
            mock_update.assert_called_once()


class TestBackToEditWidget:
    """Test _back_to_edit_widget and related methods."""

    def test_back_to_edit_button_exists(self, run_viewer):
        """Test back to editing button is created."""
        buttons = run_viewer.findChildren(QPushButton)
        back_buttons = [b for b in buttons if "Back to editing" in b.text()]
        assert len(back_buttons) == 1

    def test_back_to_edit_button_emits_none(self, run_viewer, qtbot, sample_run):
        """Test back to editing button emits None."""
        run_viewer.run = sample_run

        buttons = run_viewer.findChildren(QPushButton)
        back_button = [b for b in buttons if "Back to editing" in b.text()][0]

        with qtbot.waitSignal(run_viewer.edit_run) as blocker:
            back_button.click()

        assert blocker.args[0] is None

    def test_edit_this_run_button_exists(self, run_viewer):
        """Test edit this run button is created."""
        buttons = run_viewer.findChildren(QPushButton)
        edit_buttons = [b for b in buttons if "Edit this run" in b.text()]
        assert len(edit_buttons) == 1

    def test_edit_this_run_button_emits_run(self, run_viewer, qtbot, sample_run):
        """Test edit this run button emits current run."""
        run_viewer.run = sample_run

        buttons = run_viewer.findChildren(QPushButton)
        edit_button = [b for b in buttons if "Edit this run" in b.text()][0]

        with qtbot.waitSignal(run_viewer.edit_run) as blocker:
            edit_button.click()

        assert blocker.args[0] is sample_run


class TestEmitRun:
    """Test _emit_run method."""

    def test_emit_run_emits_signal(self, run_viewer, qtbot, sample_run):
        """Test _emit_run emits edit_run signal with current run."""
        run_viewer.run = sample_run

        with qtbot.waitSignal(run_viewer.edit_run) as blocker:
            run_viewer._emit_run()

        assert blocker.args[0] is sample_run


class TestProgressWidget:
    """Test _progress_widget and components."""

    def test_progress_widget_has_solver_label(self, run_viewer):
        """Test progress widget contains solver label."""
        assert run_viewer.solver_label is not None
        assert run_viewer.solver_label.text() == ""

    def test_progress_widget_has_gap_plot(self, run_viewer):
        """Test progress widget contains gap plot."""
        assert run_viewer.gap_plot is not None


class TestPlotWidget:
    """Test _plot_widget method."""

    def test_plot_widget_created(self, run_viewer):
        """Test plot widget is created with correct settings."""
        gap_plot = run_viewer.gap_plot
        assert gap_plot is not None

    def test_plot_widget_log_mode(self, run_viewer):
        """Test plot widget has logarithmic y-axis."""
        gap_plot = run_viewer.gap_plot
        plot_item = gap_plot.plotItem

        # Check that y-axis is in log mode
        assert plot_item.ctrl.logYCheck.isChecked()

    def test_plot_widget_labels(self, run_viewer):
        """Test plot widget has correct axis labels."""
        gap_plot = run_viewer.gap_plot
        plot_item = gap_plot.plotItem

        # Check axis labels
        left_label = plot_item.getAxis("left").labelText
        bottom_label = plot_item.getAxis("bottom").labelText

        assert "Gap" in left_label
        assert "Solver round" in bottom_label


class TestSetSolverLabel:
    """Test _set_solver_label method."""

    def test_set_solver_label(self, run_viewer):
        """Test _set_solver_label updates label text."""
        run_viewer._set_solver_label("initializing")
        assert run_viewer.solver_label.text() == "Solver status: initializing"

        run_viewer._set_solver_label("solving")
        assert run_viewer.solver_label.text() == "Solver status: solving"

        run_viewer._set_solver_label("done")
        assert run_viewer.solver_label.text() == "Solver status: done"


class TestSolverEventUpdate:
    """Test solver_event_update method."""

    def test_solver_event_update_initializing(self, run_viewer, sample_run):
        """Test solver_event_update with initializing status."""
        sample_run.status = "initializing"
        sample_run.gaps = None
        run_viewer.run = sample_run

        run_viewer.solver_event_update()

        assert "initializing" in run_viewer.solver_label.text()

    def test_solver_event_update_presolving(self, run_viewer, sample_run):
        """Test solver_event_update with presolving status."""
        sample_run.status = "presolving"
        sample_run.gaps = []
        run_viewer.run = sample_run

        run_viewer.solver_event_update()

        assert "presolving" in run_viewer.solver_label.text()

    def test_solver_event_update_solving(self, run_viewer, sample_run):
        """Test solver_event_update with solving status."""
        sample_run.status = "solving"
        sample_run.gaps = [0.5, 0.3, 0.1]
        run_viewer.run = sample_run

        run_viewer.solver_event_update()

        assert "solving" in run_viewer.solver_label.text()

    def test_solver_event_update_done(self, run_viewer, sample_run):
        """Test solver_event_update with done status."""
        sample_run.status = "done"
        sample_run.gaps = [0.5, 0.3, 0.1, 0.05]
        run_viewer.run = sample_run

        run_viewer.solver_event_update()

        assert "done" in run_viewer.solver_label.text()

    def test_solver_event_update_with_gaps(self, run_viewer, sample_run):
        """Test solver_event_update plots gap data."""
        sample_run.status = "solving"
        sample_run.gaps = [0.5, 0.3, 0.1]
        run_viewer.run = sample_run

        run_viewer.solver_event_update()

        # Check that plot has data
        plot_item = run_viewer.gap_plot.getPlotItem()
        data_items = plot_item.listDataItems()
        assert len(data_items) > 0

    def test_solver_event_update_clears_plot(self, run_viewer, sample_run):
        """Test solver_event_update clears plot before updating."""
        sample_run.status = "solving"
        sample_run.gaps = [0.5, 0.3]
        run_viewer.run = sample_run

        # First update with some data
        run_viewer.solver_event_update()

        # Update with different data
        sample_run.gaps = [0.8, 0.6, 0.4, 0.2]
        run_viewer.solver_event_update()

        # Should have only one plot line (previous cleared)
        plot_item = run_viewer.gap_plot.getPlotItem()
        data_items = plot_item.listDataItems()
        assert len(data_items) == 1

    def test_solver_event_update_handles_none_gaps(self, run_viewer, sample_run):
        """Test solver_event_update handles None gaps."""
        sample_run.status = "initializing"
        sample_run.gaps = None
        run_viewer.run = sample_run

        # Should not raise exception
        run_viewer.solver_event_update()

        # Plot should be empty
        plot_item = run_viewer.gap_plot.getPlotItem()
        data_items = plot_item.listDataItems()
        assert len(data_items) == 0

    def test_solver_event_update_handles_empty_gaps(self, run_viewer, sample_run):
        """Test solver_event_update handles empty gaps list."""
        sample_run.status = "presolving"
        sample_run.gaps = []
        run_viewer.run = sample_run

        # Should not raise exception
        run_viewer.solver_event_update()

        # Plot should be empty
        plot_item = run_viewer.gap_plot.getPlotItem()
        data_items = plot_item.listDataItems()
        assert len(data_items) == 0

    def test_solver_event_update_handles_plot_exception(self, run_viewer, sample_run):
        """Test solver_event_update handles pyqtgraph exceptions."""
        sample_run.status = "solving"
        sample_run.gaps = [0.5, 0.3, 0.1]
        run_viewer.run = sample_run

        # Mock plot to raise exception about array lengths
        with patch.object(
            run_viewer.gap_plot.getPlotItem(),
            "plot",
            side_effect=Exception("X and Y arrays must be the same length"),
        ):
            # Should catch and ignore the exception
            run_viewer.solver_event_update()


class TestResetProgress:
    """Test reset_progress method."""

    def test_reset_progress_sets_label(self, run_viewer):
        """Test reset_progress sets label to 'not running'."""
        run_viewer._set_solver_label("solving")
        run_viewer.reset_progress()

        assert "not running" in run_viewer.solver_label.text()

    def test_reset_progress_clears_plot(self, run_viewer, sample_run):
        """Test reset_progress clears the gap plot."""
        sample_run.status = "solving"
        sample_run.gaps = [0.5, 0.3, 0.1]
        run_viewer.run = sample_run

        # Add some data to plot
        run_viewer.solver_event_update()

        # Reset progress
        run_viewer.reset_progress()

        # Plot should be empty
        plot_item = run_viewer.gap_plot.getPlotItem()
        data_items = plot_item.listDataItems()
        assert len(data_items) == 0
