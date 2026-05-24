from __future__ import annotations

from dataclasses import dataclass, field
from math import atan2, hypot
from typing import Any, Iterable, Literal

PointTuple = tuple[float, float]
GeometryKind = Literal["point", "polyline", "polygon"]


def _as_point_tuple(value: Iterable[float]) -> PointTuple:
    x, y = value
    return float(x), float(y)


def distance(a: PointTuple, b: PointTuple) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def polygon_area(points: list[PointTuple]) -> float:
    if len(points) < 3:
        return 0.0
    total = 0.0
    for i, current in enumerate(points):
        nxt = points[(i + 1) % len(points)]
        total += current[0] * nxt[1] - nxt[0] * current[1]
    return abs(total) / 2.0


def path_length(points: list[PointTuple], closed: bool = False) -> float:
    if len(points) < 2:
        return 0.0
    total = sum(distance(points[i], points[i + 1]) for i in range(len(points) - 1))
    if closed:
        total += distance(points[-1], points[0])
    return total


def bbox(points: list[PointTuple]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def centroid(points: list[PointTuple], closed_polygon: bool = False) -> PointTuple:
    if not points:
        return 0.0, 0.0
    if not closed_polygon or len(points) < 3:
        return (
            sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points),
        )

    signed_area = 0.0
    cx = 0.0
    cy = 0.0
    for i, current in enumerate(points):
        nxt = points[(i + 1) % len(points)]
        cross = current[0] * nxt[1] - nxt[0] * current[1]
        signed_area += cross
        cx += (current[0] + nxt[0]) * cross
        cy += (current[1] + nxt[1]) * cross
    signed_area *= 0.5
    if abs(signed_area) < 1e-12:
        return centroid(points)
    return cx / (6.0 * signed_area), cy / (6.0 * signed_area)


def angle_signature(points: list[PointTuple], closed: bool) -> list[float]:
    if len(points) < 3:
        return []
    indexes = range(len(points)) if closed else range(1, len(points) - 1)
    signature: list[float] = []
    for idx in indexes:
        point = points[idx]
        prev_point = points[idx - 1]
        next_point = points[(idx + 1) % len(points)]
        a1 = atan2(prev_point[1] - point[1], prev_point[0] - point[0])
        a2 = atan2(next_point[1] - point[1], next_point[0] - point[0])
        angle = abs(a2 - a1)
        if angle > 3.141592653589793:
            angle = 6.283185307179586 - angle
        signature.append(round(angle / 3.141592653589793, 6))
    return signature


@dataclass(frozen=True)
class GeometryObject:
    id: str
    kind: GeometryKind
    coordinates: tuple[PointTuple, ...]
    tags: frozenset[str] = field(default_factory=frozenset)
    properties: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeometryObject":
        kind = data["kind"]
        coords = tuple(_as_point_tuple(point) for point in data["coordinates"])
        tags = frozenset(data.get("tags", []))
        return cls(
            id=str(data["id"]),
            kind=kind,
            coordinates=coords,
            tags=tags,
            properties=dict(data.get("properties", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "coordinates": [list(point) for point in self.coordinates],
            "tags": sorted(self.tags),
            "properties": self.properties,
        }

    @property
    def points(self) -> list[PointTuple]:
        return list(self.coordinates)

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return bbox(self.points)

    @property
    def centroid(self) -> PointTuple:
        return centroid(self.points, closed_polygon=self.kind == "polygon")


class Point(GeometryObject):
    def __init__(self, id: str, x: float, y: float, **kwargs: Any) -> None:
        super().__init__(id=id, kind="point", coordinates=((float(x), float(y)),), **kwargs)


class Polyline(GeometryObject):
    def __init__(self, id: str, coordinates: Iterable[Iterable[float]], **kwargs: Any) -> None:
        super().__init__(
            id=id,
            kind="polyline",
            coordinates=tuple(_as_point_tuple(point) for point in coordinates),
            **kwargs,
        )


class Polygon(GeometryObject):
    def __init__(self, id: str, coordinates: Iterable[Iterable[float]], **kwargs: Any) -> None:
        super().__init__(
            id=id,
            kind="polygon",
            coordinates=tuple(_as_point_tuple(point) for point in coordinates),
            **kwargs,
        )


@dataclass(frozen=True)
class Scene:
    id: str
    objects: tuple[GeometryObject, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scene":
        return cls(
            id=str(data["id"]),
            objects=tuple(GeometryObject.from_dict(item) for item in data.get("objects", [])),
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "objects": [obj.to_dict() for obj in self.objects],
            "metadata": self.metadata,
        }
