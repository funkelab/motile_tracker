import numpy as np
import pytest

from motile_tracker.data_views.colormap import TrackColormap, TrackIdColorSource


class ConstantColorSource:
    """A trivial ColorSource for testing: every value maps to the same color."""

    def __init__(self, color=(1.0, 0.0, 0.0, 1.0)):
        self.color = np.asarray(color, dtype=float)

    def map(self, values: np.ndarray) -> np.ndarray:
        return np.tile(self.color, (len(np.atleast_1d(values)), 1))


class TestTrackIdColorSource:
    def test_maps_same_track_id_to_same_color(self):
        source = TrackIdColorSource()
        colors = source.map(np.asarray([1, 2, 1]))
        assert np.array_equal(colors[0], colors[2])
        assert not np.array_equal(colors[0], colors[1])

    def test_background_track_id_zero_is_transparent(self):
        source = TrackIdColorSource()
        color = source.map(np.asarray([0]))[0]
        assert color[3] == 0

    def test_shuffle_changes_colors(self):
        source = TrackIdColorSource(num_colors=49, seed=0.5)
        before = source.map(np.asarray([1, 2, 3])).copy()
        source.shuffle(num_colors=60, seed=0.9)
        after = source.map(np.asarray([1, 2, 3]))
        assert not np.array_equal(before, after)


