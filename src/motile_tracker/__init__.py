import os

from ._wgpu_setup import configure_wgpu_backend

# must run before fastplotlib/pygfx create a wgpu instance
configure_wgpu_backend()

# TODO: remove once tracksdata >= the release containing royerlab/tracksdata#335
# ("Replace spatial-graph with rstar-python") is pinned.
#
# pygfx depends on uharfbuzz, and both uharfbuzz and spatial_graph's prebuilt rtree
# extensions are Cython limited-API builds that want the same shared runtime module
# (_cython_3_3_0limitednofinalize) with different struct sizes. Whichever imports
# first wins; the other raises "Shared Cython type cython_function_or_method has the
# wrong size, try recompiling". pygfx loads uharfbuzz for the tree view's text, so
# tracksdata's PointRTree loses, and importing a GEFF fails.
#
# Skipping the prebuilt modules makes spatial_graph compile the rtree on the fly with
# the locally installed Cython, which registers a differently named shared module and
# so cannot collide. Costs one compile per dtype/dims combination, then cached.
os.environ.setdefault("SPATIAL_GRAPH_NO_PREBUILT", "1")

from .application_menus.main_app import StartupWidget  # noqa: E402, F401
