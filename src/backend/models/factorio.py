
from typing import Literal

from pydantic import BaseModel


class ServerModEntry(BaseModel):
    name: str
    enabled: bool


class SteerSettings(BaseModel):
    radius: float
    separation_force: float
    separation_factor: float
    force_unit_fuzzy_goto_behavior: bool


class AutoPlace(BaseModel):
    frequency: int
    size: int
    richness: int


class Coordinates(BaseModel):
    x: int
    y: int



class AutoPlaceControls(BaseModel):
    coal: AutoPlace
    stone: AutoPlace
    copper_ore: AutoPlace
    iron_ore: AutoPlace
    uranium_ore: AutoPlace
    crude_oil: AutoPlace
    trees: AutoPlace
    enemy_base: AutoPlace


class CliffSettings(BaseModel):
    name = "cliff"
    cliff_elevation_0: int = 10
    cliff_elevation_interval: int = 40
    richness: 1

class PropertyExpressionNames(BaseModel):
    pass
    # "control-setting:moisture:frequency:multiplier": "1"
    # "control-setting:moisture:bias": "0"
    # "control-setting:aux:frequency:multiplier": "1"
    # "control-setting:aux:bias": "0"

class MapGenSettings(BaseModel):
    terrain_segmentation: int
    water: int
    width: int
    height: int
    starting_area: int
    peaceful_mode: bool
    autoplace_controls: AutoPlaceControls
    cliff_settings: CliffSettings
    property_expression_names: PropertyExpressionNames
    starting_points: list[Coordinates]
    seed: None | int = None

class DifficultySettings(BaseModel):
    recipe_difficulty: int
    technology_difficulty: int
    technology_price_multiplier: int
    research_queue_setting: Literal["after-victory", "always", "never"]
    # WARN:after-victory might not be a thing in 2.0

class PollutionSettings(BaseModel):
    enabled: bool
    _comment_min_to_diffuse_1: str
    _comment_min_to_diffuse_2: str
    diffusion_ratio: float
    min_to_diffuse: int
    ageing: int
    expected_max_per_chunk: int
    min_to_show_per_chunk: int
    min_pollution_to_damage_trees: int
    pollution_with_max_forest_damage: int
    pollution_per_tree_damage: int
    pollution_restored_per_tree_damage: int
    max_pollution_to_restore_trees: int
    enemy_attack_pollution_consumption_modifier: int

class EnemyEvolutionSettings(BaseModel):
    enabled: bool
    time_factor: float
    destroy_factor: float
    pollution_factor: float

class EnemyExpansionSettings(BaseModel):
    enabled: bool
    min_base_spacing: int
    max_expansion_distance: int
    friendly_base_influence_radius: int
    enemy_building_influence_radius: int
    building_coefficient: float
    other_base_coefficient: float
    neighbouring_chunk_coefficient: float
    neighbouring_base_chunk_coefficient: float
    max_colliding_tiles_coefficient: float
    settler_group_min_size: int
    settler_group_max_size: int
    min_expansion_cooldown: int
    max_expansion_cooldown: int

class UnitGroup(BaseModel):
    min_group_gathering_time: int
    max_group_gathering_time: int
    max_wait_time_for_late_members: int
    max_group_radius: float
    min_group_radius: float
    max_member_speedup_when_behind: float
    max_member_slowdown_when_ahead: float
    max_group_slowdown_factor: float
    max_group_member_fallback_factor: int
    member_disown_distance: int
    tick_tolerance_when_member_arrives: int
    max_gathering_unit_groups: int
    max_unit_group_size: int

class Steering(BaseModel):
    default: SteerSettings
    moving: SteerSettings

class PathFinder(BaseModel):
    fwd2bwd_ratio: int
    goal_pressure_ratio: int
    max_steps_worked_per_tick: int
    max_work_done_per_tick: int
    use_path_cache: bool
    short_cache_size: int
    long_cache_size: int
    short_cache_min_cacheable_distance: int
    short_cache_min_algo_steps_to_cache: int
    long_cache_min_cacheable_distance: int
    cache_max_connect_to_cache_steps_multiplier: int
    cache_accept_path_start_distance_ratio: float
    cache_accept_path_end_distance_ratio: float
    negative_cache_accept_path_start_distance_ratio: float
    negative_cache_accept_path_end_distance_ratio: float
    cache_path_start_distance_rating_multiplier: int
    cache_path_end_distance_rating_multiplier: int
    stale_enemy_with_same_destination_collision_penalty: int
    ignore_moving_enemy_collision_distance: int
    enemy_with_different_destination_collision_penalty: int
    general_entity_collision_penalty: int
    general_entity_subsequent_collision_penalty: int
    extended_collision_penalty: int
    max_clients_to_accept_any_new_request: int
    max_clients_to_accept_short_new_request: int
    direct_distance_to_consider_short_request: int
    short_request_max_steps: int
    short_request_ratio: float
    min_steps_to_check_path_find_termination: int
    start_to_goal_cost_multiplier_to_terminate_path_find: float
    overload_levels: list[int]
    overload_multipliers: list[int]
    negative_path_cache_delay_interval: int

class MapSettings(BaseModel):
    difficulty_settings: DifficultySettings
    pollution: PollutionSettings
    enemy_evolution: EnemyEvolutionSettings
    enemy_expansion: EnemyExpansionSettings
    unit_group: UnitGroup
    steering: Steering
    path_finder: PathFinder
    max_failed_behavior_count: int = 3


class ServerSettings(BaseModel):
    name: str
    description: str
    port: int
    tags: list[str]
    max_players: int = 0
    visibility: Literal["public", "lan"]
    username: str # Required when visibility is set to public
    password: str # Required when visibility is set to public
    # "Authentication token. May be used instead of 'password' above."
    token: str
    game_password: str
    require_user_verification: bool
    max_upload_in_kilobytes_per_second: int
    max_upload_slots: int
    minimum_latency_in_ticks: int
    max_heartbeats_per_second: int
    ignore_player_limit_for_returning_players: bool
    allow_commands: Literal["true", "false", "admins-only"]
    autosave_interval: 10
    autosave_slots: 5
    afk_autokick_interval: 0
    auto_pause: bool
    only_admins_can_pause_the_game: bool
    autosave_only_on_server: bool
    non_blocking_saving: bool
    minimum_segment_size: int
    minimum_segment_size_peer_count: int
    maximum_segment_size: int
    maximum_segment_size_peer_count: int

class MapGenerationSettings(BaseModel):
    ...
