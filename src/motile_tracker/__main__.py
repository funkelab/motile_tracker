import sys

# Set up logging BEFORE other imports to capture tqdm and other output
from motile_tracker.utils.logging import setup_logging

setup_logging()

import napari  # noqa: E402

from motile_tracker.application_menus.main_app import MainApp  # noqa: E402


def main() -> None:
    # Auto-load the motile tracker
    viewer = napari.Viewer()
    main_app = MainApp(viewer)
    viewer.window.add_dock_widget(main_app)

    # Start napari event loop
    napari.run()


if __name__ == "__main__":
    sys.exit(main())
