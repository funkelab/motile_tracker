"""Reading and writing tracks as an on-disk tracksdata SQL database.

A funtracks ``Tracks`` holds a tracksdata graph, which may be an in-memory
``IndexedRXGraph`` or a database-backed ``SQLGraph``. The SQL backend is
interesting for three reasons: the file on disk is always in sync, so a crash
loses nothing; several annotators can work against one database; and the
candidate graph (the ``solution=False`` nodes) does not have to fit in RAM.

Import never converts: CSV and geff always build in-memory graphs. The only way
into the SQL backend is to open a database that already exists, or to export one
and optionally carry on editing in it.

Note that SQL does not make the *solution* out-of-core. ``Tracks`` builds
``graph_solution`` as a ``GraphView``, which subclasses ``RustWorkXGraph``, so
for a SQL root it is materialised in memory. What lives on disk is the full
graph. Restricting the solution view to a time window is the follow-up that
makes the memory benefit real.

This module deliberately holds no Qt, so the round trip can be tested without a
running application.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import tracksdata as td
from funtracks.data_model import Tracks

SQL_SUFFIX = ".db"

DRIVERNAME = "sqlite"

# Graph metadata key holding what a database cannot otherwise say about itself.
#
# ``Tracks`` recovers nodes, edges, attributes and (via ``shape`` plus the
# ``mask`` attribute) the segmentation straight from the graph, but not the
# scale or which attribute keys are time, position and track id. Those go here,
# under one namespaced key so nothing collides with tracksdata's own metadata.
META_KEY = "motile_tracker"


def is_sql_backed(tracks: Tracks) -> bool:
    """Whether the tracks are stored in a database rather than in memory.

    Args:
        tracks (Tracks): The tracks to inspect.
    """
    return isinstance(tracks.graph_full, td.graph.SQLGraph)


def sql_database_path(tracks: Tracks) -> Path | None:
    """The database file backing the given tracks, or None if in memory.

    Reaches into ``SQLGraph._url``, which tracksdata does not expose publicly.
    Kept in one place so there is a single site to update if it ever does.

    Args:
        tracks (Tracks): The tracks to inspect.
    """
    if not is_sql_backed(tracks):
        return None
    database = tracks.graph_full._url.database
    return Path(database) if database else None


def write_tracks_to_sql(tracks: Tracks, path: Path) -> td.graph.SQLGraph:
    """Write tracks to a SQLite database at the given path.

    Writes ``graph_full``, not ``graph_solution``, so soft-deleted candidates
    survive. A database exists to be reopened and edited, and a geff round trip
    already drops candidates and marks everything ``solution=True`` again; the
    database format should not repeat that.

    The destination must not already hold data. tracksdata copies a SQLite
    source to a SQLite destination with ``ATTACH DATABASE``, never materialising
    the graph, but only when the destination file is absent or empty and
    ``overwrite`` is not set. Asking the caller to clear the path first (having
    confirmed with the user) keeps that fast path available for tracks that are
    themselves already SQL-backed.

    Args:
        tracks (Tracks): The tracks to write.
        path (Path): The database file to create.

    Returns:
        td.graph.SQLGraph: The graph that was written, open and ready to be
            handed to :func:`rebind_tracks_to_graph`.

    Raises:
        FileExistsError: If something is already at `path`.
    """
    path = Path(path)
    if path.exists() and path.stat().st_size > 0:
        raise FileExistsError(
            f"{path} already exists. Remove it before writing a database there."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    graph = td.graph.SQLGraph.from_other(
        tracks.graph_full,
        drivername=DRIVERNAME,
        database=str(path),
    )
    graph.metadata[META_KEY] = _describe(tracks)
    return graph


def tracks_from_sql(path: Path, scale: list[float] | None = None) -> Tracks:
    """Open an existing SQLite database as tracks.

    The database is opened in place, not copied: every later edit is written
    straight to this file. ``SQLGraph`` reflects the existing schema back when
    ``overwrite`` is false, which is the default.

    A database that records no scale opens without one. Tracks with no scale are
    an ordinary state throughout the application - loading a geff produces them
    too - so there is nothing to ask the user about here.

    Args:
        path (Path): An existing database file.
        scale (list[float] | None): Scale to use, overriding whatever the
            database records.

    Returns:
        Tracks: Tracks backed by the database.
    """
    graph = td.graph.SQLGraph(drivername=DRIVERNAME, database=str(Path(path)))
    described = graph.metadata.get(META_KEY) or {}

    if scale is None:
        scale = described.get("scale")

    return Tracks(
        graph,
        time_attr=described.get("time_attr") or _sniff_time_attr(graph),
        pos_attr=described.get("pos_attr") or _sniff_pos_attr(graph),
        tracklet_attr=described.get("tracklet_attr"),
        lineage_attr=described.get("lineage_attr"),
        scale=scale,
        ndim=described.get("ndim"),
    )


def rebind_tracks_to_graph(tracks: Tracks, graph: td.graph.BaseGraph) -> Tracks:
    """Return tracks of the same kind, backed by the given graph.

    Used after exporting to a database, when the user asked to carry on editing
    in it. Building a new object rather than swapping ``graph_full`` in place
    keeps the graph/view/annotator wiring entirely in funtracks' hands.

    The new object starts with an empty action history, so **undo and redo are
    cleared**: the actions on the old stack hold references into the old graph
    and cannot be replayed against the new one. Callers must tell the user.

    Args:
        tracks (Tracks): The tracks to rebind. Its own graph is left alone.
        graph (td.graph.BaseGraph): The graph to bind to.

    Returns:
        Tracks: A new object carrying over everything about `tracks` that is not
            stored in the graph. A MotileRun rebinds to a MotileRun so its solver
            params survive; anything else rebinds to a plain Tracks, which is
            what every other loader in this package returns.
    """
    # Imported here rather than at module level: motile.backend imports
    # geff_io from this package, and MotileRun is only needed on this path.
    from motile_tracker.motile.backend.motile_run import MotileRun

    if isinstance(tracks, MotileRun):
        return MotileRun(
            graph,
            run_name=tracks.run_name,
            scale=tracks.scale,
            ndim=tracks.ndim,
            solver_params=tracks.solver_params,
            input_segmentation=tracks.input_segmentation,
            input_points=tracks.input_points,
            time=tracks.time,
            gaps=tracks.gaps,
            status=tracks.status,
            _features=tracks.features,
        )

    return Tracks(
        graph,
        scale=tracks.scale,
        ndim=tracks.ndim,
        features=tracks.features,
    )


def _describe(tracks: Tracks) -> dict[str, Any]:
    """What to record in the database beyond the graph itself.

    The feature keys matter as much as the scale: ``Tracks`` defaults its time
    attribute to "time", but every funtracks graph calls it "t", so a database
    reopened without them would be given the wrong FeatureDict.
    """
    features = tracks.features
    return {
        "scale": list(tracks.scale) if tracks.scale is not None else None,
        "ndim": tracks.ndim,
        "time_attr": features.time_key,
        "pos_attr": features.position_key,
        "tracklet_attr": features.tracklet_key,
        "lineage_attr": features.lineage_key,
    }


def _sniff_time_attr(graph: td.graph.BaseGraph) -> str:
    """Guess the time attribute of a database written by something else.

    funtracks graphs use "t"; "time" is the funtracks default and worth trying
    second so a graph built elsewhere still opens.
    """
    keys = graph.node_attr_keys()
    for candidate in ("t", "time"):
        if candidate in keys:
            return candidate
    return "t"


def _sniff_pos_attr(graph: td.graph.BaseGraph) -> str | list[str]:
    """Guess the position attribute(s) of a database written by something else.

    A single "pos" array is the funtracks convention; one column per axis is the
    other shape funtracks accepts, so fall back to whichever axis columns exist.
    """
    keys = graph.node_attr_keys()
    if "pos" in keys:
        return "pos"
    axes = [axis for axis in ("z", "y", "x") if axis in keys]
    return axes if axes else "pos"
