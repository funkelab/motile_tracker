# do not put from __future__ import annotations as it breaks the injection

import logging

from finn import Viewer
from finn.track_data_views.views_coordinator.tracks_viewer import TracksViewer
from finn.utils.notifications import show_warning
from funtracks.data_model import SolutionTracks
from psygnal import Signal
from qtpy.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)
from superqt.utils import thread_worker

from motile_tracker.motile.backend import MotileRun, solve

from .run_editor import RunEditor
from .run_viewer import RunViewer

logger = logging.getLogger(__name__)


class MotileWidget(QWidget):
    """A widget that controls the backend components of the motile tracker.
    Recieves user input about solver parameters, runs motile, and passes
    results to the TrackingViewController.
    """

    # A signal for passing events from the motile solver to the run view widget
    # To provide updates on progress of the solver
    solver_update = Signal()
    new_run = Signal(SolutionTracks, str)

    def __init__(self, viewer: Viewer):
        super().__init__()
        self.viewer: Viewer = viewer
        tracks_viewer = TracksViewer.get_instance(self.viewer)
        self.new_run.connect(tracks_viewer.tracks_list.add_tracks)
        tracks_viewer.tracks_list.view_tracks.connect(self.view_run)

        # Create sub-widgets and connect signals
        self.edit_run_widget = RunEditor(self.viewer)
        self.edit_run_widget.start_run.connect(self._generate_tracks)

        self.view_run_widget = RunViewer()
        self.view_run_widget.edit_run.connect(self.edit_run)
        self.view_run_widget.hide()
        self.solver_update.connect(self.view_run_widget.solver_event_update)

        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self._title_widget())
        main_layout.addWidget(self.view_run_widget)
        main_layout.addWidget(self.edit_run_widget)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def view_run(self, tracks: SolutionTracks) -> None:
        """Populates the run viewer with the output
        of the provided run.

        Args:
            run (MotileRun): The run to view
        """
        if isinstance(tracks, MotileRun):
            self.view_run_widget.update_run(tracks)
            self.edit_run_widget.hide()
            self.view_run_widget.show()
        else:
            self.view_run_widget.hide()

    def edit_run(self, run: MotileRun | None):
        """Create or edit a new run in the run editor. Also removes solution layers
        from the napari viewer.
        Args:
            run (MotileRun | None): Initialize the new run with the parameters and name
                from this run. If not provided, uses the SolverParams default values.
        """
        self.view_run_widget.hide()
        self.edit_run_widget.show()
        if run:
            self.edit_run_widget.new_run(run)

    def _generate_tracks(self, run: MotileRun) -> None:
        """Called when we start solving a new run. Switches from run editor to run
        viewer and starts solving of the new run in a separate thread to avoid blocking

        Args:
            run (MotileRun): Start solving this motile run.
        """
        run.status = "initializing"
        self.view_run(run)
        worker = self.solve_with_motile(run)
        worker.returned.connect(self._on_solve_complete)
        worker.start()

    @thread_worker
    def solve_with_motile(self, run: MotileRun) -> MotileRun:
        """Runs the solver and relabels the segmentation to match
        the solution graph.
        Emits: self.solver_event when the solver provides an update
        (will be emitted from the thread, which is why it needs to be an
        event and not just a normal function callback)

        Args:
            run (MotileRun): A run with name, parameters, and input segmentation,
                but not including the output graph or segmentation.

        Returns:
            MotileRun: The provided run with the output graph and segmentation included.
        """
        if run.segmentation is not None:
            input_data = run.segmentation
        elif run.input_points is not None:
            input_data = run.input_points
        else:
            raise ValueError("Must have one of input segmentation or points")
        run.graph = solve(
            run.solver_params,
            input_data,
            lambda event_data: self._on_solver_event(run, event_data),
            scale=run.scale,
        )

        run._initialize_track_ids()

        if run.graph.number_of_nodes() == 0:
            show_warning(
                "No tracks found - try making your edge selection value more negative"
            )
        return run

    def _on_solver_event(self, run: MotileRun, event_data: dict) -> None:
        """Parse the solver event and set the run status and gap accordingly.
        Also emits a solver_update event to tell the run viewer to update.
        Note: This will simply tell the run viewer to refresh its plot and
        status. If the run viewer is not viewing this run, it will refresh
        anyways, which is pointless but not harmful.

        Args:
            run (MotileRun): The run that the solver is working on
            event_data (dict): The solver event data from ilpy.EventData
        """
        event_type = event_data["event_type"]
        if event_type in ["PRESOLVE", "PRESOLVEROUND"] and run.status != "presolving":
            run.status = "presolving"
            run.gaps = []  # try this to remove the weird initial gap for gurobi
            self.solver_update.emit()
        elif event_type in ["MIPSOL", "BESTSOLFOUND"]:
            run.status = "solving"
            gap = event_data["gap"]
            if run.gaps is None:
                run.gaps = []
            run.gaps.append(gap)
            self.solver_update.emit()

    def _on_solve_complete(self, run: MotileRun) -> None:
        """Called when the solver thread returns. Updates the run status to done
        and tells the run viewer to update.

        Args:
            run (MotileRun): The completed run
        """
        run.status = "done"
        self.solver_update.emit()
        self.new_run(run, run.run_name)

    def _title_widget(self) -> QWidget:
        """Create the title and intro paragraph widget, with links to docs

        Returns:
            QWidget: A widget introducing the motile tracker and linking to docs
        """
        richtext = r"""<h3>Tracking with Motile</h3>
        <p>This tracker uses the
        <a href="https://funkelab.github.io/motile/"><font color=yellow>motile</font></a> library to
        track objects with global optimization. See the
        <a href="https://funkelab.github.io/motile_tracker/"><font color=yellow>user guide</font></a>
        for a tutorial to the tracker functionality."""  # noqa
        label = QLabel(richtext)
        label.setWordWrap(True)
        label.setOpenExternalLinks(True)
        return label
