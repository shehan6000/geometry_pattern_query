from __future__ import annotations

from .patterns import Pattern, PatternConstraint, PatternObject


def parse_query(query: str, pattern_id: str = "ad_hoc") -> Pattern:
    """Parse a compact geometry-pattern query.

    Syntax:

    object alias kind=polygon tag=door min_vertices=4;
    object handle kind=polyline;
    relation handle near door tolerance=2 min_strength=0.8;
    """
    objects: list[PatternObject] = []
    constraints: list[PatternConstraint] = []

    for raw_statement in query.split(";"):
        statement = raw_statement.strip()
        if not statement:
            continue
        parts = statement.split()
        if parts[0] == "object":
            objects.append(_parse_object(parts))
        elif parts[0] == "relation":
            constraints.append(_parse_relation(parts))
        else:
            raise ValueError(f"Unknown query statement: {statement}")

    return Pattern(id=pattern_id, objects=tuple(objects), constraints=tuple(constraints))


def _parse_object(parts: list[str]) -> PatternObject:
    if len(parts) < 2:
        raise ValueError("object statement requires an alias")
    alias = parts[1]
    values = _key_values(parts[2:])
    tags_all = set(values.pop("tags_all", "").split(",")) if "tags_all" in values else set()
    tags_any = set(values.pop("tags_any", "").split(",")) if "tags_any" in values else set()
    if "tag" in values:
        tags_all.add(values.pop("tag"))
    return PatternObject(
        alias=alias,
        kind=values.get("kind"),
        tags_all=frozenset(tag for tag in tags_all if tag),
        tags_any=frozenset(tag for tag in tags_any if tag),
        min_vertices=_optional_int(values.get("min_vertices")),
        max_vertices=_optional_int(values.get("max_vertices")),
        min_area=_optional_float(values.get("min_area")),
        max_area=_optional_float(values.get("max_area")),
        min_aspect_ratio=_optional_float(values.get("min_aspect_ratio")),
        max_aspect_ratio=_optional_float(values.get("max_aspect_ratio")),
    )


def _parse_relation(parts: list[str]) -> PatternConstraint:
    if len(parts) < 4:
        raise ValueError("relation statement requires source, relation, and target")
    values = _key_values(parts[4:])
    return PatternConstraint(
        source=parts[1],
        relation=parts[2],
        target=parts[3],
        tolerance=float(values.get("tolerance", 1.0)),
        min_strength=float(values.get("min_strength", 0.75)),
    )


def _key_values(parts: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for part in parts:
        if "=" not in part:
            raise ValueError(f"Expected key=value token, got {part}")
        key, value = part.split("=", 1)
        values[key] = value
    return values


def _optional_int(value: str | None) -> int | None:
    return int(value) if value is not None else None


def _optional_float(value: str | None) -> float | None:
    return float(value) if value is not None else None
