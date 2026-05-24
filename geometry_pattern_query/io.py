from __future__ import annotations

import json
from pathlib import Path

from .geometry import GeometryObject, Scene
from .patterns import Pattern


def load_scene(path: str | Path) -> Scene:
    with Path(path).open("r", encoding="utf-8") as handle:
        return Scene.from_dict(json.load(handle))


def load_scenes(path: str | Path) -> list[Scene]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [Scene.from_dict(item) for item in data]
    return [Scene.from_dict(data)]


def load_pattern(path: str | Path) -> Pattern:
    with Path(path).open("r", encoding="utf-8") as handle:
        return Pattern.from_dict(json.load(handle))


def load_reference_objects(path: str | Path) -> dict[str, GeometryObject]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(alias): GeometryObject.from_dict(item) for alias, item in data.items()}
