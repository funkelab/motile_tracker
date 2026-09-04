"""Tests for following a reference track when stepping through time."""

import pytest

from motile_tracker.application_menus.visualization_widget import VisualizationWidget
from motile_tracker.data_views.views.ortho_views import initialize_ortho_views
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


@pytest.fixture
def viewer(make_napari_viewer):
    """Per-test viewer, because these tests inspect viewer.dims.point."""
    return make_napari_viewer()


@pytest.fixture
def tracks_viewer(viewer, solution_tracks_3d_with_division):
    """TracksViewer showing 3D+time tracks.

    Track id 1 holds node 1 (t=0, pos [50, 50, 50]) and node 2 (t=1, pos
    [20, 50, 80]), so its displacement from t=0 to t=1 is [-30, 0, 30]. It does
    not exist at t=2, where the two daughter tracks start.
    """
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=solution_tracks_3d_with_division, name="test")
    return tracks_viewer


def _step_to(viewer, time: int) -> None:
    """Move the time slider the way the user would."""
    step = list(viewer.dims.current_step)
    step[0] = time
    viewer.dims.current_step = step


def test_no_reference_track_keeps_z(viewer, tracks_viewer):
    """Without a reference track, stepping in time leaves the other dims alone."""

    viewer.dims.point = (0, 50, 50, 50)
    _step_to(viewer, 1)

    assert viewer.dims.point[1] == 50


def test_reference_track_shifts_z(viewer, tracks_viewer):
    """Stepping to the next time point shifts the z slider by the track's shift."""

    tracks_viewer.set_reference_track(1)
    viewer.dims.point = (0, 50, 50, 50)
    _step_to(viewer, 1)

    assert viewer.dims.point[0] == 1
    assert viewer.dims.point[1] == 20  # 50 + (20 - 50)


def test_reference_track_shift_is_relative(viewer, tracks_viewer):
    """The shift is applied to the current view, not the track's absolute position."""

    tracks_viewer.set_reference_track(1)
    viewer.dims.point = (0, 70, 50, 50)
    _step_to(viewer, 1)

    assert viewer.dims.point[1] == 40  # 70 + (20 - 50)


def test_stepping_back_shifts_back(viewer, tracks_viewer):
    """Stepping backwards shifts in the opposite direction."""

    tracks_viewer.set_reference_track(1)
    viewer.dims.point = (0, 50, 50, 50)
    _step_to(viewer, 1)
    _step_to(viewer, 0)

    assert viewer.dims.point[1] == 50


def test_missing_at_new_time_is_ignored(viewer, tracks_viewer):
    """Track id 1 has no node at t=2, so stepping there leaves z untouched."""

    tracks_viewer.set_reference_track(1)
    viewer.dims.point = (1, 50, 50, 50)
    _step_to(viewer, 2)

    assert viewer.dims.point[1] == 50


def test_centering_on_a_node_is_not_shifted(viewer, tracks_viewer):
    """Moving to another time point by selecting a node must not shift the view.

    Node 3 sits at t=2, [60, 50, 45], so centering has to land exactly there.
    """

    tracks_viewer.set_reference_track(1)
    viewer.dims.point = (0, 50, 50, 50)
    tracks_viewer.tracking_layers.center_view(3)

    assert tuple(viewer.dims.point) == (2, 60, 50, 45)


def test_shift_after_centering_uses_the_new_time(viewer, tracks_viewer):
    """A centered jump updates the bookkeeping, so the next slider move is correct."""

    tracks_viewer.set_reference_track(1)
    tracks_viewer.tracking_layers.center_view(2)  # node 2, t=1, [20, 50, 80]
    _step_to(viewer, 0)

    assert viewer.dims.point[1] == 50  # 20 + (50 - 20)


def test_single_axis_slider_move_shifts_z(viewer, tracks_viewer):
    """The napari slider moves the time axis on its own; that is enough to trigger."""

    tracks_viewer.set_reference_track(1)
    viewer.dims.point = (0, 50, 50, 50)
    viewer.dims.set_current_step(0, 1)

    assert viewer.dims.point[1] == 20


def test_displayed_dims_also_shift(viewer, tracks_viewer):
    """The displayed dimensions of dims.point shift too, so the orthogonal views
    (which slice on x and y) follow the reference track as well."""

    tracks_viewer.set_reference_track(1)
    viewer.dims.point = (0, 50, 50, 50)
    _step_to(viewer, 1)

    # the track moves [-30, 0, 30] in z, y, x between t=0 and t=1
    assert tuple(viewer.dims.point) == (1, 20, 50, 80)


