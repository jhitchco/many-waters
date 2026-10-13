extends Node2D
## The later boss fights.
##
## The Last Train (the Rabbit Run trestle over Dana): a locomotive runs the trestle end to
## end. Tear down the three supports under the weak span and it goes over.
## The Houndmaster (the Dana kennels): whistles up tracker dogs and cracks a whip. His dogs
## drag you off him; take them first, then him, three times.
## The Diver (drowned Prescott, after the flood): walks the bottom in lead boots and fires a
## harpoon gun. Tear his air hose at its three brass couplings, then take him as he rises.

const TS := Tiles.TS
const DECK_Y := 44.0 * 16.0          # top of the trestle deck: the rail
const POST_TOP := 45.0 * 16.0
const POST_BOTTOM := 60.0 * 16.0
const SPAN := [241, 249]             # tiles of deck that fall when their supports go
const POSTS := [242, 245, 248]

var train := {}
var hound := {}
var diver := {}
var harpoons: Array = []
var t_people: Texture2D
var t_train: Texture2D
var pieces := {}


func setup(train_p: Vector2, hound_p: Vector2, diver_p: Vector2) -> void:
	t_people = load("res://assets/people.png")
	pieces.clear()
	t_train = null
	if ResourceLoader.exists("res://assets/boss_train.png") and FileAccess.file_exists("res://assets/boss_train.json"):
		t_train = load("res://assets/boss_train.png")
		var j = JSON.parse_string(FileAccess.get_file_as_string("res://assets/boss_train.json"))
		for k in j:
			var r: Array = j[k]["rect"]
			var pv: Array = j[k]["pivot"]
			pieces[k] = {"rect": Rect2(r[0], r[1], r[2], r[3]), "pivot": Vector2(pv[0], pv[1])}
	train = {"x": train_p.x, "x0": 236.0 * TS, "x1": 262.0 * TS, "dir": 1, "wait": 1.0, "alive": train_p != Vector2.ZERO,
		"posts": [true, true, true], "hp": 3, "max": 3, "active": false, "fall": false, "y": DECK_Y, "vy": 0.0, "rot": 0.0,
		"crash_t": 0.0, "wheel": 0.0, "smoke": 0.0}
	hound = {"p": hound_p, "home": hound_p.x, "hp": 3, "max": 3, "dir": -1, "whistle": 1.0, "whip": 0.0, "swing": 0.0,
		"stun": 0.0, "alive": hound_p != Vector2.ZERO, "active": false, "anim": 0.0, "vx": 0.0, "pack": []}
	diver = {"p": diver_p, "home": diver_p.x, "hp": 3, "max": 3, "valves": [true, true, true], "alive": diver_p != Vector2.ZERO,
		"active": false, "cd": 2.0, "dir": -1, "rise": 0.0, "anim": 0.0, "here": false, "fire": 0.0}
	harpoons.clear()


# ---------------------------------------------------------------- where things are
func in_train_zone(p: Vector2) -> bool:
	return train["alive"] and p.x > 231 * TS and p.x < 279 * TS and p.y > 30 * TS and p.y < 61 * TS


func _post_x(i: int) -> float:
	return POSTS[i] * TS + 8.0


func diver_present() -> bool:
	return diver["alive"] and G.flood and G.water_y < 90.0 * TS


func _helmet() -> Vector2:
	return diver["p"] + Vector2(0, -34 - diver["rise"])


func _boat() -> Vector2:
	return Vector2(diver["home"] + 40.0, G.water_y)


func _hose(t: float) -> Vector2:
	var a := _helmet()
	var b := _boat() + Vector2(18, -1)          # the hose stub over the boat's gunwale
	var c := Vector2((a.x + b.x) * 0.5 + 30.0 * sin(G.time * 0.7), (a.y + b.y) * 0.5)
	return a.lerp(c, t).lerp(c.lerp(b, t), t)


func valve_points() -> Array:
	return [_hose(0.3), _hose(0.55), _hose(0.8)]


