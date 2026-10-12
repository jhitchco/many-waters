extends Node2D
## The rising reservoir, drawn over everything in open cells below the water line.

const TS := Tiles.TS
var tex: Texture2D


func _ready() -> void:
	tex = load("res://assets/tiles.png")


func _process(_d: float) -> void:
	queue_redraw()


func _draw() -> void:
	if not G.flood or G.cam == null:
		return
	var w = G.world
	var vs := get_viewport_rect().size
	var c := G.cam.get_screen_center_position()
	var wy: float = G.water_y
	if wy > c.y + vs.y * 0.5:
		return
	var x0 := maxi(0, floori((c.x - vs.x * 0.5) / TS) - 1)
	var x1 := mini(w.W - 1, floori((c.x + vs.x * 0.5) / TS) + 1)
	var top := floori(wy / TS)
	var y1 := mini(w.H - 1, floori((c.y + vs.y * 0.5) / TS) + 1)
	var frame := int(G.time * 5.0) % 3
	for x in range(x0, x1 + 1):
		# partial cell at the surface
		var v: int = w.tile(x, top)
		if v == Tiles.E or v == Tiles.OPEN:
			var cell_bottom := (top + 1) * TS
			draw_texture_rect_region(tex, Rect2(x * TS, wy, TS, cell_bottom - wy), Rect2(4 * TS, Tiles.ROW_MISC * TS, TS, cell_bottom - wy))
			draw_texture_rect_region(tex, Rect2(x * TS, wy - 2.0 + sin(G.time * 2.0 + x * 0.7), TS, 6), Rect2((1 + frame) * TS, Tiles.ROW_MISC * TS, TS, 6))
		for y in range(maxi(top + 1, floori((c.y - vs.y * 0.5) / TS)), y1 + 1):
			var u: int = w.tile(x, y)
			if u == Tiles.E or u == Tiles.OPEN:
				draw_texture_rect_region(tex, Rect2(x * TS, y * TS, TS, TS), Rect2(4 * TS, Tiles.ROW_MISC * TS, TS, TS))
