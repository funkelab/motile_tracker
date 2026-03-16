"""Tests for TracksList, TracksButton, and TrackListWidget.

Covers add/remove/select tracks, save/load/export dialogs, and the
load_motile_run bug fix (must call MotileRun.load, not Tracks.load).
"""

import warnings
from unittest.mock import MagicMock, patch

import napari
import pytest
from funtracks.data_model import SolutionTracks
from qtpy.QtWidgets import QDialog

from motile_tracker.data_views.views_coordinator.tracks_list import (
    TrackListWidget,
    TracksList,
    TracksButton,
)
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_tracker.motile.backend.motile_run import MotileRun, SolverParams


@pytest.fixture(autouse=True)
def clear_viewer_layers(viewer):
    yield
    viewer.layers.clear()


@pytest.fixture
def tracks(graph_2d):
    return MotileRun(graph=graph_2d, run_name="test", solver_params=SolverParams())


@pytest.fixture
def tracks_list():
    return TracksList()


# ---------------------------------------------------------------------------
# TracksButton
# ---------------------------------------------------------------------------


class TestTracksButton:
    def test_init_stores_tracks_and_name(self, tracks):
        btn = TracksButton(tracks, "my_run")
        assert btn.tracks is tracks
        assert btn.name.text() == "my_run"

    def test_size_hint_height(self, tracks):
        btn = TracksButton(tracks, "my_run")
        assert btn.sizeHint().height() == 30


# ---------------------------------------------------------------------------
# TracksList — add / remove / select
# ---------------------------------------------------------------------------


class TestTracksListAddRemove:
    def test_add_tracks_appends_item(self, tracks_list, tracks):
        tracks_list.add_tracks(tracks, "run1", select=False)
        assert tracks_list.tracks_list.count() == 1

    def test_add_tracks_with_select(self, tracks_list, tracks):
        tracks_list.add_tracks(tracks, "run1", select=True)
        assert tracks_list.tracks_list.currentRow() == 0

    def test_add_multiple_tracks(self, tracks_list, tracks):
        tracks_list.add_tracks(tracks, "run1", select=False)
        tracks_list.add_tracks(tracks, "run2", select=False)
        assert tracks_list.tracks_list.count() == 2

    def test_remove_tracks(self, tracks_list, tracks):
        tracks_list.add_tracks(tracks, "run1", select=False)
        item = tracks_list.tracks_list.item(0)
        tracks_list.remove_tracks(item)
        assert tracks_list.tracks_list.count() == 0

    def test_selection_changed_emits_signal(self, tracks_list, tracks):
        emitted = []
        tracks_list.view_tracks.connect(lambda t, n: emitted.append((t, n)))
        tracks_list.add_tracks(tracks, "run1", select=True)
        # Selecting the row triggers _selection_changed
        assert len(emitted) == 1
        assert emitted[0][1] == "run1"


# ---------------------------------------------------------------------------
# TracksList — save
# ---------------------------------------------------------------------------


class TestTracksListSave:
    def test_save_tracks_calls_save_when_dialog_accepted(
        self, tracks_list, tracks, tmp_path
    ):
        tracks_list.add_tracks(tracks, "run1", select=False)
        item = tracks_list.tracks_list.item(0)

        tracks_list.save_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.save_dialog.selectedFiles = MagicMock(return_value=[str(tmp_path)])

        with patch.object(tracks, "save") as mock_save:
            tracks_list.save_tracks(item)
            mock_save.assert_called_once_with(tmp_path)

    def test_save_tracks_does_nothing_when_dialog_rejected(
        self, tracks_list, tracks
    ):
        tracks_list.add_tracks(tracks, "run1", select=False)
        item = tracks_list.tracks_list.item(0)

        tracks_list.save_dialog.exec_ = MagicMock(return_value=False)

        with patch.object(tracks, "save") as mock_save:
            tracks_list.save_tracks(item)
            mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# TracksList — load_motile_run (bug fix: must use MotileRun.load)
# ---------------------------------------------------------------------------


