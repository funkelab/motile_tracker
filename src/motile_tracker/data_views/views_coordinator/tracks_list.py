from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from warnings import warn

from fonticon_fa6 import FA6S
from funtracks.data_model import SolutionTracks, Tracks
from funtracks.import_export import import_from_geff, write_to_geff
from napari._qt.qt_resources import QColoredSVGIcon
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from superqt.fonticon import icon as qticon

from motile_tracker.import_export.menus.export_dialog import ExportDialog
from motile_tracker.import_export.menus.import_dialog import (
    ImportDialog,
)
from motile_tracker.motile.backend.motile_run import MotileRun


def _as_solution_tracks(tracks: Tracks) -> SolutionTracks:
    """Return a SolutionTracks view of the given tracks.

    The list stores plain Tracks, but the views and actions downstream of
    view_tracks still require track IDs, so they are handed a SolutionTracks.
    Objects that are already SolutionTracks (including MotileRun) are passed
    through unchanged, so a solved run keeps its solver params and identity.

    Defers to the (deprecated) SolutionTracks.from_tracks rather than
    reconstructing here, so that scale, ndim, features and segmentation are
    carried over in one place instead of being re-derived.

    TODO: remove once motile_tracker operates on Tracks directly and consumers
    call tracks.graph_solution themselves.
    """
    if isinstance(tracks, SolutionTracks):
        return tracks
    return SolutionTracks.from_tracks(tracks)


class TracksButton(QWidget):
    # https://doc.qt.io/qt-5/qlistwidget.html#setItemWidget
    # I think this means if we want static buttons we can just make the row here
    # but if we want to change the buttons we need to do something more complex
    # Columns: Run name, save, export, delete buttons
    def __init__(self, tracks: Tracks, name: str):
        super().__init__()
        self.tracks = tracks
        self.name = QLabel(name)
        self.name.setFixedHeight(20)
        delete_icon = QColoredSVGIcon.from_resources("delete").colored("white")
        self.delete = QPushButton(icon=delete_icon)
        self.delete.setFixedSize(20, 20)
        self.delete.setToolTip("Remove track result")
        save_icon = qticon(FA6S.floppy_disk, color="white")
        self.save = QPushButton(icon=save_icon)
        self.save.setToolTip("Save tracks")
        self.save.setFixedSize(20, 20)
        export_icon = qticon(FA6S.file_export, color="white")
        self.export = QPushButton(icon=export_icon)
        self.export.setFixedSize(20, 20)
        self.export.setToolTip("Export tracks to CSV or geff")
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(self.name)
        layout.addWidget(self.save)
        layout.addWidget(self.export)
        layout.addWidget(self.delete)
        self.setLayout(layout)

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(30)
        return hint


