from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import numpy as np
from napari.utils import DirectLabelColormap
from napari.utils.colormaps import label_colormap

if TYPE_CHECKING:
    from funtracks.data_model import Tracks


@runtime_checkable
class ColorSource(Protocol):
    """Maps an array of ids/values to an (N, 4) RGBA array.

    Duck-type compatible with `CyclicLabelColormap.map`, so it's a drop-in
    replacement anywhere a napari colormap's `.map()` is used for track-id
    coloring. Swap in a continuous-feature or constant-color source later
    without touching `TrackColormap` or its consumers.
    """

    def map(self, values: np.ndarray) -> np.ndarray: ...


class CategoricalColorSource:
    """Default `ColorSource`: cyclic color per unique id, 0 -> transparent.

    Not track-specific - works for any categorical id (cell type, lineage id).
    """

    def __init__(self, num_colors: int = 49, seed: float = 0.5):
        self._cyclic_colormap = label_colormap(
            num_colors, seed=seed, background_value=0
        )

    def map(self, values: np.ndarray) -> np.ndarray:
        return self._cyclic_colormap.map(values)

    def shuffle(self, num_colors: int, seed: float) -> None:
        """Replace the color cycle (see `TrackLabels.new_colormap`)."""
        self._cyclic_colormap = label_colormap(
            num_colors, seed=seed, background_value=0
        )


