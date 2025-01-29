import logging
from pathlib import Path

import napari
import pandas as pd
import zarr
from appdirs import AppDirs
from napari.utils.theme import _themes

from motile_tracker.application_menus import MainApp
from motile_tracker.data_views import TreeWidget

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(filename)s:%(lineno)d] %(levelname)-8s %(message)s",
)
logging.getLogger("motile_tracker").setLevel(logging.DEBUG)

_themes["dark"].font_size = "18pt"


# Load Zarr datasets
csv_path = "hela_example_tracks.csv"  # replace with your points file
dataframe = pd.read_csv(csv_path)
position_columns = ["t", "x", "y"]  # replace with your position columns

positions = dataframe[position_columns].to_numpy()

# Initialize Napari viewer
viewer = napari.Viewer()

# Add image and label layers to the viewer
viewer.add_points(positions, name="points")
# Add your custom widget
widget = MainApp(viewer)
viewer.window.add_dock_widget(widget, name="Motile")

# Start the Napari GUI event loop
napari.run()
