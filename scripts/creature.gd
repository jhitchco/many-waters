extends Node2D
## The creature: movement, collision, tentacles and body. Drawn at native pixel scale.

const TS := Tiles.TS
const C_OUT := Color("2a0614")
const C_BASE := Color("8c1c34")
const C_MID := Color("b02a43")
const C_HI := Color("e0566a")
const C_TENT := Color("7a1830")
const C_TIP := Color("4a0e24")
const C_TEETH := Color("f2e6c8")
const C_MOUTH := Color("1a0410")
const C_GOLD := Color("ffd36b")

var vel := Vector2.ZERO
var mass := 5
var r := 7.0
var dr := 7.0
var inv := 0.0
var anchors: Array = []
var grab = null          # {"kind": "h"/"g", "ref": Dictionary, "t": float}
var dead := false
var dead_t := 0.0
var in_dirt := false
var in_water := false
var shed_cd := 0.0
var read_cd := 0.0
var charge = null        # {"p": Vector2, "tx": int, "ty": int, "fuse": float}
var input_override = null   # Vector2 used by the autotest
var fling = null         # {"p": Vector2, "t": float, "whiff": bool}
var fling_cd := 0.0
var momentum := 0.0      # after a fling the body carries its speed for a moment
var last_dir := Vector2.UP


static func radius_for(m: int) -> float:
	return minf(22.0, 4.5 + m * 0.55)


func reset_at(p: Vector2, m: int) -> void:
	position = p
	vel = Vector2.ZERO
	mass = m
	r = radius_for(mass)
	dr = r
	inv = 0.0
	anchors.clear()
	grab = null
	dead = false
	charge = null
	fling = null
	momentum = 0.0


func physics(delta: float) -> void:
	inv = maxf(0.0, inv - delta)
	shed_cd = maxf(0.0, shed_cd - delta)
	read_cd = maxf(0.0, read_cd - delta)
	fling_cd = maxf(0.0, fling_cd - delta)
	momentum = maxf(0.0, momentum - delta)
	if dead:
		return
	var inp: Vector2 = input_override if input_override != null else Input.get_vector("left", "right", "up", "down")
	var w = G.world
	r = radius_for(mass)
	dr = lerpf(dr, r, minf(1.0, delta * 6.0))
	in_dirt = G.ab["shovel"] and w.tile_at(position) == Tiles.DIRT
	in_water = G.flood and position.y > G.water_y
	var cl := near_cling(position, r + 8.0)
	var spd := maxf(70.0, 130.0 - mass * 1.6)
	if in_dirt:
		spd *= 0.95 if G.has_up("old_blood") else 0.55
	if inp != Vector2.ZERO:
		last_dir = inp.normalized()
	if fling != null and not fling["whiff"]:
		fling["t"] += delta
		var to: Vector2 = fling["p"] - position
		vel = vel.lerp(to.normalized() * 380.0, minf(1.0, delta * 14.0))
		if to.length() < r + 5.0 or fling["t"] > 0.7:
			fling = null
			momentum = 0.22
	elif in_water:
		spd *= 1.5 if G.has_up("old_blood") else 1.15
		vel = vel.lerp(inp * spd, minf(1.0, delta * 4.0))
	elif momentum > 0.0:
		vel = vel.lerp(inp * spd, minf(1.0, delta * 1.5))
		if not cl:
			vel.y = minf(380.0, vel.y + 600.0 * delta)
	elif cl or in_dirt:
		vel = vel.lerp(inp * spd, minf(1.0, delta * (8.0 if inp != Vector2.ZERO else 10.0)))
	else:
		vel.y = minf(380.0, vel.y + 600.0 * delta)
		vel.x = lerpf(vel.x, inp.x * spd * 0.8, minf(1.0, delta * 1.5))
	var steps := maxi(1, ceili(maxf(absf(vel.x), absf(vel.y)) * delta / 3.0))
	for s in steps:
		position += vel * delta / steps
		_collide()
	if in_dirt and inp != Vector2.ZERO and randf() < 0.25:
		G.fx.burst(position, 1, [Color("4a3424"), Color("6b4e34")], 30.0, 200.0, 1.0, 0.5)
	_update_anchors(inp, cl)
	if fling != null and fling["whiff"]:
		fling["t"] += delta
		if fling["t"] > 0.18:
			fling = null
	if mass >= G.HEAVY:
		var b = near_tile(Tiles.BOARDS, r + 8.0)
		if b != null:
			w.break_boards(b["x"], b["y"])
	if charge != null:
		charge["fuse"] -= delta
		if randf() < 0.5:
			G.fx.burst(charge["p"], 1, [Color("ffe08a")], 20.0, 60.0, 1.0, 0.3)
		if charge["fuse"] <= 0.0:
			_detonate()


