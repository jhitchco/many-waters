extends Control
## Screen-resolution interface: stage header, taken/kept balance, abilities, the chorus,
## hints, cards, and the title, pause, chorus, map and ending screens.

const BONE := Color("f2e6c8")
const DIM := Color("a89f8e")
const GOLD := Color("ffd36b")
const BLOOD := Color("e0566a")
const TEAL := Color("9cdfe0")
const INK := Color(0.03, 0.04, 0.07)

var serif: SystemFont
var serif_i: SystemFont
var mono: SystemFont

var st_kick: Label
var st_name: Label
var st_obj: Label
var bal_box: VBoxContainer
var bal_top: Label
var bal_fill: ColorRect
var bal_back: ColorRect
var bal_note: Label
var chips := {}
var chips_box: HBoxContainer
var keys_lbl: Label
var chorus_box: VBoxContainer
var hint_panel: PanelContainer
var hint_lbl: Label
var card_box: VBoxContainer
var card_kick: Label
var card_title: Label
var card_quote: Label
var card_body: Label
var card_t := 0.0
var toast_lbl: Label
var toast_t := 0.0
var game_ui: Control

var title_scr: Control
var btn_continue: Button
var btn_new: Button
var ending_scr: Control
var end_title: Label
var end_body: Label
var end_tally: Label
var end_btn: Button
var chorus_scr: Control
var chorus_list: VBoxContainer
var chorus_head: Label
var pause_scr: Control
var map_scr: Control
var fb_ui: Control
var fb_kick: Label
var fb_title: Label
var fb_line: Label
var fb_goal: Label
var fb_prompt: Label
var fb_card_t := 0.0
var region_lbl: Label
var region_t := 0.0
var boss_box: VBoxContainer
var boss_title: Label
var boss_back: ColorRect
var boss_fill: ColorRect
var frenzy_lbl: Label
var frenzy_t := 0.0
var ach_box: PanelContainer
var ach_title: Label
var ach_desc: Label
var ach_t := 0.0
var prog_lbl: Label
var pause_ach: Label
var sliders := {}
var letter_scr: Control
var letter_title: Label
var letter_from: Label
var letter_body: Label
var intro_scr: Control
var intro_lbl: Label
var intro_lines: Array = []
var intro_t := 0.0


