from motile_toolbox.candidate_graph.graph_attributes import NodeAttr


class FeatureProperty:
    def __init__(self, node_attr, display_name, required, selected, enabled, dims):
        self.node_attr = node_attr
        self.display_name = display_name
        self.required = required
        self.selected = selected
        self.enabled = enabled
        self.dims = dims


# Create a list of feature properties
feature_properties = [
    FeatureProperty(NodeAttr.TIME.value, "Time", True, False, True, 3),
    FeatureProperty(NodeAttr.POS.value, "Position", True, False, True, 3),
    FeatureProperty(NodeAttr.TRACK_ID.value, "Track ID", True, False, True, 3),
    FeatureProperty(NodeAttr.AREA.value, "Area", False, False, True, 3),
    FeatureProperty(NodeAttr.PERIMETER.value, "Perimeter", False, False, True, 3),
    FeatureProperty(NodeAttr.CIRCULARITY.value, "Circularity", False, False, True, 3),
    FeatureProperty(
        NodeAttr.INTENSITY_MEAN.value, "Mean intensity", False, False, False, 3
    ),
    FeatureProperty(NodeAttr.VOLUME.value, "Volume", False, False, True, 4),
    FeatureProperty(NodeAttr.SURFACE_AREA.value, "Surface area", False, False, True, 4),
    FeatureProperty(NodeAttr.SPHERICITY.value, "Sphericity", False, False, True, 4),
    FeatureProperty(
        NodeAttr.INTENSITY_MEAN.value, "Mean intensity", False, False, False, 4
    ),
]