## Things to take: {"kind", "i"?, "p"} or null.
func target(c: Vector2, reach: float):
	if train["alive"] and not train["fall"]:
		for i in 3:
			if train["posts"][i]:
				var q := Vector2(_post_x(i), clampf(c.y, POST_TOP, POST_BOTTOM - 8.0))
				if q.distance_to(c) < reach:
					return {"kind": "post", "i": i, "p": q}
	if hound["alive"] and hound["active"]:
		var hp: Vector2 = hound["p"] + Vector2(0, -16)
		if hp.distance_to(c) < reach:
			return {"kind": "hound", "p": hp}
	if diver_present():
		if diver["hp"] > 0:
			var vs := valve_points()
			for i in 3:
				if diver["valves"][i] and vs[i].distance_to(c) < reach:
					return {"kind": "valve", "i": i, "p": vs[i]}
		elif _helmet().distance_to(c) < reach:
			return {"kind": "diver", "p": _helmet()}
	return null


func grab_point(kind: String, i: int, c: Vector2) -> Vector2:
	if kind == "post":
		return Vector2(_post_x(i), clampf(c.y, POST_TOP, POST_BOTTOM - 8.0))
	return valve_points()[i]


func grab_valid(kind: String, i: int) -> bool:
	if kind == "post":
		return train["alive"] and train["posts"][i] and not train["fall"]
	return diver_present() and diver["valves"][i]


func grab_time(kind: String) -> float:
	return 1.2 if kind == "post" else 0.9


func grab_finish(kind: String, i: int) -> void:
	if kind == "post":
		train["posts"][i] = false
		train["hp"] -= 1
		G.fx.burst(Vector2(_post_x(i), (POST_TOP + POST_BOTTOM) * 0.5), 26, [Color("6b4a2c"), Color("a0703c"), Color("3d2918")], 140.0, 400.0, 2.0, 1.2)
		G.sfx.play("crack", 0.0)
		G.shake = maxf(G.shake, 5.0)
		if train["hp"] <= 0:
			G.hud.toast("The weak span sags. The train is coming.")
	else:
		diver["valves"][i] = false
		diver["hp"] -= 1
		G.fx.burst(valve_points()[i], 30, [Color(0.85, 0.95, 1.0, 0.8), Color(0.6, 0.85, 0.95, 0.6)], 60.0, -120.0, 1.5, 1.6)
		G.sfx.play("bubbles", 0.05)
		if diver["hp"] <= 0:
			G.hud.toast("His air is gone. He kicks for the surface.")


func hit_hound() -> void:
	var c = G.creature
	var alive_dogs := 0
	for d in hound["pack"]:
		if d["alive"]:
			alive_dogs += 1
	if alive_dogs > 0:
		c.vel += Vector2(signf(c.position.x - hound["p"].x), -0.8) * 260.0
		G.hud.toast("His dogs drag you off him.")
		G.sfx.play("bark", 0.1)
		return
	hound["hp"] -= 1
	hound["stun"] = 2.0
	hound["whistle"] = 0.3
	G.fx.gore(hound["p"] + Vector2(0, -14))
	G.sfx.play("squelch")
	G.sfx.play("scream", 0.1)
	if hound["hp"] <= 0:
		hound["alive"] = false
		G.main.boss_defeated("houndmaster", hound["p"])
	else:
		c.vel += Vector2(signf(c.position.x - hound["p"].x), -0.5) * 180.0


func take_diver() -> void:
	diver["alive"] = false
	G.fx.gore(_helmet())
	G.main.boss_defeated("diver", Vector2(diver["p"].x, diver["p"].y))


# ---------------------------------------------------------------- update
## Returns [title, hp, max] for the fight you are in, or [].
func physics(delta: float) -> Array:
	var c = G.creature
	var out := []
	if train["alive"]:
		_update_train(c, delta)
		if in_train_zone(c.position):
			if not train["active"]:
				G.sfx.play("whistle", 0.0)
				G.hud.toast(Data.BOSSES["train"]["sub"] + ". Full steam.")
			train["active"] = true
			out = [Data.BOSSES["train"]["title"], train["hp"], train["max"]]
		else:
			train["active"] = false
	if hound["alive"]:
		var near: bool = (hound["p"] as Vector2).distance_to(c.position) < 230.0 and absf(hound["p"].y - c.position.y) < 140.0
		if near and not hound["active"]:
			G.sfx.play("whistle", 0.3)
			G.hud.toast(Data.BOSSES["houndmaster"]["sub"] + ": \"Find it, girls.\"")
		hound["active"] = hound["active"] or near
		if hound["active"]:
			_update_hound(c, delta)
			if near:
				out = [Data.BOSSES["houndmaster"]["title"], hound["hp"], hound["max"]]
	if diver_present():
		if not diver["here"]:
			diver["here"] = true
			G.hud.toast("A boat on the new lake. A hose goes down into drowned Prescott.")
		var near_d: bool = _helmet().distance_to(c.position) < 280.0
		diver["active"] = near_d and c.in_water
		_update_diver(c, delta)
		if near_d:
			out = [Data.BOSSES["diver"]["title"], diver["hp"], diver["max"]]
	_update_harpoons(c, delta)
	var eng := -60.0
	if train["alive"]:
		eng = clampf(-6.0 - Vector2(train["x"], DECK_Y).distance_to(c.position) / 22.0, -60.0, -6.0)
	G.sfx.engine_db = maxf(G.sfx.engine_db, eng)
	return out


