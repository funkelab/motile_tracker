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


def _patched_tqdm_init(self, *args, **kwargs):
    if 'file' not in kwargs or kwargs['file'] is None:
        kwargs['file'] = TqdmToLogger(logger)
    # Patch tqdm globally
    _original_tqdm_init(self, *args, **kwargs)


def _launch_viewer():
    print('Open Napari Viewer with Motile Tracker plugin...')
    # use an existing viewer if one exists, otherwise create a new one 
    viewer = napari.Viewer()
    viewer.window.add_plugin_dock_widget("motile-tracker")


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
    args_parser.add_argument('--log-file', dest='logfile', help='Log file path')

    args = args_parser.parse_args()

    return args


if __name__ == '__main__':
    # freeze_support is required to prevent
    # creating a viewer every time a napari action is invoked
    multiprocessing.freeze_support()

    args = _define_args()

    if args.help:
        print('Motile Tracker launcher')
        print('Usage: python -m motile_tracker.launcher [options]')
        print('Options:')
        print('  --verbose        Enable verbose logging')
        print('  --log-file FILE  Log file path')
        print('  -h, --help       Display this help message')
        sys.exit(0)

    logger = _configure_logging(args.logfile, args.verbose)

    tqdm.tqdm.__init__ = _patched_tqdm_init

    _launch_viewer()

    # Start Napari event loop
    print('Start Napari event loop...')
    napari.run()
