import argparse
import logging
import multiprocessing
import os
import sys

from motile_tracker.__main__ import main

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


if __name__ == '__main__':
    # freeze_support is required to prevent
    # creating a viewer every time a napari action is invoked
    multiprocessing.freeze_support()

    args = _define_args()
    global logger
    logger = _configure_logging(args.logfile, args.verbose)

    # Start event loop
    print('Start event loop...')
    sys.exit(main())
