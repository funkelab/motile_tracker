from motile_tracker.motile.menus.run_editor import RunEditor


def test__has_duplicate_labels(segmentation_2d):
    assert not RunEditor._has_duplicate_ids(segmentation_2d)
    frame = segmentation_2d[1]
    frame[frame == 2] = 1
    segmentation_2d[1] = frame
    assert RunEditor._has_duplicate_ids(segmentation_2d)
