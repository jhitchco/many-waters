extends Node2D
## People, animals, graves, springs, cellar holes, decor and projectiles.

const TS := Tiles.TS

var people: Array = []
var animals: Array = []
var graves: Array = []
var springs: Array = []
var cps: Array = []
var intake := Vector2.ZERO
var start := Vector2.ZERO
var decor_back: Array = []
var decor_front: Array = []
var projs: Array = []
var hover = null

var t_people: Texture2D
var t_animals: Texture2D
var t_props: Texture2D
var t_decor: Texture2D
var decor_rects := {}


func load_entities() -> void:
	t_people = load("res://assets/people.png")
	t_animals = load("res://assets/animals.png")
	t_props = load("res://assets/props.png")
	t_decor = load("res://assets/decor.png")
	var dj = JSON.parse_string(FileAccess.get_file_as_string("res://assets/decor.json"))
	for k in dj:
		var a: Array = dj[k]
		decor_rects[k] = Rect2(a[0], a[1], a[2], a[3])
	people.clear(); animals.clear(); graves.clear(); springs.clear(); cps.clear()
	var pools := {}
	for k in Data.VOICES:
		pools[k] = Data.VOICES[k].duplicate()
	var gi := 0
	var ents = JSON.parse_string(FileAccess.get_file_as_string("res://data/entities.json"))
	for e in ents:
		var typ: String = e["t"]
		var p := Vector2(int(e["x"]) * TS + 8, int(e["y"]) * TS)
		match typ:
			"R", "B", "K", "E", "G", "P":
				var v: Array = pools[typ].pop_front() if pools[typ].size() > 0 else ["Unknown", "..."]
				people.append({"t": typ, "p": p, "home": p.x, "vy": 0.0, "vx": 0.0, "dir": 1 if randf() < 0.5 else -1,
					"state": "patrol", "alive": true, "cd": 1.0 + randf(), "anim": randf() * 6.0, "alert_t": 0.0,
					"lost": 0.0, "swing": 0.0, "name": v[0], "line": v[1], "id": people.size()})
			"D", "S":
				animals.append({"t": typ, "p": p, "start": p, "home": p.x, "vy": 0.0, "vx": 0.0, "dir": 1, "alive": true,
					"respawn": 0.0, "anim": randf() * 6.0, "scared": 0.0})
			"T":
				var d: Array = Data.DEAD[gi] if gi < Data.DEAD.size() else ["Unknown", "..."]
				graves.append({"p": p, "opened": false, "name": d[0], "line": d[1], "id": gi})
				gi += 1
			"W":
				springs.append({"p": p})
			"C":
				cps.append({"p": p, "on": false})
			"I":
				intake = p
			"@":
				start = p
	decor_back.clear(); decor_front.clear()
	var dl = JSON.parse_string(FileAccess.get_file_as_string("res://data/decor.json"))
	for d in dl:
		var item := {"k": d["k"], "p": Vector2(int(d["x"]) * TS + 8, int(d["y"]) * TS)}
		if d["layer"] == "front":
			decor_front.append(item)
		else:
			decor_back.append(item)


func near_spring(p: Vector2, r: float):
	for s in springs:
		if (s["p"] + Vector2(0, -4)).distance_to(p) < r + 22.0:
			return s
	return null


# ---------------------------------------------------------------- targeting
func _los(a: Vector2, b: Vector2) -> bool:
	var w = G.world
	var d := b - a
	var n := ceili(d.length() / 4.0)
	for i in range(2, n):
		if w.solid_c(w.tile_at(a + d * (float(i) / n))):
			return false
	return true


func find_target(c: Vector2, reach: float):
	var best = null
	var bd := 1.0e9
	for h in people:
		if not h["alive"] or h["state"] == "grabbed":
			continue
		var q: Vector2 = h["p"] + Vector2(0, -12)
		var d := q.distance_to(c)
		if d < reach and d < bd and _los(c, q):
			best = {"kind": "h", "ref": h, "t": 0.0}
			bd = d
	for a in animals:
		if not a["alive"] or a.get("grabbed", false):
			continue
		var q: Vector2 = a["p"] + Vector2(0, -8)
		var d := q.distance_to(c)
		if d < reach and d < bd and _los(c, q):
			best = {"kind": "a", "ref": a, "t": 0.0}
			bd = d
	if best != null:
		return best
	for g in graves:
		if g["opened"]:
			continue
		var q: Vector2 = g["p"] + Vector2(0, -6)
		var d := q.distance_to(c)
		if d < reach and d < bd and _los(c, q):
			best = {"kind": "g", "ref": g, "t": 0.0}
			bd = d
	return best