func near_cling(p: Vector2, rad: float) -> bool:
	var w = G.world
	var x0 := floori((p.x - rad) / TS)
	var x1 := floori((p.x + rad) / TS)
	var y0 := floori((p.y - rad) / TS)
	var y1 := floori((p.y + rad) / TS)
	for ty in range(y0, y1 + 1):
		for tx in range(x0, x1 + 1):
			if not Tiles.cling(w.tile(tx, ty)):
				continue
			var q := Vector2(clampf(p.x, tx * TS, tx * TS + TS), clampf(p.y, ty * TS, ty * TS + TS))
			if q.distance_to(p) < rad:
				return true
	return false


## Nearest tile of a type within `rad` of the body edge: {"x","y","p"} or null.
func near_tile(type: int, rad: float):
	var w = G.world
	var best = null
	var bd := 1.0e9
	for ty in range(floori((position.y - rad) / TS), floori((position.y + rad) / TS) + 1):
		for tx in range(floori((position.x - rad) / TS), floori((position.x + rad) / TS) + 1):
			if w.tile(tx, ty) != type:
				continue
			var q := Vector2(clampf(position.x, tx * TS, tx * TS + TS), clampf(position.y, ty * TS, ty * TS + TS))
			var d := q.distance_to(position)
			if d < rad and d < bd:
				bd = d
				best = {"x": tx, "y": ty, "p": q}
	return best


func _collide() -> void:
	var w = G.world
	for _pass in 2:
		var x0 := floori((position.x - r) / TS)
		var x1 := floori((position.x + r) / TS)
		var y0 := floori((position.y - r) / TS)
		var y1 := floori((position.y + r) / TS)
		for ty in range(y0, y1 + 1):
			for tx in range(x0, x1 + 1):
				var v: int = w.tile(tx, ty)
				if not w.solid_c(v):
					continue
				var rx := float(tx * TS)
				var ry := float(ty * TS)
				var q := Vector2(clampf(position.x, rx, rx + TS), clampf(position.y, ry, ry + TS))
				var d := position - q
				var d2 := d.length_squared()
				if d2 >= r * r:
					continue
				if v == Tiles.WOOD and G.ab["axe"]:
					w.smash(tx, ty)
					continue
				if v == Tiles.BOARDS and mass >= G.HEAVY:
					w.break_boards(tx, ty)
					continue
				if d2 > 0.0001:
					var dl := sqrt(d2)
					var n := d / dl
					position += n * (r - dl)
					var vn := vel.dot(n)
					if vn < 0.0:
						vel -= n * vn
				else:
					var l := position.x - rx
					var rr := rx + TS - position.x
					var u := position.y - ry
					var dn := ry + TS - position.y
					var m := minf(minf(l, rr), minf(u, dn))
					if m == u:
						position.y = ry - r
						vel.y = minf(0.0, vel.y)
					elif m == dn:
						position.y = ry + TS + r
						vel.y = maxf(0.0, vel.y)
					elif m == l:
						position.x = rx - r
						vel.x = minf(0.0, vel.x)
					else:
						position.x = rx + TS + r
						vel.x = maxf(0.0, vel.x)


func _update_anchors(inp: Vector2, cl: bool) -> void:
	var w = G.world
	var keep := []
	for a in anchors:
		var p: Vector2 = a["p"]
		if p.distance_to(position) < r + 52.0 and Tiles.cling(w.tile_at(p)):
			keep.append(a)
	anchors = keep
	var want := (5 + mini(4, mass / 5)) if cl else 0
	if anchors.size() < want and randf() < 0.6:
		var moving := inp != Vector2.ZERO
		var base := inp.angle() if moving else randf() * TAU
		var dir := Vector2.from_angle(base + (randf() - 0.5) * (2.4 if moving else TAU))
		var d := r * 0.6
		while d < r + 44.0:
			var p := position + dir * d
			if Tiles.cling(w.tile_at(p)):
				anchors.append({"p": p, "s": randf() * 9.0})
				break
			d += 3.0
	if inp != Vector2.ZERO and anchors.size() >= want and anchors.size() > 0 and randf() < 0.08:
		var fi := 0
		var fd := -1.0e9
		for i in anchors.size():
			var behind: float = -(anchors[i]["p"] - position).dot(inp)
			if behind > fd:
				fd = behind
				fi = i
		anchors.remove_at(fi)
	if not cl and anchors.size() > 0 and randf() < 0.15:
		anchors.pop_front()


