import inspect
import time

import napari_orthogonal_views.ortho_view_widget as ov_widget
from napari.layers import Labels, Layer, Points, Shapes
from napari.utils.events import Event
from napari.utils.notifications import show_info
from napari_orthogonal_views.ortho_view_manager import _get_manager  # noqa

from motile_tracker.data_views.views.layers.track_graph import TrackGraph
from motile_tracker.data_views.views.layers.track_labels import TrackLabels
from motile_tracker.data_views.views.layers.track_points import TrackPoints


# redefinition of copy_layer function
def copy_layer(layer: Layer, name: str = ""):
    if isinstance(
        layer, TrackGraph
    ):  # instead of showing the tracks (not very useful on 3D data because they are
        # collapsed to a single frame), use an empty shapes layer as substitute to ensure
        # that the layer indices in the orthogonal viewer models match with those in the
        # main viewer
        res_layer = Shapes(
            name=layer.name,
            data=[],
        )

    elif isinstance(layer, TrackLabels):
        res_layer = Labels(
            data=layer.data,
            name=layer.name,
            opacity=layer.opacity,
            scale=layer.scale,
            colormap=layer.colormap,
        )

    elif isinstance(layer, TrackPoints):
        res_layer = Points(
            data=layer.data,
            name=layer.name,
            symbol=layer.symbol,
            face_color=layer.face_color,
            size=layer.size,
            properties=layer.properties,
            border_color=layer.border_color,
            scale=layer.scale,
            blending="translucent_no_depth",
        )
    else:
        res_layer = Layer.create(*layer.as_layer_data_tuple())

    res_layer.metadata["viewer_name"] = name
    return res_layer


ov_widget.copy_layer = copy_layer  # replace the copy layer with the customized version
# defined here

# Define custom sync_filters. By default, all properties are synced forwards and backwards
# between the original layer and its derived copy. However, for Tracks Layers we need
# finer control over some syncing events, because they may have additional attached events
# that shouldn't be triggered due to reverse syncing, or because we need to capture the
# event and process it separately before it gets synced. A dictionary can be defined here
# to disable specific Layer properties for forward or reverse syncing.


def get_property_names_from_class(layer_cls):
    """Return all property names for a Layer class."""
    res = []
    for name, obj in inspect.getmembers(layer_cls):
        # must be a property with a setter
        if isinstance(obj, property) and obj.fset is not None:
            # skip special or non-sync properties
            if name in ("thumbnail", "name"):
                continue
            res.append(name)
    return res


sync_filters = {
    TrackGraph: {
        "forward_exclude": "*",  # disable all forward sync (layer is not shown)
        "reverse_exclude": "*",  # disable all reverse sync
    },
    TrackPoints: {
        "forward_exclude": {
            "data"
        },  # we will sync data separately on TrackPoints as we
        # need finer control
        "reverse_exclude": set(get_property_names_from_class(Points)) - {"mode"},
    },
    TrackLabels: {
        "reverse_exclude": set(get_property_names_from_class(Labels))
        - {
            "mode",
            "selected_label",
            "n_edit_dimensions",
            "brush_size",
        }  # Let TrackLabels handle these properties on its own because it is listening to
        # them and we do not want to overwrite through reverse syncing.
    },
}


# Define special functions to allow specific behavior on special layer types (TrackLabels,
# and TrackPoints)
#
def point_data_hook(orig_layer: TrackPoints, copied_layer: Points) -> None:
    """Hook to connect to sync points data and visualization between original and copied
    Points layers.

    Args:
        orig_layer (TrackPoints): TracksLabels layer from which the copied layer is
            derived.
        copied_layer (Points): Points equivalent of the TracksPoints layer.
    """

    # Sync the shown points and their size, as it is not synced by default. We bind to the
    # border_color event as this this is emitted when we modify shown points and point
    # size on the TrackPoints layer.
    def sync_shown_points(orig_layer: TrackPoints, copied_layer: Points) -> None:
        """Sync the visible points between original TrackPoints layer and Points layers
        in ViewerModel instances (this is not a synced property)"""

        with copied_layer.events.blocker_all():
            copied_layer.size = orig_layer.size
            copied_layer.shown = orig_layer.shown

        copied_layer.refresh()

    def shown_points_wrapper(event):
        return sync_shown_points(orig_layer, copied_layer)

    orig_layer.events.border_color.connect(shown_points_wrapper)

    # Receive data updates from the original layer
    def receive_data(orig_layer: TrackPoints, copied_layer: Points) -> None:
        """Respond to signal from the original layer, to update the data"""

        copied_layer.events.data.disconnect(copied_layer._sync_data_wrapper)
        copied_layer.data = orig_layer.data
        copied_layer.events.data.connect(copied_layer._sync_data_wrapper)

    def receive_data_wrapper():
        return receive_data(orig_layer, copied_layer)

    orig_layer.data_updated.connect(receive_data_wrapper)

    # Sync the event that is emitted when a point is moved or deleted. We need to capture
    # it on the original layer to process it there, and potentially undo it if it was an
    # invalid action (we have no way to judge that on a normal Points layer).
    def sync_data_event(
        orig_layer: TrackPoints, copied_layer: Points, event: Event
    ) -> None:
        """Send the event that is emitted when a point is moved or deleted to the original
        layer"""

        if hasattr(event, "action") and event.action in ("added", "changed", "removed"):
            with orig_layer.events.blocker_all():  # try to suppress updating visibility
                orig_layer.selected_data = (
                    copied_layer.selected_data
                )  # make sure the same data is selected
            orig_layer._update_data(event)

    def sync_data_wrapper(event):
        return sync_data_event(orig_layer, copied_layer, event)

    copied_layer._sync_data_wrapper = sync_data_wrapper
    copied_layer.events.data.connect(sync_data_wrapper)