def test_each_step_shifts_on_its_own(viewer, tracks_viewer):
    """Stepping forward and straight back leaves the view where it started."""

    tracks_viewer.set_reference_track(1)
    viewer.dims.point = (0, 50, 50, 50)
    viewer.dims.set_current_step(0, 1)
    viewer.dims.set_current_step(0, 0)

    assert tuple(viewer.dims.point) == (0, 50, 50, 50)


def test_orthogonal_views_follow_the_reference_track(
    viewer, solution_tracks_3d_with_division, qtbot
):
    """Every view follows, including the one whose own time slider was moved.

    The orthogonal views block their sync while they drive it, so the view the user
    moved would otherwise be the only one left behind.
    """

    ortho_manager = initialize_ortho_views(viewer)
    ortho_manager.show()
    qtbot.waitUntil(ortho_manager.is_shown, timeout=1000)

    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=solution_tracks_3d_with_division, name="test")
    qtbot.wait(50)

    right_vm = ortho_manager.right_widget.vm_container.viewer_model
    bottom_vm = ortho_manager.bottom_widget.vm_container.viewer_model

    tracks_viewer.set_reference_track(1)
    viewer.dims.point = (0, 50, 50, 50)
    qtbot.wait(50)

    # move time on the right orthogonal view, the way the user would
    right_vm.dims.set_current_step(0, 1)
    qtbot.wait(50)

    # the track moves [-30, 0, 30] in z, y, x between t=0 and t=1
    expected = (1, 20, 50, 80)
    assert tuple(viewer.dims.point) == expected
    assert tuple(right_vm.dims.point) == expected
    assert tuple(bottom_vm.dims.point) == expected

    ortho_manager.cleanup()


def test_edits_to_the_reference_track_are_picked_up(viewer, tracks_viewer):
    """The two nodes are looked up fresh, so moving one changes the next shift."""

    tracks_viewer.set_reference_track(1)
    # node 2 is the t=1 node of track 1, at [20, 50, 80]
    tracks_viewer.tracks.set_position(2, [10, 50, 90])

    viewer.dims.point = (0, 50, 50, 50)
    _step_to(viewer, 1)

    assert tuple(viewer.dims.point) == (1, 10, 50, 90)  # 50 + (10 - 50), etc.


def test_clearing_the_reference_track(viewer, tracks_viewer):
    """Clearing the reference stops the view from following it."""

    tracks_viewer.set_reference_track(1)
    tracks_viewer.set_reference_track(None)
    viewer.dims.point = (0, 50, 50, 50)
    _step_to(viewer, 1)

    assert tracks_viewer.reference_track is None
    assert viewer.dims.point[1] == 50


def test_unknown_track_id_is_rejected(tracks_viewer):
    """A track id that is not in the tracks does not become the reference."""

    tracks_viewer.set_reference_track(999)

    assert tracks_viewer.reference_track is None


def test_reference_track_widget(viewer, tracks_viewer, qtbot):
    """The button toggles the active tracklet id and shows it in its color."""

    widget = VisualizationWidget(viewer)
    qtbot.addWidget(widget)
    button = widget.reference_track_widget.reference_btn

    tracks_viewer.selected_nodes.add(1)  # track id 1
    button.click()

    assert tracks_viewer.reference_track == 1
    assert button.text() == "Reference: 1"
    assert "border" in button.styleSheet()

    # clicking again with the same tracklet active clears the reference
    button.click()

    assert tracks_viewer.reference_track is None
    assert button.text() == "Reference: None"
    assert "rgba(0,0,0,0)" in button.styleSheet()


def test_reference_track_widget_switches_track(viewer, tracks_viewer, qtbot):
    """Clicking with a different tracklet active moves the reference to that one."""

    widget = VisualizationWidget(viewer)
    qtbot.addWidget(widget)
    button = widget.reference_track_widget.reference_btn

    tracks_viewer.selected_nodes.add(1)  # track id 1
    button.click()
    tracks_viewer.selected_nodes.add(3)  # a daughter, so a different track id
    button.click()

    assert tracks_viewer.reference_track == tracks_viewer.selected_track
    assert tracks_viewer.reference_track != 1
