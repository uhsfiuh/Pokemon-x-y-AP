"""
Pokémon Y Archipelago Client
Runs inside ArchipelagoBizHawkClient.exe.
Communicates with pokemon_y_connector.lua on port 43055
which handles mainmemory access for verified Pokémon Y addresses.
"""

from typing import TYPE_CHECKING, Set
import logging
logger = logging.getLogger("PokemonY")

from NetUtils import ClientStatus
import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

# Memory domain — System Bus accepts full 32-bit virtual RAM addresses in BizHawk 3DS core
MEMORY_DOMAIN    = "System Bus"

ADDR_BADGES      = 0x074D86A0
ADDR_BAG_ITEMS    = 0x074D5554
ADDR_BAG_KEY      = 0x074D5B94
ADDR_BAG_TM       = 0x074D5D14
ADDR_BAG_MEDICINE = 0x074D5EBC
ADDR_BAG_BERRIES  = 0x074D5FBC

# Verified Event Flags Base Address in mainmemory domain
EVENT_FLAGS_BASE = 0x074E86B8

def get_pocket_info(item_id: int):
    if (328 <= item_id <= 424) or (618 <= item_id <= 620) or (690 <= item_id <= 694):
        # 106, not 110: ADDR_BAG_MEDICINE - ADDR_BAG_TM = 0x1A8 = 424 bytes =
        # 106 slots. 110 slots would be 440 bytes, running 4 slots into the
        # Medicine pocket.
        return ADDR_BAG_TM, 106
    if (17 <= item_id <= 54) or item_id in [134, 504, 565, 566, 567, 568, 569, 570, 571, 591, 645, 708, 709]:
        return ADDR_BAG_MEDICINE, 60
    if (149 <= item_id <= 212) or (686 <= item_id <= 688):
        return ADDR_BAG_BERRIES, 70
    if item_id in [216, 431, 442, 445, 446, 447, 450, 465, 466, 471, 628, 629, 631, 632, 638, 641, 642, 643, 651, 689, 695, 696, 697, 698, 700, 701, 702, 703, 705, 712, 713, 714]:
        return ADDR_BAG_KEY, 60
    return ADDR_BAG_ITEMS, 100

BAG_SLOT_COUNT = 100
BAG_SLOT_SIZE  = 4

BADGE_ITEM_ID_BASE = 200801
BADGE_COUNT        = 8

# Roller Skates are NOT a bag item in X/Y. They are a capability switch,
# SYS_FLAG_ROLLERSKATES. So they cannot be delivered with a bag write, and the
# vanilla grant cannot be removed by deleting an item -- both have to go through
# this flag, handled in section 1c of game_watcher.
# ROM hashes confirmed to work with the hardcoded FCRAM addresses in this world.
#
# This exists because every address here is build-specific. A different dump, or
# a dump with a 3DS update applied, can put the save-flag block somewhere else in
# FCRAM -- and BizHawk returns 0 for an out-of-range read instead of raising, so
# the symptom is a client that connects perfectly and then registers nothing at
# all, with no error anywhere. That is very hard to diagnose from the outside.
#
# Add hashes here as they are confirmed working. Get one from the connector's
# Diagnostics button ("ROM hash"), or from BizHawk itself.
KNOWN_GOOD_ROM_HASHES = {
    "0C0C54FC3A0DA480061D661BA3A5644F": "Pokemon Y (USA) (En,Ja,Fr,De,Es,It,Ko)",
}

# How many consecutive polls of an entirely blank event-flag block before we say
# something is wrong. Blank is legitimate at the title screen and before a save is
# loaded, so this needs to be long enough that a real player is certainly in game
# by the time it fires -- roughly a minute at typical poll rates.
EMPTY_FLAG_WARN_AFTER = 600

# Manual checks: items the game sets no usable pickup flag for, claimed by a
# button in the connector's helper window.
#
# The button sets a spare event flag; the client sees it, banks the check, and
# then decides whether to remove the vanilla copy from the bag. That decision
# belongs HERE, not in the Lua, because only the client knows what Archipelago
# has actually granted -- and it knows it across sessions, since the server
# resends the full items_received list on every connect. The connector could
# only ever observe writes made while it happened to be running.
#
#   location id: (archipelago item id, in-game item id, label)
MANUAL_CHECK_ITEMS = {
    200493: (200422, 422, "HM03 Surf"),
    200494: (200423, 423, "HM04 Strength"),
    200486: (200424, 424, "HM05 Waterfall"),
    200491: (200471, 471, "Dowsing Machine"),
    200492: (200700, 700, "Elevator Key"),
    200483: (200651, 651, "Poké Flute"),
}

