extends Node
## Builds the scene, runs the rules (taking, graves, abilities, checkpoints, the flood,
## the ending), saves at cellar holes, and hosts the --autotest and --shots modes.

const TS := Tiles.TS
const UNLOCK := {"R": "axe", "B": "shovel", "K": "level", "E": "charge"}
const FLOOD_START_Y := 74.6 * 16.0

var svc: SubViewportContainer
var svp: SubViewport
var world: Node2D
var actors: Node2D
var creature: Node2D
var fx: Node2D
var water: Node2D
var front: Node2D
var bg: Node2D
var cam: Camera2D
var hud: Control
var sfx: Node

var cp_pos := Vector2.ZERO
var cp_mass := 5
var cp_index := -1
var explored := PackedByteArray()
var map_img: Image
var map_tex: ImageTexture
var explore_t := 0.0
var hud_t := 0.0
var flood_toast := false


func _ready() -> void:
	G.main = self
	svc = SubViewportContainer.new()
	svc.stretch = true
	svc.stretch_shrink = 3
	svc.set_anchors_preset(Control.PRESET_FULL_RECT)
	svc.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(svc)
	svp = SubViewport.new()
	svp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	svp.snap_2d_transforms_to_pixel = true
	svc.add_child(svp)
	var bg_layer := CanvasLayer.new()
	bg_layer.layer = -10
	svp.add_child(bg_layer)
	bg = _node(preload("res://scripts/bg.gd"), bg_layer)
	world = _node(preload("res://scripts/world.gd"), svp)
	actors = _node(preload("res://scripts/actors.gd"), svp)
	creature = _node(preload("res://scripts/creature.gd"), svp)
	front = _node(preload("res://scripts/front.gd"), svp)
	water = _node(preload("res://scripts/water.gd"), svp)
	fx = _node(preload("res://scripts/fx.gd"), svp)
	cam = Camera2D.new()
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 6.0
	svp.add_child(cam)
	cam.make_current()
	sfx = preload("res://scripts/sfx.gd").new()
	add_child(sfx)
	var hud_layer := CanvasLayer.new()
	hud_layer.layer = 10
	add_child(hud_layer)
	hud = preload("res://scripts/hud.gd").new()
	hud_layer.add_child(hud)
	G.world = world; G.actors = actors; G.creature = creature; G.fx = fx; G.cam = cam; G.hud = hud; G.sfx = sfx
	G.reset()
	world.load_map()
	actors.load_entities()
	hud.build()
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = world.W * TS
	cam.limit_bottom = world.H * TS
	explored.resize(world.W * world.H)
	map_img = Image.create(world.W, world.H, false, Image.FORMAT_RGBA8)
	map_tex = ImageTexture.create_from_image(map_img)
	creature.reset_at(actors.start, 5)
	cam.position = creature.position
	var args := OS.get_cmdline_user_args()
	for a in args:
		if a == "--autotest":
			_autotest()
			return
		if a.begins_with("--shots="):
			_shots(a.substr(8))
			return
	hud.show_title(FileAccess.file_exists(G.SAVE_PATH))
	sfx.start_drone()
	sfx.set_music("title")
	sfx.set_ambient("birds_dusk")


func _node(script: Script, parent: Node) -> Node:
	var n = script.new()
	parent.add_child(n)
	return n


# ---------------------------------------------------------------- game flow
func new_game() -> void:
	G.reset()
	world.reset_tiles()
	actors.load_entities()
	fx.clear()
	explored.fill(0)
	map_img.fill(Color(0, 0, 0, 0))
	creature.reset_at(actors.start, 5)
	cp_pos = actors.start + Vector2(0, -10)
	cp_mass = 5
	cp_index = -1
	flood_toast = false
	cam.position = creature.position
	cam.reset_smoothing()
	G.running = true
	hud.on_new_game()
	sfx.start_drone()
	get_tree().create_timer(7.0).timeout.connect(func():
		if G.running and G.voices.is_empty():
			hud.toast("You cling to any rough surface. Climb toward the light."))


