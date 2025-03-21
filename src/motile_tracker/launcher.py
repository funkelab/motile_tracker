import multiprocessing
import napari


def launch_viewer():
    print('Open Napari Viewer with Motile Tracker plugin...')
    # use an existing viewer if one exists, otherwise create a new one 
    viewer = napari.Viewer()
    viewer.window.add_plugin_dock_widget("motile-tracker")


if __name__ == '__main__':
    multiprocessing.freeze_support()
    launch_viewer()

    # Start Napari event loop
    print('Start Napari event loop...')
    napari.run()