# ---------------------------------------------------------------- update
func physics(delta: float) -> void:
	var c = G.creature
	for h in people:
		_update_person(h, c, delta)
	for a in animals:
		_update_animal(a, c, delta)
	_update_projs(c, delta)


func _ground(e: Dictionary, delta: float) -> bool:
	var w = G.world
	var p: Vector2 = e["p"]
	var on_g := Tiles.solid_h(w.tile_at(p + Vector2(0, 1)))
	if not on_g:
		e["vy"] = minf(320.0, e["vy"] + 500.0 * delta)
		p.y += e["vy"] * delta
		if Tiles.solid_h(w.tile_at(p)):
			p.y = floorf(p.y / TS) * TS
			e["vy"] = 0.0
		e["p"] = p
	else:
		e["vy"] = 0.0
	return on_g


func _walk(e: Dictionary, want: float, delta: float, turn: bool) -> void:
	var w = G.world
	var p: Vector2 = e["p"]
	if want == 0.0:
		e["vx"] = 0.0
		return
	var m := signf(want)
	var nx := p.x + want * delta
	var wall := Tiles.solid_h(w.tile_at(Vector2(nx + m * 5, p.y - 4))) or Tiles.solid_h(w.tile_at(Vector2(nx + m * 5, p.y - 14)))
	var ground := Tiles.solid_h(w.tile_at(Vector2(nx + m * 5, p.y + 2)))
	if wall or not ground:
		if turn:
			e["dir"] = -e["dir"]
		e["vx"] = 0.0
	else:
		p.x = nx
		e["p"] = p
		e["vx"] = want


func _update_person(h: Dictionary, c, delta: float) -> void:
	if not h["alive"] or h["state"] == "grabbed":
		return
	h["anim"] += delta * (absf(h["vx"]) / 9.0 + 0.4)
	h["swing"] = maxf(0.0, h["swing"] - delta)
	h["alert_t"] = maxf(0.0, h["alert_t"] - delta)
	h["cd"] -= delta
	var p: Vector2 = h["p"]
	var d: Vector2 = c.position - (p + Vector2(0, -12))
	var dist := d.length()
	var warden: bool = h["t"] == "G"
	var rng := 220.0 if warden else 130.0
	var vlim := 140.0 if warden else 90.0
	var sees: bool = not c.dead and not c.in_dirt and not G.ended and dist < rng and absf(d.y) < vlim
	if sees:
		if h["state"] != "alert":
			h["state"] = "alert"
			h["alert_t"] = 1.2
			if not warden:
				G.sfx.play("gasp")
		h["lost"] = 0.0
	elif h["state"] == "alert":
		h["lost"] += delta
		if h["lost"] > 4.0:
			h["state"] = "patrol"
	var want := 0.0
	var on_g := _ground(h, delta)
	if h["state"] == "patrol":
		want = h["dir"] * 14.0
		if absf(p.x - h["home"]) > TS * 3 and signf(p.x - h["home"]) == h["dir"]:
			h["dir"] = -h["dir"]
	else:
		match h["t"]:
			"R":
				h["dir"] = 1 if d.x >= 0 else -1
				if absf(d.x) > 14.0:
					want = h["dir"] * 34.0
				if absf(d.x) < 22.0 + c.r * 0.5 and absf(d.y) < 26.0 + c.r * 0.5 and h["cd"] <= 0.0:
					h["cd"] = 1.7
					h["swing"] = 0.3
					G.sfx.play("swing")
					G.main.hurt(1)
			"G":
				h["dir"] = 1 if d.x >= 0 else -1
				if h["cd"] <= 0.0 and sees:
					h["cd"] = 1.6 + randf() * 0.4
					h["swing"] = 0.25
					_shoot(h, c)
			_:
				want = (-1.0 if d.x >= 0 else 1.0) * 40.0
				h["dir"] = int(signf(want))
				if h["t"] == "E" and h["cd"] <= 0.0 and sees and dist < 170.0:
					h["cd"] = 3.0
					h["swing"] = 0.3
					projs.append({"k": "d", "p": p + Vector2(0, -18), "v": Vector2(clampf(d.x * 1.1, -140, 140), -170), "fuse": 1.6})
	if on_g:
		_walk(h, want, delta, h["state"] == "patrol")