func continue_game() -> void:
	new_game()
	load_game()


func _input(e: InputEvent) -> void:
	if not G.running or G.ended:
		return
	if e.is_action_pressed("pause"):
		hud.toggle_overlay("pause")
	elif e.is_action_pressed("map"):
		hud.toggle_overlay("map")
	elif e.is_action_pressed("chorus"):
		hud.toggle_overlay("chorus")
	elif e.is_action_pressed("mute"):
		hud.toast("Sound off" if sfx.toggle_mute() else "Sound on")


func _physics_process(delta: float) -> void:
	if not G.running or G.paused:
		return
	G.time += delta
	G.reveal_t = maxf(0.0, G.reveal_t - delta)
	G.shake = maxf(0.0, G.shake - delta * 14.0)
	if creature.dead:
		creature.dead_t -= delta
		if creature.dead_t <= 0.0:
			creature.reset_at(cp_pos, maxi(3, cp_mass))
			creature.inv = 2.0
	else:
		if not G.ended:
			if Input.is_action_just_pressed("take"):
				try_take()
			if Input.is_action_just_pressed("read"):
				creature.try_read()
			if Input.is_action_just_pressed("charge"):
				creature.try_charge()
			if Input.is_action_pressed("shed"):
				creature.try_shed()
		creature.physics(delta)
	actors.physics(delta)
	_update_grab(delta)
	fx.update(delta)
	_rules(delta)
	_camera(delta)
	hud_t -= delta
	if hud_t <= 0.0:
		hud_t = 0.1
		_refresh_hud()


func _camera(_delta: float) -> void:
	cam.position = creature.position + Vector2(0, -16)
	cam.offset = Vector2(randf_range(-1, 1), randf_range(-1, 1)) * G.shake


# ---------------------------------------------------------------- taking and graves
func try_take() -> void:
	if creature.grab != null:
		return
	var t = actors.find_target(creature.position, creature.r + 60.0)
	if t == null:
		return
	creature.grab = t
	var ref: Dictionary = t["ref"]
	match t["kind"]:
		"h":
			ref["state"] = "grabbed"
			sfx.play("swing")
			sfx.play("scream" if randf() < 0.5 else "scream2", 0.15)
		"a":
			ref["grabbed"] = true
			sfx.play("swing")
			sfx.play("bleat", 0.2)
		"g":
			sfx.play("crack", 0.2)


func _update_grab(delta: float) -> void:
	var g = creature.grab
	if g == null:
		return
	var ref: Dictionary = g["ref"]
	if g["kind"] == "g":
		g["t"] += delta
		if randf() < 0.4:
			fx.burst(ref["p"] + Vector2(0, -2), 1, [Color("6b4e34"), Color("3b2a1c")], 40.0, 300.0, 1.0, 0.6)
		if (ref["p"] as Vector2).distance_to(creature.position) > creature.r + 140.0 or creature.dead:
			creature.grab = null
		elif g["t"] > 1.1:
			open_grave(ref)
			creature.grab = null
		return
	if not ref["alive"]:
		creature.grab = null
		return
	var center: Vector2 = ref["p"] + Vector2(0, -12 if g["kind"] == "h" else -8)
	var d: Vector2 = creature.position - center
	if d.length() < creature.r + 6.0:
		consume(ref, g["kind"])
	else:
		ref["p"] = ref["p"] + d.normalized() * minf(d.length(), 190.0 * delta)
		if randf() < 0.3:
			fx.burst(center, 1, [Color("8c1c34")], 20.0, 300.0, 1.0, 0.6)


