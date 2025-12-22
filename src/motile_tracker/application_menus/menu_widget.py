import napari
from qtpy.QtWidgets import QScrollArea, QTabWidget, QVBoxLayout

from motile_tracker.application_menus.editing_menu import EditingMenu
from motile_tracker.application_menus.visualization_widget import (
    LabelVisualizationWidget,
)
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_tracker.motile.menus.motile_widget import MotileWidget


class MenuWidget(QScrollArea):
    """Combines the different tracker menus into tabs for cleaner UI"""

    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.tracks_viewer = TracksViewer.get_instance(viewer)
        self.tracks_viewer.tracks_updated.connect(self._toggle_visualization_widget)

        motile_widget = MotileWidget(viewer)
        editing_widget = EditingMenu(viewer)
        self.visualization_widget = LabelVisualizationWidget(viewer)
        self._visualization_index = 3

        self.tabwidget = QTabWidget()

        self.tabwidget.addTab(motile_widget, "Track with Motile")
        self.tabwidget.addTab(self.tracks_viewer.tracks_list, "Tracks List")
        self.tabwidget.addTab(editing_widget, "Edit Tracks")
        self.tabwidget.addTab(self.tracks_viewer.collection_widget, "Groups")

        layout = QVBoxLayout()
        layout.addWidget(self.tabwidget)

        self.setWidget(self.tabwidget)
        self.setWidgetResizable(True)

        self.setLayout(layout)

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