func any_active(p: Vector2) -> bool:
	return in_train_zone(p) or (hound["alive"] and hound["active"] and (hound["p"] as Vector2).distance_to(p) < 260.0) \
		or (diver_present() and _helmet().distance_to(p) < 280.0)


func _update_train(c, delta: float) -> void:
	var t := train
	t["smoke"] -= delta
	if t["fall"]:
		t["vy"] += 500.0 * delta
		t["y"] += t["vy"] * delta
		t["x"] += t["dir"] * 40.0 * delta
		t["rot"] += t["dir"] * delta * 0.9
		if t["y"] > POST_BOTTOM - 10.0 and t["crash_t"] == 0.0:
			t["crash_t"] = 0.01
			for k in 3:
				G.fx.explosion(Vector2(t["x"] + (k - 1) * 30.0, POST_BOTTOM - 16.0))
			G.shake = 14.0
			G.sfx.play("crash", 0.0)
		if t["crash_t"] > 0.0:
			t["crash_t"] += delta
			t["y"] = minf(t["y"], POST_BOTTOM - 10.0)
			if t["crash_t"] > 1.2:
				t["alive"] = false
				G.main.boss_defeated("train", Vector2(t["x"], POST_BOTTOM))
		return
	if not t["active"]:
		return
	if t["wait"] > 0.0:
		t["wait"] -= delta
	else:
		var spd := 120.0
		t["x"] += t["dir"] * spd * delta
		t["wheel"] += t["dir"] * spd * delta / 9.0
		if (t["dir"] > 0 and t["x"] >= t["x1"]) or (t["dir"] < 0 and t["x"] <= t["x0"]):
			t["x"] = clampf(t["x"], t["x0"], t["x1"])
			t["dir"] = -t["dir"]
			t["wait"] = 1.8
			G.sfx.play("whistle", 0.05)
	if t["smoke"] <= 0.0:
		t["smoke"] = 0.12
		G.fx.burst(Vector2(t["x"] + t["dir"] * 31.0, DECK_Y - 57.0), 1, [Color(0.35, 0.33, 0.4, 0.7), Color(0.5, 0.48, 0.55, 0.5)], 20.0, -40.0, 3.0, 2.0)
	# the span goes when its supports are gone and the train's weight comes onto it
	var span_x0: float = SPAN[0] * TS
	var span_x1: float = (SPAN[1] + 1) * TS
	if t["hp"] <= 0 and t["x"] > span_x0 and t["x"] < span_x1:
		t["fall"] = true
		for x in range(SPAN[0], SPAN[1] + 1):
			G.world.set_tile(x, 44, Tiles.E)
			G.fx.burst(Vector2(x * TS + 8, DECK_Y + 8), 6, [Color("6b4a2c"), Color("3d2918")], 120.0, 500.0, 2.0, 1.4)
		G.sfx.play("crack", 0.0)
		return
	# contact
	var box := Rect2(t["x"] - 50.0 - (40.0 if t["dir"] > 0 else 0.0), DECK_Y - 54.0, 140.0, 54.0)
	if box.has_point(c.position) or box.grow(c.r).has_point(c.position):
		G.main.hurt(2)
		c.vel = Vector2(t["dir"] * 340.0, -220.0)


