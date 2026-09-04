from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import numpy as np
from napari.utils import DirectLabelColormap
from napari.utils.colormaps import label_colormap

if TYPE_CHECKING:
    from funtracks.data_model import Tracks


@runtime_checkable
class ColorSource(Protocol):
    """Anything that can map an array of ids/values to an (N, 4) RGBA array.

    Duck-type compatible with `napari.utils.colormaps.CyclicLabelColormap.map`
    (and `Colormap.map` in general), so a `ColorSource` can be handed directly
    to code that only ever calls `.map(...)` on a napari colormap (napari's
    `Tracks` layer `colormaps_dict`, `TrackGraph`/`TrackPoints`/`export_dialog`
    track-id coloring, etc.) without those call sites needing to change.

    Implementations plug in *how* a base color is chosen - by track id
    (`TrackIdColorSource`, the only one implemented so far), by a continuous
    feature (e.g. area/volume), or a constant color to avoid biasing reviewers
    - without `TrackColormap` or any of its consumers needing to know which.
    """

    def map(self, values: np.ndarray) -> np.ndarray: ...


class TrackIdColorSource:
    """Maps track ids to colors using napari's cyclic label colormap.

    This is the default `ColorSource`: each track id gets a distinct color
    from a random cycle, with 0 (no track) mapping to transparent.
    """

    def __init__(self, num_colors: int = 49, seed: float = 0.5):
        self._cyclic_colormap = label_colormap(
            num_colors, seed=seed, background_value=0
        )

    def map(self, values: np.ndarray) -> np.ndarray:
        return self._cyclic_colormap.map(values)

    def shuffle(self, num_colors: int, seed: float) -> None:
        """Replace the underlying color cycle (e.g. to get a new, more separated
        set of colors, see `TrackLabels.new_colormap`)."""
        self._cyclic_colormap = label_colormap(
            num_colors, seed=seed, background_value=0
        )


