##enviroment presets and sequences too

ENVIRONMENT_PRESETS = {
    "Default": {
        "sun_strength": 1.4, "sun_direction": {"x": 0.0, "y": 0.0}, "sun_color": [1.0, 1.0, 1.0],
        "light_color": [1.0, 1.0, 1.0], "dark_color": [0.1, 0.1, 0.1], "fog_enabled": False,
        "fog_color": [0.5, 0.5, 0.5], "fog_start": 1000, "brightness": 0.0, "contrast": 1.0, "desaturation": 0.0
    },
    "Clear Day": {
        "sun_strength": 1.5, "sun_direction": {"x": -45, "y": 60}, "sun_color": [1.2, 1.1, 1.0],
        "light_color": [1.1, 1.05, 1.0], "dark_color": [0.2, 0.2, 0.25], "fog_enabled": False,
        "fog_start": 1000, "brightness": 0, "contrast": 1.1, "desaturation": 0.1
    },
    "Golden Hour": {
        "sun_strength": 2.0, "sun_direction": {"x": 80, "y": 15}, "sun_color": [2.0, 1.2, 0.5],
        "light_color": [1.8, 1.3, 0.8], "dark_color": [0.3, 0.2, 0.1], "fog_enabled": True,
        "fog_color": [1.0, 0.6, 0.4], "fog_start": 1000, "brightness": 0, "contrast": 1.1, "desaturation": 0.0
    },
    "Overcast": {
        "sun_strength": 0.7, "sun_direction": {"x": -30, "y": 70}, "sun_color": [0.8, 0.9, 1.0],
        "light_color": [0.9, 0.95, 1.0], "dark_color": [0.25, 0.25, 0.3], "fog_enabled": True,
        "fog_color": [0.6, 0.6, 0.65], "fog_start": 1000, "brightness": 0, "contrast": 1.1, "desaturation": 0.4
    },
    "Night": {
        "sun_strength": 0.2, "sun_direction": {"x": -90, "y": 45}, "sun_color": [0.1, 0.2, 0.4],
        "light_color": [0.2, 0.3, 0.5], "dark_color": [0.1, 0.1, 0.1], "fog_enabled": False,
        "fog_start": 1000, "brightness": 0, "contrast": 1.1, "desaturation": 0.2
    },
    "Pitch Black": {
        "sun_strength": 0.0, "sun_direction": {"x": 0, "y": 90}, "sun_color": [0.0, 0.0, 0.0],
        "light_color": [0.0, 0.0, 0.0], "dark_color": [0.0, 0.0, 0.0], "fog_enabled": False,
        "brightness": 0, "contrast": 1.0, "desaturation": 1.0
    },
    "Dawn": {
        "sun_strength": 1.8, "sun_direction": {"x": 80, "y": 5}, "sun_color": [1.0, 0.8, 0.6],
        "light_color": [1.0, 0.9, 0.8], "dark_color": [0.6, 0.5, 0.5], "fog_enabled": True,
        "fog_color": [0.9, 0.8, 0.7], "fog_start": 400, "brightness": 0, "contrast": 1.1, "desaturation": 0.15
    },
    "Dusk": {
        "sun_strength": 2.0, "sun_direction": {"x": -80, "y": 10}, "sun_color": [1.0, 0.6, 0.4],
        "light_color": [1.0, 0.7, 0.5], "dark_color": [0.7, 0.4, 0.3], "fog_enabled": True,
        "fog_color": [0.9, 0.6, 0.5], "fog_start": 600, "brightness": 0, "contrast": 1.1, "desaturation": 0.05
    },
    "Typhoon": {
        "sun_strength": 0.4, "sun_direction": {"x": -60, "y": 60}, "sun_color": [0.4, 0.5, 0.6],
        "light_color": [0.5, 0.55, 0.6], "dark_color": [0.2, 0.2, 0.25], "fog_enabled": True,
        "fog_color": [0.3, 0.35, 0.4], "fog_start": 500, "brightness": 0, "contrast": 1.1, "desaturation": 0.7
    },

    # --- Cinematic & Stylistic ---
    "Cinematic Teal & Orange": {
        "sun_strength": 1.6, "sun_direction": {"x": 75, "y": 20}, "sun_color": [1.0, 0.7, 0.4],
        "light_color": [1.0, 0.8, 0.6], "dark_color": [0.1, 0.2, 0.3], "fog_enabled": False,
        "brightness": 0, "contrast": 1.1, "desaturation": 0.1
    },
    "Bleach Bypass": {
        "sun_strength": 1.8, "sun_direction": {"x": -50, "y": 70}, "sun_color": [1.2, 1.2, 1.2],
        "light_color": [1.1, 1.1, 1.1], "dark_color": [0.2, 0.2, 0.2], "fog_enabled": False,
        "brightness": 0, "contrast": 1.1, "desaturation": 0.8
    },
    "Noir Film": {
        "sun_strength": 1.5, "sun_direction": {"x": 70, "y": 30}, "sun_color": [1.0, 1.0, 1.0],
        "light_color": [1.0, 1.0, 1.0], "dark_color": [0.1, 0.1, 0.1], "fog_enabled": True,
        "fog_color": [0.5, 0.5, 0.5], "fog_start": 1000, "brightness": 0, "contrast": 1.1, "desaturation": 1.0
    },
    "Dreamscape": {
        "sun_strength": 1.5, "sun_direction": {"x": 80, "y": 40}, "sun_color": [1.0, 0.8, 0.9],
        "light_color": [1.2, 0.9, 1.1], "dark_color": [0.2, 0.2, 0.3], "fog_enabled": True,
        "fog_color": [0.9, 0.8, 0.85], "fog_start": 1000, "brightness": 0, "contrast": 1.0, "desaturation": 0.1
    },
    "Psychedelic Trip": {
        "sun_strength": 2.0, "sun_direction": {"x": 0, "y": 45}, "sun_color": [2.0, 0.0, 1.0],
        "light_color": [0.0, 2.0, 1.0], "dark_color": [1.0, 1.0, 0.0], "fog_enabled": False,
        "brightness": 0, "contrast": 1.1, "desaturation": 0.0
    },
    "Vaporwave Dream": {
        "sun_strength": 2.0, "sun_direction": {"x": -80, "y": 25}, "sun_color": [2.0, 0.5, 1.5],
        "light_color": [0.5, 1.5, 2.0], "dark_color": [0.2, 0.1, 0.3], "fog_enabled": True,
        "fog_color": [0.5, 0.1, 0.4], "fog_start": 1000, "brightness": 0, "contrast": 1.1, "desaturation": 0.0
    },
    "Apocalypse Orange": {
        "sun_strength": 2.2, "sun_direction": {"x": 60, "y": 10}, "sun_color": [1.0, 0.6, 0.2],
        "light_color": [1.0, 0.7, 0.3], "dark_color": [0.3, 0.2, 0.1], "fog_enabled": True,
        "fog_color": [1.0, 0.6, 0.2], "fog_start": 1000, "brightness": 0, "contrast": 1.1, "desaturation": 0.4
    },

    # --- Scary & Eerie (THICK FOG) ---
    "Silent Hill": {
        "sun_strength": 0.4, "sun_direction": {"x": 10, "y": 30}, "sun_color": [0.7, 0.6, 0.5],
        "light_color": [0.8, 0.7, 0.6], "dark_color": [0.2, 0.2, 0.2], "fog_enabled": True,
        "fog_color": [0.5, 0.45, 0.4], "fog_start": 50, "brightness": 0, "contrast": 1.1, "desaturation": 0.8,
        "flicker": {"preset": "Candle", "speed": 1200, "easing": True}
    },
    "Blood Moon": {
        "sun_strength": 1.2, "sun_direction": {"x": 20, "y": 25}, "sun_color": [1.0, 0.1, 0.1],
        "light_color": [0.9, 0.2, 0.2], "dark_color": [0.2, 0.1, 0.1], "fog_enabled": True,
        "fog_color": [0.4, 0.05, 0.05], "fog_start": 1000, "brightness": 0, "contrast": 1.1, "desaturation": 0.5
    },
    "Abandoned Hospital": {
        "sun_strength": 0.3, "sun_direction": {"x": -70, "y": 80}, "sun_color": [0.6, 0.8, 0.7],
        "light_color": [0.7, 0.9, 0.8], "dark_color": [0.1, 0.15, 0.15], "fog_enabled": True,
        "fog_color": [0.4, 0.5, 0.45], "fog_start": 600, "brightness": 0, "contrast": 1.1, "desaturation": 0.6,
        "flicker": {"preset": "Pulse", "speed": 2000, "easing": True}
    },
    "Basement Interrogation": {
        "sun_strength": 0.8, "sun_direction": {"x": 0, "y": 85}, "sun_color": [1.0, 0.9, 0.7],
        "light_color": [0.3, 0.3, 0.25], "dark_color": [0.1, 0.1, 0.1], "fog_enabled": False,
        "brightness": -0.1, "contrast": 1.1, "desaturation": 0.7,
        "flicker": {"preset": "Heartbeat", "speed": 900}
    },
    "Cursed Swamp": {
        "sun_strength": 0.2, "sun_direction": {"x": 40, "y": 20}, "sun_color": [0.4, 0.5, 0.3],
        "light_color": [0.5, 0.6, 0.4], "dark_color": [0.1, 0.15, 0.1], "fog_enabled": True,
        "fog_color": [0.2, 0.3, 0.15], "fog_start": 100, "brightness": -0.1, "contrast": 1.1, "desaturation": 0.5
    },
    "Verrückt Asylum": {
        "sun_strength": 0.4, "sun_direction": {"x": 10, "y": 80}, "sun_color": [0.6, 0.7, 0.5],
        "light_color": [0.7, 0.8, 0.7], "dark_color": [0.15, 0.2, 0.15], "fog_enabled": True,
        "fog_color": [0.2, 0.25, 0.2], "fog_start": 800, "brightness": -0.2, "contrast": 1.2, "desaturation": 0.4,
        "flicker": {"preset": "Faulty", "speed": 2000, "easing": True}
    },
    "Deep Sea Trench": {
        "sun_strength": 0.5, "sun_direction": {"x": 0, "y": 90}, "sun_color": [0.0, 0.2, 0.5],
        "light_color": [0.1, 0.3, 0.6], "dark_color": [0.1, 0.1, 0.1], "fog_enabled": True,
        "fog_color": [0.0, 0.05, 0.1], "fog_start": 80, "brightness": 0, "contrast": 1.1, "desaturation": 0.2
    },
    "Dying Star": {
        "sun_strength": 4.0, "sun_direction": {"x": 0, "y": 20}, "sun_color": [2.0, 0.1, 0.1],
        "light_color": [2.0, 0.3, 0.2], "dark_color": [0.1, 0.1, 0.1], "fog_enabled": True,
        "fog_color": [0.5, 0.0, 0.0], "fog_start": 1000, "brightness": -0.2, "contrast": 1.1, "desaturation": 0.1
    },
    "Interstellar Void": {
        "sun_strength": 0.1, "sun_direction": {"x": 0, "y": 0}, "sun_color": [0.1, 0.1, 0.2],
        "light_color": [0.1, 0.1, 0.2], "dark_color": [0.1, 0.1, 0.1], "fog_enabled": False,
        "brightness": 0, "contrast": 1.0, "desaturation": 0.5
    },

    # --- WaW Campaign Inspired ---
    "Stalingrad Winter": {
        "sun_strength": 0.6, "sun_direction": {"x": 30, "y": 35}, "sun_color": [0.7, 0.8, 0.9],
        "light_color": [0.8, 0.85, 0.9], "dark_color": [0.2, 0.2, 0.25], "fog_enabled": True,
        "fog_color": [0.7, 0.7, 0.75], "fog_start": 1000, "brightness": -0.2, "contrast": 1.1, "desaturation": 0.6
    },
    "Berlin in Flames": {
        "sun_strength": 3.0, "sun_direction": {"x": 60, "y": 20}, "sun_color": [2.0, 0.8, 0.2],
        "light_color": [1.8, 0.9, 0.3], "dark_color": [0.2, 0.1, 0.1], "fog_enabled": True,
        "fog_color": [0.3, 0.15, 0.05], "fog_start": 1000, "brightness": -0.3, "contrast": 1.1, "desaturation": 0.1,
        "flicker": {"preset": "Candle", "speed": 150, "easing": True}
    },
    "Peleliu Aftermath": {
        "sun_strength": 1.8, "sun_direction": {"x": -20, "y": 75}, "sun_color": [1.2, 1.1, 0.9],
        "light_color": [1.1, 1.0, 0.9], "dark_color": [0.25, 0.2, 0.2], "fog_enabled": True,
        "fog_color": [0.8, 0.75, 0.7], "fog_start": 1000, "brightness": 0.15, "contrast": 1.1, "desaturation": 0.5
    },
    "Jungle Night Assault": {
        "sun_strength": 0.1, "sun_direction": {"x": -120, "y": 40}, "sun_color": [0.05, 0.1, 0.2],
        "light_color": [0.1, 0.15, 0.25], "dark_color": [0.1, 0.1, 0.1], "fog_enabled": True,
        "fog_color": [0.0, 0.05, 0.02], "fog_start": 300, "brightness": 0, "contrast": 1.1, "desaturation": 0.3
    },
    "Mustard Gas": {
        "sun_strength": 1.0, "sun_direction": {"x": 25, "y": 50}, "sun_color": [1.0, 1.0, 0.4],
        "light_color": [1.0, 1.0, 0.6], "dark_color": [0.3, 0.3, 0.1], "fog_enabled": True,
        "fog_color": [0.6, 0.6, 0.2], "fog_start": 50, "brightness": 0.0, "contrast": 1.1, "desaturation": 0.3
    },
    "Wartime Trenches": {
        "sun_strength": 0.8, "sun_direction": {"x": 15, "y": 60}, "sun_color": [0.7, 0.65, 0.6],
        "light_color": [0.7, 0.65, 0.6], "dark_color": [0.3, 0.3, 0.3], "fog_enabled": True,
        "fog_color": [0.5, 0.45, 0.4], "fog_start": 1000, "brightness": 0.0, "contrast": 1.1, "desaturation": 0.9
    },
    "Arctic Blizzard": {
        "sun_strength": 1.5, "sun_direction": {"x": 0, "y": 60}, "sun_color": [0.9, 0.9, 1.0],
        "light_color": [0.95, 0.95, 1.0], "dark_color": [0.7, 0.7, 0.75], "fog_enabled": True,
        "fog_color": [0.95, 0.95, 1.0], "fog_start": 80, "brightness": 0, "contrast": 1.0, "desaturation": 0.8
    },
    "Hellscape": {
        "sun_strength": 3.0, "sun_direction": {"x": 0, "y": 30}, "sun_color": [2.0, 0.2, 0.0],
        "light_color": [2.0, 0.3, 0.0], "dark_color": [0.2, 0.1, 0.1], "fog_enabled": True,
        "fog_color": [0.5, 0.1, 0.0], "fog_start": 1000, "brightness": 0, "contrast": 1.1, "desaturation": 0.1,
        "flicker": {"preset": "Candle", "speed": 100, "easing": True}
    },
}

