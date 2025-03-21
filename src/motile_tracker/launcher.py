if __name__ == '__main__':
    import napari

    print('Opening Napari with Motile Tracker plugin...')
    # use an existing viewer if one exists, otherwise create a new one 
    viewer = napari.Viewer()
    viewer.window.add_plugin_dock_widget("motile-tracker")
    # Start Napari event loop
    print('Start Napari event loop...')
    napari.run()
