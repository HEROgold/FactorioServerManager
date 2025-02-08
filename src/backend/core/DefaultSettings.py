# TODO @HEROgold: Update and fix default map settings according to the server's default settings after being created.  # noqa: FIX002
# 0
import functools
from typing import Any

from backend.models.factorio import (
    DifficultySettings,
    EnemyEvolutionSettings,
    EnemyExpansionSettings,
    MapSettings,
    PathFinder,
    PollutionSettings,
    ServerSettings,
    Steering,
    SteerSettings,
    UnitGroup,
)


def partial_class[T = object](cls: T, *args: Any, **kwds: Any) -> T:  # noqa: ANN401
    """Return a new partial class with the provided arguments set."""

    class NewCls(cls):  # type: ignore[reportUntypedBaseClass]
        __init__ = functools.partialmethod(cls.__init__, *args, **kwds)

    return NewCls


default_difficulty_settings = DifficultySettings(
    recipe_difficulty=1,
    technology_difficulty=1,
    technology_price_multiplier=1,
    research_queue_setting="always",
)
default_pollution_settings = PollutionSettings(
    enabled=True,
    _comment_min_to_diffuse_1="",
    _comment_min_to_diffuse_2="",
    diffusion_ratio=0.02,
    min_to_diffuse=0,
    ageing=0,
    expected_max_per_chunk=0,
    min_to_show_per_chunk=0,
    min_pollution_to_damage_trees=0,
    pollution_with_max_forest_damage=0,
    pollution_per_tree_damage=0,
    pollution_restored_per_tree_damage=0,
    max_pollution_to_restore_trees=0,
    enemy_attack_pollution_consumption_modifier=0,
)

default_enemy_evolution_settings = EnemyEvolutionSettings(
    enabled=True,
    time_factor=0,
    destroy_factor=0,
    pollution_factor=0,
)

default_enemy_expansion_settings = EnemyExpansionSettings(
    enabled=True,
    min_base_spacing=0,
    max_expansion_distance=0,
    friendly_base_influence_radius=0,
    enemy_building_influence_radius=0,
    building_coefficient=0,
    other_base_coefficient=0,
    neighbouring_chunk_coefficient=0,
    neighbouring_base_chunk_coefficient=0,
    max_colliding_tiles_coefficient=0,
    settler_group_min_size=0,
    settler_group_max_size=0,
    min_expansion_cooldown=0,
    max_expansion_cooldown=0,
)

default_unit_group = UnitGroup(
    min_group_gathering_time=0,
    max_group_gathering_time=0,
    max_wait_time_for_late_members=0,
    max_group_radius=0,
    min_group_radius=0,
    max_member_speedup_when_behind=0,
    max_member_slowdown_when_ahead=0,
    max_group_slowdown_factor=0,
    max_group_member_fallback_factor=0,
    member_disown_distance=0,
    tick_tolerance_when_member_arrives=0,
    max_gathering_unit_groups=0,
    max_unit_group_size=0,
)

default_steering_settings = SteerSettings(
    radius=0,
    separation_force=0,
    separation_factor=0,
    force_unit_fuzzy_goto_behavior=True,
)

default_steering = Steering(
    default=default_steering_settings,
    moving=default_steering_settings,
)

default_path_finder = PathFinder(
    fwd2bwd_ratio=0,
    goal_pressure_ratio=0,
    max_steps_worked_per_tick=0,
    max_work_done_per_tick=0,
    use_path_cache=True,
    short_cache_size=0,
    long_cache_size=0,
    short_cache_min_cacheable_distance=0,
    short_cache_min_algo_steps_to_cache=0,
    long_cache_min_cacheable_distance=0,
    cache_max_connect_to_cache_steps_multiplier=0,
    cache_accept_path_start_distance_ratio=0,
    cache_accept_path_end_distance_ratio=0,
    negative_cache_accept_path_start_distance_ratio=0,
    negative_cache_accept_path_end_distance_ratio=0,
    cache_path_start_distance_rating_multiplier=0,
    cache_path_end_distance_rating_multiplier=0,
    stale_enemy_with_same_destination_collision_penalty=0,
    ignore_moving_enemy_collision_distance=0,
    enemy_with_different_destination_collision_penalty=0,
    general_entity_collision_penalty=0,
    general_entity_subsequent_collision_penalty=0,
    extended_collision_penalty=0,
    max_clients_to_accept_any_new_request=0,
    max_clients_to_accept_short_new_request=0,
    direct_distance_to_consider_short_request=0,
    short_request_max_steps=0,
    short_request_ratio=0,
    min_steps_to_check_path_find_termination=0,
    start_to_goal_cost_multiplier_to_terminate_path_find=0,
    overload_levels=[0],
    overload_multipliers=[0],
    negative_path_cache_delay_interval=0,
)

default_map_settings = MapSettings(
    difficulty_settings=default_difficulty_settings,
    pollution=default_pollution_settings,
    enemy_evolution=default_enemy_evolution_settings,
    enemy_expansion=default_enemy_expansion_settings,
    unit_group=default_unit_group,
    steering=default_steering,
    path_finder=default_path_finder,
    max_failed_behavior_count=3,
)

class DefaultServerSettings(ServerSettings):
    """Default server settings."""
    description="A Server Managed By Factorio Server Manager"
    port=34197
    tags=["Factorio", "Server", "Manager"]  # noqa: RUF012
    max_players=5
    visibility="public"
    username="FactorioServerManager"
    password="FactorioServerManager"  # noqa: S105
    # token="", # May be used instead of password.  # noqa: ERA001
    game_password=""
    require_user_verification=True
    max_upload_in_kilobytes_per_second=0
    max_upload_slots=0
    minimum_latency_in_ticks=0
    max_heartbeats_per_second=0
    ignore_player_limit_for_returning_players=False
    allow_commands="admins-only"
    autosave_interval=0
    autosave_slots=0
    afk_autokick_interval=0
    auto_pause=False
    only_admins_can_pause_the_game=True
    autosave_only_on_server=False
    non_blocking_saving=True
    minimum_segment_size=0
    minimum_segment_size_peer_count=0
    maximum_segment_size=0
    maximum_segment_size_peer_count=0

