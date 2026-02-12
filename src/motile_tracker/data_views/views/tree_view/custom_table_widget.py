import numpy as np
import pandas as pd
from matplotlib.colors import to_rgba
from napari.utils import DirectLabelColormap
from qtpy.QtCore import (
    QEvent,
    QItemSelectionModel,
    QModelIndex,
    QObject,
    Qt,
    QTimer,
)
from qtpy.QtGui import QColor, QPen
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


class ClickToSingleSelectFilter(QObject):
    """Event filter to make plain left-clicks act like single selection
    while still allowing Ctrl/Shift clicks to behave normally (append/range)."""

    def __init__(self, table_widget):
        super().__init__(table_widget)
        self.table = table_widget

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            modifiers = event.modifiers()
            if not (modifiers & Qt.ShiftModifier):
                self.table.clearSelection()
            return False

        return False


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
    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid():
            ctrl = bool(event.modifiers() & Qt.ControlModifier)
            shift = bool(event.modifiers() & Qt.ShiftModifier)
            self.parent()._clicked_table(ctrl=ctrl, shift=shift, index=index)

            # Call super so selection behavior still works
            if ctrl:
                return

            if shift:
                row = index.row()
                self.selectRow(row)
                event.accept()
                return

            super().mousePressEvent(event)


class ColoredTableWidget(QWidget):
    """Customized table widget with colored rows based on label colors in a napari Labels layer"""

    def __init__(self, tracks_viewer: TracksViewer, df: pd.DataFrame):
        super().__init__()

        self.tracks_viewer = tracks_viewer
        self._table_widget = CustomTableWidget()
        self.special_selection = []

        self.set_data(df)

        self.ascending = False  # for choosing whether to sort ascending or descending

        # Connect to single click in the header to sort the table.
        self._table_widget.horizontalHeader().sectionClicked.connect(self._sort_table)

        # Instruction label to explain left and right mouse click.
        label = QLabel(
            "Use left mouse click to select and center a label. Use Ctrl/Meta to center a node, Shift to append to selection."
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

        self._click_filter = ClickToSingleSelectFilter(self._table_widget)
        self._table_widget.viewport().installEventFilter(self._click_filter)

        delegate = NoSelectionHighlightDelegate(self._table_widget)
        self._table_widget.setItemDelegate(delegate)

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

    def set_data(self, df: pd.DataFrame) -> None:
        """Set the content of the table from a dictionary"""

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

    def _set_label_colors_to_rows(self) -> None:
        """Apply the colors of the napari label image to the table"""

        for i in range(self._table_widget.rowCount()):
            label = self._table["node_id"][i]
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

    def _clicked_table(self, ctrl: bool, shift: bool, index: QModelIndex) -> None:
        """Center the viewer to clicked label. If the left mouse button was used,
        highlight the selected label(s) in layer. If the right mouse button was used, hide
        all other labels entirely by modifiying the colormap.
        The special selection behavior can be modified by the ctrl/meta key, to view
        multiple labels simultaneously.

        Args:
            shift (bool): shift key was used.
            ctrl (bool): ctrl/meta key was used.
            index (QModelIndex): index of the clicked row
        """
        row = index.row()
        label = self._table["node_id"][row]

        print("clicked table", ctrl, shift)
        if ctrl:
            self.tracks_viewer.center_on_node(label)
        else:
            self.tracks_viewer.selected_nodes.add(label, shift)

        QTimer.singleShot(0, self._update_label_colormap)

    def select_label(
        self, position: list[int | float], label: int, append: bool = False
    ) -> None:
        """Select the corresponding row of the label that was clicked on, and update the colormap.

        Args:
            position (list[int|float]): coordinates of the clicked location.
            label (int): the label value that was clicked on.
            append (bool): whether to append to selection (ctrl/meta modifier), or start
                a new selection
        """

        if label is None or label == 0:
            self._table_widget.clearSelection()
            self._reset_layer_colormap()
            return

        # t = None
        # c = None

        # if "time_point" in self._table:
        #     time_dim = self._layer.metadata["dimensions"].index("T")
        #     t = position[time_dim]

        # row = self._find_row(time_point=t, channel=c, label=label)
        # self._select_row(row, append)

        # self._update_label_colormap()

    def _select_row(self, row: int, append: bool) -> None:
        """Select a row visually in the table.
        Args:
            row (int): the to be selected row.
            append (bool): whether to append to the selection, or start a new selection.
        """

        if row is None:
            return

        model = self._table_widget.model()
        index = model.index(row, 0)

        selection_model = self._table_widget.selectionModel()

        if append:
            # Add row to existing selection (Ctrl/Meta click)
            selection_model.select(
                index,
                QItemSelectionModel.SelectionFlag.Select
                | QItemSelectionModel.SelectionFlag.Rows,
            )
        else:
            # Clear existing selection and select row (normal single selection)
            selection_model.clearSelection()
            selection_model.select(
                index,
                QItemSelectionModel.SelectionFlag.Select
                | QItemSelectionModel.SelectionFlag.Rows,
            )

        # Ensure the row is visible
        self._table_widget.scrollToItem(self._table_widget.item(row, 0))

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

    def _delete_labels(self) -> None:
        """Delete the selected labels in the table and store state for undo."""

        # let tracks_viewer handle this
        # selected_rows = sorted(
        #     {index.row() for index in self._table_widget.selectedIndexes()}
        # )
        # if not selected_rows:
        #     return

        # self._undo_info = []

        # # Delete labels from the table itself
        # for row in reversed(selected_rows):
        #     row_data = {col: self._table[col][row] for col in self._table}
        #     self._undo_info.append({"row": row, "row_data": row_data})
        #     for col in self._table:
        #         self._table[col] = np.delete(self._table[col], row, axis=0)
        #     self._table_widget.removeRow(row)

        # # Identify axes
        # dims = self._layer.metadata["dimensions"]
        # has_time = "time_point" in self._table
        # has_channel = "channel" in self._table
        # time_axis = dims.index("T") if has_time else None
        # channel_axis = dims.index("C") if has_channel else None

        # # Delete from layer.data
        # for info in self._undo_info:
        #     row_data = info["row_data"]
        #     sl = [slice(None)] * self._layer.data.ndim

        #     if has_time:
        #         sl[time_axis] = int(row_data["time_point"])
        #     if has_channel:
        #         sl[channel_axis] = int(row_data["channel"])

        #     # Extract the relevant slice
        #     sliced_data = self._layer.data[tuple(sl)]
        #     if isinstance(sliced_data, da.core.Array):
        #         sliced_data = sliced_data.compute()

        #     # store only the boolean mask positions affected by the label
        #     label = row_data["label"]
        #     mask = sliced_data == int(label)
        #     prev_values = sliced_data[mask].copy()

        #     info["slice"] = sl
        #     info["mask"] = mask
        #     info["prev_values"] = prev_values

        #     # Set label to 0
        #     sliced_data[mask] = 0

        #     # Assign back to layer
        #     self._layer.data[tuple(sl)] = sliced_data

        # # Enable undo button
        # self.undo_button.setEnabled(True)
        # self._layer.data = self._layer.data

    def _undo_delete(self) -> None:
        """Restore previously deleted labels and table rows."""

        # if not hasattr(self, "_undo_info") or not self._undo_info:
        #     return

        # # Sort by row ascending so insert indices stay correct
        # for info in sorted(self._undo_info, key=lambda x: x["row"]):
        #     row = info["row"]
        #     row_data = info["row_data"]

        #     # Restore table data
        #     for col in self._table:
        #         value_to_insert = np.array([row_data[col]])
        #         self._table[col] = np.insert(
        #             self._table[col], row, value_to_insert, axis=0
        #         )

        #     # Restore QTableWidget row visually
        #     self._table_widget.insertRow(row)
        #     for col_idx, col in enumerate(self._table):
        #         item = QTableWidgetItem(str(row_data[col]))
        #         self._table_widget.setItem(row, col_idx, item)

        #     # Restore layer.data for this slice
        #     sl = info.get("slice")
        #     if sl is not None:
        #         sliced_data = self._layer.data[tuple(sl)]
        #         if isinstance(sliced_data, da.core.Array):
        #             sliced_data = sliced_data.compute()
        #         sliced_data[info["mask"]] = info["prev_values"]
        #         self._layer.data[tuple(sl)] = sliced_data
        #     else:
        #         # global volume undo
        #         self._layer.data[info["mask"]] = info["prev_values"]

        # # Clear undo info and disable button
        # self._undo_info = []
        # self.undo_button.setEnabled(False)

        # # refresh
        # self._layer.data = self._layer.data

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

            selected_labels = [self._table["node_id"][row] for row in selected_rows]
            for key, color in self.colormap.color_dict.items():
                if key is not None and key != 0:
                    color[-1] = 0.6
            for key in selected_labels:
                if key in self.colormap.color_dict:
                    self.colormap.color_dict[key][-1] = 1

    def _reset_layer_colormap(self) -> None:
        """Set all alpha values back to 1 to reset the colormap, and empty the special
        selection."""

        # self.special_selection = []
        # if self._layer is not None:
        #     for key in self._layer.colormap.color_dict:
        #         if key is not None and key != 0:
        #             self._layer.colormap.color_dict[key][-1] = 1
        #     self._layer.colormap = DirectLabelColormap(
        #         color_dict=self._layer.colormap.color_dict
        #     )

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
