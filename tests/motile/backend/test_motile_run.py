import numpy as np

from motile_tracker.motile.backend import MotileRun, SolverParams


def test_geff_path_finds_saved_geff(tmp_path, graph_2d):
    """geff_path resolves the geff store that save() wrote."""
    run = MotileRun(graph=graph_2d, run_name="test", solver_params=SolverParams())
    run_dir = run.save(tmp_path)

    geff = MotileRun.geff_path(run_dir)
    assert geff == run_dir / "tracks.geff"
    assert geff.exists()


def test_geff_path_falls_back_to_tracks_dir(tmp_path):
    """Intermediate-format runs stored the graph in a 'tracks' zarr."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "tracks").mkdir()

    assert MotileRun.geff_path(run_dir) == run_dir / "tracks"


def test_geff_path_none_for_v1_run(tmp_path):
    """v1 runs stored the graph as graph.json, so there is no geff to report."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "graph.json").write_text("{}")

    assert MotileRun.geff_path(run_dir) is None


def test_save_load(tmp_path, graph_2d):
    run_name = "test"
    scale = [1.0, 2.0, 3.0]
    run = MotileRun(
        graph=graph_2d,
        run_name=run_name,
        solver_params=SolverParams(),
        scale=scale,
    )
    path = run.save(tmp_path)
    newrun = MotileRun.load(path)
    assert set(run.graph.node_ids()) == set(newrun.graph.node_ids())
    assert {tuple(e) for e in run.graph.edge_list()} == {
        tuple(e) for e in newrun.graph.edge_list()
    }
    assert run.run_name == newrun.run_name
    assert np.array_equal(np.asarray(run.segmentation), np.asarray(newrun.segmentation))
    assert run.time.replace(microsecond=0) == newrun.time
    assert run.gaps == newrun.gaps
    assert run.scale == newrun.scale
    assert run.solver_params == newrun.solver_params
    # Verify core accessor methods work on the loaded run
    # (regression: time_attr mismatch after load caused KeyError in get_time)
    node_ids = list(newrun.graph.node_ids())
    for node_id in node_ids:
        newrun.get_time(node_id)
        newrun.get_position(node_id)
        newrun.get_track_id(node_id)
    newrun.get_positions(node_ids, incl_time=True)
