extends Node2D
## The first two boss fights (boss2.gd has the train, the Houndmaster and the Diver).
##
## The Foreman (Enfield sawmill): a giant burner. His front is a wall of fire; get behind
## him and tear at his tanks. He turns toward you, slowly.
## The Steam Shovel (the spillway cut): its bucket sweeps and slams; tear out its three
## cables, then take the operator out of the wrecked cab.

const TS := Tiles.TS

var foreman := {}
var shovel := {}
var t_people: Texture2D
var t_shovel: Texture2D
var pieces := {}


func setup(foreman_p: Vector2, shovel_p: Vector2) -> void:
	t_people = load("res://assets/people.png")
	if ResourceLoader.exists("res://assets/boss_shovel.png"):
		t_shovel = load("res://assets/boss_shovel.png")
		var j = JSON.parse_string(FileAccess.get_file_as_string("res://assets/boss_shovel.json"))
		for k in j:
			var r: Array = j[k]["rect"]
			var pv: Array = j[k]["pivot"]
			pieces[k] = {"rect": Rect2(r[0], r[1], r[2], r[3]), "pivot": Vector2(pv[0], pv[1])}
	foreman = {"p": foreman_p, "home": foreman_p, "hp": 6, "max": 6, "dir": -1, "behind_t": 0.0, "spray": 0.0, "cd": 1.5,
		"stagger": 0.0, "alive": foreman_p != Vector2.ZERO, "active": false, "anim": 0.0, "vx": 0.0}
	shovel = {"base": shovel_p, "hp": 3, "max": 3, "a": 0.4, "a_to": 1.2, "mode": "sweep", "t": 0.0,
		"stick": 0.0, "stick_v": 0.0, "cables": [true, true, true], "alive": shovel_p != Vector2.ZERO, "active": false,
		"op": true, "slam": 0.0, "fall": 0.0}


# ---------------------------------------------------------------- queries
func in_foreman_arena(p: Vector2) -> bool:
	return foreman["alive"] and p.x > 67 * TS and p.x < 84 * TS and p.y > 49 * TS and p.y < 60 * TS


func in_shovel_arena(p: Vector2) -> bool:
	return p.x > 283 * TS and p.x < 313 * TS and p.y > 59 * TS and p.y < 78 * TS


## Things the creature can take here: {"kind", "p", ...} or null.
func target(c: Vector2, reach: float):
	if foreman["alive"] and foreman["active"]:
		var back: Vector2 = foreman["p"] + Vector2(-foreman["dir"] * 10, -26)
		if back.distance_to(c) < reach and _behind(c):
			return {"kind": "boss_f", "p": back}
	if shovel["alive"]:
		var cs := cable_points()
		for i in 3:
			if shovel["cables"][i] and cs[i].distance_to(c) < reach:
				return {"kind": "cable", "i": i, "p": cs[i]}
	elif shovel["op"] and shovel["base"] != Vector2.ZERO:
		var op := _cab_point()
		if op.distance_to(c) < reach:
			return {"kind": "operator", "p": op}
	return null


func _behind(c: Vector2) -> bool:
	return signf(c.x - foreman["p"].x) != float(foreman["dir"])


## The boom's foot. The machine sits at the west end of the cut facing east, its body
## centered on `base` with its bottom on the ground, so the sprite's pivot lands here.
func _foot() -> Vector2:
	if not pieces.has("body"):
		return shovel["base"] + Vector2(34, -40)
	var pc: Dictionary = pieces["body"]
	var sz: Vector2 = pc["rect"].size
	return shovel["base"] + Vector2(pc["pivot"].x - sz.x * 0.5, pc["pivot"].y - sz.y)


func _body_size() -> Vector2:
	return pieces["body"]["rect"].size if pieces.has("body") else Vector2(112, 80)


func _tip() -> Vector2:
	return _foot() + Vector2(0, -93).rotated(shovel["a"])


func bucket_point() -> Vector2:
	var ln: float = 53.0 + shovel["slam"] * 40.0
	return _tip() + Vector2(0, ln).rotated(shovel["stick"])


func _cab_point() -> Vector2:
	return _foot() + Vector2(-20, -22)         # the cab window


func cable_points() -> Array:
	return [_tip(), _foot().lerp(_tip(), 0.55), _foot() + Vector2(-16, -49)]


# ---------------------------------------------------------------- damage
func hit_foreman() -> void:
	foreman["hp"] -= 1
	foreman["stagger"] = 1.3
	foreman["spray"] = 0.0
	G.fx.burst(foreman["p"] + Vector2(-foreman["dir"] * 10, -28), 18, [Color("ffe08a"), Color("c8a040"), Color("6a5a40")], 90.0, 200.0, 1.5, 0.9)
	G.sfx.play("crack")
	G.sfx.play("hurt", 0.2)
	G.shake = maxf(G.shake, 4.0)
	if foreman["hp"] <= 0:
		foreman["alive"] = false
		G.fx.explosion(foreman["p"] + Vector2(0, -24))
		G.fx.explosion(foreman["p"] + Vector2(-foreman["dir"] * 12, -30))
		G.fx.gore(foreman["p"] + Vector2(0, -20))
		G.main.boss_defeated("foreman", foreman["p"])


