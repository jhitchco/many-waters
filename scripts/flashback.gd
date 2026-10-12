extends Node2D
## Playable memories. While one runs, the map is shown as it was before the clearing,
## in sepia, and you walk a person from the valley's past through a few short beats.

const TS := Tiles.TS
const WALK := 36.0
const LINE_TIME := 3.6

var active := false
var fb: Dictionary = {}
var beat_i := -1
var phase := ""            # "walk" or "act" or "end"
var lines: Array = []
var line_t := 0.0
var walker := {"p": Vector2.ZERO, "vy": 0.0, "dir": 1, "anim": 0.0, "moving": false}
var dark := 0.0
var target_x := 0.0
var fade := 0.0            # 0 clear, 1 black (screen transitions)
var fade_dir := 0.0
var extras: Array = []
var input_override = null  # float, used by the autotest
var saved := {}
var t_people: Texture2D


func _ready() -> void:
	t_people = load("res://assets/people.png")


func start(id: String) -> void:
	fb = Data.memory(id)
	active = true
	G.flashback = true
	G.memories_seen[id] = true
	saved = {"tiles": G.world.t.duplicate(), "flood": G.flood}
	G.world.t = G.world.orig.duplicate()
	G.flood = false
	dark = float(fb.get("dark", 0.0))
	extras.clear()
	for e in fb.get("extras", []):
		extras.append({"row": int(e[0]), "p": Vector2(int(e[1]) * TS + 8, _ground_row(int(e[1]), int(e[2])) * TS), "ph": randf() * TAU})
	beat_i = -1
	fade = 1.0
	fade_dir = -1.0
	G.hud.flashback_begin(fb["title"], fb["when"])
	G.sfx.set_music("memory")
	G.sfx.set_ambient("night" if dark > 0.3 else "birds")
	_next_beat()


func _ground_row(tx: int, from_row: int) -> int:
	for y in range(maxi(1, from_row), G.world.H):
		if Tiles.solid_h(G.world.tile(tx, y)) and not Tiles.solid_h(G.world.tile(tx, y - 1)):
			return y
	return int(G.meta["surf"])


func _next_beat() -> void:
	beat_i += 1
	var beats: Array = fb["beats"]
	if beat_i >= beats.size():
		phase = "end"
		lines = [fb["end"]]
		line_t = LINE_TIME + 1.5
		G.hud.flashback_line(lines[0])
		G.hud.flashback_goal("")
		return
	var b: Dictionary = beats[beat_i]
	if b.has("at"):
		walker["p"] = Vector2(int(b["at"]) * TS + 8, _ground_row(int(b["at"]), int(b.get("row_from", 1))) * TS)
		walker["vy"] = 0.0
		if beat_i > 0:
			fade = 1.0
			fade_dir = -1.0
	if b.has("dark"):
		dark = float(b["dark"])
	target_x = int(b["to"]) * TS + 8
	walker["dir"] = 1 if target_x >= walker["p"].x else -1
	lines = b["say"].duplicate()
	phase = "walk"
	_show_next_line()
	G.hud.flashback_goal(b["goal"])


func _show_next_line() -> void:
	if lines.is_empty():
		G.hud.flashback_line("")
		return
	G.hud.flashback_line(lines[0])
	line_t = LINE_TIME


func near_target() -> bool:
	return phase == "walk" and absf(walker["p"].x - target_x) < 10.0


func physics(delta: float) -> void:
	if not active:
		return
	G.time += delta
	if fade_dir != 0.0:
		fade = clampf(fade + fade_dir * delta * 1.6, 0.0, 1.0)
		if fade <= 0.0 or fade >= 1.0:
			fade_dir = 0.0
	if not lines.is_empty():
		line_t -= delta
		if line_t <= 0.0 or (Input.is_action_just_pressed("take") and line_t < LINE_TIME - 0.4):
			lines.pop_front()
			_show_next_line()
	match phase:
		"walk":
			var ix: float = input_override if input_override != null else Input.get_axis("left", "right")
			_walk(ix, delta)
			G.hud.flashback_prompt(near_target())
			if near_target() and Input.is_action_just_pressed("take") or (near_target() and input_override != null):
				var b: Dictionary = fb["beats"][beat_i]
				lines = b["act"].duplicate()
				phase = "act"
				G.hud.flashback_prompt(false)
				G.hud.flashback_goal("")
				_show_next_line()
				G.sfx.play("chime", 0.05)
		"act":
			_walk(0.0, delta)
			if lines.is_empty():
				_next_beat()
		"end":
			if lines.is_empty() and fade_dir == 0.0 and fade < 1.0:
				fade_dir = 1.0
			if lines.is_empty() and fade >= 1.0:
				finish()


func _walk(ix: float, delta: float) -> void:
	var w = G.world
	var p: Vector2 = walker["p"]
	walker["moving"] = absf(ix) > 0.2
	if walker["moving"]:
		walker["dir"] = 1 if ix > 0.0 else -1
		walker["anim"] += delta * 4.0
		var nx: float = p.x + signf(ix) * WALK * delta
		var tx := floori((nx + signf(ix) * 4.0) / TS)
		var fy := floori(p.y / TS)
		# step up to two tiles, step down up to three, otherwise stop
		var moved := false
		for dy in [0, -1, -2, 1, 2, 3]:
			var gy: int = fy + dy
			if Tiles.solid_h(w.tile(tx, gy)) and not Tiles.solid_h(w.tile(tx, gy - 1)) and not Tiles.solid_h(w.tile(tx, gy - 2)):
				p = Vector2(nx, gy * TS)
				moved = true
				break
		if not moved:
			walker["moving"] = false
	walker["p"] = p


func finish() -> void:
	active = false
	G.flashback = false
	G.world.t = saved["tiles"]
	G.flood = saved["flood"]
	G.hud.flashback_end()
	phase = ""
	G.unlock("first_memory")
	if G.memories_seen.size() >= Data.memory_count():
		G.unlock("memories_all")


func _process(_d: float) -> void:
	queue_redraw()


func _draw() -> void:
	if not active:
		return
	var row: int = fb["row"]
	for e in extras:
		var bob := sin(G.time * 3.0 + e["ph"]) * 1.0
		draw_texture_rect_region(t_people, Rect2(e["p"] + Vector2(-8, -24 + bob), Vector2(16, 24)), Rect2(4 * 16, int(e["row"]) * 24, 16, 24))
	if phase == "walk":
		var m := Vector2(target_x, walker["p"].y - 30 + sin(G.time * 3.0) * 2.0)
		draw_colored_polygon(PackedVector2Array([m + Vector2(0, -4), m + Vector2(3, 0), m + Vector2(0, 4), m + Vector2(-3, 0)]), Color("ffd36b"))
		draw_circle(Vector2(target_x, walker["p"].y - 4), 8.0, Color(1.0, 0.83, 0.42, 0.12 + 0.06 * sin(G.time * 4.0)))
	var col := 4
	if walker["moving"]:
		col = int(walker["anim"] * 2.0) % 4
	draw_set_transform(walker["p"], 0.0, Vector2(walker["dir"], 1))
	draw_texture_rect_region(t_people, Rect2(Vector2(-8, -24), Vector2(16, 24)), Rect2(col * 16, row * 24, 16, 24))
	draw_set_transform(Vector2.ZERO)
	if dark > 0.3:
		var lp: Vector2 = walker["p"] + Vector2(walker["dir"] * 6, -14)
		draw_circle(lp, 1.5, Color("ffe08a"))
