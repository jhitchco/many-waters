extends Node2D
## The tile map: loading, queries, destruction, and drawing the visible tiles.

const TS := Tiles.TS
const S := Vector2(TS, TS)

var W := 0
var H := 0
var t := PackedByteArray()
var orig := PackedByteArray()
var covered := PackedByteArray()   # open cells that show the cave back wall
var tex: Texture2D


func load_map() -> void:
	tex = load("res://assets/tiles.png")
	var lines := FileAccess.get_file_as_string("res://data/world.txt").strip_edges().split("\n")
	H = lines.size()
	W = lines[0].length()
	t.resize(W * H)
	for y in H:
		var ln: String = lines[y]
		for x in W:
			t[y * W + x] = Tiles.CHARS.get(ln[x], Tiles.ROCK)
	orig = t.duplicate()
	covered.resize(W * H)
	var surf := int(G.meta["surf"])
	var basin_x0 := int(G.meta["basin_x0"])
	for x in W:
		var above := 0
		for y in H:
			var v := t[y * W + x]
			if v != Tiles.E:
				above += 1
			# underground (below the town surface, outside the open basin) or under real cover
			covered[y * W + x] = 1 if v == Tiles.E and (above >= 2 or (y > surf and x < basin_x0 - 2)) else 0


func reset_tiles() -> void:
	t = orig.duplicate()
	queue_redraw()


func tile(x: int, y: int) -> int:
	if x < 0 or y < 0 or x >= W or y >= H:
		return Tiles.CLIFF
	return t[y * W + x]


func tile_at(p: Vector2) -> int:
	return tile(floori(p.x / TS), floori(p.y / TS))


func set_tile(x: int, y: int, v: int) -> void:
	if x >= 0 and y >= 0 and x < W and y < H:
		t[y * W + x] = v


func solid_c(v: int) -> bool:
	match v:
		Tiles.E, Tiles.OPEN:
			return false
		Tiles.DIRT:
			return not G.ab["shovel"]
	return true


## Tiles changed since load, for saving: [[index, value], ...]
func changes() -> Array:
	var out := []
	for i in t.size():
		if t[i] != orig[i]:
			out.append([i, t[i]])
	return out


func apply_changes(list: Array) -> void:
	t = orig.duplicate()
	for c in list:
		t[int(c[0])] = int(c[1])


func smash(x: int, y: int) -> void:
	set_tile(x, y, Tiles.E)
	var c := Vector2(x * TS + 8, y * TS + 8)
	G.fx.burst(c, 12, [Color("6b4a2c"), Color("a0703c"), Color("3d2918")], 110.0, 400.0, 2.0, 1.0)
	G.shake = maxf(G.shake, 2.0)
	G.sfx.play("crack")


func break_boards(x: int, y: int) -> void:
	var stack := [Vector2i(x, y)]
	var n := 0
	while stack.size() > 0 and n < 80:
		var p: Vector2i = stack.pop_back()
		if tile(p.x, p.y) != Tiles.BOARDS:
			continue
		set_tile(p.x, p.y, Tiles.E)
		n += 1
		G.fx.burst(Vector2(p.x * TS + 8, p.y * TS + 8), 6, [Color("8a6a3e"), Color("5a4026"), Color("c9a36a")], 90.0, 450.0, 2.0, 1.2)
		for d in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
			stack.append(p + d)
	G.shake = maxf(G.shake, 5.0)
	G.sfx.play("boom")
	G.hud.toast("The boards give way under your weight.")


func _process(_d: float) -> void:
	queue_redraw()


func _hash(x: int, y: int) -> int:
	return ((x * 73856093) ^ (y * 19349663)) & 0x7fffffff


func _empty(x: int, y: int) -> bool:
	var v := tile(x, y)
	return v == Tiles.E or v == Tiles.OPEN


func _draw() -> void:
	if W == 0 or G.cam == null:
		return
	var vs := get_viewport_rect().size
	var c := G.cam.get_screen_center_position()
	var x0 := maxi(0, floori((c.x - vs.x * 0.5) / TS) - 1)
	var x1 := mini(W - 1, floori((c.x + vs.x * 0.5) / TS) + 1)
	var y0 := maxi(0, floori((c.y - vs.y * 0.5) / TS) - 1)
	var y1 := mini(H - 1, floori((c.y + vs.y * 0.5) / TS) + 1)
	for y in range(y0, y1 + 1):
		for x in range(x0, x1 + 1):
			var v := t[y * W + x]
			var p := Vector2(x * TS, y * TS)
			var h := _hash(x, y) % 4
			if v == Tiles.E or v == Tiles.OPEN:
				if covered[y * W + x] == 1:
					draw_texture_rect_region(tex, Rect2(p, S), Rect2(h * TS, Tiles.ROW_CAVE * TS, TS, TS))
				if v == Tiles.OPEN:
					draw_texture_rect_region(tex, Rect2(p, S), Rect2(0, Tiles.ROW_MISC * TS, TS, TS))
				continue
			draw_texture_rect_region(tex, Rect2(p, S), Rect2(h * TS, Tiles.ATLAS_ROW[v] * TS, TS, TS))
			if v == Tiles.FALSE and G.reveal_t > 0.0:
				draw_rect(Rect2(p + Vector2(1, 1), S - Vector2(2, 2)), Color(1.0, 0.83, 0.42, 0.25 + 0.2 * sin(G.time * 8.0)), false, 1.0)
	# lips: grass on exposed tops, roots under exposed ceilings
	for y in range(y0, y1 + 1):
		for x in range(x0, x1 + 1):
			var v := t[y * W + x]
			if v != Tiles.ROCK and v != Tiles.DIRT:
				continue
			var h := _hash(x + 7, y) % 4
			if _empty(x, y - 1):
				draw_texture_rect_region(tex, Rect2(Vector2(x * TS, y * TS - 8), S), Rect2(h * TS, Tiles.ROW_GRASS * TS, TS, TS))
			if _empty(x, y + 1):
				draw_texture_rect_region(tex, Rect2(Vector2(x * TS, y * TS + 8), S), Rect2(h * TS, Tiles.ROW_CEIL * TS, TS, TS))
