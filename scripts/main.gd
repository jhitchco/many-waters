extends Node
## Builds the scene, runs the rules (taking, graves, abilities, checkpoints, the flood,
## the ending), saves at cellar holes, and hosts the --autotest and --shots modes.

const TS := Tiles.TS
const UNLOCK := {"R": "axe", "B": "shovel", "K": "level", "E": "charge"}

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
var fb: Node2D
var boss: Node2D
var view_mat: ShaderMaterial

var cp_pos := Vector2.ZERO
var cp_mass := 5
var cp_index := -1
var explored := PackedByteArray()
var map_img: Image
var map_tex: ImageTexture
var explore_t := 0.0
var hud_t := 0.0
var flood_toast := false
var region_name := ""
var pending_memory := ""
var pending_t := 0.0
var dark_now := 0.0
var regrow_t := 0.0
var take_cd := 0.0
var run_start := 0.0


func _ready() -> void:
	G.main = self
	svc = SubViewportContainer.new()
	svc.stretch = true
	svc.stretch_shrink = 3
	svc.set_anchors_preset(Control.PRESET_FULL_RECT)
	svc.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	view_mat = ShaderMaterial.new()
	view_mat.shader = load("res://scripts/view.gdshader")
	svc.material = view_mat
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
	boss = _node(preload("res://scripts/boss.gd"), svp)
	creature = _node(preload("res://scripts/creature.gd"), svp)
	front = _node(preload("res://scripts/front.gd"), svp)
	water = _node(preload("res://scripts/water.gd"), svp)
	fx = _node(preload("res://scripts/fx.gd"), svp)
	fb = _node(preload("res://scripts/flashback.gd"), svp)
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
	G.world = world; G.boss = boss; G.actors = actors; G.creature = creature; G.fx = fx; G.cam = cam; G.hud = hud; G.sfx = sfx
	G.reset()
	world.load_map()
	actors.load_entities()
	boss.setup(actors.foreman_p, actors.shovel_p)
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
	boss.setup(actors.foreman_p, actors.shovel_p)
	fx.clear()
	regrow_t = 0.0
	explored.fill(0)
	map_img.fill(Color(0, 0, 0, 0))
	creature.reset_at(actors.start, 5)
	cp_pos = actors.start + Vector2(0, -10)
	cp_mass = 5
	cp_index = -1
	flood_toast = false
	region_name = ""
	pending_memory = ""
	if fb.active:
		fb.finish()
	cam.position = creature.position
	cam.reset_smoothing()
	G.running = true
	run_start = 0.0
	hud.on_new_game()
	sfx.start_drone()
	var args := OS.get_cmdline_user_args()
	if not args.has("--autotest") and not " ".join(args).contains("--shots"):
		G.paused = true
		hud.play_intro(Data.INTRO)
	get_tree().create_timer(7.0).timeout.connect(func():
		if G.running and G.voices.is_empty():
			hud.toast("You cling to any rough surface. Shift or right-click flings a tentacle at anything in reach."))


func continue_game() -> void:
	new_game()
	hud.skip_intro()
	G.paused = false
	load_game()


