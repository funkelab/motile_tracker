from functools import partial
from pathlib import Path
from warnings import warn

import napari
from fonticon_fa6 import FA6S
from napari._qt.qt_resources import QColoredSVGIcon
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
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

from motile_tracker.data_model import SolutionTracks, Tracks
from motile_tracker.import_export.menus.import_external_tracks_dialog import (
    ImportTracksDialog,
)
from motile_tracker.motile.backend.motile_run import MotileRun


class TrackListWidget(QWidget):
    """Creates or finds a TracksViewer and displays its TrackList widget.
    This is only used in case the user wants to open the trackslist from the plugins
    menu.
    """

    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        from motile_tracker.data_views.views_coordinator.tracks_viewer import (
            TracksViewer,
        )

        tracks_viewer = TracksViewer.get_instance(viewer)
        layout = QVBoxLayout()
        layout.addWidget(tracks_viewer.tracks_list)

        self.setLayout(layout)


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
        self.export.setToolTip("Export tracks to CSV")
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

    def __init__(self):
        super().__init__(title="Results List")
        self.file_dialog = QFileDialog()
        self.file_dialog.setFileMode(QFileDialog.Directory)
        self.file_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        self.save_dialog = QFileDialog()
        self.save_dialog.setFileMode(QFileDialog.Directory)
        self.save_dialog.setOption(QFileDialog.ShowDirsOnly, True)

        self.export_dialog = QFileDialog()
        self.export_dialog.setFileMode(QFileDialog.AnyFile)
        self.export_dialog.setAcceptMode(QFileDialog.AcceptSave)
        self.export_dialog.setNameFilter("CSV files (*.csv)")
        self.export_dialog.setDefaultSuffix("csv")

        self.tracks_list = QListWidget()
        self.tracks_list.setSelectionMode(1)  # single selection
        self.tracks_list.itemSelectionChanged.connect(self._selection_changed)

        load_menu = QHBoxLayout()
        self.dropdown_menu = QComboBox()
        self.dropdown_menu.addItems(["Motile Run", "External tracks from CSV"])

        load_button = QPushButton("Load")
        load_button.clicked.connect(self.load_tracks)

        load_menu.addWidget(self.dropdown_menu)
        load_menu.addWidget(load_button)

        layout = QVBoxLayout()
        layout.addWidget(self.tracks_list)
        layout.addLayout(load_menu)
        self.setLayout(layout)

    def _load_external_tracks(self):
        dialog = ImportTracksDialog()
        if dialog.exec_() == QDialog.Accepted:
            tracks = dialog.tracks
            name = dialog.name
            if tracks is not None:
                self.add_tracks(tracks, name, select=True)

    def _selection_changed(self):
        selected = self.tracks_list.selectedItems()
        if selected:
            tracks_button = self.tracks_list.itemWidget(selected[0])
            self.view_tracks.emit(tracks_button.tracks, tracks_button.name.text())

    def add_tracks(self, tracks: Tracks, name: str, select=True):
        """Add a run to the list and optionally select it. Will make a new
        row in the list UI representing the given run.

        Note: selecting the run will also emit the selection changed event on
        the list.

        Args:
            tracks (Tracks): the tracks object to add to the results list
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
        tracks_row.export.clicked.connect(partial(self.export_to_csv, item))
        tracks_row.save.clicked.connect(partial(self.save_tracks, item))
        if select:
            self.tracks_list.setCurrentRow(len(self.tracks_list) - 1)

    def export_to_csv(self, item: QListWidgetItem):
        """Export a tracks object from the list to a CSV file.

        You must pass the list item that represents the tracks, not the tracks object
        itself.

        Args:
            item (QListWidgetItem):  The list item containing the TracksButton that
                represents a set of tracks.
        """
        widget: TracksButton = self.tracks_list.itemWidget(item)
        tracks: Tracks = widget.tracks
        default_name: str = widget.name.text()
        default_name = f"{default_name}_tracks.csv"
        # use the same directory as the last time you opened the dialog
        base_path = Path(self.export_dialog.directory().path())
        self.export_dialog.selectFile(str(base_path / default_name))
        if self.export_dialog.exec_():
            file_path = Path(self.export_dialog.selectedFiles()[0])
            tracks.export_tracks(file_path)

    def save_tracks(self, item: QListWidgetItem):
        """Saves a tracks object from the list. You must pass the list item that
        represents the tracks, not the tracks object itself.

        Args:
            item (QListWidgetItem): The list item to save. This list item
                contains the TracksButton that represents a set of tracks.
        """
        tracks: Tracks = self.tracks_list.itemWidget(item).tracks
        if self.save_dialog.exec_():
            directory = Path(self.save_dialog.selectedFiles()[0])
            tracks.save(directory)

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
        """Call the function to load tracks from disk for a Motile Run or for externally
        generated tracks (CSV file),  depending on the choice in the dropdown menu.
        """

        if self.dropdown_menu.currentText() == "Motile Run":
            self.load_motile_run()
        elif self.dropdown_menu.currentText() == "External tracks from CSV":
            self._load_external_tracks()

    def load_motile_run(self):
        """Load a set of tracks from disk. The user selects the directory created
        by calling save_tracks.
        """

        if self.file_dialog.exec_():
            directory = Path(self.file_dialog.selectedFiles()[0])
            name = directory.stem
            try:
                tracks = MotileRun.load(directory)
                self.add_tracks(tracks, name, select=True)
            except (ValueError, FileNotFoundError):
                try:
                    tracks = SolutionTracks.load(directory)
                    self.add_tracks(tracks, name, select=True)
                except (ValueError, FileNotFoundError) as e:
                    warn(f"Could not load tracks from {directory}: {e}", stacklevel=2)