func cut_cable(i: int) -> void:
	shovel["cables"][i] = false
	shovel["hp"] -= 1
	var p: Vector2 = cable_points()[i]
	G.fx.burst(p, 24, [Color("ffffff"), Color("ffe08a"), Color("9ab0c8")], 140.0, 300.0, 1.0, 0.8)
	G.sfx.play("snap", 0.1)
	G.shake = maxf(G.shake, 6.0)
	shovel["mode"] = "stagger"
	shovel["t"] = 0.0
	if shovel["hp"] <= 0:
		shovel["alive"] = false
		shovel["fall"] = 0.0
		G.fx.explosion(_cab_point())
		G.hud.toast("The boom comes down. The operator is trapped in the cab.")


func take_operator() -> void:
	shovel["op"] = false
	G.fx.gore(_cab_point())
	G.main.boss_defeated("shovel", shovel["base"] + Vector2(-40, -8))


# ---------------------------------------------------------------- update
## Updates both fights. Returns [title, hp, max] for the one you are in, or [].
func physics(delta: float) -> Array:
	var c = G.creature
	if foreman["alive"]:
		_update_foreman(c, delta)
	if shovel["base"] != Vector2.ZERO:
		_update_shovel(c, delta)
	var active := ""
	if foreman["alive"] and in_foreman_arena(c.position):
		if not foreman["active"]:
			G.sfx.play("roar", 0.0)
			G.hud.toast(Data.BOSSES["foreman"]["sub"] + ": \"Light it up, boys. Something's in the mill.\"")
		foreman["active"] = true
		active = "foreman"
	elif shovel["alive"] and in_shovel_arena(c.position):
		if not shovel["active"]:
			G.sfx.play("roar", 0.0)
		shovel["active"] = true
		active = "shovel"
	G.sfx.engine_db = -60.0
	if shovel["alive"]:
		G.sfx.engine_db = clampf(-6.0 - (c.position.distance_to(shovel["base"]) / 22.0), -60.0, -6.0)
	if active == "":
		return []
	var b: Dictionary = foreman if active == "foreman" else shovel
	return [Data.BOSSES[active]["title"], b["hp"], b["max"]]


func _update_foreman(c, delta: float) -> void:
	var f := foreman
	f["anim"] += delta
	if not f["active"] or c.dead:
		return
	f["stagger"] = maxf(0.0, f["stagger"] - delta)
	f["cd"] -= delta
	var dx: float = c.position.x - f["p"].x
	if f["stagger"] > 0.0:
		if f["stagger"] < 0.4:
			f["dir"] = 1 if dx > 0 else -1           # he wheels round after you hit him
		return
	# he turns slowly toward you
	if _behind(c.position):
		f["behind_t"] += delta
		if f["behind_t"] > 1.6:
			f["dir"] = -f["dir"]
			f["behind_t"] = 0.0
	else:
		f["behind_t"] = 0.0
	# walk toward you, keeping his distance
	var want := 0.0
	if absf(dx) > 56.0 and not _behind(c.position):
		want = f["dir"] * 20.0
	var nx: float = f["p"].x + want * delta
	if nx > 69 * TS and nx < 82 * TS:
		f["p"].x = nx
	f["vx"] = want
	# spray
	if f["spray"] > 0.0:
		f["spray"] -= delta
		var o: Vector2 = f["p"] + Vector2(f["dir"] * 22, -22)
		var aim := clampf((c.position.y - o.y) / maxf(40.0, absf(dx)), -0.5, 0.5)
		for k in 2:
			G.actors.flame(o, Vector2(f["dir"], aim + randf_range(-0.12, 0.12)).normalized() * randf_range(190, 240), 0.75)
		if f["spray"] <= 0.0:
			f["cd"] = 1.1
	elif f["cd"] <= 0.0 and not _behind(c.position) and absf(dx) < 170.0:
		f["spray"] = 1.5
		G.sfx.play("flame", 0.1)
	# contact
	if c.position.distance_to(f["p"] + Vector2(0, -24)) < c.r + 16.0:
		G.main.hurt(1, "fire")
		c.vel += Vector2(signf(c.position.x - f["p"].x), -0.6) * 200.0


