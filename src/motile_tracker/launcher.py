import napari

from PyQt5.QtWidgets import QApplication

# create the application
app = QApplication.instance()

# Auto-load your plugin
print('Opening Napari with Motile Tracker plugin...')

# use an existing viewer if one exists, otherwise create a new one 
viewer = napari.current_viewer() or napari.Viewer()
viewer.window.add_plugin_dock_widget("motile-tracker")

# Start Napari event loop
print('Start Napari event loop...')
napari.run()
