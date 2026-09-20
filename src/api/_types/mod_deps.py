"""Factorio mod dependency parsing and graph resolution.

Dependency strings come from a release's ``info_json.dependencies``, e.g.
``"base"``, ``"? optional-mod"``, ``"! incompatible-mod"``,
``"~ no-load-order-mod"``, ``"some-mod >= 1.2.0"``. See the mod portal /
``info.json`` spec: a leading ``!`` marks an incompatibility, a leading ``?``
or ``(?)`` marks an optional dependency, and a leading ``~`` marks a required
dependency with no load-order constraint. No prefix also means required.
"""

from __future__ import annotations

import re

_DEPENDENCY_RE = re.compile(
    r"^(?P<prefix>!|\?|\(\?\)|~)?\s*(?P<name>[^<>=]+?)\s*(?:[<>=]+\s*[\d.]+)?$",
)


def parse_dependency(raw: str) -> tuple[str, str] | None:
    """Classify one dependency string as ``("required" | "optional" | "incompatible", mod_name)``.

    Returns ``None`` for a string we can't parse -- callers should treat that
    as "don't act on it" rather than guessing.
    """
    match = _DEPENDENCY_RE.match(raw.strip())
    if not match:
        return None
    name = match.group("name").strip()
    if not name:
        return None
    prefix = match.group("prefix")
    if prefix == "!":
        return ("incompatible", name)
    if prefix in ("?", "(?)"):
        return ("optional", name)
    return ("required", name)


def required_dependency_names(dependencies: list[str]) -> set[str]:
    """Hard-required dependency names from a release's dependency list.

    Excludes ``base``/``core``, which every mod effectively requires and which
    the app always treats as present, so they'd otherwise show up as a
    "dependency" of nearly every mod without meaning anything actionable.
    """
    names: set[str] = set()
    for raw in dependencies:
        parsed = parse_dependency(raw)
        if parsed and parsed[0] == "required" and parsed[1] not in ("base", "core"):
            names.add(parsed[1])
    return names


def closure(start: str, graph: dict[str, set[str]]) -> set[str]:
    """The set of names reachable from ``start`` (inclusive) by following ``graph`` edges."""
    seen = {start}
    stack = [start]
    while stack:
        current = stack.pop()
        for neighbor in graph.get(current, ()):
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen


def reverse_graph(graph: dict[str, set[str]]) -> dict[str, set[str]]:
    """Flip a ``{mod: required_by_mod}`` graph into ``{mod: mods_that_require_it}``."""
    reversed_graph: dict[str, set[str]] = {name: set() for name in graph}
    for name, deps in graph.items():
        for dep in deps:
            reversed_graph.setdefault(dep, set()).add(name)
    return reversed_graph
