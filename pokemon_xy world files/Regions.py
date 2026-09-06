from typing import Dict, List, Set
from BaseClasses import Region, Entrance
from .Locations import location_table, PokemonYLocation

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
        target_reg = loc_data.region if loc_data.region in regions_dict else "Santalune Area"
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
