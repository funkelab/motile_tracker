from importlib.metadata import PackageNotFoundError

try:
    from ._version import version as __version__
except PackageNotFoundError:
    # package is not installed
    __version__ = "uninstalled"
