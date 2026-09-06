import os
import sys
import subprocess
from typing import List, Dict, Any
from worlds.AutoWorld import World, WebWorld
from BaseClasses import Region, Entrance, Location, Item, Tutorial, ItemClassification
from .Options import PokemonXYOptions, pokemon_y_options
from .Items import item_table, ItemData, ITEM_ID_OFFSET
from .Locations import location_table, LOCATION_ID_OFFSET
from .Regions import create_regions
from .Rules import set_rules

from .Client import PokemonXYClient, PokemonYClient, PokemonXClient

ITEM_NAME_TO_ID = {name: data.code for name, data in item_table.items() if data.code is not None}
LOCATION_NAME_TO_ID = {name: data.code for name, data in location_table.items() if data.code is not None}

class PokemonXYLocation(Location):
    game: str = "Pokemon X and Y"

class PokemonXYItem(Item):
    game: str = "Pokemon X and Y"

class PokemonXYWeb(WebWorld):
    options_page = PokemonXYOptions
    tutorials = [Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up the Pokemon X and Y randomizer for Archipelago multiworld games.",
        "English",
        "setup_en.md",
        "setup/en",
        ["Author"]
    )]

class PokemonXYWorld(World):
    """
    Pokémon X and Y are Generation VI Pokémon games set in the Kalos region.
    """
    game = "Pokemon X and Y"
    web = PokemonXYWeb()

    options_dataclass = PokemonXYOptions
    options: PokemonXYOptions
    option_definitions = pokemon_y_options

    topology_present = True

    item_name_to_id = ITEM_NAME_TO_ID
    location_name_to_id = LOCATION_NAME_TO_ID

    def create_regions(self):
        create_regions(self, self.player)

    def create_items(self):
        item_pool: List[Item] = []
        
        progression_items: List[Item] = []
        useful_items: List[Item] = []
        filler_names: List[str] = []

        for item_name, data in item_table.items():
            if data.progression:
                progression_items.append(self.create_item(item_name))
            elif data.useful:
                useful_items.append(self.create_item(item_name))
            else:
                filler_names.append(item_name)

        if not filler_names:
            filler_names = ["Poké Ball"]

        unfilled_locations = self.multiworld.get_unfilled_locations(self.player)
        location_count = len(unfilled_locations)

        if len(progression_items) > location_count:
            item_pool = progression_items[:location_count]
        else:
            item_pool = list(progression_items)

        idx = 0
        while len(item_pool) < location_count:
            if idx < len(useful_items):
                item_pool.append(useful_items[idx])
            else:
                filler_name = filler_names[idx % len(filler_names)]
                item_pool.append(self.create_item(filler_name))
            idx += 1
            
        self.multiworld.itempool += item_pool

    def set_rules(self):
        set_rules(self, self.player)

    def create_item(self, name: str) -> Item:
        data = item_table[name]
        classification = ItemClassification.progression if data.progression else (
            ItemClassification.useful if data.useful else (
                ItemClassification.trap if data.trap else ItemClassification.filler
            )
        )
        return PokemonXYItem(name, classification, data.code, self.player)

    def fill_slot_data(self) -> Dict[str, Any]:
        include_hidden = getattr(self.options, "include_hidden_items", True)
        if hasattr(include_hidden, "value"): include_hidden = bool(include_hidden.value)
        return {
            "goal": "8 Badges + E4 + Champion",
            "include_hidden_items": include_hidden,
        }

