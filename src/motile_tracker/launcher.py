import argparse
import logging
import multiprocessing
import os
import napari
import tqdm
import sys


logger = None
_original_tqdm_init = tqdm.tqdm.__init__


class TqdmToLogger:
    def __init__(self, logger):
        self.logger = logger

    def write(self, message):
        if logger:
            self.logger.log(logger.level, message.lstrip("\r"))

    def flush(self):
        pass  # No-op for compatibility


def _configure_logging(logfile=None, verbose=False):
    loglevel = logging.DEBUG if verbose else logging.INFO
    logformat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    if logfile:
        logdir = os.path.dirname(logfile)
        if logdir and not os.path.exists(logdir):
            os.makedirs(logdir, exist_ok=True)  # Create parent dirs if needed

        handler = logging.FileHandler(logfile)
    else:
        handler = logging.StreamHandler(stream=sys.stdout)

    logging.basicConfig(level=loglevel,
                        format=logformat,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        handlers=[
                            handler
                        ])
    return logging.getLogger()


def _define_args():
    args_parser = argparse.ArgumentParser(description='Motile Tracker launcher')

    args_parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args_parser.add_argument('-l', '--logfile', dest='logfile', help='Log file path')

    args = args_parser.parse_args()

    return args


def _launch_viewer():
    print('Open Napari Viewer with Motile Tracker plugin...')
    # use an existing viewer if one exists, otherwise create a new one 
    viewer = napari.Viewer()
    viewer.window.add_plugin_dock_widget("motile-tracker")


def _patched_tqdm_init(self, *args, **kwargs):
    if (('file' not in kwargs or kwargs['file'] is None) and
        (not sys.stdout or not sys.stdout.isatty() or not sys.stderr or not sys.stderr.isatty())):
        kwargs['file'] = TqdmToLogger(logger)
    _original_tqdm_init(self, *args, **kwargs)


if __name__ == '__main__':
    # freeze_support is required to prevent
    # creating a viewer every time a napari action is invoked
    multiprocessing.freeze_support()

    args = _define_args()

    logger = _configure_logging(args.logfile, args.verbose)

    # Patch tqdm globally
    tqdm.tqdm.__init__ = _patched_tqdm_init

    _launch_viewer()

    # Start Napari event loop
    print('Start Napari event loop...')
    napari.run()