func build() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	serif = SystemFont.new()
	serif.font_names = PackedStringArray(["Georgia", "Palatino Linotype", "Times New Roman", "serif"])
	serif_i = SystemFont.new()
	serif_i.font_names = serif.font_names
	serif_i.font_italic = true
	mono = SystemFont.new()
	mono.font_names = PackedStringArray(["Courier New", "Consolas", "monospace"])
	mono.font_weight = 700

	game_ui = Control.new()
	game_ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	game_ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(game_ui)

	var head := VBoxContainer.new()
	head.position = Vector2(28, 22)
	head.custom_minimum_size = Vector2(560, 0)
	head.add_theme_constant_override("separation", 2)
	game_ui.add_child(head)
	st_kick = _label("", mono, 14, GOLD)
	st_name = _label("", serif, 36, BONE)
	st_obj = _label("", serif_i, 19, BONE, true)
	st_obj.custom_minimum_size = Vector2(560, 0)
	head.add_child(st_kick); head.add_child(st_name); head.add_child(st_obj)

	bal_box = VBoxContainer.new()
	bal_box.custom_minimum_size = Vector2(270, 0)
	bal_box.add_theme_constant_override("separation", 5)
	game_ui.add_child(bal_box)
	bal_top = _label("", mono, 15, BONE)
	bal_top.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	bal_box.add_child(bal_top)
	bal_back = ColorRect.new()
	bal_back.color = GOLD
	bal_back.custom_minimum_size = Vector2(270, 6)
	bal_box.add_child(bal_back)
	bal_fill = ColorRect.new()
	bal_fill.color = Color("8c1c34")
	bal_fill.size = Vector2(135, 6)
	bal_back.add_child(bal_fill)
	bal_note = _label("", serif_i, 15, DIM, true)
	bal_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	bal_note.custom_minimum_size = Vector2(270, 0)
	bal_box.add_child(bal_note)

	var foot := VBoxContainer.new()
	foot.name = "foot"
	foot.add_theme_constant_override("separation", 8)
	game_ui.add_child(foot)
	chips_box = HBoxContainer.new()
	chips_box.add_theme_constant_override("separation", 8)
	foot.add_child(chips_box)
	var fl := PanelContainer.new()
	fl.add_theme_stylebox_override("panel", _box(Color(0.03, 0.04, 0.07, 0.6), Color("e0566a"), 10, 5))
	fl.add_child(_label("FLING  SHIFT / RMB", mono, 13, BONE))
	chips_box.add_child(fl)
	for a in [["axe", "THE AXE"], ["shovel", "THE SHOVEL"], ["level", "THE LEVEL  F"], ["charge", "THE CHARGE  E"]]:
		var pc := PanelContainer.new()
		var l := _label(a[1], mono, 13, DIM)
		pc.add_child(l)
		chips_box.add_child(pc)
		chips[a[0]] = [pc, l]
	keys_lbl = _label("MOVE WASD · TAKE SPACE/CLICK · FLING SHIFT/RIGHT-CLICK · SHED Q AT A SPRING · MAP TAB · CHORUS C · PAUSE ESC", mono, 12, DIM)
	foot.add_child(keys_lbl)

	chorus_box = VBoxContainer.new()
	chorus_box.custom_minimum_size = Vector2(470, 0)
	chorus_box.add_theme_constant_override("separation", 10)
	game_ui.add_child(chorus_box)

	hint_panel = PanelContainer.new()
	hint_panel.add_theme_stylebox_override("panel", _box(Color(0.03, 0.04, 0.07, 0.78), Color(1, 1, 1, 0.15), 14, 8))
	hint_lbl = _label("", mono, 15, BONE)
	hint_panel.add_child(hint_lbl)
	hint_panel.visible = false
	game_ui.add_child(hint_panel)

	card_box = VBoxContainer.new()
	card_box.custom_minimum_size = Vector2(700, 0)
	card_box.add_theme_constant_override("separation", 6)
	card_box.modulate.a = 0.0
	card_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	game_ui.add_child(card_box)
	card_kick = _center(_label("", mono, 14, GOLD))
	card_title = _center(_label("", serif, 58, BONE))
	card_quote = _center(_label("", serif_i, 22, GOLD, true))
	card_body = _center(_label("", serif, 20, BONE, true))
	for l in [card_kick, card_title, card_quote, card_body]:
		l.custom_minimum_size = Vector2(700, 0)
		card_box.add_child(l)

	toast_lbl = _center(_label("", mono, 14, DIM, true))
	toast_lbl.custom_minimum_size = Vector2(800, 0)
	toast_lbl.modulate.a = 0.0
	game_ui.add_child(toast_lbl)

	region_lbl = _center(_label("", mono, 16, BONE))
	region_lbl.custom_minimum_size = Vector2(800, 0)
	region_lbl.modulate.a = 0.0
	game_ui.add_child(region_lbl)
	boss_box = VBoxContainer.new()
	boss_box.custom_minimum_size = Vector2(560, 0)
	boss_box.visible = false
	game_ui.add_child(boss_box)
	boss_title = _center(_label("", serif, 26, BONE))
	boss_title.custom_minimum_size = Vector2(560, 0)
	boss_box.add_child(boss_title)
	boss_back = ColorRect.new()
	boss_back.color = Color(0.1, 0.02, 0.05, 0.85)
	boss_back.custom_minimum_size = Vector2(560, 12)
	boss_box.add_child(boss_back)
	boss_fill = ColorRect.new()
	boss_fill.color = Color("c42a3f")
	boss_back.add_child(boss_fill)
	frenzy_lbl = _center(_label("", serif_i, 48, Color("ff6a5a")))
	frenzy_lbl.custom_minimum_size = Vector2(500, 0)
	frenzy_lbl.modulate.a = 0.0
	game_ui.add_child(frenzy_lbl)
	ach_box = PanelContainer.new()
	ach_box.add_theme_stylebox_override("panel", _box(Color(0.05, 0.04, 0.02, 0.92), GOLD, 16, 10))
	var av := VBoxContainer.new()
	ach_title = _label("", mono, 15, GOLD)
	ach_desc = _label("", serif_i, 16, BONE)
	av.add_child(ach_title)
	av.add_child(ach_desc)
	ach_box.add_child(av)
	ach_box.modulate.a = 0.0
	add_child(ach_box)
	prog_lbl = _label("", mono, 13, DIM)
	prog_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	prog_lbl.custom_minimum_size = Vector2(270, 0)
	bal_box.add_child(prog_lbl)
	_build_flashback()
	_build_letter()
	_build_intro()
	_build_title()
	_build_ending()
	_build_chorus()
	_build_pause()
	map_scr = preload("res://scripts/map_view.gd").new()
	map_scr.set_anchors_preset(Control.PRESET_FULL_RECT)
	map_scr.visible = false
	map_scr.hud = self
	add_child(map_scr)
	resized.connect(_layout)
	_layout()


