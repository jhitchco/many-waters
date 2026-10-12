extends Node
## Autoload "G": shared game state and references between the scene's parts.

const TS := 16
const HEAVY := 10            # mass at which rotten boards give way
const CRAWL_MASS := 6        # largest mass that fits a one-tile crawlway
const FLOOD_FULL_Y := 36.6 * 16.0
const SAVE_PATH := "user://many_waters_save.json"

var main: Node
var world: Node2D
var creature: Node2D
var actors: Node2D
var fx: Node2D
var hud: Control
var cam: Camera2D
var sfx: Node

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


func _ready() -> void:
	_setup_input()


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


func add_voice(who: String, line: String, kind: String) -> void:
	voices.append({"name": who, "line": line, "kind": kind})
	if hud:
		hud.voices_changed()


func zone_at(px: float) -> int:
	var tx := px / TS
	for i in Data.ZONES.size():
		if tx < Data.ZONES[i]["x1"]:
			return i
	return Data.ZONES.size() - 1


func _setup_input() -> void:
	var keys := {
		"left": [KEY_A, KEY_LEFT], "right": [KEY_D, KEY_RIGHT], "up": [KEY_W, KEY_UP], "down": [KEY_S, KEY_DOWN],
		"take": [KEY_SPACE, KEY_J], "read": [KEY_F, KEY_K], "charge": [KEY_E, KEY_L], "shed": [KEY_Q],
		"chorus": [KEY_C], "map": [KEY_TAB, KEY_M], "pause": [KEY_ESCAPE, KEY_P], "mute": [KEY_N],
	}
	var pads := {
		"take": [JOY_BUTTON_A], "shed": [JOY_BUTTON_B], "read": [JOY_BUTTON_X], "charge": [JOY_BUTTON_Y],
		"map": [JOY_BUTTON_BACK], "pause": [JOY_BUTTON_START], "chorus": [JOY_BUTTON_RIGHT_SHOULDER],
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
	for a in axes:
		var m := InputEventJoypadMotion.new()
		m.axis = axes[a][0]
		m.axis_value = axes[a][1]
		InputMap.action_add_event(a, m)
