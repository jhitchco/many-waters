extends Node
## Sound: one-shot effects from a small pool, crossfading music and ambient beds,
## the creature's slither and dig loops, a heartbeat when weak, and muffling underwater.

const NAMES := ["squelch", "hurt", "bell", "crack", "boom", "shot", "splash", "chime", "tick", "gasp", "swing", "flood",
	"unlock", "scream", "scream2", "bleat", "whisper", "splash_big", "heartbeat", "bark", "flame", "snap", "roar", "howl", "gurgle", "paper", "sting"]
const VOL := {"gasp": -10.0, "swing": -8.0, "tick": -6.0, "splash": -6.0, "shot": -4.0, "scream": -7.0, "scream2": -7.0,
	"bleat": -8.0, "bark": -6.0, "flame": -6.0, "gurgle": -10.0, "paper": -4.0, "howl": -9.0, "roar": -2.0, "whisper": -6.0, "heartbeat": -4.0, "splash_big": -5.0}
const MUSIC_DB := -9.0
const AMB_DB := -13.0
const FADE := 2.5

var streams := {}
var pool: Array = []
var next := 0
var muted := false

var music: Array = []          # two players, crossfaded
var music_cur := 0
var music_name := ""
var amb: Array = []
var amb_cur := 0
var amb_name := ""
var slither: AudioStreamPlayer
var digging: AudioStreamPlayer
var engine: AudioStreamPlayer
var crackle: AudioStreamPlayer
var engine_db := -60.0
var crackle_db := -60.0
var drone: AudioStreamPlayer
var muffle: AudioEffectLowPassFilter
var heart_t := 0.0
var was_wet := false


func _ready() -> void:
	for n in NAMES:
		streams[n] = load("res://assets/sfx/%s.wav" % n)
	for i in 12:
		var p := AudioStreamPlayer.new()
		add_child(p)
		pool.append(p)
	for i in 2:
		music.append(_looper(-80.0))
		amb.append(_looper(-80.0))
	slither = _looper(-80.0, "res://assets/sfx/slither.wav")
	digging = _looper(-80.0, "res://assets/sfx/dig.wav")
	engine = _looper(-80.0, "res://assets/sfx/engine.wav")
	crackle = _looper(-80.0, "res://assets/sfx/crackle.wav")
	drone = _looper(-20.0, "res://assets/sfx/drone.wav")
	muffle = AudioEffectLowPassFilter.new()
	muffle.cutoff_hz = 700.0
	AudioServer.add_bus_effect(0, muffle)
	AudioServer.set_bus_effect_enabled(0, AudioServer.get_bus_effect_count(0) - 1, false)


func _loop_stream(path: String) -> AudioStreamWAV:
	var s: AudioStreamWAV = load(path)
	s.loop_mode = AudioStreamWAV.LOOP_FORWARD
	s.loop_begin = 0
	s.loop_end = int(s.get_length() * s.mix_rate)
	return s


func _looper(db: float, path: String = "") -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.volume_db = db
	if path != "":
		p.stream = _loop_stream(path)
	add_child(p)
	return p


func start_drone() -> void:
	for p in [drone, slither, digging, engine, crackle]:
		if not p.playing:
			p.play()


func play(n: String, pitch_jitter: float = 0.08) -> void:
	if muted or not streams.has(n):
		return
	var p: AudioStreamPlayer = pool[next]
	next = (next + 1) % pool.size()
	p.stream = streams[n]
	p.volume_db = VOL.get(n, 0.0)
	p.pitch_scale = 1.0 + randf_range(-pitch_jitter, pitch_jitter)
	p.play()


func _switch(players: Array, cur: int, path: String) -> int:
	var nxt := 1 - cur
	var p: AudioStreamPlayer = players[nxt]
	p.stream = _loop_stream(path)
	p.volume_db = -60.0
	p.play()
	return nxt


func set_music(n: String) -> void:
	if n == music_name:
		return
	music_name = n
	music_cur = _switch(music, music_cur, "res://assets/music/%s.wav" % n)


func set_ambient(n: String) -> void:
	if n == amb_name:
		return
	amb_name = n
	amb_cur = _switch(amb, amb_cur, "res://assets/ambient/%s.wav" % n)


func _fade(players: Array, cur: int, target: float, delta: float) -> void:
	for i in players.size():
		var p: AudioStreamPlayer = players[i]
		var goal := target if i == cur else -60.0
		p.volume_db = move_toward(p.volume_db, goal, delta * 60.0 / FADE)
		if i != cur and p.playing and p.volume_db <= -59.0:
			p.stop()


func _process(delta: float) -> void:
	_fade(music, music_cur, MUSIC_DB, delta)
	_fade(amb, amb_cur, AMB_DB, delta)
	var c = G.creature
	var active: bool = G.running and not G.paused and c != null and not c.dead
	var speed: float = c.vel.length() if active else 0.0
	var wet: bool = active and c.in_water
	slither.volume_db = move_toward(slither.volume_db, -60.0 if (not active or c.in_dirt or speed < 15.0) else -16.0 + minf(6.0, speed / 30.0), delta * 120.0)
	slither.pitch_scale = 0.8 + minf(0.5, speed / 300.0) if active else 1.0
	digging.volume_db = move_toward(digging.volume_db, -12.0 if (active and c.in_dirt and speed > 10.0) else -60.0, delta * 120.0)
	engine.volume_db = move_toward(engine.volume_db, engine_db if active else -60.0, delta * 60.0)
	crackle.volume_db = move_toward(crackle.volume_db, crackle_db if active else -60.0, delta * 60.0)
	if active and wet != was_wet:
		play("splash_big")
	was_wet = wet
	AudioServer.set_bus_effect_enabled(0, AudioServer.get_bus_effect_count(0) - 1, wet)
	if active and c.mass <= 3:
		heart_t -= delta
		if heart_t <= 0.0:
			heart_t = 0.7 if c.mass <= 2 else 1.0
			play("heartbeat", 0.0)


func toggle_mute() -> bool:
	muted = not muted
	AudioServer.set_bus_mute(0, muted)
	return muted