# Roadblocks the story removes, which we put back until Archipelago grants the
# key item. Same principle as stripping an un-granted badge: the multiworld, not
# the story, decides when you may pass.
#
# Each has an OVERRIDE flag -- a spare, game-unused flag the player can set from
# the connector to switch that blocker off. This is a safety valve, not a nicety:
# an obstacle that respawns behind you can strand you somewhere you cannot leave,
# which is a softlock, and strictly worse than the sequence break the blocker
# exists to prevent. The override lives in a real event flag so it survives
# saving, reloading and reconnecting.
#
#   event flag: (archipelago item id that unlocks it, label, override flag)
BLOCKER_FLAGS = {
    0x0277: (200651, "Snorlax on Route 7", 0x0013),   # FV_R07_EV_POKE11_01
}

# Locations whose flag goes the OTHER way -- the check fires when the flag is
# CLEARED, not set.
#
# 0x03F5 (FV_T03R0101_O_MODEL01, the Shabboneau Castle Poke Flute object) is set
# by default on a fresh save and clears when the object appears. Testing "is it
# set" therefore fired the moment any client connected. Watching for the
# set -> clear transition is the meaningful signal.
#
#   event flag: location id
CLEARED_FLAG_LOCATIONS = {
    0x03F5: 200483,   # Shabboneau Castle - Received Poké Flute
}

ROLLER_SKATES_ITEM_ID = 200643
ROLLER_SKATES_LOC_ID  = 200482
ROLLER_SKATES_FLAG    = 0x0A55

# Event flag that the game sets when each gym leader is actually defeated.
# These are the same flags used as the Badge location checks in Locations.py,
# keyed by badge number (1-8, gym progression order, matching bit 0-7 of the
# badge byte). Used to tell "you have beaten this gym" apart from "AP handed
# you this badge".
# Location ids of the eight badge checks, keyed by badge number (1-8, gym
# progression order, matching bit 0-7 of the badge byte). These are detected from
# the badge byte rather than from an event flag -- see section 1b.
BADGE_LOCATION_IDS = {
    1: 200001,  # Santalune Area - Bug Badge
    2: 200002,  # Cyllage Area   - Cliff Badge
    3: 200003,  # Shalour Area   - Rumble Badge
    4: 200004,  # Coumarine Area - Plant Badge
    5: 200005,  # Lumiose Area   - Voltage Badge
    6: 200006,  # Laverre Area   - Fairy Badge
    7: 200007,  # Anistar Area   - Psychic Badge
    8: 200008,  # Snowbelle Area - Iceberg Badge
}

# RETAINED FOR REFERENCE ONLY -- do not use these to detect a gym win.
# Play testing showed they never set: beating Viola moved the badge byte from
# 0x00 to 0x01 while 0x06D2 stayed clear. They are still the flag_ids on the
# badge locations in Locations.py, and section 1 deliberately skips category
# "Badge" so they cannot fire a spurious check.
GYM_FLAG_BY_BADGE = {
    1: 0x06D2,  # Bug     - Santalune / Viola
    2: 0x0718,  # Cliff   - Cyllage / Grant
    3: 0x06E1,  # Rumble  - Shalour / Korrina
    4: 0x06E2,  # Plant   - Coumarine / Ramos
    5: 0x06E3,  # Voltage - Lumiose / Clemont
    6: 0x06E4,  # Fairy   - Laverre / Valerie
    7: 0x06E5,  # Psychic - Anistar / Olympia
    8: 0x06E6,  # Iceberg - Snowbelle / Wulfric
}


