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

    Implementations plug in *how* a base color is chosen - by a categorical id
    (`CategoricalColorSource`, e.g. track id, cell type, lineage id - the only
    one implemented so far), by a continuous feature (e.g. area/volume), or a
    constant color to avoid biasing reviewers - without `TrackColormap` or any
    of its consumers needing to know which. Which values get passed to `map`
    (e.g. track ids vs. some other categorical feature) is entirely up to the
    caller; the source itself has no notion of "track."
    """

    def map(self, values: np.ndarray) -> np.ndarray: ...


class CategoricalColorSource:
    """Maps arbitrary integer ids to colors using napari's cyclic label
    colormap - a distinct color per unique id from a random cycle, with 0
    (conventionally "no category"/background) mapping to transparent.

    This is the default `ColorSource`, used for track-id coloring today, but
    equally applicable to any other categorical value (cell type, lineage id,
    group membership, ...) - it has no track-specific behavior itself.
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
    a single `color_dict`, and constructing one (`DirectLabelColormap(
    color_dict=...)`) re-validates every color via pydantic - expensive for
    graphs with many thousands of labels. This class separates color and
    alpha as independently mutable state, and every mutator (`set_color`,
    `set_alpha`, `remove_node`, `set_nodes`) writes straight into an
    already-built `DirectLabelColormap`'s `color_dict` (already-normalized
    (4,) float arrays, so no `transform_color` validation needed) and clears
    its internal cache, rather than reconstructing it. So pydantic validation
    is only ever paid once per `TrackColormap` instance, the first time
    `to_direct_colormap()` is called - see that method for details.
    `to_direct_colormap()` is the only place that knows how to produce a
    napari `DirectLabelColormap` from this state, replacing three independent
    reimplementations of the "mutate color_dict in place, clear the cache,
    reassign the same object" trick that used to live in `TrackLabels`,
    `custom_table_widget`, and `ortho_views.py`.

    The base color for each track id comes from a `ColorSource`, so swapping
    "color by track id" for "color by a continuous feature" or "one color for
    everything" (to avoid biasing reviewers) is a matter of handing this class
    a different `ColorSource`, not rewriting it or its consumers.
    """

    def __init__(self, color_source: ColorSource | None = None):
        self.color_source: ColorSource = color_source or CategoricalColorSource()
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

        if self._direct_colormap is not None:
            # Patch the existing DirectLabelColormap's color_dict in place -
            # dropping removed nodes, writing already-normalized (4,) float
            # arrays for every current node - instead of reconstructing it,
            # which would re-validate (transform_color) every entry via
            # pydantic even though nothing here needs normalizing.
            color_dict = self._direct_colormap.color_dict
            for stale_node in color_dict.keys() - colors.keys() - {None, 0}:
                del color_dict[stale_node]
            for node in colors:
                color_dict[node] = self._colored(node)
            self._direct_colormap._clear_cache()

    def set_color(self, node: int, color: np.ndarray) -> None:
        """Set a single node's base color directly (e.g. a newly painted label
        that should get the current track's color before `set_nodes` has run
        for it). Preserves the node's current alpha, if any."""
        self._node_colors[node] = np.asarray(color, dtype=float).copy()
        self._alpha.setdefault(node, 1.0)
        if self._direct_colormap is not None:
            # Write the already-normalized (4,) float array straight into the
            # existing DirectLabelColormap's color_dict, instead of going
            # through DirectLabelColormap(color_dict=...), which would
            # re-validate (transform_color) every entry, not just this one.
            self._direct_colormap.color_dict[node] = self._colored(node)
            self._direct_colormap._clear_cache()

    def remove_node(self, node: int) -> None:
        self._node_colors.pop(node, None)
        self._alpha.pop(node, None)
        if self._direct_colormap is not None:
            self._direct_colormap.color_dict.pop(node, None)
            self._direct_colormap._clear_cache()

    def set_alpha(self, nodes, value: float) -> None:
        """Set the alpha for many nodes at once. This is the hot path (fires on
        every selection/hover/highlight change), so it never re-validates
        color state - it only ever mutates alpha in place, both on this
        instance's own state and (if one has already been built) on the
        cached `DirectLabelColormap`'s `color_dict`."""
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
        """Return a napari `DirectLabelColormap` reflecting the current color
        and alpha state, for use as a napari `Labels` layer colormap.

        Only ever pays pydantic's per-color validation cost (`transform_color`
        on every entry, ~0.2s for a 37k-label graph) once, the first time this
        is called: `set_nodes`/`set_color`/`set_alpha`/`remove_node` all keep
        this cached `DirectLabelColormap`'s `color_dict` patched in place
        afterwards (writing already-normalized (4,) float arrays directly,
        skipping validation) and clear its internal cache so napari only
        rebuilds the GPU texture on the next render - see `refresh_colormap`
        in `ContourLabels` for why that distinction matters.
        """
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
