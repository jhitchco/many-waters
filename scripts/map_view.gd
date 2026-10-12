extends Control
## The map: every tile the creature has seen, with graves, cellar holes and the intake.

var hud


func _process(_d: float) -> void:
	if visible:
		queue_redraw()


func _draw() -> void:
	var m = G.main
	var w = G.world
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.03, 0.04, 0.07, 0.95))
	var sc := floorf(minf((size.x - 120.0) / w.W, (size.y - 240.0) / w.H) * 2.0) / 2.0
	sc = maxf(1.0, sc)
	var dim := Vector2(w.W, w.H) * sc
	var o := ((size - dim) * 0.5 + Vector2(0, 20)).round()
	draw_string(hud.serif, o + Vector2(0, -56), "The valley", HORIZONTAL_ALIGNMENT_LEFT, -1, 44, hud.BONE)
	var found := 0
	var opened := 0
	for g in G.actors.graves:
		opened += 1 if g["opened"] else 0
	draw_string(hud.mono, o + Vector2(0, -24), "GRAVES OPENED %d OF %d    TAB TO CLOSE" % [opened, G.actors.graves.size()], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, hud.DIM)
	draw_rect(Rect2(o - Vector2(2, 2), dim + Vector2(4, 4)), Color(1, 1, 1, 0.12), false, 1.0)
	draw_texture_rect(m.map_tex, Rect2(o, dim), false)
	if G.flood:
		var wy: float = G.water_y / 16.0 * sc
		draw_rect(Rect2(o + Vector2(0, wy), Vector2(dim.x, dim.y - wy)), Color(0.25, 0.7, 0.75, 0.18))
	for z in Data.ZONES:
		var x0: float = z["x0"] * sc
		draw_line(o + Vector2(x0, 0), o + Vector2(x0, dim.y), Color(1, 1, 1, 0.08), 1.0)
		draw_string(hud.mono, o + Vector2(x0 + 6, dim.y + 22), String(z["n"]) + "  " + String(z["name"]).to_upper(), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, hud.DIM)
	for g in G.actors.graves:
		var gp: Vector2 = g["p"] / 16.0
		if m.explored[int(gp.y - 1) * w.W + int(gp.x)] == 0:
			continue
		found += 1
		var q := o + gp * sc
		draw_rect(Rect2(q - Vector2(2, 4), Vector2(4, 4)), Color(1, 1, 1, 0.25) if g["opened"] else hud.GOLD)
	for k in G.actors.cps:
		if k["on"]:
			var q: Vector2 = o + k["p"] / 16.0 * sc
			draw_rect(Rect2(q - Vector2(2, 3), Vector2(5, 3)), hud.BLOOD)
	var ip: Vector2 = o + G.actors.intake / 16.0 * sc
	draw_rect(Rect2(ip - Vector2(2, 6), Vector2(4, 6)), hud.TEAL)
	var cp: Vector2 = o + G.creature.position / 16.0 * sc
	var pulse := 3.0 + sin(G.time * 6.0 + Time.get_ticks_msec() * 0.006) * 1.5
	draw_circle(cp, pulse + 2.0, Color(0, 0, 0, 0.6))
	draw_circle(cp, pulse, Color("e0566a"))
	var ly := o.y + dim.y + 48
	draw_rect(Rect2(Vector2(o.x, ly - 8), Vector2(6, 6)), hud.GOLD)
	draw_string(hud.mono, Vector2(o.x + 12, ly), "UNOPENED GRAVE", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, hud.DIM)
	draw_rect(Rect2(Vector2(o.x + 160, ly - 8), Vector2(6, 6)), hud.BLOOD)
	draw_string(hud.mono, Vector2(o.x + 172, ly), "CELLAR HOLE", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, hud.DIM)
	draw_rect(Rect2(Vector2(o.x + 300, ly - 8), Vector2(6, 6)), hud.TEAL)
	draw_string(hud.mono, Vector2(o.x + 312, ly), "INTAKE", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, hud.DIM)
