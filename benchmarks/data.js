window.BENCHMARK_DATA = {
  "lastUpdate": 1783629192391,
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
      },
      {
        "commit": {
          "author": {
            "email": "45037215+TeunHuijben@users.noreply.github.com",
            "name": "Teun Huijben",
            "username": "TeunHuijben"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "af109b8ce19723c1e199a95df8865b5b414cb6b1",
          "message": "update motile to 1.0 (#456)\n\n* update motile to 1.0\n\n* upper limit on motile (<2)",
          "timestamp": "2026-07-09T13:26:51-07:00",
          "tree_id": "2c738b95ae2c2db4265665876abc788d127e5519",
          "url": "https://github.com/funkelab/motile_tracker/commit/af109b8ce19723c1e199a95df8865b5b414cb6b1"
        },
        "date": 1783629191540,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_data_model.py::test_extract_sorted_tracks[small]",
            "value": 83.49117339662847,
            "unit": "iter/sec",
            "range": "stddev: 0.006236869658827632",
            "extra": "mean: 11.977314000001607 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_add_tracks[small]",
            "value": 0.33102719639800415,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 3.0208998260000044 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_treeview[small]",
            "value": 14.911821182210478,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 67.06089000000759 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_canvas[small]",
            "value": 14.274412010203408,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 70.05542500000672 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_set_display_mode_lineage[small]",
            "value": 41.82952819177797,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 23.90655700000366 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_flip_axes[small]",
            "value": 24.832001576533614,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 40.270616000000814 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_feature_recolor[small]",
            "value": 19.233617655566547,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 51.99229900000546 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_label_colormap_rebuild[small]",
            "value": 82.4761903609879,
            "unit": "iter/sec",
            "range": "stddev: 0.0016312943600020962",
            "extra": "mean: 12.124711333333002 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_node[small]",
            "value": 5.986464245153882,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 167.04350999999917 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_nodes_bulk[small]",
            "value": 4.044125272911353,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 247.272260999992 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo_bulk_delete[small]",
            "value": 4.597495266189062,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 217.509739999997 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_edge[small]",
            "value": 6.165490773990343,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 162.19309000000237 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_create_edge[small]",
            "value": 6.392226561577939,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 156.44001200000446 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo[small]",
            "value": 6.199283814098984,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 161.30895599999917 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_redo[small]",
            "value": 6.3525530758351625,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 157.41702399999724 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_data_model.py::test_extract_sorted_tracks[large]",
            "value": 2.5024409017092393,
            "unit": "iter/sec",
            "range": "stddev: 0.18883199679445717",
            "extra": "mean: 399.60983666666056 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_add_tracks[large]",
            "value": 0.22428354303742598,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.458641888999992 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_treeview[large]",
            "value": 1.9012703647849587,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 525.9641229999943 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_canvas[large]",
            "value": 1.8284291863929596,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 546.9175440000242 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_set_display_mode_lineage[large]",
            "value": 5.303788262589558,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 188.54447999999024 msec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_flip_axes[large]",
            "value": 0.464546860863096,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 2.1526353620000123 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_feature_recolor[large]",
            "value": 0.4139834541254052,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 2.415555476999998 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_label_colormap_rebuild[large]",
            "value": 2.466393323310228,
            "unit": "iter/sec",
            "range": "stddev: 0.0011787403889912465",
            "extra": "mean: 405.4503353333227 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_node[large]",
            "value": 0.13532136186977986,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 7.389816257999996 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_nodes_bulk[large]",
            "value": 0.022667139618650408,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 44.11672654 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo_bulk_delete[large]",
            "value": 0.20265367394626077,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.934526872999982 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_edge[large]",
            "value": 0.23679146356392897,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.223125213000003 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_create_edge[large]",
            "value": 0.21970614100193292,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.5515341329999615 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo[large]",
            "value": 0.23674132864121863,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.224019548000001 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_redo[large]",
            "value": 0.13378196915123305,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 7.474848863000034 sec\nrounds: 1"
          }
        ]
      }
    ]
  }
}