func consume(ref: Dictionary, kind: String) -> void:
	ref["alive"] = false
	creature.grab = null
	creature.mass += 1
	var center: Vector2 = ref["p"] + Vector2(0, -10)
	fx.gore(center)
	G.shake = maxf(G.shake, 4.0)
	sfx.play("squelch")
	fx.float_text(creature.position + Vector2(0, -creature.r - 8), "+1 mass", Color("e0566a"))
	if kind == "a":
		ref["grabbed"] = false
		ref["respawn"] = 45.0
		return
	var typ: String = ref["t"]
	G.counts[typ] += 1
	G.taken += 1
	G.add_voice(ref["name"], ref["line"], "living")
	if UNLOCK.has(typ):
		var a: String = UNLOCK[typ]
		if not G.ab[a] and G.counts[typ] >= 3:
			G.ab[a] = true
			var m: Dictionary = Data.MEMS[a]
			hud.card(m["from"], m["title"], m["how"], "“" + m["quote"] + "”")
			sfx.play("unlock", 0.0)


func open_grave(g: Dictionary) -> void:
	g["opened"] = true
	G.kept += 1
	fx.burst(g["p"] + Vector2(0, -4), 22, [Color("6b4e34"), Color("8f7458"), Color("f2e6c8")], 80.0, 250.0, 1.5, 1.4)
	fx.burst(g["p"] + Vector2(0, -8), 10, [Color("ffd36b"), Color("fff1b8")], 30.0, -25.0, 1.0, 2.2)
	sfx.play("bell", 0.03)
	sfx.play("whisper", 0.1)
	fx.float_text(creature.position + Vector2(0, -creature.r - 8), "+1 memory", Color("ffd36b"))
	G.add_voice(g["name"], g["line"], "dead")


func hurt(n: int) -> void:
	if creature.inv > 0.0 or creature.dead or G.ended:
		return
	creature.mass -= n
	creature.inv = 0.9
	G.shake = maxf(G.shake, 4.0)
	fx.burst(creature.position, 12, [Color("4a0e24"), Color("8c1c34")], 100.0, 350.0, 1.5, 0.9)
	sfx.play("hurt")
	if creature.mass <= 0:
		creature.mass = 0
		creature.dead = true
		creature.dead_t = 2.6
		creature.anchors.clear()
		var g = creature.grab
		if g != null and g["kind"] == "h":
			g["ref"]["state"] = "alert"
		if g != null and g["kind"] == "a":
			g["ref"]["grabbed"] = false
		creature.grab = null
		fx.burst(creature.position, 50, [Color("8c1c34"), Color("4a0e24"), Color("2a0614")], 130.0, 380.0, 2.0, 1.6)
		hud.toast("The valley keeps you. You wake again in the last cellar hole.")


# ---------------------------------------------------------------- rules
func _rules(delta: float) -> void:
	var p: Vector2 = creature.position
	var z: int = G.zone_at(p.x)
	if z != G.zone:
		G.zone = z
		if not G.zone_seen[z]:
			G.zone_seen[z] = true
			var Z: Dictionary = Data.ZONES[z]
			hud.card("%s · %s" % [Z["n"], Z["place"]], Z["name"], Z["intro"])
	if not creature.dead:
		for i in actors.cps.size():
			var k: Dictionary = actors.cps[i]
			if (k["p"] + Vector2(0, -8)).distance_to(p) < creature.r + 18.0:
				if cp_index != i:
					cp_index = i
					if not k["on"]:
						hud.toast("You root into the cellar hole. The valley will remember you here.")
						fx.burst(k["p"] + Vector2(0, -4), 12, [Color("8c1c34"), Color("c42a3f")], 40.0, 120.0, 1.0, 1.0)
					k["on"] = true
					cp_pos = k["p"] + Vector2(0, -14)
					cp_mass = creature.mass
					save_game()
			elif cp_index == i and (k["p"]).distance_to(p) > 120.0:
				cp_index = -1
	if not G.flood and p.x > 315.0 * TS and p.y > 62.0 * TS:
		G.flood = true
		G.water_y = FLOOD_START_Y
		for h in actors.people:
			if h["alive"] and h["p"].x < 350.0 * TS:
				h["alive"] = false
		hud.toast("The gates at the dam are closed. The whole valley is filling.")
		sfx.play("flood", 0.0)
	if G.flood and G.water_y > G.FLOOD_FULL_Y:
		G.water_y = maxf(G.FLOOD_FULL_Y, G.water_y - G.flood_speed * delta)
		if G.water_y <= G.FLOOD_FULL_Y and not flood_toast:
			flood_toast = true
			hud.toast("Full pool. Everything below the line is lake now. Places you could not reach are within reach.")
	if not G.ended and not creature.dead and G.water_y <= G.FLOOD_FULL_Y + 12.0:
		if creature.position.distance_to(actors.intake + Vector2(0, -20)) < creature.r + 30.0:
			_finish()
	explore_t -= delta
	if explore_t <= 0.0:
		explore_t = 0.25
		_explore()


