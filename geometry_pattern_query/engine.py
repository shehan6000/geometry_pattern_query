from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

from .features import FeatureVector, extract_features, feature_distance
from .geometry import GeometryObject, Scene
from .index import IndexedScene
from .patterns import Pattern, PatternObject
from .relations import relation_strength


@dataclass(frozen=True)
class MatchResult:
    pattern_id: str
    scene_id: str
    score: float
    bindings: dict[str, str]
    object_scores: dict[str, float]
    relation_scores: dict[str, float]


class GeometryPatternEngine:
    def __init__(self) -> None:
        self._patterns: dict[str, Pattern] = {}
        self._pattern_features: dict[tuple[str, str], FeatureVector | None] = {}

    def add_pattern(self, pattern: Pattern, references: dict[str, GeometryObject] | None = None) -> None:
        self._patterns[pattern.id] = pattern
        references = references or {}
        for pattern_object in pattern.objects:
            reference = references.get(pattern_object.alias)
            self._pattern_features[(pattern.id, pattern_object.alias)] = extract_features(reference) if reference else None

    def match(self, scene: Scene, pattern_id: str, limit: int = 10, min_score: float = 0.0) -> list[MatchResult]:
        pattern = self._patterns[pattern_id]
        index = IndexedScene.build(scene)
        candidates = [
            self._candidate_objects(pattern.id, pattern_object, index)
            for pattern_object in pattern.objects
        ]
        if any(not item for item in candidates):
            return []

        results: list[MatchResult] = []
        aliases = [obj.alias for obj in pattern.objects]
        for selected in _unique_assignments(candidates):
            bindings = dict(zip(aliases, selected))
            relation_scores = self._score_relations(pattern, scene, bindings)
            if relation_scores is None:
                continue
            object_scores = {
                alias: self._score_object(pattern.id, pattern.objects[idx], _scene_object(scene, object_id), index.features[object_id])
                for idx, (alias, object_id) in enumerate(bindings.items())
            }
            denominator = len(object_scores) + len(relation_scores)
            score = (sum(object_scores.values()) + sum(relation_scores.values())) / denominator
            if score >= min_score:
                results.append(
                    MatchResult(
                        pattern_id=pattern.id,
                        scene_id=scene.id,
                        score=round(score, 6),
                        bindings=bindings,
                        object_scores={key: round(value, 6) for key, value in object_scores.items()},
                        relation_scores={key: round(value, 6) for key, value in relation_scores.items()},
                    )
                )
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

    def query(self, scenes: list[Scene], pattern_id: str, limit: int = 10, min_score: float = 0.0) -> list[MatchResult]:
        results: list[MatchResult] = []
        for scene in scenes:
            results.extend(self.match(scene, pattern_id, limit=limit, min_score=min_score))
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]

    def _candidate_objects(
        self,
        pattern_id: str,
        pattern_object: PatternObject,
        index: IndexedScene,
    ) -> list[str]:
        scored = []
        for object_id in index.candidates_for(pattern_object):
            obj = _scene_object(index.scene, object_id)
            score = self._score_object(pattern_id, pattern_object, obj, index.features[obj.id])
            if score > 0:
                scored.append((obj.id, score))
        return [obj_id for obj_id, _ in sorted(scored, key=lambda item: item[1], reverse=True)]

    def _score_object(
        self,
        pattern_id: str,
        pattern_object: PatternObject,
        obj: GeometryObject,
        features: FeatureVector,
    ) -> float:
        if pattern_object.kind and obj.kind != pattern_object.kind:
            return 0.0
        if pattern_object.tags_all and not pattern_object.tags_all <= obj.tags:
            return 0.0
        if pattern_object.tags_any and not (pattern_object.tags_any & obj.tags):
            return 0.0
        if pattern_object.min_vertices is not None and features.vertex_count < pattern_object.min_vertices:
            return 0.0
        if pattern_object.max_vertices is not None and features.vertex_count > pattern_object.max_vertices:
            return 0.0
        if pattern_object.min_area is not None and features.area < pattern_object.min_area:
            return 0.0
        if pattern_object.max_area is not None and features.area > pattern_object.max_area:
            return 0.0
        if pattern_object.min_aspect_ratio is not None and features.aspect_ratio < pattern_object.min_aspect_ratio:
            return 0.0
        if pattern_object.max_aspect_ratio is not None and features.aspect_ratio > pattern_object.max_aspect_ratio:
            return 0.0

        reference = pattern_object.reference_features or self._pattern_features.get((pattern_id, pattern_object.alias))
        if reference is None:
            return 1.0
        return 1.0 - feature_distance(reference, features)

    def _score_relations(self, pattern: Pattern, scene: Scene, bindings: dict[str, str]) -> dict[str, float] | None:
        scores: dict[str, float] = {}
        for constraint in pattern.constraints:
            source = _scene_object(scene, bindings[constraint.source])
            target = _scene_object(scene, bindings[constraint.target])
            strength = relation_strength(source, target, constraint.relation, constraint.tolerance)
            if strength < constraint.min_strength:
                return None
            key = f"{constraint.source}.{constraint.relation}.{constraint.target}"
            scores[key] = strength
        return scores


def _scene_object(scene: Scene, object_id: str) -> GeometryObject:
    for obj in scene.objects:
        if obj.id == object_id:
            return obj
    raise KeyError(object_id)


def _unique_assignments(candidates: list[list[str]]) -> list[tuple[str, ...]]:
    if not candidates:
        return []
    flattened = sorted(set(item for group in candidates for item in group))
    allowed = [set(group) for group in candidates]
    assignments = []
    for selected in permutations(flattened, len(candidates)):
        if all(selected[idx] in allowed[idx] for idx in range(len(selected))):
            assignments.append(selected)
    return assignments
