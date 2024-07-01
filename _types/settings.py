import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Self


# from _types.dicts import AutoPlace, Coordinates, SteerSettings


@dataclass
class ServerSettings:
    name: str
    game_password: str | None

    port: int = 34197
    description: str = ""
    tags: str = ""
    visibility_public: bool = False
    visibility_steam: bool = False
    visibility_lan: bool = True
    require_user_verification: bool = True
    use_authserver_bans: bool = True
    whitelist: bool = True
    max_players: int = 10
    ignore_limit_returning: bool = True
    admins: str = ""
    allow_commands: str = "admins-only"
    only_admins_can_pause_the_game: bool = True
    afk_autokick_interval: int = 0
    max_upload_in_kilobytes_per_second: int = 2000
    max_upload_slots: int = 5
    ignore_player_limit_for_returning_players: bool = False
    autosave_interval: int = 3600
    autosave_only_on_server: bool = True
    non_blocking_saving: bool = False
    auto_pause: bool = True

    def write(self: Self, file: Path) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch(exist_ok=True)
        with file.open("w") as f:
            json.dump(asdict(self), f)

    @classmethod
    def read(cls, file: Path) -> Self:
        with file.open() as f:
            return cls(**json.load(f))



# @dataclass
# class DifficultySettings:
#     recipe_difficulty: int = 0
#     technology_difficulty: int = 0
#     technology_price_multiplier: int = 1
#     research_queue_setting: str = "after-victory"


# @dataclass
# class PollutionSettings:
#     enabled: bool = True
#     diffusion_ratio: float = 0.02
#     min_to_diffuse: int = 15
#     ageing: int = 1
#     expected_max_per_chunk: int = 150
#     min_to_show_per_chunk: int = 50
#     min_pollution_to_damage_trees: int = 60
#     pollution_with_max_forest_damage: int = 150
#     pollution_per_tree_damage: int = 50
#     pollution_restored_per_tree_damage: int = 10
#     max_pollution_to_restore_trees: int = 20
#     enemy_attack_pollution_consumption_modifier: int = 1


# @dataclass
# class EvolutionSettings:
#     enabled: bool = True
#     time_factor: float = 0.000004
#     destroy_factor: float = 0.002
#     pollution_factor: float = 0.0000009


# @dataclass
# class ExpansionSettings:
#     enabled: bool = True
#     max_expansion_distance: int = 7
#     settler_group_min_size: int = 5
#     settler_group_max_size: int = 20
#     min_expansion_cooldown: int = 14400
#     max_expansion_cooldown: int = 216000


# @dataclass
# class UnitGroupSettings:
#     min_group_gathering_time: int = 3600
#     max_group_gathering_time: int = 36000
#     max_wait_time_for_late_members: int = 7200
#     max_group_radius: float = 30.0
#     min_group_radius: float = 5.0
#     max_member_speedup_when_behind: float = 1.4
#     max_member_slowdown_when_ahead: float = 0.6
#     max_group_slowdown_factor: float = 0.3
#     max_group_member_fallback_factor: int = 3
#     member_disown_distance: int = 10
#     tick_tolerance_when_member_arrives: int = 60
#     max_gathering_unit_groups: int = 30
#     max_unit_group_size: int = 200


# @dataclass
# class SteeringSettings:
#     default: SteerSettings = {"radius": 1.2, "separation_force": 0.005, "separation_factor": 1.2, "force_unit_fuzzy_goto_behavior": False}
#     moving: SteerSettings = {"radius": 3, "separation_force": 0.01, "separation_factor": 3, "force_unit_fuzzy_goto_behavior": False}


# @dataclass
# class PathFinderSettings:
#     fwd2bwd_ratio: int = 5
#     goal_pressure_ratio: int = 2
#     max_steps_worked_per_tick: int = 100
#     max_work_done_per_tick: int = 8000
#     use_path_cache: bool = True
#     short_cache_size: int = 5
#     long_cache_size: int = 25
#     short_cache_min_cacheable_distance: int = 10
#     short_cache_min_algo_steps_to_cache: int = 50
#     long_cache_min_cacheable_distance: int = 30
#     cache_max_connect_to_cache_steps_multiplier: int = 100
#     cache_accept_path_start_distance_ratio: float = 0.2
#     cache_accept_path_end_distance_ratio: float = 0.15
#     negative_cache_accept_path_start_distance_ratio: float = 0.3
#     negative_cache_accept_path_end_distance_ratio: float = 0.3
#     cache_path_start_distance_rating_multiplier: int = 10
#     cache_path_end_distance_rating_multiplier: int = 20
#     stale_enemy_with_same_destination_collision_penalty: int = 30
#     ignore_moving_enemy_collision_distance: int = 5
#     enemy_with_different_destination_collision_penalty: int = 30
#     general_entity_collision_penalty: int = 10
#     general_entity_subsequent_collision_penalty: int = 3
#     extended_collision_penalty: int = 3
#     max_clients_to_accept_any_new_request: int = 10
#     max_clients_to_accept_short_new_request: int = 100
#     direct_distance_to_consider_short_request: int = 100
#     short_request_max_steps: int = 1000
#     short_request_ratio: float = 0.5
#     min_steps_to_check_path_find_termination: int = 2000
#     start_to_goal_cost_multiplier_to_terminate_path_find: float = 500.0
#     overload_levels: list[int] = [0, 100, 500]
#     overload_multipliers: list[int] = [2, 3, 4]
#     negative_path_cache_delay_interval: int = 20


# @dataclass
# class MapSettings:
#     difficulty = DifficultySettings()
#     pollution = PollutionSettings()
#     evolution = EvolutionSettings()
#     expansion = ExpansionSettings()
#     unit_group = UnitGroupSettings()
#     steering = SteeringSettings()
#     path_finder = PathFinderSettings()
#     max_failed_behavior_count: int = 3

# @dataclass
# class AutoPlaceSettings:
#     coal: AutoPlace = {"frequency": 1, "size": 1, "richness": 1}
#     stone: AutoPlace = {"frequency": 1, "size": 1, "richness": 1}
#     copper_ore: AutoPlace = {"frequency": 1, "size": 1, "richness": 1}
#     iron_ore: AutoPlace = {"frequency": 1, "size": 1, "richness": 1}
#     uranium_ore: AutoPlace = {"frequency": 1, "size": 1, "richness": 1}
#     crude_oil: AutoPlace = {"frequency": 1, "size": 1, "richness": 1}
#     trees: AutoPlace = {"frequency": 1, "size": 1, "richness": 1}
#     enemy_base: AutoPlace = {"frequency": 1, "size": 1, "richness": 1}

# @dataclass
# class CliffSettings:
#     name: str = "cliff"
#     cliff_elevation_0: int = 10
#     cliff_elevation_interval: int = 40
#     richness: int = 1

# @dataclass
# class MapGenerationSettings:
#     terrain_segmentation: int = 1
#     water: int = 1
#     width: int = 0
#     height: int = 0
#     starting_area: int = 1
#     peaceful_mode: bool = False
#     auto_place_settings = AutoPlaceSettings()
#     cliff_settings = CliffSettings()
#     starting_points: Coordinates = {"x": 0, "y": 0}
#     seed: int | None = None
