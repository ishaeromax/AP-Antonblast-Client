from BaseClasses import MultiWorld, Region
from .Locations import (AntonLocation, location_table, ALL_STAGE_REGIONS, ALL_BOSS_REGIONS, ALL_EX_REGIONS, ALL_LIME_REGIONS, OPTION_KEY_TO_STAGE, STAGE_TO_KEY_ITEM, TIME_TRIAL_LOCS, CRACKED_LOCS, DETONATOR_LOCS, PAUL_LOCS, RED_ROOM_LOCS)

def _make_region(name: str, player: int, multiworld: MultiWorld) -> Region:
    region = Region(name, player, multiworld)
    multiworld.regions.append(region)
    return region

# Adds every active location that belongs to the given region.
def _populate_region(region: Region, player: int, active_loc_names: set, filter_region: str) -> None:
    locs = {
        name: data.code
        for name, data in location_table.items()
        if data.region == filter_region and name in active_loc_names
    }
    region.add_locations(locs, AntonLocation)

# Builds all regions and connects them to the hub based on the options.
def create_regions(multiworld: MultiWorld, player: int, options) -> None:
    stage_unlock = bool(options.stage_unlock_mode)
    dual_char = bool(options.dual_character)
    include_ex = bool(options.include_ex_bosses)
    include_lime = bool(options.include_lime_trials)
    include_shop = bool(options.include_shop_items)
    include_time_trials = bool(options.include_time_trials)
    include_cracked = bool(options.include_cracked)
    include_detonators = bool(options.include_detonators)
    include_pauls = bool(options.include_pauls)
    include_red_rooms = bool(options.include_red_rooms)

    starting_stage = OPTION_KEY_TO_STAGE.get(options.starting_stage.current_key, 'Boiler City')
    active = _build_active_set(dual_char, include_ex, include_lime, include_shop, include_time_trials, include_cracked, include_detonators, include_pauls, include_red_rooms)

    menu = _make_region('Menu', player, multiworld)

    all_regions = ALL_STAGE_REGIONS + ALL_BOSS_REGIONS + ALL_EX_REGIONS + ALL_LIME_REGIONS + ['Shop']

    region_map: dict[str, Region] = {}
    for rname in all_regions:
        reg = _make_region(rname, player, multiworld)
        _populate_region(reg, player, active, rname)
        region_map[rname] = reg

        if dual_char:
            annie_rname = f'Annie - {rname}'
            annie_reg = _make_region(annie_rname, player, multiworld)
            _populate_region(annie_reg, player, active, annie_rname)
            region_map[annie_rname] = annie_reg

    _connect_regions(menu, region_map, stage_unlock, dual_char, starting_stage, player, include_ex, include_lime, include_shop, all_regions)


# Decides which location names are in play for this seed.
def _build_active_set(dual_char: bool, include_ex: bool, include_lime: bool, include_shop: bool, include_time_trials: bool, include_cracked: bool, include_detonators: bool, include_pauls: bool, include_red_rooms: bool) -> set:
    par_codes = set(TIME_TRIAL_LOCS.values())
    par_codes |= {c + 5000 for c in TIME_TRIAL_LOCS.values()}
    cracked_codes = set(CRACKED_LOCS.values())
    cracked_codes |= {c + 5000 for c in CRACKED_LOCS.values()}
    detonator_codes = {c for codes in DETONATOR_LOCS.values() for c in codes}
    detonator_codes |= {c + 5000 for codes in DETONATOR_LOCS.values() for c in codes}
    paul_codes = set(PAUL_LOCS.values())
    paul_codes |= {c + 5000 for c in PAUL_LOCS.values()}
    red_room_codes = set(RED_ROOM_LOCS.values())
    red_room_codes |= {c + 5000 for c in RED_ROOM_LOCS.values()}

    active = set()
    for name, data in location_table.items():
        is_annie = name.startswith('Annie - ')
        if is_annie and not dual_char:
            continue

        if not include_ex and data.region in ALL_EX_REGIONS:
            continue

        if not include_ex and is_annie and any(data.region == f'Annie - {r}' for r in ALL_EX_REGIONS):
            continue

        if not include_lime and data.region in ALL_LIME_REGIONS:
            continue

        if not include_lime and is_annie and any(data.region == f'Annie - {r}' for r in ALL_LIME_REGIONS):
            continue

        if not include_shop and data.region == 'Shop':
            continue

        if not include_time_trials and data.code in par_codes:
            continue

        if not include_cracked and data.code in cracked_codes:
            continue

        if not include_detonators and data.code in detonator_codes:
            continue

        if not include_pauls and data.code in paul_codes:
            continue

        if not include_red_rooms and data.code in red_room_codes:
            continue

        active.add(name)

    return active


# Wires every region to the hub, gated by its key item when stage unlock is on.
def _connect_regions(menu: Region, region_map: dict, stage_unlock: bool, dual_char: bool, starting_stage: str, player: int, include_ex: bool, include_lime: bool, include_shop: bool, all_regions: list) -> None:
    for rname in all_regions:
        if rname == 'Shop' and not include_shop:
            continue

        if rname in ALL_EX_REGIONS and not include_ex:
            continue

        if rname in ALL_LIME_REGIONS and not include_lime:
            continue

        if rname not in region_map:
            continue

        key_item = STAGE_TO_KEY_ITEM.get(rname)
        needs_key = stage_unlock and bool(key_item) and rname != starting_stage

        _connect_one(menu, region_map[rname], rname, needs_key, key_item, player)

        if dual_char:
            annie_rname = f'Annie - {rname}'

            if annie_rname in region_map:
                _connect_one(menu, region_map[annie_rname], annie_rname, needs_key, key_item, player)

def _connect_one(menu: Region, target: Region, label: str, needs_key: bool, key_item, player: int) -> None:
    entrance = menu.create_exit(f'Enter {label}')
    entrance.connect(target)

    if needs_key and key_item:
        entrance.access_rule = lambda state, k=key_item: state.has(k, player)