class TrackColormap:
    """Owns the node -> display color mapping for a `Tracks` object, keeping
    color (which base RGB a node/track gets) and alpha (highlighted /
    foreground / background / hidden) as independent, independently
    updatable pieces of state.

    Rationale: `napari.utils.DirectLabelColormap` conflates color and alpha in
    a single `color_dict`, and rebuilding it (`DirectLabelColormap(color_dict=
    ...)`) re-validates every color via pydantic - expensive for graphs with
    many thousands of labels, and unnecessary for changes that only touch
    alpha (selection, hover, foreground/background opacity). This class
    separates the two so that:

    - `set_color` / `recolor_from` only run when the node -> base color
      mapping actually changes (new track, recolor, merge/split).
    - `set_alpha` is the hot path (fires on every selection/hover change) and
      never touches color state.
    - `to_direct_colormap()` is the only place that knows how to produce a
      napari `DirectLabelColormap` from this state, replacing three
      independent reimplementations of the same "mutate color_dict in place,
      clear the cache, reassign the same object" trick that used to live in
      `TrackLabels`, `custom_table_widget`, and `ortho_views.py`.

    The base color for each track id comes from a `ColorSource`, so swapping
    "color by track id" for "color by a continuous feature" or "one color for
    everything" (to avoid biasing reviewers) is a matter of handing this class
    a different `ColorSource`, not rewriting it or its consumers.
    """

    def __init__(self, color_source: ColorSource | None = None):
        self.color_source: ColorSource = color_source or TrackIdColorSource()
        self._node_colors: dict[int, np.ndarray] = {}
        self._alpha: dict[int, float] = {}
        self._direct_colormap: DirectLabelColormap | None = None

    def map(self, values: np.ndarray) -> np.ndarray:
        """Map track ids to their base RGBA color, ignoring any per-node alpha
        overrides set on this instance.

        Delegates to `color_source`, so this instance is a drop-in replacement
        anywhere a napari colormap's `.map()` is used for track-id coloring
        (e.g. `TrackGraph`/`TrackPoints`/`export_dialog`/`tree_widget_utils`).
        """
        return self.color_source.map(values)

    def set_nodes(self, tracks: Tracks) -> None:
        """(Re)compute the node -> base color mapping for every node currently
        in `tracks`, using `color_source` to look up track-id colors.

        This is the "rare" path: call it when the set of nodes changes (new
        Tracks object, nodes added/removed in bulk) or the color source itself
        changes (recolor). Existing per-node alpha overrides for nodes that
        are still present are preserved; overrides for removed nodes are
        dropped and new nodes default to fully opaque.
        """
        nodes = tracks.graph.node_ids()
        track_ids = tracks.get_track_ids(nodes)
        if len(track_ids) > 0:
            # One vectorized call: color_source.map has a large fixed per-call
            # overhead, so mapping the whole array at once is far faster than
            # calling it per node or per unique track id.
            mapped = self.color_source.map(np.asarray(track_ids))
            colors = {node: color.copy() for node, color in zip(nodes, mapped, strict=True)}
        else:
            colors = {}

        self._alpha = {node: self._alpha.get(node, 1.0) for node in nodes}
        self._node_colors = colors
        self._direct_colormap = None

    def set_color(self, node: int, color: np.ndarray) -> None:
        """Set a single node's base color directly (e.g. a newly painted label
        that should get the current track's color before `set_nodes` has run
        for it). Preserves the node's current alpha, if any."""
        self._node_colors[node] = np.asarray(color, dtype=float).copy()
        self._alpha.setdefault(node, 1.0)
        self._direct_colormap = None

    def remove_node(self, node: int) -> None:
        self._node_colors.pop(node, None)
        self._alpha.pop(node, None)
        self._direct_colormap = None

    def set_alpha(self, nodes, value: float) -> None:
        """Set the alpha for many nodes at once. This is the hot path (fires on
        every selection/hover/highlight change), so it never touches color
        state or triggers napari colormap validation."""
        for node in nodes:
            if node is not None and node in self._alpha:
                self._alpha[node] = value

    def get_alpha(self, node: int, default: float = 0.0) -> float:
        return self._alpha.get(node, default)

    def get_color(self, node: int) -> np.ndarray | None:
        """Return the current RGBA (base color with alpha applied) for a node,
        or None if the node is not known to this colormap."""
        color = self._node_colors.get(node)
        if color is None:
            return None
        rgba = color.copy()
        rgba[3] = self._alpha.get(node, 1.0)
        return rgba

    @property
    def nodes(self):
        return self._node_colors.keys()

    def to_direct_colormap(self) -> DirectLabelColormap:
        """Build (or return the cached) napari `DirectLabelColormap` combining
        the current color and alpha state, for use as a napari `Labels` layer
        colormap.

        Rebuilds from scratch (paying pydantic's per-color validation cost)
        only the first time this is called after `set_nodes`/`set_color`/
        `remove_node` changed the color_dict's keys or colors. A pure
        `set_alpha` change reuses the existing `DirectLabelColormap` object,
        mutating its `color_dict` alphas in place and clearing its internal
        cache so napari only rebuilds the GPU texture, not re-validates every
        color - see `refresh_colormap` in `ContourLabels` for why this
        matters (~0.2s vs ~0.08s for a 37k-label graph).
        """
        if self._direct_colormap is None:
            self._direct_colormap = DirectLabelColormap(
                color_dict={
                    **{
                        node: self._colored(node)
                        for node in self._node_colors
                    },
                    None: np.array([0, 0, 0, 0], dtype=float),
                }
            )
            return self._direct_colormap

        color_dict = self._direct_colormap.color_dict
        for node, alpha in self._alpha.items():
            color = color_dict.get(node)
            if color is not None:
                color[3] = alpha
        self._direct_colormap._clear_cache()
        return self._direct_colormap

    def _colored(self, node: int) -> np.ndarray:
        color = self._node_colors[node].copy()
        color[3] = self._alpha.get(node, 1.0)
        return color
