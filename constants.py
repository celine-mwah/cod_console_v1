## profiles for the other cods - eventually this tool should work for mw2, bo1 as well
GAME_PROFILES = {
    "CoDWaWmp.exe": {
        "friendly_name": "Call of Duty: World at War",
        "cbuf_addtext": 0x0055C000 ## german binary - the english one doesnt work with
    },
    "iw4m.exe": {
        "friendly_name": "Call of Duty: Modern Warfare 2",
        "cbuf_addtext": 0x0404B2B ## iw4m.exe
    },
    "BlackOpsMP.exe": {
        "friendly_name": "Call of Duty: Black Ops",
        "cbuf_addtext": 0x00624850
    }
}


#defaults
MEMORY_MAP = {
    "defaults": {
        "brightness": 0.0,
        "contrast": 1.4,
        "desaturation": 0.2,
        "fov": 65.0,
        "sun_strength": 1.4,
        "sun_direction_x": 0.0,
        "sun_direction_y": 0.0,
        "color_map": 1,
        "light_map": 1,
        "debug_shader": 0,
        "filmtweaks_enabled": False,
        "light_color": [1.0, 1.0, 1.0],
        "dark_color": [1.0, 1.0, 1.0],
        "sun_color": [1.0, 1.0, 1.0],
        "fog_enabled": False,
        "fog_color": [1.0, 1.0, 1.0],
        "fog_start": 250.0,
        "dof_enabled": False,
        "glow_enabled": False,
    }
}