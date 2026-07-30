"""Helpers for writing geff stores that hold extra, non-geff files.

Saving tracks writes a geff store, and dependent applications add their own
files inside it by listening to TracksList.tracks_saved. That is a supported
arrangement — a geff is a zarr directory, and rewriting the geff leaves
everything else alone — but it makes both zarr and geff chatty.
"""

from __future__ import annotations

import warnings
from pathlib import Path

from funtracks.data_model import Tracks
from funtracks.import_export import write_to_geff


def write_geff_over(tracks: Tracks, path: Path) -> None:
    """Write tracks to a geff store, replacing any geff already there.

    Saved tracks are a geff store that dependents may also keep their own files
    in: tracks_saved listeners write extra data (e.g. solver params) inside the
    store, and it survives because writing a geff only replaces geff-controlled
    groups. Zarr walks the directory on the way and warns once per file it does
    not recognise, and geff warns that it found non-geff members. Both are
    expected for any store with extras in it and say nothing the caller can act
    on, so they are silenced.

    The filters match on message rather than category: zarr only grew a
    dedicated ZarrUserWarning class in 3.x, and this package supports 2.x,
    where importing it fails outright.

    Args:
        tracks (Tracks): The tracks to write.
        path (Path): The geff store to write them to.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Object at .* is not recognized as a component of a Zarr hierarchy",
            category=UserWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message="Found non-geff members in zarr.*",
            category=UserWarning,
        )
        write_to_geff(tracks, path, overwrite=True)