func _update_shovel(c, delta: float) -> void:
	var s := shovel
	if not s["alive"]:
		s["fall"] = minf(1.0, s["fall"] + delta * 1.2)
		s["a"] = lerpf(s["a"], 1.45, s["fall"] * 0.2)
		s["stick"] = lerpf(s["stick"], 0.3, 0.1)
		s["slam"] = 0.0
		return
	if not s["active"] or c.dead:
		return
	s["t"] += delta
	match s["mode"]:
		"sweep":
			s["a"] = move_toward(s["a"], s["a_to"], delta * 0.9)
			if absf(s["a"] - s["a_to"]) < 0.02:
				s["a_to"] = 0.35 if s["a_to"] > 0.8 else 1.35
				if randf() < 0.55:
					s["mode"] = "aim"
					s["t"] = 0.0
		"aim":
			# swing the bucket over the creature, then drop it
			var want: float = (c.position - _foot()).angle() + PI / 2.0
			s["a"] = move_toward(s["a"], clampf(want, 0.25, 1.4), delta * 1.3)
			if s["t"] > 1.2:
				s["mode"] = "slam"
				s["t"] = 0.0
		"slam":
			s["slam"] = minf(1.0, s["slam"] + delta * 5.0)
			if s["slam"] >= 1.0 and s["t"] < 0.3:
				G.shake = maxf(G.shake, 7.0)
				G.fx.burst(bucket_point(), 16, [Color("6b4e34"), Color("8f7458"), Color("4f5a70")], 120.0, 400.0, 2.0, 1.0)
				G.sfx.play("boom", 0.2)
				s["t"] = 0.3
			if s["t"] > 1.0:
				s["mode"] = "lift"
		"lift":
			s["slam"] = maxf(0.0, s["slam"] - delta * 1.5)
			if s["slam"] <= 0.0:
				s["mode"] = "sweep"
		"stagger":
			s["a"] += sin(s["t"] * 30.0) * 0.01
			s["slam"] = maxf(0.0, s["slam"] - delta * 2.0)
			if s["t"] > 1.0:
				s["mode"] = "sweep"
	# the stick swings like a pendulum behind the boom's motion
	s["stick_v"] += (-s["stick"] * 18.0 - s["stick_v"] * 2.5) * delta
	s["stick"] += s["stick_v"] * delta
	if c.position.distance_to(bucket_point() + Vector2(0, 14)) < c.r + 16.0:
		G.main.hurt(2)
		c.vel += (c.position - bucket_point()).normalized() * 260.0


# ---------------------------------------------------------------- drawing
func _process(_d: float) -> void:
	queue_redraw()


func _piece(name: String, at: Vector2, rot: float = 0.0, flip: bool = false) -> void:
	if not pieces.has(name):
		return
	var pc: Dictionary = pieces[name]
	var r: Rect2 = pc["rect"]
	draw_set_transform(at, rot, Vector2(-1 if flip else 1, 1))
	draw_texture_rect_region(t_shovel, Rect2(-pc["pivot"], r.size), r)
	draw_set_transform(Vector2.ZERO)


func _draw() -> void:
	if G.flashback or t_people == null:
		return
	if foreman["alive"]:
		var f := foreman
		var col := 4
		if f["spray"] > 0.0 or f["stagger"] > 0.0:
			col = 7 if f["spray"] > 0.0 else 6
		elif absf(f["vx"]) > 1.0:
			col = int(f["anim"] * 5.0) % 4
		var flick: bool = f["stagger"] > 0.0 and int(G.time * 20.0) % 2 == 0
		draw_set_transform(f["p"], 0.0, Vector2(f["dir"] * 2, 2))
		draw_texture_rect_region(t_people, Rect2(Vector2(-8, -24), Vector2(16, 24)), Rect2(col * 16, 7 * 24, 16, 24), Color(1.6, 1.2, 1.2) if flick else Color.WHITE)
		draw_set_transform(Vector2.ZERO)
		if f["active"] and _behind(G.creature.position):
			var back: Vector2 = f["p"] + Vector2(-f["dir"] * 12, -30)
			draw_arc(back, 7.0 + sin(G.time * 8.0), 0.0, TAU, 16, Color("ffd36b"), 1.0)
	if shovel["base"] != Vector2.ZERO and t_shovel != null:
		var s := shovel
		var base: Vector2 = s["base"]
		_piece("body" if s["alive"] or not pieces.has("body_wreck") else "body_wreck", _foot(), 0.0, false)
		if s["op"]:
			_piece("operator", _cab_point())
		_piece("boom", _foot(), s["a"])
		var tip := _tip()
		var ln: float = 53.0 + s["slam"] * 40.0
		draw_set_transform(tip, s["stick"], Vector2.ONE)
		if pieces.has("stick"):
			var st: Dictionary = pieces["stick"]
			draw_texture_rect_region(t_shovel, Rect2(-st["pivot"], Vector2(st["rect"].size.x, ln)), st["rect"])
		draw_set_transform(Vector2.ZERO)
		_piece("bucket", bucket_point(), s["stick"] * 0.5)
		var cs := cable_points()
		for i in 3:
			_piece("cable_ok" if s["cables"][i] else "cable_cut", cs[i])
			if s["cables"][i] and s["alive"] and s["active"]:
				draw_arc(cs[i], 8.0 + sin(G.time * 6.0 + i), 0.0, TAU, 16, Color("ffd36b"), 1.0)
		if not s["alive"] and s["op"]:
			draw_arc(_cab_point(), 9.0 + sin(G.time * 6.0), 0.0, TAU, 16, Color("e0566a"), 1.0)

