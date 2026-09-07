from typing import NamedTuple, Dict, Optional, List
from BaseClasses import Location

class PokemonYLocation(Location):
    game: str = "Pokemon X and Y"

class LocationData(NamedTuple):
    code: int
    region: str = "Unknown"
    category: List[str] = []
    flag_id: Optional[int] = None
    requires: str = ""
    victory: bool = False

LOCATION_ID_OFFSET = 200000

location_table: Dict[str, LocationData] = {
    "Santalune Area - Bug Badge": LocationData(200001, "Santalune Area", category=["Badge"], flag_id=0x06D2),
    "Cyllage Area - Cliff Badge": LocationData(200002, "Cyllage Area", category=["Badge"], flag_id=0x0718),
    "Shalour Area - Rumble Badge": LocationData(200003, "Shalour Area", category=["Badge"], flag_id=0x06E1),
    "Coumarine Area - Plant Badge": LocationData(200004, "Coumarine Area", category=["Badge"], flag_id=0x06E2),
    "Lumiose Area - Voltage Badge": LocationData(200005, "Lumiose Area", category=["Badge"], flag_id=0x06E3),
    "Laverre Area - Fairy Badge": LocationData(200006, "Laverre Area", category=["Badge"], flag_id=0x06E4),
    "Anistar Area - Psychic Badge": LocationData(200007, "Anistar Area", category=["Badge"], flag_id=0x06E5),
    "Snowbelle Area - Iceberg Badge": LocationData(200008, "Snowbelle Area", category=["Badge"], flag_id=0x06E6),
    "Pokémon League - Champion Victory": LocationData(200009, "Victory Road", category=["Goal"], flag_id=0x0A50, victory=True),
    "Shalour City - Exchanged a Sitrus Berry for a Leppa Berry with guy": LocationData(200011, "Shalour Area", category=['ITEM GIFT'], flag_id=0x008D, requires=""),
    "Cyllage City - Received Destiny Knot from maid": LocationData(200012, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x008E, requires=""),
    "Cyllage City - Received Whipped Dream / Sachet from man": LocationData(200014, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x0090, requires=""),
    "Lumiose City (South Boulevard) - Received Luxury Ball (x5) from woman": LocationData(200016, "Lumiose Area", category=['ITEM GIFT'], flag_id=0x0092, requires=""),
    "Shalour City - Received Shoothe Bell from madame for showing her a Pokémon with good friendship": LocationData(200017, "Shalour Area", category=['ITEM GIFT'], flag_id=0x0093, requires=""),
    # REMOVED: "Shalour City - Received Eviolite from scientist for seeing at
    # least 40 species in Coastal Pokédex" (id 200020, flag 0x0097). Grindy
    # Pokédex requirement, unreasonable in a randomised run. Id retired.
    "Aquacorde Town - Received Potion from shopkeeper": LocationData(200023, "Santalune Area", category=['ITEM GIFT'], flag_id=0x00A4, requires=""),
    # Key items whose vanilla source was previously not a check, so the story
    # handed them over regardless and the matching gate in Rules.py was fake.
    # Flags taken from the Gen6_XY event flag sheet:
    #   0x0A55  SYS_FLAG_ROLLERSKATES  "Can use Roller Skates"       Santalune City
    #   0x03F5  FV_T03R0101_O_MODEL01  "Poké Flute obj disappeared"  Shabboneau Castle 1F
    "Santalune City - Received Roller Skates from Roller Skater Rinka": LocationData(200482, "Santalune Area", category=['ITEM GIFT'], flag_id=0x0A55, requires=""),
    # Was flag 0x03F5 (FV_T03R0101_O_MODEL01, "Poké Flute obj disappeared").
    # That is a field-object VISIBILITY flag, and it reads as already set on a
    # brand new save -- "disappeared" is its default state before the room is
    # ever initialised -- so the check fired the instant a client connected.
    # Moved to a manual button on spare flag 0x0012 instead.
    "Shabboneau Castle - Received Poké Flute from the castle's owner": LocationData(200483, "Camphrier Area", category=['ITEM GIFT'], flag_id=0x0012, requires=""),
    # Manual checks. The game sets no event flag when it hands you these five,
    # so their pickups cannot be detected automatically. The player presses a
    # button in the connector's helper window when they receive one, which sets
    # a spare flag that the normal flag scan then reports as a check.
    #
    # The flags are five the game never touches, listed as "_UNUSED /* not used
    # */" in the Gen6_XY event flag reference: 0x0A51, 0x0A53, 0x0A56, 0x0A57,
    # 0x0A58. Borrowing them cannot disturb a save.
    "Shalour City - Received HM03 (Surf) from Calem/Serena": LocationData(200493, "Shalour Area", category=['ITEM GIFT'], flag_id=0x0A51, requires=""),
    "Cyllage City - Received HM04 (Strength) from Grant": LocationData(200494, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x0A53, requires=""),
    "Route 19 - Received HM05 (Waterfall) from Shauna": LocationData(200486, "Snowbelle Area", category=['ITEM GIFT'], flag_id=0x0A56, requires=""),
    "Route 8 - Received the Dowsing Machine from woman": LocationData(200491, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x0A57, requires=""),
    "Lysandre Labs - Received the Elevator Key from Mable": LocationData(200492, "Snowbelle Area", category=['ITEM GIFT'], flag_id=0x0A58, requires=""),
    "Coumarine City - Received Poké Toy from woman for answering her sound quiz first time": LocationData(200025, "Coumarine Area", category=['ITEM GIFT'], flag_id=0x00AA, requires=""),
    # REMOVED: "Lumiose City (South Boulevard) - Received TM54 (False Swipe) from
    # female scientist for seeing at least 20 species in Central Kalos Pokédex"
    # (id 200026, flag 0x00B1). Grindy Pokédex requirement. Id retired.
    "Camphrier Town - Received Berry Juice from girl": LocationData(200027, "Camphrier Area", category=['ITEM GIFT'], flag_id=0x00B2, requires=""),
    "Camphrier Town - Received Ultra Ball from man": LocationData(200028, "Camphrier Area", category=['ITEM GIFT'], flag_id=0x00B3, requires=""),
    "Camphrier Town - Received Full Heal from boy": LocationData(200029, "Camphrier Area", category=['ITEM GIFT'], flag_id=0x00B4, requires=""),
    "Camphrier Town - Received TM46 (Thief) from punk girl": LocationData(200030, "Camphrier Area", category=['ITEM GIFT'], flag_id=0x00B5, requires=""),
    # REMOVED: "Coumarine City - Received Lucky Egg from woman for showing her a
    # Pokémon with maximum friendship" (id 200032, flag 0x00B7). Maximum
    # friendship is a long grind; the "good friendship" check at 0x0093 is kept
    # as the reasonable version of this. Id retired.
    "Lumiose City (South Boulevard) - Received Quick Claw from woman": LocationData(200036, "Lumiose Area", category=['ITEM GIFT'], flag_id=0x00C6, requires=""),
    "Lumiose City (South Boulevard) - Received Quick Ball (x3) from man": LocationData(200037, "Lumiose Area", category=['ITEM GIFT'], flag_id=0x00C7, requires=""),
    # REMOVED: "Ambrette Town - Received the Douse Drive" (id 200039, flag 0x00D5).
    # The NPC only hands over a Drive if you show him a Genesect, which is an
    # event-only Pokemon and unobtainable in a normal playthrough, so this check
    # could never be completed. ID 200039 is left permanently retired rather
    # than reused, so it cannot collide with an older seed.
    "Santalune Forest - Received Poké Ball from Calem/Serena if interacted": LocationData(200041, "Santalune Area", category=['ITEM GIFT'], flag_id=0x00D7, requires=""),
    "Lumiose City (South Boulevard) - Received Timer Ball (x3) from man": LocationData(200042, "Lumiose Area", category=['ITEM GIFT'], flag_id=0x00FE, requires=""),
    "Cyllage City - Received Persim Berry (x3) from girl for answering her quiz": LocationData(200043, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x00FF, requires=""),
    "Parfum Palace - Received Oran Berry from woman": LocationData(200050, "Camphrier Area", category=['ITEM GIFT'], flag_id=0x0106, requires=""),
    "Ambrette Town - Received TM94 (Rock Smash) from girl": LocationData(200051, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x0109, requires=""),
    "Santalune City - Received Great Ball from boy": LocationData(200053, "Santalune Area", category=['ITEM GIFT'], flag_id=0x010B, requires=""),
    # REMOVED: "Lumiose City (Vernal Avenue) - Received Pearl String (x2) from
    # madame for showing her a Furfrou that has kept the same trim for 15 days"
    # (id 200055, flag 0x010D). Gated on 15 days of real time. Id retired.
    "Tower of Mastery - Received TM47 (Low Sweep) from ace trainer": LocationData(200056, "Shalour Area", category=['ITEM GIFT'], flag_id=0x010E, requires=""),
    "Coumarine City - Received Good Rod from fisherman": LocationData(200059, "Coumarine Area", category=['ITEM GIFT'], flag_id=0x011A, requires=""),
    # REMOVED: "Reflection Cave - Received Reveal Glass from female scientist for
    # showing her a Tornadus / Thundurus / Landorus" (id 200060, flag 0x011C).
    # None of the three can be obtained in X/Y without a Gen 5 transfer, so this
    # was impossible for the same reason as the Genesect check. Id retired.
    # Azure Bay is reachable only by surfing north across the water from Route 12; every location on this map requires Surf.
    "Azure Bay - Received Ampharosite from old man": LocationData(200061, "Coumarine Area", category=['ITEM GIFT'], flag_id=0x011D, requires="HM03 Surf"),
    "Ambrette Town - Received Aerodactylite from male scientist": LocationData(200062, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x011E, requires=""),
    "Shalour City - Exchanged the Intriguing Stone for a Sun Stone with hiker": LocationData(200086, "Shalour Area", category=['ITEM GIFT'], flag_id=0x0146, requires=""),
    "Ambrette Gate - Received Rocky Helmet from woman": LocationData(200089, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x0191, requires=""),
    "Coumarine Gate - Received Black Sludge from punk guy": LocationData(200090, "Coumarine Area", category=['ITEM GIFT'], flag_id=0x0193, requires=""),
    "Coumarine City - Received Silk Scarf from old man": LocationData(200091, "Coumarine Area", category=['ITEM GIFT'], flag_id=0x0195, requires=""),
    "Coumarine City - Received Metronome from man": LocationData(200092, "Coumarine Area", category=['ITEM GIFT'], flag_id=0x019B, requires=""),
    "Route 12 - Received TM45 (Attract) from girl": LocationData(200093, "Coumarine Area", category=['ITEM GIFT'], flag_id=0x019C, requires=""),
    "Ambrette Town - Received TM96 (Nature Power) from woman": LocationData(200095, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x019E, requires=""),
    "Geosenge Town - Received TM66 (Payback) from old man": LocationData(200098, "Shalour Area", category=['ITEM GIFT'], flag_id=0x01A1, requires=""),
    "Cyllage City - Received TM44 (Rest) from guy": LocationData(200099, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x01A3, requires=""),
    "Cyllage City - Received TM88 (Sleep Talk) from girl": LocationData(200100, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x01A4, requires=""),
    "Connecting Cave - Received TM21 (Frustration) from Backpacker": LocationData(200101, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x01A5, requires=""),
    "Santalune City - Received X Attack (x3) and X Defense (x3) from old man": LocationData(200103, "Santalune Area", category=['ITEM GIFT'], flag_id=0x01AC, requires=""),
    "Shalour City - Received Stardust (x5) from girl for helping her": LocationData(200104, "Shalour Area", category=['ITEM GIFT'], flag_id=0x01AD, requires=""),
    "Geosenge Town - Received Everstone from female scientist": LocationData(200105, "Shalour Area", category=['ITEM GIFT'], flag_id=0x01AE, requires=""),
    "Route 13 - Found Power Plant Pass": LocationData(200111, "Lumiose Area", category=['HIDDEN ITEM'], flag_id=0x044D, requires="Dowsing Machine"),
    "Santalune City - Found Super Potion": LocationData(200112, "Santalune Area", category=['HIDDEN ITEM'], flag_id=0x044E, requires="Dowsing Machine"),
    "Santalune City - Found Great Ball": LocationData(200113, "Santalune Area", category=['HIDDEN ITEM'], flag_id=0x044F, requires="Dowsing Machine"),
    "Santalune City - Found Antidote": LocationData(200114, "Santalune Area", category=['HIDDEN ITEM'], flag_id=0x0450, requires="Dowsing Machine"),
    "Route 4 - Found Honey (recurring)": LocationData(200115, "Camphrier Area", category=['HIDDEN ITEM'], flag_id=0x0451, requires="Dowsing Machine"),
    "Route 4 - Found Honey (recurring) (2)": LocationData(200116, "Camphrier Area", category=['HIDDEN ITEM'], flag_id=0x0452, requires="Dowsing Machine"),
    "Route 4 - Found Honey (recurring) (3)": LocationData(200117, "Camphrier Area", category=['HIDDEN ITEM'], flag_id=0x0453, requires="Dowsing Machine"),
    "Route 4 - Found Super Potion": LocationData(200118, "Camphrier Area", category=['HIDDEN ITEM'], flag_id=0x0454, requires="Dowsing Machine"),
    "Route 5 - Found Paralyze Heal": LocationData(200119, "Camphrier Area", category=['HIDDEN ITEM'], flag_id=0x0455, requires="Dowsing Machine"),
    "Route 5 - Found Super Potion": LocationData(200120, "Camphrier Area", category=['HIDDEN ITEM'], flag_id=0x0456, requires="Dowsing Machine"),
    "Camphrier Town - Found Antidote": LocationData(200121, "Camphrier Area", category=['HIDDEN ITEM'], flag_id=0x0457, requires="Dowsing Machine"),
    "Camphrier Town - Found Ether": LocationData(200122, "Camphrier Area", category=['HIDDEN ITEM'], flag_id=0x0458, requires="Dowsing Machine"),
    "Route 6 - Found Antidote": LocationData(200123, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x0459, requires="Dowsing Machine"),
    "Route 6 - Found Tiny Mushroom": LocationData(200124, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x045A, requires="Dowsing Machine"),
    "Parfum Palace - Found Rare Candy": LocationData(200125, "Camphrier Area", category=['HIDDEN ITEM'], flag_id=0x045B, requires="Dowsing Machine"),
    "Parfum Palace - Found X Sp. Atk": LocationData(200126, "Camphrier Area", category=['HIDDEN ITEM'], flag_id=0x045C, requires="Dowsing Machine"),
    "Parfum Palace - Found Pretty Wing (recurring)": LocationData(200127, "Camphrier Area", category=['HIDDEN ITEM'], flag_id=0x045D, requires="Dowsing Machine"),
    "Route 8 - Found Super Potion": LocationData(200128, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x045E, requires="Dowsing Machine"),
    "Route 8 - Found Escape Rope": LocationData(200129, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x045F, requires="Dowsing Machine"),
    "Route 8 - Found Pearl (recurring)": LocationData(200130, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x0460, requires="Dowsing Machine"),
    "Route 8 - Found Ultra Ball": LocationData(200131, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x0461, requires="Dowsing Machine"),
    # Bulbapedia: on a rock on the big NW island, requires Surf; the other hidden Heart Scale on this route is unclear which flag it maps to, so Surf is applied to both as a safe fallback.
    "Route 8 - Found Heart Scale": LocationData(200132, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x0462, requires="Dowsing Machine AND HM03 Surf"),
    "Route 8 - Found Stardust (recurring)": LocationData(200133, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x0463, requires="Dowsing Machine"),
    # Bulbapedia: matches the recurring hidden Heart Scale on the NW coastal area; flag mapping to the Surf-gated spot is uncertain, so Surf is applied here too as a safe fallback.
    "Route 8 - Found Heart Scale (recurring)": LocationData(200134, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x0464, requires="Dowsing Machine AND HM03 Surf"),
    "Ambrette Town - Found Rare Candy": LocationData(200135, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x0465, requires="Dowsing Machine"),
    "Ambrette Town - Found X Attack": LocationData(200136, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x0466, requires="Dowsing Machine"),
    "Route 9 - Found Super Repel": LocationData(200137, "Shalour Area", category=['HIDDEN ITEM'], flag_id=0x0467, requires="Dowsing Machine"),
    "Cyllage City - Found Ether": LocationData(200138, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x0468, requires="Dowsing Machine"),
    "Cyllage City - Found Pearl": LocationData(200139, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x0469, requires="Dowsing Machine"),
    "Cyllage City - Found X Speed": LocationData(200140, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x046A, requires="Dowsing Machine"),
    "Cyllage City - Found Protein": LocationData(200141, "Cyllage Area", category=['HIDDEN ITEM'], flag_id=0x046B, requires="Dowsing Machine"),
    # Bulbapedia: on the SW-most menhir north of the Cyllage City entrance, requires Strength.
    "Route 10 - Found Revive": LocationData(200142, "Shalour Area", category=['HIDDEN ITEM'], flag_id=0x046C, requires="Dowsing Machine AND HM04 Strength"),
    "Route 10 - Found Paralyze Heal": LocationData(200143, "Shalour Area", category=['HIDDEN ITEM'], flag_id=0x046D, requires="Dowsing Machine"),
    "Route 10 - Found Burn Heal": LocationData(200144, "Shalour Area", category=['HIDDEN ITEM'], flag_id=0x046E, requires="Dowsing Machine"),
    "Route 11 - Found Super Potion": LocationData(200145, "Shalour Area", category=['HIDDEN ITEM'], flag_id=0x046F, requires="Dowsing Machine"),
    "Route 11 - Found Thunder Stone": LocationData(200146, "Shalour Area", category=['HIDDEN ITEM'], flag_id=0x0470, requires="Dowsing Machine"),
    "Shalour City - Found X Sp. Atk": LocationData(200147, "Shalour Area", category=['HIDDEN ITEM'], flag_id=0x0471, requires="Dowsing Machine"),
    "Shalour City - Found Stardust (recurring)": LocationData(200148, "Shalour Area", category=['HIDDEN ITEM'], flag_id=0x0472, requires="Dowsing Machine"),
    "Shalour City - Found Max Repel": LocationData(200149, "Shalour Area", category=['HIDDEN ITEM'], flag_id=0x0473, requires="Dowsing Machine"),
    "Route 12 - Found Honey (recurring)": LocationData(200150, "Coumarine Area", category=['HIDDEN ITEM'], flag_id=0x0474, requires="Dowsing Machine"),
    "Route 12 - Found Net Ball": LocationData(200151, "Coumarine Area", category=['HIDDEN ITEM'], flag_id=0x0475, requires="Dowsing Machine"),
    "Route 12 - Found Water Stone": LocationData(200152, "Coumarine Area", category=['HIDDEN ITEM'], flag_id=0x0476, requires="HM03 Surf AND Dowsing Machine"),
    "Route 12 - Found Ice Heal": LocationData(200153, "Coumarine Area", category=['HIDDEN ITEM'], flag_id=0x0477, requires="Dowsing Machine"),
    # Azure Bay is Surf-only.
    "Azure Bay - Found Star Piece": LocationData(200154, "Coumarine Area", category=['HIDDEN ITEM'], flag_id=0x0478, requires="Dowsing Machine AND HM03 Surf"),
    # Azure Bay is Surf-only.
    "Azure Bay - Found Hyper Potion": LocationData(200155, "Coumarine Area", category=['HIDDEN ITEM'], flag_id=0x0479, requires="Dowsing Machine AND HM03 Surf"),
    # Azure Bay is Surf-only.
    "Azure Bay - Found Heart Scale": LocationData(200156, "Coumarine Area", category=['HIDDEN ITEM'], flag_id=0x047A, requires="Dowsing Machine AND HM03 Surf"),
    "Coumarine City - Found Elixir": LocationData(200157, "Coumarine Area", category=['HIDDEN ITEM'], flag_id=0x047B, requires="Dowsing Machine"),
    "Coumarine City - Found Awakening": LocationData(200158, "Coumarine Area", category=['HIDDEN ITEM'], flag_id=0x047C, requires="Dowsing Machine"),
    "Coumarine City - Found Max Repel": LocationData(200159, "Coumarine Area", category=['HIDDEN ITEM'], flag_id=0x047D, requires="Dowsing Machine"),
    "Route 13 - Found Guard Spec.": LocationData(200160, "Lumiose Area", category=['HIDDEN ITEM'], flag_id=0x047E, requires="Dowsing Machine"),
    "Route 13 - Found Heat Rock": LocationData(200161, "Lumiose Area", category=['HIDDEN ITEM'], flag_id=0x047F, requires="Dowsing Machine"),
    "Route 13 - Found Nest Ball": LocationData(200162, "Lumiose Area", category=['HIDDEN ITEM'], flag_id=0x0480, requires="Dowsing Machine"),
    # Bulbapedia: across two grind rails in the western ravine path, requires Rock Smash and a grind rail (Roller Skates).
    "Route 13 - Found Hyper Potion": LocationData(200163, "Lumiose Area", category=['HIDDEN ITEM'], flag_id=0x0481, requires="Dowsing Machine AND Roller Skates AND TM94 Rock Smash"),
    # Bulbapedia: across two nearby grind rails in a ravine, requires Roller Skates.
    "Route 13 - Found PP Up": LocationData(200164, "Lumiose Area", category=['HIDDEN ITEM'], flag_id=0x0482, requires="Dowsing Machine AND Roller Skates"),
    "Route 13 - Found X Accuracy": LocationData(200165, "Lumiose Area", category=['HIDDEN ITEM'], flag_id=0x0483, requires="Dowsing Machine"),
    # Bulbapedia: at the end of the first branch east of the Lumiose City Gate, requires Rock Smash.
    "Route 13 - Found Stardust": LocationData(200166, "Lumiose Area", category=['HIDDEN ITEM'], flag_id=0x0484, requires="Dowsing Machine AND TM94 Rock Smash"),
    "Route 13 - Found Fire Stone": LocationData(200167, "Lumiose Area", category=['HIDDEN ITEM'], flag_id=0x0485, requires="Dowsing Machine"),
    "Route 13 - Found Star Piece": LocationData(200168, "Lumiose Area", category=['HIDDEN ITEM'], flag_id=0x0486, requires="Dowsing Machine"),
    "Route 14 - Found Super Potion": LocationData(200169, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0487, requires="Dowsing Machine"),
    "Route 14 - Found Tiny Mushroom": LocationData(200170, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0488, requires="Dowsing Machine"),
    "Route 14 - Found Revive": LocationData(200171, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0489, requires="Dowsing Machine"),
    "Laverre City - Found Tiny Mushroom (recurring)": LocationData(200172, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x048A, requires="Dowsing Machine"),
    "Laverre City - Found Leaf Stone": LocationData(200173, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x048B, requires="Dowsing Machine"),
    "Laverre City - Found Ultra Ball": LocationData(200174, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x048C, requires="Dowsing Machine"),
    "Poké Ball Factory - Found Dusk Ball": LocationData(200175, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x048D, requires="Dowsing Machine"),
    "Poké Ball Factory - Found Burn Heal": LocationData(200176, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x048E, requires="Dowsing Machine"),
    "Poké Ball Factory - Found Poké Ball": LocationData(200177, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x048F, requires="Dowsing Machine"),
    "Poké Ball Factory - Found Hyper Potion": LocationData(200178, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0490, requires="Dowsing Machine"),
    # Bulbapedia: up the waterfall in the eastern stream, requires Rock Smash, Surf, and Waterfall.
    "Route 15 - Found HP Up": LocationData(200179, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0491, requires="Dowsing Machine AND TM94 Rock Smash AND HM03 Surf AND HM05 Waterfall"),
    "Route 15 - Found Antidote": LocationData(200180, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0492, requires="Dowsing Machine"),
    # Bulbapedia: beyond the ledge east of the Leppa Berry tree, requires Surf.
    "Route 15 - Found Tiny Mushroom": LocationData(200181, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0493, requires="Dowsing Machine AND HM03 Surf"),
    "Route 15 - Found X Defense": LocationData(200182, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0494, requires="Dowsing Machine"),
    # Bulbapedia: south on the eastern stream from the bridge, requires Surf.
    "Route 15 - Found Pretty Wing": LocationData(200183, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0495, requires="Dowsing Machine AND HM03 Surf"),
    "Route 16 - Found Repel": LocationData(200184, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0496, requires="Dowsing Machine"),
    # Bulbapedia: southeast of the Fishing Shack on a rock, requires Strength.
    "Route 16 - Found Rare Candy": LocationData(200185, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0497, requires="Dowsing Machine AND HM04 Strength"),
    "Route 16 - Found Big Mushroom": LocationData(200186, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0498, requires="Dowsing Machine"),
    "Route 16 - Found Max Revive": LocationData(200187, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x0499, requires="Dowsing Machine"),
    "Dendemille Town - Found Heal Ball": LocationData(200188, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x049A, requires="Dowsing Machine"),
    "Dendemille Town - Found X Speed": LocationData(200189, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x049B, requires="Dowsing Machine"),
    "Dendemille Town - Found Nugget": LocationData(200190, "Laverre Area", category=['HIDDEN ITEM'], flag_id=0x049C, requires="Dowsing Machine"),
    "Frost Cavern - Found Escape Rope": LocationData(200191, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x049D, requires="Dowsing Machine"),
    "Frost Cavern - Found X Sp. Def": LocationData(200192, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x049E, requires="Dowsing Machine"),
    "Frost Cavern - Found Ice Heal": LocationData(200193, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x049F, requires="Dowsing Machine"),
    "Frost Cavern - Found Dusk Ball": LocationData(200194, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04A0, requires="Dowsing Machine"),
    "Frost Cavern - Found Dire Hit": LocationData(200195, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04A1, requires="Dowsing Machine"),
    "Frost Cavern - Found Pearl": LocationData(200196, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04A2, requires="Dowsing Machine"),
    "Frost Cavern - Found Super Potion": LocationData(200197, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04A3, requires="Dowsing Machine"),
    "Frost Cavern - Found Ice Heal (2)": LocationData(200198, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04A4, requires="Dowsing Machine"),
    "Frost Cavern - Found Elixir": LocationData(200199, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04A5, requires="Dowsing Machine"),
    "Frost Cavern - Found PP Up": LocationData(200200, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04A6, requires="Dowsing Machine"),
    "Route 17 - Found Timer Ball": LocationData(200201, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04A7, requires="Dowsing Machine"),
    "Route 17 - Found Paralyze Heal": LocationData(200202, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04A8, requires="Dowsing Machine"),
    "Anistar City - Found Pretty Wing (recurring)": LocationData(200203, "Anistar Area", category=['HIDDEN ITEM'], flag_id=0x04A9, requires="Dowsing Machine"),
    "Anistar City - Found Escape Rope": LocationData(200204, "Anistar Area", category=['HIDDEN ITEM'], flag_id=0x04AA, requires="Dowsing Machine"),
    "Anistar City - Found Super Repel": LocationData(200205, "Anistar Area", category=['HIDDEN ITEM'], flag_id=0x04AB, requires="Dowsing Machine"),
    "Anistar City - Found Sun Stone": LocationData(200206, "Anistar Area", category=['HIDDEN ITEM'], flag_id=0x04AC, requires="Dowsing Machine"),
    "Route 18 - Found Poké Ball": LocationData(200207, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04AD, requires="Dowsing Machine"),
    "Route 18 - Found Ether": LocationData(200208, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04AE, requires="Dowsing Machine"),
    "Route 18 - Found Honey": LocationData(200209, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04AF, requires="Dowsing Machine"),
    "Route 18 - Found Super Potion": LocationData(200210, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04B0, requires="Dowsing Machine"),
    "Terminus Cave - Found Dusk Ball": LocationData(200211, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04B1, requires="Dowsing Machine"),
    "Terminus Cave - Found Hyper Potion": LocationData(200212, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04B2, requires="Dowsing Machine"),
    # Bulbapedia: requires Rock Smash.
    "Terminus Cave - Found Moon Stone": LocationData(200213, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04B3, requires="Dowsing Machine AND TM94 Rock Smash"),
    "Terminus Cave - Found Max Repel": LocationData(200214, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04B4, requires="Dowsing Machine"),
    "Terminus Cave - Found Iron": LocationData(200215, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04B5, requires="Dowsing Machine"),
    "Terminus Cave - Found Dire Hit": LocationData(200216, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04B6, requires="Dowsing Machine"),
    # Bulbapedia: requires Rock Smash.
    "Terminus Cave - Found Max Potion": LocationData(200217, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04B7, requires="Dowsing Machine AND TM94 Rock Smash"),
    "Terminus Cave - Found Big Nugget": LocationData(200218, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04B8, requires="Dowsing Machine"),
    # Bulbapedia: Rock Smash is required to reach the Zygarde-chamber entrance.
    "Terminus Cave - Found Normal Gem": LocationData(200219, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04B9, requires="Dowsing Machine AND TM94 Rock Smash"),
    "Couriway Town - Found Pretty Wing": LocationData(200220, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04BA, requires="Dowsing Machine"),
    "Couriway Town - Found Ether": LocationData(200221, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04BB, requires="Dowsing Machine"),
    "Couriway Town - Found Burn Heal": LocationData(200222, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04BC, requires="Dowsing Machine"),
    # Bulbapedia states no requirement, but "isolated, single tile of land by the three waterfalls" strongly implies Surf; applied conservatively.
    "Couriway Town - Found Prism Scale (recurring)": LocationData(200223, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04BD, requires="Dowsing Machine AND HM03 Surf"),
    "Route 19 - Found Net Ball": LocationData(200224, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04BE, requires="Dowsing Machine"),
    "Route 19 - Found Antidote": LocationData(200225, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04BF, requires="Dowsing Machine"),
    # Bulbapedia (this key is really Kalos Route 19): under leaves in the southeast corner of the swamp area, requires Surf.
    "Route 19 - Found Damp Rock": LocationData(200226, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04C0, requires="Dowsing Machine AND HM03 Surf"),
    # Bulbapedia (this key is really Kalos Route 19): on the rock next to Pokémon Ranger Clementine in the swamp area, requires Surf.
    "Route 19 - Found Escape Rope": LocationData(200227, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04C1, requires="Dowsing Machine AND HM03 Surf"),
    "Route 19 - Found Timer Ball": LocationData(200228, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04C2, requires="Dowsing Machine"),
    "Snowbelle City - Found Icy Rock": LocationData(200229, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04C3, requires="Dowsing Machine"),
    "Snowbelle City - Found X Sp. Atk": LocationData(200230, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04C4, requires="Dowsing Machine"),
    "Snowbelle City - Found Full Heal": LocationData(200231, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04C5, requires="Dowsing Machine"),
    # Bulbapedia (this key is really Kalos Route 20, Winding Woods): on a stump west of Poké Fan Corey, requires Cut.
    "Route 20 - Found Repeat Ball": LocationData(200232, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04C6, requires="Dowsing Machine AND HM01 Cut"),
    "Route 20 - Found Antidote": LocationData(200233, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04C7, requires="Dowsing Machine"),
    "Route 20 - Found Mental Herb": LocationData(200234, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04C8, requires="Dowsing Machine"),
    "Route 20 - Found Tiny Mushroom": LocationData(200235, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04C9, requires="Dowsing Machine"),
    "Route 20 - Found Balm Mushroom": LocationData(200236, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04CA, requires="Dowsing Machine"),
    # Bulbapedia lists one hidden Honey requiring Surf (among yellow flowers on the western riverbank) and one without; flag mapping is unclear, so Surf is applied to both as a safe fallback.
    "Pokémon Village - Found Honey": LocationData(200237, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04CB, requires="Dowsing Machine AND HM03 Surf"),
    "Pokémon Village - Found Pretty Wing": LocationData(200238, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04CC, requires="Dowsing Machine"),
    # Bulbapedia lists one hidden Honey requiring Surf (among yellow flowers on the western riverbank) and one without; flag mapping is unclear, so Surf is applied to both as a safe fallback.
    "Pokémon Village - Found Honey (2)": LocationData(200239, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04CD, requires="Dowsing Machine AND HM03 Surf"),
    "Route 21 - Found Guard Spec.": LocationData(200240, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04CE, requires="Dowsing Machine"),
    "Route 21 - Found PP Up": LocationData(200241, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04CF, requires="Dowsing Machine"),
    # Bulbapedia (this key is really Kalos Route 21, Dernière Way): in the bare area among the purple flowers, requires Strength.
    "Route 21 - Found Pearl String": LocationData(200242, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04D0, requires="Dowsing Machine AND HM04 Strength"),
    # Bulbapedia (this key is really Kalos Route 21, Dernière Way): on the rock face northwest of the Figy Berry tree, requires Cut, Strength, and Surf.
    "Route 21 - Found Elixir": LocationData(200243, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04D1, requires="Dowsing Machine AND HM01 Cut AND HM04 Strength AND HM03 Surf"),
    # Bush west of the southeastern-most Strength depression, down the waterfall.
    "Route 22 - Found Max Elixir": LocationData(200244, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04D2, requires="Dowsing Machine AND HM03 Surf AND HM05 Waterfall AND HM04 Strength"),
    # Westernmost small rock in the southern part of the area down the waterfall.
    "Route 22 - Found Full Restore": LocationData(200245, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04D3, requires="Dowsing Machine AND HM03 Surf AND HM05 Waterfall"),
    "Victory Road - Found X Attack": LocationData(200246, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04D4, requires="Dowsing Machine"),
    "Victory Road - Found Full Heal": LocationData(200247, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04D5, requires="Dowsing Machine"),
    "Victory Road - Found Hyper Potion": LocationData(200248, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04D6, requires="Dowsing Machine"),
    # Bulbapedia: requires Rock Smash.
    "Victory Road - Found Ultra Ball": LocationData(200249, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04D7, requires="Dowsing Machine AND TM94 Rock Smash"),
    "Victory Road - Found Smooth Rock": LocationData(200250, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04D8, requires="Dowsing Machine"),
    # Bulbapedia: on the rock nearest the southern entrance to the second cave, requires Strength.
    "Victory Road - Found Revive": LocationData(200251, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04D9, requires="Dowsing Machine AND HM04 Strength"),
    "Victory Road - Found Pretty Wing": LocationData(200252, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04DA, requires="Dowsing Machine"),
    "Victory Road - Found Escape Rope": LocationData(200253, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04DB, requires="Dowsing Machine"),
    "Victory Road - Found Max Repel": LocationData(200254, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04DC, requires="Dowsing Machine"),
    "Victory Road - Found X Defense": LocationData(200255, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04DD, requires="Dowsing Machine"),
    # Bulbapedia: south of TM02, requires Surf and Waterfall.
    "Victory Road - Found Max Ether": LocationData(200256, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04DE, requires="Dowsing Machine AND HM03 Surf AND HM05 Waterfall"),
    "Victory Road - Found Star Piece": LocationData(200257, "Victory Road", category=['HIDDEN ITEM'], flag_id=0x04DF, requires="Dowsing Machine"),
    "Couriway Town - Found Poké Ball": LocationData(200258, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04E0, requires="Dowsing Machine"),
    "Kiloude City - Found Max Revive": LocationData(200259, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04E1, requires="Dowsing Machine"),
    "Kiloude City - Found PP Up": LocationData(200260, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04E2, requires="Dowsing Machine"),
    # Bulbapedia: Surf is needed to access the cave.
    "Unknown Dungeon - Found Oval Stone (recurring)": LocationData(200261, "Snowbelle Area", category=['HIDDEN ITEM'], flag_id=0x04E3, requires="Dowsing Machine AND HM03 Surf"),
    "Santalune Forest - Potion item ball disappeared": LocationData(200262, "Santalune Area", category=['FIELD ITEM'], flag_id=0x051A, requires=""),
    "Santalune Forest - Poké Ball item ball disappeared": LocationData(200263, "Santalune Area", category=['FIELD ITEM'], flag_id=0x051B, requires=""),
    "Route 3 - Super Potion item ball disappeared": LocationData(200264, "Santalune Area", category=['FIELD ITEM'], flag_id=0x051C, requires=""),
    # Northeastern-most corner of the route.
    "Route 3 - Revive item ball disappeared": LocationData(200265, "Santalune Area", category=['FIELD ITEM'], flag_id=0x051D, requires="HM01 Cut"),
    # Across the pond by the Santalune Forest entrance.
    "Route 3 - Dawn Stone item ball disappeared": LocationData(200266, "Santalune Area", category=['FIELD ITEM'], flag_id=0x051E, requires="HM03 Surf"),
    "Route 22 - Super Potion item ball disappeared": LocationData(200267, "Victory Road", category=['FIELD ITEM'], flag_id=0x051F, requires=""),
    # Northwest of the route, north of Rising Star Louise. Behind a cuttable tree.
    "Route 22 - Elixir item ball disappeared": LocationData(200268, "Victory Road", category=['FIELD ITEM'], flag_id=0x0520, requires="HM01 Cut"),
    # Up the second waterfall, east after descending the first.
    "Route 22 - Draco Plate item ball disappeared": LocationData(200269, "Victory Road", category=['FIELD ITEM'], flag_id=0x0521, requires="HM03 Surf AND HM05 Waterfall"),
    "Route 4 - Great Ball item ball disappeared": LocationData(200270, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x0522, requires=""),
    "Route 4 - Antidote item ball disappeared": LocationData(200271, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x0523, requires=""),
    "Route 4 - Super Potion item ball disappeared": LocationData(200272, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x0524, requires=""),
    "Route 4 - Repel item ball disappeared": LocationData(200273, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x0525, requires=""),
    "Route 4 - Poison Barb item ball disappeared": LocationData(200274, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x0526, requires=""),
    "Route 4 - Net Ball item ball disappeared": LocationData(200275, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x0527, requires=""),
    "Route 4 - Ether item ball disappeared": LocationData(200276, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x0528, requires=""),
    "Route 5 - Super Potion item ball disappeared": LocationData(200277, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x0529, requires=""),
    "Route 5 - Super Potion item ball disappeared (2)": LocationData(200278, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x052A, requires=""),
    "Route 5 - Great Ball item ball disappeared": LocationData(200279, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x052B, requires=""),
    "Route 5 - TM01 (Hone Claws) item ball disappeared": LocationData(200280, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x052C, requires=""),
    "Route 5 - X Attack item ball disappeared": LocationData(200281, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x052D, requires=""),
    # End of the northern of the two paths blocked by thorny trees, near the
    # Camphrier Town entrance.
    "Route 5 - Sharp Beak item ball disappeared": LocationData(200282, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x052E, requires="HM01 Cut"),
    "Route 6 - X Sp. Atk item ball disappeared": LocationData(200283, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x052F, requires=""),
    "Route 6 - Antidote item ball disappeared": LocationData(200284, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0530, requires=""),
    "Route 6 - X Speed item ball disappeared": LocationData(200285, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0531, requires=""),
    "Route 6 - Paralyze Heal item ball disappeared": LocationData(200286, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0532, requires=""),
    "Route 6 - TM09 (Venosock) item ball disappeared": LocationData(200287, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0533, requires=""),
    "Route 6 - Awakening item ball disappeared": LocationData(200288, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0534, requires=""),
    "Route 6 - Super Repel item ball disappeared": LocationData(200289, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0535, requires=""),
    "Route 6 - Ultra Ball item ball disappeared": LocationData(200290, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0536, requires=""),
    "Route 7 - X Sp. Def item ball disappeared": LocationData(200291, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0537, requires=""),
    "Route 7 - PP Up item ball disappeared": LocationData(200292, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0538, requires=""),
    "Route 7 - Tiny Mushroom item ball disappeared": LocationData(200293, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0539, requires=""),
    # North of the southern Connecting Cave entrance, behind a cuttable tree.
    "Route 7 - Silver Powder item ball disappeared": LocationData(200294, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x053A, requires="HM01 Cut"),
    # Bulbapedia: in the cave's north branch, directly across from the Cyllage City entrance, requires Strength.
    "Connecting Cave - TM40 (Aerial Ace) item ball disappeared": LocationData(200295, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x053B, requires="HM04 Strength"),
    "Route 8 - HP Up item ball disappeared": LocationData(200296, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x053C, requires=""),
    "Route 8 - Leaf Stone item ball disappeared": LocationData(200297, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x053D, requires=""),
    # Bulbapedia: at the end of the narrow path west of the yellow flowers on the cliffside area, requires Strength (previous "HM03 Surf" value was wrong).
    "Route 8 - Water Stone item ball disappeared": LocationData(200298, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x053E, requires="HM04 Strength"),
    "Route 8 - Heart Scale item ball disappeared": LocationData(200299, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x053F, requires=""),
    # Bulbapedia: on the small shallow island in the northwest of the coastal area, requires Surf.
    "Route 8 - TM19 (Roost) item ball disappeared": LocationData(200300, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0540, requires="HM03 Surf"),
    "Route 9 - X Defense item ball disappeared": LocationData(200301, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0541, requires=""),
    "Route 9 - Paralyze Heal item ball disappeared": LocationData(200302, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0542, requires=""),
    "Route 9 - Fire Stone item ball disappeared": LocationData(200303, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0543, requires=""),
    "Route 9 - Dusk Ball item ball disappeared": LocationData(200304, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0544, requires=""),
    "Glittering Cave - Hard Stone item ball disappeared": LocationData(200305, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0545, requires=""),
    "Glittering Cave - TM65 (Shadow Claw) item ball disappeared": LocationData(200306, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x0546, requires=""),
    # Bulbapedia: past two Strength puzzles north of the Cyllage City entrance, requires Strength.
    "Route 10 - TM73 (Thunder Wave) item ball disappeared": LocationData(200307, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0547, requires="HM04 Strength"),
    "Route 10 - Mind Plate item ball disappeared": LocationData(200308, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0548, requires=""),
    "Route 10 - X Accuracy item ball disappeared": LocationData(200309, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0549, requires=""),
    "Route 10 - Thunder Stone item ball disappeared": LocationData(200310, "Shalour Area", category=['FIELD ITEM'], flag_id=0x054A, requires=""),
    # Bulbapedia: north of the Berry tree via a dirt slope west of Brains & Brawn Frank & Sly, requires Cut.
    "Route 11 - TM69 (Rock Polish) item ball disappeared": LocationData(200311, "Shalour Area", category=['FIELD ITEM'], flag_id=0x054B, requires="HM01 Cut"),
    "Route 11 - Hyper Potion item ball disappeared": LocationData(200312, "Shalour Area", category=['FIELD ITEM'], flag_id=0x054C, requires=""),
    "Reflection Cave - Nest Ball item ball disappeared": LocationData(200313, "Shalour Area", category=['FIELD ITEM'], flag_id=0x054D, requires=""),
    "Reflection Cave - Revive item ball disappeared": LocationData(200314, "Shalour Area", category=['FIELD ITEM'], flag_id=0x054E, requires=""),
    "Reflection Cave - Moon Stone item ball disappeared": LocationData(200315, "Shalour Area", category=['FIELD ITEM'], flag_id=0x054F, requires=""),
    "Reflection Cave - Black Belt item ball disappeared": LocationData(200316, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0550, requires=""),
    "Reflection Cave - Hyper Potion item ball disappeared": LocationData(200317, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0551, requires=""),
    "Reflection Cave - Escape Rope item ball disappeared": LocationData(200318, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0552, requires=""),
    "Reflection Cave - Iron item ball disappeared": LocationData(200319, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0553, requires=""),
    "Reflection Cave - Earth Plate item ball disappeared": LocationData(200320, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0554, requires=""),
    "Reflection Cave - TM74 (Gyro Ball) item ball disappeared": LocationData(200321, "Shalour Area", category=['FIELD ITEM'], flag_id=0x0555, requires=""),
    # Bulbapedia: behind the ranch house, requires Cut.
    "Route 12 - Sachet item ball disappeared": LocationData(200322, "Coumarine Area", category=['FIELD ITEM'], flag_id=0x0556, requires="HM01 Cut"),
    "Route 12 - Shiny Stone item ball disappeared": LocationData(200323, "Coumarine Area", category=['FIELD ITEM'], flag_id=0x0557, requires=""),
    "Route 12 - Whipped Dream item ball disappeared": LocationData(200324, "Coumarine Area", category=['FIELD ITEM'], flag_id=0x0558, requires=""),
    "Parfum Palace - Guard Spec. item ball disappeared": LocationData(200325, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x0559, requires=""),
    # Bulbapedia: down a path between the fields of yellow flowers, requires Cut.
    "Route 12 - Leftovers item ball disappeared": LocationData(200326, "Coumarine Area", category=['FIELD ITEM'], flag_id=0x055A, requires="HM01 Cut"),
    # Azure Bay is Surf-only.
    "Azure Bay - Deep Sea Tooth item ball disappeared": LocationData(200327, "Coumarine Area", category=['FIELD ITEM'], flag_id=0x055B, requires="HM03 Surf"),
    # Azure Bay is Surf-only.
    "Azure Bay - TM81 (X-Scissor) item ball disappeared": LocationData(200328, "Coumarine Area", category=['FIELD ITEM'], flag_id=0x055C, requires="HM03 Surf"),
    # Azure Bay is Surf-only.
    "Azure Bay - Dive Ball item ball disappeared": LocationData(200329, "Coumarine Area", category=['FIELD ITEM'], flag_id=0x055D, requires="HM03 Surf"),
    # Azure Bay is Surf-only.
    "Azure Bay - Big Pearl item ball disappeared": LocationData(200330, "Coumarine Area", category=['FIELD ITEM'], flag_id=0x055E, requires="HM03 Surf"),
    # Azure Bay is Surf-only.
    "Azure Bay - Splash Plate item ball disappeared": LocationData(200331, "Coumarine Area", category=['FIELD ITEM'], flag_id=0x055F, requires="HM03 Surf"),
    # Bulbapedia: across the grind rail east of the Coumarine City entrance, requires Roller Skates.
    "Route 13 - Smooth Rock item ball disappeared": LocationData(200332, "Lumiose Area", category=['FIELD ITEM'], flag_id=0x0560, requires="Roller Skates"),
    # Bulbapedia: across a small ravine via the grind rail to the north, requires Roller Skates and Rock Smash.
    "Route 13 - Burn Heal item ball disappeared": LocationData(200333, "Lumiose Area", category=['FIELD ITEM'], flag_id=0x0561, requires="Roller Skates AND TM94 Rock Smash"),
    # Bulbapedia: at the end of the western ravine path across two grind rails, requires Roller Skates and Rock Smash.
    "Route 13 - TM57 (Charge Beam) item ball disappeared": LocationData(200334, "Lumiose Area", category=['FIELD ITEM'], flag_id=0x0562, requires="Roller Skates AND TM94 Rock Smash"),
    "Route 13 - Flame Plate item ball disappeared": LocationData(200335, "Lumiose Area", category=['FIELD ITEM'], flag_id=0x0563, requires=""),
    # Bulbapedia: in a small ravine west of the stairs to the Lumiose City Gate, accessible via the nearby grind rail (Roller Skates).
    "Route 13 - Sun Stone item ball disappeared": LocationData(200336, "Lumiose Area", category=['FIELD ITEM'], flag_id=0x0564, requires="Roller Skates"),
    # Bulbapedia: requires Rock Smash.
    "Route 13 - Rare Candy item ball disappeared": LocationData(200337, "Lumiose Area", category=['FIELD ITEM'], flag_id=0x0565, requires="TM94 Rock Smash"),
    "Route 14 - Cleanse Tag item ball disappeared": LocationData(200338, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0566, requires=""),
    "Route 14 - Big Mushroom item ball disappeared": LocationData(200339, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0567, requires=""),
    "Route 14 - Hyper Potion item ball disappeared": LocationData(200340, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0568, requires=""),
    # Bulbapedia: across the pond just east of the Laverre City entrance, requires Surf.
    "Route 14 - Damp Rock item ball disappeared": LocationData(200341, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0569, requires="HM03 Surf"),
    "Route 14 - Spell Tag item ball disappeared": LocationData(200342, "Laverre Area", category=['FIELD ITEM'], flag_id=0x056A, requires=""),
    # Bulbapedia: at the end of a narrow path south in the northeastern-most branch of the route, requires Cut.
    "Route 14 - TM61 (Will-O-Wisp) item ball disappeared": LocationData(200343, "Laverre Area", category=['FIELD ITEM'], flag_id=0x056B, requires="HM01 Cut"),
    "Poké Ball Factory - Max Revive item ball disappeared": LocationData(200344, "Laverre Area", category=['FIELD ITEM'], flag_id=0x056C, requires=""),
    "Poké Ball Factory - Max Ether item ball disappeared": LocationData(200345, "Laverre Area", category=['FIELD ITEM'], flag_id=0x056D, requires=""),
    "Poké Ball Factory - Quick Ball item ball disappeared": LocationData(200346, "Laverre Area", category=['FIELD ITEM'], flag_id=0x056E, requires=""),
    "Poké Ball Factory - Metal Coat item ball disappeared": LocationData(200347, "Laverre Area", category=['FIELD ITEM'], flag_id=0x056F, requires=""),
    "Poké Ball Factory - Timer Ball item ball disappeared": LocationData(200348, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0570, requires=""),
    "Route 15 - Net Ball item ball disappeared": LocationData(200349, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0571, requires=""),
    "Route 15 - Revive item ball disappeared": LocationData(200350, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0572, requires=""),
    "Route 15 - Dire Hit item ball disappeared": LocationData(200351, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0573, requires=""),
    # Bulbapedia: at the north end of the western stream, requires Surf.
    "Route 15 - PP Up item ball disappeared": LocationData(200352, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0574, requires="HM03 Surf"),
    "Route 15 - Full Heal item ball disappeared": LocationData(200353, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0575, requires=""),
    # Bulbapedia: behind a cracked wall northeast from the western bridge, requires Rock Smash.
    "Route 15 - Protein item ball disappeared": LocationData(200354, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0576, requires="TM94 Rock Smash"),
    # Bulbapedia: behind a cracked wall northeast from the eastern bridge, requires Rock Smash.
    "Route 15 - Macho Brace item ball disappeared": LocationData(200355, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0577, requires="TM94 Rock Smash"),
    # Bulbapedia: up the waterfall in the eastern stream, requires Rock Smash, Surf, and Waterfall.
    "Route 15 - Stone Plate item ball disappeared": LocationData(200356, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0578, requires="TM94 Rock Smash AND HM03 Surf AND HM05 Waterfall"),
    # Bulbapedia: accessed from Route 16, requires Cut, Surf, and Waterfall.
    "Route 15 - TM97 (Dark Pulse) item ball disappeared": LocationData(200357, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0579, requires="HM01 Cut AND HM03 Surf AND HM05 Waterfall"),
    # Bulbapedia: northeast of the long grass on the west side of the Lost Hotel, requires Cut.
    "Route 16 - Rare Candy item ball disappeared": LocationData(200358, "Laverre Area", category=['FIELD ITEM'], flag_id=0x057A, requires="HM01 Cut"),
    "Route 16 - Max Potion item ball disappeared": LocationData(200359, "Laverre Area", category=['FIELD ITEM'], flag_id=0x057B, requires=""),
    # Bulbapedia: southeast of the Fishing Shack, requires Strength.
    "Route 16 - Fist Plate item ball disappeared": LocationData(200360, "Laverre Area", category=['FIELD ITEM'], flag_id=0x057C, requires="HM04 Strength"),
    "Route 16 - Dive Ball item ball disappeared": LocationData(200361, "Laverre Area", category=['FIELD ITEM'], flag_id=0x057D, requires=""),
    "Lost Hotel - Smoke Ball item ball disappeared": LocationData(200362, "Laverre Area", category=['FIELD ITEM'], flag_id=0x057E, requires=""),
    # Bulbapedia: requires knowing the skate tricks 360 and Backflip (Roller Skates).
    "Lost Hotel - Twisted Spoon item ball disappeared": LocationData(200363, "Laverre Area", category=['FIELD ITEM'], flag_id=0x057F, requires="Roller Skates"),
    # Bulbapedia: requires Rock Smash and the skate tricks 360 and Backflip (Roller Skates).
    "Lost Hotel - TM95 (Snarl) item ball disappeared": LocationData(200364, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0580, requires="Roller Skates AND TM94 Rock Smash"),
    # Bulbapedia: behind the middle cracked wall in the south hall, requires Rock Smash.
    "Lost Hotel - Dread Plate item ball disappeared": LocationData(200365, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0581, requires="TM94 Rock Smash"),
    # Bulbapedia: between a pair of cracked walls, requires Rock Smash.
    "Lost Hotel - Protector item ball disappeared": LocationData(200366, "Laverre Area", category=['FIELD ITEM'], flag_id=0x0582, requires="TM94 Rock Smash"),
    # Bulbapedia: down the waterfall, immediately to the northeast, requires Surf and Waterfall.
    "Frost Cavern - Heart Scale item ball disappeared": LocationData(200367, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0583, requires="HM03 Surf AND HM05 Waterfall"),
    # Bulbapedia: down the waterfall, at the far east end of the river, requires Surf and Waterfall.
    "Frost Cavern - TM71 (Stone Edge) item ball disappeared": LocationData(200368, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0584, requires="HM03 Surf AND HM05 Waterfall"),
    "Frost Cavern - Hyper Potion item ball disappeared": LocationData(200369, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0585, requires=""),
    "Frost Cavern - Ice Heal item ball disappeared": LocationData(200370, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0586, requires=""),
    "Frost Cavern - Max Repel item ball disappeared": LocationData(200371, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0587, requires=""),
    # Bulbapedia: in the southwest corner of 2F, at the end of the stream, requires Surf.
    "Frost Cavern - Never-Melt Ice item ball disappeared": LocationData(200372, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0588, requires="HM03 Surf"),
    "Frost Cavern - TM79 (Frost Breath) item ball disappeared": LocationData(200373, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0589, requires=""),
    "Frost Cavern - Ether item ball disappeared": LocationData(200374, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x058A, requires=""),
    "Frost Cavern - Zinc item ball disappeared": LocationData(200375, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x058B, requires=""),
    # Bulbapedia: in the room with the Ice Rock on 2F, across the stream west of Battle Girl Kinsey, requires Surf.
    "Frost Cavern - Icy Rock item ball disappeared": LocationData(200376, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x058C, requires="HM03 Surf"),
    "Route 17 - Icicle Plate item ball disappeared": LocationData(200377, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x058D, requires=""),
    "Route 17 - Calcium item ball disappeared": LocationData(200378, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x058E, requires=""),
    "Route 17 - Rare Candy item ball disappeared": LocationData(200379, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x058F, requires=""),
    "Route 18 - Hyper Potion item ball disappeared": LocationData(200380, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0590, requires=""),
    # Bulbapedia (this key is really Kalos Route 18): down the grind rail by the Wacan Berry tree; Bulbapedia states only "requires Cut" but the item sits past a grind rail, so Roller Skates is added conservatively to avoid an unreachable placement.
    "Route 18 - PP Up item ball disappeared": LocationData(200381, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0591, requires="HM01 Cut AND Roller Skates"),
    # Bulbapedia (this key is really Kalos Route 18): requires Rock Smash.
    "Route 18 - X Defense item ball disappeared": LocationData(200382, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0592, requires="TM94 Rock Smash"),
    "Route 18 - Max Ether item ball disappeared": LocationData(200383, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0593, requires=""),
    # Bulbapedia: requires Rock Smash.
    "Terminus Cave - Star Piece item ball disappeared": LocationData(200384, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0594, requires="TM94 Rock Smash"),
    # Bulbapedia: requires Rock Smash.
    "Terminus Cave - Heat Rock item ball disappeared": LocationData(200385, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0595, requires="TM94 Rock Smash"),
    "Terminus Cave - Escape Rope item ball disappeared": LocationData(200386, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0596, requires=""),
    "Terminus Cave - Reaper Cloth item ball disappeared": LocationData(200387, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0597, requires=""),
    "Terminus Cave - Dusk Stone item ball disappeared": LocationData(200388, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0598, requires=""),
    "Terminus Cave - X Attack item ball disappeared": LocationData(200389, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x0599, requires=""),
    # Bulbapedia: requires Rock Smash.
    "Terminus Cave - Elixir item ball disappeared": LocationData(200390, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x059A, requires="TM94 Rock Smash"),
    "Terminus Cave - Full Heal item ball disappeared": LocationData(200391, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x059B, requires=""),
    "Terminus Cave - Iron Plate item ball disappeared": LocationData(200392, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x059C, requires=""),
    # Bulbapedia: requires Rock Smash.
    "Terminus Cave - TM30 (Shadow Ball) item ball disappeared": LocationData(200393, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x059D, requires="TM94 Rock Smash"),
    "Terminus Cave - Griseous Orb item ball disappeared": LocationData(200394, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x059E, requires=""),
    # Bulbapedia: same chamber gate as Found Normal Gem, requires Rock Smash.
    "Terminus Cave - Dragon Scale item ball disappeared": LocationData(200395, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x059F, requires="TM94 Rock Smash"),
    "Terminus Cave - TM31 (Brick Break) item ball disappeared": LocationData(200396, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05A0, requires=""),
    "Route 19 - Max Revive item ball disappeared": LocationData(200397, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05A1, requires=""),
    "Route 19 - HP Up item ball disappeared": LocationData(200398, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05A2, requires=""),
    # Bulbapedia (this key is really Kalos Route 19): in the southwest corner of the swamp area, requires Surf.
    "Route 19 - Rare Bone item ball disappeared": LocationData(200399, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05A3, requires="HM03 Surf"),
    # Bulbapedia (this key is really Kalos Route 19): at the south end of the yellow flowers at the top of the stairs at the end of the swamp area, requires Surf.
    "Route 19 - PP Up item ball disappeared": LocationData(200400, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05A4, requires="HM03 Surf"),
    # Bulbapedia (this key is really Kalos Route 19): in the far north at the end of the swamp area, requires Surf and Strength.
    "Route 19 - Toxic Plate item ball disappeared": LocationData(200401, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05A5, requires="HM03 Surf AND HM04 Strength"),
    # Bulbapedia (this key is really Kalos Route 19): west of the Couriway Town Gate across the swamp area, requires Surf.
    "Route 19 - TM36 (Sludge Bomb) item ball disappeared": LocationData(200402, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05A6, requires="HM03 Surf"),
    "Route 20 - Paralyze Heal item ball disappeared": LocationData(200403, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05A7, requires=""),
    # Bulbapedia (this key is really Kalos Route 20, Winding Woods): in the middle of the red flowers, requires Cut.
    "Route 20 - Protein item ball disappeared": LocationData(200404, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05A8, requires="HM01 Cut"),
    "Route 20 - Meadow Plate item ball disappeared": LocationData(200405, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05A9, requires=""),
    "Route 20 - X Accuracy item ball disappeared": LocationData(200406, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05AA, requires=""),
    # Bulbapedia (this key is really Kalos Route 20, Winding Woods): east, west, south, then west from the Pokémon Village entrance, requires Cut.
    "Route 20 - TM53 (Energy Ball) item ball disappeared": LocationData(200407, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05AB, requires="HM01 Cut"),
    "Pokémon Village - Max Ether item ball disappeared": LocationData(200408, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05AC, requires=""),
    "Pokémon Village - Full Restore item ball disappeared": LocationData(200409, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05AD, requires=""),
    # Bulbapedia: in the patch of yellow flowers on the western riverbank, requires Surf.
    "Pokémon Village - Pixie Plate item ball disappeared": LocationData(200410, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05AE, requires="HM03 Surf"),
    # Bulbapedia: at the top of the waterfall, requires Surf and Waterfall.
    "Pokémon Village - TM29 (Psychic) item ball disappeared": LocationData(200411, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05AF, requires="HM03 Surf AND HM05 Waterfall"),
    # Bulbapedia: north of the Snowbelle City Gate, up the northern leg of the stream, requires Surf.
    "Route 21 - Insect Plate item ball disappeared": LocationData(200412, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05B0, requires="HM03 Surf"),
    # Bulbapedia: in the southwestern-most corner of the route, by Veteran Trisha, requires Cut.
    "Route 21 - Elixir item ball disappeared": LocationData(200413, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05B1, requires="HM01 Cut"),
    # Bulbapedia: requires Cut, Strength, and Surf.
    "Route 21 - TM22 (Solar Beam) item ball disappeared": LocationData(200414, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05B2, requires="HM01 Cut AND HM04 Strength AND HM03 Surf"),
    # Bulbapedia: on the south side of the southern leg of the stream, requires Cut, Strength, and Surf.
    "Route 21 - Rare Candy item ball disappeared": LocationData(200415, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05B3, requires="HM01 Cut AND HM04 Strength AND HM03 Surf"),
    # Bulbapedia: in the far northwest of the route, across the pond, requires Strength and Surf.
    "Route 21 - Repeat Ball item ball disappeared": LocationData(200416, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05B4, requires="HM04 Strength AND HM03 Surf"),
    "Victory Road - Dusk Ball item ball disappeared": LocationData(200417, "Victory Road", category=['FIELD ITEM'], flag_id=0x05B5, requires=""),
    # Bulbapedia: requires Rock Smash.
    "Victory Road - TM03 (Psyshock) item ball disappeared": LocationData(200418, "Victory Road", category=['FIELD ITEM'], flag_id=0x05B6, requires="TM94 Rock Smash"),
    # Bulbapedia: on the cliff through the northwest exit of the second cave, north of Brains & Brawn Arman & Hugo, requires Strength.
    "Victory Road - Rare Candy item ball disappeared": LocationData(200419, "Victory Road", category=['FIELD ITEM'], flag_id=0x05B7, requires="HM04 Strength"),
    "Victory Road - Carbos item ball disappeared": LocationData(200420, "Victory Road", category=['FIELD ITEM'], flag_id=0x05B8, requires=""),
    # Bulbapedia: past a cracked wall, requires Rock Smash.
    "Victory Road - PP Up item ball disappeared": LocationData(200421, "Victory Road", category=['FIELD ITEM'], flag_id=0x05B9, requires="TM94 Rock Smash"),
    # Bulbapedia: behind a cracked wall, requires Rock Smash.
    "Victory Road - Zinc item ball disappeared": LocationData(200422, "Victory Road", category=['FIELD ITEM'], flag_id=0x05BA, requires="TM94 Rock Smash"),
    "Victory Road - Max Elixir item ball disappeared": LocationData(200423, "Victory Road", category=['FIELD ITEM'], flag_id=0x05BB, requires=""),
    "Victory Road - Dragon Fang item ball disappeared": LocationData(200424, "Victory Road", category=['FIELD ITEM'], flag_id=0x05BC, requires=""),
    "Victory Road - Full Restore item ball disappeared": LocationData(200425, "Victory Road", category=['FIELD ITEM'], flag_id=0x05BD, requires=""),
    # Bulbapedia: at the northeast of the area at the top of the waterfall, requires Surf and Waterfall.
    "Victory Road - TM02 (Dragon Claw) item ball disappeared": LocationData(200426, "Victory Road", category=['FIELD ITEM'], flag_id=0x05BE, requires="HM03 Surf AND HM05 Waterfall"),
    "Camphrier Town - X Attack item ball disappeared": LocationData(200427, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x05BF, requires=""),
    "Ambrette Town - Pearl item ball disappeared": LocationData(200428, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x05C0, requires=""),
    "Cyllage City - Super Potion item ball disappeared": LocationData(200429, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x05C1, requires=""),
    "Cyllage City - X Sp. Atk item ball disappeared": LocationData(200430, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x05C2, requires=""),
    "Cyllage City - X Defense item ball disappeared": LocationData(200431, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x05C3, requires=""),
    "Geosenge Town - Timer Ball item ball disappeared": LocationData(200432, "Shalour Area", category=['FIELD ITEM'], flag_id=0x05C4, requires=""),
    "Coumarine City - Sky Plate item ball disappeared": LocationData(200433, "Coumarine Area", category=['FIELD ITEM'], flag_id=0x05C5, requires=""),
    "Laverre City - Ether item ball disappeared": LocationData(200434, "Laverre Area", category=['FIELD ITEM'], flag_id=0x05C6, requires=""),
    "Dendemille Town - Big Root item ball disappeared": LocationData(200435, "Laverre Area", category=['FIELD ITEM'], flag_id=0x05C7, requires=""),
    "Couriway Town - Rare Candy item ball disappeared": LocationData(200436, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05C8, requires=""),
    "Couriway Town - Max Potion item ball disappeared": LocationData(200437, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05C9, requires=""),
    # Bulbapedia: up the waterfall southeast of the Couriway Hotel, requires Surf and Waterfall.
    "Couriway Town - TM80 (Rock Slide) item ball disappeared": LocationData(200438, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05CA, requires="HM03 Surf AND HM05 Waterfall"),
    "Snowbelle City - Full Restore item ball disappeared": LocationData(200439, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05CB, requires=""),
    "Route 7 - Heal Ball item ball disappeared": LocationData(200440, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x05CC, requires=""),
    "Shabboneau Castle - Escape Rope item ball disappeared": LocationData(200441, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x05CD, requires=""),
    "Parfum Palace - Ether item ball disappeared": LocationData(200442, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x05CE, requires=""),
    "Parfum Palace - Amulet Coin item ball disappeared": LocationData(200443, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x05CF, requires=""),
    "Parfum Palace - Antidote item ball disappeared": LocationData(200444, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x05D0, requires=""),
    "Kalos Power Plant - Zap Plate item ball disappeared": LocationData(200445, "Lumiose Area", category=['FIELD ITEM'], flag_id=0x05D1, requires=""),
    "Lysandre Labs - Hyper Potion item ball disappeared": LocationData(200446, "Anistar Area", category=['FIELD ITEM'], flag_id=0x05D2, requires=""),
    "Lysandre Labs - Black Glasses item ball disappeared": LocationData(200447, "Anistar Area", category=['FIELD ITEM'], flag_id=0x05D3, requires=""),
    "Lysandre Labs - Revive item ball disappeared": LocationData(200448, "Anistar Area", category=['FIELD ITEM'], flag_id=0x05D4, requires=""),
    "Lysandre Labs - Rare Candy item ball disappeared": LocationData(200449, "Anistar Area", category=['FIELD ITEM'], flag_id=0x05D5, requires=""),
    # Bulbapedia: accessed by surfing south of the main path and scaling down a waterfall.
    "Chamber of Emptiness - Spooky Plate item ball disappeared": LocationData(200450, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05D6, requires="HM03 Surf AND HM05 Waterfall"),
    "Parfum Palace - Revive item ball disappeared": LocationData(200451, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x05D7, requires=""),
    "Parfum Palace - Super Potion item ball disappeared": LocationData(200452, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x05D8, requires=""),
    "Santalune Forest - Potion item ball disappeared (2)": LocationData(200453, "Santalune Area", category=['FIELD ITEM'], flag_id=0x05D9, requires=""),
    "Shalour City - Max Ether item ball disappeared": LocationData(200454, "Shalour Area", category=['FIELD ITEM'], flag_id=0x05DA, requires=""),
    "Kiloude City - Nugget item ball disappeared": LocationData(200455, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05DB, requires=""),
    "Route 14 - Rare Candy item ball disappeared": LocationData(200456, "Laverre Area", category=['FIELD ITEM'], flag_id=0x05DC, requires=""),
    "Santalune Forest - Potion item ball disappeared (3)": LocationData(200457, "Santalune Area", category=['FIELD ITEM'], flag_id=0x05DD, requires=""),
    "Santalune Forest - Antidote item ball disappeared": LocationData(200458, "Santalune Area", category=['FIELD ITEM'], flag_id=0x05DE, requires=""),
    # Northeast of the southern part of the area down the waterfall.
    "Route 22 - TM26 (Earthquake) item ball disappeared": LocationData(200459, "Victory Road", category=['FIELD ITEM'], flag_id=0x05DF, requires="HM03 Surf AND HM05 Waterfall AND HM04 Strength"),
    "Camphrier Town - Star Piece item ball disappeared": LocationData(200460, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x05E0, requires=""),
    # Azure Bay is Surf-only.
    "Azure Bay - Deep Sea Scale item ball disappeared": LocationData(200461, "Coumarine Area", category=['FIELD ITEM'], flag_id=0x05E1, requires="HM03 Surf"),
    "Terminus Cave - Adamant Orb item ball disappeared": LocationData(200462, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05E2, requires=""),
    "Terminus Cave - Lustrous Orb item ball disappeared": LocationData(200463, "Snowbelle Area", category=['FIELD ITEM'], flag_id=0x05E3, requires=""),
    "Geosenge Town - Soft Sand item ball disappeared": LocationData(200464, "Shalour Area", category=['FIELD ITEM'], flag_id=0x05E4, requires=""),
    "Route 7 - Miracle Seed item ball disappeared": LocationData(200465, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x05E5, requires=""),
    "Glittering Cave - Escape Rope item ball disappeared": LocationData(200466, "Cyllage Area", category=['FIELD ITEM'], flag_id=0x05E6, requires=""),
    # requires was "HM01 Cut", which gated the Cut HM behind already owning Cut.
    # That made the location permanently unreachable, so it never appeared in
    # logic and could never hold a progression item.
    "Parfum Palace - HM01 (Cut) item ball disappeared": LocationData(200467, "Camphrier Area", category=['FIELD ITEM'], flag_id=0x05E7, requires=""),
    "Victory Road - Quick Ball item ball disappeared": LocationData(200468, "Victory Road", category=['FIELD ITEM'], flag_id=0x05E8, requires=""),
    # REMOVED: the nine Coumarine City Pokédex diplomas (ids 200469-200477,
    # flags 0x0A76-0x0A7E). Each needs a completed Pokédex; the National one is
    # outright impossible without transfers, and the rest are unreasonable in a
    # randomised run. They were in Coumarine Area with requires="", so Fill
    # treated them as early and could strand progression on them.
    # Ids 200469-200477 are permanently retired, not reused.
    "Camphrier Town - [Daily] Received Sweet Heart from maid": LocationData(200478, "Camphrier Area", category=['ITEM GIFT'], flag_id=0x0B90, requires=""),
    "Ambrette Town - [Daily] Exchanged a Poké Ball for a Dive Ball with the punk guy": LocationData(200479, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x0BA5, requires=""),
    "Lumiose City (South Boulevard) - [Daily] Received Rare Candy from male scientist for a chain length of at least 31 Pokémon with the Poké Radar": LocationData(200480, "Lumiose Area", category=['ITEM GIFT'], flag_id=0x0BA6, requires=""),
    "Ambrette Town - [Daily] Received Health Wing from woman for showing a Pokémon with a Speed stat equals or higher than requested": LocationData(200481, "Cyllage Area", category=['ITEM GIFT'], flag_id=0x0BAC, requires=""),
    "Coumarine City - [Daily] Picked the random berry from the empty stand": LocationData(200484, "Coumarine Area", category=['ITEM GIFT'], flag_id=0x0BB3, requires=""),
    "Camphrier Town - [Daily] Received a berry from man for showing him a Pokémon of the requested type": LocationData(200485, "Camphrier Area", category=['ITEM GIFT'], flag_id=0x0BB7, requires=""),
    "Lumiose City (South Boulevard) - [Daily] Received PP Max from male scientist for a chain length of 21-30 Pokémon with the Poké Radar": LocationData(200487, "Lumiose Area", category=['ITEM GIFT'], flag_id=0x0BBD, requires=""),
    "Lumiose City (South Boulevard) - [Daily] Received PP Up from male scientist for a chain length of 11-20 Pokémon with the Poké Radar": LocationData(200488, "Lumiose Area", category=['ITEM GIFT'], flag_id=0x0BBE, requires=""),
    "Lumiose City (South Boulevard) - [Daily] Received Ultra Ball from male scientist for a chain length of 1-10 Pokémon with the Poké Radar": LocationData(200489, "Lumiose Area", category=['ITEM GIFT'], flag_id=0x0BBF, requires=""),
    "Coumarine City - [Daily] Received Heart Scale from Tierno for showing him a Pokémon with the requested dance move": LocationData(200490, "Coumarine Area", category=['ITEM GIFT'], flag_id=0x0BC5, requires=""),
    "Lumiose City (Lysandre Cafe) - Team Flame Grunt M Battle": LocationData(201001, "Lumiose Area", category=["TRAINER"], flag_id=0x0189, requires=""),
    "Lumiose City (Lysandre Cafe) - Team Flame Grunt F Battle": LocationData(201002, "Lumiose Area", category=["TRAINER"], flag_id=0x018A, requires=""),
    "Victory Road (Entrance) - Ace Trainer Robbie Battle": LocationData(201003, "Victory Road", category=["TRAINER"], flag_id=0x0301, requires=""),
    "Route 12 - Battled Youngster Aidan": LocationData(201004, "Coumarine Area", category=["TRAINER"], flag_id=0x06CD, requires=""),
    "Santalune Forest - Battled Lass Lise": LocationData(201005, "Santalune Area", category=["TRAINER"], flag_id=0x06CF, requires=""),
    "Route 8 (Cliffside) - Battled Sky Trainer Howe": LocationData(201006, "Cyllage Area", category=["TRAINER"], flag_id=0x06E0, requires=""),
    "Reflection Cave (B1F) - Battled Ace Trainer Emil": LocationData(201007, "Shalour Area", category=["TRAINER"], flag_id=0x06E7, requires=""),
    "Lumiose City (Gym 4F) - Ace Trainer Mathis": LocationData(201008, "Lumiose Area", category=["TRAINER"], flag_id=0x06E8, requires=""),
    "Lumiose City (Gym 4F) - Ace Trainer Maxim": LocationData(201009, "Lumiose Area", category=["TRAINER"], flag_id=0x06E9, requires=""),
    "Lumiose City (Gym 4F) - Ace Trainer Rico": LocationData(201010, "Lumiose Area", category=["TRAINER"], flag_id=0x06EA, requires=""),
    "Snowbelle City (Gym) - Ace Trainer Theo": LocationData(201011, "Snowbelle Area", category=["TRAINER"], flag_id=0x06EB, requires=""),
    "Snowbelle City (Gym) - Ace Trainer Viktor": LocationData(201012, "Snowbelle Area", category=["TRAINER"], flag_id=0x06EC, requires=""),
    "Santalune Forest - Battled Youngster Joey": LocationData(201013, "Santalune Area", category=["TRAINER"], flag_id=0x06F0, requires=""),
    "Route 2 - Battled Youngster Austin": LocationData(201014, "Santalune Area", category=["TRAINER"], flag_id=0x06F1, requires=""),
    "Santalune City (Gym) - Battled Youngster David": LocationData(201015, "Santalune Area", category=["TRAINER"], flag_id=0x06F3, requires=""),
    "Santalune City (Gym) - Battled Youngster Zachary": LocationData(201016, "Santalune Area", category=["TRAINER"], flag_id=0x06F4, requires=""),
    "Route 5 - Battled Youngster Keita": LocationData(201017, "Camphrier Area", category=["TRAINER"], flag_id=0x06F5, requires=""),
    "Route 5 - Battled Youngster Anthony": LocationData(201018, "Camphrier Area", category=["TRAINER"], flag_id=0x06F6, requires=""),
    "Route 6 - Battled Youngster Jacob": LocationData(201019, "Cyllage Area", category=["TRAINER"], flag_id=0x06F7, requires=""),
    "Route 6 - Battled Youngster Tyler": LocationData(201020, "Cyllage Area", category=["TRAINER"], flag_id=0x06F8, requires=""),
    "Santalune Forest - Battled Lass Anna": LocationData(201021, "Santalune Area", category=["TRAINER"], flag_id=0x06F9, requires=""),
    "Route 22 - Battled Lass Elin": LocationData(201022, "Victory Road", category=["TRAINER"], flag_id=0x06FA, requires=""),
    "Route 22 - Battled Lass Elsa": LocationData(201023, "Victory Road", category=["TRAINER"], flag_id=0x06FB, requires=""),
    "Santalune City (Gym) - Battled Lass Charlotte": LocationData(201024, "Santalune Area", category=["TRAINER"], flag_id=0x06FC, requires=""),
    "Route 3 - Battled Schoolboy Brighton": LocationData(201025, "Santalune Area", category=["TRAINER"], flag_id=0x06FD, requires=""),
    "Route 22 - Battled Schoolboy Rabbie": LocationData(201026, "Victory Road", category=["TRAINER"], flag_id=0x06FE, requires=""),
    "Route 3 - Battled Schoolgirl Bridget": LocationData(201027, "Santalune Area", category=["TRAINER"], flag_id=0x0700, requires=""),
    "Route 22 - Battled Schoolgirl Mackenzie": LocationData(201028, "Victory Road", category=["TRAINER"], flag_id=0x0701, requires=""),
    "Route 3 - Battled Preschooler Oliver": LocationData(201029, "Santalune Area", category=["TRAINER"], flag_id=0x0703, requires=""),
    "Route 4 - Battled Preschooler Adrian": LocationData(201030, "Camphrier Area", category=["TRAINER"], flag_id=0x0704, requires=""),
    "Route 3 - Battled Preschooler Ella": LocationData(201031, "Santalune Area", category=["TRAINER"], flag_id=0x0705, requires=""),
    "Route 4 - Battled Preschooler Mia": LocationData(201032, "Camphrier Area", category=["TRAINER"], flag_id=0x0706, requires=""),
    "Route 22 - Battled Rising Star Loïc": LocationData(201033, "Victory Road", category=["TRAINER"], flag_id=0x0707, requires=""),
    "Route 5 - Battled Rising Star Hamish": LocationData(201034, "Camphrier Area", category=["TRAINER"], flag_id=0x0708, requires=""),
    "Route 22 - Battled Rising Star Louise": LocationData(201035, "Victory Road", category=["TRAINER"], flag_id=0x0709, requires=""),
    "Cyllage City (Gym) - Battled Rising Star Manon": LocationData(201036, "Cyllage Area", category=["TRAINER"], flag_id=0x070B, requires=""),
    "Cyllage City (Gym) - Battled Rising Star Didier": LocationData(201037, "Cyllage Area", category=["TRAINER"], flag_id=0x070C, requires=""),
    "Route 22 - Battled Ace Trainer Adelbert": LocationData(201038, "Victory Road", category=["TRAINER"], flag_id=0x070D, requires=""),
    "Route 22 - Battled Ace Trainer Hilde": LocationData(201039, "Victory Road", category=["TRAINER"], flag_id=0x070E, requires=""),
    "Route 4 - Battled Poké Fan Gabe": LocationData(201040, "Camphrier Area", category=["TRAINER"], flag_id=0x070F, requires=""),
    "Route 4 - Battled Poké Fan Agnes": LocationData(201041, "Camphrier Area", category=["TRAINER"], flag_id=0x0710, requires=""),
    "Route 6 - Battled Poké Fan Family Jan & Erin": LocationData(201042, "Cyllage Area", category=["TRAINER"], flag_id=0x0711, requires=""),
    "Route 4 - Battled Gardener Wheaton": LocationData(201043, "Camphrier Area", category=["TRAINER"], flag_id=0x0712, requires=""),
    "Route 4 - Battled Gardener Fabian": LocationData(201044, "Camphrier Area", category=["TRAINER"], flag_id=0x0713, requires=""),
    "Route 4 - Battled Gardener Grover": LocationData(201045, "Camphrier Area", category=["TRAINER"], flag_id=0x0714, requires=""),
    "Route 6 - Battled Tourist Takemi": LocationData(201046, "Cyllage Area", category=["TRAINER"], flag_id=0x0719, requires=""),
    "Route 6 - Battled Tourist Mari": LocationData(201047, "Cyllage Area", category=["TRAINER"], flag_id=0x071A, requires=""),
    "Route 6 - Battled Tourist Eriko": LocationData(201048, "Cyllage Area", category=["TRAINER"], flag_id=0x071B, requires=""),
    "Route 6 - Battled Tourist Hiroko": LocationData(201049, "Cyllage Area", category=["TRAINER"], flag_id=0x071C, requires=""),
    "Route 10 - Battled Tourist Fumiko": LocationData(201050, "Shalour Area", category=["TRAINER"], flag_id=0x071D, requires=""),
    "Route 10 - Battled Tourist Tomoko": LocationData(201051, "Shalour Area", category=["TRAINER"], flag_id=0x071E, requires=""),
    "Shalour City (Gym) - Battled Roller Skater Shun": LocationData(201052, "Shalour Area", category=["TRAINER"], flag_id=0x071F, requires=""),
    "Shalour City (Gym) - Battled Roller Skater Rolanda": LocationData(201053, "Shalour Area", category=["TRAINER"], flag_id=0x0720, requires=""),
    "Route 5 - Battled Backpacker Heike": LocationData(201054, "Camphrier Area", category=["TRAINER"], flag_id=0x0721, requires=""),
    "Route 6 - Battled Backpacker Jerome": LocationData(201055, "Cyllage Area", category=["TRAINER"], flag_id=0x0722, requires=""),
    "Route 6 - Battled Backpacker Roderick": LocationData(201056, "Cyllage Area", category=["TRAINER"], flag_id=0x0723, requires=""),
    "Route 5 - Battled Twins Faith & Joy": LocationData(201057, "Camphrier Area", category=["TRAINER"], flag_id=0x0724, requires=""),
    "Route 6 - Battled Beauty Brigitte": LocationData(201058, "Cyllage Area", category=["TRAINER"], flag_id=0x0725, requires=""),
    "Route 7 - Battled Artist Pierre": LocationData(201059, "Cyllage Area", category=["TRAINER"], flag_id=0x0726, requires=""),
    "Route 7 - Battled Artist Georgia": LocationData(201060, "Cyllage Area", category=["TRAINER"], flag_id=0x0727, requires=""),
    "Route 7 - Battled Artist Family Mona & Paolo": LocationData(201061, "Cyllage Area", category=["TRAINER"], flag_id=0x0728, requires=""),
    "Connecting Cave - Battled Pokemon Breeder Mercy": LocationData(201062, "Cyllage Area", category=["TRAINER"], flag_id=0x072B, requires=""),
    "Route 8 (Coast) - Battled Fisherman Wharton": LocationData(201063, "Cyllage Area", category=["TRAINER"], flag_id=0x072C, requires=""),
    "Route 8 (Coast) - Battled Fisherman Shad": LocationData(201064, "Cyllage Area", category=["TRAINER"], flag_id=0x072D, requires=""),
    # Azure Bay is Surf-only.
    "Azure Bay - Battled Fisherman Ewan": LocationData(201065, "Coumarine Area", category=["TRAINER"], flag_id=0x072E, requires="HM03 Surf"),
    "Route 8 (Coast) - Battled Swimmer ♀ Genevieve": LocationData(201066, "Cyllage Area", category=["TRAINER"], flag_id=0x072F, requires=""),
    "Route 8 (Coast) - Battled Swimmer ♀ Marissa": LocationData(201067, "Cyllage Area", category=["TRAINER"], flag_id=0x0730, requires=""),
    "Route 8 (Coast) - Battled Swimmer ♂ Ramses": LocationData(201068, "Cyllage Area", category=["TRAINER"], flag_id=0x0731, requires=""),
    "Route 8 (Coast) - Battled Swimmer ♂ Estaban": LocationData(201069, "Cyllage Area", category=["TRAINER"], flag_id=0x0732, requires=""),
    "Route 8 (Cliffside) - Battled Black Belt Cadoc": LocationData(201070, "Cyllage Area", category=["TRAINER"], flag_id=0x0734, requires=""),
    "Cyllage City (Gym) - Battled Hiker Bernard": LocationData(201071, "Cyllage Area", category=["TRAINER"], flag_id=0x0735, requires=""),
    "Cyllage City (Gym) - Battled Hiker Craig": LocationData(201072, "Cyllage Area", category=["TRAINER"], flag_id=0x0736, requires=""),
    "Glittering Cave - Battled Team Flare Grunt": LocationData(201073, "Cyllage Area", category=["TRAINER"], flag_id=0x073A, requires=""),
    "Route 10 - Battled Team Flare Grunt (1)": LocationData(201074, "Shalour Area", category=["TRAINER"], flag_id=0x073C, requires=""),
    "Route 10 - Battled Psychic Sayid": LocationData(201075, "Shalour Area", category=["TRAINER"], flag_id=0x073D, requires=""),
    "Route 11 - Battled Brains & Brawn Frank & Sly": LocationData(201076, "Shalour Area", category=["TRAINER"], flag_id=0x073E, requires=""),
    "Route 11 - Battled Psychic Emanuel": LocationData(201077, "Shalour Area", category=["TRAINER"], flag_id=0x073F, requires=""),
    "Route 11 - Battled Battle Girl Gerardine": LocationData(201078, "Shalour Area", category=["TRAINER"], flag_id=0x0740, requires=""),
    "Route 8 (Coast) - Battled Sky Trainer Colm": LocationData(201079, "Cyllage Area", category=["TRAINER"], flag_id=0x0741, requires=""),
    "Route 9 - Battled Sky Trainer Orion": LocationData(201080, "Shalour Area", category=["TRAINER"], flag_id=0x0742, requires=""),
    "Route 8 (Coast) - Battled Sky Trainer Aveza": LocationData(201081, "Cyllage Area", category=["TRAINER"], flag_id=0x0743, requires=""),
    "Route 11 - Battled Sky Trainer Yvette": LocationData(201082, "Shalour Area", category=["TRAINER"], flag_id=0x0744, requires=""),
    "Coumarine City (Gym) - Battled Pokémon Ranger Brooke": LocationData(201083, "Coumarine Area", category=["TRAINER"], flag_id=0x0745, requires=""),
    "Coumarine City (Gym) - Battled Pokémon Ranger Twiggy": LocationData(201084, "Coumarine Area", category=["TRAINER"], flag_id=0x0746, requires=""),
    "Coumarine City (Gym) - Battled Pokémon Ranger Chaise": LocationData(201085, "Coumarine Area", category=["TRAINER"], flag_id=0x0747, requires=""),
    "Coumarine City (Gym) - Battled Pokémon Ranger Maurice": LocationData(201086, "Coumarine Area", category=["TRAINER"], flag_id=0x0748, requires=""),
    "Route 10 - Battled Team Flare Grunt (2)": LocationData(201087, "Shalour Area", category=["TRAINER"], flag_id=0x074D, requires=""),
    "Reflection Cave (B1F) - Battled Honeymooners Yuu & Ami": LocationData(201088, "Shalour Area", category=["TRAINER"], flag_id=0x0758, requires=""),
    "Reflection Cave (B1F) - Battled Tourist Haruto": LocationData(201089, "Shalour Area", category=["TRAINER"], flag_id=0x0759, requires=""),
    "Reflection Cave (B1F) - Battled Tourist Monami": LocationData(201090, "Shalour Area", category=["TRAINER"], flag_id=0x075A, requires=""),
    "Reflection Cave (B1F) - Battled Psychic Franz": LocationData(201091, "Shalour Area", category=["TRAINER"], flag_id=0x075B, requires=""),
    "Reflection Cave (1F) - Battled Backpacker Lane": LocationData(201092, "Shalour Area", category=["TRAINER"], flag_id=0x075C, requires=""),
    "Reflection Cave (1F) - Battled Hiker Dunstan": LocationData(201093, "Shalour Area", category=["TRAINER"], flag_id=0x075D, requires=""),
    "Shalour City (Gym) - Battled Roller Skater Kate": LocationData(201094, "Shalour Area", category=["TRAINER"], flag_id=0x075E, requires=""),
    "Shalour City (Gym) - Battled Roller Skater Dash": LocationData(201095, "Shalour Area", category=["TRAINER"], flag_id=0x075F, requires=""),
    "Route 12 - Battled Backpacker Joren": LocationData(201096, "Coumarine Area", category=["TRAINER"], flag_id=0x0760, requires=""),
    "Route 12 - Battled Fisherman Murray": LocationData(201097, "Coumarine Area", category=["TRAINER"], flag_id=0x0761, requires=""),
    "Route 12 - Battled Pokémon Breeder Foster": LocationData(201098, "Coumarine Area", category=["TRAINER"], flag_id=0x0762, requires=""),
    "Route 12 - Battled Pokémon Breeder Amala": LocationData(201099, "Coumarine Area", category=["TRAINER"], flag_id=0x0763, requires=""),
    # Bulbapedia: this trainer requires Surf.
    "Route 12 - Battled Swimmer ♂ Alessandro": LocationData(201100, "Coumarine Area", category=["TRAINER"], flag_id=0x0764, requires="HM03 Surf"),
    "Reflection Cave (1F) - Battled Ace Trainer Monique": LocationData(201101, "Shalour Area", category=["TRAINER"], flag_id=0x0765, requires=""),
    "Route 14 - Fairy Tale Girl Imogen": LocationData(201102, "Laverre Area", category=["TRAINER"], flag_id=0x0768, requires=""),
    "Route 14 - Hex Maniac Anina": LocationData(201103, "Laverre Area", category=["TRAINER"], flag_id=0x0769, requires=""),
    "Route 14 - Pokémon Ranger Melina": LocationData(201104, "Laverre Area", category=["TRAINER"], flag_id=0x076A, requires=""),
    "Route 14 - Pokémon Ranger Reed": LocationData(201105, "Laverre Area", category=["TRAINER"], flag_id=0x076C, requires=""),
    "Route 14 - Pokémon Ranger Nash": LocationData(201106, "Laverre Area", category=["TRAINER"], flag_id=0x076D, requires=""),
    "Reflection Cave (1F) - Battled Battle Girl Hedvig": LocationData(201107, "Shalour Area", category=["TRAINER"], flag_id=0x076E, requires=""),
    "Reflection Cave (B1F) - Battled Black Belt Igor": LocationData(201108, "Shalour Area", category=["TRAINER"], flag_id=0x076F, requires=""),
    "Route 5 - Battled Roller Skater Winnie": LocationData(201109, "Camphrier Area", category=["TRAINER"], flag_id=0x0770, requires=""),
    "Route 5 - Battled Roller Skater Florin": LocationData(201110, "Camphrier Area", category=["TRAINER"], flag_id=0x0771, requires=""),
    "Snowbelle City (Gym) - Ace Trainer Shannon": LocationData(201111, "Snowbelle Area", category=["TRAINER"], flag_id=0x0774, requires=""),
    "Snowbelle City (Gym) - Ace Trainer Imelda": LocationData(201112, "Snowbelle Area", category=["TRAINER"], flag_id=0x0775, requires=""),
    "Anistar City (Gym) - Psychic Paschal": LocationData(201113, "Anistar Area", category=["TRAINER"], flag_id=0x0776, requires=""),
    "Anistar City (Gym) - Psychic Harry": LocationData(201114, "Anistar Area", category=["TRAINER"], flag_id=0x0777, requires=""),
    "Anistar City (Gym) - Psychic Arthur": LocationData(201115, "Anistar Area", category=["TRAINER"], flag_id=0x0778, requires=""),
    "Power Plant - Team Flare Grunt M (1)": LocationData(201116, "Lumiose Area", category=["TRAINER"], flag_id=0x077D, requires=""),
    "Power Plant - Team Flare Grunt M (2)": LocationData(201117, "Lumiose Area", category=["TRAINER"], flag_id=0x077E, requires=""),
    "Power Plant - Team Flare Grunt F (1)": LocationData(201118, "Lumiose Area", category=["TRAINER"], flag_id=0x077F, requires=""),
    "Power Plant - Team Flare Grunt F (2)": LocationData(201119, "Lumiose Area", category=["TRAINER"], flag_id=0x0780, requires=""),
    "Power Plant - Team Flare Grunt F (3)": LocationData(201120, "Lumiose Area", category=["TRAINER"], flag_id=0x0781, requires=""),
    "Power Plant - Team Flare Grunt F (4)": LocationData(201121, "Lumiose Area", category=["TRAINER"], flag_id=0x0782, requires=""),
    "Laverre City (Gym) - Furisode Girl Katherine": LocationData(201122, "Laverre Area", category=["TRAINER"], flag_id=0x07BF, requires=""),
    "Laverre City (Gym) - Furisode Girl Kali": LocationData(201123, "Laverre Area", category=["TRAINER"], flag_id=0x07C1, requires=""),
    "Laverre City (Gym) - Furisode Girl Blossom": LocationData(201124, "Laverre Area", category=["TRAINER"], flag_id=0x07C4, requires=""),
    "Laverre City (Gym) - Furisode Girl Linnea": LocationData(201125, "Laverre Area", category=["TRAINER"], flag_id=0x07C6, requires=""),
    "PokeBall Factory - Team Flare Grunt M (1)": LocationData(201126, "Laverre Area", category=["TRAINER"], flag_id=0x07FD, requires=""),
    "PokeBall Factory - Team Flare Grunt M (2)": LocationData(201127, "Laverre Area", category=["TRAINER"], flag_id=0x07FE, requires=""),
    "Lysandre Lab - Team Flare Grunt M (1)": LocationData(201128, "Anistar Area", category=["TRAINER"], flag_id=0x0801, requires=""),
    "Lysandre Lab - Team Flare Grunt M (2)": LocationData(201129, "Anistar Area", category=["TRAINER"], flag_id=0x0802, requires=""),
    "Lysandre Lab - Team Flare Grunt M (3)": LocationData(201130, "Anistar Area", category=["TRAINER"], flag_id=0x0803, requires=""),
    "PokeBall Factory - Team Flare Grunt F (1)": LocationData(201131, "Laverre Area", category=["TRAINER"], flag_id=0x0807, requires=""),
    "PokeBall Factory - Team Flare Grunt F (2)": LocationData(201132, "Laverre Area", category=["TRAINER"], flag_id=0x0808, requires=""),
    "Lysandre Lab - Team Flare Grunt F (1)": LocationData(201133, "Anistar Area", category=["TRAINER"], flag_id=0x080A, requires=""),
    "Lysandre Lab - Team Flare Grunt F (2)": LocationData(201134, "Anistar Area", category=["TRAINER"], flag_id=0x080B, requires=""),
    "Lysandre Lab - Team Flare Grunt F (3)": LocationData(201135, "Anistar Area", category=["TRAINER"], flag_id=0x080C, requires=""),
    "Frost Cavern (1F) - Ace Trainer Cordelia": LocationData(201136, "Snowbelle Area", category=["TRAINER"], flag_id=0x082D, requires=""),
    "Route 21 - Ace Trainer Mireille": LocationData(201137, "Snowbelle Area", category=["TRAINER"], flag_id=0x0830, requires=""),
    "Frost Cavern (1F) - Ace Trainer Neil": LocationData(201138, "Snowbelle Area", category=["TRAINER"], flag_id=0x0831, requires=""),
    "Route 21 - Ace Trainer Evan": LocationData(201139, "Snowbelle Area", category=["TRAINER"], flag_id=0x0834, requires=""),
    "Route 19 - Hex Maniac Josette": LocationData(201140, "Snowbelle Area", category=["TRAINER"], flag_id=0x0835, requires=""),
    "Route 15 - Hex Maniac Luna": LocationData(201141, "Laverre Area", category=["TRAINER"], flag_id=0x0836, requires=""),
    "Route 15 - Hex Maniac Carrie": LocationData(201142, "Laverre Area", category=["TRAINER"], flag_id=0x0837, requires=""),
    "Route 16 - Hex Maniac Osanna": LocationData(201143, "Laverre Area", category=["TRAINER"], flag_id=0x0838, requires=""),
    "Anistar City (Gym) - Hex Maniac Melanie": LocationData(201144, "Anistar Area", category=["TRAINER"], flag_id=0x0839, requires=""),
    "Anistar City (Gym) - Hex Maniac Arachna": LocationData(201145, "Anistar Area", category=["TRAINER"], flag_id=0x083A, requires=""),
    "Frost Cavern (2F) - Black Belt Alonzo": LocationData(201146, "Snowbelle Area", category=["TRAINER"], flag_id=0x083B, requires=""),
    "Frost Cavern (3F) - Black Belt Kenji": LocationData(201147, "Snowbelle Area", category=["TRAINER"], flag_id=0x083C, requires=""),
    "Route 18 - Black Belt Yanis": LocationData(201148, "Snowbelle Area", category=["TRAINER"], flag_id=0x083D, requires=""),
    "Terminus Cave (B2F) - Black Belt Ricardo": LocationData(201149, "Snowbelle Area", category=["TRAINER"], flag_id=0x083E, requires=""),
    "Terminus Cave (B2F) - Black Belt Gunnar": LocationData(201150, "Snowbelle Area", category=["TRAINER"], flag_id=0x083F, requires=""),
    "Frost Cavern (Outside) - Artist Salvador": LocationData(201151, "Snowbelle Area", category=["TRAINER"], flag_id=0x0840, requires=""),
    "Terminus Cave (B1F) - Worker Dimitri": LocationData(201152, "Snowbelle Area", category=["TRAINER"], flag_id=0x0844, requires=""),
    "Terminus Cave (B1F) - Worker Narek": LocationData(201153, "Snowbelle Area", category=["TRAINER"], flag_id=0x0845, requires=""),
    "Terminus Cave (B1F) - Worker Yusif": LocationData(201154, "Snowbelle Area", category=["TRAINER"], flag_id=0x0846, requires=""),
    "Frost Cavern (2F) - Brains & Brawn Eoin & Wolf": LocationData(201155, "Snowbelle Area", category=["TRAINER"], flag_id=0x0847, requires=""),
    "Route 16 - Sky Trainer Gavin": LocationData(201156, "Laverre Area", category=["TRAINER"], flag_id=0x0848, requires=""),
    "Frost Cavern (Outside) - Sky Trainer Celso": LocationData(201157, "Snowbelle Area", category=["TRAINER"], flag_id=0x0849, requires=""),
    "Route 18 - Sky Trainer Jeremy": LocationData(201158, "Snowbelle Area", category=["TRAINER"], flag_id=0x084A, requires=""),
    # Azure Bay is Surf-only.
    "Azure Bay - Battled Sky Trainer Indra": LocationData(201159, "Coumarine Area", category=["TRAINER"], flag_id=0x084B, requires="HM03 Surf"),
    "Route 16 - Sky Trainer Clara": LocationData(201160, "Laverre Area", category=["TRAINER"], flag_id=0x084C, requires=""),
    "Frost Cavern (Outside) - Sky Trainer Era": LocationData(201161, "Snowbelle Area", category=["TRAINER"], flag_id=0x084D, requires=""),
    "Route 17 - Sky Trainer Anila": LocationData(201162, "Anistar Area", category=["TRAINER"], flag_id=0x084E, requires=""),
    "Route 19 - Sky Trainer Sera": LocationData(201163, "Snowbelle Area", category=["TRAINER"], flag_id=0x084F, requires=""),
    "Lost Hotel - Punk Girl Jeanne": LocationData(201164, "Laverre Area", category=["TRAINER"], flag_id=0x0850, requires=""),
    "Lost Hotel - Punk Guy Sid": LocationData(201165, "Laverre Area", category=["TRAINER"], flag_id=0x0851, requires=""),
    "Lost Hotel - Punk Guy Jaques": LocationData(201166, "Laverre Area", category=["TRAINER"], flag_id=0x0852, requires=""),
    "Lost Hotel - Punk Guy Slater": LocationData(201167, "Laverre Area", category=["TRAINER"], flag_id=0x0853, requires=""),
    "Lost Hotel - Punk Girl Cecile": LocationData(201168, "Laverre Area", category=["TRAINER"], flag_id=0x0854, requires=""),
    "Route 18 - Youngster Jayden": LocationData(201169, "Snowbelle Area", category=["TRAINER"], flag_id=0x0855, requires=""),
    "Route 16 - Fisherman Finn": LocationData(201170, "Laverre Area", category=["TRAINER"], flag_id=0x0856, requires=""),
    "Route 16 - Fisherman Seward": LocationData(201171, "Laverre Area", category=["TRAINER"], flag_id=0x0857, requires=""),
    "Route 16 - Fisherman Wade": LocationData(201172, "Laverre Area", category=["TRAINER"], flag_id=0x0858, requires=""),
    "Frost Cavern (2F) - Battle Girl Kinsey": LocationData(201173, "Snowbelle Area", category=["TRAINER"], flag_id=0x0859, requires=""),
    "Frost Cavern (3F) - Battle Girl Gabrielle": LocationData(201174, "Snowbelle Area", category=["TRAINER"], flag_id=0x085A, requires=""),
    "Route 18 - Battle Girl Justine": LocationData(201175, "Snowbelle Area", category=["TRAINER"], flag_id=0x085B, requires=""),
    "Terminus Cave (B2F) - Battle Girl Andrea": LocationData(201176, "Snowbelle Area", category=["TRAINER"], flag_id=0x085C, requires=""),
    "Terminus Cave (B2F) - Battle Girl Hailey": LocationData(201177, "Snowbelle Area", category=["TRAINER"], flag_id=0x085D, requires=""),
    "Route 19 - Swimmer F Coral": LocationData(201178, "Snowbelle Area", category=["TRAINER"], flag_id=0x085E, requires=""),
    "Route 15 - Mysterious Sisters Rune & Rime": LocationData(201179, "Laverre Area", category=["TRAINER"], flag_id=0x085F, requires=""),
    "Route 16 - Mysterious Sisters Achlys & Eos": LocationData(201180, "Laverre Area", category=["TRAINER"], flag_id=0x0860, requires=""),
    "Route 21 - Veteran Louis": LocationData(201181, "Snowbelle Area", category=["TRAINER"], flag_id=0x0862, requires=""),
    "Route 21 - Veteran Trisha": LocationData(201182, "Snowbelle Area", category=["TRAINER"], flag_id=0x0864, requires=""),
    "Route 18 - Lass Sara": LocationData(201183, "Snowbelle Area", category=["TRAINER"], flag_id=0x0865, requires=""),
    "Route 15 - Fairy Tale Girl Mahalyn": LocationData(201184, "Laverre Area", category=["TRAINER"], flag_id=0x0866, requires=""),
    "Route 16 - Fairy Tale Girl Alice": LocationData(201185, "Laverre Area", category=["TRAINER"], flag_id=0x0867, requires=""),
    "Route 19 - Fairy Tale Girl Lovelyn": LocationData(201186, "Snowbelle Area", category=["TRAINER"], flag_id=0x0868, requires=""),
    "Frost Cavern (1F) - Hiker Alain": LocationData(201187, "Snowbelle Area", category=["TRAINER"], flag_id=0x0869, requires=""),
    "Frost Cavern (2F) - Hiker Delmon": LocationData(201188, "Snowbelle Area", category=["TRAINER"], flag_id=0x086A, requires=""),
    "Frost Cavern (3F) - Hiker Brent": LocationData(201189, "Snowbelle Area", category=["TRAINER"], flag_id=0x086B, requires=""),
    "Frost Cavern (Outside) - Hiker Ross": LocationData(201190, "Snowbelle Area", category=["TRAINER"], flag_id=0x086C, requires=""),
    "Route 18 - Hiker Orestes": LocationData(201191, "Snowbelle Area", category=["TRAINER"], flag_id=0x086F, requires=""),
    "Terminus Cave (B1F) - Hiker Aaron": LocationData(201192, "Snowbelle Area", category=["TRAINER"], flag_id=0x0870, requires=""),
    "Terminus Cave (B1F) - Hiker Bergin": LocationData(201193, "Snowbelle Area", category=["TRAINER"], flag_id=0x0871, requires=""),
    "Route 16 - Roller Skater Olle": LocationData(201194, "Laverre Area", category=["TRAINER"], flag_id=0x0872, requires=""),
    "Route 16 - Roller Skater Jet": LocationData(201195, "Laverre Area", category=["TRAINER"], flag_id=0x0873, requires=""),
    "Route 21 - Ace Duo Elina & Sean": LocationData(201196, "Snowbelle Area", category=["TRAINER"], flag_id=0x0874, requires=""),
    "Terminus Cave (B2F) - Rangers Fern & Lee": LocationData(201197, "Snowbelle Area", category=["TRAINER"], flag_id=0x0875, requires=""),
    "Route 19 - Rangers Ivy & Orrick": LocationData(201198, "Snowbelle Area", category=["TRAINER"], flag_id=0x0876, requires=""),
    "Lost Hotel - Punk Couple Zoya & Asa": LocationData(201199, "Laverre Area", category=["TRAINER"], flag_id=0x0877, requires=""),
    "Route 15 - Pokémon Ranger Pedro": LocationData(201200, "Laverre Area", category=["TRAINER"], flag_id=0x0878, requires=""),
    "Route 15 - Pokémon Ranger Dean": LocationData(201201, "Laverre Area", category=["TRAINER"], flag_id=0x0879, requires=""),
    "Route 15 - Pokémon Ranger Silas": LocationData(201202, "Laverre Area", category=["TRAINER"], flag_id=0x087A, requires=""),
    "Route 15 - Pokémon Ranger Keith": LocationData(201203, "Laverre Area", category=["TRAINER"], flag_id=0x087B, requires=""),
    "Route 19 - Pokémon Ranger Shinobu": LocationData(201204, "Snowbelle Area", category=["TRAINER"], flag_id=0x087C, requires=""),
    "Route 19 - Pokémon Ranger Clementine": LocationData(201205, "Snowbelle Area", category=["TRAINER"], flag_id=0x087D, requires=""),
    "Route 19 - Pokémon Ranger Ambre": LocationData(201206, "Snowbelle Area", category=["TRAINER"], flag_id=0x087E, requires=""),
    "Route 4 - Battled Roller Skater Roland": LocationData(201207, "Camphrier Area", category=["TRAINER"], flag_id=0x0897, requires=""),
    "Route 4 - Battled Roller Skater Calida": LocationData(201208, "Camphrier Area", category=["TRAINER"], flag_id=0x0898, requires=""),
    "Lumiose City (Gym 2F) - Schoolboy Arno": LocationData(201209, "Lumiose Area", category=["TRAINER"], flag_id=0x0899, requires=""),
    "Lumiose City (Gym 2F) - Schoolboy Sherlock": LocationData(201210, "Lumiose Area", category=["TRAINER"], flag_id=0x089A, requires=""),
    "Lumiose City (Gym 2F) - Schoolboy Finnian": LocationData(201211, "Lumiose Area", category=["TRAINER"], flag_id=0x089B, requires=""),
    "Lumiose City (Gym 3F) - Rising Star Estel": LocationData(201212, "Lumiose Area", category=["TRAINER"], flag_id=0x089C, requires=""),
    "Lumiose City (Gym 3F) - Rising Star Nelly": LocationData(201213, "Lumiose Area", category=["TRAINER"], flag_id=0x089D, requires=""),
    "Lumiose City (Gym 3F) - Rising Star Helene": LocationData(201214, "Lumiose Area", category=["TRAINER"], flag_id=0x089E, requires=""),
    "Lumiose City (Gym 5F) - Poké Fan Abigail": LocationData(201215, "Lumiose Area", category=["TRAINER"], flag_id=0x089F, requires=""),
    "Lumiose City (Gym 5F) - Poké Fan Lydie": LocationData(201216, "Lumiose Area", category=["TRAINER"], flag_id=0x08A0, requires=""),
    "Lumiose City (Gym 5F) - Poké Fan Tara": LocationData(201217, "Lumiose Area", category=["TRAINER"], flag_id=0x08A1, requires=""),
    "Route 8 (Cliffside) - Battled Rising Star Rhys": LocationData(201218, "Cyllage Area", category=["TRAINER"], flag_id=0x08AC, requires=""),
    "Route 8 (Cliffside) - Battled Rising Star Paulette": LocationData(201219, "Cyllage Area", category=["TRAINER"], flag_id=0x08AD, requires=""),
    # Azure Bay is Surf-only.
    "Azure Bay - Battled Swimmer ♂ Kieran": LocationData(201220, "Coumarine Area", category=["TRAINER"], flag_id=0x08AE, requires="HM03 Surf"),
    # Azure Bay is Surf-only.
    "Azure Bay - Battled Swimmer ♀ Romy": LocationData(201221, "Coumarine Area", category=["TRAINER"], flag_id=0x08AF, requires="HM03 Surf"),
    "Route 10 - Battled Psychic Robert": LocationData(201222, "Shalour Area", category=["TRAINER"], flag_id=0x08B0, requires=""),
    # Azure Bay is Surf-only.
    "Azure Bay - Battled Sky Trainer Elata": LocationData(201223, "Coumarine Area", category=["TRAINER"], flag_id=0x08D6, requires="HM03 Surf"),
    # Azure Bay is Surf-only.
    "Azure Bay - Battled Swimmer ♀ Isla": LocationData(201224, "Coumarine Area", category=["TRAINER"], flag_id=0x08D8, requires="HM03 Surf"),
    "Victory Road (Inside 1) - Ace Trainer Alanza": LocationData(201225, "Victory Road", category=["TRAINER"], flag_id=0x08DB, requires=""),
    "Victory Road (Inside 1) - Ace Trainer Bence": LocationData(201226, "Victory Road", category=["TRAINER"], flag_id=0x08DC, requires=""),
    "Victory Road (Inside 1) - Black Belt Markus": LocationData(201227, "Victory Road", category=["TRAINER"], flag_id=0x08DD, requires=""),
    "Victory Road (Inside 2) - Black Belt Ander": LocationData(201228, "Victory Road", category=["TRAINER"], flag_id=0x08DE, requires=""),
    "Victory Road (Inside 1) - Battle Girl Veronique": LocationData(201229, "Victory Road", category=["TRAINER"], flag_id=0x08DF, requires=""),
    "Victory Road (Inside 2) - Battle Girl Sigrid": LocationData(201230, "Victory Road", category=["TRAINER"], flag_id=0x08E0, requires=""),
    "Victory Road (Outside 2) - Backpacker Farid": LocationData(201231, "Victory Road", category=["TRAINER"], flag_id=0x08E1, requires=""),
    "Victory Road (Inside 2) - Psychic William": LocationData(201232, "Victory Road", category=["TRAINER"], flag_id=0x08E2, requires=""),
    "Victory Road (Outside 3) - Hex Maniac Raziah": LocationData(201233, "Victory Road", category=["TRAINER"], flag_id=0x08E3, requires=""),
    "Victory Road (Outside 3) - Fairy Tale Girl Corinne": LocationData(201234, "Victory Road", category=["TRAINER"], flag_id=0x08E4, requires=""),
    "Victory Road (Inside 3) - Veteran Gerard": LocationData(201235, "Victory Road", category=["TRAINER"], flag_id=0x08E5, requires=""),
    "Victory Road (Inside 4) - Veteran Timeo": LocationData(201236, "Victory Road", category=["TRAINER"], flag_id=0x08E6, requires=""),
    "Victory Road (Inside 3) - Veteran Inga": LocationData(201237, "Victory Road", category=["TRAINER"], flag_id=0x08E7, requires=""),
    "Victory Road (Inside 4) - Veteran Catrina": LocationData(201238, "Victory Road", category=["TRAINER"], flag_id=0x08E8, requires=""),
    "Victory Road (Inside 4) - Veteran Gilles": LocationData(201239, "Victory Road", category=["TRAINER"], flag_id=0x08E9, requires=""),
    "Victory Road (Inside 3) - Pokémon Ranger Ralf": LocationData(201240, "Victory Road", category=["TRAINER"], flag_id=0x08EA, requires=""),
    "Victory Road (Inside 3) - Pokémon Ranger Petra": LocationData(201241, "Victory Road", category=["TRAINER"], flag_id=0x08EB, requires=""),
    "Victory Road (Outside 4) - Ace Trainer Michele": LocationData(201242, "Victory Road", category=["TRAINER"], flag_id=0x08EC, requires=""),
    "Victory Road (Outside 4) - Hiker Corwin": LocationData(201243, "Victory Road", category=["TRAINER"], flag_id=0x08ED, requires=""),
    "Victory Road (Outside 4) - Artist Vincent": LocationData(201244, "Victory Road", category=["TRAINER"], flag_id=0x08EE, requires=""),
    "Victory Road (Inside 2) - Brains & Brawn Arman & Hugo": LocationData(201245, "Victory Road", category=["TRAINER"], flag_id=0x08EF, requires=""),
    "Route 16 - Pokémon Ranger Bjorn": LocationData(201246, "Laverre Area", category=["TRAINER"], flag_id=0x08F0, requires=""),
    "Route 16 - Pokémon Ranger Lee": LocationData(201247, "Laverre Area", category=["TRAINER"], flag_id=0x08F1, requires=""),
    "Lysandre Lab - Team Flare Grunt F (4)": LocationData(201248, "Anistar Area", category=["TRAINER"], flag_id=0x08F2, requires=""),
    "Route 20 - Twins Nana & Nina": LocationData(201249, "Snowbelle Area", category=["TRAINER"], flag_id=0x08F6, requires=""),
    "Route 20 - Poké Fan Corey": LocationData(201250, "Snowbelle Area", category=["TRAINER"], flag_id=0x08F7, requires=""),
    "Route 20 - Poké Fan Roisin": LocationData(201251, "Snowbelle Area", category=["TRAINER"], flag_id=0x08F8, requires=""),
    "Route 20 - Fairy Tale Girl Wynne": LocationData(201252, "Snowbelle Area", category=["TRAINER"], flag_id=0x08F9, requires=""),
    "Route 20 - Hex Maniac Desdemona": LocationData(201253, "Snowbelle Area", category=["TRAINER"], flag_id=0x08FA, requires=""),
    "Route 5 - Battled Rising Star Tyson": LocationData(201254, "Camphrier Area", category=["TRAINER"], flag_id=0x0927, requires=""),
}

flag_to_location: Dict[int, str] = {
    data.flag_id: name for name, data in location_table.items() if data.flag_id is not None
}