class TestTrackColormapSetNodes:
    def test_populates_a_color_per_node(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        nodes = solution_tracks_2d.graph.node_ids()
        assert set(cmap.nodes) == set(nodes)
        for node in nodes:
            assert cmap.get_color(node) is not None

    def test_nodes_sharing_a_track_id_share_a_color(self, solution_tracks_2d):
        # nodes 3, 4, 5 in solution_tracks_2d all belong to track_id 3
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        color_3 = cmap.get_color(3)
        color_4 = cmap.get_color(4)
        color_5 = cmap.get_color(5)
        assert np.array_equal(color_3, color_4)
        assert np.array_equal(color_4, color_5)

    def test_different_track_ids_get_different_colors(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        color_1 = cmap.get_color(1)  # track_id 1
        color_3 = cmap.get_color(3)  # track_id 3
        assert not np.array_equal(color_1, color_3)

    def test_new_nodes_default_to_fully_opaque(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        for node in solution_tracks_2d.graph.node_ids():
            assert cmap.get_alpha(node) == 1.0

    def test_preserves_alpha_for_nodes_still_present(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)
        cmap.set_alpha([1, 2], 0.3)

        # re-run set_nodes with the same tracks (simulating a refresh where the
        # node set didn't actually change)
        cmap.set_nodes(solution_tracks_2d)

        assert cmap.get_alpha(1) == 0.3
        assert cmap.get_alpha(2) == 0.3
        assert cmap.get_alpha(3) == 1.0

    def test_drops_alpha_overrides_for_removed_nodes(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)
        cmap.set_alpha([1], 0.3)

        class NodeSubsetGraph:
            def node_ids(self):
                return [2, 3]

        class TracksSubset:
            graph = NodeSubsetGraph()

            def get_track_ids(self, nodes):
                return solution_tracks_2d.get_track_ids(nodes)

        cmap.set_nodes(TracksSubset())

        assert set(cmap.nodes) == {2, 3}
        assert cmap.get_alpha(1, default=None) is None


class TestTrackColormapColorAlphaSeparation:
    def test_set_alpha_does_not_change_color(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)
        rgb_before = cmap.get_color(1)[:3].copy()

        cmap.set_alpha([1], 0.2)

        assert np.array_equal(cmap.get_color(1)[:3], rgb_before)
        assert cmap.get_color(1)[3] == 0.2

    def test_set_alpha_ignores_unknown_nodes(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        # should not raise, and should not add the unknown node
        cmap.set_alpha([999], 0.5)
        assert 999 not in cmap.nodes

    def test_set_color_preserves_existing_alpha(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)
        cmap.set_alpha([1], 0.4)

        cmap.set_color(1, np.array([0.1, 0.2, 0.3, 1.0]))

        assert cmap.get_alpha(1) == 0.4
        assert np.array_equal(cmap.get_color(1)[:3], [0.1, 0.2, 0.3])

    def test_set_color_on_new_node_defaults_to_opaque(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        cmap.set_color(999, np.array([0.1, 0.2, 0.3, 1.0]))

        assert cmap.get_alpha(999) == 1.0

    def test_remove_node_drops_both_color_and_alpha(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        cmap.remove_node(1)

        assert 1 not in cmap.nodes
        assert cmap.get_color(1) is None
        assert cmap.get_alpha(1, default=None) is None


class TestTrackColormapMap:
    def test_map_delegates_to_color_source(self):
        source = ConstantColorSource(color=(0.5, 0.5, 0.5, 1.0))
        cmap = TrackColormap(color_source=source)

        result = cmap.map(np.asarray([1, 2, 3]))

        assert result.shape == (3, 4)
        assert np.all(result == [0.5, 0.5, 0.5, 1.0])

    def test_default_color_source_is_track_id_based(self, solution_tracks_2d):
        cmap = TrackColormap()
        colors = cmap.map(np.asarray([1, 3]))
        assert not np.array_equal(colors[0], colors[1])


class TestTrackColormapDirectColormap:
    def test_produces_direct_colormap_with_all_nodes(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        direct = cmap.to_direct_colormap()

        for node in solution_tracks_2d.graph.node_ids():
            assert node in direct.color_dict

    def test_none_key_maps_to_transparent(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        direct = cmap.to_direct_colormap()

        assert np.array_equal(direct.color_dict[None], [0, 0, 0, 0])

    def test_alpha_only_change_reuses_same_object(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        direct_before = cmap.to_direct_colormap()
        cmap.set_alpha([1], 0.2)
        direct_after = cmap.to_direct_colormap()

        assert direct_before is direct_after
        assert direct_after.color_dict[1][3] == 0.2

    def test_color_change_invalidates_cached_colormap(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        direct_before = cmap.to_direct_colormap()
        cmap.set_color(1, np.array([0.9, 0.9, 0.9, 1.0]))
        direct_after = cmap.to_direct_colormap()

        assert direct_before is not direct_after
        assert np.allclose(direct_after.color_dict[1][:3], [0.9, 0.9, 0.9])

    def test_new_node_invalidates_cached_colormap(self, solution_tracks_2d):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)

        direct_before = cmap.to_direct_colormap()
        cmap.set_color(999, np.array([0.1, 0.2, 0.3, 1.0]))
        direct_after = cmap.to_direct_colormap()

        assert direct_before is not direct_after
        assert 999 in direct_after.color_dict

    def test_reflects_alpha_set_before_first_build(self, solution_tracks_2d):
        # alpha set before to_direct_colormap() has ever been called should
        # still show up in the first built colormap
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d)
        cmap.set_alpha([1], 0.0)

        direct = cmap.to_direct_colormap()

        assert direct.color_dict[1][3] == 0.0

    def test_empty_colormap_only_has_default_keys(self):
        # napari's DirectLabelColormap always adds a `0` (background) entry
        # alongside whatever default we provide via the `None` key.
        cmap = TrackColormap()
        direct = cmap.to_direct_colormap()
        assert set(direct.color_dict.keys()) == {None, 0}
        assert np.array_equal(direct.color_dict[None], [0, 0, 0, 0])


@pytest.fixture
def solution_tracks_2d_empty():
    """A Tracks-like object with no nodes, to exercise the empty-graph path."""
    from funtracks.data_model import SolutionTracks
    from funtracks.utils.tracksdata_utils import create_empty_graphview_graph

    empty_graph = create_empty_graphview_graph(
        node_attributes=["pos", "area", "track_id", "lineage_id"],
        edge_attributes=["iou"],
        ndim=3,
    )
    return SolutionTracks(graph=empty_graph, ndim=3, time_attr="t")


class TestTrackColormapEmptyTracks:
    def test_set_nodes_with_no_nodes(self, solution_tracks_2d_empty):
        cmap = TrackColormap()
        cmap.set_nodes(solution_tracks_2d_empty)

        assert list(cmap.nodes) == []
        direct = cmap.to_direct_colormap()
        assert set(direct.color_dict.keys()) == {None, 0}
