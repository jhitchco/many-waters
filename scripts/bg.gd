extends Node2D
## Parallax sky, far hills and near tree line for each town, cross-faded between areas,
## with the cave backdrop fading in as the camera goes underground.

var GROUND_Y := 0.0
const AREAS := ["enfield", "greenwich", "dana", "works", "basin"]

var sets := {}
var cave: Texture2D
var cur := 0
var prev := 0
var blend := 1.0


func _ready() -> void:
	GROUND_Y = G.SURF_Y
	for a in AREAS:
		sets[a] = [load("res://assets/bg_%s_sky.png" % a), load("res://assets/bg_%s_far.png" % a), load("res://assets/bg_%s_mid.png" % a)]
	cave = load("res://assets/bg_cave.png")


func _process(delta: float) -> void:
	if G.cam == null:
		return
	var z: int = G.zone_at(G.cam.get_screen_center_position().x)
	if z != cur:
		prev = cur
		cur = z
		blend = 0.0
	blend = minf(1.0, blend + delta * 0.8)
	queue_redraw()


func _layer(t: Texture2D, cx: float, cy: float, fx: float, fy: float, base: float, a: float) -> void:
	var vs := get_viewport_rect().size
	var tw := float(t.get_width())
	var th := float(t.get_height())
	var y := roundf(vs.y * 0.5 + (GROUND_Y - cy) * fy - base)
	var ox := -fposmod(cx * fx, tw)
	var col := Color(1, 1, 1, a)
	var x := ox
	while x < vs.x:
		draw_texture_rect(t, Rect2(roundf(x), y, tw, th), false, col)
		# extend the bottom row downward so nothing shows beneath the layer
		if y + th < vs.y:
			draw_texture_rect_region(t, Rect2(roundf(x), y + th, tw, vs.y - (y + th)), Rect2(0, th - 1, tw, 1), col)
		x += tw


func _draw_set(key: String, cx: float, cy: float, a: float) -> void:
	var s: Array = sets[key]
	var vs := get_viewport_rect().size
	draw_texture_rect(s[0], Rect2(Vector2.ZERO, vs), false, Color(1, 1, 1, a))
	_layer(s[1], cx, cy, 0.1, 0.3, 215.0, a)
	_layer(s[2], cx, cy, 0.3, 0.55, 205.0, a)


func _draw() -> void:
	if G.cam == null:
		return
	var c := G.cam.get_screen_center_position()
	if blend < 1.0:
		_draw_set(AREAS[prev], c.x, c.y, 1.0)
	_draw_set(AREAS[cur], c.x, c.y, blend if blend < 1.0 else 1.0)
	if cur < 4:
		var under := clampf((c.y - (GROUND_Y + 120.0)) / 200.0, 0.0, 1.0)
		if under > 0.0:
			draw_texture_rect(cave, Rect2(Vector2.ZERO, get_viewport_rect().size), false, Color(1, 1, 1, under))
