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
        return ADDR_BAG_TM, 110
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


class PokemonXYClient(BizHawkClient):
    game         = "Pokemon X and Y"
    system       = ("N3DS", "3DS", "N3DS Extra RAM", "System Bus")
    patch_suffix = (".appatch", ".apypatch", ".apxypatch", ".apworld")

    _received_index: int = 0
    _sent_locations: Set[int]
    _ap_received_badges: Set[int]

    def __init__(self):
        super().__init__()
        self._sent_locations = set()
        self._ap_received_badges = set()

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
        # 1b. Enforce RAM Badge State (Strips vanilla-awarded badges if AP has not granted them yet)
        # ----------------------------------------------------------------
        try:
            expected_badge_byte = 0
            for b in self._ap_received_badges:
                expected_badge_byte |= (1 << (b - 1))

            badge_data = await bizhawk.read(ctx.bizhawk_ctx, [(ADDR_BADGES, 1, MEMORY_DOMAIN)])
            if badge_data and len(badge_data) > 0 and len(badge_data[0]) > 0:
                current_badge_byte = badge_data[0][0]
                if current_badge_byte != expected_badge_byte:
                    await bizhawk.write(ctx.bizhawk_ctx, [(ADDR_BADGES, bytes([expected_badge_byte]), MEMORY_DOMAIN)])
                    logger.info(f"[PokémonXY] Synced RAM badges (0x{current_badge_byte:02X} -> 0x{expected_badge_byte:02X}) to match AP inventory.")
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
            if BADGE_ITEM_ID_BASE <= item_id < BADGE_ITEM_ID_BASE + BADGE_COUNT:
                badge_num = item_id - BADGE_ITEM_ID_BASE + 1
                if badge_num in self._ap_received_badges:
                    self._received_index += 1
                    processed += 1
                    continue
                self._ap_received_badges.add(badge_num)
                success = await self._give_badge(ctx, badge_num)
            else:
                success = await self._give_bag_item(ctx, item_id)

            if success:
                self._received_index += 1
                processed += 1
            else:
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
