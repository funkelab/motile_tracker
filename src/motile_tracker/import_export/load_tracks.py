import ast

import networkx as nx
import numpy as np
import pandas as pd
from motile_toolbox.candidate_graph import NodeAttr

from motile_tracker.data_model import SolutionTracks


def ensure_integer_ids(df):
    """Ensure that the 'id' column in the dataframe contains integer values"""

    if not pd.api.types.is_integer_dtype(df["id"]):
        unique_ids = df["id"].unique()
        id_mapping = {
            original_id: new_id
            for new_id, original_id in enumerate(unique_ids, start=1)
        }
        df["id"] = df["id"].map(id_mapping)
        df["parent_id"] = df["parent_id"].map(id_mapping).astype(pd.Int64Dtype())

    return df


def ensure_correct_labels(df, segmentation):
    """create a new segmentation image where the values from the column df['seg_id'] are replaced by those in df['id']"""

    # Create a new segmentation image
    new_segmentation = np.zeros_like(segmentation)

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


def _test_valid(df: pd.DataFrame, segmentation: np.ndarray, scale: list[float]) -> bool:
    """Test if the segmentation pixel value for the coordinates of first node corresponds
    with the provided seg_id as a basic sanity check that the csv file matches with the
    segmentation file
    """
    if NodeAttr.SEG_ID.value not in df.columns:
        print("No SEG_ID was provided")
        return False

    if segmentation.ndim != len(scale):
        print(
            "Dimensions of the segmentation image do not match the number of scale values given"
        )
        return False

    row = df.iloc[0]
    pos = (
        [row[NodeAttr.TIME.value], row["z"], row["y"], row["x"]]
        if "z" in df.columns
        else [row[NodeAttr.TIME.value], row["y"], row["x"]]
    )

    if segmentation.ndim != len(pos):
        print(
            "Dimensions of the segmentation do not match with the number of positional dimensions"
        )
        return False

    seg_id = row[NodeAttr.SEG_ID.value]
    coordinates = [
        int(coord / scale_value) for coord, scale_value in zip(pos, scale, strict=True)
    ]

    try:
        value = segmentation[tuple(coordinates)]
    except IndexError:
        return False

    return value == seg_id


def tracks_from_df(
    df: pd.DataFrame,
    segmentation: np.ndarray | None = None,
    scale: list[float] | None = None,
    measurements: list[str] | None = (),
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
            The scale of the segmentation (including the time dimension). Defaults to None.
        measurements (list[str] | None, optional)
            The list of measurement attributes (area, volume) to compute (
            if they were not provided by the dataframe already). Defaults to None.

    Returns:
        SolutionTracks: a solution tracks object
    Raises:
        ValueError: if the segmentation IDs in the dataframe do not match the provided
            segmentation
    """

    required_columns = ["id", NodeAttr.TIME.value, "y", "x", "parent_id"]
    for column in required_columns:
        assert (
            column in df.columns
        ), f"Required column {column} not found in dataframe columns {df.columns}"

    if segmentation is not None and not _test_valid(df, segmentation, scale):
        raise ValueError(
            "Segmentation ids in dataframe do not match values in segmentation. Is it possible that you loaded the wrong combination of csv file and segmentation, or that the scaling information you provided is incorrect?"
        )
    if not df["id"].is_unique:
        raise ValueError("The 'id' column must contain unique values")

    df = df.map(lambda x: None if pd.isna(x) else x)  # Convert NaN values to None

    # Convert custom attributes stored as strings back to lists
    for col in df.columns:
        if col not in [
            NodeAttr.TIME.value,
            "z",
            "y",
            "x",
            "id",
            "parent_id",
            NodeAttr.SEG_ID.value,
        ]:
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
            del row_dict["z"]
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
            attrs[NodeAttr.TRACK_ID.value] = row["track_id"]

        # add the node to the graph
        graph.add_node(_id, **attrs)

        # add the edge to the graph, if the node has a parent
        # note: this loading format does not support edge attributes
        if not pd.isna(parent_id) and parent_id != -1:
            assert (
                parent_id in graph.nodes
            ), f"Parent id {parent_id} of node {_id} not in graph yet"
            graph.add_edge(parent_id, _id)

    if segmentation is not None and row["seg_id"] != row["id"]:
        segmentation = ensure_correct_labels(
            df, segmentation
        )  # in the case a different column than the id column was used for the seg_id, we need to update the segmentation to make sure it matches the values in the id column (it should be checked by now that these are unique and integers)

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
        and len(measurements) > 0
    ):
        nodes = tracks.graph.nodes
        times = tracks.get_times(nodes)
        computed_attrs = tracks._compute_node_attrs(nodes, times)
        areas = computed_attrs[NodeAttr.AREA.value]
        tracks._set_nodes_attr(nodes, NodeAttr.AREA.value, areas)

    return tracks