func _label(text: String, f: Font, sz: int, c: Color, wrap: bool = false) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", f)
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", c)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("shadow_offset_x", 2)
	l.add_theme_constant_override("shadow_offset_y", 2)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if wrap:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


func _center(l: Label) -> Label:
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l


func _box(bg: Color, border: Color, mx: int, my: int) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(1)
	s.content_margin_left = mx
	s.content_margin_right = mx
	s.content_margin_top = my
	s.content_margin_bottom = my
	return s


func _button(text: String) -> Button:
	var b := Button.new()
	b.text = text
	b.add_theme_font_override("font", serif)
	b.add_theme_font_size_override("font_size", 26)
	b.add_theme_color_override("font_color", BONE)
	b.add_theme_color_override("font_hover_color", BONE)
	b.add_theme_color_override("font_focus_color", BONE)
	b.add_theme_stylebox_override("normal", _box(Color(0, 0, 0, 0), BONE, 28, 10))
	b.add_theme_stylebox_override("hover", _box(Color("8c1c34"), Color("8c1c34"), 28, 10))
	b.add_theme_stylebox_override("pressed", _box(Color("8c1c34"), Color("8c1c34"), 28, 10))
	var f := _box(Color("8c1c34"), GOLD, 28, 10)
	b.add_theme_stylebox_override("focus", f)
	return b


func _screen(alpha: float) -> Control:
	var c := Control.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	var bg := ColorRect.new()
	bg.color = Color(INK.r, INK.g, INK.b, alpha)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	c.add_child(bg)
	c.visible = false
	add_child(c)
	return c


func _build_flashback() -> void:
	fb_ui = Control.new()
	fb_ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	fb_ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fb_ui.visible = false
	add_child(fb_ui)
	var head := VBoxContainer.new()
	head.name = "head"
	head.custom_minimum_size = Vector2(900, 0)
	fb_ui.add_child(head)
	fb_kick = _center(_label("", mono, 15, GOLD))
	fb_title = _center(_label("", serif_i, 54, BONE))
	for l in [fb_kick, fb_title]:
		l.custom_minimum_size = Vector2(900, 0)
		head.add_child(l)
	fb_line = _center(_label("", serif_i, 27, BONE, true))
	fb_line.custom_minimum_size = Vector2(980, 0)
	fb_ui.add_child(fb_line)
	fb_goal = _label("", mono, 15, GOLD)
	fb_ui.add_child(fb_goal)
	fb_prompt = _center(_label("SPACE", mono, 16, BONE))
	fb_prompt.custom_minimum_size = Vector2(400, 0)
	fb_ui.add_child(fb_prompt)


