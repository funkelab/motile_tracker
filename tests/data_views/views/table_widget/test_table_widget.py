import pandas as pd
import pytest
from funtracks.data_model import SolutionTracks
from qtpy.QtWidgets import QApplication

from motile_tracker.data_views.views.tree_view.custom_table_widget import (
    ColoredTableWidget,
)
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


@pytest.fixture
def setup_tracks_viewer(make_napari_viewer, graph_2d):
    """Create a TracksViewer with tracks loaded."""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_2d, ndim=3)

    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    return viewer, tracks_viewer


@pytest.fixture
def colored_table_widget(qtbot, setup_tracks_viewer):
    _, tracks_viewer = setup_tracks_viewer

    # Build dataframe from tracks
    nodes = list(tracks_viewer.tracks.graph.nodes())

    df = pd.DataFrame(
        {
            "ID": nodes,
            "value": list(range(len(nodes))),
        }
    )

    widget = ColoredTableWidget(tracks_viewer, df)
    qtbot.addWidget(widget)

    return widget, tracks_viewer


def test_table_population(colored_table_widget):
    widget, _ = colored_table_widget

    table = widget._table_widget

    assert table.rowCount() > 0
    assert table.columnCount() >= 1


def test_table_selection_updates_tracksviewer(colored_table_widget, qtbot):
    widget, tracks_viewer = colored_table_widget
    table = widget._table_widget

    first_row_node = widget._table["ID"][0]

    with qtbot.waitSignal(tracks_viewer.selected_nodes.list_updated, timeout=1000):
        table.selectRow(0)

    assert first_row_node in tracks_viewer.selected_nodes.as_list


def test_tracksviewer_selection_updates_table(colored_table_widget, qtbot):
    widget, tracks_viewer = colored_table_widget
    table = widget._table_widget

    # Select first two nodes in viewer
    nodes = widget._table["ID"][:2].tolist()
    tracks_viewer.selected_nodes.add_list(nodes, append=False)

    qtbot.wait(50)

    selected_rows = sorted({index.row() for index in table.selectedIndexes()})

    assert selected_rows == [0, 1]


def test_no_infinite_selection_loop(colored_table_widget, qtbot):
    widget, tracks_viewer = colored_table_widget
    table = widget._table_widget

    spy_count = {"calls": 0}

    def spy():
        spy_count["calls"] += 1

    tracks_viewer.selected_nodes.list_updated.connect(spy)

    table.selectRow(0)
    qtbot.wait(50)

    assert spy_count["calls"] == 1


def test_center_from_table_triggers_viewer(colored_table_widget, qtbot):
    widget, tracks_viewer = colored_table_widget
    table = widget._table_widget

    index = table.model().index(0, 0)

    with qtbot.waitSignal(tracks_viewer.center_node, timeout=1000):
        widget.center_node(index)


def test_center_from_tracksviewer_scrolls_table(colored_table_widget, qtbot):
    widget, _ = colored_table_widget
    table = widget._table_widget

    # Force small viewport so only 2 rows fit
    row_height = 30
    table.setFixedHeight(row_height * 2)
    for i in range(table.rowCount()):
        table.setRowHeight(i, row_height)

    widget.show()
    qtbot.wait(50)
    qtbot.waitExposed(widget)  # Ensure widget is rendered
    qtbot.wait(50)

    table.verticalScrollBar().setValue(0)
    qtbot.wait(50)

    node = widget._table["ID"][5]
    target_row_index = widget._find_row(ID=node)

    # Scroll to node and check that it is visible
    widget.scroll_to_node(node)
    qtbot.wait(50)

    QApplication.processEvents()
    row_rect = table.visualRect(table.model().index(target_row_index, 0))
    viewport_rect = table.viewport().rect()

    assert row_rect.intersects(viewport_rect), (
        "The target row should be visible after scroll"
    )

    assert widget._syncing is False


def test_sort_preserves_functionality(colored_table_widget, qtbot):
    widget, tracks_viewer = colored_table_widget

    widget._sort_table(0)
    qtbot.wait(50)

    # Try selecting again after sort
    widget._table_widget.selectRow(0)
    qtbot.wait(50)

    assert len(tracks_viewer.selected_nodes.as_list) >= 1
