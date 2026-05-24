from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .features import FeatureVector, extract_features
from .geometry import GeometryObject, Scene
from .patterns import PatternObject


@dataclass(frozen=True)
class IndexedScene:
    scene: Scene
    features: dict[str, FeatureVector]
    by_kind: dict[str, tuple[str, ...]]
    by_tag: dict[str, tuple[str, ...]]

    @classmethod
    def build(cls, scene: Scene) -> "IndexedScene":
        features = {obj.id: extract_features(obj) for obj in scene.objects}
        by_kind: dict[str, list[str]] = defaultdict(list)
        by_tag: dict[str, list[str]] = defaultdict(list)
        for obj in scene.objects:
            by_kind[obj.kind].append(obj.id)
            for tag in obj.tags:
                by_tag[tag].append(obj.id)
        return cls(
            scene=scene,
            features=features,
            by_kind={key: tuple(value) for key, value in by_kind.items()},
            by_tag={key: tuple(value) for key, value in by_tag.items()},
        )

    def candidates_for(self, pattern_object: PatternObject) -> tuple[str, ...]:
        candidates = {obj.id for obj in self.scene.objects}
        if pattern_object.kind:
            candidates &= set(self.by_kind.get(pattern_object.kind, ()))
        for tag in pattern_object.tags_all:
            candidates &= set(self.by_tag.get(tag, ()))
        if pattern_object.tags_any:
            any_tag_ids = set()
            for tag in pattern_object.tags_any:
                any_tag_ids |= set(self.by_tag.get(tag, ()))
            candidates &= any_tag_ids
        return tuple(sorted(candidates))
