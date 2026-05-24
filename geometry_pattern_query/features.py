from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from .geometry import GeometryObject, angle_signature, path_length, polygon_area


@dataclass(frozen=True)
class FeatureVector:
    kind: str
    vertex_count: int
    width: float
    height: float
    aspect_ratio: float
    area: float
    perimeter: float
    compactness: float
    convexity_hint: float
    normalized_edges: tuple[float, ...]
    angle_signature: tuple[float, ...]
    tags: frozenset[str]

    def numeric(self) -> tuple[float, ...]:
        return (
            float(self.vertex_count),
            self.aspect_ratio,
            self.area,
            self.perimeter,
            self.compactness,
            self.convexity_hint,
            *self.normalized_edges,
            *self.angle_signature,
        )


def extract_features(obj: GeometryObject) -> FeatureVector:
    points = obj.points
    min_x, min_y, max_x, max_y = obj.bbox
    width = max(max_x - min_x, 0.0)
    height = max(max_y - min_y, 0.0)
    aspect_ratio = width / height if height > 1e-12 else (width if width else 1.0)

    if obj.kind == "polygon":
        area = polygon_area(points)
        perimeter = path_length(points, closed=True)
        closed = True
    elif obj.kind == "polyline":
        area = 0.0
        perimeter = path_length(points)
        closed = False
    else:
        area = 0.0
        perimeter = 0.0
        closed = False

    compactness = 0.0
    if obj.kind == "polygon" and perimeter > 1e-12:
        compactness = (4.0 * 3.141592653589793 * area) / (perimeter * perimeter)

    bbox_area = width * height
    convexity_hint = area / bbox_area if bbox_area > 1e-12 else 0.0

    edge_lengths = []
    if len(points) >= 2:
        limit = len(points) if closed else len(points) - 1
        for idx in range(limit):
            start = points[idx]
            end = points[(idx + 1) % len(points)]
            edge_lengths.append(((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2) ** 0.5)
    norm = sqrt(sum(edge * edge for edge in edge_lengths)) or 1.0
    normalized_edges = tuple(round(edge / norm, 6) for edge in edge_lengths[:16])

    return FeatureVector(
        kind=obj.kind,
        vertex_count=len(points),
        width=width,
        height=height,
        aspect_ratio=round(aspect_ratio, 6),
        area=round(area, 6),
        perimeter=round(perimeter, 6),
        compactness=round(compactness, 6),
        convexity_hint=round(convexity_hint, 6),
        normalized_edges=normalized_edges,
        angle_signature=tuple(angle_signature(points, closed=closed)[:16]),
        tags=obj.tags,
    )


def feature_distance(left: FeatureVector, right: FeatureVector) -> float:
    if left.kind != right.kind:
        return 1.0

    common_tags = len(left.tags & right.tags)
    tag_penalty = 0.0
    if left.tags or right.tags:
        tag_penalty = 1.0 - (common_tags / max(len(left.tags | right.tags), 1))

    vertex_penalty = min(abs(left.vertex_count - right.vertex_count) / max(left.vertex_count, right.vertex_count, 1), 1.0)
    aspect_penalty = _relative_difference(left.aspect_ratio, right.aspect_ratio)
    compact_penalty = abs(left.compactness - right.compactness)
    convexity_penalty = abs(left.convexity_hint - right.convexity_hint)
    edge_penalty = _sequence_distance(left.normalized_edges, right.normalized_edges)
    angle_penalty = _sequence_distance(left.angle_signature, right.angle_signature)

    return min(
        1.0,
        (0.20 * vertex_penalty)
        + (0.20 * aspect_penalty)
        + (0.15 * compact_penalty)
        + (0.10 * convexity_penalty)
        + (0.15 * edge_penalty)
        + (0.15 * angle_penalty)
        + (0.05 * tag_penalty),
    )


def _relative_difference(left: float, right: float) -> float:
    scale = max(abs(left), abs(right), 1e-9)
    return min(abs(left - right) / scale, 1.0)


def _sequence_distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if not left and not right:
        return 0.0
    size = max(len(left), len(right))
    total = 0.0
    for idx in range(size):
        total += abs((left[idx] if idx < len(left) else 0.0) - (right[idx] if idx < len(right) else 0.0))
    return min(total / size, 1.0)