func _explore() -> void:
	var cx := floori(creature.position.x / TS)
	var cy := floori(creature.position.y / TS)
	var changed := false
	for y in range(cy - 10, cy + 11):
		for x in range(cx - 16, cx + 17):
			if x < 0 or y < 0 or x >= world.W or y >= world.H:
				continue
			var i: int = y * world.W + x
			if explored[i] == 0:
				explored[i] = 1
				changed = true
				map_img.set_pixel(x, y, _map_color(world.t[i]))
	if changed:
		map_tex.update(map_img)


func _map_color(v: int) -> Color:
	match v:
		Tiles.E, Tiles.OPEN: return Color(0.16, 0.2, 0.3, 1)
		Tiles.DIRT: return Color("6b4e34")
		Tiles.WOOD: return Color("a0703c")
		Tiles.GRAN: return Color("c9b8b4")
		Tiles.CONC: return Color("7d8a86")
		Tiles.BOARDS: return Color("b8955a")
		Tiles.CLIFF: return Color("2a2f3e")
	return Color("4f5a70")


func _refresh_hud() -> void:
	var z: Dictionary = Data.ZONES[maxi(0, G.zone)]
	var obj := ""
	if G.zone < 4:
		var typ: String = z["type"]
		if not G.ab[z["ab"]]:
			obj = "Take %s.  %d / 3" % [z["noun"], mini(3, G.counts[typ])]
		else:
			obj = z["done"]
		if G.zone == 2 and creature.position.x < 184.0 * TS and creature.mass > G.CRAWL_MASS:
			obj += "
The way east is a crawlway that fits %d mass. You are %d. Hold Q at the spring west of the wall." % [G.CRAWL_MASS, creature.mass]
	elif not G.flood:
		obj = "Drop into the basin."
	elif G.water_y > G.FLOOD_FULL_Y + 1.0:
		var el := roundi(380.0 + (FLOOD_START_Y - G.water_y) / (FLOOD_START_Y - G.FLOOD_FULL_Y) * 150.0)
		obj = "The water is rising. Elevation %d ft." % el
	else:
		obj = "Full pool, 530 ft. Reach the intake, or swim back for the graves the water opened."
	hud.refresh(z, obj, creature.mass)
	_pick_audio()
	hud.set_hint(_hint())
	actors.hover = null if creature.grab != null or creature.dead else actors.find_target(creature.position, creature.r + 60.0)


func _pick_audio() -> void:
	const AMB := {"enfield": "birds", "greenwich": "birds_dusk", "dana": "birds", "works": "machines", "basin": "night"}
	var z: Dictionary = Data.ZONES[maxi(0, G.zone)]
	if G.flood and G.water_y < 60.0 * TS:
		sfx.set_music("basin")
		sfx.set_ambient("water")
	elif G.zone < 4 and creature.position.y > 47.0 * TS:
		sfx.set_music("cave")
		sfx.set_ambient("cave")
	else:
		sfx.set_music(z["bg"])
		sfx.set_ambient(AMB[z["bg"]])


