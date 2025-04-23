import napari
from qtpy.QtWidgets import QScrollArea, QTabWidget, QVBoxLayout

from motile_tracker.application_menus.editing_menu import EditingMenu
from motile_tracker.data_views.views.view_3d import View3D
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_tracker.motile.menus.motile_widget import MotileWidget


class MenuWidget(QScrollArea):
    """Combines the different tracker menus into tabs for cleaner UI"""

    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.viewer = viewer
        tracks_viewer = TracksViewer.get_instance(viewer)

        motile_widget = MotileWidget(viewer)
        editing_widget = EditingMenu(viewer)
        view3D_widget = View3D(viewer)
        view3D_widget.update_tab.connect(self.update_3D_tab)

        self.tabwidget = QTabWidget()

        self.tabwidget.addTab(view3D_widget, "3D viewing")
        self.tabwidget.addTab(motile_widget, "Track with Motile")
        self.tabwidget.addTab(editing_widget, "Edit Tracks")
        self.tabwidget.addTab(tracks_viewer.tracks_list, "Results List")
        self.tabwidget.addTab(tracks_viewer.collection_widget, "Collections")

        layout = QVBoxLayout()
        layout.addWidget(self.tabwidget)

        self.setWidget(self.tabwidget)
        self.setWidgetResizable(True)

        self.setLayout(layout)
        self.setMinimumWidth(300)

    def update_3D_tab(self):
        if self.tabwidget.currentIndex() == 0:
            self.tabwidget.setCurrentIndex(1)
            self.tabwidget.setCurrentIndex(0)