# ==================================================================================================
# ANIMATION PRESETS
# ==================================================================================================
ENHANCED_ANIMATION_PRESETS = {}

# ==================================================================================================
# SEQUENCE PRESETS
# ==================================================================================================
SEQUENCE_PRESETS = {
    "Sunrise to Sunset": [
        {"type": "environment", "name": "Night"},
        {"type": "animation", "preset": "Sunrise", "wait_for_completion": True},
        {"type": "wait", "value": 3000},
        {"type": "animation", "preset": "Noon", "wait_for_completion": True},
        {"type": "wait", "value": 3000},
        {"type": "animation", "preset": "Sunset", "wait_for_completion": True},
        {"type": "transition", "to": "Night", "duration": 4000},
    ],
    "Bombing Raid": [
        {"type": "environment", "name": "Overcast"},
        {"type": "wait", "value": 3000},
        {"type": "transition", "to": "Berlin in Flames", "duration": 2000},
        {"type": "wait", "value": 10000},
        {"type": "transition", "to": "Peleliu Aftermath", "duration": 5000},
    ],
    "Gas Attack": [
        {"type": "environment", "name": "Stalingrad Winter"},
        {"type": "wait", "value": 4000},
        {"type": "transition", "to": "Mustard Gas", "duration": 1500},
        {"type": "wait", "value": 8000},
        {"type": "transition", "to": "Stalingrad Winter", "duration": 6000},
    ],
    "Descent into Madness": [
        {"type": "environment", "name": "Clear Day"},
        {"type": "transition", "to": "Overcast", "duration": 3000},
        {"type": "transition", "to": "Silent Hill", "duration": 4000},
        {"type": "flicker", "preset": "Heartbeat"},
    ],
    "System Glitch": [
        {"type": "environment", "name": "Clear Day"},
        {"type": "wait", "value": 1000},
        {"type": "flicker", "preset": "Strobe"},
        {"type": "wait", "value": 100},
        {"type": "stop_effects"},
        {"type": "transition", "to": "Matrix", "duration": 500},
    ],
    "Nuclear Detonation": [
        {"type": "environment", "name": "Clear Day"},
        {"type": "wait", "value": 5000},
        {"type": "command", "value": "r_lighttweaksunlight 10.0"},
        {"type": "command", "value": "r_filmtweakbrightness 1.0"},
        {"type": "wait", "value": 150},
        {"type": "stop_effects"},
        {"type": "wait", "value": 500},
        {"type": "transition", "to": "Apocalypse Orange", "duration": 1000},
        {"type": "flicker", "preset": "Storm"},
        {"type": "wait", "value": 12000},
        {"type": "stop_effects"},
        {"type": "transition", "to": "Nuclear Winter", "duration": 8000},
    ],
    "Artillery Barrage": [
        {"type": "environment", "name": "Peleliu Aftermath"},
        {"type": "flicker", "preset": "Storm"},
        {"type": "wait", "value": 20000},
        {"type": "stop_effects"},
    ],
    "Asylum Lockdown": [
        {"type": "environment", "name": "Verrückt Asylum"},
        {"type": "wait", "value": 7000},
        {"type": "stop_effects"},
        {"type": "transition", "to": "Pitch Black", "duration": 200},
        {"type": "wait", "value": 2000},
        {"type": "flicker", "preset": "Strobe"},
        {"type": "wait", "value": 70},
        {"type": "stop_effects"},
    ],
    "The Summoning": [
        {"type": "environment", "name": "Night"},
        {"type": "transition", "to": "Blood Moon", "duration": 8000},
        {"type": "wait", "value": 4000},
        {"type": "flicker", "preset": "Storm"},
    ],
    "Trench Night Flare": [
        {"type": "environment", "name": "Wartime Trenches"},
        {"type": "transition", "to": "Night", "duration": 1000},
        {"type": "wait", "value": 5000},
        {"type": "command", "value": "r_lighttweaksunlight 10.0"},
        {"type": "command", "value": "r_filmtweakbrightness 1.0"},
        {"type": "wait", "value": 150},
        {"type": "transition", "to": "Bleach Bypass", "duration": 500},
        {"type": "wait", "value": 7000},
        {"type": "transition", "to": "Night", "duration": 2000},
    ],
    "Der Riese Teleporter": [
        {"type": "environment", "name": "Overcast"},
        {"type": "flicker", "preset": "Pulse"},
        {"type": "wait", "value": 3000},
        {"type": "stop_effects"},
        {"type": "flicker", "preset": "Strobe"},
        {"type": "wait", "value": 2000},
        {"type": "command", "value": "r_lighttweaksunlight 10.0"},
        {"type": "wait", "value": 100},
        {"type": "transition", "to": "Hellscape", "duration": 500},
    ],
    "Deep Sea Horror": [
        {"type": "environment", "name": "Deep Sea Trench"},
        {"type": "wait", "value": 6000},
        {"type": "flicker", "preset": "Heartbeat"},
        {"type": "wait", "value": 8000},
        {"type": "transition", "to": "Blood Moon", "duration": 100},
        {"type": "flicker", "preset": "Strobe"},
        {"type": "wait", "value": 200},
        {"type": "stop_effects"},
    ],
    "Forest Abduction": [
        {"type": "environment", "name": "Night"},
        {"type": "wait", "value": 5000},
        {"type": "flicker", "preset": "Pulse"},
        {"type": "transition", "to": "Alien World", "duration": 3000},
        {"type": "wait", "value": 4000},
        {"type": "stop_effects"},
    ],
    "Supernova Collapse": [
        {"type": "environment", "name": "Dying Star"},
        {"type": "wait", "value": 8000},
        {"type": "command", "value": "r_filmtweakbrightness 1.0"},
        {"type": "wait", "value": 80},
        {"type": "stop_effects"},
        {"type": "transition", "to": "Interstellar Void", "duration": 2000},
    ],
    "Air Raid": [
        {"type": "environment", "name": "Dusk"},
        {"type": "wait", "value": 3000},
        {"type": "transition", "to": "Apocalypse Orange", "duration": 2000},
        {"type": "flicker", "preset": "Faulty"},
        {"type": "wait", "value": 5000},
        {"type": "stop_effects"},
        {"type": "flicker", "preset": "Storm"},
    ],
    "Bad Trip": [
        {"type": "environment", "name": "Dreamscape"},
        {"type": "wait", "value": 4000},
        {"type": "transition", "to": "Psychedelic Trip", "duration": 1000},
        {"type": "flicker", "preset": "Strobe"},
    ],
    "Ambush!": [
        {"type": "environment", "name": "Golden Hour"},
        {"type": "wait", "value": 5000},
        {"type": "flicker", "preset": "Storm"},
        {"type": "transition", "to": "Berlin in Flames", "duration": 200},
    ],
    "Pacific Typhoon": [
        {"type": "environment", "name": "Clear Day"},
        {"type": "transition", "to": "Overcast", "duration": 10000},
        {"type": "transition", "to": "Typhoon", "duration": 5000},
        {"type": "flicker", "preset": "Storm"},
        {"type": "wait", "value": 15000},
        {"type": "stop_effects"},
        {"type": "transition", "to": "Bleach Bypass", "duration": 3000},
        {"type": "wait", "value": 5000},
        {"type": "transition", "to": "Typhoon", "duration": 3000},
        {"type": "flicker", "preset": "Storm"},
    ],
    "Haunting": [
        {"type": "environment", "name": "Basement Interrogation"},
        {"type": "wait", "value": 10000},
        {"type": "stop_effects"},
        {"type": "wait", "value": 3000},
        {"type": "flicker", "preset": "Storm"},
        {"type": "transition", "to": "Blood Moon", "duration": 100},
        {"type": "wait", "value": 5000},
        {"type": "transition", "to": "Pitch Black", "duration": 1000},
    ],
}