func _hint() -> String:
	if creature.dead or G.ended:
		return ""
	var t = actors.hover
	if t != null:
		match t["kind"]:
			"h": return "SPACE  take " + Data.LABEL[t["ref"]["t"]]
			"a": return "SPACE  take " + Data.LABEL[t["ref"]["t"]]
			"g": return "SPACE  open the grave of " + String(t["ref"]["name"]).split(",")[0]
	if actors.near_spring(creature.position, creature.r) != null and creature.mass > 2:
		return "HOLD Q  give mass back to the spring  (mass %d, crawlways fit %d)" % [creature.mass, G.CRAWL_MASS]
	if creature.near_tile(Tiles.GRAN, creature.r + 26.0) != null:
		return "E  set a charge in the granite" if G.ab["charge"] else "Granite. You do not know how to break it yet."
	if creature.near_tile(Tiles.WOOD, creature.r + 20.0) != null and not G.ab["axe"]:
		return "A jam of felled timber. You do not know how to break it yet."
	if creature.near_tile(Tiles.BOARDS, creature.r + 12.0) != null and creature.mass < G.HEAVY:
		return "Rotten boards creak under you. Something heavier would go through.  (%d / %d)" % [creature.mass, G.HEAVY]
	if creature.near_tile(Tiles.FALSE, creature.r + 40.0) != null:
		return "F  read the land" if G.ab["level"] else "Solid rock. Or something that wants you to think so."
	if creature.near_tile(Tiles.DIRT, creature.r + 4.0) != null and not G.ab["shovel"] and creature.position.y > 44 * TS:
		return "Soft earth, packed too tight for you. For now."
	if creature.mass > G.CRAWL_MASS and (_near_crawl() or (G.zone == 2 and creature.position.x > 172.0 * TS and creature.position.x < 184.0 * TS)):
		return "Too much of you for the crawlway (%d, fits %d). Hold Q at the spring just west of the wall." % [creature.mass, G.CRAWL_MASS]
	return ""


func _near_crawl() -> bool:
	# a one-tile gap beside the body: open cell with solid directly above and below
	var cx := floori(creature.position.x / TS)
	var cy := floori(creature.position.y / TS)
	for dx in [-2, -1, 1, 2]:
		for dy in [-1, 0, 1]:
			var x: int = cx + dx
			var y: int = cy + dy
			if world.tile(x, y) == Tiles.E and world.solid_c(world.tile(x, y - 1)) and world.solid_c(world.tile(x, y + 1)):
				return true
	return false


func _finish() -> void:
	G.ended = true
	var memory: bool = G.kept >= G.taken
	var e: Dictionary = Data.ENDINGS["memory" if memory else "hunger"]
	var tally := "You took %d of the living and kept %d of the dead. Graves opened: %d of %d." % [G.taken, G.kept, G.kept, actors.graves.size()]
	tally += "  Say the towns so they stay." if memory else "  Keep as many of the dead as you take, and the city will remember instead."
	sfx.play("bell", 0.0)
	sfx.play("flood", 0.0)
	await get_tree().create_timer(1.8).timeout
	G.running = false
	sfx.set_music("title")
	sfx.set_ambient("water")
	hud.show_ending(e["title"], e["body"], tally)


# ---------------------------------------------------------------- saving
func save_game() -> void:
	var d := {
		"ab": G.ab, "counts": G.counts, "taken": G.taken, "kept": G.kept, "voices": G.voices,
		"flood": G.flood, "water_y": G.water_y, "zone_seen": G.zone_seen, "time": G.time,
		"mass": creature.mass, "cp": [cp_pos.x, cp_pos.y], "cp_mass": cp_mass,
		"dead": actors.people.filter(func(h): return not h["alive"]).map(func(h): return h["id"]),
		"graves": actors.graves.filter(func(g): return g["opened"]).map(func(g): return g["id"]),
		"cps": range(actors.cps.size()).filter(func(i): return actors.cps[i]["on"]),
		"tiles": world.changes(),
		"explored": Marshalls.raw_to_base64(explored.compress(FileAccess.COMPRESSION_DEFLATE)),
	}
	var f := FileAccess.open(G.SAVE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(d))


