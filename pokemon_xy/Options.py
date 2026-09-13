from dataclasses import dataclass
from Options import PerGameCommonOptions, DefaultOnToggle, Toggle, Choice

class IncludeHiddenItems(DefaultOnToggle):
    """Include hidden items scattered across Kalos in the location pool."""
    display_name = "Include Hidden Items"

class RequireDowsingMachine(Toggle):
    """Require the Dowsing Machine item in logic to access hidden ground items."""
    display_name = "Require Dowsing Machine for Hidden Items"

class TrainerSanity(Toggle):
    """Include beating in-game trainers (Youngsters, Lasses, Gym Trainers, Rivals) as location checks."""
    display_name = "Trainersanity"

class Goal(Choice):
    """Goal condition for completing the multiworld."""
    display_name = "Goal"
    option_pokemon_league = 0
    default = 0

@dataclass
class PokemonXYOptions(PerGameCommonOptions):
    include_hidden_items: IncludeHiddenItems
    require_dowsing_machine: RequireDowsingMachine
    trainersanity: TrainerSanity
    goal: Goal

@dataclass
class PokemonYOptions(PerGameCommonOptions):
    include_hidden_items: IncludeHiddenItems
    require_dowsing_machine: RequireDowsingMachine
    trainersanity: TrainerSanity
    goal: Goal

@dataclass
class PokemonXOptions(PerGameCommonOptions):
    include_hidden_items: IncludeHiddenItems
    require_dowsing_machine: RequireDowsingMachine
    trainersanity: TrainerSanity
    goal: Goal

pokemon_y_options = {
    "include_hidden_items": IncludeHiddenItems,
    "require_dowsing_machine": RequireDowsingMachine,
    "trainersanity": TrainerSanity,
    "goal": Goal,
}

option_definitions = pokemon_y_options