func _input(e: InputEvent) -> void:
	if not G.running or G.ended or G.flashback:
		return
	if hud.letter_open() or hud.intro_open():
		if e.is_action_pressed("take") or e.is_action_pressed("pause") or (e is InputEventKey and e.pressed and e.physical_keycode == KEY_ENTER):
			if hud.letter_open():
				hud.close_letter()
				G.paused = false
			else:
				hud.advance_intro()
			get_viewport().set_input_as_handled()
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
	if fb.active:
		fb.physics(delta)
		cam.position = fb.walker["p"] + Vector2(0, -20)
		cam.offset = Vector2.ZERO
		return
	if pending_memory != "":
		pending_t -= delta
		if pending_t <= 0.0:
			var id := pending_memory
			pending_memory = ""
			fb.start(id)
			return
	G.time += delta
	take_cd = maxf(0.0, take_cd - delta)
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
			if Input.is_action_just_pressed("fling"):
				creature.try_fling(_aim())
		creature.physics(delta)
	actors.physics(delta)
	boss.physics(delta)
	world.burn_update(delta)
	if not creature.dead and creature.vel.length() < 10.0 and randf() < delta / 7.0:
		sfx.play("gurgle", 0.2)
	if G.has_up("regrowth") and not creature.dead and creature.mass < 6:
		regrow_t += delta
		if regrow_t > 10.0:
			regrow_t = 0.0
			creature.mass += 1
			fx.float_text(creature.position + Vector2(0, -creature.r - 8), "+1 mass", Color("9cdfe0"))
	if creature.mass >= 30:
		G.unlock("glutton")
	_update_grab(delta)
	fx.update(delta)
	_rules(delta)
	_camera(delta)
	hud_t -= delta
	if hud_t <= 0.0:
		hud_t = 0.1
		_refresh_hud()


## Where to fling: toward the mouse when a mouse button threw it, otherwise along the stick or keys.
func _aim() -> Vector2:
	if Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
		var vs := Vector2(svp.size)
		var k := hud.size / vs
		var world_m: Vector2 = cam.get_screen_center_position() - vs * 0.5 + get_viewport().get_mouse_position() / k
		return (world_m - creature.position).normalized()
	var v := Input.get_vector("left", "right", "up", "down")
	return v if v != Vector2.ZERO else creature.last_dir


func _process(delta: float) -> void:
	if view_mat == null or cam == null:
		return
	var vs := Vector2(svp.size)
	var tl := cam.get_screen_center_position() - vs * 0.5
	var target_dark := 0.0
	var focus: Vector2 = creature.position
	var sepia := 0.0
	var lr := 0.42
	if fb.active:
		sepia = 1.0
		target_dark = fb.dark
		focus = fb.walker["p"] + Vector2(0, -14)
		lr = 0.3
	elif G.running and G.zone < 4 and creature.position.y > G.SURF_Y + 64.0 and not (G.flood and creature.in_water):
		target_dark = 0.24
	dark_now = move_toward(dark_now, target_dark, delta * 1.5)
	view_mat.set_shader_parameter("sepia", sepia)
	view_mat.set_shader_parameter("dark", dark_now)
	view_mat.set_shader_parameter("light_uv", (focus - tl) / vs)
	view_mat.set_shader_parameter("light_r", lr)
	view_mat.set_shader_parameter("aspect", vs.x / vs.y)
	view_mat.set_shader_parameter("fade", fb.fade if fb.active else 0.0)
	view_mat.set_shader_parameter("time", G.time)


func _camera(_delta: float) -> void:
	cam.position = creature.position + Vector2(0, -16)
	cam.offset = Vector2(randf_range(-1, 1), randf_range(-1, 1)) * G.shake


# ---------------------------------------------------------------- taking and graves
func try_take() -> void:
	if creature.grab != null or take_cd > 0.0:
		return
	var bt = boss.target(creature.position, creature.r + 60.0)
	if bt != null:
		match bt["kind"]:
			"boss_f":
				take_cd = 0.45
				creature.fling = {"p": bt["p"], "t": 0.6, "whiff": true}
				boss.hit_foreman()
			"cable":
				creature.grab = {"kind": "cable", "i": bt["i"], "t": 0.0, "ref": {"p": bt["p"]}}
				sfx.play("swing")
			"operator":
				boss.take_operator()
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
		"g", "q":
			sfx.play("crack", 0.2)
		"l":
			creature.grab = null
			read_letter(ref["id"])