func load_game() -> void:
	var raw := FileAccess.get_file_as_string(G.SAVE_PATH)
	var d = JSON.parse_string(raw)
	if typeof(d) != TYPE_DICTIONARY:
		return
	for k in d["ab"]:
		G.ab[k] = bool(d["ab"][k])
	for k in d["counts"]:
		G.counts[k] = int(d["counts"][k])
	G.taken = int(d["taken"])
	G.kept = int(d["kept"])
	G.voices = d["voices"]
	G.flood = bool(d["flood"])
	G.water_y = float(d["water_y"])
	G.zone_seen = d["zone_seen"]
	G.time = float(d["time"])
	for id in d["dead"]:
		actors.people[int(id)]["alive"] = false
	for id in d["graves"]:
		actors.graves[int(id)]["opened"] = true
	for i in d["cps"]:
		actors.cps[int(i)]["on"] = true
	world.apply_changes(d["tiles"])
	var ex: PackedByteArray = Marshalls.base64_to_raw(d["explored"]).decompress(world.W * world.H, FileAccess.COMPRESSION_DEFLATE)
	if ex.size() == explored.size():
		explored = ex
		for i in explored.size():
			if explored[i] == 1:
				map_img.set_pixel(i % world.W, i / world.W, _map_color(world.t[i]))
		map_tex.update(map_img)
	cp_pos = Vector2(d["cp"][0], d["cp"][1])
	cp_mass = int(d["cp_mass"])
	creature.reset_at(cp_pos, int(d["mass"]))
	cam.position = creature.position
	cam.reset_smoothing()
	if G.flood and G.water_y <= G.FLOOD_FULL_Y:
		flood_toast = true
	hud.voices_changed()


# ---------------------------------------------------------------- automated checks
func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _tp(tx: float, ty: float, mass: int) -> void:
	creature.reset_at(Vector2(tx * TS, ty * TS), mass)
	creature.inv = 999.0


func _hold(dir: Vector2, frames: int) -> void:
	creature.input_override = dir
	await _frames(frames)
	creature.input_override = Vector2.ZERO


