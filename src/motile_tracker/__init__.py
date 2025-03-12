from importlib.metadata import PackageNotFoundError, version

try:
    from ._version import version as __version__
    __version__ = version("motile-tracker")
except PackageNotFoundError:
    # package is not installed
    __version__ = "uninstalled"
