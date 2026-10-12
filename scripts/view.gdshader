shader_type canvas_item;
// Post effect for the game view: sepia memories, lantern light in the dark,
// and a soft light around the creature underground.

uniform float sepia : hint_range(0.0, 1.0) = 0.0;
uniform float dark : hint_range(0.0, 1.0) = 0.0;
uniform vec2 light_uv = vec2(0.5, 0.5);
uniform float light_r = 0.3;
uniform float aspect = 1.7778;
uniform float fade : hint_range(0.0, 1.0) = 0.0;
uniform float time = 0.0;

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	float l = dot(c.rgb, vec3(0.299, 0.587, 0.114));
	vec3 sep = vec3(l * 1.08, l * 0.9, l * 0.68);
	c.rgb = mix(c.rgb, sep, sepia);
	vec2 d = UV - light_uv;
	d.x *= aspect;
	float flicker = 1.0 + 0.05 * sin(time * 13.0) + 0.03 * sin(time * 7.3);
	float m = smoothstep(light_r * flicker, light_r * 0.3, length(d));
	c.rgb *= mix(1.0 - dark, 1.0, m);
	vec2 v = (UV - 0.5) * vec2(aspect, 1.0);
	c.rgb *= mix(1.0, smoothstep(1.05, 0.35, length(v)), sepia * 0.7);
	float n = fract(sin(dot(floor(UV * vec2(480.0, 270.0)) + floor(time * 24.0), vec2(12.9898, 78.233))) * 43758.5453);
	c.rgb += (n - 0.5) * 0.07 * sepia;
	c.rgb *= 1.0 - fade;
	COLOR = c;
}
