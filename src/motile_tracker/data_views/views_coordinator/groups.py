from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from funtracks.features._feature import Feature
from napari._qt.qt_resources import QColoredSVGIcon
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.data_views.views.tree_view.tree_widget_utils import (
    extract_lineage_tree,
)

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
        self.delete = QPushButton(icon=delete_icon)
        self.delete.setFixedSize(20, 20)
        layout = QHBoxLayout()
        layout.setSpacing(1)
        layout.addWidget(self.name)
        layout.addWidget(self.node_count)
        layout.addWidget(self.delete)
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
        edit_widget = QGroupBox("Edit")
        edit_layout = QVBoxLayout()

        add_layout = QHBoxLayout()
        self.add_nodes_btn = QPushButton("Add node(s)")
        self.add_nodes_btn.clicked.connect(self._add_selection)
        self.add_track_btn = QPushButton("Add track(s)")
        self.add_track_btn.clicked.connect(self._add_track)
        self.add_lineage_btn = QPushButton("Add lineage(s)")
        self.add_lineage_btn.clicked.connect(self._add_lineage)
        add_layout.addWidget(self.add_nodes_btn)
        add_layout.addWidget(self.add_track_btn)
        add_layout.addWidget(self.add_lineage_btn)

        remove_layout = QHBoxLayout()
        self.remove_node_btn = QPushButton("Remove node(s)")
        self.remove_node_btn.clicked.connect(self._remove_selection)
        self.remove_track_btn = QPushButton("Remove track(s)")
        self.remove_track_btn.clicked.connect(self._remove_track)
        self.remove_lineage_btn = QPushButton("Remove lineage(s)")
        self.remove_lineage_btn.clicked.connect(self._remove_lineage)
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
            lambda: self.add_group(name=None, select=True)
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

        nodes = [
            node
            for node in self.tracks_viewer.tracks.graph.nodes
            if node not in self.tracks_viewer.selected_nodes
        ]
        self.tracks_viewer.selected_nodes.add_list(nodes, append=False)

    def _refresh(self) -> None:
        """Removes nodes that are no longer existing from the collection"""

        selected = self.collection_list.selectedItems()
        if selected:
            self.selected_collection = self.collection_list.itemWidget(selected[0])
            nodes = self.selected_collection.collection
            graph_nodes = set(self.tracks_viewer.tracks.graph.nodes)
            self.selected_collection.collection = {
                item for item in nodes if item in graph_nodes
            }
            self.selected_collection.update_node_count()

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
            if group_dict["is_group"]
        ]
        print("these are the existing group features on tracks", group_features)
        group_dict = {}
        for group_name, _ in group_features:
            if group_name not in group_dict:
                nodes = [
                    node
                    for node in self.tracks_viewer.tracks.nodes()
                    if self.tracks_viewer.tracks.get_node_attr(node, group_name)
                ]
                print("these nodes are in group", group_name, nodes)
                group_dict[group_name] = nodes
                self.add_group(name=group_name, select=True)
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

    def add_nodes(self, nodes: list[Any] | None = None) -> None:
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

        self.add_nodes(self.tracks_viewer.selected_nodes._list)

    def _add_track(self) -> None:
        """Add the tracks belonging to selected nodes to the selected collection"""

        track_ids = []
        for node_id in self.tracks_viewer.selected_nodes:
            track_id = self.tracks_viewer.tracks.get_track_id(node_id)
            if track_id in track_ids:
                continue  # skip, since we already added all nodes with this track id
            else:
                track = list(
                    {
                        node
                        for node, data in self.tracks_viewer.tracks.graph.nodes(
                            data=True
                        )
                        if data.get("track_id") == track_id
                    }
                )
                self.add_nodes(track)
                track_ids.append(track_id)

    def _add_lineage(self) -> None:
        """Add lineages to the selected collection"""

        track_ids = []
        for node_id in self.tracks_viewer.selected_nodes:
            track_id = self.tracks_viewer.tracks.get_track_id(node_id)
            if track_id in track_ids:
                continue  # skip, since we already added all nodes with this track id
            else:
                lineage = extract_lineage_tree(self.tracks_viewer.tracks.graph, node_id)
                track_ids.append(track_id)
            self.add_nodes(lineage)

    def remove_nodes(self, nodes: list[Any]) -> None:
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

        self.remove_nodes(self.tracks_viewer.selected_nodes)

    def _remove_track(self) -> None:
        """Remove tracks by track id from the selected collection"""

        track_ids = []
        for node_id in self.tracks_viewer.selected_nodes:
            track_id = self.tracks_viewer.tracks.get_track_id(node_id)
            if track_id in track_ids:
                continue
            else:
                track = list(
                    {
                        node
                        for node, data in self.tracks_viewer.tracks.graph.nodes(
                            data=True
                        )
                        if data.get("track_id") == track_id
                    }
                )
                self.remove_nodes(track)
                track_ids.append(track_id)

    def _remove_lineage(self) -> None:
        """Remove lineages from the selected collection"""

        track_ids = []
        for node_id in self.tracks_viewer.selected_nodes:
            track_id = self.tracks_viewer.tracks.get_track_id(node_id)
            if track_id in track_ids:
                continue
            else:
                lineage = extract_lineage_tree(self.tracks_viewer.tracks.graph, node_id)
                self.remove_nodes(lineage)
                track_ids.append(track_id)

    def add_group(self, name: str | None = None, select: bool = True) -> None:
        """Create a new custom group

        Args:
            name (str, optional): the name to give to this group. If not provided, the
                name in the self.group_name QLineEdit widget is used.
            select (bool, optional): whether or not to make this group the selected item
                in the QListWidget. Defaults to True.
        """

        print("adding new group!", name)
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
        if select:
            self.collection_list.setCurrentRow(len(self.collection_list) - 1)

        print("new row should have been added")

        # Register group as new feature on Tracks
        if name not in self.tracks_viewer.tracks.features:
            print("adding this group feature to Tracks", name)
            new_feature_key = name
            new_feature: Feature = {
                "feature_type": "node",  # This is a node feature
                "value_type": "bool",  # The feature is a boolean
                "num_values": 1,  # Each node has one value for this feature
                "display_name": name,
                "required": False,  # The feature is not required
                "default_value": False,  # Default value for nodes without this feature
                "is_group": True,
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

        print("removed this group", group_name)
