"""Generic dataclass<->JSON value conversion, shared by the JSON-backed settings models.

Split out of :mod:`api._types.settings` purely to keep that module's top-level
definition count under Skylos's god-file threshold; this module has no
dependency on the Factorio schema itself.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, Union, get_args, get_origin, get_type_hints

_NONE_TYPE = type(None)

# Sentinel distinguishing "no container conversion applies" from a legitimate
# ``None``/falsy converted value.
_UNHANDLED = object()


def _convert_union(args: tuple[Any, ...], value: Any) -> Any:  # noqa: ANN401 - generic JSON decoding
    """Convert ``value`` for a ``Union``/``X | None`` type hint."""
    non_none = [a for a in args if a is not _NONE_TYPE]
    if value is None or len(non_none) != 1:
        return value
    return convert(non_none[0], value)


def _is_dataclass_sequence(origin: Any, args: tuple[Any, ...], value: Any) -> bool:  # noqa: ANN401
    """Whether ``type_hint`` is a ``list``/``set``/``tuple`` of a dataclass and ``value`` matches."""
    return origin in (list, set, tuple) and bool(args) and is_dataclass(args[0]) and isinstance(value, list)


def _is_dataclass_dict(origin: Any, args: tuple[Any, ...], value: Any) -> bool:  # noqa: ANN401
    """Whether ``type_hint`` is a ``dict`` with dataclass values and ``value`` matches."""
    return origin is dict and len(args) == 2 and is_dataclass(args[1]) and isinstance(value, dict)


def _convert_container(origin: Any, args: tuple[Any, ...], value: Any) -> Any:  # noqa: ANN401
    """Convert ``value`` for a dataclass-typed list/set/tuple/dict container.

    Returns :data:`_UNHANDLED` when ``origin``/``args``/``value`` don't describe
    one of those container shapes.
    """
    if _is_dataclass_sequence(origin, args, value):
        return [from_dict(args[0], item) for item in value]
    if _is_dataclass_dict(origin, args, value):
        return {key: from_dict(args[1], item) for key, item in value.items()}
    return _UNHANDLED


def convert(type_hint: Any, value: Any) -> Any:  # noqa: ANN401 - generic JSON decoding
    """Convert a raw JSON value into the dataclass type indicated by ``type_hint``."""
    origin = get_origin(type_hint)
    args = get_args(type_hint)
    if origin is Union:
        return _convert_union(args, value)
    if is_dataclass(type_hint) and isinstance(value, dict):
        return from_dict(type_hint, value)
    converted = _convert_container(origin, args, value)
    return value if converted is _UNHANDLED else converted


def from_dict(cls: Any, data: dict[str, Any]) -> Any:  # noqa: ANN401 - generic factory
    """Build a dataclass instance from ``data``, ignoring unknown keys."""
    hints = get_type_hints(cls)
    kwargs = {f.name: convert(hints[f.name], data[f.name]) for f in fields(cls) if f.name in data}
    return cls(**kwargs)


def drop_none(items: list[tuple[str, Any]]) -> dict[str, Any]:
    """``dict_factory`` that omits ``None`` values so output stays valid Factorio JSON."""
    return {key: value for key, value in items if value is not None}
