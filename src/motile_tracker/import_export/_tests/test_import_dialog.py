from pathlib import Path

import pandas as pd
import pytest

from motile_tracker.import_export.menus.import_dialog import ImportDialog


@pytest.fixture
def small_csv(tmp_path: Path) -> Path:
    p = tmp_path / "test.csv"
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "parent_id": [None, 1],
            "time": [0, 1],
            "y": [10.0, 20.0],
            "x": [5.0, 15.0],
            "area": [100.0, 150.0],
            "group": [True, False],
        }
    )
    df.to_csv(p, index=False)
    return p


def test_csv_dialog(qtbot, small_csv):
    """ImportDialog should load CSV, populate the field map correctly, and respond to
    changing the dimensions."""
    dialog = ImportDialog(import_type="csv")
    qtbot.addWidget(dialog)

    dialog.show()
    qtbot.waitExposed(dialog)

    # load csv
    dialog.import_widget._load_csv(str(small_csv))

    # import_widget._load_csv emits update_buttons which should trigger mapping update
    assert dialog.prop_map_widget.isVisible() is True

    # check standard fields
    expected_keys = {
        "id",
        "parent_id",
        "time",
        "y",
        "x",
        "tracklet_id",
        "lineage_id",
        "seg_id",
    }
    assert set(dialog.prop_map_widget.mapping_widgets.keys()) == expected_keys

    # seg_id visibility depends on segmentation selection (default None -> hidden)
    assert dialog.prop_map_widget.mapping_widgets["seg_id"].isVisible() is False
    dialog._toggle_scale_widget_and_seg_id(False)
    assert dialog.prop_map_widget.mapping_widgets["seg_id"].isVisible() is True
    assert dialog.scale_widget.isVisible() is True

    # update dimensions and check that now 'z' is in the standard fields and the scale
    # widget has 3 spatial elements (+1 for time)
    dialog.dimension_widget.radio_3D.setChecked(True)
    assert "z" in dialog.prop_map_widget.standard_fields
    assert len(dialog.scale_widget.get_scale()) == 4

    # check the optional features
    optional = dialog.prop_map_widget.optional_features
    assert "area" in optional or "flag" in optional

    widgets = optional["area"]
    combo = widgets["feature_option"]
    combo.setCurrentIndex(combo.count() - 1)
    assert combo.currentText() == "Custom"
    assert widgets["recompute"].isEnabled() is False
    combo.setCurrentIndex(0)  # Area
    assert widgets["recompute"].isEnabled() is True

    widgets = optional["group"]
    combo = widgets["feature_option"]
    combo.setCurrentIndex(combo.count() - 1)
    assert combo.currentText() == "Custom"
    assert widgets["recompute"].isEnabled() is False
    # Check the combobox count (regionprops features should not be available)
    assert combo.count() == 2
