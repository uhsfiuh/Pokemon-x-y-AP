from typing import TYPE_CHECKING
from BaseClasses import CollectionState
from .Locations import location_table

if TYPE_CHECKING:
    from . import PokemonXYWorld

def count_badges(state: CollectionState, player: int) -> int:
    badges = ["Bug Badge", "Cliff Badge", "Rumble Badge", "Plant Badge",
              "Voltage Badge", "Fairy Badge", "Psychic Badge", "Iceberg Badge"]
    return sum(1 for b in badges if state.has(b, player))

def has_all_badges(state: CollectionState, player: int) -> bool:
    badges = ["Bug Badge", "Cliff Badge", "Rumble Badge", "Plant Badge",
              "Voltage Badge", "Fairy Badge", "Psychic Badge", "Iceberg Badge"]
    return all(state.has(b, player) for b in badges)

def set_rules(world: "PokemonXYWorld", player: int) -> None:
    # 1. Regional Entrance Rules (Require specific overworld Gym Badges)
    multiworld = world.multiworld

    def get_entrance(name: str):
        return multiworld.get_entrance(name, player)

    # Santalune -> Camphrier requires Bug Badge (Badge 1)
    get_entrance("Santalune Area -> Camphrier Area").access_rule = \
        lambda state: state.has("Bug Badge", player)

    # Camphrier -> Cyllage requires Bug Badge + Poké Flute
    get_entrance("Camphrier Area -> Cyllage Area").access_rule = \
        lambda state: state.has("Bug Badge", player) and state.has("Poke Flute", player)

    # Cyllage -> Shalour requires Cliff Badge (Badge 2)
    get_entrance("Cyllage Area -> Shalour Area").access_rule = \
        lambda state: state.has("Cliff Badge", player)

    # Shalour -> Coumarine requires Rumble Badge (Badge 3)
    get_entrance("Shalour Area -> Coumarine Area").access_rule = \
        lambda state: state.has("Rumble Badge", player)

    # Coumarine -> Lumiose requires Plant Badge (Badge 4) + Power Plant Pass
    get_entrance("Coumarine Area -> Lumiose Area").access_rule = \
        lambda state: state.has("Plant Badge", player) and state.has("Power Plant Pass", player)

    # Lumiose -> Laverre requires Voltage Badge (Badge 5)
    get_entrance("Lumiose Area -> Laverre Area").access_rule = \
        lambda state: state.has("Voltage Badge", player)

    # Laverre -> Anistar requires Fairy Badge (Badge 6)
    get_entrance("Laverre Area -> Anistar Area").access_rule = \
        lambda state: state.has("Fairy Badge", player)

    # Anistar -> Snowbelle requires Psychic Badge (Badge 7) + Elevator Key
    get_entrance("Anistar Area -> Snowbelle Area").access_rule = \
        lambda state: state.has("Psychic Badge", player) and state.has("Elevator Key", player)

    # Snowbelle -> Victory Road requires Iceberg Badge (Badge 8)
    get_entrance("Snowbelle Area -> Victory Road").access_rule = \
        lambda state: state.has("Iceberg Badge", player)

    # 2. Location-specific item requirements (HMs require HM item + Badge Count)
    for loc in multiworld.get_locations(player):
        loc_data = location_table.get(loc.name)
        if loc_data and loc_data.requires:
            reqs = loc_data.requires
            if "HM01 Cut" in reqs:
                old_rule = loc.access_rule
                loc.access_rule = lambda state, r=old_rule: r(state) and state.has("HM01 Cut", player) and count_badges(state, player) >= 1
            if "HM03 Surf" in reqs:
                old_rule = loc.access_rule
                loc.access_rule = lambda state, r=old_rule: r(state) and state.has("HM03 Surf", player) and count_badges(state, player) >= 3
            if "HM04 Strength" in reqs:
                old_rule = loc.access_rule
                loc.access_rule = lambda state, r=old_rule: r(state) and state.has("HM04 Strength", player) and count_badges(state, player) >= 2
            if "HM05 Waterfall" in reqs:
                old_rule = loc.access_rule
                loc.access_rule = lambda state, r=old_rule: r(state) and state.has("HM05 Waterfall", player) and count_badges(state, player) >= 8
            if "Roller Skates" in reqs:
                old_rule = loc.access_rule
                loc.access_rule = lambda state, r=old_rule: r(state) and state.has("Roller Skates", player)
            if "Dowsing Machine" in reqs:
                old_rule = loc.access_rule
                loc.access_rule = lambda state, r=old_rule: r(state) and state.has("Dowsing Machine", player)

    # 2b. Require Dowsing Machine option for all Hidden Item locations
    req_dowsing = getattr(world.options, "include_hidden_items", True) and getattr(world.options, "require_dowsing_machine", False)
    if hasattr(req_dowsing, "value"): req_dowsing = bool(req_dowsing.value)

    if req_dowsing:
        for loc in multiworld.get_locations(player):
            loc_data = location_table.get(loc.name)
            if loc_data and "HIDDEN ITEM" in loc_data.category:
                old_rule = loc.access_rule
                loc.access_rule = lambda state, r=old_rule: r(state) and state.has("Dowsing Machine", player)

    # 3. Completion Condition: All 8 Badges + HM03 Surf (requires Badge count >= 3)
    multiworld.completion_condition[player] = lambda state: has_all_badges(state, player) and state.has("HM03 Surf", player)
