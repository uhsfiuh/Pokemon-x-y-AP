from typing import Dict, List, Set
from BaseClasses import Region, Entrance
from .Locations import location_table, PokemonYLocation

# ---------------------------------------------------------------------------
# Region corrections.
#
# The `region` field in Locations.py was filled in in bulk and mis-files whole
# routes, which silently drops them out of logic (assigned too late) or makes
# them reachable before they should be (assigned too early). Correcting it here
# by name prefix keeps each fix to one reviewable line instead of editing every
# row of a route by hand.
#
# Region names are progression tiers, not geography: "Camphrier Area" means
# "reachable once you hold the Bug Badge", "Cyllage Area" means "reachable once
# you also hold the Poke Flute", and so on down the chain in regions_data.
#
# Matching is longest-prefix-first, so list more specific prefixes above more
# general ones.
# ---------------------------------------------------------------------------
REGION_OVERRIDES = {
    # Route 6 (Palais Lane) runs Camphrier Town -> Parfum Palace, and you walk
    # it to fetch the Poke Flute. Filing it under Cyllage Area put it behind the
    # very item it leads to, so the whole route sat out of logic.
    "Route 6 - ": "Camphrier Area",

    # Route 22 (Detourne Way) connects Santalune City to Victory Road, so its
    # near end is reachable as soon as you leave Santalune. It was filed wholly
    # under Victory Road. The genuinely deep items on it are gated by field
    # moves instead, via `requires` in Locations.py.
    "Route 22 - ": "Santalune Area",

    # Route 9 is the Ambrette -> Cyllage approach (infobox: north=Glittering
    # Cave, west=Ambrette Town), so it is reached before the Cliff Badge, not
    # after. It was filed under Shalour Area. The Ambrette Gate that leads onto
    # it was already Cyllage Area, so the file contradicted itself.
    "Route 9 - ": "Cyllage Area",

    # Route 16, the Lost Hotel and the Poke Ball Factory are blocked until
    # Bryony and Celosia are beaten at the factory, which needs the Fairy Badge.
    # Route 15 leads there. All were filed a tier early under Laverre Area.
    "Route 15 - ": "Anistar Area",
    "Route 16 - ": "Anistar Area",
    "Lost Hotel - ": "Anistar Area",
    "Poké Ball Factory - ": "Anistar Area",
    "PokeBall Factory - ": "Anistar Area",

    # Dendemille Town, Route 17 and Frost Cavern sit between the Fairy Badge and
    # the Psychic Badge. Frost Cavern and the Route 17 items were filed under
    # Snowbelle Area (a tier late) while Route 17's trainers were already
    # Anistar Area -- the file disagreed with itself.
    "Dendemille Town - ": "Anistar Area",
    "Frost Cavern - ": "Anistar Area",
    # The trainer rows are named "Frost Cavern (1F) - ", "(2F)", "(3F)",
    # "(Outside)", so the prefix above misses all 14 of them and they would stay
    # a tier late in Snowbelle Area, splitting one dungeon across two tiers.
    "Frost Cavern (": "Anistar Area",
    # Route 17 (Mamoswine Road) runs Dendemille -> Anistar, so it sits in the
    # same tier. Its trainers were already Anistar Area; only the item entries
    # were filed under Snowbelle Area.
    "Route 17 - ": "Anistar Area",

    # Lysandre Labs open only after the Anistar Gym, i.e. the Psychic Badge.
    "Lysandre Lab - ": "Snowbelle Area",
    "Lysandre Labs - ": "Snowbelle Area",

    # Kiloude City is post-Hall-of-Fame. Victory Road is the last tier this
    # linear region chain has, so that is the closest honest placement.
    "Kiloude City - ": "Victory Road",
}

# NOTE: the item locations for Kalos Routes 17-21 used to be misnamed, each
# shifted one route number too high. They have since been renamed to match the
# real routes, verified against Bulbapedia's per-route item tables. Flag ids
# were always correct, so this was a display-only fault. The rename changes the
# datapackage, so this world is NOT backwards compatible with seeds generated
# before it.


def _resolve_region(loc_name: str, loc_data, regions_dict) -> str:
    for prefix, region in REGION_OVERRIDES.items():
        if loc_name.startswith(prefix):
            if region in regions_dict:
                return region
            break
    if loc_data.region in regions_dict:
        return loc_data.region
    return "Santalune Area"


def create_regions(world, player):
    regions_data = {'Menu': {'connects_to': ['Santalune Area']}, 'Santalune Area': {'connects_to': ['Camphrier Area']}, 'Camphrier Area': {'connects_to': ['Cyllage Area']}, 'Cyllage Area': {'connects_to': ['Shalour Area']}, 'Shalour Area': {'connects_to': ['Coumarine Area']}, 'Coumarine Area': {'connects_to': ['Lumiose Area']}, 'Lumiose Area': {'connects_to': ['Laverre Area']}, 'Laverre Area': {'connects_to': ['Anistar Area']}, 'Anistar Area': {'connects_to': ['Snowbelle Area']}, 'Snowbelle Area': {'connects_to': ['Victory Road']}, 'Victory Road': {'connects_to': []}}

    regions_dict: Dict[str, Region] = {}
    for reg_name in regions_data.keys():
        reg = Region(reg_name, player, world.multiworld)
        regions_dict[reg_name] = reg
        world.multiworld.regions.append(reg)

    # Add locations to regions
    include_hidden = getattr(world.options, "include_hidden_items", True)
    if hasattr(include_hidden, "value"): include_hidden = bool(include_hidden.value)

    include_trainers = getattr(world.options, "trainersanity", False)
    if hasattr(include_trainers, "value"): include_trainers = bool(include_trainers.value)

    for loc_name, loc_data in location_table.items():
        # Skip un-named raw event flag entries (e.g. FE_R14_ITEMGET_01, TMFLG_C06_ITEMGET_01)
        if loc_name.startswith("FE_") or loc_name.startswith("TMFLG_") or loc_name.startswith("FLAG_"):
            continue
        # Skip daily/weekly repeatable checks - these reset and can't be reliably tracked
        if "[Daily]" in loc_name or "[Weekly]" in loc_name:
            continue
        # Skip locations with no flag_id - they can't be detected by the client
        if loc_data.flag_id is None:
            continue
        if not include_hidden and "HIDDEN ITEM" in loc_data.category:
            continue
        if not include_trainers and "TRAINER" in loc_data.category:
            continue
        target_reg = _resolve_region(loc_name, loc_data, regions_dict)
        loc = PokemonYLocation(player, loc_name, loc_data.code, regions_dict[target_reg])
        regions_dict[target_reg].locations.append(loc)

    # Connect entrance graph
    for reg_name, reg_info in regions_data.items():
        parent_reg = regions_dict[reg_name]
        for dest_reg_name in reg_info.get("connects_to", []):
            if dest_reg_name in regions_dict:
                entrance = Entrance(player, f"{reg_name} -> {dest_reg_name}", parent_reg)
                parent_reg.exits.append(entrance)
                entrance.connect(regions_dict[dest_reg_name])