class TestTracksListLoadMotileRun:
    def test_load_motile_run_success(self, tracks_list, tracks, tmp_path):
        save_dir = tracks.save(tmp_path)

        tracks_list.file_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.file_dialog.selectedFiles = MagicMock(
            return_value=[str(save_dir)]
        )

        tracks_list.load_motile_run()

        assert tracks_list.tracks_list.count() == 1

    def test_load_motile_run_bad_path_warns(self, tracks_list, tmp_path):
        bad_path = tmp_path / "nonexistent_run"
        tracks_list.file_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.file_dialog.selectedFiles = MagicMock(
            return_value=[str(bad_path)]
        )

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            tracks_list.load_motile_run()

        assert len(caught) == 1
        assert tracks_list.tracks_list.count() == 0

    def test_load_motile_run_dialog_cancelled(self, tracks_list):
        tracks_list.file_dialog.exec_ = MagicMock(return_value=False)
        tracks_list.load_motile_run()
        assert tracks_list.tracks_list.count() == 0


# ---------------------------------------------------------------------------
# TracksList — load_tracks dispatch
# ---------------------------------------------------------------------------


class TestTracksListLoadDispatch:
    def test_load_tracks_dispatches_motile_run(self, tracks_list):
        tracks_list.dropdown_menu.setCurrentText("Motile Run")
        with patch.object(tracks_list, "load_motile_run") as mock:
            tracks_list.load_tracks()
            mock.assert_called_once()

    def test_load_tracks_dispatches_csv(self, tracks_list):
        tracks_list.dropdown_menu.setCurrentText("External tracks from CSV")
        with patch.object(tracks_list, "_load_tracks") as mock:
            tracks_list.load_tracks()
            mock.assert_called_once_with(import_type="csv")

    def test_load_tracks_dispatches_geff(self, tracks_list):
        tracks_list.dropdown_menu.setCurrentText("External tracks from geff")
        with patch.object(tracks_list, "_load_tracks") as mock:
            tracks_list.load_tracks()
            mock.assert_called_once_with("geff")


# ---------------------------------------------------------------------------
# TracksList — _load_tracks (CSV / GEFF via ImportDialog)
# ---------------------------------------------------------------------------


class TestTracksListLoadExternal:
    def test_load_tracks_accepted_adds_tracks(self, tracks_list, tracks):
        mock_dialog = MagicMock()
        mock_dialog.exec_.return_value = QDialog.Accepted
        mock_dialog.tracks = tracks
        mock_dialog.name = "imported"

        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_list.ImportDialog",
            return_value=mock_dialog,
        ):
            tracks_list._load_tracks("csv")

        assert tracks_list.tracks_list.count() == 1

    def test_load_tracks_rejected_adds_nothing(self, tracks_list):
        mock_dialog = MagicMock()
        mock_dialog.exec_.return_value = QDialog.Rejected

        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_list.ImportDialog",
            return_value=mock_dialog,
        ):
            tracks_list._load_tracks("csv")

        assert tracks_list.tracks_list.count() == 0

    def test_load_tracks_accepted_but_none_tracks(self, tracks_list):
        mock_dialog = MagicMock()
        mock_dialog.exec_.return_value = QDialog.Accepted
        mock_dialog.tracks = None

        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_list.ImportDialog",
            return_value=mock_dialog,
        ):
            tracks_list._load_tracks("csv")

        assert tracks_list.tracks_list.count() == 0


# ---------------------------------------------------------------------------
# TracksList — show_export_dialog
# ---------------------------------------------------------------------------


class TestTracksListExport:
    def test_show_export_dialog_called(self, tracks_list, tracks):
        tracks_list.add_tracks(tracks, "run1", select=False)
        item = tracks_list.tracks_list.item(0)

        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_list.ExportDialog.show_export_dialog"
        ) as mock_export:
            tracks_list.show_export_dialog(item)
            mock_export.assert_called_once()

    def test_show_export_dialog_emits_request_colormap(self, tracks_list, tracks):
        tracks_list.add_tracks(tracks, "run1", select=False)
        item = tracks_list.tracks_list.item(0)

        emitted = []
        tracks_list.request_colormap.connect(lambda: emitted.append(True))

        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_list.ExportDialog.show_export_dialog"
        ):
            tracks_list.show_export_dialog(item)

        assert len(emitted) == 1


# ---------------------------------------------------------------------------
# TrackListWidget
# ---------------------------------------------------------------------------


class TestTrackListWidget:
    def test_init_contains_tracks_list(self, viewer):
        widget = TrackListWidget(viewer)
        tracks_viewer = TracksViewer.get_instance(viewer)
        assert widget.layout().itemAt(0).widget() is tracks_viewer.tracks_list
