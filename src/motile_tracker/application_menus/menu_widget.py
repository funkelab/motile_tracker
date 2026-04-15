import napari
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from motile_tracker.application_menus.editing_menu import EditingMenu
from motile_tracker.application_menus.selection_menu import SelectionWidget
from motile_tracker.application_menus.visualization_widget import (
    LabelVisualizationWidget,
)
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_tracker.motile.menus.motile_widget import MotileWidget

DOCS_URL = "https://funkelab.github.io/motile_tracker"
KEYBINDINGS_URL = f"{DOCS_URL}/key_bindings.html"


class MenuWidget(QScrollArea):
    """Combines the different tracker menus into tabs for cleaner UI"""

    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.tracks_viewer = TracksViewer.get_instance(viewer)
        self.tracks_viewer.tracks_updated.connect(self._toggle_visualization_widget)

        motile_widget = MotileWidget(viewer)

        editing_widget = EditingMenu(viewer)
        selection_widget = SelectionWidget(self.tracks_viewer)
        selection_editing_widget = QWidget()
        selection_editing_layout = QVBoxLayout()
        selection_editing_layout.addWidget(editing_widget)
        selection_editing_layout.addWidget(selection_widget)
        selection_editing_layout.setContentsMargins(0, 0, 0, 0)
        selection_editing_widget.setLayout(selection_editing_layout)
        selection_editing_widget.setMaximumHeight(600)

        self.visualization_widget = LabelVisualizationWidget(viewer)
        self._visualization_index = 3

        self.tabwidget = QTabWidget()

        self.tabwidget.addTab(motile_widget, "Tracking")
        self.tabwidget.addTab(self.tracks_viewer.tracks_list, "Tracks List")
        self.tabwidget.addTab(selection_editing_widget, "Editing && Selection")
        self.tabwidget.addTab(self.tracks_viewer.collection_widget, "Groups")

        # Header with title and help links
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 0)
        header_label = QLabel(
            f"<b>Motile Tracker</b> · "
            f'<a href="{DOCS_URL}"><font color=yellow>Docs</font></a> · '
            f'<a href="{KEYBINDINGS_URL}"><font color=yellow>Keybindings</font></a>'
        )
        header_label.setOpenExternalLinks(True)
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Container widget with header + tabs
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)
        container_layout.addLayout(header_layout)
        container_layout.addWidget(self.tabwidget)
        container.setLayout(container_layout)

        self.setWidget(container)
        self.setWidgetResizable(True)

    def _has_visualization_tab(self):
        return self.tabwidget.indexOf(self.visualization_widget) != -1

    def _toggle_visualization_widget(self):
        """Only show the visualization tab when we have a TracksLabels layer"""

        has_seg = self.tracks_viewer.tracking_layers.seg_layer is not None
        has_tab = self._has_visualization_tab()

        if has_seg and not has_tab:
            index = self._visualization_index
            self.tabwidget.insertTab(index, self.visualization_widget, "Visualization")

        elif not has_seg and has_tab:
            self._visualization_index = self.tabwidget.indexOf(
                self.visualization_widget
            )
            self.tabwidget.removeTab(self._visualization_index)
