import sys

import finn
from finn.track_application_menus.main_app import MainApp

from motile_tracker.motile.menus.motile_widget import MotileWidget


def main():
    # Auto-load the motile tracker
    viewer = finn.Viewer()
    main_app = MainApp(viewer)
    motile_widget = MotileWidget(viewer)
    main_app.menu_widget.tabwidget.addTab(motile_widget, "Track with Motile")
    viewer.window.add_dock_widget(main_app)

    # Start finn event loop
    finn.run()


if __name__ == "__main__":
    sys.exit(main())