class TrackColormap:
    """Node -> display color for a `Tracks` object, with color and alpha as
    independently updatable state (unlike `DirectLabelColormap`, which
    conflates them in one `color_dict`).

    `to_direct_colormap()` produces the napari colormap, patching an
    already-built one in place rather than reconstructing it, so pydantic's
    per-color validation is paid at most once per instance - see that method.
    This replaces three copies of the same mutate-in-place-then-clear-cache
    trick that used to live in `TrackLabels`, `custom_table_widget`, and
    `ortho_views.py`.

    Color is node -> track id -> RGB via `color_source`; there's no per-node
    color setter, since a node's color should always be a pure function of
    its category value. Recoloring happens by changing `color_source` (e.g.
    `shuffle`) and letting the next sync pick it up. `add_node` is the
    exception, for nodes that need a color before `Tracks` knows about them.

    The node/color join is lazy: `set_tracks()` only marks it stale - it does
    not do the O(node count) recompute itself. That cost still has to be paid
    by whichever accessor next needs current colors (see `_sync_nodes`); the
    laziness just means `set_alpha`, the hot path (every selection/hover
    change), skips it entirely when nothing is actually stale, instead of
    paying it on every call regardless.
    """

    def __init__(self, color_source: ColorSource | None = None):
        self.color_source: ColorSource = color_source or CategoricalColorSource()
        self._tracks: Tracks | None = None
        self._nodes_dirty = True
        self._node_colors: dict[int, np.ndarray] = {}
        self._alpha: dict[int, float] = {}
        self._direct_colormap: DirectLabelColormap | None = None

    def map(self, values: np.ndarray) -> np.ndarray:
        """Map track ids to base RGBA (no per-node alpha). Delegates to
        `color_source`, so this is a drop-in replacement anywhere a napari
        colormap's `.map()` is used for track-id coloring.
        """
        return self.color_source.map(values)

    def set_tracks(self, tracks: Tracks | None) -> None:
        """Point this colormap at a `Tracks` object.

        This call itself is O(1) - it just stores the reference and marks
        colors stale, it doesn't touch any nodes. The actual O(node count)
        re-derivation happens later, in `_sync_nodes`, the first time an
        accessor needs current colors. So it's fine to call this even when
        nothing changed, but don't mistake that for the whole operation being
        cheap - something downstream still pays for the resync.
        """
        self._tracks = tracks
        self._nodes_dirty = True

    def _sync_nodes(self) -> None:
        """Recompute the node -> base color mapping from `self._tracks` if
        `set_tracks` marked it stale since the last sync. O(node count) - not
        cheap, just skipped when nothing is dirty. Existing per-node alpha
        overrides for nodes that are still present are preserved; overrides
        for removed nodes are dropped and new nodes default to fully opaque.
        """
        if not self._nodes_dirty:
            return
        self._nodes_dirty = False

        tracks = self._tracks
        nodes = tracks.graph.node_ids() if tracks is not None else []
        track_ids = tracks.get_track_ids(nodes) if tracks is not None else []
        if len(track_ids) > 0:
            # One vectorized call - color_source.map has a large fixed
            # per-call overhead, so mapping per-node is much slower.
            mapped = self.color_source.map(np.asarray(track_ids))
            colors = {node: color.copy() for node, color in zip(nodes, mapped, strict=True)}
        else:
            colors = {}

        self._alpha = {node: self._alpha.get(node, 1.0) for node in nodes}
        self._node_colors = colors

        if self._direct_colormap is not None:
            # Patch color_dict in place instead of reconstructing it.
            color_dict = self._direct_colormap.color_dict
            for stale_node in color_dict.keys() - colors.keys() - {None, 0}:
                del color_dict[stale_node]
            for node in colors:
                color_dict[node] = self._colored(node)
            self._direct_colormap._clear_cache()

    def add_node(self, node: int, category_value) -> None:
        """Add a node not yet known to `self._tracks`, colored via
        `color_source.map(category_value)`. Alpha defaults to opaque.

        `category_value` must be passed in (rather than looked up, like
        `_sync_nodes` does) because callers need this before the node exists
        in the `Tracks` graph - e.g. `TrackLabels._new_label`, previewing a
        color while painting. Named generically rather than `track_id` so a
        differently-keyed `color_source` doesn't change this method's shape.
        """
        self._sync_nodes()
        color = self.color_source.map(np.asarray([category_value]))[0]
        self._node_colors[node] = np.asarray(color, dtype=float).copy()
        self._alpha[node] = 1.0
        if self._direct_colormap is not None:
            self._direct_colormap.color_dict[node] = self._colored(node)
            self._direct_colormap._clear_cache()

    def remove_node(self, node: int) -> None:
        self._sync_nodes()
        self._node_colors.pop(node, None)
        self._alpha.pop(node, None)
        if self._direct_colormap is not None:
            self._direct_colormap.color_dict.pop(node, None)
            self._direct_colormap._clear_cache()

    def set_alpha(self, nodes, value: float) -> None:
        """Set alpha for many nodes at once - the hot path, fired on every
        selection/hover change. Syncs first so it never operates on a stale
        node set; that sync is a no-op (cheap) unless a `set_tracks()` call
        is actually pending, which is the overwhelmingly common case here.
        """
        self._sync_nodes()
        color_dict = (
            self._direct_colormap.color_dict if self._direct_colormap else None
        )
        changed = False
        for node in nodes:
            if node is not None and node in self._alpha:
                self._alpha[node] = value
                if color_dict is not None and node in color_dict:
                    color_dict[node][3] = value
                changed = True
        if changed and self._direct_colormap is not None:
            self._direct_colormap._clear_cache()

    def get_alpha(self, node: int, default: float = 0.0) -> float:
        self._sync_nodes()
        return self._alpha.get(node, default)

    def get_color(self, node: int) -> np.ndarray | None:
        """RGBA (color + alpha) for a node, or None if unknown."""
        self._sync_nodes()
        color = self._node_colors.get(node)
        if color is None:
            return None
        rgba = color.copy()
        rgba[3] = self._alpha.get(node, 1.0)
        return rgba

    @property
    def nodes(self):
        self._sync_nodes()
        return self._node_colors.keys()

    def to_direct_colormap(self) -> DirectLabelColormap:
        """Return a napari `DirectLabelColormap` for the current color/alpha
        state, syncing first if stale (see `_sync_nodes` - not free). Only
        pays pydantic's per-color validation cost once per instance, though:
        every mutator patches the cached object's `color_dict` in place
        afterward instead of rebuilding it.
        """
        self._sync_nodes()
        if self._direct_colormap is None:
            self._direct_colormap = DirectLabelColormap(
                color_dict={
                    **{node: self._colored(node) for node in self._node_colors},
                    None: np.array([0, 0, 0, 0], dtype=float),
                }
            )
        return self._direct_colormap

    def _colored(self, node: int) -> np.ndarray:
        color = self._node_colors[node].copy()
        color[3] = self._alpha.get(node, 1.0)
        return color
