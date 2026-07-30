"""Helpers for writing geff stores that hold extra, non-geff files."""

from __future__ import annotations

import warnings
from pathlib import Path

from funtracks.data_model import Tracks
from funtracks.import_export import write_to_geff
from zarr.errors import ZarrUserWarning


def write_geff_over(tracks: Tracks, path: Path) -> None:
    """Write tracks to a geff store, replacing any geff already there.

    Use this instead of calling write_to_geff directly when the store may also
    hold files that are not part of the geff (a MotileRun keeps its solver
    params and gaps inside its store). Writing a geff only replaces
    geff-controlled groups, so those files survive — but zarr walks the
    directory on the way and warns once per file it does not recognise, and
    geff warns that it found non-geff members. Both are expected here and say
    nothing the caller can act on, so they are silenced.

    Args:
        tracks (Tracks): The tracks to write.
        path (Path): The geff store to write them to.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Object at .* is not recognized as a component of a Zarr hierarchy",
            category=ZarrUserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="Found non-geff members in zarr.*",
            category=UserWarning,
        )
        write_to_geff(tracks, path, overwrite=True)