func _update_hound(c, delta: float) -> void:
	var h := hound
	h["anim"] += delta
	h["swing"] = maxf(0.0, h["swing"] - delta)
	h["whip"] -= delta
	h["whistle"] -= delta
	if h["stun"] > 0.0:
		h["stun"] -= delta
		return
	var d: Vector2 = c.position - (h["p"] + Vector2(0, -16))
	h["dir"] = 1 if d.x >= 0 else -1
	var alive_dogs := 0
	for dog in h["pack"]:
		if dog["alive"]:
			alive_dogs += 1
	if h["whistle"] <= 0.0 and alive_dogs < 3:
		h["whistle"] = 6.5
		G.sfx.play("whistle", 0.4)
		for k in 2:
			var dog := {"t": "H", "p": h["p"] + Vector2(randf_range(-20, 20), 0), "start": h["p"], "home": h["p"].x, "vy": 0.0, "vx": 0.0,
				"dir": h["dir"], "alive": true, "respawn": 1.0e9, "anim": randf() * 6.0, "scared": 0.0, "pack": true}
			G.actors.animals.append(dog)
			h["pack"].append(dog)
	var want := 0.0
	if absf(d.x) > 70.0:
		want = h["dir"] * 30.0
	elif absf(d.x) < 40.0:
		want = -h["dir"] * 22.0
	var nx: float = h["p"].x + want * delta
	if absf(nx - h["home"]) < 9.0 * TS:
		h["p"].x = nx
	h["vx"] = want
	if h["whip"] <= 0.0 and absf(d.x) < 64.0 and absf(d.y) < 36.0:
		h["whip"] = 1.4
		h["swing"] = 0.3
		G.sfx.play("whip", 0.1)
		G.main.hurt(1)
		c.vel += Vector2(h["dir"], -0.4) * 160.0


func _update_diver(c, delta: float) -> void:
	var dv := diver
	dv["anim"] += delta
	dv["fire"] = maxf(0.0, dv["fire"] - delta)
	if dv["hp"] <= 0:
		dv["rise"] = minf(220.0, dv["rise"] + 18.0 * delta)
		if randf() < 0.2:
			G.fx.burst(_helmet(), 1, [Color(0.85, 0.95, 1.0, 0.7)], 10.0, -60.0, 1.0, 1.5)
		return
	if randf() < 0.08:
		G.fx.burst(_helmet() + Vector2(0, -8), 1, [Color(0.85, 0.95, 1.0, 0.6)], 8.0, -50.0, 1.0, 2.0)
	if not dv["active"]:
		return
	var d: Vector2 = c.position - _helmet()
	dv["dir"] = 1 if d.x >= 0 else -1
	var nx: float = dv["p"].x + dv["dir"] * 14.0 * delta
	if absf(nx - dv["home"]) < 12.0 * TS and absf(d.x) > 30.0:
		dv["p"].x = nx
	dv["cd"] -= delta
	if dv["cd"] <= 0.0:
		dv["cd"] = 2.3
		dv["fire"] = 0.3
		var o: Vector2 = _helmet() + Vector2(dv["dir"] * 12, 10)
		harpoons.append({"p": o, "v": (c.position - o).normalized() * 230.0, "life": 2.2})
		G.sfx.play("harpoon", 0.1)


func _update_harpoons(c, delta: float) -> void:
	for i in range(harpoons.size() - 1, -1, -1):
		var hp: Dictionary = harpoons[i]
		hp["life"] -= delta
		hp["p"] += hp["v"] * delta
		if hp["life"] <= 0.0 or Tiles.solid_h(G.world.tile_at(hp["p"])):
			harpoons.remove_at(i)
			continue
		if not c.dead and hp["p"].distance_to(c.position) < c.r + 2.0:
			G.main.hurt(1)
			harpoons.remove_at(i)


# ---------------------------------------------------------------- drawing
func _process(_d: float) -> void:
	queue_redraw()


func _piece(name: String, at: Vector2, rot: float = 0.0, flip: bool = false, mod: Color = Color.WHITE) -> bool:
	if t_train == null or not pieces.has(name):
		return false
	var pc: Dictionary = pieces[name]
	var r: Rect2 = pc["rect"]
	draw_set_transform(at, rot, Vector2(-1 if flip else 1, 1))
	draw_texture_rect_region(t_train, Rect2(-pc["pivot"], r.size), r, mod)
	draw_set_transform(Vector2.ZERO)
	return true


func _post(x: float, torn: bool) -> void:
	var y := POST_TOP
	while y < POST_BOTTOM:
		var seg := "post_torn" if torn and y > POST_TOP + 60.0 and y < POST_TOP + 120.0 else "post"
		if not _piece(seg, Vector2(x, y)):
			draw_rect(Rect2(x - 3, y, 6, 48), Color("4a3020"))
		y += 48.0


