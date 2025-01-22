from pathlib import Path

import funlib.persistence as fp
import numpy as np


def convert_seg(seg: np.ndarray, save_loc: Path, scale=None, relabel=True):
    """Convert an in-memory segmentation into the motile tracker format. Includes
    relabeling to ensure unique labels across time and saving into a zarr.

    Args:
        seg (np.ndarray): _description_
        save_loc (Path): _description_
        scale (_type_, optional): _description_. Defaults to None.

    Raises:
        ValueError: _description_
    """
    if seg.ndim == 3:
        axis_names = ["t", "y", "x"]
        units = ["s", "", ""]
    elif seg.ndim == 4:
        axis_names = ["t", "z", "y", "x"]
        units = ["s", "", "", ""]
    else:
        raise ValueError(f"Segmentation must have 3 or 4 dimensions, found {seg.ndim}")

    arr = fp.prepare_ds(
        save_loc,
        shape=seg.shape,
        voxel_size=scale,
        axis_names=axis_names,
        units=units,
        dtype=seg.dtype,
    )
    curr_max = 0
    for idx in range(seg.shape[0]):
        frame = seg[idx]
        if relabel:
            frame[frame != 0] += curr_max
            curr_max = int(np.max(frame))
        arr[idx] = frame