func _update_animal(a: Dictionary, c, delta: float) -> void:
	if not a["alive"]:
		a["respawn"] -= delta
		if a["respawn"] <= 0.0 and a["start"].distance_to(c.position) > 300.0 and not G.flood:
			a["alive"] = true
			a["p"] = a["start"]
		return
	if a.get("grabbed", false):
		return
	a["anim"] += delta * (absf(a["vx"]) / 8.0 + 0.3)
	var on_g := _ground(a, delta)
	var d: Vector2 = c.position - a["p"]
	var want := 0.0
	if not c.dead and not c.in_dirt and d.length() < 110.0:
		a["scared"] = 2.0
	a["scared"] = maxf(0.0, a["scared"] - delta)
	if a["scared"] > 0.0:
		want = (-1.0 if d.x >= 0 else 1.0) * (70.0 if a["t"] == "D" else 32.0)
		a["dir"] = int(signf(want))
	else:
		if absf(a["p"].x - a["home"]) > TS * 4 and signf(a["p"].x - a["home"]) == a["dir"]:
			a["dir"] = -a["dir"]
		want = a["dir"] * 10.0 if fmod(G.time + a["home"], 6.0) < 3.5 else 0.0
	if on_g:
		_walk(a, want, delta, a["scared"] <= 0.0)


func _shoot(h: Dictionary, c) -> void:
	var o: Vector2 = h["p"] + Vector2(h["dir"] * 8, -14)
	var ang: float = (c.position - o).angle() + (randf() - 0.5) * 0.12
	projs.append({"k": "b", "p": o, "v": Vector2.from_angle(ang) * 260.0, "life": 2.0})
	G.fx.burst(o, 4, [Color("ffe08a"), Color("ffb347")], 40.0, 0.0, 1.0, 0.15)
	G.sfx.play("shot")


func _update_projs(c, delta: float) -> void:
	var w = G.world
	for i in range(projs.size() - 1, -1, -1):
		var q: Dictionary = projs[i]
		if q["k"] == "b":
			q["life"] -= delta
			q["p"] += q["v"] * delta
			var wet: bool = G.flood and q["p"].y > G.water_y
			if q["life"] <= 0.0 or Tiles.solid_h(w.tile_at(q["p"])) or wet:
				G.fx.burst(q["p"], 3, [Color("9cdfe0")] if wet else [Color("ffe08a"), Color("777777")], 50.0, 200.0, 1.0, 0.3)
				projs.remove_at(i)
				continue
			if not c.dead and not c.in_dirt and q["p"].distance_to(c.position) < c.r:
				G.main.hurt(1)
				projs.remove_at(i)
		else:
			var v: Vector2 = q["v"]
			v.y += 450.0 * delta
			q["fuse"] -= delta
			var p: Vector2 = q["p"]
			p.x += v.x * delta
			if Tiles.solid_h(w.tile_at(p)):
				p.x -= v.x * delta
				v.x *= -0.4
			p.y += v.y * delta
			if Tiles.solid_h(w.tile_at(p)):
				p.y -= v.y * delta
				v.y *= -0.3
				v.x *= 0.7
			q["p"] = p
			q["v"] = v
			if randf() < 0.6:
				G.fx.burst(p + Vector2(0, -3), 1, [Color("ffe08a"), Color("ff7a30")], 25.0, 0.0, 1.0, 0.2)
			if q["fuse"] <= 0.0:
				G.fx.explosion(p)
				if p.distance_to(c.position) < 40.0 + c.r * 0.5:
					G.main.hurt(1)
				projs.remove_at(i)


# ---------------------------------------------------------------- drawing
func _process(_d: float) -> void:
	queue_redraw()


func _visible(p: Vector2, margin: float) -> bool:
	var vs := get_viewport_rect().size
	var c := G.cam.get_screen_center_position()
	return absf(p.x - c.x) < vs.x * 0.5 + margin and absf(p.y - c.y) < vs.y * 0.5 + margin + 120.0


