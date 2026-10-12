extends Node2D
## Foreground decor (ferns, flowers, glowing mushrooms) drawn in front of the creature.


func _process(_d: float) -> void:
	queue_redraw()


func _draw() -> void:
	var a = G.actors
	if a == null or a.t_props == null:
		return
	for d in a.decor_front:
		if a._visible(d["p"], 40.0):
			a.draw_decor_item(self, d)