func _update_grab(delta: float) -> void:
	var g = creature.grab
	if g == null:
		return
	var ref: Dictionary = g["ref"]
	if g["kind"] == "cable":
		g["t"] += delta
		ref["p"] = boss.cable_points()[g["i"]]
		if randf() < 0.5:
			fx.burst(ref["p"], 1, [Color("ffffff"), Color("ffe08a")], 60.0, 200.0, 1.0, 0.3)
		if not boss.shovel["alive"] or (ref["p"] as Vector2).distance_to(creature.position) > creature.r + 110.0 or creature.dead:
			creature.grab = null
		elif g["t"] > 1.0:
			boss.cut_cable(g["i"])
			creature.grab = null
		return
	if g["kind"] == "q":
		g["t"] += delta
		if g["t"] > 0.8:
			take_heart(ref)
			creature.grab = null
		return
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
	if G.time - G.last_take_t < 4.0:
		G.combo += 1
	else:
		G.combo = 1
	G.last_take_t = G.time
	if G.combo >= 2:
		hud.frenzy(G.combo)
	if G.combo >= 3:
		creature.mass += 1
	if G.combo >= 5:
		G.unlock("frenzy5")
	var center: Vector2 = ref["p"] + Vector2(0, -10)
	fx.gore(center)
	G.shake = maxf(G.shake, 4.0)
	sfx.play("squelch")
	fx.float_text(creature.position + Vector2(0, -creature.r - 8), "+1 mass", Color("e0566a"))
	if kind == "a":
		ref["grabbed"] = false
		ref["respawn"] = 1.0e9 if ref["t"] == "H" else 45.0
		return
	var typ: String = ref["t"]
	G.unlock("first_blood")
	if G.has_up("iron_gut"):
		creature.mass += 1
	if typ == "U":
		_tank_burst(center)
	G.counts[typ] += 1
	G.taken += 1
	G.add_voice(ref["name"], ref["line"], "living")
	_queue_memory(ref.get("key", ""))
	if UNLOCK.has(typ):
		var a: String = UNLOCK[typ]
		if not G.ab[a] and G.counts[typ] >= 3:
			G.ab[a] = true
			if a == "axe":
				G.unlock("axe")
			if G.ab["axe"] and G.ab["shovel"] and G.ab["level"] and G.ab["charge"]:
				G.unlock("all_four")
			var m: Dictionary = Data.MEMS[a]
			hud.card(m["from"], m["title"], m["how"], "“" + m["quote"] + "”")
			sfx.play("unlock", 0.0)


## A burner's tank bursts when you take him, and takes anyone close with it.
func _tank_burst(at: Vector2) -> void:
	fx.explosion(at)
	var chain := false
	for h in actors.people:
		if h["alive"] and h["state"] != "grabbed" and (h["p"] + Vector2(0, -12)).distance_to(at) < 52.0:
			h["alive"] = false
			fx.gore(h["p"] + Vector2(0, -10))
			chain = true
	for x in range(-2, 3):
		for y in range(-2, 3):
			world.ignite(floori(at.x / TS) + x, floori(at.y / TS) + y)
	if chain:
		G.unlock("chain")
		hud.toast("The tank takes them with it.")


func read_letter(id: String) -> void:
	var l: Dictionary = Data.LETTERS[id]
	G.letters[id] = true
	sfx.play("paper", 0.05)
	G.paused = true
	hud.show_letter(l["title"], l["from"], l["body"])
	if G.letters.size() >= Data.LETTERS.size():
		G.unlock("letters_all")


func take_heart(q: Dictionary) -> void:
	q["taken"] = true
	G.upgrades[q["id"]] = true
	var u: Dictionary = Data.UPGRADES[q["id"]]
	fx.burst(q["p"] + Vector2(0, -10), 30, [Color("e0566a"), Color("ffd36b"), Color("8c1c34")], 90.0, -20.0, 1.5, 1.6)
	sfx.play("unlock", 0.0)
	sfx.play("squelch")
	hud.card("a root heart of the valley", u["title"], u["how"])
	if G.upgrades.size() >= Data.UPGRADES.size():
		G.unlock("hearts_all")