func flashback_begin(title: String, when: String) -> void:
	fb_kick.text = "A MEMORY · " + when.to_upper()
	fb_title.text = title
	fb_card_t = 5.0
	fb_ui.visible = true
	game_ui.visible = false
	fb_line.text = ""
	_layout()


func flashback_line(s: String) -> void:
	fb_line.text = s
	_layout()


func flashback_goal(s: String) -> void:
	fb_goal.text = s.to_upper()


func flashback_prompt(on: bool) -> void:
	fb_prompt.visible = on
	fb_prompt.text = "SPACE  " + fb_goal.text.to_lower() if on else ""


func flashback_end() -> void:
	fb_ui.visible = false
	game_ui.visible = true


func _build_letter() -> void:
	letter_scr = _screen(0.7)
	var pc := PanelContainer.new()
	pc.name = "v"
	pc.add_theme_stylebox_override("panel", _box(Color("efe5cc"), Color("6a5a40"), 40, 32))
	letter_scr.add_child(pc)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	pc.add_child(v)
	letter_from = _label("", mono, 13, Color("7a6040"))
	letter_title = _label("", serif, 36, Color("2a2018"))
	letter_body = _label("", serif, 20, Color("2a2018"), true)
	letter_body.custom_minimum_size = Vector2(720, 0)
	var close := _label("SPACE / ESC  put it back", mono, 13, Color("7a6040"))
	for l in [letter_from, letter_title, letter_body, close]:
		l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0))
		v.add_child(l)


func show_letter(title: String, from: String, body: String) -> void:
	letter_from.text = from.to_upper()
	letter_title.text = title
	letter_body.text = body
	letter_scr.visible = true
	_layout()


func close_letter() -> void:
	letter_scr.visible = false


func letter_open() -> bool:
	return letter_scr != null and letter_scr.visible


func _build_intro() -> void:
	intro_scr = _screen(1.0)
	intro_lbl = _center(_label("", serif_i, 30, BONE, true))
	intro_lbl.custom_minimum_size = Vector2(900, 0)
	intro_scr.add_child(intro_lbl)
	var skip := _label("SPACE  continue", mono, 13, DIM)
	skip.name = "skip"
	intro_scr.add_child(skip)


func play_intro(lines: Array) -> void:
	intro_lines = lines.duplicate()
	intro_scr.visible = true
	advance_intro()


func advance_intro() -> void:
	if intro_lines.is_empty():
		skip_intro()
		return
	intro_lbl.text = intro_lines.pop_front()
	intro_t = 6.0
	intro_lbl.modulate.a = 0.0
	G.sfx.play("chime", 0.0)
	_layout()


func skip_intro() -> void:
	intro_lines.clear()
	if intro_scr.visible:
		intro_scr.visible = false
		G.paused = false


func intro_open() -> bool:
	return intro_scr != null and intro_scr.visible


func boss_bar(title: String, hp: int, mx: int) -> void:
	boss_box.visible = title != ""
	if title != "":
		boss_title.text = title
		boss_fill.size = Vector2(560.0 * maxf(0.0, float(hp)) / maxf(1.0, float(mx)), 12)


func frenzy(n: int) -> void:
	frenzy_lbl.text = "FRENZY ×%d" % n + ("   +1 mass" if n >= 3 else "")
	frenzy_t = 2.2
	frenzy_lbl.scale = Vector2.ONE * 1.25


func achievement(title: String, desc: String) -> void:
	ach_title.text = "ACHIEVEMENT  ·  " + title.to_upper()
	ach_desc.text = desc
	ach_t = 4.5
	G.sfx.play("chime", 0.0)


