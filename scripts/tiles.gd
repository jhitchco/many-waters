class_name Tiles
## Tile ids shared by every script. Matches the legend in tools/build_level.py.

const TS := 16
const E := 0
const ROCK := 1
const DIRT := 2
const WOOD := 3
const GRAN := 4
const FALSE := 5
const CONC := 6
const OPEN := 7
const CLIFF := 8
const BOARDS := 9

const CHARS := {".": E, "#": ROCK, "d": DIRT, "w": WOOD, "g": GRAN, "f": FALSE, "c": CONC, "X": CLIFF, "b": BOARDS}
## Row in assets/tiles.png for each solid tile.
const ATLAS_ROW := {ROCK: 0, DIRT: 1, WOOD: 2, GRAN: 3, FALSE: 4, CONC: 5, CLIFF: 6, BOARDS: 7}
const ROW_GRASS := 8
const ROW_CEIL := 9
const ROW_MISC := 10
const ROW_CAVE := 11

## Things a walker (person, animal, bullet) collides with.
static func solid_h(t: int) -> bool:
	return t != E and t != OPEN

## Surfaces the creature's tentacles can grip.
static func cling(t: int) -> bool:
	return t == ROCK or t == DIRT or t == WOOD or t == GRAN or t == FALSE or t == BOARDS
