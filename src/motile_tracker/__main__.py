import sys

import napari

from motile_tracker.application_menus.main_app import MainApp


def main() -> None:
    # Auto-load the motile tracker
    viewer = napari.Viewer()
    main_app = MainApp(viewer)
    viewer.window.add_dock_widget(main_app)

    # Start napari event loop
    napari.run()


if __name__ == "__main__":
    sys.exit(main())
