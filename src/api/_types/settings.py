"""Factorio 2.1 settings models (server-settings, map-gen-settings, map-settings).

The schema mirrors the canonical example files shipped with Factorio 2.1. Files
are read and written as JSON through confkit's parser interface
(:class:`api._types.json_parser.JsonParser`), giving us one consistent I/O path
for every per-server settings document.

Nested objects with keys that are not valid Python identifiers (e.g.
``"copper-ore"`` or ``"control:moisture:frequency"``) are modelled as ``dict``
fields so the exact Factorio key names are preserved on disk.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import TYPE_CHECKING, Any, Self, Union, cast, get_args, get_origin, get_type_hints

from api._types.json_parser import JsonParser

if TYPE_CHECKING:
    from pathlib import Path

    from _typeshed import DataclassInstance

_NONE_TYPE = type(None)


def _convert(type_hint: Any, value: Any) -> Any:  # noqa: ANN401 - generic JSON decoding
    """Convert a raw JSON value into the dataclass type indicated by ``type_hint``."""
    origin = get_origin(type_hint)
    args = get_args(type_hint)
    if origin is Union:
        non_none = [a for a in args if a is not _NONE_TYPE]
        if value is None or len(non_none) != 1:
            return value
        return _convert(non_none[0], value)
    if is_dataclass(type_hint) and isinstance(value, dict):
        return _from_dict(type_hint, value)
    if origin in (list, set, tuple) and args and is_dataclass(args[0]) and isinstance(value, list):
        return [_from_dict(args[0], item) for item in value]
    if origin is dict and len(args) == 2 and is_dataclass(args[1]) and isinstance(value, dict):
        return {key: _from_dict(args[1], item) for key, item in value.items()}
    return value


def _from_dict(cls: Any, data: dict[str, Any]) -> Any:  # noqa: ANN401 - generic factory
    """Build a dataclass instance from ``data``, ignoring unknown keys."""
    hints = get_type_hints(cls)
    kwargs = {f.name: _convert(hints[f.name], data[f.name]) for f in fields(cls) if f.name in data}
    return cls(**kwargs)


def _drop_none(items: list[tuple[str, Any]]) -> dict[str, Any]:
    """``dict_factory`` that omits ``None`` values so output stays valid Factorio JSON."""
    return {key: value for key, value in items if value is not None}


class JsonSettings:
    """Mixin giving dataclasses JSON read/write via the confkit JSON parser."""

    @classmethod
    def read(cls, file: Path) -> Self:
        parser = JsonParser()
        parser.read(file)
        return _from_dict(cls, parser.data)

    def write(self, file: Path) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        parser = JsonParser()
        parser.data = asdict(cast("DataclassInstance", self), dict_factory=_drop_none)
        with file.open("w", encoding="utf-8") as f:
            parser.write(f)


# --------------------------------------------------------------------------
# server-settings.json
# --------------------------------------------------------------------------
@dataclass
class Visibility:
    public: bool = True
    lan: bool = True


@dataclass
class ServerSettings(JsonSettings):
    name: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    max_players: int = 0
    visibility: Visibility = field(default_factory=Visibility)
    username: str = ""
    password: str = ""
    token: str = ""
    game_password: str = ""
    require_user_verification: bool = True
    max_upload_in_kilobytes_per_second: int = 0
    max_upload_slots: int = 5
    minimum_latency_in_ticks: int = 0
    max_heartbeats_per_second: int = 60
    ignore_player_limit_for_returning_players: bool = False
    allow_commands: str = "admins-only"
    autosave_interval: int = 10
    autosave_slots: int = 5
    afk_autokick_interval: int = 0
    auto_pause: bool = True
    auto_pause_when_players_connect: bool = False
    only_admins_can_pause_the_game: bool = True
    autosave_only_on_server: bool = True
    non_blocking_saving: bool = False
    minimum_segment_size: int = 25
    minimum_segment_size_peer_count: int = 20
    maximum_segment_size: int = 100
    maximum_segment_size_peer_count: int = 10


# --------------------------------------------------------------------------
# map-gen-settings.json
# --------------------------------------------------------------------------
@dataclass
class AutoplaceControl:
    frequency: float = 1
    size: float = 1
    richness: float | None = None


@dataclass
class CliffSettings:
    name: str = "cliff"
    cliff_elevation_0: float = 10
    cliff_elevation_interval: float = 40
    richness: float = 1


@dataclass
class Coordinates:
    x: float = 0
    y: float = 0


def _default_autoplace() -> dict[str, AutoplaceControl]:
    return {
        "coal": AutoplaceControl(1, 1, 1),
        "stone": AutoplaceControl(1, 1, 1),
        "copper-ore": AutoplaceControl(1, 1, 1),
        "iron-ore": AutoplaceControl(1, 1, 1),
        "uranium-ore": AutoplaceControl(1, 1, 1),
        "crude-oil": AutoplaceControl(1, 1, 1),
        "water": AutoplaceControl(1, 1),
        "trees": AutoplaceControl(1, 1),
        "enemy-base": AutoplaceControl(1, 1),
    }


def _default_property_expression_names() -> dict[str, str]:
    return {
        "control:moisture:frequency": "1",
        "control:moisture:bias": "0",
        "control:aux:frequency": "1",
        "control:aux:bias": "0",
    }


@dataclass
class MapGenerationSettings(JsonSettings):
    width: int = 0
    height: int = 0
    starting_area: float = 1
    peaceful_mode: bool = False
    autoplace_controls: dict[str, AutoplaceControl] = field(default_factory=_default_autoplace)
    cliff_settings: CliffSettings = field(default_factory=CliffSettings)
    property_expression_names: dict[str, str] = field(default_factory=_default_property_expression_names)
    starting_points: list[Coordinates] = field(default_factory=lambda: [Coordinates()])
    seed: int | None = None


# --------------------------------------------------------------------------
# map-settings.json
# --------------------------------------------------------------------------
@dataclass
class DifficultySettings:
    technology_price_multiplier: float = 1
    spoil_time_modifier: float = 1


@dataclass
class PollutionSettings:
    enabled: bool = True
    diffusion_ratio: float = 0.02
    min_to_diffuse: int = 15
    ageing: float = 1
    expected_max_per_chunk: int = 150
    min_to_show_per_chunk: int = 50
    min_pollution_to_damage_trees: int = 60
    pollution_with_max_forest_damage: int = 150
    pollution_per_tree_damage: int = 50
    pollution_restored_per_tree_damage: int = 10
    max_pollution_to_restore_trees: int = 20
    enemy_attack_pollution_consumption_modifier: float = 1


@dataclass
class EnemyEvolution:
    enabled: bool = True
    time_factor: float = 0.000004
    destroy_factor: float = 0.002
    pollution_factor: float = 0.0000009


@dataclass
class EnemyExpansion:
    enabled: bool = True
    max_expansion_distance: int = 5
    min_expansion_distance: int = 3
    friendly_base_influence_radius: int = 6
    enemy_building_influence_radius: int = 3
    building_coefficient: float = 0.5
    other_base_coefficient: float = 3.0
    neighbouring_chunk_coefficient: float = 0.5
    neighbouring_base_chunk_coefficient: float = 0.5
    max_colliding_tiles_coefficient: float = 0.8
    settler_group_min_size: int = 5
    settler_group_max_size: int = 20
    evolution_group_size_factor: float = 4.0
    min_expansion_cooldown: int = 14400
    max_expansion_cooldown: int = 216000


@dataclass
class UnitGroupSettings:
    min_group_gathering_time: int = 3600
    max_group_gathering_time: int = 36000
    max_wait_time_for_late_members: int = 7200
    max_group_radius: float = 30.0
    min_group_radius: float = 5.0
    max_member_speedup_when_behind: float = 1.4
    max_member_slowdown_when_ahead: float = 0.6
    max_group_slowdown_factor: float = 0.3
    max_group_member_fallback_factor: int = 3
    member_disown_distance: int = 10
    tick_tolerance_when_member_arrives: int = 60
    max_gathering_unit_groups: int = 30
    max_unit_group_size: int = 200


@dataclass
class PathFinderSettings:
    fwd2bwd_ratio: int = 5
    goal_pressure_ratio: int = 2
    max_steps_worked_per_tick: float = 1000
    max_work_done_per_tick: int = 8000
    use_path_cache: bool = True
    short_cache_size: int = 5
    long_cache_size: int = 25
    short_cache_min_cacheable_distance: float = 10
    short_cache_min_algo_steps_to_cache: int = 50
    long_cache_min_cacheable_distance: float = 30
    cache_max_connect_to_cache_steps_multiplier: int = 100
    cache_accept_path_start_distance_ratio: float = 0.2
    cache_accept_path_end_distance_ratio: float = 0.15
    negative_cache_accept_path_start_distance_ratio: float = 0.3
    negative_cache_accept_path_end_distance_ratio: float = 0.3
    cache_path_start_distance_rating_multiplier: int = 10
    cache_path_end_distance_rating_multiplier: int = 20
    stale_enemy_with_same_destination_collision_penalty: int = 30
    ignore_moving_enemy_collision_distance: float = 5
    enemy_with_different_destination_collision_penalty: int = 30
    general_entity_collision_penalty: int = 10
    general_entity_subsequent_collision_penalty: int = 3
    extended_collision_penalty: int = 3
    max_clients_to_accept_any_new_request: int = 10
    max_clients_to_accept_short_new_request: int = 100
    direct_distance_to_consider_short_request: int = 100
    short_request_max_steps: int = 1000
    short_request_ratio: float = 0.5
    min_steps_to_check_path_find_termination: int = 2000
    start_to_goal_cost_multiplier_to_terminate_path_find: float = 2000.0
    overload_levels: list[int] = field(default_factory=lambda: [0, 100, 500])
    overload_multipliers: list[int] = field(default_factory=lambda: [2, 3, 4])
    negative_path_cache_delay_interval: int = 20


@dataclass
class SteeringSetting:
    radius: float
    separation_force: float
    separation_factor: float
    force_unit_fuzzy_goto_behavior: bool = False


@dataclass
class SteeringSettings:
    default: SteeringSetting = field(default_factory=lambda: SteeringSetting(1.2, 0.005, 1.2))
    moving: SteeringSetting = field(default_factory=lambda: SteeringSetting(3, 0.01, 3))


@dataclass
class AsteroidSettings:
    spawning_rate: float = 1
    max_ray_portals_expanded_per_tick: int = 100


@dataclass
class MapSettings(JsonSettings):
    difficulty_settings: DifficultySettings = field(default_factory=DifficultySettings)
    pollution: PollutionSettings = field(default_factory=PollutionSettings)
    enemy_evolution: EnemyEvolution = field(default_factory=EnemyEvolution)
    enemy_expansion: EnemyExpansion = field(default_factory=EnemyExpansion)
    unit_group: UnitGroupSettings = field(default_factory=UnitGroupSettings)
    steering: SteeringSettings = field(default_factory=SteeringSettings)
    path_finder: PathFinderSettings = field(default_factory=PathFinderSettings)
    asteroids: AsteroidSettings = field(default_factory=AsteroidSettings)
    max_failed_behavior_count: int = 3
