from __future__ import annotations

import argparse
import json

from .dsl import parse_query
from .engine import GeometryPatternEngine
from .io import load_pattern, load_reference_objects, load_scenes


def main() -> None:
    parser = argparse.ArgumentParser(description="Query geometry scenes for spatial patterns.")
    parser.add_argument("--scenes", required=True, help="JSON file containing one scene or a list of scenes.")
    parser.add_argument("--pattern", help="JSON pattern definition.")
    parser.add_argument("--query", help="Inline DSL query.")
    parser.add_argument("--references", help="Optional reference objects keyed by pattern alias.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--min-score", type=float, default=0.0)
    args = parser.parse_args()

    if not args.pattern and not args.query:
        parser.error("Provide --pattern or --query")

    pattern = load_pattern(args.pattern) if args.pattern else parse_query(args.query)
    references = load_reference_objects(args.references) if args.references else None
    scenes = load_scenes(args.scenes)

    engine = GeometryPatternEngine()
    engine.add_pattern(pattern, references=references)
    results = engine.query(scenes, pattern.id, limit=args.limit, min_score=args.min_score)
    print(json.dumps([_result_to_dict(item) for item in results], indent=2))


def _result_to_dict(result: object) -> dict[str, object]:
    return {
        "pattern_id": result.pattern_id,
        "scene_id": result.scene_id,
        "score": result.score,
        "bindings": result.bindings,
        "object_scores": result.object_scores,
        "relation_scores": result.relation_scores,
    }


if __name__ == "__main__":
    main()
