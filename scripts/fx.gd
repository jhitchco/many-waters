extends Node2D
## Particles, blood, survey pulses, delayed reveals of false stone, floating text.

var parts: Array = []
var splats: Array = []
var pulses: Array = []
var reveals: Array = []
var floats: Array = []      # drawn by the HUD at screen resolution


func clear() -> void:
	parts.clear(); splats.clear(); pulses.clear(); reveals.clear(); floats.clear()


func burst(p: Vector2, n: int, cols: Array, spd: float, grav: float = 300.0, size: float = 1.0, life: float = 1.0) -> void:
	for i in n:
		if parts.size() > 900:
			return
		var a := randf() * TAU
		var s := spd * (0.3 + randf() * 0.7)
		parts.append({"p": p, "v": Vector2(cos(a) * s, sin(a) * s - spd * 0.3), "g": grav,
			"life": life * (0.5 + randf() * 0.5), "max": life, "c": cols[randi() % cols.size()], "sz": maxf(1.0, round(size * (0.6 + randf() * 0.8)))})


func gore(p: Vector2) -> void:
	burst(p, 40, [Color("8c1c34"), Color("c42a3f"), Color("4a0e24"), Color("f2e6c8")], 140.0, 380.0, 2.0, 1.3)
	for i in 8:
		splats.append({"p": (p + Vector2(randf_range(-26, 26), randf_range(-10, 8))).round(), "s": Vector2(randi_range(2, 5), randi_range(1, 2))})
	if splats.size() > 300:
		splats = splats.slice(splats.size() - 300)


func explosion(p: Vector2) -> void:
	burst(p, 34, [Color("ffe08a"), Color("ff7a30"), Color("c0401a"), Color("5a5560"), Color("2e2a33")], 170.0, 160.0, 2.0, 1.0)
	G.shake = maxf(G.shake, 6.0)
	G.sfx.play("boom")


func pulse(p: Vector2) -> void:
	pulses.append({"p": p, "r": 0.0})


func reveal_later(x: int, y: int, t: float) -> void:
	for r in reveals:
		if r["x"] == x and r["y"] == y:
			return
	reveals.append({"x": x, "y": y, "t": t})


func float_text(p: Vector2, s: String, c: Color) -> void:
	floats.append({"p": p, "s": s, "c": c, "t": 1.4})


func update(delta: float) -> void:
	var w = G.world
	for i in range(parts.size() - 1, -1, -1):
		var q: Dictionary = parts[i]
		q["life"] -= delta
		if q["life"] <= 0.0:
			parts.remove_at(i)
			continue
		var v: Vector2 = q["v"]
		v.y += q["g"] * delta
		var p: Vector2 = q["p"] + v * delta
		if q["g"] > 0.0 and Tiles.solid_h(w.tile_at(p)):
			v = Vector2(v.x * 0.3, 0.0)
			q["g"] = 0.0
			p = q["p"]
		q["p"] = p
		q["v"] = v
	for i in range(reveals.size() - 1, -1, -1):
		reveals[i]["t"] -= delta
		if reveals[i]["t"] <= 0.0:
			var x: int = reveals[i]["x"]
			var y: int = reveals[i]["y"]
			if w.tile(x, y) == Tiles.FALSE:
				w.set_tile(x, y, Tiles.OPEN)
				burst(Vector2(x * 16 + 8, y * 16 + 8), 6, [Color("ffd36b"), Color("fff1b8")], 30.0, -10.0, 1.0, 1.0)
			reveals.remove_at(i)
	for i in range(pulses.size() - 1, -1, -1):
		pulses[i]["r"] += 320.0 * delta
		if pulses[i]["r"] > 230.0:
			pulses.remove_at(i)
	for i in range(floats.size() - 1, -1, -1):
		floats[i]["t"] -= delta
		floats[i]["p"] += Vector2(0, -12.0 * delta)
		if floats[i]["t"] <= 0.0:
			floats.remove_at(i)


func _process(_d: float) -> void:
	queue_redraw()


func _draw() -> void:
	for s in splats:
		draw_rect(Rect2(s["p"], s["s"]), Color(0.42, 0.05, 0.12, 0.85))
	for q in parts:
		var c: Color = q["c"]
		c.a = clampf(q["life"] / q["max"] * 1.4, 0.0, 1.0)
		var sz: float = q["sz"]
		draw_rect(Rect2((q["p"] as Vector2).round(), Vector2(sz, sz)), c)
	for pl in pulses:
		draw_arc(pl["p"], pl["r"], 0.0, TAU, 48, Color(1.0, 0.83, 0.42, (1.0 - pl["r"] / 230.0) * 0.8), 1.0)
