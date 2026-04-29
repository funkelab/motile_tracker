import argparse
import sys

import napari

from motile_tracker.application_menus.main_app import StartupWidget


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["all", "tracking", "editing"],
        default="all",
    )

    args = parser.parse_args()

    viewer = napari.Viewer()
    StartupWidget(viewer, mode=args.mode)

    napari.run()


if __name__ == "__main__":
    sys.exit(main())