class TracksList(QGroupBox):
    """Widget for holding in-memory Tracks. Emits a view_tracks signal whenever
    a run is selected in the list, useful for telling the TracksViewer to display the
    selected tracks.
    """

    view_tracks = Signal(Tracks, str)
    request_colormap = Signal()

    tracks_saved = Signal(object, Path)
    """Emitted after tracks are saved to disk. Arguments: (tracks, path).
    Dependent applications can connect to this signal to save additional
    data (e.g. solver parameters) alongside the tracks.

    The path is the geff store the tracks were written to. For a MotileRun that
    is the tracks.geff inside the timestamped run directory, so data saved
    beside the tracks (e.g. solver params) lives in the parent."""

    tracks_loaded = Signal(object, Path)
    """Emitted after tracks are loaded from disk. Arguments: (tracks, path).
    Dependent applications can connect to this signal to load additional
    data (e.g. solver parameters) from the same location.

    The path is the geff store the tracks were read from, matching what
    tracks_saved reports for the same tracks. For a MotileRun that is the
    tracks.geff inside the run directory, so data stored beside the tracks
    (e.g. solver params) lives in the parent. It is never a container a geff
    merely happened to be found inside.

    The exception is a CSV import, which reports the .csv file, and a v1 run
    directory, which has no geff and reports the directory itself. Listeners
    should tolerate a file as well as a directory."""

    def __init__(self):
        super().__init__(title="Results List")

        self.colormap = None
        self.file_dialog = QFileDialog()
        self.file_dialog.setFileMode(QFileDialog.Directory)
        self.file_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        self.save_dialog = QFileDialog()
        self.save_dialog.setFileMode(QFileDialog.Directory)
        self.save_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        # Saving plain Tracks/SolutionTracks writes a geff store directly at the
        # chosen path, so the user must be able to name a new store (or pick an
        # existing one to replace). AcceptSave also gives us the native
        # "file exists, replace?" confirmation for free.
        self.save_geff_dialog = QFileDialog()
        self.save_geff_dialog.setFileMode(QFileDialog.AnyFile)
        self.save_geff_dialog.setAcceptMode(QFileDialog.AcceptSave)
        self.save_geff_dialog.setNameFilter("Geff store (*.geff)")
        self.save_geff_dialog.setDefaultSuffix("geff")

        self.tracks_list = QListWidget()
        self.tracks_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.tracks_list.itemSelectionChanged.connect(self._selection_changed)

        load_menu = QHBoxLayout()
        self.dropdown_menu = QComboBox()
        self.dropdown_menu.addItems(
            [
                "Tracks (geff)",
                "Motile Run",
                "External tracks from CSV",
                "External tracks from geff",
            ]
        )

        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load_tracks)

        load_menu.addWidget(self.dropdown_menu)
        load_menu.addWidget(load_button)

        layout = QVBoxLayout()
        layout.addWidget(self.tracks_list)
        layout.addLayout(load_menu)
        self.setLayout(layout)

    def _load_tracks(self, import_type: str) -> tuple[Tracks, str, Path | None] | None:
        """Load externally generated tracks (CSV or geff) via the import dialog.

        Returns (tracks, name, path), where the path may be None because the
        import dialog does not always know the file the tracks came from.
        """
        dialog = ImportDialog(import_type)
        if dialog.exec_() != QDialog.Accepted or dialog.tracks is None:
            return None
        return dialog.tracks, dialog.name, dialog.source_path

    def _selection_changed(self):
        selected = self.tracks_list.selectedItems()
        if selected:
            tracks_button = self.tracks_list.itemWidget(selected[0])
            self.view_tracks.emit(
                _as_solution_tracks(tracks_button.tracks), tracks_button.name.text()
            )

    def add_tracks(self, tracks: Tracks, name: str, select=True):
        """Add tracks to the list and optionally select them. Will make a new
        row in the list UI representing the given tracks.

        Accepts any Tracks object directly (SolutionTracks, MotileRun, etc.).

        Note: selecting the tracks will also emit the selection changed event on
        the list.

        Args:
            tracks (Tracks): the tracks object to add to the results list.
            name (str): the name of the tracks to display
            select (bool, optional): Whether or not to select the new tracks item in the
                list (and thus display it in the tracks viewer). Defaults to True.
        """
        item = QListWidgetItem(self.tracks_list)
        tracks_row = TracksButton(tracks, name)
        self.tracks_list.setItemWidget(item, tracks_row)
        item.setSizeHint(tracks_row.minimumSizeHint())
        self.tracks_list.addItem(item)
        tracks_row.delete.clicked.connect(partial(self.remove_tracks, item))
        tracks_row.export.clicked.connect(partial(self.show_export_dialog, item))
        tracks_row.save.clicked.connect(partial(self.save_tracks, item))
        if select:
            self.tracks_list.setCurrentRow(len(self.tracks_list) - 1)

    def show_export_dialog(self, item: QListWidgetItem) -> None:
        """Prompt user to choose export format (csv or geff), then export the tracks
        object from the list accordingly.
        You must pass the list item that represents the tracks, not the tracks object
        itself.

        Args:
            item (QListWidgetItem):  The list item containing the TracksButton that
                represents a set of tracks.
        """

        widget: TracksButton = self.tracks_list.itemWidget(item)
        tracks: Tracks = widget.tracks
        name: str = widget.name.text()
        self.request_colormap.emit()
        colormap = self.colormap

        ExportDialog.show_export_dialog(
            self, tracks=tracks, name=name, colormap=colormap
        )

    def save_tracks(self, item: QListWidgetItem):
        """Saves a tracks object from the list. You must pass the list item that
        represents the tracks, not the tracks object itself.

        For MotileRun objects, the user picks a parent directory and
        MotileRun.save() creates a timestamped subdirectory inside it,
        storing solver params alongside the tracks.

        For plain Tracks/SolutionTracks, the user names a geff store (or
        selects an existing one to replace) and write_to_geff writes the
        store directly at that path.

        After saving, emits the tracks_saved signal with the geff store that
        was written, so that downstream code can save additional data beside
        it. For a MotileRun that is the tracks.geff inside the run directory,
        not the run directory itself.

        Args:
            item (QListWidgetItem): The list item to save. This list item
                contains the TracksButton that represents a set of tracks.
        """
        widget: TracksButton = self.tracks_list.itemWidget(item)
        tracks: Tracks = widget.tracks
        if isinstance(tracks, MotileRun):
            if not self.save_dialog.exec_():
                return
            directory = Path(self.save_dialog.selectedFiles()[0])
            run_dir = tracks.save(directory)
            # Report the geff store, not the run directory that contains it, so
            # that saving and loading name the same thing. Sibling data (solver
            # params) lives in its parent. save() always writes a geff, so
            # geff_path is never None here (only loaded v1 runs lack one).
            saved_path = MotileRun.geff_path(run_dir)
        else:
            name = widget.name.text()
            self.save_geff_dialog.selectFile(str(Path.home() / f"{name}.geff"))
            if not self.save_geff_dialog.exec_():
                return
            saved_path = Path(self.save_geff_dialog.selectedFiles()[0])
            write_to_geff(tracks, saved_path, overwrite=True)
        self.tracks_saved.emit(tracks, saved_path)

    def remove_tracks(self, item: QListWidgetItem):
        """Remove a tracks object from the list. You must pass the list item that
        represents the tracks, not the tracks object itself.

        Args:
            item (QListWidgetItem): The list item to remove. This list item
                contains the TracksButton that represents a set of tracks.
        """
        row = self.tracks_list.indexFromItem(item).row()
        self.tracks_list.takeItem(row)

    def load_tracks(self):
        """Load tracks from disk, depending on the choice in the dropdown menu.

        Each loader returns the loaded tracks along with the name to display and
        the path they came from, or None if the user cancelled or the load
        failed. Adding the tracks to the list and announcing them via
        tracks_loaded happens here, so every load route behaves the same way.
        """
        selection = self.dropdown_menu.currentText()
        if selection == "Tracks (geff)":
            result = self.load_internal_tracks()
        elif selection == "Motile Run":
            result = self.load_motile_run()
        elif selection == "External tracks from CSV":
            result = self._load_tracks(import_type="csv")
        elif selection == "External tracks from geff":
            result = self._load_tracks("geff")
        else:
            return

        if result is None:
            return
        tracks, name, source_path = result
        self.add_tracks(tracks, name, select=True)
        if source_path is not None:
            self.tracks_loaded.emit(tracks, source_path)

    def _load_from_dialog(
        self,
        loader: Callable[[Path], Tracks],
        geff_path: Callable[[Path], Path | None] | None = None,
    ) -> tuple[Tracks, str, Path] | None:
        """Ask the user for a directory and load tracks from it with `loader`.

        The name shown in the list comes from the directory the user picked. The
        reported path is the geff store that was actually read, which `geff_path`
        resolves when the user picks a directory containing one rather than the
        store itself.

        Returns (tracks, name, path), or None if the user cancelled or the
        directory did not contain loadable tracks.
        """
        if not self.file_dialog.exec_():
            return None
        directory = Path(self.file_dialog.selectedFiles()[0])
        try:
            tracks = loader(directory)
        except (ValueError, FileNotFoundError) as e:
            warn(f"Could not load tracks from {directory}: {e}", stacklevel=2)
            return None
        source = directory if geff_path is None else geff_path(directory)
        return tracks, directory.stem, source or directory

    def load_internal_tracks(self) -> tuple[Tracks, str, Path] | None:
        """Load tracks saved in internal format. The user selects the GEFF
        store directly (the path written by :func:`write_to_geff`).
        """
        return self._load_from_dialog(import_from_geff)

    def load_motile_run(self) -> tuple[Tracks, str, Path] | None:
        """Load a MotileRun from disk. The user selects the directory created
        by MotileRun.save(), and the geff store inside it is reported.
        """
        return self._load_from_dialog(MotileRun.load, geff_path=MotileRun.geff_path)
