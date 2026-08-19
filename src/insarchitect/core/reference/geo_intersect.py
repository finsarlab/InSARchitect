import numpy as np


def get_geo_slice(attr: dict, lat_min: float, lat_max: float, lon_min: float, lon_max: float):
    """
    Given file's metadata and target bounding box,
    returns (row_slice, col_slice) to index into that file's array.
    """
    y_first = float(attr["Y_FIRST"])
    x_first = float(attr["X_FIRST"])
    y_step = float(attr["Y_STEP"])
    x_step = float(attr["X_STEP"])
    length = int(attr["LENGTH"])
    width = int(attr["WIDTH"])

    # convert coords to pixel indexes
    row_start = round((lat_max - y_first) / y_step) 
    row_end   = round((lat_min - y_first) / y_step) 
    col_start = round((lon_min - x_first) / x_step)
    col_end   = round((lon_max - x_first) / x_step)

    # clamp to valid array bounds
    row_start = max(0, min(row_start, length - 1))
    row_end   = max(0, min(row_end,   length))
    col_start = max(0, min(col_start, width - 1))
    col_end   = max(0, min(col_end,   width))

    return slice(row_start, row_end), slice(col_start, col_end)


def geographic_intersection(attr1: dict, attr2: dict) -> tuple[float, float, float, float] | None:
    """
    Computes the geographic intersection (lat/lon bounding box) of two files.
    Returns (lat_min, lat_max, lon_min, lon_max) or None if no overlap.
    """
    def bbox_from_attr(attr):
        y_first = float(attr["Y_FIRST"])
        x_first = float(attr["X_FIRST"])
        y_step  = float(attr["Y_STEP"])
        x_step  = float(attr["X_STEP"])
        length  = int(attr["LENGTH"])
        width   = int(attr["WIDTH"])
        y_last  = y_first + y_step * (length - 1)
        x_last  = x_first + x_step * (width  - 1)
        return (
            min(y_first, y_last),  # lat_min
            max(y_first, y_last),  # lat_max
            min(x_first, x_last),  # lon_min
            max(x_first, x_last),  # lon_max
        )

    lat_min1, lat_max1, lon_min1, lon_max1 = bbox_from_attr(attr1)
    lat_min2, lat_max2, lon_min2, lon_max2 = bbox_from_attr(attr2)

    # intersection
    lat_min = max(lat_min1, lat_min2)
    lat_max = min(lat_max1, lat_max2)
    lon_min = max(lon_min1, lon_min2)
    lon_max = min(lon_max1, lon_max2)

    if lat_min >= lat_max or lon_min >= lon_max:
        return None  # no spatial overlap

    return lat_min, lat_max, lon_min, lon_max