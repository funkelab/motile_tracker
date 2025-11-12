from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fonticon_fa6 import FA6S
from funtracks.features._feature import Feature
from funtracks.import_export.export_to_geff import export_to_geff
from napari._qt.qt_resources import QColoredSVGIcon
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from superqt.fonticon import icon as qticon

if TYPE_CHECKING:
    from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer


class CollectionButton(QWidget):
    """Widget holding a name and delete icon for listing in the QListWidget. Also contains
    an initially empty instance of a Collection to which nodes can be assigned"""

    def __init__(self, name: str):
        super().__init__()
        self.name = QLabel(name)
        self.name.setFixedHeight(20)
        self.collection = set()
        delete_icon = QColoredSVGIcon.from_resources("delete").colored("white")
        self.node_count = QLabel(f"{len(self.collection)} nodes")

        export_icon = qticon(FA6S.file_export, color="white")
        self.export = QPushButton(icon=export_icon)
        self.export.setFixedSize(20, 20)
        self.export.setToolTip("Export nodes in this group to CSV or geff")

        self.delete = QPushButton(icon=delete_icon)
        self.delete.setFixedSize(20, 20)
        layout = QHBoxLayout()
        layout.setSpacing(1)
        layout.addWidget(self.name)
        layout.addWidget(self.node_count)
        layout.addWidget(self.export)
        layout.addWidget(self.delete)
        layout.setSpacing(10)

        self.setLayout(layout)

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(30)
        return hint

    def update_node_count(self):
        self.node_count.setText(f"{len(self.collection)} nodes")


