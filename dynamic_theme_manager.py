import dearpygui.dearpygui as dpg
import math
import time
import threading
import colorsys
import json
import os


class DynamicThemeManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.current_theme = "Default"
        self.animation_thread = None
        self.stop_animation = False

        ## themes
        self.color_schemes = {
            "Default": {
                "primary": [255, 105, 180],
                "secondary": [255, 255, 0],
                "background": [40, 40, 40],
                "surface": [25, 25, 25],
                "text": [255, 255, 255],
                "accent": [100, 200, 255]
            },
            "Yelvis": {
                "primary": [255, 183, 197],
                "secondary": [187, 222, 251],
                "background": [235, 200, 225],
                "surface": [252, 240, 244],
                "text": [50, 40, 45],
                "accent": [255, 105, 180]
            },
            "Ocean": {
                "primary": [0, 150, 255],
                "secondary": [0, 255, 200],
                "background": [10, 25, 40],
                "surface": [15, 35, 55],
                "text": [220, 240, 255],
                "accent": [100, 255, 255]
            },
            "Sunset": {
                "primary": [255, 100, 50],
                "secondary": [255, 200, 100],
                "background": [40, 20, 20],
                "surface": [60, 30, 30],
                "text": [255, 240, 220],
                "accent": [255, 150, 100]
            },
            "Forest": {
                "primary": [100, 200, 100],
                "secondary": [200, 255, 150],
                "background": [20, 30, 20],
                "surface": [30, 45, 30],
                "text": [240, 255, 240],
                "accent": [150, 255, 100]
            },
            "Cyberpunk": {
                "primary": [255, 0, 255],
                "secondary": [0, 255, 255],
                "background": [10, 0, 20],
                "surface": [25, 10, 35],
                "text": [255, 200, 255],
                "accent": [255, 100, 255]
            },
            "Custom": {}
        }

        self.rainbow_mode = True
        self.pulse_mode = False
        self.reactive_mode = False
        self.color_transition_speed = 3.0

        self.original_theme = self.color_schemes["Default"].copy()

        self._start_rainbow_animation()

    def create_theme_ui(self, parent_tag):
        with dpg.collapsing_header(label="Theme Settings", default_open=False, parent=parent_tag):
            dpg.add_combo(
                label="Color Scheme",
                tag="theme_selector",
                items=list(self.color_schemes.keys()),
                default_value=self.current_theme,
                callback=self._apply_theme,
                width=200
            )

            dpg.add_separator()

            dpg.add_text("Dynamic Effects", color=(255, 255, 0))
            with dpg.group(horizontal=True):
                dpg.add_checkbox(
                    label="Rainbow Mode",
                    tag="rainbow_mode_check",
                    default_value=self.rainbow_mode,  # Use the class variable for default
                    callback=self._toggle_rainbow_mode
                )
                dpg.add_checkbox(
                    label="Pulse Mode",
                    tag="pulse_mode_check",
                    callback=self._toggle_pulse_mode
                )
                dpg.add_checkbox(
                    label="Reactive Mode",
                    tag="reactive_mode_check",
                    callback=self._toggle_reactive_mode
                )

            dpg.add_slider_float(
                label="Animation Speed",
                tag="color_transition_speed",
                min_value=0.1,
                max_value=5.0,
                default_value=1.0,
                callback=self._update_animation_speed,
                width=200
            )

            dpg.add_separator()

            dpg.add_text("Custom Colors", color=(255, 255, 0))
            with dpg.group(horizontal=True):
                with dpg.child_window(width=250, height=200):
                    dpg.add_color_edit(
                        label="Primary",
                        tag="custom_primary_color",
                        no_alpha=True,
                        default_value=[255 / 255, 105 / 255, 180 / 255],
                        callback=lambda s, d: self._update_custom_color("primary", d)
                    )
                    dpg.add_color_edit(
                        label="Secondary",
                        tag="custom_secondary_color",
                        no_alpha=True,
                        default_value=[255 / 255, 255 / 255, 0 / 255],
                        callback=lambda s, d: self._update_custom_color("secondary", d)
                    )
                    dpg.add_color_edit(
                        label="Accent",
                        tag="custom_accent_color",
                        no_alpha=True,
                        default_value=[100 / 255, 200 / 255, 255 / 255],
                        callback=lambda s, d: self._update_custom_color("accent", d)
                    )

                with dpg.child_window(width=300, height=200):
                    dpg.add_color_edit(
                        label="Background",
                        tag="custom_background_color",
                        no_alpha=True,
                        default_value=[40 / 255, 40 / 255, 40 / 255],
                        callback=lambda s, d: self._update_custom_color("background", d)
                    )
                    dpg.add_color_edit(
                        label="Surface",
                        tag="custom_surface_color",
                        no_alpha=True,
                        default_value=[25 / 255, 25 / 255, 25 / 255],
                        callback=lambda s, d: self._update_custom_color("surface", d)
                    )
                    dpg.add_color_edit(
                        label="Text",
                        tag="custom_text_color",
                        no_alpha=True,
                        default_value=[255 / 255, 255 / 255, 255 / 255],
                        callback=lambda s, d: self._update_custom_color("text", d)
                    )

            with dpg.group(horizontal=True):
                dpg.add_button(label="Save Theme", callback=self._save_theme_to_file, width=90)
                dpg.add_button(label="Load Theme", callback=self._load_theme_from_file, width=90)
                dpg.add_button(label="Reset to Default", callback=self._reset_to_default, width=120)


    def _apply_theme(self, sender=None, theme_name=None):
        if theme_name is None:
            theme_name = dpg.get_value("theme_selector") if dpg.does_item_exist("theme_selector") else "Default"

        is_dynamic_theme_running = self.rainbow_mode or self.pulse_mode or self.reactive_mode
        if theme_name != "Custom" or not is_dynamic_theme_running:
            self._stop_animation()
            self.rainbow_mode = False
            self.pulse_mode = False
            self.reactive_mode = False
            if dpg.does_item_exist("rainbow_mode_check"):
                dpg.set_value("rainbow_mode_check", False)
            if dpg.does_item_exist("pulse_mode_check"):
                dpg.set_value("pulse_mode_check", False)
            if dpg.does_item_exist("reactive_mode_check"):
                dpg.set_value("reactive_mode_check", False)

        if theme_name not in self.color_schemes:
            return

        self.current_theme = theme_name
        colors = self.color_schemes[theme_name]

        if not colors:
            return

        with dpg.theme() as dynamic_theme:
            with dpg.theme_component(dpg.mvAll):
                if "text" in colors:
                    dpg.add_theme_color(dpg.mvThemeCol_Text, colors["text"])

                if "primary" in colors:
                    dpg.add_theme_color(dpg.mvThemeCol_Button, [min(255, c * 0.8) for c in colors["primary"]])
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, colors["primary"])
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [min(255, c * 1.2) for c in colors["primary"]])

                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, colors["primary"])
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, [min(255, c * 1.2) for c in colors["primary"]])
                    dpg.add_theme_color(dpg.mvThemeCol_CheckMark, colors["primary"])
                    dpg.add_theme_color(dpg.mvThemeCol_Header, colors["primary"])
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, [min(255, c * 1.2) for c in colors["primary"]])
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, [min(255, c * 1.4) for c in colors["primary"]])

                if "surface" in colors:
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, colors["surface"])
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, [min(255, c * 1.2) for c in colors["surface"]])
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, [min(255, c * 1.4) for c in colors["surface"]])

                    dpg.add_theme_color(dpg.mvThemeCol_Tab, colors["surface"])
                    dpg.add_theme_color(dpg.mvThemeCol_TabActive, [min(255, c * 1.5) for c in colors["surface"]])
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBg, colors["surface"])
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, [min(255, c * 1.5) for c in colors["surface"]])

                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)
                dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 10)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 10)

            with dpg.theme_component(dpg.mvWindowAppItem):
                if "background" in colors:
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, colors["background"])

        dpg.bind_theme(dynamic_theme)

        if theme_name != "Custom":
            self._update_color_pickers(colors)

    def _update_custom_color(self, color_type, color_value):
        rgb_color = [int(c * 255) for c in color_value[:3]]

        if "Custom" not in self.color_schemes:
            self.color_schemes["Custom"] = {}

        self.color_schemes["Custom"][color_type] = rgb_color

        if dpg.does_item_exist("theme_selector"):
            dpg.set_value("theme_selector", "Custom")

        if self.current_theme == "Custom":
            self._apply_theme(theme_name="Custom")

    ## Animation modes
    def _toggle_rainbow_mode(self, sender, app_data):
        self.rainbow_mode = app_data
        if app_data:
            self.pulse_mode = False
            self.reactive_mode = False
            if dpg.does_item_exist("pulse_mode_check"):
                dpg.set_value("pulse_mode_check", False)
            if dpg.does_item_exist("reactive_mode_check"):
                dpg.set_value("reactive_mode_check", False)
            self._start_rainbow_animation()
        else:
            self._stop_animation()

    def _toggle_pulse_mode(self, sender, app_data):
        self.pulse_mode = app_data
        if app_data:
            self.rainbow_mode = False
            self.reactive_mode = False
            if dpg.does_item_exist("rainbow_mode_check"):
                dpg.set_value("rainbow_mode_check", False)
            if dpg.does_item_exist("reactive_mode_check"):
                dpg.set_value("reactive_mode_check", False)
            self._start_pulse_animation()
        else:
            self._stop_animation()

    def _toggle_reactive_mode(self, sender, app_data):
        self.reactive_mode = app_data
        if app_data:
            self.rainbow_mode = False
            self.pulse_mode = False
            if dpg.does_item_exist("rainbow_mode_check"):
                dpg.set_value("rainbow_mode_check", False)
            if dpg.does_item_exist("pulse_mode_check"):
                dpg.set_value("pulse_mode_check", False)
            self._start_reactive_mode()
        else:
            self._stop_animation()

    def _start_rainbow_animation(self):
        self._stop_animation()
        self.stop_animation = False

        if dpg.does_item_exist("theme_selector"):
            dpg.set_value("theme_selector", "Custom")

        def rainbow_worker():
            hue = 0
            base = self.color_schemes["Default"].copy()
            while not self.stop_animation and self.rainbow_mode:
                rgb = colorsys.hsv_to_rgb(hue / 360.0, 0.7, 1.0)
                primary_color = [int(c * 255) for c in rgb]

                comp_hue = (hue + 180) % 360
                rgb_comp = colorsys.hsv_to_rgb(comp_hue / 360.0, 0.7, 1.0)
                secondary_color = [int(c * 255) for c in rgb_comp]

                self.color_schemes["Custom"]["primary"] = primary_color
                self.color_schemes["Custom"]["secondary"] = secondary_color
                self.color_schemes["Custom"]["accent"] = secondary_color
                for key, value in base.items():
                    if key not in self.color_schemes["Custom"]:
                        self.color_schemes["Custom"][key] = value

                self._apply_theme(theme_name="Custom")

                hue = (hue + self.color_transition_speed) % 360
                time.sleep(0.05)

        self.animation_thread = threading.Thread(target=rainbow_worker)
        self.animation_thread.daemon = True
        self.animation_thread.start()

    def _start_pulse_animation(self):
        self._stop_animation()
        self.stop_animation = False

        if dpg.does_item_exist("theme_selector"):
            dpg.set_value("theme_selector", "Custom")

        def pulse_worker():
            phase = 0
            base_colors = self.color_schemes.get(self.current_theme, self.color_schemes["Default"]).copy()
            if not base_colors or 'primary' not in base_colors:
                base_colors = self.color_schemes["Default"].copy()

            while not self.stop_animation and self.pulse_mode:
                intensity = (math.sin(phase) + 1) / 2

                pulsed_primary = [
                    int(base_colors["primary"][i] * (0.5 + intensity * 0.5))
                    for i in range(3)
                ]

                self.color_schemes["Custom"] = base_colors.copy()
                self.color_schemes["Custom"]["primary"] = pulsed_primary
                self._apply_theme(theme_name="Custom")

                phase += 0.1 * self.color_transition_speed
                time.sleep(0.05)

        self.animation_thread = threading.Thread(target=pulse_worker)
        self.animation_thread.daemon = True
        self.animation_thread.start()

    def _start_reactive_mode(self):
        self._stop_animation()
        self.stop_animation = False

        if dpg.does_item_exist("theme_selector"):
            dpg.set_value("theme_selector", "Custom")

        def reactive_worker():
            while not self.stop_animation and self.reactive_mode:
                if hasattr(self.app, 'sun_animator') and self.app.sun_animator.is_animating:
                    reactive_colors = self.color_schemes.get("Sunset", self.original_theme)
                elif hasattr(self.app, 'memory_manager') and not self.app.memory_manager.is_connected():
                    reactive_colors = {"primary": [255, 50, 50], "secondary": [255, 150, 150],
                                       "background": [40, 20, 20], "surface": [50, 25, 25], "text": [255, 200, 200],
                                       "accent": [255, 100, 100]}
                else:
                    reactive_colors = self.color_schemes.get("Ocean", self.original_theme)

                self.color_schemes["Custom"] = reactive_colors
                self._apply_theme(theme_name="Custom")
                time.sleep(0.5)

        self.animation_thread = threading.Thread(target=reactive_worker)
        self.animation_thread.daemon = True
        self.animation_thread.start()

    def _update_animation_speed(self, sender, app_data):
        self.color_transition_speed = app_data

    def _stop_animation(self):
        self.stop_animation = True
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=0.5)

    def _update_color_pickers(self, colors):
        for color_type, color_value in colors.items():
            picker_tag = f"custom_{color_type}_color"
            if dpg.does_item_exist(picker_tag):
                normalized_color = [c / 255.0 for c in color_value[:3]]
                dpg.set_value(picker_tag, normalized_color)

    ## theme saving
    def _save_theme_to_file(self):
        theme_data = {
            "current_theme": self.current_theme,
            "color_schemes": self.color_schemes,
            "animation_settings": {
                "rainbow_mode": self.rainbow_mode,
                "pulse_mode": self.pulse_mode,
                "reactive_mode": self.reactive_mode,
                "transition_speed": self.color_transition_speed
            }
        }

        theme_file = "custom_theme.json"
        try:
            with open(theme_file, 'w') as f:
                json.dump(theme_data, f, indent=2)
            if hasattr(self.app, '_add_debug_message'):
                self.app._add_debug_message(f"Theme saved to {theme_file}")
        except Exception as e:
            if hasattr(self.app, '_add_debug_message'):
                self.app._add_debug_message(f"Error saving theme: {e}", is_error=True)

    def _load_theme_from_file(self):
        theme_file = "custom_theme.json"
        try:
            if os.path.exists(theme_file):
                with open(theme_file, 'r') as f:
                    theme_data = json.load(f)

                self.color_schemes.update(theme_data.get("color_schemes", {}))
                settings = theme_data.get("animation_settings", {})

                loaded_theme = theme_data.get("current_theme", "Default")
                if dpg.does_item_exist("theme_selector"):
                    dpg.configure_item("theme_selector", items=list(self.color_schemes.keys()))
                    dpg.set_value("theme_selector", loaded_theme)
                self._apply_theme(theme_name=loaded_theme)

                if hasattr(self.app, '_add_debug_message'):
                    self.app._add_debug_message(f"Theme loaded from {theme_file}")
        except Exception as e:
            if hasattr(self.app, '_add_debug_message'):
                self.app._add_debug_message(f"Error loading theme: {e}", is_error=True)

    def _reset_to_default(self):
        self._stop_animation()
        self.rainbow_mode = False
        self.pulse_mode = False
        self.reactive_mode = False

        for check_tag in ["rainbow_mode_check", "pulse_mode_check", "reactive_mode_check"]:
            if dpg.does_item_exist(check_tag):
                dpg.set_value(check_tag, False)

        if dpg.does_item_exist("theme_selector"):
            dpg.set_value("theme_selector", "Default")
        self._apply_theme(theme_name="Default")