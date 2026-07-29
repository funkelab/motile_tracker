import pytest


@pytest.fixture
def viewer(make_napari_viewer):
    """A napari viewer for data-view tests.

    A thin alias for napari's ``make_napari_viewer`` factory, for the common case
    of needing exactly one viewer. Tests that need a second one can request
    ``make_napari_viewer`` directly.

    Do not construct ``napari.Viewer`` directly in tests: ``make_napari_viewer``
    gives each test an isolated app-model registry, whereas a bare viewer
    re-registers plugin actions into the real one and napari >= 0.7 then raises
    ``ValueError: Command 'motile-tracker.solve' already registered``.
    """
    return make_napari_viewer()