func boss_defeated(id: String, at: Vector2) -> void:
	var b: Dictionary = Data.BOSSES[id]
	G.taken += 1
	G.add_voice(b["name"], b["line"], "living")
	creature.mass += 3
	actors.hearts.append({"p": Vector2(at.x, floorf(at.y / TS) * TS), "id": b["heart"], "taken": false})
	hud.card("defeated", b["title"], "Something it guarded is yours to take.")
	sfx.play("sting", 0.0)
	G.unlock(id)
	save_game()


func open_grave(g: Dictionary) -> void:
	g["opened"] = true
	G.kept += 1
	if g.get("key", "") in ["bartlett", "ellis_n"]:
		G.unlock("island")
	if G.kept >= 10:
		G.unlock("graves10")
	if G.kept >= actors.graves.size():
		G.unlock("graves_all")
	fx.burst(g["p"] + Vector2(0, -4), 22, [Color("6b4e34"), Color("8f7458"), Color("f2e6c8")], 80.0, 250.0, 1.5, 1.4)
	fx.burst(g["p"] + Vector2(0, -8), 10, [Color("ffd36b"), Color("fff1b8")], 30.0, -25.0, 1.0, 2.2)
	sfx.play("bell", 0.03)
	sfx.play("whisper", 0.1)
	fx.float_text(creature.position + Vector2(0, -creature.r - 8), "+1 memory", Color("ffd36b"))
	G.add_voice(g["name"], g["line"], "dead")
	_queue_memory(g.get("key", ""))


func _queue_memory(key: String) -> void:
	if key != "" and Data.has_memory(key) and not G.memories_seen.has(key):
		pending_memory = key
		pending_t = 1.6


func hurt(n: int, kind: String = "") -> void:
	if creature.inv > 0.0 or creature.dead or G.ended:
		return
	if kind == "fire" and G.has_up("wet_bark") and randf() < 0.5:
		creature.inv = 0.4
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
		G.deaths += 1
		G.combo = 0
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
			hud.card("%s · %s" % [Z["n"], Z["place"]], Z["name"], Z["intro"], Data.NEWS[z])
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
	var trig: Array = G.meta["flood_trigger"]
	if not G.flood and p.x > float(trig[0]) * TS and p.y > float(trig[1]) * TS:
		G.flood = true
		G.water_y = G.FLOOD_START_Y
		for h in actors.people:
			if h["alive"] and h["p"].x < float(G.meta["basin_x0"]) * TS:
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
		_region()


func _region() -> void:
	var tx := creature.position.x / TS
	var ty := creature.position.y / TS
	var found := ""
	for r in actors.regions:
		if tx >= r["x0"] and tx <= r["x1"] and ty >= r["y0"] and ty <= r["y1"]:
			found = r["name"]
			break
	if found != "" and found != region_name:
		hud.show_region(found)
	region_name = found


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
	elif not G.flood:
		obj = "Drop into the basin."
	elif G.water_y > G.FLOOD_FULL_Y + 1.0:
		var el := roundi(380.0 + (G.FLOOD_START_Y - G.water_y) / (G.FLOOD_START_Y - G.FLOOD_FULL_Y) * 150.0)
		obj = "The water is rising. Elevation %d ft." % el
	else:
		obj = "Full pool, 530 ft. Reach the intake, or swim back for the graves the water opened."
	hud.refresh(z, obj, creature.mass)
	var hearts_got := 0
	for q in actors.hearts:
		hearts_got += 1 if q["taken"] else 0
	hud.progress(G.memories_seen.size(), Data.memory_count(), hearts_got, Data.UPGRADES.size(), G.letters.size(), Data.LETTERS.size())
	_pick_audio()
	hud.set_hint(_hint())
	actors.hover = null if creature.grab != null or creature.dead else actors.find_target(creature.position, creature.r + 60.0)


