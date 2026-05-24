"""Geometry pattern query engine.

The package exposes a small but practical system for storing geometric
patterns, extracting invariant features, and querying scenes by shape and
spatial relationships.
"""

from .engine import GeometryPatternEngine, MatchResult
from .geometry import GeometryObject, Point, Polygon, Polyline, Scene
from .patterns import Pattern, PatternConstraint, PatternObject

__all__ = [
    "GeometryPatternEngine",
    "GeometryObject",
    "MatchResult",
    "Pattern",
    "PatternConstraint",
    "PatternObject",
    "Point",
    "Polygon",
    "Polyline",
    "Scene",
]