func _draw() -> void:
	if G.flashback or t_people == null:
		return
	var c = G.creature
	# the trestle bents under the deck
	for tx in range(234, 266, 4):
		if tx >= SPAN[0] and tx <= SPAN[1]:
			continue
		if G.world.tile(tx, 44) == Tiles.TRESTLE:
			_post(tx * TS + 8.0, false)
	if train["alive"] or train["fall"]:
		for i in 3:
			if not train["fall"]:
				_post(_post_x(i), not train["posts"][i])
				if train["posts"][i] and train["active"]:
					draw_arc(Vector2(_post_x(i), clampf(c.position.y, POST_TOP + 8.0, POST_BOTTOM - 16.0)), 8.0 + sin(G.time * 6.0 + i), 0.0, TAU, 16, Color("ffd36b"), 1.0)
	if train["alive"]:
		var t := train
		var at := Vector2(t["x"], t["y"])
		var flip: bool = t["dir"] < 0
		var tender_at := at + Vector2(-t["dir"] * 72.0, 0).rotated(t["rot"])
		if not _piece("tender", tender_at, t["rot"], flip):
			draw_rect(Rect2(tender_at + Vector2(-22, -40), Vector2(44, 40)), Color("2a2a30"))
		if not _piece("loco", at, t["rot"], flip):
			draw_rect(Rect2(at + Vector2(-48, -56), Vector2(96, 56)), Color("1a1a20"))
		for off in [-12.0, 8.0]:             # drive wheel centers on the loco sprite, from its pivot
			var wp: Vector2 = at + Vector2(off * (-1.0 if flip else 1.0), -9).rotated(t["rot"])
			_piece("wheel", wp, t["wheel"] * (-1.0 if flip else 1.0))
	if hound["alive"]:
		var h := hound
		var col := 4
		if h["stun"] > 0.0:
			col = 6
		elif h["swing"] > 0.0:
			col = 7
		elif h["whistle"] > 6.0:
			col = 5
		elif absf(h["vx"]) > 1.0:
			col = int(h["anim"] * 6.0) % 4
		draw_set_transform(h["p"], 0.0, Vector2(h["dir"] * 1.5, 1.5))
		draw_texture_rect_region(t_people, Rect2(Vector2(-8, -24), Vector2(16, 24)), Rect2(col * 16, 9 * 24, 16, 24))
		draw_set_transform(Vector2.ZERO)
		if h["swing"] > 0.0:
			draw_line(h["p"] + Vector2(h["dir"] * 10, -20), h["p"] + Vector2(h["dir"] * 64, -16 + sin(G.time * 40.0) * 4.0), Color("3a2a1c"), 1.0)
	if diver_present():
		var dv := diver
		var pts := PackedVector2Array()
		for k in 21:
			pts.append(_hose(k / 20.0))
		draw_polyline(pts, Color("1a1410"), 3.0)
		draw_polyline(pts, Color("7a6a50"), 1.0)
		var vs := valve_points()
		for i in 3:
			if not _piece("hose_valve" if dv["valves"][i] else "hose_cut", vs[i]):
				draw_circle(vs[i], 4.0, Color("c8a040") if dv["valves"][i] else Color("555555"))
			if dv["valves"][i] and dv["active"]:
				draw_arc(vs[i], 8.0 + sin(G.time * 6.0 + i), 0.0, TAU, 16, Color("ffd36b"), 1.0)
		_piece("rowboat", _boat() + Vector2(0, 2 + sin(G.time * 1.5) * 1.5))
		var col := 4
		if dv["hp"] <= 0:
			col = 6
		elif dv["fire"] > 0.0:
			col = 7
		elif dv["active"]:
			col = int(dv["anim"] * 3.0) % 4
		draw_set_transform(dv["p"] + Vector2(0, -dv["rise"]), 0.0, Vector2(dv["dir"] * 1.5, 1.5))
		draw_texture_rect_region(t_people, Rect2(Vector2(-8, -24), Vector2(16, 24)), Rect2(col * 16, 8 * 24, 16, 24))
		draw_set_transform(Vector2.ZERO)
		if dv["hp"] <= 0:
			draw_arc(_helmet(), 10.0 + sin(G.time * 6.0), 0.0, TAU, 16, Color("e0566a"), 1.0)
	for hp in harpoons:
		var hv: Vector2 = hp["v"]
		draw_line(hp["p"], hp["p"] - hv.normalized() * 12.0, Color("c8ccd8"), 1.0)
		draw_line(hp["p"] - hv.normalized() * 12.0, hp["p"] - hv.normalized() * 30.0, Color(0.6, 0.6, 0.6, 0.5), 1.0)
