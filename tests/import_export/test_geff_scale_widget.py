from motile_tracker.import_export.menus.import_from_geff.geff_scale_widget import (
    ScaleWidget,
)


def test_scale_widget_with_3d_segmentation(qtbot):
    """Test that scale widget handles 3D segmentation data.

    When ndim=3 is provided (from actual segmentation), the widget should
    configure for 3D data with no z spinbox shown.
    """
    widget = ScaleWidget()
    qtbot.addWidget(widget)

    # Simulate metadata with no axes, but provide actual ndim from segmentation
    metadata = {}

    widget._prefill_from_metadata(metadata, ndim=3)

    # Should have y and x spinboxes but no z spinbox
    assert hasattr(widget, "y_spin_box"), "Widget should have y spinbox"
    assert hasattr(widget, "x_spin_box"), "Widget should have x spinbox"
    assert not hasattr(widget, "z_spin_box"), (
        "Widget should not have z spinbox for 3D data"
    )

    # get_scale should return [time_scale, y_scale, x_scale] for 3D
    scale = widget.get_scale()
    assert len(scale) == 3, (
        f"Expected get_scale() to return length 3 for 3D data, got {len(scale)}"
    )


def test_scale_widget_with_4d_segmentation(qtbot):
    """Test that scale widget handles 4D segmentation data.

    When ndim=4 is provided (from actual segmentation), the widget should
    configure for 4D data with z, y, and x spinboxes.
    """
    widget = ScaleWidget()
    qtbot.addWidget(widget)

    # Simulate metadata with no axes, but provide actual ndim from segmentation
    metadata = {}

    widget._prefill_from_metadata(metadata, ndim=4)

    # Should have z, y, and x spinboxes
    assert hasattr(widget, "z_spin_box"), "Widget should have z spinbox for 4D data"
    assert hasattr(widget, "y_spin_box"), "Widget should have y spinbox"
    assert hasattr(widget, "x_spin_box"), "Widget should have x spinbox"

    # get_scale should return [time_scale, z_scale, y_scale, x_scale] for 4D
    scale = widget.get_scale()
    assert len(scale) == 4, (
        f"Expected get_scale() to return length 4 for 4D data, got {len(scale)}"
    )


def test_scale_widget_with_3d_axes(qtbot):
    """Test that scale widget correctly handles 3D axes in metadata."""
    widget = ScaleWidget()
    qtbot.addWidget(widget)

    # Metadata with explicit 3D axes
    metadata = {
        "axes": [
            {"name": "t", "type": "time", "scale": 1.0},
            {"name": "y", "type": "space", "scale": 0.5},
            {"name": "x", "type": "space", "scale": 0.5},
        ]
    }

    widget._prefill_from_metadata(metadata)

    # Should not have z spinbox for 3D data
    assert not hasattr(widget, "z_spin_box"), (
        "Widget should not have z spinbox for 3D data"
    )

    # Scale should be 3D with values from metadata
    assert len(widget.scale) == 3
    assert widget.scale == [1.0, 0.5, 0.5]

    # Verify spinboxes have correct values
    assert widget.y_spin_box.value() == 0.5
    assert widget.x_spin_box.value() == 0.5

    scale = widget.get_scale()
    assert len(scale) == 3
    assert scale == [1, 0.5, 0.5]


def test_scale_widget_with_4d_axes(qtbot):
    """Test that scale widget correctly handles 4D axes in metadata."""
    widget = ScaleWidget()
    qtbot.addWidget(widget)

    # Metadata with explicit 4D axes
    metadata = {
        "axes": [
            {"name": "t", "type": "time", "scale": 1.0},
            {"name": "z", "type": "space", "scale": 2.0},
            {"name": "y", "type": "space", "scale": 0.5},
            {"name": "x", "type": "space", "scale": 0.5},
        ]
    }

    widget._prefill_from_metadata(metadata)

    # Should have z spinbox for 4D data
    assert hasattr(widget, "z_spin_box"), "Widget should have z spinbox for 4D data"

    # Scale should be 4D with values from metadata
    assert len(widget.scale) == 4
    assert widget.scale == [1.0, 2.0, 0.5, 0.5]

    # Verify spinboxes have correct values
    assert widget.z_spin_box.value() == 2.0
    assert widget.y_spin_box.value() == 0.5
    assert widget.x_spin_box.value() == 0.5

    scale = widget.get_scale()
    assert len(scale) == 4
    assert scale == [1, 2.0, 0.5, 0.5]
