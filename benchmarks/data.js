window.BENCHMARK_DATA = {
  "lastUpdate": 1785769860062,
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
          "id": "25f0e9df98facc17d944c92901159e7c36df72ee",
          "message": "Update the benchmarks (#455)\n\n* run benchmarks base+head on same machine for fair comparison + average fast tests over multiple rounds + remove the small benchmark, only large for now\n\n* update motile to 1.0\n\n* upper limit on motile (v2)",
          "timestamp": "2026-07-24T14:07:19-07:00",
          "tree_id": "0e6e7a15feb37546cbc234f4eea1349964e7e0de",
          "url": "https://github.com/funkelab/motile_tracker/commit/25f0e9df98facc17d944c92901159e7c36df72ee"
        },
        "date": 1784927676276,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_data_model.py::test_extract_sorted_tracks[large]",
            "value": 2.780368749352561,
            "unit": "iter/sec",
            "range": "stddev: 0.18531539032544717",
            "extra": "mean: 359.6645230000017 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_add_tracks[large]",
            "value": 0.15907837062773683,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 6.2862097220000095 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_treeview[large]",
            "value": 2.287324668587119,
            "unit": "iter/sec",
            "range": "stddev: 0.008966631510129521",
            "extra": "mean: 437.19197966666457 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_canvas[large]",
            "value": 1.7123675407150305,
            "unit": "iter/sec",
            "range": "stddev: 0.2104671550456624",
            "extra": "mean: 583.9867763333283 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_set_display_mode_lineage[large]",
            "value": 6.536067369442587,
            "unit": "iter/sec",
            "range": "stddev: 0.003517174927456958",
            "extra": "mean: 152.99719899999786 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_flip_axes[large]",
            "value": 0.5005501599365643,
            "unit": "iter/sec",
            "range": "stddev: 0.03517214329010231",
            "extra": "mean: 1.997801778999995 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_feature_recolor[large]",
            "value": 0.4658453995608423,
            "unit": "iter/sec",
            "range": "stddev: 0.2688091268514354",
            "extra": "mean: 2.146634915666681 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_label_colormap_rebuild[large]",
            "value": 3.0471404016439076,
            "unit": "iter/sec",
            "range": "stddev: 0.006831302992689951",
            "extra": "mean: 328.17654200000374 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_node[large]",
            "value": 0.1294250424438264,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 7.726479984999997 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_nodes_bulk[large]",
            "value": 0.019029033949432995,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 52.55127520700003 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo_bulk_delete[large]",
            "value": 0.22521683706470735,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.44016536700002 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_edge[large]",
            "value": 0.25814744707895926,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 3.8737551400000143 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_create_edge[large]",
            "value": 0.2662269410480112,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 3.756193855000049 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo[large]",
            "value": 0.23367160429254413,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.279510139999957 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_redo[large]",
            "value": 0.13241766040925632,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 7.551862771999993 sec\nrounds: 1"
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
          "id": "b99f6770180dd452affe539c7fa5f681aa60b730",
          "message": "Benchmark uses separate uvs for base vs main (#466)\n\n* make benchmark comparison use separate uvs\n\n* do all benchmarks 3 times + take the min + report mean/std in table\n\n* precommit fixes",
          "timestamp": "2026-07-27T15:15:07-07:00",
          "tree_id": "8598157a8a067b1578c03bd6ad3b8b75da3d96e6",
          "url": "https://github.com/funkelab/motile_tracker/commit/b99f6770180dd452affe539c7fa5f681aa60b730"
        },
        "date": 1785191145867,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_data_model.py::test_extract_sorted_tracks[large]",
            "value": 2.5802037921845247,
            "unit": "iter/sec",
            "range": "stddev: 0.17427361160577526",
            "extra": "mean: 387.56628566666507 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_add_tracks[large]",
            "value": 0.18375810779843166,
            "unit": "iter/sec",
            "range": "stddev: 1.3775342841300475",
            "extra": "mean: 5.441936750333336 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_treeview[large]",
            "value": 1.4845460823766308,
            "unit": "iter/sec",
            "range": "stddev: 0.22135596065555477",
            "extra": "mean: 673.6065736666698 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_canvas[large]",
            "value": 1.470213179587849,
            "unit": "iter/sec",
            "range": "stddev: 0.20582548886304558",
            "extra": "mean: 680.1734699999997 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_set_display_mode_lineage[large]",
            "value": 5.317385939891561,
            "unit": "iter/sec",
            "range": "stddev: 0.0033118569412281464",
            "extra": "mean: 188.06233199999647 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_flip_axes[large]",
            "value": 0.46380369111015834,
            "unit": "iter/sec",
            "range": "stddev: 0.050943244353848005",
            "extra": "mean: 2.1560846089999948 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_feature_recolor[large]",
            "value": 0.4360654125282766,
            "unit": "iter/sec",
            "range": "stddev: 0.29486139531305816",
            "extra": "mean: 2.293233930666664 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_label_colormap_rebuild[large]",
            "value": 2.426361921475708,
            "unit": "iter/sec",
            "range": "stddev: 0.00373502104588687",
            "extra": "mean: 412.1396693333376 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_node[large]",
            "value": 0.14112009680192888,
            "unit": "iter/sec",
            "range": "stddev: 0.06950303626878884",
            "extra": "mean: 7.08616293966666 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_nodes_bulk[large]",
            "value": 0.022383924970601324,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 44.674917437999966 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo_bulk_delete[large]",
            "value": 0.1926902474819029,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 5.189676244999987 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_edge[large]",
            "value": 0.23417751853770044,
            "unit": "iter/sec",
            "range": "stddev: 0.12270870028897254",
            "extra": "mean: 4.270264738666659 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_create_edge[large]",
            "value": 0.2396212397544185,
            "unit": "iter/sec",
            "range": "stddev: 0.10112263143424209",
            "extra": "mean: 4.1732527593333275 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo[large]",
            "value": 0.2311269931486551,
            "unit": "iter/sec",
            "range": "stddev: 0.12400382353632634",
            "extra": "mean: 4.326625749666657 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_redo[large]",
            "value": 0.1303214472985013,
            "unit": "iter/sec",
            "range": "stddev: 0.2796366522738499",
            "extra": "mean: 7.673334057666655 sec\nrounds: 3"
          }
        ]
      },
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
          "id": "863efae9aaf08bd20a6b13dbe4188199298528ba",
          "message": "Merge pull request #452 from funkelab/speedup-colormap\n\nSpeedup colormap",
          "timestamp": "2026-07-29T10:53:00-04:00",
          "tree_id": "ef961442e403cc6e651926b1c330a53d06d703a3",
          "url": "https://github.com/funkelab/motile_tracker/commit/863efae9aaf08bd20a6b13dbe4188199298528ba"
        },
        "date": 1785337346623,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_data_model.py::test_extract_sorted_tracks[large]",
            "value": 2.555861329054773,
            "unit": "iter/sec",
            "range": "stddev: 0.16868805763606767",
            "extra": "mean: 391.2575336666748 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_add_tracks[large]",
            "value": 0.21786740822682504,
            "unit": "iter/sec",
            "range": "stddev: 1.533312423617969",
            "extra": "mean: 4.58994765733333 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_treeview[large]",
            "value": 3.0533653486017736,
            "unit": "iter/sec",
            "range": "stddev: 0.006406285840962285",
            "extra": "mean: 327.5074830000051 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_canvas[large]",
            "value": 2.981179216389873,
            "unit": "iter/sec",
            "range": "stddev: 0.014536680991810496",
            "extra": "mean: 335.43773366667057 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_set_display_mode_lineage[large]",
            "value": 10.3538750521482,
            "unit": "iter/sec",
            "range": "stddev: 0.0004975373594065987",
            "extra": "mean: 96.58219700000359 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_flip_axes[large]",
            "value": 0.4984361104320328,
            "unit": "iter/sec",
            "range": "stddev: 0.22526116356025022",
            "extra": "mean: 2.0062751856666714 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_feature_recolor[large]",
            "value": 0.38550489336742577,
            "unit": "iter/sec",
            "range": "stddev: 0.17032652918648847",
            "extra": "mean: 2.5940007953333484 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_label_colormap_rebuild[large]",
            "value": 5.936473171327808,
            "unit": "iter/sec",
            "range": "stddev: 0.006868508242176389",
            "extra": "mean: 168.4501843333237 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_node[large]",
            "value": 0.14775435448298674,
            "unit": "iter/sec",
            "range": "stddev: 0.31620378282505085",
            "extra": "mean: 6.767990043333346 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_nodes_bulk[large]",
            "value": 0.022107515665089627,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 45.233485985000016 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo_bulk_delete[large]",
            "value": 0.2260177656323906,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.424430961000041 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_edge[large]",
            "value": 0.26153552187248846,
            "unit": "iter/sec",
            "range": "stddev: 0.19324290738367084",
            "extra": "mean: 3.8235723883333512 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_create_edge[large]",
            "value": 0.268512007057594,
            "unit": "iter/sec",
            "range": "stddev: 0.36856091649699696",
            "extra": "mean: 3.724228242000019 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo[large]",
            "value": 0.24278699878784343,
            "unit": "iter/sec",
            "range": "stddev: 0.3283054719820762",
            "extra": "mean: 4.118836696333308 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_redo[large]",
            "value": 0.14055007325226637,
            "unit": "iter/sec",
            "range": "stddev: 0.16554991422178206",
            "extra": "mean: 7.114902019333347 sec\nrounds: 3"
          }
        ]
      },
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
          "id": "b45a47c8220643c0532298c5aca0b636c9c6b338",
          "message": "Merge pull request #457 from funkelab/pre-commit-ci-update-config\n\n[pre-commit.ci] pre-commit autoupdate",
          "timestamp": "2026-07-29T10:54:11-04:00",
          "tree_id": "516023d82db9af983be5a93166d9899267916ca1",
          "url": "https://github.com/funkelab/motile_tracker/commit/b45a47c8220643c0532298c5aca0b636c9c6b338"
        },
        "date": 1785337428832,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_data_model.py::test_extract_sorted_tracks[large]",
            "value": 2.6499213449463115,
            "unit": "iter/sec",
            "range": "stddev: 0.15574423912449545",
            "extra": "mean: 377.3696913333329 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_add_tracks[large]",
            "value": 0.21103341111262097,
            "unit": "iter/sec",
            "range": "stddev: 1.372547012331199",
            "extra": "mean: 4.738586154333333 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_treeview[large]",
            "value": 3.155490047488728,
            "unit": "iter/sec",
            "range": "stddev: 0.004879969497785679",
            "extra": "mean: 316.90798733332787 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_canvas[large]",
            "value": 3.066103414339387,
            "unit": "iter/sec",
            "range": "stddev: 0.016640544504701378",
            "extra": "mean: 326.1468596666551 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_set_display_mode_lineage[large]",
            "value": 10.770582433138486,
            "unit": "iter/sec",
            "range": "stddev: 0.00028957098784136503",
            "extra": "mean: 92.84548966667217 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_flip_axes[large]",
            "value": 0.4926212086922272,
            "unit": "iter/sec",
            "range": "stddev: 0.05039672067323379",
            "extra": "mean: 2.0299572619999915 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_feature_recolor[large]",
            "value": 0.3854251897706158,
            "unit": "iter/sec",
            "range": "stddev: 0.0394839948003764",
            "extra": "mean: 2.594537218999998 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_label_colormap_rebuild[large]",
            "value": 6.522778960660822,
            "unit": "iter/sec",
            "range": "stddev: 0.006814653001995327",
            "extra": "mean: 153.30888966666598 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_node[large]",
            "value": 0.13962777022483408,
            "unit": "iter/sec",
            "range": "stddev: 0.16346477814243815",
            "extra": "mean: 7.161899086333335 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_nodes_bulk[large]",
            "value": 0.02005753335360352,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 49.85657918999999 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo_bulk_delete[large]",
            "value": 0.23269335434209434,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.297501330999978 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_edge[large]",
            "value": 0.26372833088080944,
            "unit": "iter/sec",
            "range": "stddev: 0.11136516066385047",
            "extra": "mean: 3.7917807186666814 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_create_edge[large]",
            "value": 0.25835687254376216,
            "unit": "iter/sec",
            "range": "stddev: 0.2893897868223169",
            "extra": "mean: 3.8706150533333052 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo[large]",
            "value": 0.2516230381910731,
            "unit": "iter/sec",
            "range": "stddev: 0.3471009412453733",
            "extra": "mean: 3.974198893666634 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_redo[large]",
            "value": 0.13857151095516218,
            "unit": "iter/sec",
            "range": "stddev: 0.13707982308293143",
            "extra": "mean: 7.21649055499995 sec\nrounds: 3"
          }
        ]
      },
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
          "id": "48103308bc88895ea2c9edff9039222838f5f68a",
          "message": "Merge pull request #464 from funkelab/fix_colliding_attributes_in_import_widget\n\nFix colliding features widges in import menu",
          "timestamp": "2026-07-29T11:17:14-04:00",
          "tree_id": "5fedd8cf7052bc695569266e87df74249dda2687",
          "url": "https://github.com/funkelab/motile_tracker/commit/48103308bc88895ea2c9edff9039222838f5f68a"
        },
        "date": 1785338821172,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_data_model.py::test_extract_sorted_tracks[large]",
            "value": 2.27742372762941,
            "unit": "iter/sec",
            "range": "stddev: 0.19742428794119937",
            "extra": "mean: 439.0926413333318 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_add_tracks[large]",
            "value": 0.21523757580600525,
            "unit": "iter/sec",
            "range": "stddev: 1.5151917525680993",
            "extra": "mean: 4.646028911333332 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_treeview[large]",
            "value": 3.143701464124737,
            "unit": "iter/sec",
            "range": "stddev: 0.008748488232679822",
            "extra": "mean: 318.09636233331656 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_canvas[large]",
            "value": 3.1564904175779684,
            "unit": "iter/sec",
            "range": "stddev: 0.015177754819868362",
            "extra": "mean: 316.8075513333311 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_set_display_mode_lineage[large]",
            "value": 10.986020055111748,
            "unit": "iter/sec",
            "range": "stddev: 0.0009080350670616505",
            "extra": "mean: 91.02477466666414 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_flip_axes[large]",
            "value": 0.5899711459763478,
            "unit": "iter/sec",
            "range": "stddev: 0.09523388632729893",
            "extra": "mean: 1.694998148333326 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_feature_recolor[large]",
            "value": 0.4088871029572519,
            "unit": "iter/sec",
            "range": "stddev: 0.041861078752342046",
            "extra": "mean: 2.4456628560000033 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_label_colormap_rebuild[large]",
            "value": 6.558803097839976,
            "unit": "iter/sec",
            "range": "stddev: 0.008290026955072229",
            "extra": "mean: 152.46684266666458 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_node[large]",
            "value": 0.14641492425314342,
            "unit": "iter/sec",
            "range": "stddev: 0.3833789824299775",
            "extra": "mean: 6.82990484133335 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_nodes_bulk[large]",
            "value": 0.021541761798276743,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 46.421458438 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo_bulk_delete[large]",
            "value": 0.22564298654569356,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.43177966799999 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_edge[large]",
            "value": 0.2626874468895398,
            "unit": "iter/sec",
            "range": "stddev: 0.14850272087579286",
            "extra": "mean: 3.806805433000003 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_create_edge[large]",
            "value": 0.2490767696172377,
            "unit": "iter/sec",
            "range": "stddev: 0.5582789725186729",
            "extra": "mean: 4.014826439000008 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo[large]",
            "value": 0.2416395068297768,
            "unit": "iter/sec",
            "range": "stddev: 0.5007877985465562",
            "extra": "mean: 4.138396130333319 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_redo[large]",
            "value": 0.1377240845364146,
            "unit": "iter/sec",
            "range": "stddev: 0.12984051617266024",
            "extra": "mean: 7.2608941519999535 sec\nrounds: 3"
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
          "id": "e85a0dd57646074d207b0bc2386b8fabe3e45037",
          "message": "make table lazy (QTableView) to fix OOM on large datasets (#461)\n\n* make table lazy (QTableView) to fix OOM on large datasets\n\n* remove unused special selection from table view\n\n* Use QStyle selected flag instead of iterating rows\n\n---------\n\nCo-authored-by: AnniekStok <anniek.stokkermans@gmail.com>\nCo-authored-by: Caroline Malin-Mayor <malinmayorc@janelia.hhmi.org>",
          "timestamp": "2026-07-29T11:11:24-07:00",
          "tree_id": "414e43ee39c59b52c56887a4fa01a1b25d31a7a7",
          "url": "https://github.com/funkelab/motile_tracker/commit/e85a0dd57646074d207b0bc2386b8fabe3e45037"
        },
        "date": 1785349224556,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_data_model.py::test_extract_sorted_tracks[large]",
            "value": 2.5281860851209985,
            "unit": "iter/sec",
            "range": "stddev: 0.1587341178063402",
            "extra": "mean: 395.5405046666651 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_add_tracks[large]",
            "value": 0.22812761143950305,
            "unit": "iter/sec",
            "range": "stddev: 1.4047125924455603",
            "extra": "mean: 4.383511464000004 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_treeview[large]",
            "value": 3.4037364410131348,
            "unit": "iter/sec",
            "range": "stddev: 0.006527046342932577",
            "extra": "mean: 293.79478033332873 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_canvas[large]",
            "value": 2.3012409168563774,
            "unit": "iter/sec",
            "range": "stddev: 0.21092738361786834",
            "extra": "mean: 434.54815733332924 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_set_display_mode_lineage[large]",
            "value": 11.34590267477973,
            "unit": "iter/sec",
            "range": "stddev: 0.0009807919799373994",
            "extra": "mean: 88.13754433332595 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_flip_axes[large]",
            "value": 0.5004266696168248,
            "unit": "iter/sec",
            "range": "stddev: 0.020748335440350246",
            "extra": "mean: 1.998294776666673 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_feature_recolor[large]",
            "value": 0.43711674540831896,
            "unit": "iter/sec",
            "range": "stddev: 0.05108846092548533",
            "extra": "mean: 2.287718350999986 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_label_colormap_rebuild[large]",
            "value": 6.779540961620329,
            "unit": "iter/sec",
            "range": "stddev: 0.005401390272355007",
            "extra": "mean: 147.50261200000145 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_node[large]",
            "value": 0.14976131129068063,
            "unit": "iter/sec",
            "range": "stddev: 0.2843013636920345",
            "extra": "mean: 6.677291961333329 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_nodes_bulk[large]",
            "value": 0.02090115998588049,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 47.84423451499998 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo_bulk_delete[large]",
            "value": 0.25428495307426235,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 3.932596042 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_edge[large]",
            "value": 0.2895360752396501,
            "unit": "iter/sec",
            "range": "stddev: 0.09669504524185055",
            "extra": "mean: 3.4538010476666727 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_create_edge[large]",
            "value": 0.275779457510947,
            "unit": "iter/sec",
            "range": "stddev: 0.36289103084257224",
            "extra": "mean: 3.626085891333313 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo[large]",
            "value": 0.2590941719921866,
            "unit": "iter/sec",
            "range": "stddev: 0.35278534394873484",
            "extra": "mean: 3.8596005163333302 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_redo[large]",
            "value": 0.1480490101589305,
            "unit": "iter/sec",
            "range": "stddev: 0.13230432354701793",
            "extra": "mean: 6.754519999333335 sec\nrounds: 3"
          }
        ]
      },
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
          "id": "c7c186143e82debee902642db7b3eb153a05e9f7",
          "message": "Merge pull request #469 from funkelab/dependabot/github_actions/dependencies-9e9b9688a3\n\nBump the dependencies group with 3 updates",
          "timestamp": "2026-08-03T11:04:02-04:00",
          "tree_id": "2666251001c57495447516bd8c0f94adf1b02de7",
          "url": "https://github.com/funkelab/motile_tracker/commit/c7c186143e82debee902642db7b3eb153a05e9f7"
        },
        "date": 1785769859677,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/benchmarks/bench_data_model.py::test_extract_sorted_tracks[large]",
            "value": 2.4635207270484485,
            "unit": "iter/sec",
            "range": "stddev: 0.18669631107808302",
            "extra": "mean: 405.9231119999964 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_add_tracks[large]",
            "value": 0.22458141592669967,
            "unit": "iter/sec",
            "range": "stddev: 1.3719564808857305",
            "extra": "mean: 4.452728182666665 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_treeview[large]",
            "value": 3.41971121865606,
            "unit": "iter/sec",
            "range": "stddev: 0.0054949893270443235",
            "extra": "mean: 292.422352666667 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_click_node_canvas[large]",
            "value": 3.3161281770820277,
            "unit": "iter/sec",
            "range": "stddev: 0.011868865413654974",
            "extra": "mean: 301.556498000006 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_set_display_mode_lineage[large]",
            "value": 11.338411576072062,
            "unit": "iter/sec",
            "range": "stddev: 0.0005097225785094128",
            "extra": "mean: 88.19577533332297 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_flip_axes[large]",
            "value": 0.4926509758733269,
            "unit": "iter/sec",
            "range": "stddev: 0.048031626577547754",
            "extra": "mean: 2.029834606999998 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_tree_feature_recolor[large]",
            "value": 0.43059085075867126,
            "unit": "iter/sec",
            "range": "stddev: 0.06482650979010589",
            "extra": "mean: 2.3223902649999864 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_label_colormap_rebuild[large]",
            "value": 6.728528926088352,
            "unit": "iter/sec",
            "range": "stddev: 0.004967028660395058",
            "extra": "mean: 148.62089633333161 msec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_node[large]",
            "value": 0.30128975642894207,
            "unit": "iter/sec",
            "range": "stddev: 0.0788185359138268",
            "extra": "mean: 3.3190640526666755 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_nodes_bulk[large]",
            "value": 0.2532302145561644,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 3.9489758429999995 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo_bulk_delete[large]",
            "value": 0.22990989455789398,
            "unit": "iter/sec",
            "range": "stddev: 0",
            "extra": "mean: 4.349530071000004 sec\nrounds: 1"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_delete_edge[large]",
            "value": 0.2807884212592801,
            "unit": "iter/sec",
            "range": "stddev: 0.06545242056863163",
            "extra": "mean: 3.561400415000018 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_create_edge[large]",
            "value": 0.2691746879441361,
            "unit": "iter/sec",
            "range": "stddev: 0.3475522563724837",
            "extra": "mean: 3.715059568333326 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_undo[large]",
            "value": 0.2837813117149218,
            "unit": "iter/sec",
            "range": "stddev: 0.1558697629793096",
            "extra": "mean: 3.52384022033336 sec\nrounds: 3"
          },
          {
            "name": "tests/benchmarks/bench_ui_actions.py::test_redo[large]",
            "value": 0.25631425559267773,
            "unit": "iter/sec",
            "range": "stddev: 0.174615515334436",
            "extra": "mean: 3.901460719333348 sec\nrounds: 3"
          }
        ]
      }
    ]
  }
}