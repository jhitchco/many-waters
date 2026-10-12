extends Node
## Sound effects (a small pool of players) and the looping valley drone.

const NAMES := ["squelch", "hurt", "bell", "crack", "boom", "shot", "splash", "chime", "tick", "gasp", "swing", "flood", "unlock"]
const VOL := {"gasp": -10.0, "swing": -8.0, "tick": -6.0, "splash": -6.0, "shot": -4.0}

var streams := {}
var pool: Array = []
var next := 0
var drone: AudioStreamPlayer
var muted := false


func _ready() -> void:
	for n in NAMES:
		streams[n] = load("res://assets/sfx/%s.wav" % n)
	for i in 10:
		var p := AudioStreamPlayer.new()
		add_child(p)
		pool.append(p)
	drone = AudioStreamPlayer.new()
	var s: AudioStreamWAV = load("res://assets/sfx/drone.wav")
	s.loop_mode = AudioStreamWAV.LOOP_FORWARD
	s.loop_begin = 0
	s.loop_end = int(s.get_length() * s.mix_rate)
	drone.stream = s
	drone.volume_db = -14.0
	add_child(drone)


func start_drone() -> void:
	if not drone.playing:
		drone.play()


func play(n: String, pitch_jitter: float = 0.08) -> void:
	if muted or not streams.has(n):
		return
	var p: AudioStreamPlayer = pool[next]
	next = (next + 1) % pool.size()
	p.stream = streams[n]
	p.volume_db = VOL.get(n, 0.0)
	p.pitch_scale = 1.0 + randf_range(-pitch_jitter, pitch_jitter)
	p.play()


func toggle_mute() -> bool:
	muted = not muted
	AudioServer.set_bus_mute(0, muted)
	return muted
