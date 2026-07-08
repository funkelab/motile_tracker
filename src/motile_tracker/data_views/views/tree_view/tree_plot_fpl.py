# do not put the from __future__ import annotations as it breaks the injection

import contextlib
from typing import Any

import fastplotlib as fpl
import numpy as np
import pandas as pd
import pygfx as gfx
from psygnal import Signal
from pygfx.utils.enums import MarkerInt
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QVBoxLayout, QWidget

_SELECT_COLOR = np.array(
    [0.0, 1.0, 1.0, 1.0], dtype=np.float32
)  # cyan selection outline
_EDGE_NONE = np.array(
    [0.0, 0.0, 0.0, 0.0], dtype=np.float32
)  # transparent (unselected)
_SELECT_EDGE_WIDTH = (
    2.0  # px outline around a selected node (fill keeps its track color)
)
_BASE_SIZE = 10.0  # bigger than the old 10 so nodes are easier to click and glyphs read
_SELECT_BUMP = 6.0  # size increase for a selected node
# triangle (split) and cross (end) glyphs have less visual weight than a filled circle
# at the same bounding-box size, so enlarge them to match and stay clickable/legible.
_SYMBOL_SIZE_FACTOR = {"t1": 1.9, "x": 1.4}
# a right-button press that moves <= this many pixels counts as a click (-> reset view);
# a larger movement is a drag, which the pan/zoom controller uses to squeeze x/y.
_RIGHT_CLICK_DRAG_PX = 4.0
# node-type glyphs: track_df["symbol"] uses pyqtgraph names; map to pygfx per-vertex
# marker codes. continue="o" (circle), split="t1" (triangle), end="x" (cross).
_MARKER_CODES = {
    "o": int(MarkerInt.circle),
    "t1": int(MarkerInt.triangle_up),
    "x": int(MarkerInt.cross),
}
_DEFAULT_MARKER = int(MarkerInt.circle)
_AXIS_COLOR = (0.6, 0.6, 0.6, 1.0)  # grey axis lines/ticks/labels (like pyqtgraph)
# Axes live in the subplot's docks (separate fixed-width viewports, like pyqtgraph's
# AxisItem cells around a central ViewBox). The main plot area then clips its contents
# at the dock boundary automatically, so panning the tree past the axis makes cells
# disappear under it — material clipping planes have no effect on the marker material.
_DOCK_LEFT_PX = 54.0  # left margin for a vertical axis (line + tick labels)
_DOCK_BOTTOM_PX = 34.0  # bottom margin for a horizontal axis (line + tick labels)
# thin margin for the minimal (tree-mode) perpendicular axis: just tick marks, no
# numbers — keep it small so the tracks reach almost to the marks (no big empty bar)
_DOCK_MINIMAL_PX = 2.0
# world width assigned to a dock's own camera (arbitrary; the dock viewport is narrow)
_DOCK_WORLD = 100.0
# the axis line sits just inside the dock edge adjacent to the plot. It must NOT be
# exactly at the edge (NDC ±1): pygfx's ruler treats a line lying on the clip boundary
# as off-screen and then generates zero tick labels. Insetting also leaves room for the
# inward-pointing tick marks to stay within the dock viewport.
_AXIS_LINE = _DOCK_WORLD * 0.88
# the perpendicular axis in tree mode is drawn "minimal": no axis line, no numbers,
# just tick marks near the *outer* edge of the canvas (matching the old pyqtgraph look).
_AXIS_EDGE = _DOCK_WORLD * 0.10