func progress(mem: int, mem_total: int, hearts: int, hearts_total: int, papers: int, papers_total: int) -> void:
	prog_lbl.text = "MEMORIES %d/%d · HEARTS %d/%d · PAPERS %d/%d" % [mem, mem_total, hearts, hearts_total, papers, papers_total]


func show_region(name: String) -> void:
	region_lbl.text = "—  " + name.to_upper() + "  —"
	region_t = 3.5


func _build_title() -> void:
	title_scr = _screen(0.82)
	var v := VBoxContainer.new()
	v.name = "v"
	v.add_theme_constant_override("separation", 10)
	title_scr.add_child(v)
	v.add_child(_label("SWIFT RIVER VALLEY, MASSACHUSETTS · 1938–1946", mono, 15, GOLD))
	v.add_child(_label("Many Waters", serif, 120, BONE))
	for p in ["In 1938 the Commonwealth dissolved four towns to build a reservoir for Boston. Crews cut every tree, dug up every grave they could find, and closed the gates.",
			"Something under the valley has been fed by those graves for two hundred years. It is waking up."]:
		var l := _label(p, serif, 22, BONE, true)
		l.custom_minimum_size = Vector2(760, 0)
		v.add_child(l)
	var s := _label("Take the living for strength. Open the graves for memory. Each kind of person you take teaches you something they knew, and what you learn opens places you have already been.", serif_i, 19, DIM, true)
	s.custom_minimum_size = Vector2(760, 0)
	v.add_child(s)
	v.add_child(_label("ENFIELD · GREENWICH · DANA · PRESCOTT", mono, 16, DIM))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	v.add_child(row)
	btn_continue = _button("Continue")
	btn_new = _button("Wake")
	var quit := _button("Quit")
	row.add_child(btn_continue); row.add_child(btn_new); row.add_child(quit)
	btn_continue.pressed.connect(func(): G.main.continue_game())
	btn_new.pressed.connect(func(): G.main.new_game())
	quit.pressed.connect(func(): get_tree().quit())


func _build_ending() -> void:
	ending_scr = _screen(0.9)
	var v := VBoxContainer.new()
	v.name = "v"
	v.add_theme_constant_override("separation", 12)
	ending_scr.add_child(v)
	v.add_child(_label("FULL POOL · 530 FEET", mono, 15, GOLD))
	end_title = _label("", serif, 96, BONE)
	end_body = _label("", serif, 22, BONE, true)
	end_body.custom_minimum_size = Vector2(800, 0)
	end_tally = _label("", mono, 15, DIM, true)
	end_tally.custom_minimum_size = Vector2(800, 0)
	v.add_child(end_title); v.add_child(end_body); v.add_child(end_tally)
	v.add_child(_label("ENFIELD · GREENWICH · DANA · PRESCOTT", mono, 16, DIM))
	end_btn = _button("Wake again")
	end_btn.pressed.connect(func(): G.main.new_game())
	v.add_child(end_btn)


func _build_chorus() -> void:
	chorus_scr = _screen(0.93)
	var sc := ScrollContainer.new()
	sc.name = "sc"
	chorus_scr.add_child(sc)
	chorus_list = VBoxContainer.new()
	chorus_list.add_theme_constant_override("separation", 14)
	chorus_list.custom_minimum_size = Vector2(820, 0)
	sc.add_child(chorus_list)


