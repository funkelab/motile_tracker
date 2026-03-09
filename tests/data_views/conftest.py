import napari
import pytest


@pytest.fixture(scope="module")
def viewer(qapp):
    """Module-scoped napari viewer shared across all tests in a module.

    Avoids the expensive viewer creation per test. Tests should use the
    per-file autouse ``clear_viewer_layers`` fixture (defined in each test
    module) to clean up layers between tests.
    """
    v = napari.Viewer(show=False)
    yield v
    v.close()
