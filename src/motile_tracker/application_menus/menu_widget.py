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
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer
from motile_tracker.motile.menus.motile_widget import MotileWidget

DOCS_URL = "https://funkelab.github.io/motile_tracker"
KEYBINDINGS_URL = f"{DOCS_URL}/key_bindings.html"


class MenuWidget(QScrollArea):
    """Combines the different tracker menus into tabs for cleaner UI"""

    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        tracks_viewer = TracksViewer.get_instance(viewer)

        motile_widget = MotileWidget(viewer)
        editing_widget = EditingMenu(viewer)

        self.tabwidget = QTabWidget()

        self.tabwidget.addTab(motile_widget, "Tracking")
        self.tabwidget.addTab(tracks_viewer.tracks_list, "Tracks List")
        self.tabwidget.addTab(editing_widget, "Edit Tracks")
        self.tabwidget.addTab(tracks_viewer.collection_widget, "Groups")

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