func _build_pause() -> void:
	pause_scr = _screen(0.8)
	var v := VBoxContainer.new()
	v.name = "v"
	v.add_theme_constant_override("separation", 10)
	pause_scr.add_child(v)
	v.add_child(_label("Paused", serif, 72, BONE))
	for line in ["Move  WASD / arrows / left stick. You cling to any rough surface.",
			"Take a person or animal, open a grave  Space / J / A",
			"Read the land (The Level)  F / X        Set a charge (The Charge)  E / Y",
			"Give mass back at a spring  hold Q / B",
			"Map  Tab / M        Chorus  C        Sound  N        Resume  Esc / P",
			"",
			"Rotten boards give way under 10 mass or more. Crawlways fit 6 or less.",
			"Taken counts the living you eat. Kept counts the graves you open. Animals count for neither.",
			"Fling  Shift / right-click / LB. Take three in a row quickly for a FRENZY."]:
		v.add_child(_label(line, mono, 16, BONE if line != "" else DIM))
	for row in [["MUSIC", "music"], ["SOUND", "sound"]]:
		var h := HBoxContainer.new()
		h.add_theme_constant_override("separation", 16)
		var l := _label(row[0], mono, 16, GOLD)
		l.custom_minimum_size = Vector2(90, 0)
		h.add_child(l)
		var sl := HSlider.new()
		sl.name = "slider_" + row[1]
		sl.min_value = 0.0
		sl.max_value = 1.0
		sl.step = 0.05
		sl.custom_minimum_size = Vector2(320, 24)
		sl.focus_mode = Control.FOCUS_ALL
		var which: String = row[1]
		sl.value_changed.connect(func(val): G.sfx.set_volume(which, val); G.sfx.play("tick", 0.0))
		h.add_child(sl)
		var hint := _label("LEFT / RIGHT to change", mono, 12, DIM)
		h.add_child(hint)
		v.add_child(h)
		sliders[which] = sl
	pause_ach = _label("", mono, 14, GOLD, true)
	pause_ach.custom_minimum_size = Vector2(900, 0)
	v.add_child(pause_ach)


func _layout() -> void:
	var s := size
	bal_box.position = Vector2(s.x - 270 - 28, 24)
	var foot: Control = game_ui.get_node("foot")
	foot.position = Vector2(28, s.y - foot.get_combined_minimum_size().y - 24)
	chorus_box.position = Vector2(s.x - 470 - 28, s.y - chorus_box.get_combined_minimum_size().y - 24)
	hint_panel.position = Vector2((s.x - hint_panel.get_combined_minimum_size().x) * 0.5, s.y - 120)
	card_box.position = Vector2((s.x - 700) * 0.5, s.y * 0.2)
	region_lbl.position = Vector2((s.x - 800) * 0.5, s.y * 0.13)
	boss_box.position = Vector2((s.x - 560) * 0.5, s.y * 0.19)
	frenzy_lbl.position = Vector2((s.x - 500) * 0.5, s.y * 0.3)
	frenzy_lbl.pivot_offset = Vector2(250, 30)
	ach_box.position = Vector2(s.x - ach_box.get_combined_minimum_size().x - 28, s.y * 0.2)
	if fb_ui != null:
		var head: Control = fb_ui.get_node("head")
		head.position = Vector2((s.x - 900) * 0.5, s.y * 0.1)
		fb_line.position = Vector2((s.x - 980) * 0.5, s.y - 150)
		fb_goal.position = Vector2(28, s.y - 40)
		fb_prompt.position = Vector2((s.x - 400) * 0.5, s.y - 70)
	toast_lbl.size = Vector2(800, 0)
	toast_lbl.position = Vector2((s.x - 800) * 0.5, s.y - 178)
	for scr in [title_scr, ending_scr, pause_scr, letter_scr]:
		var v: Control = scr.get_node("v")
		var m := v.get_combined_minimum_size()
		v.position = Vector2(maxf(40.0, s.x * 0.09), maxf(30.0, (s.y - m.y) * 0.5))
	if intro_scr != null:
		intro_lbl.position = Vector2((s.x - 900) * 0.5, s.y * 0.42)
		intro_scr.get_node("skip").position = Vector2(28, s.y - 40)
	var sc: ScrollContainer = chorus_scr.get_node("sc")
	sc.position = Vector2(maxf(40.0, s.x * 0.09), 40)
	sc.size = Vector2(minf(880.0, s.x - 80.0), s.y - 80)