def paint_event_hook(orig_layer: TrackLabels, copied_layer: Labels) -> None:
    """Hook to connect to paint events and process them on the original TracksLabels
    layer.

    Args:
        orig_layer (TrackLabels): TracksLabels layer from which the copied layer is
            derived.
        copied_layer (Labels): Labels equivalent of the TracksLabels layer. Instead of
            processing paint actions on this copy, we want to send them to the original
            layer and process them there.
    """

    def sync_paint(orig_layer: TrackLabels, copied_layer: Labels, event: Event):
        """Process paint event on original TrackLabels instance."""

        if copied_layer.data.ndim > 3:
            orig_layer._on_paint(event)
        else:
            show_info("Painting in the time dimension is not supported")
            orig_layer._revert_paint(event, copied_layer)
            orig_layer.refresh()

    def paint_wrapper(event: Event):
        """Wrap paint event and send to original layer."""

        return sync_paint(orig_layer, copied_layer, event)

    copied_layer.events.paint.connect(paint_wrapper)


def track_layers_hook(
    orig_layer: TrackLabels | TrackPoints, copied_layer: Labels | Points
) -> None:
    """Hook to capture click events on TrackLabels and TrackPoints derived Labels and
    Points layers, and forward them to their original layer. Also, register key binds
    for view mode, undo & redo to copied layer, that call functions on the original layer.

    Args:
        orig_layer (TrackLabels | TrackPoints): TracksLabels or TrackPoints layer from
            which the copied layer is derived.
        copied_layer (Labels | Points): Labels or Points equivalent of the TracksLabels
            or TrackPoints layer.
    """

    # define the click behavior the layer should respond to
    def click(
        orig_layer: TrackLabels | TrackPoints, layer: Labels | Points, event: Event
    ):
        if layer.mode == "pan_zoom":
            mouse_press_time = time.time()
            dragged = False
            yield  # start
            while event.type == "mouse_move":
                dragged = True
                yield
            if dragged and time.time() - mouse_press_time < 0.5:
                dragged = False  # treat micro drags as clicks

            if not dragged:
                if isinstance(layer, Labels):
                    label = layer.get_value(
                        event.position,
                        view_direction=event.view_direction,
                        dims_displayed=event.dims_displayed,
                        world=True,
                    )
                    orig_layer.process_click(event, label)

                if isinstance(layer, Points):
                    point_index = layer.get_value(
                        event.position,
                        view_direction=event.view_direction,
                        dims_displayed=event.dims_displayed,
                        world=True,
                    )
                    orig_layer.process_point_click(point_index, event)

    # Wrap and attach click callback
    def click_wrapper(layer, event):
        return click(orig_layer, layer, event)

    copied_layer.mouse_drag_callbacks.append(click_wrapper)

    # Bind keys to original layer TracksViewer
    copied_layer.bind_key("q")(orig_layer.tracks_viewer.toggle_display_mode)
    copied_layer.bind_key("z")(orig_layer.tracks_viewer.undo)
    copied_layer.bind_key("r")(orig_layer.tracks_viewer.redo)
    copied_layer.bind_key("d")(orig_layer.tracks_viewer.delete_node)
    copied_layer.bind_key("a")(orig_layer.tracks_viewer.create_edge)
    copied_layer.bind_key("b")(orig_layer.tracks_viewer.delete_edge)
    if isinstance(orig_layer, TrackLabels):
        copied_layer.bind_key("m")(orig_layer.assign_new_label)
