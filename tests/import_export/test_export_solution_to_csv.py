from motile_tracker.data_model import SolutionTracks


def test_export_to_csv(graph_2d, graph_3d, tmp_path, colormap):
    tracks = SolutionTracks(graph_2d, ndim=3)
    temp_file = tmp_path / "test_export_2d.csv"
    tracks.export_tracks(temp_file, colormap=colormap)
    with open(temp_file) as f:
        lines = f.readlines()

    assert len(lines) == tracks.graph.number_of_nodes() + 1  # add header

    header = [
        "t",
        "y",
        "x",
        "id",
        "parent_id",
        "track_id",
        "lineage_id",
        "color",
        "area",
    ]
    assert lines[0].strip().split(",") == header
    line1 = [
        "0",
        "50",
        "50",
        "1",
        "",
        "1",
        "1",
        "[120.  37.   6.]",
        "1245",
    ]
    assert lines[1].strip().split(",") == line1

    tracks = SolutionTracks(graph_3d, ndim=4)
    temp_file = tmp_path / "test_export_3d.csv"
    tracks.export_tracks(temp_file, colormap=colormap)
    with open(temp_file) as f:
        lines = f.readlines()

    assert len(lines) == tracks.graph.number_of_nodes() + 1  # add header

    header = ["t", "z", "y", "x", "id", "parent_id", "track_id", "lineage_id", "color"]
    assert lines[0].strip().split(",") == header
