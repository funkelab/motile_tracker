window.BENCHMARK_DATA = {
  "lastUpdate": 1783616344647,
  "repoUrl": "https://github.com/funkelab/motile_tracker",
  "entries": {
    "motile_tracker benchmarks (pytest-benchmark)": [
      {
        "commit": {
          "author": {
            "email": "malinmayorc@janelia.hhmi.org",
            "name": "Caroline Malin-Mayor",
            "username": "cmalinmayor"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "8b3e4d48bd7820cfd4c5ea759bff0121b44932e1",
          "message": "Merge pull request #449 from funkelab/dependabot/github_actions/dependencies-5bb021c6cc\n\nBump the dependencies group with 2 updates",
          "timestamp": "2026-07-09T11:50:15-04:00",
          "tree_id": "6934d1314849e3011013eb86b24aebf91efea57b",
          "url": "https://github.com/funkelab/motile_tracker/commit/8b3e4d48bd7820cfd4c5ea759bff0121b44932e1"
        },
        "date": 1783616344339,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_data_model.py::test_extract_sorted_tracks[small]",
            "value": 86.0943899862679,
            "unit": "iter/sec",
            "range": "stddev: 0.0074215813964221295",
            "extra": "mean: 11.615158666662259 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_add_tracks[small]",
            "value": 0.3249766872692525,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 3.0771438049999915 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_treeview[small]",
            "value": 14.129389346023698,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 70.77446699997836 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_canvas[small]",
            "value": 13.708240740447948,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 72.94882100001132 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_set_display_mode_lineage[small]",
            "value": 38.95536817245519,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 25.670402999992348 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_flip_axes[small]",
            "value": 22.02067966430825,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 45.4118590000121 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_feature_recolor[small]",
            "value": 17.938107787950102,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 55.747239999959675 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_label_colormap_rebuild[small]",
            "value": 78.73325540486424,
            "unit": "iter/sec",
            "range": "stddev: 0.0019368741738160437",
            "extra": "mean: 12.701113333340194 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_node[small]",
            "value": 5.577762113934787,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 179.28337199998623 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_nodes_bulk[small]",
            "value": 3.7060068222325953,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 269.832206999979 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo_bulk_delete[small]",
            "value": 4.025309455224216,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 248.42810500001633 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_edge[small]",
            "value": 5.46830172315023,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 182.8721329999894 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_create_edge[small]",
            "value": 5.882189070308852,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 170.00473600000987 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo[small]",
            "value": 5.539348928523935,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 180.52663100002064 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_redo[small]",
            "value": 5.709404923457718,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 175.14960199991947 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_data_model.py::test_extract_sorted_tracks[large]",
            "value": 2.255342201444282,
            "unit": "iter/sec",
            "range": "stddev: 0.21819040688361985",
            "extra": "mean: 443.39169433339976 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_add_tracks[large]",
            "value": 0.2112367382488996,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.734025001000077 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_treeview[large]",
            "value": 1.7490467022090845,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 571.7400219999718 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_canvas[large]",
            "value": 1.685832883864892,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 593.1786060000377 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_set_display_mode_lineage[large]",
            "value": 5.087842749842765,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 196.54695499991703 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_flip_axes[large]",
            "value": 0.4387737787355817,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 2.2790787610000507 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_feature_recolor[large]",
            "value": 0.39178054094247183,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 2.552449382999953 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_label_colormap_rebuild[large]",
            "value": 2.3689067177827923,
            "unit": "iter/sec",
            "range": "stddev: 0.002047763684195715",
            "extra": "mean: 422.135659666651 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_node[large]",
            "value": 0.1297463079976066,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 7.707348405000062 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_nodes_bulk[large]",
            "value": 0.023145120333509073,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 43.20565136799996 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo_bulk_delete[large]",
            "value": 0.18289575539097436,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 5.467595449999976 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_edge[large]",
            "value": 0.22976232266400867,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.352323690000048 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_create_edge[large]",
            "value": 0.23346330625475858,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.283328357000073 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo[large]",
            "value": 0.22620325811256534,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.420802814000012 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_redo[large]",
            "value": 0.12414135065096278,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 8.055333656000016 sec\nrounds: 1"
          }
        ]
      }
    ]
  }
}