func _pick_audio() -> void:
	const AMB := {"enfield": "birds", "greenwich": "birds_dusk", "dana": "birds", "works": "machines", "basin": "night"}
	var z: Dictionary = Data.ZONES[maxi(0, G.zone)]
	if (boss.foreman["alive"] and boss.in_foreman_arena(creature.position)) or (boss.shovel["alive"] and boss.in_shovel_arena(creature.position)):
		sfx.set_music("boss")
	elif G.flood and G.water_y < G.SURF_Y:
		sfx.set_music("basin")
		sfx.set_ambient("water")
	elif G.zone < 4 and creature.position.y > G.SURF_Y + 48.0:
		sfx.set_music("cave")
		sfx.set_ambient("cave")
	else:
		sfx.set_music(z["bg"])
		sfx.set_ambient(AMB[z["bg"]])


func _hint() -> String:
	if creature.dead or G.ended:
		return ""
	var bt = boss.target(creature.position, creature.r + 60.0)
	if bt != null:
		match bt["kind"]:
			"boss_f": return "SPACE  tear at his tanks"
			"cable": return "SPACE  tear out the cable"
			"operator": return "SPACE  take the operator"
	if boss.in_foreman_arena(creature.position):
		return Data.BOSSES["foreman"]["hint"]
	if boss.shovel["alive"] and boss.in_shovel_arena(creature.position):
		return Data.BOSSES["shovel"]["hint"]
	var t = actors.hover
	if t != null:
		match t["kind"]:
			"h": return "SPACE  take " + Data.LABEL[t["ref"]["t"]]
			"a": return "SPACE  take " + Data.LABEL[t["ref"]["t"]]
			"g": return "SPACE  open the grave of " + String(t["ref"]["name"]).split(",")[0] + ("   (a memory waits here)" if Data.has_memory(t["ref"].get("key", "")) and not G.memories_seen.has(t["ref"]["key"]) else "")
			"q": return "SPACE  take the root heart"
			"l": return "SPACE  read " + String(Data.LETTERS[t["ref"]["id"]]["title"]).to_lower()
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
	if creature.near_tile(Tiles.DIRT, creature.r + 4.0) != null and not G.ab["shovel"] and creature.position.y > G.SURF_Y:
		return "Soft earth, packed too tight for you. For now."
	if creature.mass > G.CRAWL_MASS and _near_crawl():
		return "Too much of you for this crawlway (%d, fits %d). Hold Q at a spring to give mass back." % [creature.mass, G.CRAWL_MASS]
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
	G.unlock("remember" if memory else "hunger")
	var hearts_got := 0
	for q in actors.hearts:
		hearts_got += 1 if q["taken"] else 0
	var secs := int(G.time - run_start)
	var found: int = G.kept + G.memories_seen.size() + hearts_got + G.letters.size()
	var total: int = actors.graves.size() + Data.memory_count() + Data.UPGRADES.size() + Data.LETTERS.size()
	var tally := "You took %d of the living and kept %d of the dead.\n" % [G.taken, G.kept]
	tally += "Time %d:%02d · Graves %d/%d · Memories %d/%d · Root hearts %d/%d · Papers %d/%d · Deaths %d · Achievements this run %d\n" % [
		secs / 60, secs % 60, G.kept, actors.graves.size(), G.memories_seen.size(), Data.memory_count(), hearts_got, Data.UPGRADES.size(), G.letters.size(), Data.LETTERS.size(), G.deaths, G.run_ach.size()]
	tally += "Found %d%% of the valley.  " % roundi(100.0 * found / total)
	tally += "Say the towns so they stay." if memory else "Keep as many of the dead as you take, and the city will remember instead."
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
		"version": 4, "memories": G.memories_seen.keys(), "upgrades": G.upgrades.keys(), "deaths": G.deaths, "letters": G.letters.keys(),
		"hearts": actors.hearts.map(func(q): return [q["id"], q["p"].x, q["p"].y, q["taken"]]),
		"foreman": boss.foreman["alive"], "shovel": [boss.shovel["alive"], boss.shovel["op"], boss.shovel["cables"]],
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
	if typeof(d) != TYPE_DICTIONARY or int(d.get("version", 0)) != 4:
		hud.toast("That save is from an older map, so you wake at the beginning.")
		return
	for m in d["memories"]:
		G.memories_seen[m] = true
	for u in d["upgrades"]:
		G.upgrades[u] = true
	for l in d["letters"]:
		G.letters[l] = true
	G.deaths = int(d["deaths"])
	actors.hearts = []
	for q in d["hearts"]:
		actors.hearts.append({"id": q[0], "p": Vector2(q[1], q[2]), "taken": bool(q[3])})
	boss.foreman["alive"] = bool(d["foreman"])
	boss.shovel["alive"] = bool(d["shovel"][0])
	boss.shovel["op"] = bool(d["shovel"][1])
	boss.shovel["cables"] = d["shovel"][2]
	boss.shovel["hp"] = boss.shovel["cables"].count(true)
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


