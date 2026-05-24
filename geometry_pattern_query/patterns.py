from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .features import FeatureVector
from .relations import RelationName


@dataclass(frozen=True)
class PatternObject:
    alias: str
    kind: str | None = None
    tags_any: frozenset[str] = field(default_factory=frozenset)
    tags_all: frozenset[str] = field(default_factory=frozenset)
    min_vertices: int | None = None
    max_vertices: int | None = None
    min_area: float | None = None
    max_area: float | None = None
    min_aspect_ratio: float | None = None
    max_aspect_ratio: float | None = None
    reference_features: FeatureVector | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatternObject":
        return cls(
            alias=str(data["alias"]),
            kind=data.get("kind"),
            tags_any=frozenset(data.get("tags_any", [])),
            tags_all=frozenset(data.get("tags_all", [])),
            min_vertices=data.get("min_vertices"),
            max_vertices=data.get("max_vertices"),
            min_area=data.get("min_area"),
            max_area=data.get("max_area"),
            min_aspect_ratio=data.get("min_aspect_ratio"),
            max_aspect_ratio=data.get("max_aspect_ratio"),
        )


@dataclass(frozen=True)
class PatternConstraint:
    source: str
    relation: RelationName
    target: str
    tolerance: float = 1.0
    min_strength: float = 0.75

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatternConstraint":
        return cls(
            source=str(data["source"]),
            relation=data["relation"],
            target=str(data["target"]),
            tolerance=float(data.get("tolerance", 1.0)),
            min_strength=float(data.get("min_strength", 0.75)),
        )


@dataclass(frozen=True)
class Pattern:
    id: str
    objects: tuple[PatternObject, ...]
    constraints: tuple[PatternConstraint, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Pattern":
        return cls(
            id=str(data["id"]),
            objects=tuple(PatternObject.from_dict(item) for item in data.get("objects", [])),
            constraints=tuple(PatternConstraint.from_dict(item) for item in data.get("constraints", [])),
            metadata=dict(data.get("metadata", {})),
        )