# ---------------------------------------------------------------- screens
func show_title(has_save: bool) -> void:
	game_ui.visible = false
	title_scr.visible = true
	btn_continue.visible = has_save
	_layout()
	(btn_continue if has_save else btn_new).grab_focus()


func on_new_game() -> void:
	title_scr.visible = false
	ending_scr.visible = false
	letter_scr.visible = false
	chorus_scr.visible = false
	pause_scr.visible = false
	map_scr.visible = false
	game_ui.visible = true
	card_t = 0.0
	card_box.modulate.a = 0.0
	voices_changed()


func show_ending(title: String, body: String, tally: String) -> void:
	end_title.text = title
	end_body.text = body
	end_tally.text = tally
	game_ui.visible = false
	ending_scr.visible = true
	_layout()
	end_btn.grab_focus()


func any_overlay() -> bool:
	return chorus_scr.visible or pause_scr.visible or map_scr.visible


func toggle_overlay(which: String) -> void:
	var scr: Control = {"chorus": chorus_scr, "pause": pause_scr, "map": map_scr}[which]
	var open := not scr.visible
	for o in [chorus_scr, pause_scr, map_scr]:
		o.visible = false
	scr.visible = open
	if which == "chorus" and open:
		_fill_chorus()
	if which == "pause" and open:
		for k in sliders:
			sliders[k].set_value_no_signal(G.sfx.vol[k])
		sliders["music"].grab_focus()
		var got := []
		for a in Data.ACHIEVEMENTS:
			if G.ach.has(a[0]):
				got.append(a[1])
		pause_ach.text = "ACHIEVEMENTS %d / %d    %s" % [got.size(), Data.ACHIEVEMENTS.size(), " · ".join(got)]
	G.paused = open
	_layout()


func _fill_chorus() -> void:
	for c in chorus_list.get_children():
		c.queue_free()
	chorus_head = _label("The chorus", serif, 52, BONE)
	chorus_list.add_child(chorus_head)
	var sub := "Everyone you carry, in the order you took them. %d taken, %d kept. Press C to close." % [G.taken, G.kept]
	if G.voices.is_empty():
		sub = "You carry no one yet. Press C to close."
	chorus_list.add_child(_label(sub, mono, 14, DIM, true))
	for v in G.voices:
		chorus_list.add_child(_voice(v, 820.0))


func _voice(v: Dictionary, width: float) -> VBoxContainer:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	var kind: String = v["kind"]
	var who := _label(String(v["name"]).to_upper() + ("  · KEPT" if kind == "dead" else "  · TAKEN"), mono, 12, GOLD if kind == "dead" else BLOOD)
	var line := _label("“" + String(v["line"]) + "”", serif_i, 18, BONE, true)
	line.custom_minimum_size = Vector2(width, 0)
	box.add_child(who)
	box.add_child(line)
	return box


func voices_changed() -> void:
	for c in chorus_box.get_children():
		c.queue_free()
	var last: Array = G.voices.slice(maxi(0, G.voices.size() - 3))
	for i in last.size():
		var b := _voice(last[i], 470.0)
		b.modulate.a = 0.45 + 0.55 * float(i + 1) / last.size()
		for l in b.get_children():
			(l as Label).horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		chorus_box.add_child(b)
	await get_tree().process_frame
	_layout()


# ---------------------------------------------------------------- in-game text
func refresh(zone: Dictionary, objective: String, mass: int) -> void:
	st_kick.text = ("%s · %s" % [zone["n"], zone["place"]]).to_upper()
	st_name.text = zone["name"]
	st_obj.text = objective
	bal_top.text = "MASS %d    TAKEN %d · KEPT %d" % [mass, G.taken, G.kept]
	var tot := G.taken + G.kept
	bal_fill.size = Vector2(270.0 * (float(G.taken) / tot if tot > 0 else 0.5), 6)
	if tot == 0:
		bal_note.text = "The living give you strength. The dead give you memory."
	elif G.kept >= G.taken:
		bal_note.text = "You remember more than you hunger."
	else:
		bal_note.text = "You hunger more than you remember."
	for a in chips:
		var on: bool = G.ab[a]
		var pc: PanelContainer = chips[a][0]
		var l: Label = chips[a][1]
		pc.add_theme_stylebox_override("panel", _box(Color(0.03, 0.04, 0.07, 0.6), GOLD if on else Color(1, 1, 1, 0.12), 10, 5))
		l.add_theme_color_override("font_color", BONE if on else Color(1, 1, 1, 0.25))


