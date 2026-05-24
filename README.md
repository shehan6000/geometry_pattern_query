# Geometry Pattern Query

An advanced Python query system that finds geometry patterns inside 2D scenes. It can match by object geometry, tags, shape features, and spatial relations such as `near`, `above`, `left_of`, `overlaps_bbox`, and `contains_centroid`.

## What It Does

- Stores scene objects as points, polylines, and polygons.
- Extracts invariant-ish features: vertex count, area, perimeter, aspect ratio, compactness, normalized edge lengths, and angle signatures.
- Defines patterns with named aliases and spatial constraints.
- Returns ranked matches with bindings from pattern aliases to scene object IDs.
- Supports JSON pattern files and a compact inline query DSL.

## Quick Start

Run the example from this folder:

```powershell
python -m geometry_pattern_query.cli --scenes examples/scene_house.json --pattern examples/pattern_house.json --min-score 0.8
```

Inline query example:

```powershell
python -m geometry_pattern_query.cli --scenes examples/scene_house.json --query "object roof kind=polygon tag=roof max_vertices=3; object body kind=polygon tag=wall; relation roof above body tolerance=0.5 min_strength=0.8"
```

## Python API

```python
from geometry_pattern_query import GeometryPatternEngine, Pattern, Scene

scene = Scene.from_dict({...})
pattern = Pattern.from_dict({...})

engine = GeometryPatternEngine()
engine.add_pattern(pattern)
matches = engine.match(scene, "my_pattern", min_score=0.75)
```

## Pattern JSON

```json
{
  "id": "house_facade",
  "objects": [
    {"alias": "body", "kind": "polygon", "tags_all": ["wall"]},
    {"alias": "roof", "kind": "polygon", "tags_all": ["roof"], "max_vertices": 3}
  ],
  "constraints": [
    {"source": "roof", "relation": "above", "target": "body", "tolerance": 0.5}
  ]
}
```

## Scene JSON

```json
{
  "id": "scene_1",
  "objects": [
    {"id": "a", "kind": "polygon", "coordinates": [[0, 0], [4, 0], [4, 2], [0, 2]], "tags": ["wall"]}
  ]
}
```

## Design Notes

The engine separates three layers:

1. Geometry primitives and feature extraction.
2. Pattern constraints and spatial topology.
3. Ranked matching and query execution.

That makes it easy to extend with stronger geometry libraries later, such as Shapely or PostGIS, without changing the pattern API.