class TreePlot(QWidget):
    """fastplotlib (pygfx/wgpu) canvas for the lineage tree.

    Drop-in replacement for the pyqtgraph ``TreePlot``: exposes the same signals
    (``node_clicked``, ``jump_to_node``, ``nodes_selected``, ``update_selection``)
    and the same public methods (``update``, ``set_selection``, ``set_view``,
    ``_update_viewed_data``, ``center_on_node``, ``setMouseEnabled``) so
    ``TreeWidget`` needs no changes beyond which class it instantiates.
    """

    node_clicked = Signal(Any, bool)  # node_id, append
    jump_to_node = Signal(int)
    nodes_selected = Signal(list, bool)
    update_selection = Signal(bool)  # forward/backward in selection history

    def __init__(self) -> None:
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)

        self.view_direction = "vertical"
        self.plot_type = "tree"
        self.feature = None
        self.track_df = pd.DataFrame()

        # per-render caches (stable node_id <-> row index mapping)
        self._node_ids = np.empty(0, dtype=np.int64)
        self._id_to_row: dict[int, int] = {}
        self._positions = np.empty((0, 3), dtype=np.float32)
        self._base_colors = np.empty((0, 4), dtype=np.float32)
        self._base_sizes = np.empty(0, dtype=np.float32)
        self._edge_colors = (
            None  # pygfx per-vertex edge-color buffer (selection outline)
        )
        self._selected_rows: list[int] = []

        # shift-drag rectangle (box-select) state
        self._drag_start: tuple[float, float] | None = None
        self._rubber = None
        # right-button press position (screen px), to tell a click (reset) from a
        # drag (axis squeeze/zoom, handled natively by the pan/zoom controller)
        self._rpress_xy: tuple | None = None

        # build the figure (Qt auto-detected; bitmap present method is dock-safe)
        # names=[[""]] suppresses the default subplot title (which otherwise shows
        # the grid position "(0, 0)" as a title bar above the plot)
        self._figure = fpl.Figure(
            size=(900, 300),
            names=[[""]],
            canvas_kwargs={"present_method": "bitmap"},
        )
        self._subplot = self._figure[0, 0]
        # font_size 0 collapses the title bar's reserved height to the minimum
        # (fastplotlib always reserves 4 + font_size + 4 px above the plot)
        self._subplot.title.font_size = 0
        self._scatter = None
        self._edges = None

        # Axes: fastplotlib's default Axes overlay draws rulers at the *data* bbox
        # edges (so the y-axis floats inset from the canvas and moves with the data)
        # plus xy grids. The old pyqtgraph tree had no grid, no x-axis (in tree mode),
        # and a grey time axis in a fixed left margin that clipped the tree.
        # Reproduce that with pygfx Rulers living in the subplot's docks (separate
        # fixed-width viewports); the main plot area then clips at the dock boundary.
        self._subplot.axes.visible = False
        self._dock_left = self._subplot.docks["left"]
        self._dock_bottom = self._subplot.docks["bottom"]
        self._dock_left.camera.maintain_aspect = False
        self._dock_bottom.camera.maintain_aspect = False
        # the tree fills a wide canvas non-uniformly — never preserve aspect on the
        # MAIN camera (its default is True), else show_rect/reset letterboxes and the
        # tree won't fill. Set persistently so pan/zoom/resize can't revert it.
        self._subplot.camera.maintain_aspect = False
        self._ruler_time = gfx.Ruler(tick_side="left")
        self._ruler_feature = gfx.Ruler(tick_side="left")
        for ruler in (self._ruler_time, self._ruler_feature):
            ruler.color = _AXIS_COLOR
            ruler.tick_size = 6
        # rotated "Time Point" axis title, lives in the time-axis dock
        self._time_label = gfx.Text(
            text="Time Point",
            font_size=13,
            screen_space=True,
            anchor="middle-center",
            material=gfx.TextMaterial(color=_AXIS_COLOR),
        )
        self._configure_docks()

        canvas_widget = self._figure.show()
        # The render canvas (and its inner QRenderWidget child) grab keyboard focus
        # and swallow key events. Force NoFocus on the whole subtree so Q / X / Y
        # bubble up to TreeWidget.keyPressEvent; TreePlot itself keeps StrongFocus
        # and grabs focus on click (see _on_canvas_pointer_down).
        canvas_widget.setFocusPolicy(Qt.NoFocus)
        for child in canvas_widget.findChildren(QWidget):
            child.setFocusPolicy(Qt.NoFocus)
        # keep the canvas tall enough that the subplot viewport height never goes
        # negative during dock layout (avoids wgpu "Viewport size < zero" draw errors)
        canvas_widget.setMinimumHeight(120)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(canvas_widget)
        self.setLayout(layout)

        # keep the rulers pinned to the viewport edges every frame (they follow the
        # camera as the user pans/zooms)
        self._subplot.add_animations(self._update_rulers)

        # canvas mouse handling: right-click reset + shift-drag box-select
        self._figure.renderer.add_event_handler(
            self._on_canvas_pointer_down, "pointer_down"
        )
        self._figure.renderer.add_event_handler(
            self._on_canvas_pointer_move, "pointer_move"
        )
        self._figure.renderer.add_event_handler(
            self._on_canvas_pointer_up, "pointer_up"
        )

    # ------------------------------------------------------------------ #
    # pan/zoom + X/Y axis lock
    # ------------------------------------------------------------------ #
    def setMouseEnabled(self, x: bool, y: bool) -> None:  # noqa: N802 (Qt-style name)
        """Restrict zoom/pan to the given axes (X or Y key held). Reconfigures the
        subplot's own PanZoomController so it stays correctly event-registered."""
        cam = self._subplot.camera
        ctrl = self._subplot.controller
        with contextlib.suppress(Exception):
            ctrl.remove_camera(cam)
            if x and y:
                ctrl.add_camera(cam)
            elif x:
                ctrl.add_camera(cam, include_state={"x", "width"})
            elif y:
                ctrl.add_camera(cam, include_state={"y", "height"})

    # ------------------------------------------------------------------ #
    # public API expected by TreeWidget
    # ------------------------------------------------------------------ #
    def update(
        self,
        track_df: pd.DataFrame,
        view_direction: str,
        plot_type: str,
        feature: str,
        selected_nodes: list[Any],
        reset_view: bool | None = False,
        allow_flip: bool | None = True,
    ) -> None:
        if plot_type == "feature" and (feature is None or feature == ""):
            plot_type = "tree"
        self.view_direction = view_direction
        self.plot_type = plot_type
        self.feature = feature
        self.track_df = track_df if track_df is not None else pd.DataFrame()

        self._configure_docks()
        self._rebuild()
        self.set_selection(selected_nodes, plot_type)
        if reset_view:
            self._reset_view()

    def set_view(
        self,
        view_direction: str,
        plot_type: str,
        reset_view: bool | None = False,
        allow_flip: bool | None = True,
    ) -> None:
        """Store the view direction / plot type. Axis rulers update themselves each
        frame in ``_update_rulers``; ``allow_flip`` is accepted for interface parity
        with the old pyqtgraph TreePlot but is not needed here (orientation is derived
        from ``view_direction`` in ``_compute_positions``)."""
        self.view_direction = view_direction
        self.plot_type = plot_type
        self._configure_docks()
        if reset_view:
            self._reset_view()

    def _update_viewed_data(self, view_direction: str) -> None:
        """Re-apply positions for the given view direction (used by flip_axes)."""
        self.view_direction = view_direction
        self._configure_docks()
        self._rebuild()

    # ------------------------------------------------------------------ #
    # axis rulers (hosted in dock viewports; synced to the main camera)
    # ------------------------------------------------------------------ #
    def _configure_docks(self) -> None:
        """Assign the two rulers to their docks and size both docks. Both axes are
        always shown (the perpendicular axis shows tick marks even in tree mode; its
        number labels are toggled per-mode in ``_update_rulers``). Time axis: left
        dock (vertical) / bottom dock (horizontal); feature axis: the other dock."""
        for obj in (self._ruler_time, self._ruler_feature, self._time_label):
            if obj.parent is not None:
                obj.parent.remove(obj)

        # the perpendicular (feature) axis is minimal in tree mode -> a thin margin
        minimal = _DOCK_MINIMAL_PX
        if self.view_direction == "vertical":
            self._dock_left.scene.add(self._ruler_time, self._time_label)
            self._dock_bottom.scene.add(self._ruler_feature)
            self._dock_left.size = _DOCK_LEFT_PX
            self._dock_bottom.size = (
                _DOCK_BOTTOM_PX if self.plot_type == "feature" else minimal
            )
        else:  # horizontal: time along the bottom
            self._dock_bottom.scene.add(self._ruler_time, self._time_label)
            self._dock_left.scene.add(self._ruler_feature)
            self._dock_bottom.size = _DOCK_BOTTOM_PX
            self._dock_left.size = (
                _DOCK_LEFT_PX if self.plot_type == "feature" else minimal
            )

    def _update_rulers(self) -> None:
        """Each frame, sync both rulers' dock cameras to the main camera's matching
        range and lay each ruler along its dock edge next to the plot. The dock is a
        separate viewport, so the tree is clipped at the axis for free. Number labels
        show on the time axis always, and on the feature axis only in feature mode
        (tree mode shows the perpendicular axis as tick marks only, like pyqtgraph)."""
        if self._scatter is None:
            self._ruler_time.visible = False
            self._ruler_feature.visible = False
            self._time_label.visible = False
            return

        state = self._subplot.camera.get_state()
        px, py = state["position"][0], state["position"][1]
        w, h = state["width"], state["height"]
        left, right = px - w / 2, px + w / 2
        bottom, top = py - h / 2, py + h / 2
        # tree mode: the perpendicular axis is "minimal" (edge tick marks only)
        minimal = self.plot_type != "feature"

        if self.view_direction == "vertical":
            self._sync_left(self._ruler_time, bottom, top, False, self._time_label)
            self._sync_bottom(self._ruler_feature, left, right, minimal)
        else:
            self._sync_bottom(self._ruler_time, left, right, False, self._time_label)
            # a numeric feature axis increases upward (not negated like tree lanes)
            self._sync_left(
                self._ruler_feature,
                bottom,
                top,
                minimal,
                negated=self.plot_type != "feature",
            )

    def _sync_left(self, ruler, bottom, top, minimal, label=None, negated=True) -> None:
        """Lay a vertical ruler in the left dock. Normal: axis line just inside the
        right edge (next to the plot), tick marks toward the plot, numbers in the
        margin to the left. Minimal (tree-mode perpendicular axis): no line, no
        numbers, just tick marks near the far-left edge of the canvas.

        The ruler's value always increases from ``start_pos`` toward ``end_pos``.
        ``negated=True`` (time axis / tree lanes, whose world y = -value) lays it
        top->bottom so values increase downward (parent-at-top). ``negated=False``
        (a numeric feature axis, whose world y = +value) lays it bottom->top so
        feature values increase upward."""
        dock = self._dock_left
        dv = dock.viewport.logical_size
        if dv[0] < 1 or dv[1] < 1:
            return  # transient degenerate size — keep last-good geometry, don't hide
        dock.camera.show_rect(0, _DOCK_WORLD, bottom, top, depth=1)
        axis = _AXIS_EDGE if minimal else _AXIS_LINE
        ruler.visible = True
        # tick_side is relative to the ruler's start->end direction. For the downward
        # ruler "right" puts marks toward the plot and numbers in the left margin; for
        # the upward ruler that same margin side is "left" (else numbers render into the
        # clipped plot area and disappear).
        if negated:  # world y = -value: lay top->bottom, value increases downward
            ruler.tick_side = "right"
            ruler.start_value = -top
            ruler.start_pos = (axis, top, 0)
            ruler.end_pos = (axis, bottom, 0)
        else:  # world y = +value: lay bottom->top, value increases upward
            ruler.tick_side = "left"
            ruler.start_value = bottom
            ruler.start_pos = (axis, bottom, 0)
            ruler.end_pos = (axis, top, 0)
        ruler.update(dock.camera, dv)
        ruler._line.visible = not minimal
        ruler._text.visible = not minimal
        if label is not None:
            label.visible = not minimal
            label.local.rotation = (0.0, 0.0, 0.70710677, 0.70710677)  # +90°
            label.local.position = (_DOCK_WORLD * 0.14, (top + bottom) / 2, 0)

    def _sync_bottom(self, ruler, left, right, minimal, label=None) -> None:
        """Lay a horizontal ruler in the bottom dock. Normal: axis line just inside
        the top edge (next to the plot), tick marks toward the plot, numbers in the
        margin below. Minimal (tree-mode perpendicular axis): no line, no numbers,
        just tick marks near the bottom edge of the canvas."""
        dock = self._dock_bottom
        dv = dock.viewport.logical_size
        if dv[0] < 1 or dv[1] < 1:
            return  # transient degenerate size — keep last-good geometry, don't hide
        dock.camera.show_rect(left, right, 0, _DOCK_WORLD, depth=1)
        axis = _AXIS_EDGE if minimal else _AXIS_LINE
        ruler.visible = True
        ruler.tick_side = "right"  # marks toward plot, numbers extend down into margin
        ruler.start_value = left
        ruler.start_pos = (left, axis, 0)
        ruler.end_pos = (right, axis, 0)
        ruler.update(dock.camera, dv)
        ruler._line.visible = not minimal
        ruler._text.visible = not minimal
        if label is not None:
            label.visible = not minimal
            label.local.rotation = (0.0, 0.0, 0.0, 1.0)  # horizontal
            label.local.position = ((left + right) / 2, _DOCK_WORLD * 0.14, 0)

    # ------------------------------------------------------------------ #
    # rendering
    # ------------------------------------------------------------------ #
    def _axis_value_column(self) -> str:
        return self.feature if self.plot_type == "feature" else "x_axis_pos"

    def _compute_positions(self, df: pd.DataFrame) -> np.ndarray:
        """(N, 3) float32 positions. Vertical: (axis_value, -t). Horizontal swaps.

        In horizontal view the perpendicular (y) axis is negated so tree lanes read
        top-to-bottom like the old pyqtgraph tree. But for a numeric *feature* the
        y-axis should increase upward (larger values higher), so feature positions are
        NOT negated. Feature plots are always horizontal (see TreeWidget), so this only
        affects the horizontal branch.
        """
        axis_col = self._axis_value_column()
        a = df[axis_col].to_numpy(dtype=np.float32)
        t = df["t"].to_numpy(dtype=np.float32)
        n = len(df)
        pos = np.zeros((n, 3), dtype=np.float32)
        if self.view_direction == "vertical":
            pos[:, 0] = a
            pos[:, 1] = -t
        else:  # horizontal: time along x, perpendicular axis along y
            pos[:, 0] = t
            pos[:, 1] = a if self.plot_type == "feature" else -a
        return pos

    def _rebuild(self) -> None:
        """Full rebuild of the scene from ``self.track_df``. Only called when the
        data or view direction changes — not on selection."""
        self._subplot.clear()
        self._scatter = None
        self._edges = None
        self._edge_colors = None
        self._rubber = None  # cleared with the scene; recreated lazily on next drag
        self._selected_rows = []

        df = self.track_df
        if df is None or df.empty:
            self._node_ids = np.empty(0, dtype=np.int64)
            self._id_to_row = {}
            self._base_sizes = np.empty(0, dtype=np.float32)
            return

        self._node_ids = df["node_id"].to_numpy()
        self._id_to_row = {int(nid): i for i, nid in enumerate(self._node_ids)}
        self._positions = self._compute_positions(df)

        # colors: track_df["color"] is per-row RGBA in 0-255 -> float 0-1
        colors = np.stack(df["color"].to_numpy()).astype(np.float32) / 255.0
        self._base_colors = colors.copy()

        # edges under nodes: ALL parent->child edges in ONE NaN-separated line
        # (single draw call / buffer upload — far cheaper than a per-edge collection)
        edge_pos, edge_cols = self._build_edges(df, colors)
        if edge_pos is not None:
            self._edges = self._subplot.add_line(
                data=edge_pos,
                colors=edge_cols,
                thickness=1.5,
                name="edges",
            )

        # nodes: single scatter with per-vertex marker shapes (node-type glyphs).
        # A single scatter keeps selection surgical; per-vertex markers are enabled by
        # setting the material's marker_mode to "vertex" + a geometry "markers" int
        # buffer (pygfx's per-vertex marker path), so we avoid finn's 3-scatter split.
        symbols = df["symbol"].to_numpy()
        # per-vertex sizes: enlarge triangle/cross glyphs so they read as big as the dots
        factors = np.array(
            [_SYMBOL_SIZE_FACTOR.get(s, 1.0) for s in symbols], dtype=np.float32
        )
        self._base_sizes = (_BASE_SIZE * factors).astype(np.float32)
        self._scatter = self._subplot.add_scatter(
            data=self._positions,
            colors=colors,
            sizes=self._base_sizes,
            markers="circle",
            name="nodes",
        )
        codes = np.array(
            [_MARKER_CODES.get(s, _DEFAULT_MARKER) for s in symbols], dtype=np.int32
        )
        wo = self._scatter.world_object
        wo.material.marker_mode = "vertex"
        wo.geometry.markers = gfx.Buffer(codes)
        # Selection is shown as an OUTLINE (like the old pyqtgraph tree): a uniform
        # edge that is transparent for unselected nodes and cyan for selected ones, so
        # a selected node keeps its track-color fill. Per-vertex edge colors need
        # edge_color_mode="vertex" + a geometry "edge_colors" buffer; edge_width is
        # uniform (pygfx has no per-vertex width), transparent nodes just show no edge.
        wo.material.edge_color_mode = "vertex"
        wo.material.edge_width = _SELECT_EDGE_WIDTH
        edge_colors = np.zeros((len(self._node_ids), 4), dtype=np.float32)
        wo.geometry.edge_colors = gfx.Buffer(edge_colors)
        self._edge_colors = wo.geometry.edge_colors
        self._scatter.add_event_handler(self._on_click, "pointer_down")

    def _build_edges(self, df: pd.DataFrame, colors: np.ndarray):
        """Vectorized edge build for a single NaN-separated ``gfx.Line``.

        Returns ``(positions, colors)`` where positions is ``(3E, 3)`` laid out as
        ``[parent, child, NaN]`` per edge (the NaN row breaks the polyline into
        independent segments), and colors matches. Returns ``(None, None)`` if
        there are no edges.
        """
        n = len(df)
        parent_ids = df["parent_id"].to_numpy()
        # vectorized parent_id -> row index (NaN where the parent isn't present)
        row_of = pd.Series(np.arange(n), index=self._node_ids)
        parent_rows = row_of.reindex(parent_ids).to_numpy()
        mask = (parent_ids != 0) & ~np.isnan(parent_rows)
        if not mask.any():
            return None, None

        child_rows = np.nonzero(mask)[0]
        par_rows = parent_rows[mask].astype(np.int64)
        e = len(child_rows)

        edge_pos = np.full((3 * e, 3), np.nan, dtype=np.float32)
        edge_pos[0::3] = self._positions[par_rows]
        edge_pos[1::3] = self._positions[child_rows]

        edge_cols = np.ones((3 * e, 4), dtype=np.float32)
        c = colors[child_rows]
        edge_cols[0::3] = c
        edge_cols[1::3] = c
        edge_cols[2::3] = c
        return edge_pos, edge_cols

    # ------------------------------------------------------------------ #
    # selection (surgical: only touch changed rows)
    # ------------------------------------------------------------------ #
    def set_selection(self, selected_nodes: list[Any], plot_type: str) -> None:
        if self._scatter is None:
            return
        # Selection = a cyan outline + a size bump; the fill keeps its track color so
        # you can still tell which track a selected node belongs to (like the old tree).
        # Surgical: only touch changed rows' edge-color buffer + size.
        # restore previously selected rows: clear the outline and the size bump
        for row in self._selected_rows:
            self._set_edge_color(row, _EDGE_NONE)
            self._scatter.sizes[row] = self._base_sizes[row]

        new_rows = []
        for node_id in selected_nodes:
            row = self._id_to_row.get(int(node_id))
            if row is not None:
                self._set_edge_color(row, _SELECT_COLOR)
                self._scatter.sizes[row] = self._base_sizes[row] + _SELECT_BUMP
                new_rows.append(row)
        self._selected_rows = new_rows

        if len(new_rows) > 1:
            self._center_on_rows(new_rows)

    def _set_edge_color(self, row: int, rgba: np.ndarray) -> None:
        """Set one node's per-vertex outline color and upload just that element."""
        if self._edge_colors is None:
            return
        self._edge_colors.data[row] = rgba
        self._edge_colors.update_range(row, 1)

    # ------------------------------------------------------------------ #
    # picking
    # ------------------------------------------------------------------ #
    def _on_canvas_pointer_down(self, ev) -> None:
        # any click on the canvas gives TreePlot keyboard focus so Q/X/Y work
        self.setFocus()
        button = getattr(ev, "button", None)
        # right button (2): a plain click resets the view; a drag squeezes/zooms the
        # x or y axis (the controller's native mouse2 "zoom" drag). Only record the
        # press here — resetting now would override the drag-zoom. pointer_up decides
        # click vs drag. Do NOT disable the controller, so the drag-zoom still runs.
        if button == 2:
            self._rpress_xy = (getattr(ev, "x", None), getattr(ev, "y", None))
            return
        # mouse side buttons -> step through selection history (like browser back/fwd).
        # back (4) = previous selection, forward (5) = next. TreeWidget connects
        # update_selection -> tracks_viewer.select_node_set_from_history(previous=...).
        if button == 4:
            self.update_selection.emit(True)
            return
        if button == 5:
            self.update_selection.emit(False)
            return
        # left button + Shift -> start a rubber-band box-select (like the old tree).
        # Disable the pan controller for the duration so the drag draws a box
        # instead of panning.
        if button == 1 and "Shift" in set(getattr(ev, "modifiers", ()) or ()):
            world = self._subplot.map_screen_to_world(ev, allow_outside=True)
            if world is not None:
                self._drag_start = (float(world[0]), float(world[1]))
                self._subplot.controller.enabled = False

    def _on_canvas_pointer_move(self, ev) -> None:
        if self._drag_start is None:
            return
        world = self._subplot.map_screen_to_world(ev, allow_outside=True)
        if world is not None:
            self._update_rubber(self._drag_start, (float(world[0]), float(world[1])))

    def _on_canvas_pointer_up(self, ev) -> None:
        # right-button release: reset only if it was a click (moved <= threshold). A
        # larger movement was a drag-zoom already applied by the controller.
        if self._rpress_xy is not None:
            x0, y0 = self._rpress_xy
            self._rpress_xy = None
            x1, y1 = getattr(ev, "x", None), getattr(ev, "y", None)
            moved = abs(x1 - x0) + abs(y1 - y0) if None not in (x0, y0, x1, y1) else 0.0
            if moved <= _RIGHT_CLICK_DRAG_PX:
                self._reset_view()
            return

        if self._drag_start is None:
            return
        world = self._subplot.map_screen_to_world(ev, allow_outside=True)
        x0, y0 = self._drag_start
        self._drag_start = None
        self._clear_rubber()
        self._subplot.controller.enabled = True
        if world is None:
            return
        x1, y1 = float(world[0]), float(world[1])
        # ignore a plain shift-click (no drag) — that's handled as node append
        if abs(x1 - x0) > 1e-9 or abs(y1 - y0) > 1e-9:
            self.select_points_in_rect(x0, x1, y0, y1)

    def _ensure_rubber(self):
        if self._rubber is None:
            self._rubber = self._subplot.add_line(
                np.zeros((5, 3), dtype=np.float32),
                colors="yellow",
                thickness=1.0,
                name="_rubber",
            )
            self._rubber.visible = False
        return self._rubber

    def _update_rubber(self, start: tuple, cur: tuple) -> None:
        x0, y0 = start
        x1, y1 = cur
        r = self._ensure_rubber()
        r.data[:] = np.array(
            [[x0, y0, 0], [x1, y0, 0], [x1, y1, 0], [x0, y1, 0], [x0, y0, 0]],
            dtype=np.float32,
        )
        r.visible = True
        self._figure.canvas.request_draw()

    def _clear_rubber(self) -> None:
        if self._rubber is not None:
            self._rubber.visible = False
            self._figure.canvas.request_draw()

    def _reset_view(self) -> None:
        """Fit the view to the node positions, filling the canvas.

        Framed directly from the scatter data via ``camera.show_rect`` rather than
        ``auto_scale``: auto_scale unions the bounds of *all* scene objects (the
        rulers, the NaN-separated edge line, the idle rubber rectangle), so it can't
        reliably tighten to the tree — e.g. when zoomed out, the rulers sit at the
        wide viewport edges. Framing from ``self._positions`` ignores everything else.
        maintain_aspect=False fills the wide canvas; request_draw is required because
        a camera change doesn't repaint on its own between interactions."""
        if len(self._positions) == 0:
            return
        xs, ys = self._positions[:, 0], self._positions[:, 1]
        xmin, xmax = float(np.min(xs)), float(np.max(xs))
        ymin, ymax = float(np.min(ys)), float(np.max(ys))
        px = (xmax - xmin) * 0.05 or 1.0
        py = (ymax - ymin) * 0.05 or 1.0
        # the axis lives in a dock outside the plot area, so no gutter compensation
        # is needed here — fit the data to the full (already-inset) plot viewport.
        with contextlib.suppress(Exception):
            cam = self._subplot.camera
            cam.maintain_aspect = False
            cam.show_rect(xmin - px, xmax + px, ymin - py, ymax + py, depth=1)
            # drop any in-flight pan/zoom momentum, else the PanZoomController's
            # per-frame tick() keeps driving the camera from its own cached target
            # and overrides show_rect (reset would appear stuck at the drag position).
            actions = getattr(self._subplot.controller, "_actions", None)
            if actions:
                actions.clear()
            self._figure.canvas.request_draw()

    def _on_click(self, ev) -> None:
        # ignore middle/right buttons (0 = primary/left, 1 = left on some backends)
        if getattr(ev, "button", 1) not in (1, 0):
            return
        idx = ev.pick_info.get("vertex_index")
        if idx is None:
            return
        node_id = int(self._node_ids[int(idx)])
        mods = set(getattr(ev, "modifiers", ()) or ())
        if "Control" in mods or "Meta" in mods:
            self.jump_to_node.emit(node_id)
        else:
            append = "Shift" in mods
            self.node_clicked.emit(node_id, append)
            self.setFocus()

    def select_points_in_rect(self, x0, x1, y0, y1) -> None:
        """Box-select: emit all node ids whose positions fall in the rect."""
        if len(self._positions) == 0:
            return
        xs, ys = self._positions[:, 0], self._positions[:, 1]
        inside = (
            (xs >= min(x0, x1))
            & (xs <= max(x0, x1))
            & (ys >= min(y0, y1))
            & (ys <= max(y0, y1))
        )
        picked = [int(nid) for nid in self._node_ids[inside]]
        if picked:
            self.nodes_selected.emit(picked, True)

    # ------------------------------------------------------------------ #
    # centering
    # ------------------------------------------------------------------ #
    def center_on_node(self, node_id: int) -> None:
        row = self._id_to_row.get(int(node_id))
        if row is None:
            return
        self._center_on_rows([row])

    def _center_on_rows(self, rows: list[int]) -> None:
        """Bring the given rows into view.

        Keeps the current zoom if the rows already fit in the viewport; otherwise
        zooms out *just enough* (per axis) to fit them, and never zooms in. Used for
        single-node centering and for multi-node selection — e.g. the two endpoints of
        a just-broken edge, which may now sit far apart: rather than pan to their
        midpoint at the current zoom (leaving both off-screen), we widen the view so
        both are visible.
        """
        if not rows:
            return
        pts = self._positions[rows]
        xmin, xmax = float(pts[:, 0].min()), float(pts[:, 0].max())
        ymin, ymax = float(pts[:, 1].min()), float(pts[:, 1].max())
        with contextlib.suppress(Exception):
            cam = self._subplot.camera
            state = cam.get_state()
            x, y = state["position"][0], state["position"][1]
            w, h = state["width"], state["height"]
            # already fully visible at the current zoom -> nothing to do
            if (
                (x - w / 2) <= xmin
                and xmax <= (x + w / 2)
                and (y - h / 2) <= ymin
                and ymax <= (y + h / 2)
            ):
                return
            # grow the view only if the rows don't fit (never shrink = never zoom in);
            # dividing the span by 0.8 leaves a ~10% margin so nodes aren't flush to
            # the edge. For a single row the span is 0, so the zoom is preserved and we
            # simply pan to it.
            new = dict(state)
            new["position"] = (
                (xmin + xmax) / 2,
                (ymin + ymax) / 2,
                state["position"][2],
            )
            new["width"] = max(w, (xmax - xmin) / 0.8)
            new["height"] = max(h, (ymax - ymin) / 0.8)
            cam.set_state(new)
            # clear in-flight momentum so the controller doesn't override the change
            actions = getattr(self._subplot.controller, "_actions", None)
            if actions:
                actions.clear()