## How far a flung tentacle reaches. Bigger bodies reach further.
func reach() -> float:
	return minf(150.0, 90.0 + mass * 2.5) * (1.33 if G.has_up("long_reach") else 1.0)


## Throw a tentacle along `dir` at the first rough surface in reach and pull the body to it.
## With nothing in reach it whips the air and gives a short burst instead.
func try_fling(dir: Vector2) -> void:
	if fling_cd > 0.0 or dead:
		return
	if dir == Vector2.ZERO:
		dir = last_dir
	dir = dir.normalized()
	var w = G.world
	var d := r * 0.6
	var hit = null
	while d < r + reach():
		var p := position + dir * d
		var v: int = w.tile_at(p)
		if Tiles.cling(v):
			hit = p
			break
		if w.solid_c(v):
			break
		d += 3.0
	if hit != null:
		fling = {"p": hit, "t": 0.0, "whiff": false}
		fling_cd = 0.15 if G.has_up("quick_tendons") else 0.3
		anchors.clear()
		G.sfx.play("swing", 0.2)
		G.fx.burst(hit, 4, [Color("8c1c34"), Color("4a0e24")], 30.0, 200.0, 1.0, 0.4)
	else:
		fling = {"p": position + dir * (r + reach() * 0.7), "t": 0.0, "whiff": true}
		vel += dir * 170.0
		momentum = 0.25
		fling_cd = 0.25 if G.has_up("quick_tendons") else 0.5
		G.sfx.play("swing", 0.3)


func try_shed() -> bool:
	var s = G.actors.near_spring(position, r)
	if s == null or shed_cd > 0.0 or mass <= 2:
		return false
	mass -= 1
	shed_cd = 0.35
	G.fx.burst(s["p"] + Vector2(0, -3), 10, [Color("3fb8c4"), Color("8a6a46"), Color("bff3f0")], 60.0, 300.0, 1.5, 0.9)
	G.fx.float_text(position + Vector2(0, -r - 6), "-1 mass", Color("9cdfe0"))
	G.sfx.play("splash")
	return true


func try_read() -> void:
	if not G.ab["level"] or read_cd > 0.0:
		return
	read_cd = 1.6
	G.reveal_t = 4.0
	G.fx.pulse(position)
	G.sfx.play("chime")
	var w = G.world
	var tx := floori(position.x / TS)
	var ty := floori(position.y / TS)
	for y in range(ty - 14, ty + 15):
		for x in range(tx - 14, tx + 15):
			if w.tile(x, y) == Tiles.FALSE:
				var d := Vector2(x * TS + 8, y * TS + 8).distance_to(position)
				if d < 220.0:
					G.fx.reveal_later(x, y, d / 320.0)


func try_charge() -> void:
	if not G.ab["charge"] or charge != null:
		return
	var n = near_tile(Tiles.GRAN, r + 26.0)
	if n == null:
		return
	charge = {"p": n["p"], "tx": n["x"], "ty": n["y"], "fuse": 1.4}
	G.sfx.play("tick")


func _detonate() -> void:
	var w = G.world
	var cx: int = charge["tx"]
	var cy: int = charge["ty"]
	for y in range(cy - 3, cy + 4):
		for x in range(cx - 3, cx + 4):
			if w.tile(x, y) == Tiles.GRAN and Vector2(x - cx, y - cy).length() <= 2.7:
				w.set_tile(x, y, Tiles.E)
				G.fx.burst(Vector2(x * TS + 8, y * TS + 8), 8, [Color("b7a9a6"), Color("e2d6cf"), Color("6d6362")], 140.0, 450.0, 2.0, 1.2)
	G.fx.explosion(charge["p"])
	G.shake = maxf(G.shake, 6.0)
	charge = null


# ---------------------------------------------------------------- drawing
func _process(_d: float) -> void:
	queue_redraw()