class PokemonXYClient(BizHawkClient):
    game         = "Pokemon X and Y"
    system       = ("N3DS", "3DS", "N3DS Extra RAM", "System Bus")
    patch_suffix = (".appatch", ".apypatch", ".apxypatch", ".apworld")

    _received_index: int = 0
    _sent_locations: Set[int]
    # Badges Archipelago has granted. Drives the RAM enforcement block.
    _ap_received_badges: Set[int]
    # Badges whose bit this client has actually poked into RAM. Kept separate
    # from the above because the two answer different questions, and conflating
    # them made _give_badge unreachable.
    _written_badges: Set[int]
    # True when the last delivery attempt failed because the bag pocket was
    # full (permanent) rather than because a read/write failed (transient).
    _last_failure_was_pocket_full: bool = False
    # Consecutive polls where the whole event-flag block read as zero. Drives the
    # memory health warning in section 1a.
    _empty_flag_polls: int = 0
    # The badge byte as we last left it. Comparing against what we WROTE, rather
    # than what we last read, is what lets us tell a gym win apart from our own
    # enforcement writes.
    _prev_badge_byte = None
    # The whole event flag block as of the previous poll, so flags that CLEAR can
    # be detected. Starts None so the very first poll establishes a baseline
    # rather than reporting everything at once.
    _prev_flag_bytes = None

    def __init__(self):
        super().__init__()
        self._sent_locations = set()
        self._ap_received_badges = set()
        self._written_badges = set()

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        try:
            rom_info = await bizhawk.get_hash(ctx.bizhawk_ctx)
            logger.info(f"[PokémonXY] Received game identification from Lua connector: '{rom_info}'")
        except Exception as e:
            logger.warning(f"[PokémonXY] Error receiving game identification: {e}")
            rom_info = ""

        # --- The whole handshake -------------------------------------------
        # Our connector announces itself: it answers HASH with
        #     PKMNXY|<hash>|<rom name>
        #
        # That marker is the entire test. If it is there, the player has loaded
        # our connector, so this is our game and we claim it. If it is not, some
        # other world's connector is running and this game is not ours.
        #
        # Identifying the CONNECTOR rather than the ROM is what makes this work.
        # Several Archipelago worlds target the 3DS, and the client asks each
        # installed world in turn whether a game is theirs. Any ROM-based test
        # would be inconclusive for another world's connector and we would end up
        # claiming their game. A marker cannot be inconclusive -- and it makes the
        # worlds mutually exclusive, since their handler will not recognise our
        # string either.
        raw = (rom_info or "").strip()
        parts = raw.split("|")

        if not parts or parts[0].strip().upper() != "PKMNXY":
            logger.info("[PokémonXY] Not claiming this game: the running Lua script is not the "
                        "Pokemon X/Y connector.")
            logger.info("[PokémonXY] If you ARE playing Pokemon X or Y, you are running an old "
                        "connector -- load pokemon_xy_connector.lua from this release.")
            return False

        rom_hash = parts[1].strip().upper() if len(parts) > 1 else ""
        rom_name = parts[2].strip() if len(parts) > 2 else ""

        # --- Everything below is advisory ----------------------------------
        # We have already decided to claim the game. These checks only tell the
        # player whether their dump looks like one the addresses were built for.
        # None of them refuse the connection: a wrong-looking ROM that happens to
        # work is far better than a working ROM we locked out over a name.
        if rom_name:
            lowered = rom_name.lower().replace("é", "e")
            if "pokemon x" in lowered or "pokemon y" in lowered:
                logger.info(f"[PokémonXY] Game identified: {rom_name}")
            else:
                logger.warning(f"[PokémonXY] Loaded ROM does not look like Pokemon X or Y: '{rom_name}'")
                logger.warning("[PokémonXY] Continuing anyway, but expect nothing to work.")

        if rom_hash in KNOWN_GOOD_ROM_HASHES:
            logger.info(f"[PokémonXY] Dump recognised: {KNOWN_GOOD_ROM_HASHES[rom_hash]}")
        elif rom_hash in ("", "N/A", "NOHASH", "NONE", "NULL"):
            logger.info("[PokémonXY] BizHawk reported no ROM hash for this dump, so it cannot "
                        "be checked against the known-good list. That is normal for some "
                        "dump formats and is not a problem by itself.")
        else:
            logger.warning("[PokémonXY] ------------------------------------------------------------")
            logger.warning(f"[PokémonXY] This ROM is not on the known-good list (hash {rom_hash or 'unknown'}).")
            logger.warning("[PokémonXY] It may still work. But if checks never register while the")
            logger.warning("[PokémonXY] connection looks healthy, THIS IS ALMOST CERTAINLY WHY: the")
            logger.warning("[PokémonXY] memory addresses are specific to a particular dump and BizHawk")
            logger.warning("[PokémonXY] build, and a mismatch reads as all-zero rather than erroring.")
            logger.warning("[PokémonXY] Press Diagnostics in the connector's helper window. If")
            logger.warning("[PokémonXY] 'Event flags set' is 0 bits, that is confirmed.")
            logger.warning("[PokémonXY] ------------------------------------------------------------")

        # Route game name to match server room registration
        server_game = getattr(ctx, "server_game", None) or getattr(ctx, "game", None)
        if server_game in ["Pokemon X and Y", "Pokemon Y", "Pokemon X"]:
            ctx.game = server_game
        else:
            ctx.game = self.game

        ctx.items_handling = 0b111
        ctx.want_slot_data = True
        logger.info(f"[PokémonXY] Successfully routed '{rom_info}' to handler '{ctx.game}'!")
        return True

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        try:
            from .Locations import location_table
        except Exception:
            try:
                from worlds.pokemon_y.Locations import location_table
            except Exception:
                try:
                    from pokemon_y.Locations import location_table
                except Exception:
                    try:
                        from pokemon_xy.Locations import location_table
                    except Exception:
                        location_table = {}

        # 0. Sync received badges from AP to prevent false location checks
        if ctx.items_received:
            for item in ctx.items_received:
                item_id = item.item
                if BADGE_ITEM_ID_BASE <= item_id < BADGE_ITEM_ID_BASE + BADGE_COUNT:
                    badge_num = item_id - BADGE_ITEM_ID_BASE + 1
                    self._ap_received_badges.add(badge_num)

        # ----------------------------------------------------------------
        # 1. Check event flags → send location checks (Bulk 375-byte read = 3000 flags)
        # ----------------------------------------------------------------
        # Badge locations are excluded on purpose. Their flag_ids never set (see
        # BADGE_LOCATION_IDS), so scanning them here could only ever produce a
        # spurious check if one of those flags happens to be used for something
        # else. They are detected from the badge byte in section 1b instead.
        flag_locs = [(name, data) for name, data in location_table.items()
                     if data.flag_id is not None and data.code is not None
                     and "Badge" not in data.category]

        checked = []
        if flag_locs:
            try:
                results = await bizhawk.read(ctx.bizhawk_ctx, [(EVENT_FLAGS_BASE, 375, MEMORY_DOMAIN)])
                if results and len(results) > 0:
                    flag_bytes = results[0]
                    for name, data in flag_locs:
                        loc_id = data.code
                        byte_offset = data.flag_id // 8
                        bit = data.flag_id % 8
                        if byte_offset < len(flag_bytes):
                            is_set = (flag_bytes[byte_offset] >> bit) & 1
                            if is_set:
                                if loc_id not in self._sent_locations and loc_id not in ctx.checked_locations:
                                    self._sent_locations.add(loc_id)
                                    checked.append(loc_id)
                                    logger.info(f"[PokémonXY] Location checked via flag: {name} (0x{data.flag_id:04X})")
            except bizhawk.RequestFailedError as e:
                logger.warning(f"[PokémonXY Debug] bizhawk.read failed for event flags: {e}")
            except Exception as e:
                logger.error(f"[PokémonXY Debug] Error reading event flags: {e}")

        if checked:
            ctx.locations_checked.update(checked)
            await ctx.send_msgs([{"cmd": "LocationChecks", "locations": list(checked)}])

            await self._manual_item_followup(ctx, checked)

        # ----------------------------------------------------------------
        # 1a. Memory health check
        #
        # The hardest failure to diagnose is a memory map that does not match the
        # addresses this world uses. BizHawk returns 0 for an out-of-range read
        # rather than raising, so the client connects perfectly, reports no error
        # of any kind, and silently registers nothing forever.
        #
        # An all-zero flag block is perfectly normal at the title screen or before
        # a save is loaded, so this only complains once it has persisted long
        # enough that the player is certainly in game. Warns once, not every poll.
        # ----------------------------------------------------------------
        if 'flag_bytes' in locals():
            if any(flag_bytes):
                self._empty_flag_polls = 0
            else:
                self._empty_flag_polls += 1
                if self._empty_flag_polls == EMPTY_FLAG_WARN_AFTER:
                    logger.warning("[PokémonXY] ------------------------------------------------------------")
                    logger.warning("[PokémonXY] Every event flag has read as zero for a long time.")
                    logger.warning("[PokémonXY] If you are at the title screen or have not loaded a save,")
                    logger.warning("[PokémonXY] this is normal and you can ignore it.")
                    logger.warning("[PokémonXY] ")
                    logger.warning("[PokémonXY] If you ARE in game, this connector cannot see your game's")
                    logger.warning("[PokémonXY] memory, and no check will ever register. The addresses are")
                    logger.warning("[PokémonXY] specific to a particular ROM dump and BizHawk build.")
                    logger.warning("[PokémonXY] Press Diagnostics in the connector's helper window and share")
                    logger.warning("[PokémonXY] the output.")
                    logger.warning("[PokémonXY] ------------------------------------------------------------")

        # ----------------------------------------------------------------
        # 1d. Cleared-flag checks, and roadblock enforcement
        # ----------------------------------------------------------------
        if 'flag_bytes' in locals():
            try:
                prev_flags = self._prev_flag_bytes

                # Checks that fire when a flag CLEARS. Skipped on the very first
                # poll: with no baseline we cannot tell a real transition from
                # "this is simply how the save already was", and at the title
                # screen every flag reads clear.
                if prev_flags is not None:
                    cleared = []
                    for flag_id, loc_id in CLEARED_FLAG_LOCATIONS.items():
                        off, bit = flag_id // 8, flag_id % 8
                        if off >= len(flag_bytes) or off >= len(prev_flags):
                            continue
                        was_set = (prev_flags[off] >> bit) & 1
                        now_set = (flag_bytes[off] >> bit) & 1
                        if was_set and not now_set:
                            if (loc_id not in self._sent_locations
                                    and loc_id not in ctx.checked_locations):
                                self._sent_locations.add(loc_id)
                                cleared.append(loc_id)
                                logger.info(f"[PokémonXY] Location checked via flag clearing: "
                                            f"0x{flag_id:04X}")
                    if cleared:
                        ctx.locations_checked.update(cleared)
                        await ctx.send_msgs([{"cmd": "LocationChecks", "locations": cleared}])
                        await self._manual_item_followup(ctx, cleared)

                self._prev_flag_bytes = flag_bytes

                # Roadblocks, enforced in BOTH directions.
                #
                # Flag set == obstacle gone. So the flag should simply track
                # whether Archipelago has granted the key item: put the obstacle
                # back while it has not, and clear it the moment it has. Only
                # doing the first half left the path shut even after the item
                # arrived, since nothing ever removed the obstacle again.
                #
                # Note this changes when the map is next loaded, not instantly:
                # the game spawns these objects from the flag on map load, so a
                # Snorlax already despawned by a battle stays gone until you
                # leave the area and come back.
                for flag_id, (ap_item_id, label, override_flag) in BLOCKER_FLAGS.items():
                    off, bit = flag_id // 8, flag_id % 8
                    if off >= len(flag_bytes):
                        continue

                    # Player has switched this blocker off from the connector.
                    # Leave the flag entirely alone -- including not re-opening
                    # it later, since they are managing it by hand now.
                    ov_off, ov_bit = override_flag // 8, override_flag % 8
                    if ov_off < len(flag_bytes) and (flag_bytes[ov_off] >> ov_bit) & 1:
                        continue

                    have_key = any(i.item == ap_item_id for i in ctx.items_received)
                    is_cleared = bool((flag_bytes[off] >> bit) & 1)
                    if is_cleared == have_key:
                        continue

                    res = await bizhawk.read(
                        ctx.bizhawk_ctx, [(EVENT_FLAGS_BASE + off, 1, MEMORY_DOMAIN)])
                    if res and len(res) > 0 and len(res[0]) > 0:
                        cur = res[0][0]
                        new = (cur | (1 << bit)) if have_key else (cur & ~(1 << bit) & 0xFF)
                        await bizhawk.write(
                            ctx.bizhawk_ctx,
                            [(EVENT_FLAGS_BASE + off, bytes([new]), MEMORY_DOMAIN)])
                        if have_key:
                            logger.info(f"[PokémonXY] {label} removed -- Archipelago granted the "
                                        f"item that clears it. Re-enter the area to see it.")
                        else:
                            logger.info(f"[PokémonXY] {label} restored -- Archipelago has not "
                                        f"granted the item that clears it yet.")
            except Exception:
                pass

        # ----------------------------------------------------------------
        # 1b. Enforce RAM Badge State
        #
        # Two jobs, deliberately asymmetric:
        #
        #   Strip   - a badge bit AP has not granted gets cleared. This stops a
        #             vanilla gym win from handing out a badge the multiworld
        #             has not given you yet.
        #
        #   Restore - a badge AP HAS granted is only forced back on once that
        #             gym's event flag is set. Until then, if the bit is off,
        #             it is left off.
        #
        # That second rule is what makes gym refights possible. Receiving a
        # badge from another world before beating its gym makes the leader give
        # post-victory dialogue instead of battling, which strands that gym's
        # location check. The badge helper in the Lua connector clears the bit
        # so the leader fights again -- but if this loop forced the bit straight
        # back, as it used to, the suppression would not survive one tick.
        #
        # Winning the refight sets the gym flag, so the bit comes back here
        # automatically on the next tick and the location check fires normally.
        #
        # This does NOT delay badge benefits: a badge arriving from AP is written
        # by _give_badge in step 2 below, and this loop then keeps it. Gating the
        # bit on beating the gym would deadlock, because Rules.py uses badge
        # count to gate HM field moves and region access.
        #
        # That dependency is load-bearing. _give_badge was previously unreachable
        # (the delivery loop tested the wrong set), which the old unconditional
        # `write(expected_badge_byte)` masked. With this asymmetric version the
        # mask is gone, so if _give_badge ever stops running, AP-granted badges
        # will silently never appear in RAM.
        # ----------------------------------------------------------------
        try:
            expected_badge_byte = 0
            for b in self._ap_received_badges:
                expected_badge_byte |= (1 << (b - 1))

            badge_data = await bizhawk.read(ctx.bizhawk_ctx, [(ADDR_BADGES, 1, MEMORY_DOMAIN)])
            if badge_data and len(badge_data) > 0 and len(badge_data[0]) > 0:
                current_badge_byte = badge_data[0][0]

                # --- Detect a gym win from the badge byte, not an event flag ---
                #
                # The eight GYM_FLAG_BY_BADGE ids do NOT fire. Confirmed in play
                # testing: beating Viola moved this byte 0x00 -> 0x01 while flag
                # 0x06D2 stayed clear. So the badge bit itself is the only
                # reliable signal that a leader was defeated, and it is what both
                # the badge checks and the refight restore key off now.
                #
                # A bit going 0 -> 1 that we did not write ourselves means the
                # game just awarded it, i.e. the player beat that gym. Comparing
                # against the value we last wrote (rather than last read) is what
                # makes that distinguishable.
                prev = self._prev_badge_byte
                if prev is None:
                    # First look at this byte since the client started.
                    #
                    # Any bit that is SET but NOT granted by Archipelago is
                    # evidence of a gym beaten while nothing was watching --
                    # before connecting, across a reconnect, or with the client
                    # closed. Baselining on those bits as "already known" would
                    # throw that away, and the strip below then erases the only
                    # evidence there was: the badge byte is transient, cleared
                    # within a quarter of a second, so a restarted client would
                    # have nothing left to detect and the check would be lost
                    # permanently.
                    #
                    # Baselining on only the GRANTED bits makes those un-granted
                    # bits look like fresh wins, so their checks get banked first.
                    prev = current_badge_byte & expected_badge_byte

                game_set_bits = current_badge_byte & ~prev & 0xFF
                badge_checks = []
                for badge_num, loc_id in BADGE_LOCATION_IDS.items():
                    if game_set_bits & (1 << (badge_num - 1)):
                        if loc_id not in self._sent_locations and loc_id not in ctx.checked_locations:
                            self._sent_locations.add(loc_id)
                            badge_checks.append(loc_id)
                            logger.info(f"[PokémonXY] Gym cleared: badge {badge_num} awarded by the "
                                        f"game, sending its location check.")

                if badge_checks:
                    ctx.locations_checked.update(badge_checks)
                    await ctx.send_msgs([{"cmd": "LocationChecks", "locations": badge_checks}])

                # --- Which gyms are beaten -------------------------------------
                # A banked badge check IS the record that the gym was beaten, and
                # it survives client restarts because the server remembers it.
                gyms_beaten_byte = 0
                for badge_num, loc_id in BADGE_LOCATION_IDS.items():
                    if loc_id in ctx.checked_locations or loc_id in self._sent_locations:
                        gyms_beaten_byte |= (1 << (badge_num - 1))

                # Keep only granted badges, then force back any whose gym is
                # already cleared.
                target_badge_byte = (current_badge_byte & expected_badge_byte) \
                                    | (expected_badge_byte & gyms_beaten_byte)

                if current_badge_byte != target_badge_byte:
                    await bizhawk.write(ctx.bizhawk_ctx,
                                        [(ADDR_BADGES, bytes([target_badge_byte]), MEMORY_DOMAIN)])
                    logger.info(f"[PokémonXY] Synced RAM badges "
                                f"(0x{current_badge_byte:02X} -> 0x{target_badge_byte:02X}).")

                # Remember what the byte is AFTER our own write, so next tick only
                # sees changes the game made.
                self._prev_badge_byte = target_badge_byte
        except Exception:
            pass

        # ----------------------------------------------------------------
        # 1c. Enforce the Roller Skates capability flag
        #
        # Roller Skates are a capability switch rather than a bag item, so the
        # vanilla grant cannot be stripped by deleting something from the bag --
        # the bit itself has to be cleared, exactly like a badge.
        #
        # Ordering matters: the location scan in section 1 runs before this and
        # sends the check from the same flag read, so the check is banked before
        # the bit is taken away. As a belt-and-braces guard we additionally
        # refuse to clear the bit until the location is known to be checked, so
        # that a failed location_table import can never silently eat the check.
        # ----------------------------------------------------------------
        try:
            want_skates = any(i.item == ROLLER_SKATES_ITEM_ID for i in ctx.items_received)
            skates_banked = (ROLLER_SKATES_LOC_ID in self._sent_locations
                             or ROLLER_SKATES_LOC_ID in ctx.checked_locations)

            if want_skates or skates_banked:
                byte_off = ROLLER_SKATES_FLAG // 8
                bit      = ROLLER_SKATES_FLAG % 8
                res = await bizhawk.read(
                    ctx.bizhawk_ctx, [(EVENT_FLAGS_BASE + byte_off, 1, MEMORY_DOMAIN)])
                if res and len(res) > 0 and len(res[0]) > 0:
                    cur = res[0][0]
                    has = bool((cur >> bit) & 1)
                    if has != want_skates:
                        new = (cur | (1 << bit)) if want_skates else (cur & ~(1 << bit) & 0xFF)
                        await bizhawk.write(
                            ctx.bizhawk_ctx,
                            [(EVENT_FLAGS_BASE + byte_off, bytes([new]), MEMORY_DOMAIN)])
                        logger.info("[PokémonXY] Roller Skates %s."
                                    % ("granted from Archipelago" if want_skates
                                       else "removed (vanilla grant stripped)"))
        except Exception:
            pass

        # ----------------------------------------------------------------
        # 2. Receive items → write to RAM (Batch processing up to 10 items/frame)
        # ----------------------------------------------------------------
        batch_limit = 10
        processed = 0

        while ctx.items_received and self._received_index < len(ctx.items_received) and processed < batch_limit:
            item    = ctx.items_received[self._received_index]
            item_id = item.item

            success = False
            # Reset each iteration so a stale flag from an earlier item cannot
            # cause the next one to be wrongly skipped.
            self._last_failure_was_pocket_full = False
            if BADGE_ITEM_ID_BASE <= item_id < BADGE_ITEM_ID_BASE + BADGE_COUNT:
                badge_num = item_id - BADGE_ITEM_ID_BASE + 1
                # Test _written_badges, NOT _ap_received_badges. Step 0 above
                # already put every granted badge into _ap_received_badges on
                # this same tick, so testing that set here always matched and
                # _give_badge was dead code -- the badge bit was never written.
                if badge_num in self._written_badges:
                    self._received_index += 1
                    processed += 1
                    continue
                success = await self._give_badge(ctx, badge_num)
                if success:
                    self._written_badges.add(badge_num)
            elif item_id == ROLLER_SKATES_ITEM_ID:
                # Capability flag, not a bag item -- writing it into the bag
                # would create a phantom entry the game never reads. Section 1c
                # above owns setting the bit; just acknowledge it here.
                success = True
            else:
                success = await self._give_bag_item(ctx, item_id)

            if success:
                self._received_index += 1
                processed += 1
            elif self._last_failure_was_pocket_full:
                # A full pocket is permanent, not transient. Breaking here left
                # _received_index parked on the same item forever, so every
                # later item -- including progression -- was never delivered.
                # Skip it instead and keep the queue moving.
                logger.error(f"[PokémonXY] Skipping item {item_id}: no room in its bag pocket. "
                             f"This item is LOST -- use the manual send to recover it.")
                self._received_index += 1
                processed += 1
            else:
                # Transient failure (a failed read/write). Retry next tick.
                break

        # ----------------------------------------------------------------
        # 3. Goal check — Entered Hall of Fame / Champion Victory (Flag 0x0A50)
        # ----------------------------------------------------------------
        try:
            flag_goal = 0x0A50
            byte_offset = flag_goal // 8
            bit = flag_goal % 8
            goal_set = False
            if 'flag_bytes' in locals() and byte_offset < len(flag_bytes):
                goal_set = bool((flag_bytes[byte_offset] >> bit) & 1)
            else:
                res = await bizhawk.read(ctx.bizhawk_ctx, [(EVENT_FLAGS_BASE + byte_offset, 1, MEMORY_DOMAIN)])
                if res and len(res) > 0 and len(res[0]) > 0:
                    goal_set = bool((res[0][0] >> bit) & 1)

            if goal_set and not getattr(ctx, "finished_game", False):
                await ctx.send_msgs([{"cmd": "StatusUpdate",
                                      "status": ClientStatus.CLIENT_GOAL}])
                ctx.finished_game = True
                logger.info("[PokémonXY] Goal complete! Entered Hall of Fame / Champion Defeated (Flag 0x0A50).")
        except Exception:
            pass

    async def _give_badge(self, ctx: "BizHawkClientContext", badge_num: int) -> bool:
        try:
            data    = await bizhawk.read(ctx.bizhawk_ctx, [(ADDR_BADGES, 1, MEMORY_DOMAIN)])
            current = data[0][0]
            new_val = current | (1 << (badge_num - 1))
            await bizhawk.write(ctx.bizhawk_ctx,
                                [(ADDR_BADGES, bytes([new_val]), MEMORY_DOMAIN)])

            # Record our own write. Section 1b decides "the player beat this gym"
            # from a 0 -> 1 transition it did not make, and it captures its
            # baseline earlier in the same tick than this runs. Without this line
            # the next poll sees Archipelago's own badge grant as a gym win and
            # fires that gym's location check for free.
            self._prev_badge_byte = new_val

            logger.info(f"[PokémonXY] Badge {badge_num} granted from AP!")
            return True
        except bizhawk.RequestFailedError:
            return False

    async def _manual_item_followup(self, ctx: "BizHawkClientContext", loc_ids) -> None:
        """Take the vanilla copy of a just-checked manual item out of the bag.

        Deciding this here rather than in the connector is deliberate: only the
        client knows what Archipelago has granted, and it knows it across
        sessions because the server resends the full list on every connect.
        """
        for loc_id in loc_ids:
            entry = MANUAL_CHECK_ITEMS.get(loc_id)
            if not entry:
                continue
            ap_item_id, game_item_id, label = entry
            if any(i.item == ap_item_id for i in ctx.items_received):
                logger.info(f"[PokémonXY] {label}: Archipelago already granted this one, "
                            f"so your copy stays.")
            elif await self._remove_bag_item(ctx, game_item_id):
                logger.info(f"[PokémonXY] {label}: vanilla copy removed from your bag.")
            else:
                logger.info(f"[PokémonXY] {label}: not found in your bag, nothing removed.")

    async def _remove_bag_item(self, ctx: "BizHawkClientContext", game_item_id: int) -> bool:
        """Take one copy of an in-game item out of the bag. Returns True if found."""
        pocket_addr, max_slots = get_pocket_info(game_item_id)
        try:
            res = await bizhawk.read(
                ctx.bizhawk_ctx, [(pocket_addr, max_slots * 4, MEMORY_DOMAIN)])
            data = res[0]
            for i in range(max_slots):
                o = i * 4
                if o + 4 > len(data):
                    break
                if (data[o] | (data[o + 1] << 8)) != game_item_id:
                    continue
                qty = data[o + 2] | (data[o + 3] << 8)
                if qty <= 1:
                    # Last one: clear the whole slot so the game does not show an
                    # item with a quantity of zero.
                    payload = bytes([0, 0, 0, 0])
                else:
                    left = qty - 1
                    payload = bytes([game_item_id & 0xFF, (game_item_id >> 8) & 0xFF,
                                     left & 0xFF, (left >> 8) & 0xFF])
                await bizhawk.write(
                    ctx.bizhawk_ctx, [(pocket_addr + o, payload, MEMORY_DOMAIN)])
                return True
            return False
        except Exception as e:
            logger.warning(f"[PokémonXY] Could not remove item {game_item_id} from the bag: {e}")
            return False

    async def _give_bag_item(self, ctx: "BizHawkClientContext", item_id: int) -> bool:
        game_item_id = item_id - 200000 if item_id >= 200000 else item_id

        if game_item_id > 65535 or game_item_id <= 0:
            logger.warning(f"[PokémonXY] Invalid item_id for bag: {item_id} -> {game_item_id}")
            return True

        pocket_addr, max_slots = get_pocket_info(game_item_id)
        slot_bytes_count = max_slots * 4

        try:
            res = await bizhawk.read(ctx.bizhawk_ctx, [(pocket_addr, slot_bytes_count, MEMORY_DOMAIN)])
            data = res[0]

            target_empty_offset = None

            for i in range(max_slots):
                offset = i * 4
                if offset + 4 > len(data):
                    break

                slot_item_id = data[offset] | (data[offset + 1] << 8)
                slot_qty = data[offset + 2] | (data[offset + 3] << 8)

                if slot_item_id == game_item_id:
                    new_qty = min(slot_qty + 1, 999)
                    qty_bytes = bytes([new_qty & 0xFF, (new_qty >> 8) & 0xFF])
                    await bizhawk.write(ctx.bizhawk_ctx, [(pocket_addr + offset + 2, qty_bytes, MEMORY_DOMAIN)])
                    logger.info(f"[PokémonXY] Stacked item 0x{game_item_id:04X} in bag (Qty: {slot_qty} -> {new_qty})")
                    return True

                if slot_item_id == 0 and target_empty_offset is None:
                    target_empty_offset = offset

            if target_empty_offset is not None:
                item_data_bytes = bytes([
                    game_item_id & 0xFF,
                    (game_item_id >> 8) & 0xFF,
                    1,
                    0
                ])
                await bizhawk.write(ctx.bizhawk_ctx, [(pocket_addr + target_empty_offset, item_data_bytes, MEMORY_DOMAIN)])
                logger.info(f"[PokémonXY] Added item 0x{game_item_id:04X} to empty bag slot at offset 0x{target_empty_offset:02X}")
                return True

            logger.warning(f"[PokémonXY] Bag pocket full for item 0x{game_item_id:04X}")
            self._last_failure_was_pocket_full = True
            return False

        except bizhawk.RequestFailedError:
            return False
        except Exception as e:
            logger.warning(f"[PokémonXY] Error giving bag item 0x{game_item_id:04X}: {e}")
            return False


class PokemonYClient(PokemonXYClient):
    game = "Pokemon Y"
    system = ("N3DS", "3DS", "N3DS Extra RAM", "System Bus")
    game_watcher = PokemonXYClient.game_watcher


class PokemonXClient(PokemonXYClient):
    game = "Pokemon X"
    system = ("N3DS", "3DS", "N3DS Extra RAM", "System Bus")
    game_watcher = PokemonXYClient.game_watcher
