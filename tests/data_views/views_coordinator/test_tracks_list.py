"""Tests for TracksList and TracksButton.

Covers add/remove/select tracks, save/load/export dialogs, signal emission,
and the load_motile_run bug fix (must call MotileRun.load, not Tracks.load).
"""

import warnings
from unittest.mock import MagicMock, patch

import pytest
from funtracks.data_model import SolutionTracks
from funtracks.import_export import write_to_geff
from qtpy.QtWidgets import QDialog

from motile_tracker.data_views.views_coordinator.tracks_list import (
    TracksButton,
    TracksList,
)
from motile_tracker.motile.backend.motile_run import MotileRun, SolverParams


@pytest.fixture(autouse=True)
def clear_viewer_layers(viewer):
    yield
    viewer.layers.clear()


@pytest.fixture
def motile_run(graph_2d):
    return MotileRun(graph=graph_2d, run_name="test", solver_params=SolverParams())


@pytest.fixture
def tracks_list():
    return TracksList()


# ---------------------------------------------------------------------------
# TracksButton
# ---------------------------------------------------------------------------


class TestTracksButton:
    def test_init_stores_tracks_and_name(self, motile_run):
        btn = TracksButton(motile_run, "my_run")
        assert btn.tracks is motile_run
        assert btn.name.text() == "my_run"

    def test_size_hint_height(self, motile_run):
        btn = TracksButton(motile_run, "my_run")
        assert btn.sizeHint().height() == 30


# ---------------------------------------------------------------------------
# TracksList — add / remove / select
# ---------------------------------------------------------------------------


class TestTracksListAddRemove:
    def test_add_tracks_appends_item(self, tracks_list, motile_run):
        tracks_list.add_tracks(motile_run, "run1", select=False)
        assert tracks_list.tracks_list.count() == 1

    def test_add_tracks_with_select(self, tracks_list, motile_run):
        tracks_list.add_tracks(motile_run, "run1", select=True)
        assert tracks_list.tracks_list.currentRow() == 0

    def test_add_multiple_tracks(self, tracks_list, motile_run):
        tracks_list.add_tracks(motile_run, "run1", select=False)
        tracks_list.add_tracks(motile_run, "run2", select=False)
        assert tracks_list.tracks_list.count() == 2

    def test_remove_tracks(self, tracks_list, motile_run):
        tracks_list.add_tracks(motile_run, "run1", select=False)
        item = tracks_list.tracks_list.item(0)
        tracks_list.remove_tracks(item)
        assert tracks_list.tracks_list.count() == 0

    def test_selection_changed_emits_signal(self, tracks_list, motile_run):
        emitted = []
        tracks_list.view_tracks.connect(lambda t, n: emitted.append((t, n)))
        tracks_list.add_tracks(motile_run, "run1", select=True)
        # Selecting the row triggers _selection_changed
        assert len(emitted) == 1
        assert emitted[0][1] == "run1"

    def test_add_solution_tracks_not_wrapped(self, tracks_list, solution_tracks_2d):
        """SolutionTracks added to the list should NOT be wrapped in MotileRun."""
        tracks_list.add_tracks(solution_tracks_2d, "imported", select=False)
        item = tracks_list.tracks_list.item(0)
        widget = tracks_list.tracks_list.itemWidget(item)
        assert isinstance(widget.tracks, SolutionTracks)
        assert not isinstance(widget.tracks, MotileRun)


# ---------------------------------------------------------------------------
# TracksList — save
# ---------------------------------------------------------------------------