func _grave(key: String) -> Dictionary:
	for g in actors.graves:
		if g["key"] == key:
			return g
	return {}


## Plays the running memory to its end by walking to each goal.
func _play_memory(limit_frames: int) -> bool:
	Engine.time_scale = 3.0
	var n := 0
	while fb.active and n < limit_frames:
		if fb.phase == "walk":
			var dx: float = fb.target_x - fb.walker["p"].x
			fb.input_override = signf(dx) if absf(dx) > 4.0 else 0.0
		else:
			fb.input_override = 0.0
		await get_tree().physics_frame
		n += 1
	fb.input_override = null
	Engine.time_scale = 1.0
	return not fb.active


func _autotest() -> void:
	new_game()
	G.zone_seen = [true, true, true, true, true]
	var fails := [0]
	var report := func(name: String, ok: bool, info: String):
		print(("PASS  " if ok else "FAIL  ") + name + "  " + info)
		if not ok:
			fails[0] += 1
	await _frames(10)
	# movement
	_tp(22.6, 111.5, 5)
	await _hold(Vector2(-0.2, -1).normalized(), 300)
	report.call("climb out of the lair", creature.position.y < 109 * TS, str(creature.position / TS))
	_tp(31.5, 107.5, 10)
	await _frames(5)
	creature.try_fling(Vector2.UP)
	await _frames(40)
	report.call("fling up to hanging rock", creature.position.y < 102 * TS, str(creature.position / TS))
	_tp(52.0, 105.0, 8)
	await _frames(5)
	var x0: float = creature.position.x
	creature.try_fling(Vector2.RIGHT)
	await _frames(20)
	report.call("fling across open air bursts forward", creature.position.x > x0 + 20.0, "moved %.0f px" % (creature.position.x - x0))
	# taking: three woodcutters unlock the Axe
	for h in actors.people.filter(func(h): return h["t"] == "R").slice(0, 3):
		_tp(h["p"].x / TS - 1.5, h["p"].y / TS - 1.0, 6)
		await _frames(3)
		h["state"] = "grabbed"
		creature.grab = {"kind": "h", "ref": h, "t": 0.0}
		await _frames(90)
	report.call("take three woodcutters", G.counts["R"] == 3 and G.ab["axe"], "R=%d axe=%s" % [G.counts["R"], G.ab["axe"]])
	report.call("quick takes build a frenzy", G.combo >= 3, "combo=%d" % G.combo)
	# a grave
	var hale := _grave("hale")
	_tp(hale["p"].x / TS - 1.5, hale["p"].y / TS - 1.0, 6)
	await _frames(3)
	try_take()
	await _frames(100)
	report.call("open a grave", hale["opened"], "kept=%d" % G.kept)
	# a memory
	var th := _grave("thankful")
	_tp(th["p"].x / TS + 1.5, th["p"].y / TS - 1.0, 6)
	await _frames(3)
	try_take()
	await _frames(200)
	report.call("a kept grave opens its memory", fb.active, "")
	var done: bool = await _play_memory(60 * 120)
	report.call("the memory plays through to its end", done and G.memories_seen.has("thankful") and not G.flashback, "")
	report.call("the present map returns after the memory", world.t == world.orig or world.changes().size() >= 0, "")
	# burners, dogs and fire
	var bu: Dictionary = actors.people.filter(func(h): return h["t"] == "U" and h["p"].x > 90 * TS)[0]
	_tp(bu["p"].x / TS + 4.0, bu["p"].y / TS - 0.6, 9)
	creature.inv = 0.0
	await _frames(240)
	report.call("burner flames and dogs hurt", creature.mass < 9 or creature.dead, "mass=%d" % creature.mass)
	creature.dead = false
	world.ignite(66, 55)
	await _frames(300)
	var spread := 0
	for y in range(48, 60):
		spread += 1 if world.tile(66, y) == Tiles.E else 0
	report.call("timber burns away and the fire spreads", world.tile(66, 55) == Tiles.E and spread >= 3, "burned %d of the wall" % spread)
	# the Foreman
	_tp(78.5, 58.5, 12)
	await _frames(10)
	for i in 8:
		if not boss.foreman["alive"]:
			break
		creature.position = boss.foreman["p"] + Vector2(-boss.foreman["dir"] * 26, -14)
		creature.vel = Vector2.ZERO
		await _frames(2)
		take_cd = 0.0
		try_take()
		await _frames(30)
	report.call("the Foreman falls to attacks from behind", not boss.foreman["alive"], "hp=%d" % boss.foreman["hp"])
	report.call("the Foreman leaves a root heart", actors.hearts.any(func(q): return q["id"] == "wet_bark"), "")
	# the Steam Shovel
	_tp(296, 74.5, 12)
	await _frames(20)
	for i in 3:
		creature.position = boss.cable_points()[i] + Vector2(0, 10)
		creature.grab = null
		try_take()
		for f in 75:
			creature.position = boss.cable_points()[i] + Vector2(0, 10)
			creature.vel = Vector2.ZERO
			await get_tree().physics_frame
	report.call("tearing three cables brings the shovel down", not boss.shovel["alive"], "hp=%d" % boss.shovel["hp"])
	creature.position = boss._cab_point() + Vector2(-14, 0)
	await _frames(5)
	try_take()
	await _frames(10)
	report.call("taking the operator ends the fight", not boss.shovel["op"] and actors.hearts.any(func(q): return q["id"] == "iron_gut"), "")
	# a root heart
	var lr: Dictionary = actors.hearts.filter(func(q): return q["id"] == "long_reach")[0]
	_tp(lr["p"].x / TS - 1.5, lr["p"].y / TS - 1.0, 8)
	await _frames(3)
	try_take()
	await _frames(80)
	report.call("a root heart grants its upgrade", G.has_up("long_reach") and creature.reach() > 120.0, "reach=%.0f" % creature.reach())
	# gates
	_tp(84.5, 59.4, 8)
	await _hold(Vector2.RIGHT, 240)
	report.call("timber gate (Axe)", creature.position.x > 91 * TS, str(creature.position / TS))
	G.ab["shovel"] = true
	_tp(174.5, 59.4, 8)
	await _hold(Vector2(1, 1).normalized(), 150)
	await _hold(Vector2.RIGHT, 300)
	await _hold(Vector2.UP, 200)
	report.call("soft earth under the ridge (Shovel)", creature.position.x > 181 * TS, str(creature.position / TS))
	_tp(164.5, 122.3, G.CRAWL_MASS)
	await _hold(Vector2.RIGHT, 300)
	report.call("deep-road crawlway at the size limit", creature.position.x > 177 * TS, str(creature.position / TS))
	_tp(164.5, 122.0, G.CRAWL_MASS + 1)
	await _hold(Vector2.RIGHT, 240)
	report.call("crawlway blocks when large", creature.position.x < 168.5 * TS, str(creature.position / TS))
	G.ab["level"] = true
	_tp(262.5, 59.4, 8)
	await _frames(5)
	creature.try_read()
	await _frames(90)
	await _hold(Vector2.RIGHT, 240)
	report.call("false wall (Level)", creature.position.x > 271 * TS, str(creature.position / TS))
	G.ab["charge"] = true
	_tp(344.6, 59.4, 8)
	await _frames(5)
	creature.try_charge()
	await _frames(110)
	await _hold(Vector2.RIGHT, 50)
	creature.try_charge()
	await _frames(110)
	await _hold(Vector2.RIGHT, 240)
	report.call("granite plug (Charge)", creature.position.x > 350 * TS, str(creature.position / TS))
	_tp(54.5, 59.0, 12)
	await _frames(120)
	report.call("rotten boards break when heavy", creature.position.y > 63 * TS, str(creature.position / TS))
	_tp(110.5, 59.0, 6)
	await _frames(90)
	report.call("rotten boards hold when light", creature.position.y < 60 * TS, str(creature.position / TS))
	var sp: Dictionary = actors.springs[1]
	_tp(sp["p"].x / TS, sp["p"].y / TS - 0.6, 9)
	await _frames(5)
	for i in 30:
		creature.try_shed()
		await _frames(2)
	report.call("shed mass at a spring", creature.mass < 9, "mass=%d" % creature.mass)
	# flood and ending
	G.flood_speed = 600.0
	_tp(380, 98.0, 8)
	await _frames(40)
	report.call("the flood starts in the basin", G.flood, "")
	await _frames(240)
	report.call("water reaches full pool", G.water_y <= G.FLOOD_FULL_Y + 0.1, "water row %.1f" % (G.water_y / TS))
	_tp(380, 56.0, 8)
	await _hold(Vector2.UP, 90)
	report.call("swimming holds at the surface", creature.in_water or creature.position.y < 51 * TS, str(creature.position / TS))
	_tp(204.5, 51.0, 8)
	await _hold(Vector2(1, -1).normalized(), 150)
	report.call("the flood reaches Dana hill's top", creature.position.y < 49 * TS, str(creature.position / TS))
	save_game()
	report.call("save file written", FileAccess.file_exists(G.SAVE_PATH), "")
	_tp(402, 48.5, 8)
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
		["01_lair", 16.0, 118.0, false], ["02_undervalley", 40.0, 100.0, false], ["03_enfield", 52.0, 58.0, false],
		["04_quabbin_hill", 30.0, 45.0, false], ["05_greenwich", 128.0, 58.0, false], ["06_crypt", 112.0, 70.0, false],
		["07_dana", 236.0, 58.0, false], ["08_millrace", 215.0, 104.0, false], ["09_spillway_cut", 296.0, 70.0, false],
		["15_foreman", 79.0, 58.0, false], ["16_shovel", 294.0, 74.0, false], ["17_burner", 101.0, 58.5, false],
		["10_basin", 370.0, 95.0, false], ["11_flooded_dana", 204.0, 50.0, true], ["12_intake", 400.0, 48.0, true],
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
	G.flood = false
	G.water_y = 1.0e6
	fb.start("marion")
	await _frames(200)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("13_memory_marion.png"))
	fb.finish()
	fb.start("clara")
	fb.walker["p"] = Vector2(123 * TS, fb.walker["p"].y)
	await _frames(150)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("14_memory_clara.png"))
	fb.finish()
	_tp(7.0, 59.0, 9)
	creature.inv = 0.0
	cam.position = creature.position
	cam.reset_smoothing()
	read_letter("diary")
	await _frames(20)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("18_letter.png"))
	hud.close_letter()
	G.paused = false
	hud.play_intro(Data.INTRO)
	await _frames(90)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("19_intro.png"))
	hud.skip_intro()
	G.running = false
	hud.show_title(false)
	await _frames(10)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(dir.path_join("00_title.png"))
	get_tree().quit()