class CollectionWidget(QWidget):
    """Widget for holding in-memory Collections (groups). Emits a signal whenever
    a collection is selected in the list, to update the viewing properties
    """

    group_changed = Signal()

    def __init__(self, tracks_viewer: TracksViewer):
        super().__init__()

        self.tracks_viewer = tracks_viewer
        self.tracks_viewer.selected_nodes.list_updated.connect(
            self._update_buttons_and_node_count
        )

        self.group_changed.connect(self._update_buttons_and_node_count)

        self.collection_list = QListWidget()
        self.collection_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.collection_list.itemSelectionChanged.connect(self._selection_changed)
        self.selected_collection = None

        # Select widget group
        select_widget = QGroupBox("Selection")
        selection_layout = QVBoxLayout()

        row1_layout = QHBoxLayout()
        self.select_btn = QPushButton("Select nodes in group")
        self.select_btn.clicked.connect(self._select_nodes)
        self.invert_btn = QPushButton("Invert selection")
        self.invert_btn.clicked.connect(self._invert_selection)
        row1_layout.addWidget(self.select_btn)
        row1_layout.addWidget(self.invert_btn)

        row2_layout = QHBoxLayout()
        self.deselect_btn = QPushButton("Deselect")
        self.deselect_btn.clicked.connect(self.tracks_viewer.selected_nodes.reset)
        self.reselect_btn = QPushButton("Restore selection")
        self.reselect_btn.clicked.connect(self.tracks_viewer.selected_nodes.restore)
        row2_layout.addWidget(self.deselect_btn)
        row2_layout.addWidget(self.reselect_btn)

        selection_layout.addLayout(row1_layout)
        selection_layout.addLayout(row2_layout)
        select_widget.setLayout(selection_layout)

        # edit layout
        edit_widget = QGroupBox("Edit group")
        edit_layout = QVBoxLayout()

        add_layout = QHBoxLayout()
        self.add_nodes_btn = QPushButton("Add node(s)")
        self.add_nodes_btn.clicked.connect(self._add_selection)
        self.add_track_btn = QPushButton("Add track(s)")
        self.add_track_btn.clicked.connect(lambda: self._add_track(add=True))
        self.add_lineage_btn = QPushButton("Add lineage(s)")
        self.add_lineage_btn.clicked.connect(lambda: self._add_lineage(add=True))
        add_layout.addWidget(self.add_nodes_btn)
        add_layout.addWidget(self.add_track_btn)
        add_layout.addWidget(self.add_lineage_btn)

        remove_layout = QHBoxLayout()
        self.remove_node_btn = QPushButton("Remove node(s)")
        self.remove_node_btn.clicked.connect(self._remove_selection)
        self.remove_track_btn = QPushButton("Remove track(s)")
        self.remove_track_btn.clicked.connect(lambda: self._add_track(add=False))
        self.remove_lineage_btn = QPushButton("Remove lineage(s)")
        self.remove_lineage_btn.clicked.connect(lambda: self._add_lineage(add=False))
        remove_layout.addWidget(self.remove_node_btn)
        remove_layout.addWidget(self.remove_track_btn)
        remove_layout.addWidget(self.remove_lineage_btn)

        edit_layout.addLayout(add_layout)
        edit_layout.addLayout(remove_layout)
        edit_widget.setLayout(edit_layout)

        # adding a new group
        new_group_box = QGroupBox("New Group")
        new_group_layout = QHBoxLayout()
        self.group_name = QLineEdit("new group")
        new_group_layout.addWidget(self.group_name)
        self.new_group_button = QPushButton("Create")
        self.new_group_button.clicked.connect(
            lambda: self._add_group(name=None, select=True)
        )
        new_group_layout.addWidget(self.new_group_button)
        new_group_box.setLayout(new_group_layout)

        # combine widgets
        layout = QVBoxLayout()
        layout.addWidget(self.collection_list)
        layout.addWidget(select_widget)
        layout.addWidget(edit_widget)
        layout.addWidget(new_group_box)
        self.setLayout(layout)

        self._update_buttons_and_node_count()

    def _update_buttons_and_node_count(self) -> None:
        """Enable or disable selection and edit buttons depending on whether a group is
        selected, nodes are selected, and whether the group contains any nodes"""

        selected = self.collection_list.selectedItems()
        if selected and len(self.tracks_viewer.selected_nodes) > 0:
            self.add_nodes_btn.setEnabled(True)
            self.add_track_btn.setEnabled(True)
            self.add_lineage_btn.setEnabled(True)
            self.remove_node_btn.setEnabled(True)
            self.remove_track_btn.setEnabled(True)
            self.remove_lineage_btn.setEnabled(True)
        else:
            self.add_nodes_btn.setEnabled(False)
            self.add_track_btn.setEnabled(False)
            self.add_lineage_btn.setEnabled(False)
            self.remove_node_btn.setEnabled(False)
            self.remove_track_btn.setEnabled(False)
            self.remove_lineage_btn.setEnabled(False)
            self.select_btn.setEnabled(False)

        if selected:
            self.collection_list.itemWidget(
                selected[0]
            ).update_node_count()  # update the node count

            if len(self.selected_collection.collection) > 0:
                self.select_btn.setEnabled(True)
            else:
                self.select_btn.setEnabled(False)

        if len(self.tracks_viewer.selected_nodes) > 0:
            self.deselect_btn.setEnabled(True)
        else:
            self.deselect_btn.setEnabled(False)

        if self.tracks_viewer.tracks is not None:
            self.new_group_button.setEnabled(True)
        else:
            self.new_group_button.setEnabled(False)

    def _invert_selection(self) -> None:
        """Invert the current selection"""

        all_nodes = set(self.tracks_viewer.tracks.graph.nodes)
        inverted = list(all_nodes - set(self.tracks_viewer.selected_nodes))
        self.tracks_viewer.selected_nodes.add_list(inverted, append=False)

    def _refresh(self) -> None:
        """Keep the node collection in sync with the node group attributes on the graph"""

        # TODO Currently, this function only removes nodes that no longer exist in the
        # graph. When undoing an action, a node can be put back in the graph, but in the
        # current state it is not added back to the collection.

        items = [
            self.collection_list.itemWidget(self.collection_list.item(i))
            for i in range(self.collection_list.count())
        ]
        for item in items:
            nodes = item.collection
            graph_nodes = set(self.tracks_viewer.tracks.graph.nodes)
            item.collection = {item for item in nodes if item in graph_nodes}
            item.update_node_count()

    def _select_nodes(self) -> None:
        """Select all nodes in the collection"""

        selected = self.collection_list.selectedItems()
        if selected:
            self.selected_collection = self.collection_list.itemWidget(selected[0])
            self.tracks_viewer.selected_nodes.add_list(
                list(self.selected_collection.collection), append=False
            )

    def retrieve_existing_groups(self) -> None:
        """Create collections based on the node attributes. Nodes assigned to a group
        should have that group in their 'group' attribute"""

        # first clear the entire list
        self.collection_list.clear()

        # find existing group features on Tracks
        group_features = [
            (group_name, group_dict)
            for group_name, group_dict in self.tracks_viewer.tracks.features.items()
            if group_dict["value_type"] == "bool"
        ]
        group_dict = {}
        for group_name, _ in group_features:
            if group_name not in group_dict:
                nodes = [
                    node
                    for node in self.tracks_viewer.tracks.nodes()
                    if self.tracks_viewer.tracks.get_node_attr(node, group_name)
                ]
                group_dict[group_name] = nodes
                self._add_group(name=group_name, select=True)
                self.selected_collection.collection = set(group_dict[group_name])
                self.selected_collection.update_node_count()  # update node count

        self._update_buttons_and_node_count()

    def _selection_changed(self) -> None:
        """Update the currently selected collection and send update signal"""

        selected = self.collection_list.selectedItems()
        if selected:
            self.selected_collection = self.collection_list.itemWidget(selected[0])
            self.group_changed.emit()

        self._update_buttons_and_node_count()

    def _add_nodes(self, nodes: list[Any] | None = None) -> None:
        """Add individual nodes to the selected collection and send update signal

        Args:
            nodes (list, optional): A list of nodes to add to this group. If not provided,
            the nodes are taken from the current selection in tracks_viewer.selected_nodes
        """

        if self.selected_collection is not None:
            self.selected_collection.collection = (
                self.selected_collection.collection | set(nodes)
            )

            # Use UpdateNodeAttrs to set the feature value to True
            feature_key = self.selected_collection.name.text()
            attrs = {feature_key: [True for _ in nodes]}
            self.tracks_viewer.tracks_controller.update_node_attrs(nodes, attrs)

            self.group_changed.emit()

    def _add_selection(self) -> None:
        """Add the currently selected node(s) to the collection"""

        self._add_nodes(self.tracks_viewer.selected_nodes.as_list)

    def _add_track(self, add: bool = True) -> None:
        """Adds or removes the tracks belonging to selected nodes to the selected
        collection.

        Args:
            add (bool=True): when True, will add the nodes to the collection, when False,
            it will remove them.
        """

        selected = set(self.tracks_viewer.selected_nodes)
        nodes_to_process = []

        while selected:
            node_id = selected.pop()
            track_id = self.tracks_viewer.tracks.get_track_id(node_id)
            track = self.tracks_viewer.tracks.track_annotator.tracklet_id_to_nodes[
                track_id
            ]
            nodes_to_process.extend(track)
            selected.difference_update(track)

        self._add_nodes(nodes_to_process) if add else self._remove_nodes(
            nodes_to_process
        )

    def _add_lineage(self, add: bool = True) -> None:
        """Add or remove lineages to/from the selected collection
        Args:
            add (bool=True): when True, will add the nodes to the collection, when False,
            it will remove them.
        """

        selected = set(self.tracks_viewer.selected_nodes)
        nodes_to_process = []

        while selected:
            node_id = selected.pop()
            lineage_key = self.tracks_viewer.tracks.track_annotator.lineage_key
            lineage_id = self.tracks_viewer.tracks.get_node_attr(node_id, lineage_key)
            lineage = self.tracks_viewer.tracks.track_annotator.lineage_id_to_nodes[
                lineage_id
            ]
            nodes_to_process.extend(lineage)
            selected.difference_update(lineage)
        self._add_nodes(nodes_to_process) if add else self._remove_nodes(
            nodes_to_process
        )

    def _remove_nodes(self, nodes: list[Any]) -> None:
        """Remove selected nodes from the selected collection"""

        if self.selected_collection is not None:
            # remove from the collection
            self.selected_collection.collection = {
                item
                for item in self.selected_collection.collection
                if item not in nodes
            }

            feature_key = self.selected_collection.name.text()
            attrs = {feature_key: [False for _ in nodes]}
            self.tracks_viewer.tracks_controller.update_node_attrs(nodes, attrs)

            self.group_changed.emit()

    def _remove_selection(self) -> None:
        """Remove individual nodes from the selected collection"""

        self._remove_nodes(self.tracks_viewer.selected_nodes)

    def _add_group(self, name: str | None = None, select: bool = True) -> None:
        """Create a new custom group

        Args:
            name (str, optional): the name to give to this group. If not provided, the
                name in the self.group_name QLineEdit widget is used.
            select (bool, optional): whether or not to make this group the selected item
                in the QListWidget. Defaults to True.
        """

        if name is None:
            name = self.group_name.text()

        names = [
            self.collection_list.itemWidget(self.collection_list.item(i)).name.text()
            for i in range(self.collection_list.count())
        ]
        while name in names:
            name = name + "_1"
        item = QListWidgetItem(self.collection_list)
        group_row = CollectionButton(name)
        self.collection_list.setItemWidget(item, group_row)
        item.setSizeHint(group_row.minimumSizeHint())
        self.collection_list.addItem(item)
        group_row.delete.clicked.connect(partial(self._remove_group, item))
        group_row.export.clicked.connect(partial(self._show_export_dialog, item))

        if select:
            self.collection_list.setCurrentRow(len(self.collection_list) - 1)

        # Register group as new feature on Tracks
        if name not in self.tracks_viewer.tracks.features:
            new_feature_key = name
            new_feature: Feature = {
                "feature_type": "node",  # This is a node feature
                "value_type": "bool",  # The feature is a boolean
                "num_values": 1,  # Each node has one value for this feature
                "display_name": name,
                "required": False,  # The feature is not required
                "default_value": False,  # Default value for nodes without this feature
            }

            # Add the new feature to the FeatureDict of the Tracks instance
            self.tracks_viewer.tracks.features[new_feature_key] = new_feature

    def _remove_group(self, item: QListWidgetItem) -> None:
        """Remove a collection object from the list. You must pass the list item that
        represents the collection, not the collection object itself.

        Args:
            item (QListWidgetItem): The list item to remove. This list item
                contains the CollectionButton that represents a set of node_ids.
        """

        row = self.collection_list.indexFromItem(item).row()
        group_name = self.collection_list.itemWidget(item).name.text()
        self.collection_list.takeItem(row)

        # remove from the features on Tracks
        del self.tracks_viewer.tracks.features[group_name]

    def _show_export_dialog(self, item: QListWidgetItem) -> None:
        """Prompt user to choose export format (csv or geff), then export the nodes
         belonging to this group.
        You must pass the list item that represents the group.

        Args:
            item (QListWidgetItem):  The list item containing the CollectionButton that
                represents a group of nodes.

        """

        group_name = self.collection_list.itemWidget(item).name.text()

        export_type, ok = QInputDialog.getItem(
            self,
            "Select Export Type",
            (
                f"<p style='white-space: normal;'>"
                f"<i>Export all nodes in group </i>"
                f"<span style='color: green;'><b>{group_name}.</b></span><br>"
                f"<i>Note that ancestors will also be included to maintain a valid graph.</i>"
                f"</p>"
                f"<p>Choose export format:</p>"
            ),
            ["CSV", "geff"],
            0,
            False,
        )

        if not ok:
            return

        # Keep nodes that belong to the selected group
        nodes_to_keep = self.collection_list.itemWidget(item).collection

        if export_type == "CSV":
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.AnyFile)
            file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            file_dialog.setNameFilter("CSV files (*.csv)")
            file_dialog.setDefaultSuffix("csv")
            default_file = f"{group_name}_tracks.csv"
            base_path = Path(file_dialog.directory().path())
            file_dialog.selectFile(str(base_path / default_file))

            if file_dialog.exec_():
                file_path = Path(file_dialog.selectedFiles()[0])
                self.tracks_viewer.tracks.export_tracks(file_path, nodes_to_keep)

        elif export_type == "geff":
            default_file = f"{group_name}_geff.zarr"

            file_dialog = QFileDialog(self, "Save as geff file")
            file_dialog.setFileMode(QFileDialog.AnyFile)
            file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            file_dialog.setNameFilter("Zarr folder (*.zarr)")
            file_dialog.setDefaultSuffix("zarr")

            # Set default selected file
            base_path = Path.home()
            file_dialog.selectFile(str(base_path / default_file))

            if file_dialog.exec_():
                file_path = Path(file_dialog.selectedFiles()[0])
                try:
                    export_to_geff(
                        self.tracks_viewer.tracks,
                        file_path,
                        overwrite=True,
                        node_ids=nodes_to_keep,
                    )  # QFileDialog
                    # already asks whether to overwrite in an existing directory
                except ValueError as e:
                    QMessageBox.warning(self, "Export Error", str(e))
