# do not put the from __future__ import annotations as it breaks the injection

import contextlib
from typing import Any

import fastplotlib as fpl
import numpy as np
import pandas as pd
from psygnal import Signal
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QVBoxLayout, QWidget

_SELECT_COLOR = np.array([0.0, 1.0, 1.0, 1.0], dtype=np.float32)  # cyan
_BASE_SIZE = 8.0
_SELECT_SIZE = 13.0


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
        self._selected_rows: list[int] = []

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

        # right-click anywhere resets/fits the view (replaces old CustomViewBox)
        self._figure.renderer.add_event_handler(
            self._on_canvas_pointer_down, "pointer_down"
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
        # axis labels/rulers styling: TODO match old look; for now just rescale
        self.view_direction = view_direction
        self.plot_type = plot_type
        if reset_view:
            self._reset_view()

    def _update_viewed_data(self, view_direction: str) -> None:
        """Re-apply positions for the given view direction (used by flip_axes)."""
        self.view_direction = view_direction
        self._rebuild()

    # ------------------------------------------------------------------ #
    # rendering
    # ------------------------------------------------------------------ #
    def _axis_value_column(self) -> str:
        return self.feature if self.plot_type == "feature" else "x_axis_pos"

    def _compute_positions(self, df: pd.DataFrame) -> np.ndarray:
        """(N, 3) float32 positions. Vertical: (axis_value, -t). Horizontal swaps."""
        axis_col = self._axis_value_column()
        a = df[axis_col].to_numpy(dtype=np.float32)
        t = df["t"].to_numpy(dtype=np.float32)
        n = len(df)
        pos = np.zeros((n, 3), dtype=np.float32)
        if self.view_direction == "vertical":
            pos[:, 0] = a
            pos[:, 1] = -t
        else:  # horizontal: time along x, tracks along y
            pos[:, 0] = t
            pos[:, 1] = -a
        return pos

    def _rebuild(self) -> None:
        """Full rebuild of the scene from ``self.track_df``. Only called when the
        data or view direction changes — not on selection."""
        self._subplot.clear()
        self._scatter = None
        self._edges = None
        self._selected_rows = []

        df = self.track_df
        if df is None or df.empty:
            self._node_ids = np.empty(0, dtype=np.int64)
            self._id_to_row = {}
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

        # nodes: single scatter, uniform circle markers (dots).
        # NOTE: pygfx PointsMarkerMaterial.marker is a single per-material property,
        # not per-vertex, so node-type shapes (division=triangle, end=x) would need
        # separate scatters per shape (as finn did). Deferred — dots for all for now.
        self._scatter = self._subplot.add_scatter(
            data=self._positions,
            colors=colors,
            sizes=_BASE_SIZE,
            markers="circle",
            name="nodes",
        )
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
        # restore previously selected rows to their base color/size
        for row in self._selected_rows:
            self._scatter.colors[row] = self._base_colors[row]
            self._scatter.sizes[row] = _BASE_SIZE

        new_rows = []
        for node_id in selected_nodes:
            row = self._id_to_row.get(int(node_id))
            if row is not None:
                self._scatter.colors[row] = _SELECT_COLOR
                self._scatter.sizes[row] = _SELECT_SIZE
                new_rows.append(row)
        self._selected_rows = new_rows

        if len(new_rows) > 1:
            self._center_on_rows(new_rows)

    # ------------------------------------------------------------------ #
    # picking
    # ------------------------------------------------------------------ #
    def _on_canvas_pointer_down(self, ev) -> None:
        # any click on the canvas gives TreePlot keyboard focus so Q/X/Y work
        self.setFocus()
        # right button (2) anywhere -> reset/fit view to all data
        if getattr(ev, "button", None) == 2:
            self._reset_view()

    def _reset_view(self) -> None:
        """Fit the view to all data, filling the canvas (maintain_aspect=False so the
        wide tree isn't letterboxed). The explicit request_draw is required — changing
        the camera doesn't repaint on its own between interactions."""
        if self._scatter is None:
            return
        with contextlib.suppress(Exception):
            self._subplot.auto_scale(maintain_aspect=False)
            self._figure.canvas.request_draw()

    def _on_click(self, ev) -> None:
        # left button only
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
        """Pan the camera to the given rows if they're outside the current view."""
        if not rows:
            return
        pts = self._positions[rows]
        cx, cy = float(pts[:, 0].mean()), float(pts[:, 1].mean())
        with contextlib.suppress(Exception):
            cam = self._subplot.camera
            state = cam.get_state()
            x, y = state["position"][0], state["position"][1]
            w, h = state["width"], state["height"]
            if (x - w / 2) <= cx <= (x + w / 2) and (y - h / 2) <= cy <= (y + h / 2):
                return  # already visible
            new = dict(state)
            new["position"] = (cx, cy, state["position"][2])
            cam.set_state(new)
