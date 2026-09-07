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
ROLLER_SKATES_ITEM_ID = 200643
ROLLER_SKATES_LOC_ID  = 200482
ROLLER_SKATES_FLAG    = 0x0A55

# Event flag that the game sets when each gym leader is actually defeated.
# These are the same flags used as the Badge location checks in Locations.py,
# keyed by badge number (1-8, gym progression order, matching bit 0-7 of the
# badge byte). Used to tell "you have beaten this gym" apart from "AP handed
# you this badge".
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
        flag_locs = [(name, data) for name, data in location_table.items()
                     if data.flag_id is not None and data.code is not None]

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

            # Which gyms have actually been beaten, reusing the flag block read
            # above. If that read failed, assume none and change nothing.
            gyms_beaten_byte = 0
            if 'flag_bytes' in locals():
                for badge_num, gym_flag in GYM_FLAG_BY_BADGE.items():
                    byte_offset = gym_flag // 8
                    bit = gym_flag % 8
                    if byte_offset < len(flag_bytes) and (flag_bytes[byte_offset] >> bit) & 1:
                        gyms_beaten_byte |= (1 << (badge_num - 1))

            badge_data = await bizhawk.read(ctx.bizhawk_ctx, [(ADDR_BADGES, 1, MEMORY_DOMAIN)])
            if badge_data and len(badge_data) > 0 and len(badge_data[0]) > 0:
                current_badge_byte = badge_data[0][0]

                # Keep only granted badges, then force back any whose gym is
                # already cleared.
                target_badge_byte = (current_badge_byte & expected_badge_byte) \
                                    | (expected_badge_byte & gyms_beaten_byte)

                if current_badge_byte != target_badge_byte:
                    await bizhawk.write(ctx.bizhawk_ctx,
                                        [(ADDR_BADGES, bytes([target_badge_byte]), MEMORY_DOMAIN)])
                    logger.info(f"[PokémonXY] Synced RAM badges "
                                f"(0x{current_badge_byte:02X} -> 0x{target_badge_byte:02X}).")
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
            logger.info(f"[PokémonXY] Badge {badge_num} granted from AP!")
            return True
        except bizhawk.RequestFailedError:
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
