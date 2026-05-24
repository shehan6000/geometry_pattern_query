from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .geometry import GeometryObject, distance

RelationName = Literal["near", "left_of", "right_of", "above", "below", "overlaps_bbox", "contains_centroid"]


@dataclass(frozen=True)
class Relation:
    source_id: str
    target_id: str
    name: RelationName
    strength: float


def relation_strength(source: GeometryObject, target: GeometryObject, name: RelationName, tolerance: float) -> float:
    sx, sy = source.centroid
    tx, ty = target.centroid
    if name == "near":
        gap = distance((sx, sy), (tx, ty))
        return 1.0 if gap <= tolerance else max(0.0, 1.0 - ((gap - tolerance) / max(tolerance, 1e-9)))
    if name == "left_of":
        return _ordered_strength(sx, tx, tolerance)
    if name == "right_of":
        return _ordered_strength(tx, sx, tolerance)
    if name == "above":
        return _ordered_strength(ty, sy, tolerance)
    if name == "below":
        return _ordered_strength(sy, ty, tolerance)
    if name == "overlaps_bbox":
        return 1.0 if _bbox_overlap(source.bbox, target.bbox) else 0.0
    if name == "contains_centroid":
        return 1.0 if _point_in_bbox(target.centroid, source.bbox) else 0.0
    raise ValueError(f"Unknown relation: {name}")


def _ordered_strength(before: float, after: float, tolerance: float) -> float:
    if before <= after:
        return 1.0
    return max(0.0, 1.0 - ((before - after) / max(tolerance, 1e-9)))


def _bbox_overlap(left: tuple[float, float, float, float], right: tuple[float, float, float, float]) -> bool:
    return not (left[2] < right[0] or right[2] < left[0] or left[3] < right[1] or right[3] < left[1])


def _point_in_bbox(point: tuple[float, float], box: tuple[float, float, float, float]) -> bool:
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]