func _prop(i: int, p: Vector2) -> void:
	draw_texture_rect_region(t_props, Rect2(p + Vector2(-16, -32), Vector2(32, 32)), Rect2((i % 8) * 32, (i / 8) * 32, 32, 32))


func draw_decor_item(ci: CanvasItem, d: Dictionary) -> void:
	var k: String = d["k"]
	var p: Vector2 = d["p"]
	if k.begins_with("p:"):
		var i := int(k.substr(2))
		ci.draw_texture_rect_region(t_props, Rect2(p + Vector2(-16, -32), Vector2(32, 32)), Rect2((i % 8) * 32, (i / 8) * 32, 32, 32))
	elif decor_rects.has(k):
		var r: Rect2 = decor_rects[k]
		ci.draw_texture_rect_region(t_decor, Rect2(p + Vector2(-r.size.x * 0.5, -r.size.y), r.size), r)


func _draw() -> void:
	if t_people == null or G.cam == null:
		return
	for d in decor_back:
		if _visible(d["p"], 120.0):
			draw_decor_item(self, d)
	for k in cps:
		if _visible(k["p"], 32.0):
			_prop(5 if k["on"] else 4, k["p"])
	for s in springs:
		if _visible(s["p"], 32.0):
			_prop(2 + (int(G.time * 3.0) % 2), s["p"])
	for g in graves:
		if not _visible(g["p"], 32.0):
			continue
		var lit: bool = not g["opened"] and (G.reveal_t > 0.0 or (hover != null and hover["ref"] == g))
		if lit:
			draw_circle(g["p"] + Vector2(0, -8), 13.0, Color(1.0, 0.83, 0.42, 0.18))
		_prop(1 if g["opened"] else 0, g["p"])
	for a in animals:
		if a["alive"] and _visible(a["p"], 24.0):
			var row := 0 if a["t"] == "D" else 1
			var col := 2 if a["scared"] > 0.0 and absf(a["vx"]) < 1.0 else int(a["anim"] * 2.0) % 2
			if a.get("grabbed", false):
				col = 2
			draw_set_transform(a["p"], 0.0, Vector2(a["dir"], 1))
			draw_texture_rect_region(t_animals, Rect2(Vector2(-12, -16), Vector2(24, 16)), Rect2(col * 24, row * 16, 24, 16))
			draw_set_transform(Vector2.ZERO)
	for h in people:
		if not h["alive"] or not _visible(h["p"], 24.0):
			continue
		var row: int = Data.TYPE_ROW[h["t"]]
		var col := 4
		if h["state"] == "grabbed":
			col = 6
		elif h["swing"] > 0.0:
			col = 7
		elif absf(h["vx"]) > 1.0:
			col = int(h["anim"] * 4.0) % 4
		elif h["state"] == "alert":
			col = 7 if h["t"] in ["K", "P"] or (h["t"] == "G") else 5
		if hover != null and hover["ref"] == h:
			draw_arc(h["p"] + Vector2(0, -1), 9.0, 0.0, TAU, 16, Color("e0566a"), 1.0)
		if G.reveal_t > 0.0:
			draw_circle(h["p"] + Vector2(0, -12), 12.0, Color(1.0, 0.83, 0.42, 0.12))
		draw_set_transform(h["p"], 0.0, Vector2(h["dir"], 1))
		draw_texture_rect_region(t_people, Rect2(Vector2(-8, -24), Vector2(16, 24)), Rect2(col * 16, row * 24, 16, 24))
		draw_set_transform(Vector2.ZERO)
		if h["alert_t"] > 0.0 and h["state"] != "grabbed":
			draw_rect(Rect2(h["p"] + Vector2(-1, -33), Vector2(2, 5)), Color("f2e6c8"))
			draw_rect(Rect2(h["p"] + Vector2(-1, -27), Vector2(2, 2)), Color("f2e6c8"))
	for q in projs:
		if q["k"] == "b":
			draw_line(q["p"], q["p"] - q["v"] * 0.02, Color("ffe08a"), 1.0)
		else:
			draw_rect(Rect2(q["p"] + Vector2(-2, -6), Vector2(3, 7)), Color("b8302a"))
			draw_rect(Rect2(q["p"] + Vector2(-1, -8), Vector2(1, 2)), Color("ffe08a"))
