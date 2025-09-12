import napari
from qtpy.QtWidgets import (
    QVBoxLayout,
    QWidget,
)

from motile_tracker.data_views.views.layers.track_labels import TrackLabels
from motile_tracker.data_views.views.layers.track_points import TrackPoints
from motile_tracker.data_views.views.ortho_views import (
    _get_manager,
    paint_event_hook,
    point_data_hook,
    sync_filters,
    track_layers_hook,
)
from motile_tracker.data_views.views.tree_view.tree_widget import TreeWidget

from .menu_widget import MenuWidget


class MainApp(QWidget):
    """Combines the different tracker widgets for faster dock arrangement"""

    def __init__(self, viewer: napari.Viewer):
        super().__init__()

        self.menu_widget = MenuWidget(viewer)
        tree_widget = TreeWidget(viewer)

        viewer.window.add_dock_widget(tree_widget, area="bottom", name="Tree View")

        layout = QVBoxLayout()
        layout.addWidget(self.menu_widget)

        orth_view_manager = _get_manager(viewer)
        orth_view_manager.register_layer_hook(
            (TrackLabels, TrackPoints), track_layers_hook
        )
        orth_view_manager.register_layer_hook((TrackLabels), paint_event_hook)
        orth_view_manager.register_layer_hook((TrackPoints), point_data_hook)
        orth_view_manager.set_sync_filters(sync_filters)

        self.setLayout(layout)