class TestTracksListSave:
    def test_save_motile_run_creates_subdirectory(
        self, tracks_list, motile_run, tmp_path
    ):
        """MotileRun.save() creates a timestamped subdirectory."""
        tracks_list.add_tracks(motile_run, "run1", select=False)
        item = tracks_list.tracks_list.item(0)

        tracks_list.save_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.save_dialog.selectedFiles = MagicMock(return_value=[str(tmp_path)])

        tracks_list.save_tracks(item)

        saved_dirs = [p for p in tmp_path.iterdir() if p.is_dir()]
        assert len(saved_dirs) == 1

    def test_save_tracks_does_nothing_when_dialog_rejected(
        self, tracks_list, motile_run, tmp_path
    ):
        tracks_list.add_tracks(motile_run, "run1", select=False)
        item = tracks_list.tracks_list.item(0)

        tracks_list.save_dialog.exec_ = MagicMock(return_value=False)

        tracks_list.save_tracks(item)

        assert list(tmp_path.iterdir()) == []

    def test_save_emits_tracks_saved_signal(self, tracks_list, motile_run, tmp_path):
        tracks_list.add_tracks(motile_run, "run1", select=False)
        item = tracks_list.tracks_list.item(0)

        tracks_list.save_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.save_dialog.selectedFiles = MagicMock(return_value=[str(tmp_path)])

        emitted = []
        tracks_list.tracks_saved.connect(lambda t, p: emitted.append((t, p)))

        tracks_list.save_tracks(item)

        assert len(emitted) == 1
        assert emitted[0][0] is motile_run

    def test_save_does_not_emit_when_dialog_rejected(
        self, tracks_list, motile_run, tmp_path
    ):
        tracks_list.add_tracks(motile_run, "run1", select=False)
        item = tracks_list.tracks_list.item(0)

        tracks_list.save_dialog.exec_ = MagicMock(return_value=False)

        emitted = []
        tracks_list.tracks_saved.connect(lambda t, p: emitted.append((t, p)))

        tracks_list.save_tracks(item)

        assert len(emitted) == 0


# ---------------------------------------------------------------------------
# TracksList — save SolutionTracks directly (not wrapped in MotileRun)
# ---------------------------------------------------------------------------


class TestTracksListSaveSolutionTracks:
    def test_solution_tracks_saved_directly_to_path(
        self, tracks_list, solution_tracks_2d, tmp_path
    ):
        """SolutionTracks should be saved directly via write_to_geff,
        not wrapped in MotileRun. The geff store is written directly at
        the user-chosen path (no timestamped subdirectory).
        """
        tracks_list.add_tracks(solution_tracks_2d, "imported", select=False)
        item = tracks_list.tracks_list.item(0)

        save_path = tmp_path / "my_tracks.geff"

        tracks_list.save_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.save_dialog.selectedFiles = MagicMock(return_value=[str(save_path)])

        tracks_list.save_tracks(item)

        # write_to_geff writes the geff store directly at the given path
        assert save_path.exists()

    def test_solution_tracks_save_emits_signal(
        self, tracks_list, solution_tracks_2d, tmp_path
    ):
        tracks_list.add_tracks(solution_tracks_2d, "imported", select=False)
        item = tracks_list.tracks_list.item(0)

        save_path = tmp_path / "my_tracks.geff"

        tracks_list.save_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.save_dialog.selectedFiles = MagicMock(return_value=[str(save_path)])

        emitted = []
        tracks_list.tracks_saved.connect(lambda t, p: emitted.append((t, p)))

        tracks_list.save_tracks(item)

        assert len(emitted) == 1
        assert emitted[0][0] is solution_tracks_2d
        assert emitted[0][1] == save_path

    def test_solution_tracks_save_overwrites(
        self, tracks_list, solution_tracks_2d, tmp_path
    ):
        """Saving the same SolutionTracks twice to the same path should
        overwrite rather than fail.
        """
        tracks_list.add_tracks(solution_tracks_2d, "imported", select=False)
        item = tracks_list.tracks_list.item(0)

        save_path = tmp_path / "my_tracks.geff"

        tracks_list.save_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.save_dialog.selectedFiles = MagicMock(return_value=[str(save_path)])

        # Save twice — should not raise
        tracks_list.save_tracks(item)
        tracks_list.save_tracks(item)

        assert save_path.exists()


# ---------------------------------------------------------------------------
# TracksList — load_motile_run (bug fix: must use MotileRun.load)
# ---------------------------------------------------------------------------


