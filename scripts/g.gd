extends Node
## Autoload "G": shared game state and references between the scene's parts.

const TS := 16
const HEAVY := 10            # mass at which rotten boards give way
const CRAWL_MASS := 6        # largest mass that fits a one-tile crawlway
const SAVE_PATH := "user://many_waters_save.json"
const ACH_PATH := "user://achievements.json"

var main: Node
var world: Node2D
var creature: Node2D
var actors: Node2D
var fx: Node2D
var hud: Control
var cam: Camera2D
var sfx: Node
var boss: Node2D
var boss2: Node2D

var ab := {}
var counts := {}
var taken := 0
var kept := 0
var voices: Array = []
var flood := false
var flood_speed := 6.0
var water_y := 1.0e6
var reveal_t := 0.0
var time := 0.0
var zone := -1
var zone_seen: Array = []
var running := false
var paused := false
var ended := false
var shake := 0.0
var flashback := false
var memories_seen := {}
var upgrades := {}
var letters := {}
var deaths := 0
var combo := 0
var last_take_t := -100.0
var ach := {}               # every achievement ever earned, across playthroughs
var run_ach: Array = []     # earned this playthrough

## Map geometry from data/meta.json (written by tools/build_level.py).
var meta := {}
var FLOOD_FULL_Y := 0.0
var FLOOD_START_Y := 0.0
var SURF_Y := 0.0


func _ready() -> void:
	_setup_input()
	meta = JSON.parse_string(FileAccess.get_file_as_string("res://data/meta.json"))
	FLOOD_FULL_Y = float(meta["flood_row"]) * TS
	FLOOD_START_Y = float(meta["flood_start_row"]) * TS
	SURF_Y = float(meta["surf"]) * TS
	var a = JSON.parse_string(FileAccess.get_file_as_string(ACH_PATH)) if FileAccess.file_exists(ACH_PATH) else null
	if typeof(a) == TYPE_DICTIONARY:
		ach = a


func reset() -> void:
	ab = {"axe": false, "shovel": false, "level": false, "charge": false}
	counts = {"R": 0, "B": 0, "K": 0, "E": 0, "G": 0, "P": 0}
	taken = 0
	kept = 0
	voices = []
	flood = false
	water_y = 1.0e6
	reveal_t = 0.0
	time = 0.0
	zone = -1
	zone_seen = [false, false, false, false, false]
	ended = false
	paused = false
	shake = 0.0
	flashback = false
	memories_seen = {}
	upgrades = {}
	letters = {}
	deaths = 0
	combo = 0
	last_take_t = -100.0
	run_ach = []


func add_voice(who: String, line: String, kind: String) -> void:
	voices.append({"name": who, "line": line, "kind": kind})
	if hud:
		hud.voices_changed()


## Earn an achievement. Returns true the first time it is ever earned.
func unlock(id: String) -> bool:
	if run_ach.has(id):
		return false
	run_ach.append(id)
	var first := not ach.has(id)
	ach[id] = true
	var f := FileAccess.open(ACH_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(ach))
	for a in Data.ACHIEVEMENTS:
		if a[0] == id and hud:
			hud.achievement(a[1], a[2])
	return first


func has_up(id: String) -> bool:
	return upgrades.get(id, false)


func zone_at(px: float) -> int:
	var tx := px / TS
	for i in Data.ZONES.size():
		if tx < Data.ZONES[i]["x1"]:
			return i
	return Data.ZONES.size() - 1


func _setup_input() -> void:
	var keys := {
		"left": [KEY_A, KEY_LEFT], "right": [KEY_D, KEY_RIGHT], "up": [KEY_W, KEY_UP], "down": [KEY_S, KEY_DOWN],
		"take": [KEY_SPACE, KEY_J], "read": [KEY_F, KEY_K], "charge": [KEY_E, KEY_L], "shed": [KEY_Q], "fling": [KEY_SHIFT, KEY_I],
		"chorus": [KEY_C], "map": [KEY_TAB, KEY_M], "pause": [KEY_ESCAPE, KEY_P], "mute": [KEY_N],
	}
	var pads := {
		"take": [JOY_BUTTON_A], "shed": [JOY_BUTTON_B], "read": [JOY_BUTTON_X], "charge": [JOY_BUTTON_Y],
		"map": [JOY_BUTTON_BACK], "pause": [JOY_BUTTON_START], "chorus": [JOY_BUTTON_RIGHT_SHOULDER], "fling": [JOY_BUTTON_LEFT_SHOULDER],
		"left": [JOY_BUTTON_DPAD_LEFT], "right": [JOY_BUTTON_DPAD_RIGHT], "up": [JOY_BUTTON_DPAD_UP], "down": [JOY_BUTTON_DPAD_DOWN],
	}
	var axes := {"left": [JOY_AXIS_LEFT_X, -1.0], "right": [JOY_AXIS_LEFT_X, 1.0], "up": [JOY_AXIS_LEFT_Y, -1.0], "down": [JOY_AXIS_LEFT_Y, 1.0]}
	for a in keys:
		if not InputMap.has_action(a):
			InputMap.add_action(a, 0.3)
		for k in keys[a]:
			var e := InputEventKey.new()
			e.physical_keycode = k
			InputMap.action_add_event(a, e)
	for a in pads:
		for b in pads[a]:
			var j := InputEventJoypadButton.new()
			j.button_index = b
			InputMap.action_add_event(a, j)
	var rmb := InputEventMouseButton.new()
	rmb.button_index = MOUSE_BUTTON_RIGHT
	InputMap.action_add_event("fling", rmb)
	var lmb := InputEventMouseButton.new()
	lmb.button_index = MOUSE_BUTTON_LEFT
	InputMap.action_add_event("take", lmb)
	var rt := InputEventJoypadMotion.new()
	rt.axis = JOY_AXIS_TRIGGER_RIGHT
	rt.axis_value = 1.0
	InputMap.action_add_event("fling", rt)
	for a in axes:
		var m := InputEventJoypadMotion.new()
		m.axis = axes[a][0]
		m.axis_value = axes[a][1]
		InputMap.action_add_event(a, m)