func set_hint(s: String) -> void:
	hint_panel.visible = s != ""
	if s != "" and hint_lbl.text != s:
		hint_lbl.text = s
		hint_panel.reset_size()
		_layout()


func card(kick: String, title: String, body: String, quote: String = "") -> void:
	card_kick.text = kick.to_upper()
	card_title.text = title
	card_quote.text = quote
	card_quote.visible = quote != ""
	card_body.text = body
	card_t = 6.5
	_layout()


func toast(s: String) -> void:
	toast_lbl.text = s
	toast_t = 4.0


func _process(delta: float) -> void:
	if card_box == null:
		return
	var vr := get_viewport_rect().size
	if size != vr:
		position = Vector2.ZERO
		size = vr
	_layout()
	card_t = maxf(0.0, card_t - delta)
	toast_t = maxf(0.0, toast_t - delta)
	card_box.modulate.a = clampf(card_t / 0.8, 0.0, 1.0) if card_t < 6.0 else clampf((6.5 - card_t) / 0.5, 0.0, 1.0)
	toast_lbl.modulate.a = clampf(toast_t / 0.6, 0.0, 1.0)
	if intro_open():
		intro_t -= delta
		intro_lbl.modulate.a = clampf((6.0 - intro_t) / 1.0, 0.0, 1.0) * clampf(intro_t / 0.8, 0.0, 1.0)
		if intro_t <= 0.0:
			advance_intro()
	frenzy_t = maxf(0.0, frenzy_t - delta)
	frenzy_lbl.modulate.a = clampf(frenzy_t / 0.5, 0.0, 1.0)
	frenzy_lbl.scale = frenzy_lbl.scale.lerp(Vector2.ONE, minf(1.0, delta * 8.0))
	ach_t = maxf(0.0, ach_t - delta)
	ach_box.modulate.a = clampf(ach_t / 0.6, 0.0, 1.0)
	region_t = maxf(0.0, region_t - delta)
	region_lbl.modulate.a = clampf(region_t / 0.8, 0.0, 1.0) if region_t < 2.7 else clampf((3.5 - region_t) / 0.6, 0.0, 1.0)
	fb_card_t = maxf(0.0, fb_card_t - delta)
	if fb_ui.visible:
		var head: Control = fb_ui.get_node("head")
		head.modulate.a = clampf(fb_card_t / 1.0, 0.0, 1.0)
	queue_redraw()


func _draw() -> void:
	if game_ui == null or not game_ui.visible or G.fx == null or G.cam == null:
		return
	var svp: SubViewport = G.main.svp
	var vs := Vector2(svp.size)
	var k := size / vs
	var tl := G.cam.get_screen_center_position() - vs * 0.5
	for f in G.fx.floats:
		var p: Vector2 = (f["p"] - tl) * k
		var c: Color = f["c"]
		c.a = clampf(f["t"], 0.0, 1.0)
		draw_string(mono, p + Vector2(-60, 0), f["s"], HORIZONTAL_ALIGNMENT_CENTER, 120, 15, c)
	if G.creature != null and G.creature.dead:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, clampf((2.6 - G.creature.dead_t) * 0.4, 0.0, 0.85)))
	elif G.creature != null and G.creature.inv > 0.0:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.5, 0.0, 0.05, minf(0.12, G.creature.inv * 0.15)))