func _autotest() -> void:
	new_game()
	G.zone_seen = [true, true, true, true, true]
	var fails := [0]
	var report := func(name: String, ok: bool, info: String):
		print(("PASS  " if ok else "FAIL  ") + name + "  " + info)
		if not ok:
			fails[0] += 1
	await _frames(10)
	# climbing out of the lair shaft
	_tp(22.6, 85.0, 5)
	await _hold(Vector2(-0.2, -1).normalized(), 300)
	report.call("climb lair shaft", creature.position.y < 64 * TS, str(creature.position / TS))
	# taking: three woodcutters unlock the Axe
	G.ab["axe"] = false
	for h in actors.people.filter(func(h): return h["t"] == "R").slice(0, 3):
		_tp(h["p"].x / TS - 1.5, h["p"].y / TS - 1.0, 6)
		await _frames(3)
		try_take()
		await _frames(90)
	report.call("take three woodcutters", G.counts["R"] == 3 and G.ab["axe"], "R=%d axe=%s" % [G.counts["R"], G.ab["axe"]])
	# a grave
	var g0: Dictionary = actors.graves[8]
	_tp(g0["p"].x / TS - 1.5, g0["p"].y / TS - 1.0, 6)
	await _frames(3)
	try_take()
	await _frames(100)
	report.call("open a grave", G.kept == 1 and g0["opened"], "kept=%d" % G.kept)
	# gates
	_tp(70, 43.4, 8)
	await _hold(Vector2.RIGHT, 240)
	report.call("timber gate (Axe)", creature.position.x > 79 * TS, str(creature.position / TS))
	G.ab["shovel"] = true
	_tp(150, 43.4, 8)
	await _hold(Vector2(1, 1).normalized(), 150)
	await _hold(Vector2.RIGHT, 300)
	await _hold(Vector2.UP, 200)
	report.call("soft earth under ridge (Shovel)", creature.position.x > 158 * TS, str(creature.position / TS))
	_tp(180, 43.4, G.CRAWL_MASS)
	await _hold(Vector2.RIGHT, 240)
	report.call("crawlway at the size limit", creature.position.x > 189 * TS, str(creature.position / TS))
	_tp(180, 43.0, G.CRAWL_MASS + 1)
	await _hold(Vector2.RIGHT, 240)
	report.call("crawlway blocks when large", creature.position.x < 185 * TS, str(creature.position / TS))
	G.ab["level"] = true
	_tp(232, 43.4, 8)
	await _frames(5)
	creature.try_read()
	await _frames(90)
	await _hold(Vector2.RIGHT, 240)
	report.call("false wall (Level)", creature.position.x > 241 * TS, str(creature.position / TS))
	G.ab["charge"] = true
	_tp(304.5, 43.4, 8)
	await _frames(5)
	creature.try_charge()
	await _frames(110)
	await _hold(Vector2.RIGHT, 50)
	creature.try_charge()
	await _frames(110)
	await _hold(Vector2.RIGHT, 240)
	report.call("granite plug (Charge)", creature.position.x > 311 * TS, str(creature.position / TS))
	_tp(50.5, 43.0, 12)
	await _frames(120)
	report.call("rotten boards break when heavy", creature.position.y > 46 * TS, str(creature.position / TS))
	_tp(100.5, 43.0, 6)
	await _frames(90)
	report.call("rotten boards hold when light", creature.position.y < 44 * TS, str(creature.position / TS))
	# spring
	var sp: Dictionary = actors.springs[2]
	_tp(sp["p"].x / TS, sp["p"].y / TS - 0.6, 9)
	await _frames(5)
	for i in 30:
		creature.try_shed()
		await _frames(2)
	report.call("shed mass at a spring", creature.mass < 9, "mass=%d" % creature.mass)
	# flood and ending
	G.flood_speed = 400.0
	_tp(330, 73.0, 8)
	await _frames(40)
	report.call("flood starts in the basin", G.flood, "")
	await _frames(240)
	report.call("water reaches full pool", G.water_y <= G.FLOOD_FULL_Y + 0.1, "water row %.1f" % (G.water_y / TS))
	_tp(345, 40.0, 8)
	await _hold(Vector2.UP, 60)
	report.call("swimming holds at the surface", creature.in_water or creature.position.y < 37 * TS, str(creature.position / TS))
	_tp(20.5, 37.0, 8)
	await _hold(Vector2(1, -1).normalized(), 150)
	report.call("flood reaches Quabbin Hill top", creature.position.y < 35 * TS, str(creature.position / TS))
	save_game()
	report.call("save file written", FileAccess.file_exists(G.SAVE_PATH), "")
	_tp(366, 35.0, 8)
	await _hold(Vector2.RIGHT, 60)
	await _frames(20)
	report.call("reaching the intake ends the game", G.ended, "taken=%d kept=%d" % [G.taken, G.kept])
	DirAccess.remove_absolute(ProjectSettings.globalize_path(G.SAVE_PATH))
	print("AUTOTEST %s (%d failures)" % ["OK" if fails[0] == 0 else "FAILED", fails[0]])
	get_tree().quit(1 if fails[0] > 0 else 0)


func _shots(dir: String) -> void:
	new_game()
	G.zone_seen = [true, true, true, true, true]
	var spots := [
		["01_lair", 18.0, 94.0, false], ["02_enfield", 44.0, 43.0, false], ["03_rootcave", 30.0, 58.0, false],
		["04_greenwich", 112.0, 43.0, false], ["05_crypt", 100.0, 57.0, false], ["06_dana", 214.0, 43.0, false],
		["07_millrace", 200.0, 66.0, false], ["08_works", 268.0, 43.0, false], ["09_basin", 340.0, 72.0, false],
		["10_flooded_enfield", 19.0, 36.0, true], ["11_intake", 362.0, 35.0, true],
	]
	for s in spots:
		if s[3]:
			G.flood = true
			G.water_y = G.FLOOD_FULL_Y
		_tp(s[1], s[2], 9)
		creature.inv = 0.0
		cam.position = creature.position
		cam.reset_smoothing()
		await _frames(50)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(dir.path_join(s[0] + ".png"))
	# a title-screen shot
	G.running = false
	hud.show_title(false)
	await _frames(10)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("00_title.png"))
	get_tree().quit()
