from geometry_pattern_query import GeometryPatternEngine, Pattern, Polygon, Scene
from geometry_pattern_query.dsl import parse_query
from geometry_pattern_query.features import extract_features, feature_distance


def test_polygon_feature_extraction() -> None:
    square = Polygon("square", [(0, 0), (2, 0), (2, 2), (0, 2)])
    features = extract_features(square)

    assert features.kind == "polygon"
    assert features.vertex_count == 4
    assert features.area == 4
    assert features.perimeter == 8
    assert features.aspect_ratio == 1


def test_feature_distance_prefers_similar_shapes() -> None:
    square = extract_features(Polygon("square", [(0, 0), (2, 0), (2, 2), (0, 2)]))
    rectangle = extract_features(Polygon("rect", [(0, 0), (4, 0), (4, 2), (0, 2)]))
    triangle = extract_features(Polygon("tri", [(0, 0), (2, 0), (1, 3)]))

    assert feature_distance(square, rectangle) < feature_distance(square, triangle)


def test_dsl_query_matches_scene_relation() -> None:
    scene = Scene(
        id="demo",
        objects=(
            Polygon("body", [(0, 0), (6, 0), (6, 4), (0, 4)], tags=frozenset({"wall"})),
            Polygon("roof", [(-0.5, 4), (3, 7), (6.5, 4)], tags=frozenset({"roof"})),
        ),
    )
    pattern = parse_query(
        "object roof kind=polygon tag=roof max_vertices=3; "
        "object body kind=polygon tag=wall; "
        "relation roof above body tolerance=0.5 min_strength=0.8",
        pattern_id="roof_on_body",
    )

    engine = GeometryPatternEngine()
    engine.add_pattern(pattern)
    matches = engine.match(scene, "roof_on_body", min_score=0.9)

    assert matches
    assert matches[0].bindings == {"roof": "roof", "body": "body"}


def test_json_pattern_with_three_bindings() -> None:
    scene = Scene(
        id="demo",
        objects=(
            Polygon("body", [(0, 0), (6, 0), (6, 4), (0, 4)], tags=frozenset({"wall"})),
            Polygon("roof", [(-0.5, 4), (3, 7), (6.5, 4)], tags=frozenset({"roof"})),
            Polygon("door", [(2.5, 0), (3.5, 0), (3.5, 2), (2.5, 2)], tags=frozenset({"door"})),
        ),
    )
    pattern = Pattern.from_dict(
        {
            "id": "facade",
            "objects": [
                {"alias": "body", "kind": "polygon", "tags_all": ["wall"]},
                {"alias": "roof", "kind": "polygon", "tags_all": ["roof"]},
                {"alias": "door", "kind": "polygon", "tags_all": ["door"]},
            ],
            "constraints": [
                {"source": "roof", "relation": "above", "target": "body", "tolerance": 0.5},
                {"source": "door", "relation": "contains_centroid", "target": "body", "min_strength": 1.0},
            ],
        }
    )

    engine = GeometryPatternEngine()
    engine.add_pattern(pattern)
    matches = engine.match(scene, "facade", min_score=0.9)

    assert len(matches) == 1
    assert matches[0].bindings["door"] == "door"