func _tentacle(a: Vector2, b: Vector2, w: float, seed: float) -> void:
	var d := b - a
	var len := maxf(1.0, d.length())
	var n := Vector2(-d.y, d.x) / len
	var wob := sin(G.time * 3.0 + seed * 1.7) * minf(9.0, len * 0.2)
	var c := (a + b) * 0.5 + n * wob
	var prev := a
	var N := 8
	for k in range(1, N + 1):
		var s := float(k) / N
		var q := a * (1.0 - s) * (1.0 - s) + c * 2.0 * (1.0 - s) * s + b * s * s
		var width := maxf(1.0, round(w * (1.0 - s * 0.8)))
		draw_line(prev, q, C_OUT, width + 2.0)
		draw_line(prev, q, C_TENT if s < 0.6 else C_TIP, width)
		prev = q


func _draw() -> void:
	if dead or G.flashback:
		return
	var t := G.time
	var rr := dr
	if inv > 0.0 and int(t * 18.0) % 2 == 0:
		modulate.a = 0.5
	elif in_dirt:
		modulate.a = 0.45
	else:
		modulate.a = 1.0
	var bal: float = float(G.kept) / maxf(1.0, float(G.kept + G.taken))
	if G.kept > 0:
		draw_circle(Vector2.ZERO, rr * 2.0, Color(1.0, 0.83, 0.42, 0.06 + bal * 0.08))
	for a in anchors:
		_tentacle(Vector2.ZERO, a["p"] - position, rr * 0.34, a["s"])
	var nf := 5 if anchors.size() < 3 else 2
	for i in nf:
		var ang := float(i) / nf * TAU + t * 0.6 + sin(t * 1.3 + i) * 0.6
		var ln := rr * 1.5 + sin(t * 2.0 + i) * rr * 0.3
		_tentacle(Vector2.ZERO, Vector2.from_angle(ang) * ln + Vector2(0, 0 if in_water else rr * 0.3), rr * 0.26, i + 10.0)
	if fling != null:
		var fp: Vector2 = fling["p"]
		if fling["whiff"]:
			fp = position.lerp(fp, clampf(fling["t"] / 0.09, 0.0, 1.0))
		_tentacle(Vector2.ZERO, fp - position, rr * 0.42, 77.0)
	if grab != null:
		var ref: Dictionary = grab["ref"]
		var tp: Vector2 = ref["p"] + (Vector2(0, -12) if grab["kind"] == "h" else Vector2(0, -4))
		_tentacle(Vector2.ZERO, tp - position, rr * 0.4, 99.0)
	# body: outline pass, base, mid, highlights
	var lobes := []
	for i in 9:
		var a := float(i) / 9.0 * TAU + t * 0.25
		var off := rr * 0.38 * (0.8 + 0.2 * sin(t * 1.7 + i))
		lobes.append([Vector2.from_angle(a) * off, rr * (0.55 + 0.12 * sin(t * 2.3 + i * 1.3))])
	for l in lobes:
		draw_circle(l[0], l[1] + 1.0, C_OUT)
	for l in lobes:
		draw_circle(l[0], l[1], C_BASE)
	for l in lobes:
		draw_circle(l[0] + Vector2(-0.25, -0.25) * l[1], l[1] * 0.6, C_MID)
	for l in lobes:
		draw_circle(l[0] + Vector2(-0.4, -0.45) * l[1], maxf(1.0, l[1] * 0.22), C_HI)
	for i in 3:
		var a := i * 2.1 + t * 0.2
		var m := Vector2.from_angle(a) * rr * 0.36
		var open := 1.0 + 0.5 * sin(t * 4.0 + i)
		draw_set_transform(m, a, Vector2(1.0, 0.55 * open))
		draw_circle(Vector2.ZERO, maxf(1.5, rr * 0.2), C_MOUTH)
		draw_set_transform(Vector2.ZERO)
		for k in [-1, 0, 1]:
			var tp: Vector2 = m + Vector2.from_angle(a + PI / 2) * k * rr * 0.09
			draw_rect(Rect2(tp.round(), Vector2.ONE), C_TEETH)
	var motes := mini(24, G.kept)
	for j in motes:
		var a := j * 2.4 + t * 0.5 * (1.0 if j % 2 == 0 else -1.0)
		var rad := rr * 0.2 + (j % 4) * rr * 0.09
		draw_rect(Rect2((Vector2.from_angle(a) * rad).round(), Vector2.ONE), C_GOLD)
	if charge != null:
		var cp: Vector2 = charge["p"] - position
		draw_rect(Rect2(cp + Vector2(-2, -5), Vector2(4, 8)), Color("b8302a"))
		draw_rect(Rect2(cp + Vector2(-1, -7), Vector2(2, 2)), Color("ffe08a") if int(t * 8.0) % 2 == 0 else Color("5a2a10"))