class TestTracksListLoadMotileRun:
    def test_load_motile_run_success(self, tracks_list, motile_run, tmp_path):
        save_dir = motile_run.save(tmp_path)

        tracks_list.file_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.file_dialog.selectedFiles = MagicMock(return_value=[str(save_dir)])

        tracks_list.load_motile_run()

        assert tracks_list.tracks_list.count() == 1

    def test_load_motile_run_bad_path_warns(self, tracks_list, tmp_path):
        bad_path = tmp_path / "nonexistent_run"
        tracks_list.file_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.file_dialog.selectedFiles = MagicMock(return_value=[str(bad_path)])

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
# TracksList — load_internal_tracks
# ---------------------------------------------------------------------------


class TestTracksListLoadGeff:
    def test_load_internal_tracks_success(
        self, tracks_list, solution_tracks_2d, tmp_path
    ):
        geff_path = tmp_path / "saved_tracks.geff"
        write_to_geff(solution_tracks_2d, geff_path)

        tracks_list.file_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.file_dialog.selectedFiles = MagicMock(return_value=[str(geff_path)])

        tracks_list.load_internal_tracks()

        assert tracks_list.tracks_list.count() == 1
        item = tracks_list.tracks_list.item(0)
        widget = tracks_list.tracks_list.itemWidget(item)
        assert widget.name.text() == "saved_tracks"

    def test_load_internal_tracks_emits_signal(
        self, tracks_list, solution_tracks_2d, tmp_path
    ):
        geff_path = tmp_path / "saved_tracks.geff"
        write_to_geff(solution_tracks_2d, geff_path)

        tracks_list.file_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.file_dialog.selectedFiles = MagicMock(return_value=[str(geff_path)])

        emitted = []
        tracks_list.tracks_loaded.connect(lambda t, p: emitted.append((t, p)))

        tracks_list.load_internal_tracks()

        assert len(emitted) == 1
        assert isinstance(emitted[0][0], SolutionTracks)
        assert emitted[0][1] == geff_path

    def test_load_internal_tracks_bad_path_warns(self, tracks_list, tmp_path):
        bad_path = tmp_path / "nonexistent.geff"
        tracks_list.file_dialog.exec_ = MagicMock(return_value=True)
        tracks_list.file_dialog.selectedFiles = MagicMock(return_value=[str(bad_path)])

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            tracks_list.load_internal_tracks()

        assert len(caught) == 1
        assert tracks_list.tracks_list.count() == 0

    def test_load_internal_tracks_dialog_cancelled(self, tracks_list):
        tracks_list.file_dialog.exec_ = MagicMock(return_value=False)
        tracks_list.load_internal_tracks()
        assert tracks_list.tracks_list.count() == 0


# ---------------------------------------------------------------------------
# TracksList — load_tracks dispatch
# ---------------------------------------------------------------------------


class TestTracksListLoadDispatch:
    def test_load_tracks_dispatches_geff_tracks(self, tracks_list):
        tracks_list.dropdown_menu.setCurrentText("Tracks (geff)")
        with patch.object(tracks_list, "load_internal_tracks") as mock:
            tracks_list.load_tracks()
            mock.assert_called_once()

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
    def test_load_tracks_accepted_adds_tracks(self, tracks_list, motile_run, tmp_path):
        mock_dialog = MagicMock()
        mock_dialog.exec_.return_value = QDialog.Accepted
        mock_dialog.tracks = motile_run
        mock_dialog.name = "imported"
        mock_dialog.source_path = tmp_path / "test.csv"

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
    def test_show_export_dialog_called(self, tracks_list, motile_run):
        tracks_list.add_tracks(motile_run, "run1", select=False)
        item = tracks_list.tracks_list.item(0)

        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_list.ExportDialog.show_export_dialog"
        ) as mock_export:
            tracks_list.show_export_dialog(item)
            mock_export.assert_called_once()

    def test_show_export_dialog_emits_request_colormap(self, tracks_list, motile_run):
        tracks_list.add_tracks(motile_run, "run1", select=False)
        item = tracks_list.tracks_list.item(0)

        emitted = []
        tracks_list.request_colormap.connect(lambda: emitted.append(True))

        with patch(
            "motile_tracker.data_views.views_coordinator.tracks_list.ExportDialog.show_export_dialog"
        ):
            tracks_list.show_export_dialog(item)

        assert len(emitted) == 1
