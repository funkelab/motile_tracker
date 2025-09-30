import ast
from warnings import warn

import networkx as nx
import numpy as np
import pandas as pd
from funtracks.data_model import SolutionTracks

from motile_tracker.data_views.graph_attributes import NodeAttr


def ensure_integer_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure that the 'id' column in the dataframe contains integer values

    Args:
        df (pd.DataFrame): A pandas dataframe with a columns named "id" and "parent_id"

    Returns:
        pd.DataFrame: The same dataframe with the ids remapped to be unique integers.
            Parent id column is also remapped.
    """
    if not pd.api.types.is_integer_dtype(df["id"]):
        unique_ids = df["id"].unique()
        id_mapping = {
            original_id: new_id
            for new_id, original_id in enumerate(unique_ids, start=1)
        }
        df["id"] = df["id"].map(id_mapping)
        df["parent_id"] = df["parent_id"].map(id_mapping).astype(pd.Int64Dtype())

    return df


def ensure_correct_labels(df: pd.DataFrame, segmentation: np.ndarray) -> np.ndarray:
    """Create a new segmentation where the values from the column df['seg_id'] are
    replaced by those in df['id']

    Args:
        df (pd.DataFrame): A pandas dataframe with columns "seg_id" and "id" where
            the "id" column contains unique integers
        segmentation (np.ndarray): A numpy array where segmentation label values
            are recorded in the "seg_id" column of the dataframe

    Returns:
        np.ndarray: A numpy array similar to the input segmentation of dtype uint64
            where each segmentation now has a unique label across time that corresponds
            to the ID of each node
    """

    # Create a new segmentation image
    new_segmentation = np.zeros_like(segmentation).astype(np.uint64)

    # Loop through each time point
    for t in df[NodeAttr.TIME.value].unique():
        # Filter the dataframe for the current time point
        df_t = df[df[NodeAttr.TIME.value] == t]

        # Create a mapping from seg_id to id for the current time point
        seg_id_to_id = dict(zip(df_t["seg_id"], df_t["id"], strict=True))

        # Apply the mapping to the segmentation image for the current time point
        for seg_id, new_id in seg_id_to_id.items():
            new_segmentation[t][segmentation[t] == seg_id] = new_id

    return new_segmentation


def _test_valid(
    df: pd.DataFrame, segmentation: np.ndarray, scale: list[float] | None
) -> bool:
    """Test if the provided segmentation, dataframe, and scale values are valid together.
    Tests the following requirements:
      - The scale, if provided, has same dimensions as the segmentation
      - The location coordinates have the same dimensions as the segmentation
      - The segmentation pixel value for the coordinates of first node corresponds
    with the provided seg_id as a basic sanity check that the csv file matches with the
    segmentation file

    Args:
        df (pd.DataFrame): the pandas dataframe to turn into tracks, with standardized
            column names
        segmentation (np.ndarray): The segmentation, a 3D or 4D array of integer labels
        scale (list[float] | None): A list of floats representing the relationship between
            the point coordinates and the pixels in the segmentation

    Returns:
        bool: True if the combination of segmentation, dataframe, and scale
            pass all validity tests and can likely be loaded, and False otherwise
    """
    if scale is not None:
        if segmentation.ndim != len(scale):
            warn(
                f"Dimensions of the segmentation image ({segmentation.ndim}) "
                f"do not match the number of scale values given ({len(scale)})",
                stacklevel=2,
            )
            return False
    else:
        scale = [
            1,
        ] * segmentation.ndim

    row = df.iloc[0]
    pos = (
        [row[NodeAttr.TIME.value], row["z"], row["y"], row["x"]]
        if "z" in df.columns
        else [row[NodeAttr.TIME.value], row["y"], row["x"]]
    )

    if segmentation.ndim != len(pos):
        warn(
            f"Dimensions of the segmentation ({segmentation.ndim}) do not match the "
            f"number of positional dimensions ({len(pos)})",
            stacklevel=2,
        )
        return False

    seg_id = row[NodeAttr.SEG_ID.value]
    coordinates = [
        int(coord / scale_value) for coord, scale_value in zip(pos, scale, strict=True)
    ]

    try:
        value = segmentation[tuple(coordinates)]
    except IndexError:
        warn(
            f"Could not get the segmentation value at index {coordinates}", stacklevel=2
        )
        return False

    return value == seg_id


def tracks_from_df(
    df: pd.DataFrame,
    segmentation: np.ndarray | None = None,
    scale: list[float] | None = None,
    features: dict[str, str] | None = None,
) -> SolutionTracks:
    """Turns a pandas data frame with columns:
        t,[z],y,x,id,parent_id,[seg_id], [optional custom attr 1], ...
    into a SolutionTracks object.

    Cells without a parent_id will have an empty string or a -1 for the parent_id.

    Args:
        df (pd.DataFrame):
            a pandas DataFrame containing columns
            t,[z],y,x,id,parent_id,[seg_id], [optional custom attr 1], ...
        segmentation (np.ndarray | None, optional):
            An optional accompanying segmentation.
            If provided, assumes that the seg_id column in the dataframe exists and
            corresponds to the label ids in the segmentation array. Defaults to None.
        scale (list[float] | None, optional):
            The scale of the segmentation (including the time dimension). Defaults to
            None.
        features (dict[str: str] | None, optional)
            Dict mapping measurement attributes (area, volume) to value that specifies a
            column from which to import. If value equals to "Recompute", recompute these
            values instead of importing them from a column. Defaults to None.

    Returns:
        SolutionTracks: a solution tracks object
    Raises:
        ValueError: if the segmentation IDs in the dataframe do not match the provided
            segmentation
    """
    if features is None:
        features = {}
    # check that the required columns are present
    required_columns = ["id", NodeAttr.TIME.value, "y", "x", "parent_id"]
    ndim = None
    if segmentation is not None:
        required_columns.append("seg_id")
        ndim = segmentation.ndim
        if ndim == 4:
            required_columns.append("z")
    for column in required_columns:
        assert column in df.columns, (
            f"Required column {column} not found in dataframe columns {df.columns}"
        )

    if segmentation is not None and not _test_valid(df, segmentation, scale):
        raise ValueError(
            "Segmentation ids in dataframe do not match values in segmentation."
            "Is it possible that you loaded the wrong combination of csv file and "
            "segmentation, or that the scaling information you provided is incorrect?"
        )
    if not df["id"].is_unique:
        raise ValueError("The 'id' column must contain unique values")

    df = df.map(lambda x: None if pd.isna(x) else x)  # Convert NaN values to None

    # Convert custom attributes stored as strings back to lists
    for col in df.columns:
        if col not in required_columns:
            df[col] = df[col].apply(
                lambda x: ast.literal_eval(x)
                if isinstance(x, str) and x.startswith("[") and x.endswith("]")
                else x
            )

    df = df.sort_values(
        NodeAttr.TIME.value
    )  # sort the dataframe to ensure that parents get added to the graph before children
    df = ensure_integer_ids(df)  # Ensure that the 'id' column contains integer values

    graph = nx.DiGraph()
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        _id = int(row["id"])
        parent_id = row["parent_id"]
        if "z" in df.columns:
            pos = [row["z"], row["y"], row["x"]]
            ndims = 4
        else:
            pos = [row["y"], row["x"]]
            ndims = 3

        attrs = {
            NodeAttr.TIME.value: int(row["time"]),
            NodeAttr.POS.value: pos,
        }

        # add all other columns into the attributes
        for attr in required_columns:
            del row_dict[attr]
        attrs.update(row_dict)

        if "track_id" in df.columns:
            attrs[NodeAttr.TRACK_ID.value] = int(row["track_id"])

        # add the node to the graph
        graph.add_node(_id, **attrs)

        # add the edge to the graph, if the node has a parent
        # note: this loading format does not support edge attributes
        if not pd.isna(parent_id) and parent_id != -1:
            assert parent_id in graph.nodes, (
                f"Parent id {parent_id} of node {_id} not in graph yet"
            )
            graph.add_edge(parent_id, _id)

    # in the case a different column than the id column was used for the seg_id, we need
    # to update the segmentation to make sure it matches the values in the id column (it
    # should be checked by now that these are unique and integers)
    if segmentation is not None and row["seg_id"] != row["id"]:
        segmentation = ensure_correct_labels(df, segmentation)

    tracks = SolutionTracks(
        graph=graph,
        segmentation=segmentation,
        pos_attr=NodeAttr.POS.value,
        time_attr=NodeAttr.TIME.value,
        ndim=ndims,
        scale=scale,
    )

    # compute the 'area' attribute if needed
    if (
        tracks.segmentation is not None
        and NodeAttr.AREA.value not in df.columns
        and len(features) > 0
    ):
        nodes = tracks.graph.nodes
        times = tracks.get_times(nodes)
        computed_attrs = [
            tracks._compute_node_attrs(node, time)
            for node, time in zip(nodes, times, strict=False)
        ]
        areas = [attrs[NodeAttr.AREA.value] for attrs in computed_attrs]
        tracks._set_nodes_attr(nodes, NodeAttr.AREA.value, areas)

    return tracks
