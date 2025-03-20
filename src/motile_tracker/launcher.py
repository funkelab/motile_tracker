import napari

# Auto-load your plugin
print('Opening Napari with Motile Tracker plugin...')
viewer = napari.Viewer()
viewer.window.add_plugin_dock_widget("motile-tracker")

# Start Napari event loop
print('Start Napari event loop...')
napari.run()
