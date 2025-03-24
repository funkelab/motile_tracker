import logging
import multiprocessing
import napari
import tqdm
import sys


logger = None
_original_tqdm_init = tqdm.tqdm.__init__


class TqdmToLogger:
    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level
        self._buffer = ""

    def write(self, message):
        # tqdm outputs '\r', so we buffer lines
        if message.strip():  # skip empty lines
            self.logger.log(self.level, message.strip())

    def flush(self):
        pass  # No-op for compatibility


# Patch tqdm globally


def _patched_tqdm_init(self, *args, **kwargs):
    if 'file' not in kwargs or kwargs['file'] is None:
        kwargs['file'] = TqdmToLogger(logger)
    _original_tqdm_init(self, *args, **kwargs)


def launch_viewer():
    print('Open Napari Viewer with Motile Tracker plugin...')
    # use an existing viewer if one exists, otherwise create a new one 
    viewer = napari.Viewer()
    viewer.window.add_plugin_dock_widget("motile-tracker")


def configure_logging(verbose):
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=log_level,
                        format=log_format,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        handlers=[
                            logging.StreamHandler(stream=sys.stdout)
                        ])
    return logging.getLogger()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    launch_viewer()
    logger = configure_logging(True)

    tqdm.tqdm.__init__ = _patched_tqdm_init

    # Start Napari event loop
    print('Start Napari event loop...')
    napari.run()
