import numpy as np
import pandas as pd
from matplotlib.colors import to_rgba
from napari.utils import DirectLabelColormap
from qtpy.QtCore import (
    QItemSelection,
    QItemSelectionModel,
    Qt,
    QTimer,
)
from qtpy.QtGui import QColor, QKeyEvent, QMouseEvent, QPen
from qtpy.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.data_views.keybindings_config import GENERAL_KEY_ACTIONS
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class NoSelectionHighlightDelegate(QStyledItemDelegate):
    """Prevents Qt from painting the default selection background,
    preserving each row's custom background color, and draws a cyan border instead."""

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)

        table = index.model().parent()

        if opt.state & QStyle.State_Selected:
            opt.state &= ~QStyle.State_Selected

        # Paint normally first (preserving your setBackground + setForeground)
        super().paint(painter, opt, index)

        # Draw a cyan border around the *entire row* if selected
        if index.row() in {i.row() for i in table.selectedIndexes()}:
            pen = QPen(Qt.cyan, 2)
            painter.setPen(pen)
            painter.drawRect(opt.rect.adjusted(1, 1, -2, -2))


class FloatDelegate(QStyledItemDelegate):
    def __init__(self, decimals, parent=None):
        super().__init__(parent)
        self.nDecimals = decimals

    def displayText(self, value, locale):
        try:
            number = float(value)
        except (ValueError, TypeError):
            return str(value)

        if number.is_integer():
            return str(int(number))
        return f"{number:.{self.nDecimals}f}"


class CustomTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verticalHeader().setSectionsClickable(False)
        self._drag_start_row = None

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse click events and check modifiers for different behaviors:
        - Plain click: single selection, toggle if already selected
        - Shift: append to selection.
        - Ctrl/CMD: center node, should not affect selection.
        """
        index = self.indexAt(event.pos())
        if not index.isValid():
            return

        row = index.row()
        modifiers = event.modifiers()

        ctrl = modifiers & Qt.ControlModifier
        shift = modifiers & Qt.ShiftModifier

        sel_model = self.selectionModel()
        model_index = self.model().index(row, 0)

        if ctrl:
            self.parent().center_node(model_index)
            event.accept()
            return

        if shift:
            # Append single row
            sel_model.select(
                model_index, QItemSelectionModel.Select | QItemSelectionModel.Rows
            )
            self._drag_start_row = row
            event.accept()
            return

        # Plain click: single selection, toggle if already selected
        if sel_model.isSelected(model_index):
            sel_model.select(
                model_index, QItemSelectionModel.Deselect | QItemSelectionModel.Rows
            )
            self._drag_start_row = None
        else:
            sel_model.clearSelection()
            sel_model.select(
                model_index, QItemSelectionModel.Select | QItemSelectionModel.Rows
            )
            self._drag_start_row = row

        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Record mouse drag events to select a range. In combination with shift, it is
        possible to select multiple ranges.
        """

        if not (event.buttons() & Qt.LeftButton):
            return

        index = self.indexAt(event.pos())
        if not index.isValid() or self._drag_start_row is None:
            return

        current_row = index.row()
        start = self._drag_start_row
        end = current_row

        top = min(start, end)
        bottom = max(start, end)

        selection = QItemSelection(
            self.model().index(top, 0),
            self.model().index(bottom, self.columnCount() - 1),
        )

        modifiers = event.modifiers()

        if modifiers & Qt.ShiftModifier:
            # add range
            self.selectionModel().select(selection, QItemSelectionModel.Select)
        else:
            # replace selection with this range
            self.selectionModel().select(selection, QItemSelectionModel.ClearAndSelect)

        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_row = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for common tracksviewer actions."""
        # Get the parent ColoredTableWidget to access tracks_viewer
        parent = self.parent()
        if parent is None or not hasattr(parent, "tracks_viewer"):
            super().keyPressEvent(event)
            return

        tracks_viewer = parent.tracks_viewer

        # Get the action name from the general keybind mapping
        action_name = GENERAL_KEY_ACTIONS.get(event.key())
        if action_name:
            method = getattr(tracks_viewer, action_name, None)
            if method:
                method()
                event.accept()
                return

        # Allow parent class to handle other events
        super().keyPressEvent(event)


class ColoredTableWidget(QWidget):
    """Customized table widget with colored rows based on label colors in a napari Labels layer"""

    def __init__(self, tracks_viewer: TracksViewer, df: pd.DataFrame):
        super().__init__()

        self.tracks_viewer = tracks_viewer
        self._table_widget = CustomTableWidget()
        self.special_selection = []

        self.set_data(df)
        self.ascending = False  # for choosing whether to sort ascending or descending
        self._syncing = False

        # Connect to single click in the header to sort the table.
        self._table_widget.horizontalHeader().sectionClicked.connect(self._sort_table)

        # Instruction label to explain left and right mouse click.
        label = QLabel(
            "Use left mouse click to select and center a label. Use Ctrl/CMD to center a node, Shift to append to selection. Use mouse drag to select a range."
        )
        label.setWordWrap(True)
        font = label.font()
        font.setItalic(True)
        label.setFont(font)

        main_layout = QVBoxLayout()
        main_layout.addWidget(label)
        main_layout.addWidget(self._table_widget)
        self.setLayout(main_layout)
        self.setMinimumHeight(300)

        # Selection behavior
        self._table_widget.setStyleSheet("""
            QTableWidget::item:selected {
                border: 2px solid cyan;
            }
        """)

        self._table_widget.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: rgb(40,40,40);       /* normal */
                color: white;
                padding: 4px;
                border: 1px solid #555;
            }

            QHeaderView::section:selected {            /* when the row is selected */
                background-color: cyan;
                color: black;
            }

            QHeaderView::section:pressed {
                background-color: cyan;
                color: black;
            }
        """)

        self._table_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self._table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)

        delegate = NoSelectionHighlightDelegate(self._table_widget)
        self._table_widget.setItemDelegate(delegate)

        self._table_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.tracks_viewer.selected_nodes.list_updated.connect(self._update_selected)
        self.tracks_viewer.center_node.connect(self.scroll_to_node)

    def _update_selected(self) -> None:
        """Select the rows belonging to the nodes that are in the selection list of the
        TracksViewer
        """
        if self._syncing:
            return

        self._syncing = True
        try:
            selected_nodes = self.tracks_viewer.selected_nodes.as_list
            rows = [
                self._find_row(ID=node) for node in selected_nodes if node is not None
            ]

            self._table_widget.clearSelection()
            self._select_rows(rows)

        finally:
            self._syncing = False

    def _select_rows(self, rows: list[int]) -> None:
        """Replace current table selection with given rows.

        Args:
            rows (list[int]): list of indices to be selected.
        """

        if not rows:
            return

        model = self._table_widget.model()
        selection_model = self._table_widget.selectionModel()

        selection = QItemSelection()

        for row in rows:
            if row is None:
                continue
            index = model.index(row, 0)
            selection.select(index, index)

        selection_model.select(
            selection,
            QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows,
        )

    def _on_selection_changed(self) -> None:
        """Update the node selection list on TracksViewer based on the rows selected in
        the table.
        """
        if self._syncing:
            return  # skip if selection was changed programmatically

        rows = sorted({index.row() for index in self._table_widget.selectedIndexes()})
        if not rows:
            return

        labels = [self._table["ID"][row] for row in rows]

        # Ensure we do not call this when it is still updating.
        self._syncing = True
        try:
            self.tracks_viewer.selected_nodes.add_list(labels)
        finally:
            self._syncing = False

        QTimer.singleShot(0, self._update_label_colormap)

    def center_node(self, index: int) -> None:
        """Call TracksViewer to center Viewer on the node of current index

        Args:
            index (int): the index in the table corresponding to the to be centered node.
        """
        if self._syncing:
            return

        self._syncing = True
        try:
            row = index.row()
            node = self._table["ID"][row]
            self.tracks_viewer.center_on_node(node)
        finally:
            self._syncing = False

    def scroll_to_node(self, node: int) -> None:
        """Identify the index of the node that was selected, and scroll to that index.

        Args:
            node (int): the node to scroll to.
        """

        if self._syncing:
            return

        self._syncing = True
        try:
            index = self._find_row(ID=node)
            selection_model = self._table_widget.selectionModel()

            model_index = self._table_widget.model().index(index, 0)

            if (
                selection_model.isSelected(model_index)
                and len(selection_model.selectedRows()) == 1
            ):
                return

            self.scroll_to_row(index)

        finally:
            self._syncing = False

    def scroll_to_row(self, index: int) -> None:
        """Scroll to make sure the row is in view

        Args:
            index (int): the index to scroll to
        """
        self._table_widget.scrollTo(
            self._table_widget.model().index(index, 0),
            QAbstractItemView.PositionAtCenter,
        )

    def _find_row(self, **conditions) -> int | None:
        """
        Find the first row matching the given conditions (e.g. label=12, time_point=5)
        Returns: row index or None
        """

        n_rows = self._table_widget.rowCount()

        for row in range(n_rows):
            # Only check conditions that are not None
            if all(
                float(self._table[col][row]) == float(val)
                for col, val in conditions.items()
                if val is not None
            ):
                return row

        return None

    def set_data(
        self, df: pd.DataFrame, columns_to_display: list[str] | None = None
    ) -> None:
        """Set the content of the table from a dictionary

        Args:
            df (pd.DataFrame): dataframe holding the tree widget data, one row per node.
            columns_to_display (list[str] | None): optional list of column headers to
                filter on (should correspond to the tracks features). Column 'node_id'
                should always be included.
        """

        if columns_to_display is not None and len(df.columns) > 0:
            df = df[[col for col in columns_to_display if col in df.columns]]
            df = df.rename(columns={"node_id": "ID"})
        table: dict[str, np.ndarray] = {col: df[col].to_numpy() for col in df.columns}

        self._table = table
        self.colormap = self._get_colormap()

        self._table_widget.clear()
        try:
            self._table_widget.setRowCount(len(next(iter(table.values()))))
            self._table_widget.setColumnCount(len(table))
        except StopIteration:
            pass

        for i, column in enumerate(table):
            self._table_widget.setHorizontalHeaderItem(i, QTableWidgetItem(column))
            for j, value in enumerate(table.get(column)):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self._table_widget.setItem(j, i, item)

        self._table_widget.setItemDelegate(FloatDelegate(3, self._table_widget))

        self._set_label_colors_to_rows()

    def _get_colormap(self) -> DirectLabelColormap:
        """Get a DirectLabelColormap that maps node ids to their track ids, and then
        uses the tracks_viewer.colormap to map from track_id to color.

        Returns:
            DirectLabelColormap: A map from node ids to colors based on track id
        """
        tracks = self.tracks_viewer.tracks
        if tracks is not None:
            nodes = list(tracks.graph.nodes())
            track_ids = [tracks.get_track_id(node) for node in nodes]
            colors = [self.tracks_viewer.colormap.map(tid) for tid in track_ids]
        else:
            nodes = []
            colors = []

        return DirectLabelColormap(
            color_dict={
                **dict(zip(nodes, colors, strict=True)),
                None: [0, 0, 0, 0],
            }
        )

    def _set_label_colors_to_rows(self) -> None:
        """Apply the colors of the napari label image to the table, and set the text color
         depending on luminance (black test on light backgrounds, white text on dark
        backgrounds)"""

        for i in range(self._table_widget.rowCount()):
            label = self._table["ID"][i]
            label_color = to_rgba(self.colormap.map(label))

            if label_color[3] == 0:
                label_color = [0, 0, 0, 0]

            r, g, b = (
                int(label_color[0] * 255),
                int(label_color[1] * 255),
                int(label_color[2] * 255),
            )

            qcolor = QColor(r, g, b)

            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            text_color = QColor(0, 0, 0) if luminance > 140 else QColor(255, 255, 255)

            for j in range(self._table_widget.columnCount()):
                item = self._table_widget.item(i, j)
                item.setBackground(qcolor)
                item.setForeground(text_color)

    def _update_label_colormap(self) -> None:
        """
        Highlight the labels of selected rows. Assumes the layer already has a
        DirectLabelColormap.
        """

        # in case of right-click on the table, we should only show the selected label(s)
        if len(self.special_selection) != 0:
            for _, color in self.colormap.color_dict.items():
                color[-1] = 0
            for key in self.special_selection:
                if key in self.colormap.color_dict:
                    self.colormap.color_dict[key][-1] = 1

        # find selected rows, and set highlight matching labels
        else:
            selected_rows = sorted(
                {index.row() for index in self._table_widget.selectedIndexes()}
            )
            if not selected_rows:
                self._reset_layer_colormap()
                return

            selected_labels = [self._table["ID"][row] for row in selected_rows]
            for key, color in self.colormap.color_dict.items():
                if key is not None and key != 0:
                    color[-1] = 0.6
            for key in selected_labels:
                if key in self.colormap.color_dict:
                    self.colormap.color_dict[key][-1] = 1

    def _sort_table(self, column_index: int) -> None:
        """Sorts the table in ascending or descending order

        Args:
            column_index (int): The index of the clicked column header
        """

        selected_column = list(self._table.keys())[column_index]
        df = pd.DataFrame(self._table).sort_values(
            by=selected_column, ascending=self.ascending
        )
        self.ascending = not self.ascending

        self.set_data(df)
        self._set_label_colors_to_rows()
