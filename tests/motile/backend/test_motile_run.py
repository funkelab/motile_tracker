import numpy as np

from motile_tracker.motile.backend import MotileRun, SolverParams


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
