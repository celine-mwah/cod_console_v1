import dearpygui.dearpygui as dpg
import datetime
import os
import sys
import time
import threading
import copy
import re

from memory_manager import MemoryManager
from sun_animation import SunAnimationSystem, SunFlickerSystem
from config_manager import save_config, load_config, list_config_files
from constants import MEMORY_MAP
from preset_manager import PresetManager
from sequence_builder import SequenceBuilder
from history_manager import HistoryManager, ModifyKeyframesAction
from hotkey_manager import HotkeyManager
from action_manager import ActionManager
from weather_presets import ENVIRONMENT_PRESETS, SEQUENCE_PRESETS
from keyframe_editor import EnhancedKeyframeEditor
from dynamic_theme_manager import DynamicThemeManager


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class WAW_App_DPG:
    def __init__(self):
        self.debug_messages = []
        self.max_debug_lines = 100
        self.memory_manager = MemoryManager()
        self.memory_manager.set_debug_callback(self._add_debug_message)
        self._init_ui_vars_map()
        self._check_initial_status()

        self.sun_animator = SunAnimationSystem(
            self.memory_manager,
            self._update_ui_from_animation
        )
        self.sun_flicker = SunFlickerSystem(self.memory_manager)
        self.sequence_builder = SequenceBuilder(self, self._add_debug_message)
        self.action_manager = ActionManager(self.memory_manager, self._add_debug_message)

        self.theme_manager = DynamicThemeManager(self)

        self.history_manager = HistoryManager(self)
        self.keyframe_clipboard = []
        self.current_keyframes = []
        self.easing_options = ["Linear", "Smooth", "Ease-In", "Ease-Out"]
        self.easing_functions = {
            "Linear": lambda t: t,
            "Smooth": SunAnimationSystem.ease_in_out_cubic,
            "Ease-In": SunAnimationSystem.ease_in_quad,
            "Ease-Out": SunAnimationSystem.ease_out_quad
        }

        self.is_transitioning = False
        self.transition_thread = None
        self.stop_transition = False

        self.enhanced_keyframe_editor = EnhancedKeyframeEditor(self)
        self.is_animating_keyframes = False  # Flag to prevent callback loops

        self.preset_manager = PresetManager()
        self.environment_presets = ENVIRONMENT_PRESETS
        self.sequence_presets = SEQUENCE_PRESETS
        self.builtin_flicker_presets = {"Custom": {}, "Pulse": {}, "Faulty": {}, "Strobe": {}, "Storm": {},
                                        "Heartbeat": {}, "Candle": {}}

        self.demo_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Activision', 'CoDWaW', 'players', 'demos')
        self.builtin_anim_presets = {
            "Custom": {"type": "linear"},
            "Sunrise": {"type": "linear", "x": 90.0, "y": 45.0, "duration": 5.0, "easing": "ease-out", "fps": 60,
                        "reset": False},
            "Sunset": {"type": "linear", "x": -90.0, "y": -10.0, "duration": 5.0, "easing": "ease-in", "fps": 60,
                       "reset": False},
            "Sweep": {"type": "linear", "x": 120.0, "y": 45.0, "duration": 3.0, "easing": "smooth", "fps": 60,
                      "reset": True},
            "Noon": {"type": "linear", "x": -90.0, "y": 60.0, "duration": 4.0, "easing": "smooth", "fps": 60,
                     "reset": False},
            "Searchlight": {"type": "linear", "x": 90.0, "y": 10.0, "duration": 1.5, "easing": "smooth", "fps": 60,
                            "reset": True},
            "DayCycle": {"type": "orbital", "center_x": 0, "center_y": -20, "radius_x": 180, "radius_y": 90,
                         "rev_duration": 20.0, "direction": "Counter-Clockwise"},
        }

        self.hotkey_manager = HotkeyManager(self)
        self.hotkeys = {'start_animation': 'ctrl+f1', 'stop_animation': 'ctrl+f2', 'start_flicker': 'ctrl+f3',
                        'stop_flicker': 'ctrl+f4'}
        self.hotkey_manager.reregister_all_hotkeys(self.hotkeys)

        self.keyframable_controls = [
            "sun_strength", "sun_direction_x", "sun_direction_y", "sun_color",
            "brightness", "contrast", "desaturation", "light_color", "dark_color",
            "fog_start", "fog_color", "fov"
        ]

    def _main_float_prop_cb(self, sender, app_data, user_data):
        if self.is_animating_keyframes:
            return

        prop_name, command = user_data
        self.ui_vars["doubles"][prop_name] = app_data

        kf_tag = f"kf_{prop_name}"
        if dpg.does_item_exist(kf_tag):
            dpg.set_value(kf_tag, app_data)

        self.memory_manager.execute_command(f"{command} {app_data:.2f}")

    def _main_color_prop_cb(self, sender, app_data, user_data):
        if self.is_animating_keyframes:
            return

        prop_name, command = user_data
        rgb_internal = [c * 2.0 for c in app_data[:3]]
        self.ui_vars["colors"][prop_name] = rgb_internal

        kf_tag = f"kf_{prop_name}"
        if dpg.does_item_exist(kf_tag):
            dpg.set_value(kf_tag, app_data)

        self.memory_manager.execute_command(
            f"{command} {rgb_internal[0]:.2f} {rgb_internal[1]:.2f} {rgb_internal[2]:.2f}")

    def _main_sun_dir_cb(self, sender, app_data, user_data=None):
        if self.is_animating_keyframes:
            return

        x = dpg.get_value("main_sun_direction_x")
        y = dpg.get_value("main_sun_direction_y")
        self.ui_vars["doubles"]["sun_direction_x"] = x
        self.ui_vars["doubles"]["sun_direction_y"] = y

        if dpg.does_item_exist("kf_sun_direction_x"):
            dpg.set_value("kf_sun_direction_x", x)
        if dpg.does_item_exist("kf_sun_direction_y"):
            dpg.set_value("kf_sun_direction_y", y)

        self.memory_manager.execute_command(f"r_lighttweaksundirection {x:.2f} {y:.2f}")

    def _update_legacy_animation_controls(self):
        if dpg.does_item_exist("main_anim_target_x"):
            dpg.set_value("main_anim_target_x", self.ui_vars["doubles"]["sun_direction_x"])
        if dpg.does_item_exist("main_anim_target_y"):
            dpg.set_value("main_anim_target_y", self.ui_vars["doubles"]["sun_direction_y"])

    def _set_keyframable_controls_state(self, enabled: bool):
        for tag in self.keyframable_controls:
            if dpg.does_item_exist(tag):
                dpg.configure_item(tag, enabled=enabled)


                if not enabled:

                    if tag == "fov":
                        dpg.configure_item(tag, callback=None)
                    elif tag in ["sun_direction_x", "sun_direction_y"]:
                        dpg.configure_item(tag, callback=None)

                else:

                    if tag == "fov":
                        dpg.configure_item(tag, callback=self._float_prop_cb,
                                           user_data=["fov", "cg_fov"])
                    elif tag == "sun_direction_x":
                        dpg.configure_item(tag, callback=self._sun_dir_cb)
                    elif tag == "sun_direction_y":
                        dpg.configure_item(tag, callback=self._sun_dir_cb)

    def _execute_keyframe_action(self, new_keyframes, description):

        if not isinstance(new_keyframes, list):
            return
        action = ModifyKeyframesAction(self, self.current_keyframes, new_keyframes, description)
        self.history_manager.execute_action(action)

        self.enhanced_keyframe_editor.on_keyframes_changed()

    def _get_all_keyframable_values(self):
        return {
            "sun_strength": self.ui_vars["doubles"]["sun_strength"],
            "sun_direction_x": self.ui_vars["doubles"]["sun_direction_x"],
            "sun_direction_y": self.ui_vars["doubles"]["sun_direction_y"],
            "sun_color": self.ui_vars["colors"]["sun_color"],
            "brightness": self.ui_vars["doubles"]["brightness"], "contrast": self.ui_vars["doubles"]["contrast"],
            "desaturation": self.ui_vars["doubles"]["desaturation"],
            "light_color": self.ui_vars["colors"]["light_color"],
            "dark_color": self.ui_vars["colors"]["dark_color"], "fog_start": self.ui_vars["doubles"]["fog_start"],
            "fog_color": self.ui_vars["colors"]["fog_color"], "fov": self.ui_vars["doubles"]["fov"],
        }

    def _scrub_to_time(self, sender, app_data):

        if not self.current_keyframes or self.sun_animator.is_animating:
            return


        if dpg.does_item_exist("keyframe_playhead"):
            dpg.set_value("keyframe_playhead", app_data)
        if dpg.does_item_exist("interactive_timeline_slider"):
            dpg.set_value("interactive_timeline_slider", app_data)


        interpolated_values = self.sun_animator.interpolate_values_at_time(app_data, self.current_keyframes,
                                                                           self.easing_functions)
        if interpolated_values:
            self.sun_animator.update_all_properties(interpolated_values)


    def _update_keyframe_list_ui(self):

        self.enhanced_keyframe_editor.update_keyframe_list()

    def _open_keyframe_editor_modal(self, sender, app_data, user_data):

        index = user_data
        kf = self.current_keyframes[index]
        dpg.set_value("kf_modal_index", index)


        for key, value in kf['values'].items():
            modal_tag = f"kf_modal_{key}"
            if dpg.does_item_exist(modal_tag):
                if "color" in key and isinstance(value, list):

                    dpg.set_value(modal_tag, [c / 2.0 for c in value])
                else:

                    dpg.set_value(modal_tag, value)

        dpg.configure_item("keyframe_edit_modal", show=True)

    def _save_keyframe_modal_changes(self):

        index = dpg.get_value("kf_modal_index")
        keyframes_copy = copy.deepcopy(self.current_keyframes)


        for key in keyframes_copy[index]['values']:
            modal_tag = f"kf_modal_{key}"
            if dpg.does_item_exist(modal_tag):
                val = dpg.get_value(modal_tag)
                if "color" in key and isinstance(val, list):
                    keyframes_copy[index]['values'][key] = [c * 2 for c in val]
                else:
                    keyframes_copy[index]['values'][key] = val

        self._execute_keyframe_action(keyframes_copy, "Edit Keyframe Values")
        dpg.configure_item("keyframe_edit_modal", show=False)

    def _update_ui_from_animation(self, values):

        self.is_animating_keyframes = True

        for key, val in values.items():

            if key in self.ui_vars["doubles"]:
                self.ui_vars["doubles"][key] = val
            elif key in self.ui_vars["colors"]:
                self.ui_vars["colors"][key] = val


            if dpg.does_item_exist(f"kf_{key}"):
                if key in self.ui_vars["colors"]:
                    dpg.set_value(f"kf_{key}", [c / 2.0 for c in val])
                else:
                    dpg.set_value(f"kf_{key}", val)


            main_tag = f"main_{key}"
            if dpg.does_item_exist(main_tag):
                if key in self.ui_vars["colors"]:
                    dpg.set_value(main_tag, [c / 2.0 for c in val])
                else:
                    dpg.set_value(main_tag, val)


            if dpg.does_item_exist(key):
                if key in self.ui_vars["colors"]:
                    dpg.set_value(key, [c / 2.0 for c in val])
                else:
                    dpg.set_value(key, val)

        self.is_animating_keyframes = False  # Clear flag

    def transition_to_environment(self, preset_name, duration_ms):
        if self.is_transitioning: self._add_debug_message("Another transition is already in progress.",
                                                          is_error=True); return
        end_preset = self.environment_presets.get(preset_name)
        if not end_preset: self._add_debug_message(f"Target preset '{preset_name}' not found for transition.",
                                                   is_error=True); return
        self.stop_animation()
        self.stop_transition = False
        self.is_transitioning = True
        self.transition_thread = threading.Thread(target=self._transition_worker, args=(end_preset, duration_ms))
        self.transition_thread.daemon = True
        self.transition_thread.start()

    def _transition_worker(self, end_preset, duration_ms):
        start_time = time.time()
        duration_s = duration_ms / 1000.0
        start_state = self._get_all_keyframable_values()
        frame_delay = 1.0 / 60.0
        try:
            preset_name = list(self.environment_presets.keys())[
                list(self.environment_presets.values()).index(end_preset)]
        except ValueError:
            preset_name = "Unknown"
        self._add_debug_message(f"Starting transition to '{preset_name}' over {duration_s}s.")
        while not self.stop_transition:
            elapsed = time.time() - start_time
            if elapsed >= duration_s: break
            progress = SunAnimationSystem.ease_in_out_cubic(elapsed / duration_s)
            interpolated_values = {}
            for key, start_val in start_state.items():
                if key in end_preset:
                    end_val = end_preset[key]
                    if isinstance(start_val, (float, int)):
                        interpolated_values[key] = SunAnimationSystem.lerp(start_val, end_val, progress)
                    elif isinstance(start_val, list):
                        interpolated_values[key] = [SunAnimationSystem.lerp(start_val[i], end_val[i], progress) for i in
                                                    range(len(start_val))]
            self.sun_animator.update_all_properties(interpolated_values)
            time.sleep(frame_delay)
        if not self.stop_transition: self.apply_environment_preset(preset_name)
        self.is_transitioning = False
        self._add_debug_message(f"Transition to '{preset_name}' finished.")

    def stop_animation(self):
        self.sun_animator.stop();
        self.sun_flicker.stop();
        self.sequence_builder.stop();
        self.stop_transition = True
        self._set_keyframable_controls_state(enabled=True)
        self._add_debug_message(f"All effects stopped.")

    def apply_environment_preset(self, preset_name):
        self.stop_animation()
        preset = self.environment_presets.get(preset_name)
        if not preset: self._add_debug_message(f"Environment preset '{preset_name}' not found", is_error=True); return
        self.sun_animator.update_all_properties(preset)
        if "flicker" in preset:
            flicker_data = preset["flicker"]
            if dpg.does_item_exist("flicker_preset_combo"): dpg.set_value("flicker_preset_combo",
                                                                          flicker_data.get("preset", "Pulse"))
            if dpg.does_item_exist("flicker_speed_ms"): dpg.set_value("flicker_speed_ms",
                                                                      flicker_data.get("speed", 500))
            if dpg.does_item_exist("flicker_use_easing"): dpg.set_value("flicker_use_easing",
                                                                        flicker_data.get("easing", True))
            self.start_flicker()
        if "animation" in preset:
            anim_data = preset["animation"]
            anim_preset_name = anim_data.get("preset")
            if anim_preset_name:
                self.apply_anim_preset(None, anim_preset_name)
                self.start_animation()
        self._add_debug_message(f"Applied environment: {preset_name}")


        if hasattr(self, 'enhanced_keyframe_editor'):
            self.enhanced_keyframe_editor.timeline_widget.update_timeline()

    def _start_legacy_animation(self):

        try:
            self._set_keyframable_controls_state(enabled=False)
            on_complete_callback = lambda: self._set_keyframable_controls_state(enabled=True)

            if dpg.get_value("enable_flicker_along_path"):
                self.start_flicker()

            anim_type = dpg.get_value("anim_type_selector")

            if anim_type == "Linear":
                cx, cy = self.ui_vars["doubles"]["sun_direction_x"], self.ui_vars["doubles"]["sun_direction_y"]
                tx, ty = dpg.get_value("anim_target_x"), dpg.get_value("anim_target_y")
                dur = float(dpg.get_value("anim_duration"))
                fps = int(dpg.get_value("anim_fps"))
                ease, reset = dpg.get_value("anim_easing"), dpg.get_value("anim_reset_on_finish")
                self.sun_animator.animate_sun_direction(cx, tx, cy, ty, dur, fps, ease, reset,
                                                        on_complete=on_complete_callback)
                self._add_debug_message(f"Legacy linear animation started.")
            elif anim_type == "Orbital":
                cx, cy, rx, ry = dpg.get_value("orbital_center_x"), dpg.get_value("orbital_center_y"), dpg.get_value(
                    "orbital_radius_x"), dpg.get_value("orbital_radius_y")
                rev_dur = float(dpg.get_value("orbital_rev_duration"))
                direction = dpg.get_value("orbital_direction")
                self.sun_animator.animate_sun_orbital(cx, cy, rx, ry, rev_dur, direction,
                                                      on_complete=on_complete_callback)
                self._add_debug_message(f"Legacy orbital animation started.")
        except Exception as e:
            self._add_debug_message(f"Error starting legacy animation: {e}", is_error=True)
            self._set_keyframable_controls_state(enabled=True)

    def start_animation(self, duration_override=None):
        """Start keyframe animation with extensive debugging"""

        # Add debug message right at the start to confirm method is being called
        self._add_debug_message("=== START ANIMATION BUTTON PRESSED ===")

        try:
            # Debug: Check current keyframes
            self._add_debug_message(f"Current keyframes count: {len(self.current_keyframes)}")
            if self.current_keyframes:
                for i, kf in enumerate(self.current_keyframes):
                    self._add_debug_message(
                        f"  Keyframe {i}: time={kf.get('time', 'N/A')}, values={len(kf.get('values', {}))}")

            # Debug: Check connection
            self._add_debug_message(f"Memory manager connected: {self.memory_manager.is_connected()}")

            # Check if we have enough keyframes
            if not self.current_keyframes or len(self.current_keyframes) < 2:
                self._add_debug_message(
                    f"FAILED: Need at least 2 keyframes for animation. Currently have {len(self.current_keyframes)}. "
                    f"Use 'Add Keyframe' button to create keyframes first.",
                    is_error=True
                )
                return

            # Debug: Check validation method exists
            if not hasattr(self, 'enhanced_keyframe_editor'):
                self._add_debug_message("FAILED: enhanced_keyframe_editor not found!", is_error=True)
                return

            if not hasattr(self.enhanced_keyframe_editor, '_validate_keyframes'):
                self._add_debug_message("FAILED: _validate_keyframes method not found!", is_error=True)
                return

            # Try validation
            self._add_debug_message("Running keyframe validation...")
            validation_result = self.enhanced_keyframe_editor._validate_keyframes()
            self._add_debug_message(f"Validation result: {validation_result}")

            if not validation_result:
                self._add_debug_message(
                    "FAILED: Keyframe validation failed. Check for issues like duplicate times or missing properties.",
                    is_error=True
                )
                return

            # Check connection again
            if not self.memory_manager.is_connected():
                self._add_debug_message(
                    "FAILED: Cannot start animation - Not connected to game. Make sure the game is running.",
                    is_error=True
                )
                return

            # Get duration
            total_duration = duration_override
            if total_duration is None:
                total_duration = dpg.get_value("keyframe_total_duration") if dpg.does_item_exist(
                    "keyframe_total_duration") else 10.0
            self._add_debug_message(f"Animation duration: {total_duration}s")

            # Disable controls
            self._add_debug_message("Disabling keyframable controls...")
            self._set_keyframable_controls_state(enabled=False)

            # Create completion callback
            def on_complete():
                self._set_keyframable_controls_state(enabled=True)
                self._add_debug_message("=== KEYFRAME ANIMATION COMPLETED ===")

            # Debug: Check if sun_animator exists and has the method
            if not hasattr(self, 'sun_animator'):
                self._add_debug_message("FAILED: sun_animator not found!", is_error=True)
                self._set_keyframable_controls_state(enabled=True)
                return

            if not hasattr(self.sun_animator, 'animate_from_keyframes'):
                self._add_debug_message("FAILED: animate_from_keyframes method not found!", is_error=True)
                self._set_keyframable_controls_state(enabled=True)
                return

            # Start the animation
            self._add_debug_message("=== STARTING KEYFRAME ANIMATION ===")
            self.sun_animator.animate_from_keyframes(
                self.current_keyframes,
                total_duration,
                self.easing_functions,
                on_complete=on_complete
            )

            self._add_debug_message(
                f"SUCCESS: Keyframe animation started - {len(self.current_keyframes)} keyframes over {total_duration}s"
            )

        except Exception as e:
            self._set_keyframable_controls_state(enabled=True)
            self._add_debug_message(f"ERROR in start_animation: {e}", is_error=True)
            import traceback
            self._add_debug_message(f"Full traceback: {traceback.format_exc()}", is_error=True)


    def apply_anim_preset(self, sender, app_data):
        preset_name = app_data
        preset_data = self.builtin_anim_presets.get(preset_name)
        if preset_data is None: preset_data = self.preset_manager.get_presets("animation").get(preset_name)
        is_manual_mode = preset_name == "Custom"
        if preset_data:
            preset_type = preset_data.get("type", "linear").title()
            dpg.set_value("anim_type_selector", preset_type)
            is_linear = preset_type == "Linear"
            dpg.configure_item("linear_anim_group", show=is_linear)
            dpg.configure_item("orbital_anim_group", show=not is_linear)
            if not is_manual_mode:
                if is_linear:
                    dpg.set_value("anim_target_x", preset_data.get("x", 0));
                    dpg.set_value("anim_target_y", preset_data.get("y", 0))
                    dpg.set_value("anim_duration", preset_data.get("duration", 10));
                    dpg.set_value("anim_easing", preset_data.get("easing", "smooth"))
                    dpg.set_value("anim_fps", preset_data.get("fps", 60));
                    dpg.set_value("anim_reset_on_finish", preset_data.get("reset", False))
                else:
                    dpg.set_value("orbital_center_x", preset_data.get("center_x", 0));
                    dpg.set_value("orbital_center_y", preset_data.get("center_y", 0))
                    dpg.set_value("orbital_radius_x", preset_data.get("radius_x", 180));
                    dpg.set_value("orbital_radius_y", preset_data.get("radius_y", 60))
                    dpg.set_value("orbital_rev_duration", preset_data.get("rev_duration", 30));
                    dpg.set_value("orbital_direction", preset_data.get("direction", "Counter-Clockwise"))

    def start_flicker(self):
        try:
            if not self.memory_manager.is_connected():
                return

            strength = self.ui_vars["doubles"]["sun_strength"]

            speed = None
            if dpg.does_item_exist("flicker_speed_ms"):
                speed = dpg.get_value("flicker_speed_ms")
            elif dpg.does_item_exist("main_flicker_speed_ms"):
                speed = dpg.get_value("main_flicker_speed_ms")

            if speed is None:
                speed = 500  # Default 500ms
                self._add_debug_message("Warning: Flicker speed not found, using default 500ms", is_error=False)

            preset_name = "Pulse"
            if dpg.does_item_exist("flicker_preset_combo"):
                preset_name = dpg.get_value("flicker_preset_combo") or "Pulse"
            elif dpg.does_item_exist("main_flicker_preset_combo"):
                preset_name = dpg.get_value("main_flicker_preset_combo") or "Pulse"

            use_easing = True
            if dpg.does_item_exist("flicker_use_easing"):
                use_easing = dpg.get_value("flicker_use_easing")
            elif dpg.does_item_exist("main_flicker_use_easing"):
                use_easing = dpg.get_value("main_flicker_use_easing")

            self.sun_flicker.start(strength, speed, preset=preset_name, use_easing=use_easing)
            self._add_debug_message(f"'{preset_name}' flicker started.")

        except Exception as e:
            self._add_debug_message(f"Error starting flicker: {e}", is_error=True)

    def stop_flicker(self):
        if self.sun_flicker.is_flickering:
            self.sun_flicker.stop()
            self._add_debug_message("Sun flicker stopped.")
        else:

            self.sun_flicker.stop()
            self._add_debug_message("Flicker stop requested (was not running).")


    def _add_debug_message(self, message, is_error=False):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = "[ERROR]" if is_error else "[INFO]"
        formatted_message = f"[{timestamp}] {prefix} {message}"
        self.debug_messages.append((formatted_message, is_error))
        if len(self.debug_messages) > self.max_debug_lines: self.debug_messages = self.debug_messages[
            -self.max_debug_lines:]
        if dpg.does_item_exist("debug_text"): self._update_debug_display()

    def _update_debug_display(self):
        debug_text = "\n".join([msg[0] for msg in self.debug_messages]);
        dpg.set_value("debug_text", debug_text)
        if dpg.does_item_exist("debug_window"): dpg.set_y_scroll("debug_window", dpg.get_y_scroll_max("debug_window"))

    def _clear_debug_console(self):
        self.debug_messages = [];
        if dpg.does_item_exist("debug_text"): dpg.set_value("debug_text", "Debug console cleared.")

    def _init_ui_vars_map(self):
        self.ui_vars = {"doubles": {}, "booleans": {}, "colors": {}, "integers": {}}
        defaults = MEMORY_MAP["defaults"]
        for key, value in defaults.items():
            if isinstance(value, bool):
                self.ui_vars["booleans"][key] = value
            elif isinstance(value, float):
                self.ui_vars["doubles"][key] = value
            elif isinstance(value, int):
                self.ui_vars["integers"][key] = value
            elif isinstance(value, list) and len(value) == 3:
                self.ui_vars["colors"][key] = value

    def _check_initial_status(self):
        if self.memory_manager.is_connected():
            self.status_message, self.status_color = self.memory_manager.status_message, (0, 255, 0)
        else:
            self.status_message, self.status_color = self.memory_manager.status_message, (255, 0, 0)

    def _apply_config_to_ui(self, config_data):
        ui_data = config_data.get("ui", {})
        for category, values in ui_data.items():
            if category in self.ui_vars: self.ui_vars[category].update(values)
        self.sun_animator.update_all_properties(self._get_all_keyframable_values())
        for key, value in self.ui_vars["booleans"].items():
            if dpg.does_item_exist(f"{key}_bool"): dpg.set_value(f"{key}_bool", value)
        for key, value in self.ui_vars["integers"].items():
            if dpg.does_item_exist(key): dpg.set_value(key, value)

        hotkey_data = config_data.get("hotkeys", {});
        self.hotkeys.update(hotkey_data)
        self.hotkey_manager.reregister_all_hotkeys(self.hotkeys)
        if dpg.does_item_exist("hotkey_table"): self.update_hotkey_tab_ui()
        self._add_debug_message("Config loaded.")

    def _scan_for_demos(self):
        if not os.path.exists(self.demo_path): self._add_debug_message(f"Demo directory not found at {self.demo_path}",
                                                                       is_error=True); return []
        try:
            demos = sorted([f.replace('.dm6', '') for f in os.listdir(self.demo_path) if f.endswith('.dm_6')])
            self._add_debug_message(f"Found {len(demos)} demo(s).");
            return demos
        except Exception as e:
            self._add_debug_message(f"Failed to scan for demos: {e}", is_error=True);
            return []

    def _on_demo_selected(self, sender, demo_name):
        if demo_name:
            command = f"demo {demo_name}"
            self.memory_manager.execute_command(command);
            self._add_debug_message(f"Executing: {command}")

    def _bool_prop_cb(self, sender, app_data, user_data):
        prop_name, command = user_data
        self.ui_vars["booleans"][prop_name] = app_data
        self.memory_manager.execute_command(f"{command} {int(app_data)}")

    def _filmtweaks_cb(self, sender, app_data):
        value = int(app_data)
        self.ui_vars["booleans"]["filmtweaks_enabled"] = app_data
        self.memory_manager.execute_command(f"r_filmtweakenable {value}")
        self.memory_manager.execute_command(f"r_filmusetweaks {value}")

    def _float_prop_cb(self, sender, app_data, user_data):
        if self.is_animating_keyframes:
            return

        prop_name, command = user_data
        self.ui_vars["doubles"][prop_name] = app_data
        self.memory_manager.execute_command(f"{command} {app_data:.2f}")

    def _color_prop_cb(self, sender, app_data, user_data):
        if self.is_animating_keyframes:
            return

        prop_name, command = user_data
        rgb_internal = [c * 2.0 for c in app_data[:3]]
        self.ui_vars["colors"][prop_name] = rgb_internal
        self.memory_manager.execute_command(
            f"{command} {rgb_internal[0]:.2f} {rgb_internal[1]:.2f} {rgb_internal[2]:.2f}")

    def _sun_dir_cb(self, sender, app_data, user_data=None):
        if self.is_animating_keyframes:
            return

        x = dpg.get_value("sun_direction_x")
        y = dpg.get_value("sun_direction_y")
        self.ui_vars["doubles"]["sun_direction_x"] = x
        self.ui_vars["doubles"]["sun_direction_y"] = y
        self.memory_manager.execute_command(f"r_lighttweaksundirection {x:.2f} {y:.2f}")

    def update_hotkey_tab_ui(self):
        if dpg.does_item_exist("hotkey_table"): dpg.delete_item("hotkey_table", children_only=True)
        dpg.add_table_column(label="Action", parent="hotkey_table");
        dpg.add_table_column(label="Assigned Hotkey", width_stretch=True, parent="hotkey_table")
        for action_name, description in self.hotkey_manager.bindable_actions.items():
            with dpg.table_row(parent="hotkey_table"): dpg.add_text(
                description); tag = f"hotkey_input_{action_name}"; dpg.add_input_text(tag=tag); dpg.set_value(tag,
                                                                                                              self.hotkeys.get(
                                                                                                                  action_name,
                                                                                                                  ""))
        for preset_type, label in [("animation", "Anim"), ("flicker", "Flicker")]:
            for name in self.preset_manager.get_presets(preset_type):
                with dpg.table_row(parent="hotkey_table"): dpg.add_text(
                    f"({label} Preset) {name}"); tag = f"hotkey_input_{preset_type}_preset:{name}"; dpg.add_input_text(
                    tag=tag); dpg.set_value(tag, self.hotkeys.get(f"{preset_type}_preset:{name}", ""))
        for action_name in self.preset_manager.get_presets("actions"):
            with dpg.table_row(parent="hotkey_table"): dpg.add_text(
                f"(Custom Action) {action_name}"); tag = f"hotkey_input_custom:{action_name}"; dpg.add_input_text(
                tag=tag); dpg.set_value(tag, self.hotkeys.get(f"custom:{action_name}", ""))

    def execute_custom_action(self, action_name):
        if action_name.startswith("custom:"): action_name = action_name.split(":", 1)[1]
        all_actions = self.preset_manager.get_presets("actions")
        action_steps = all_actions.get(action_name)
        if action_steps:
            self.action_manager.execute_action(action_name, action_steps)
        else:
            self._add_debug_message(f"Custom action '{action_name}' not found.", is_error=True)

    def execute_animation_preset(self, preset_name):
        self._add_debug_message(f"Hotkey: Executing animation preset '{preset_name}'.")
        self.apply_anim_preset(None, preset_name)
        self.start_animation()

    def execute_flicker_preset(self, preset_name):
        self._add_debug_message(f"Hotkey: Executing flicker preset '{preset_name}'.")
        self.start_flicker()







   ## user interface starts here
    ## add themes?



    def create_ui(self):
        with dpg.window(tag="Primary Window", autosize=False, width=640, height=850, no_collapse=False):
            dpg.add_text(self.status_message, tag="status_text", color=self.status_color);
            dpg.add_separator()
            dpg.add_text("Console -- Enter to send")
            with dpg.group(horizontal=True):
                dpg.add_input_text(label="", tag="console_input", width=-1, on_enter=True,
                                   callback=lambda s, d, u: self.memory_manager.execute_command(d.lstrip('/')))
                dpg.add_button(label="Send", callback=lambda: self.memory_manager.execute_command(
                    dpg.get_value("console_input").lstrip('/')))
            dpg.add_separator();
            dpg.add_text("Demo Browser")
            with dpg.group(horizontal=False):
                demo_files = self._scan_for_demos()
                dpg.add_combo(label="Demos", tag="demo_combo", items=demo_files, callback=self._on_demo_selected,
                              width=-50)

                def refresh_demos():
                    dpg.configure_item("demo_combo", items=self._scan_for_demos());
                    self._add_debug_message("Refreshed demo list.")

                dpg.add_button(label="Refresh", callback=refresh_demos, width=0)
            dpg.add_separator()
            with dpg.tab_bar():
                with dpg.tab(label="Tweaks"):
                    dpg.add_text("General", color=(255, 255, 0))
                    with dpg.group(horizontal=True):
                        dpg.add_checkbox(label="Film Tweaks", tag="filmtweaks_enabled_bool",
                                         default_value=self.ui_vars["booleans"]["filmtweaks_enabled"],
                                         callback=self._filmtweaks_cb)
                        dpg.add_checkbox(label="DOF", tag="dof_enabled_bool",
                                         default_value=self.ui_vars["booleans"]["dof_enabled"],
                                         callback=self._bool_prop_cb, user_data=["dof_enabled", "r_dof_enable"])
                        dpg.add_checkbox(label="Glow Tweaks", tag="glow_enabled_bool",
                                         default_value=self.ui_vars["booleans"]["glow_enabled"],
                                         callback=self._bool_prop_cb, user_data=["glow_enabled", "r_glowusetweaks"])
                    dpg.add_separator()
                    dpg.add_slider_int(label="FOV", tag="fov", default_value=int(self.ui_vars["doubles"]["fov"]),
                                       min_value=5, max_value=165, callback=self._float_prop_cb,
                                       user_data=["fov", "cg_fov"])
                    dpg.add_slider_float(label="Brightness", tag="brightness",
                                         default_value=self.ui_vars["doubles"]["brightness"], min_value=-1.0,
                                         max_value=1.0, callback=self._float_prop_cb,
                                         user_data=["brightness", "r_filmtweakbrightness"])
                    dpg.add_slider_float(label="Contrast", tag="contrast",
                                         default_value=self.ui_vars["doubles"]["contrast"], min_value=0.0,
                                         max_value=4.0, callback=self._float_prop_cb,
                                         user_data=["contrast", "r_filmtweakcontrast"])
                    dpg.add_slider_float(label="Desaturation", tag="desaturation",
                                         default_value=self.ui_vars["doubles"]["desaturation"], min_value=0.0,
                                         max_value=1.0, callback=self._float_prop_cb,
                                         user_data=["desaturation", "r_filmtweakdesaturation"])
                    dpg.add_separator()
                    dpg.add_text("Passes", color=(255, 255, 0))
                    with dpg.group(horizontal=True):
                        dpg.add_slider_int(label="Color Map", tag="color_map", width=50,
                                           default_value=self.ui_vars["integers"]["color_map"], min_value=0,
                                           max_value=4,
                                           callback=lambda s, d: self.memory_manager.execute_command(f"r_colormap {d}"))
                        dpg.add_slider_int(label="Light Map", tag="light_map", width=50,
                                           default_value=self.ui_vars["integers"]["light_map"], min_value=0,
                                           max_value=4,
                                           callback=lambda s, d: self.memory_manager.execute_command(f"r_lightmap {d}"))
                        dpg.add_slider_int(label="Debug Shader", tag="debug_shader", width=50,
                                           default_value=self.ui_vars["integers"]["debug_shader"], min_value=0,
                                           max_value=4, callback=lambda s, d: self.memory_manager.execute_command(
                                f"r_debugshader {d}"))
                    dpg.add_separator()
                    dpg.add_text("Light/Dark Tints", color=(255, 255, 0))
                    with dpg.group(horizontal=True):
                        dpg.add_color_picker(tag="light_color", label="", no_side_preview=True,
                                             alpha_bar=False, width=250, picker_mode=dpg.mvColorPicker_wheel,
                                             default_value=[c / 2.0 for c in self.ui_vars["colors"]["light_color"]],
                                             callback=self._color_prop_cb,
                                             user_data=["light_color", "r_filmtweaklighttint"])
                        dpg.add_color_picker(tag="dark_color", label="", no_side_preview=True, alpha_bar=False,
                                             width=250, picker_mode=dpg.mvColorPicker_wheel,
                                             default_value=[c / 2.0 for c in self.ui_vars["colors"]["dark_color"]],
                                             callback=self._color_prop_cb,
                                             user_data=["dark_color", "r_filmtweakdarktint"])
                    dpg.add_separator()
                    dpg.add_text("Environment Presets & Sequences", color=(255, 255, 0))
                    dpg.add_combo(label="Environment", tag="environment_preset_combo",
                                  items=list(self.environment_presets.keys()), default_value="Clear Day", width=300)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Apply", callback=lambda: self.apply_environment_preset(
                            dpg.get_value("environment_preset_combo")))
                        dpg.add_button(label="Transition to Preset", callback=lambda: self.transition_to_environment(
                            dpg.get_value("environment_preset_combo"),
                            dpg.get_value("transition_duration_slider") * 1000))
                        dpg.add_slider_float(label="Duration (s)", tag="transition_duration_slider", default_value=3.0,
                                             min_value=0.1, max_value=20.0, width=150)
                    dpg.add_separator()
                    dpg.add_text("Sequences", color=(255, 255, 0))
                    with dpg.group(horizontal=True):
                        dpg.add_combo(label="Sequence", tag="sequence_preset_combo",
                                      items=list(self.sequence_presets.keys()), width=300)
                        dpg.add_slider_float(label="Speed", tag="sequence_speed_multiplier", min_value=0.1,
                                             max_value=4.0, default_value=1.0, width=150, format="%.2fx")
                    with dpg.group(horizontal=True):
                        def execute_sequence():
                            name = dpg.get_value("sequence_preset_combo");
                            steps = self.sequence_presets.get(name)
                            multiplier = dpg.get_value("sequence_speed_multiplier")
                            if steps: self.sequence_builder.execute_sequence(name, steps, multiplier)

                        dpg.add_button(label="Start Sequences", callback=execute_sequence)
                        dpg.add_button(label="Stop All Effects", callback=self.stop_animation)

                with dpg.tab(label="Fog"):
                    dpg.add_text("Fog requires WAWMVM by @luckkyy to work!", color=(255, 0, 0))
                    dpg.add_checkbox(label="Enable Fog", tag="fog_enabled_bool",
                                     default_value=self.ui_vars["booleans"]["fog_enabled"], callback=self._bool_prop_cb,
                                     user_data=["fog_enabled", "mvm_fog_custom"])
                    dpg.add_separator()
                    dpg.add_slider_float(label="Fog Density", tag="fog_start",
                                         default_value=int(self.ui_vars["doubles"]["fog_start"]), min_value=1, max_value=9999, callback=self._float_prop_cb,
                                         user_data=["fog_start", "mvm_fog_start"])
                    dpg.add_color_picker(tag="fog_color", label="Fog Color", no_side_preview=True, alpha_bar=False,
                                         picker_mode=dpg.mvColorPicker_wheel, width=350,
                                         default_value=[c / 2.0 for c in self.ui_vars["colors"]["fog_color"]],
                                         callback=self._color_prop_cb, user_data=["fog_color", "mvm_fog_color"])

                with dpg.tab(label="Sun"):
                    with dpg.group(label="Sun Properties"):
                        # Use unique tags by adding "main_" prefix
                        dpg.add_slider_float(label="Sun Strength", tag="main_sun_strength",
                                             default_value=self.ui_vars["doubles"]["sun_strength"], min_value=0.0,
                                             max_value=8.0, callback=self._main_float_prop_cb,
                                             user_data=["sun_strength", "r_lighttweaksunlight"])
                        dpg.add_slider_float(label="Sun Direction X", tag="main_sun_direction_x",
                                             default_value=self.ui_vars["doubles"]["sun_direction_x"], min_value=-360.0,
                                             max_value=360.0, callback=self._main_sun_dir_cb)
                        dpg.add_slider_float(label="Sun Direction Y", tag="main_sun_direction_y",
                                             default_value=self.ui_vars["doubles"]["sun_direction_y"], min_value=-360.0,
                                             max_value=360.0, callback=self._main_sun_dir_cb)
                        dpg.add_color_picker(tag="main_sun_color", label="Sun Color", no_side_preview=True,
                                             alpha_bar=False,
                                             width=250, picker_mode=dpg.mvColorPicker_wheel,
                                             default_value=[c / 2.0 for c in self.ui_vars["colors"]["sun_color"]],
                                             callback=self._main_color_prop_cb,
                                             user_data=["sun_color", "r_lighttweaksuncolor"])
                    dpg.add_separator()
                    dpg.add_text("Sun Animation", color=(255, 255, 0))
                    dpg.add_text("For advanced keyframing, use the Keyframing tab!", color=(100, 255, 100))
                    dpg.add_text("Note: Animation does not work with cl_avidemo -- Please record with OBS and timescale",color=(255, 0, 0))

                    def toggle_anim_type(s, a):
                        dpg.configure_item("main_linear_anim_group", show=a == "Linear")
                        dpg.configure_item("main_orbital_anim_group", show=a == "Orbital")

                    dpg.add_radio_button(label="Animation Type", items=["Linear", "Orbital"],
                                         tag="main_anim_type_selector", default_value="Linear", horizontal=True,
                                         callback=toggle_anim_type)

                    with dpg.group(tag="main_linear_anim_group"):
                        dpg.add_combo(label="Preset", tag="main_anim_preset_combo",
                                      items=list(self.builtin_anim_presets.keys()), callback=self.apply_anim_preset)
                        dpg.add_slider_float(label="Sun X Target", tag="main_anim_target_x", default_value=90.0,
                                             min_value=-360.0, max_value=360.0)
                        dpg.add_slider_float(label="Sun Y Target", tag="main_anim_target_y", default_value=45.0,
                                             min_value=-360.0, max_value=360.0)
                        with dpg.group(horizontal=True):
                            dpg.add_input_float(label="Duration (s)", tag="main_anim_duration", default_value=10.0,
                                                width=150, step=0.5)
                            dpg.add_input_int(label="FPS", tag="main_anim_fps", default_value=60, width=150, step=5)
                        dpg.add_combo(label="Easing", tag="main_anim_easing",
                                      items=["linear", "smooth", "ease-in", "ease-out"], default_value="smooth",
                                      width=150)
                        dpg.add_checkbox(label="Reset to (0,0) after animation", tag="main_anim_reset_on_finish",
                                         default_value=False)

                    with dpg.group(tag="main_orbital_anim_group", show=False):
                        dpg.add_input_float(label="Center X", tag="main_orbital_center_x", default_value=0.0)
                        dpg.add_input_float(label="Center Y", tag="main_orbital_center_y", default_value=0.0)
                        dpg.add_input_float(label="Radius X", tag="main_orbital_radius_x", default_value=180.0)
                        dpg.add_input_float(label="Radius Y", tag="main_orbital_radius_y", default_value=60.0)
                        dpg.add_input_float(label="Duration per Revolution (s)", tag="main_orbital_rev_duration",
                                            default_value=30.0)
                        dpg.add_combo(label="Direction", items=["Clockwise", "Counter-Clockwise"],
                                      tag="main_orbital_direction", default_value="Counter-Clockwise")

                    with dpg.group(horizontal=True):
                        dpg.add_checkbox(label="Flicker during animation", tag="main_enable_flicker_along_path")
                        dpg.add_button(label="Start", callback=self._start_legacy_animation)
                        dpg.add_button(label="Stop", callback=self.stop_animation)

                    dpg.add_separator()
                    dpg.add_text("Sun Flicker", color=(255, 255, 0))
                    dpg.add_combo(label="Preset", tag="main_flicker_preset_combo",
                                  items=list(self.builtin_flicker_presets.keys())[1:], default_value="Pulse")
                    dpg.add_checkbox(label="Smoothing", tag="main_flicker_use_easing", default_value=True)
                    dpg.add_slider_int(label="Speed / Fade (ms)", tag="main_flicker_speed_ms", default_value=100,
                                       min_value=10, max_value=2000, width=200)
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Start Flicker", callback=self.start_flicker)
                        dpg.add_button(label="Stop Flicker", callback=self.stop_flicker)

                dpg.add_tab(label="|")

                with dpg.tab(label="Keyframing"):
                    dpg.add_text("KEYFRAMES DO NOT WORK WITH CL_AVIDEMO -- PLEASE RECORD WITH OBS AND TIMESCALE",  color=(255, 0, 0))


                    dpg.add_text("Quick Property Controls", color=(255, 255, 0))
                    with dpg.group(horizontal=True):
                        with dpg.child_window(width=200, height=150, border=True):
                            dpg.add_text("Sun", color=(255, 255, 0))
                            dpg.add_slider_float(label="Strength", tag="kf_sun_strength", width=110,
                                                 default_value=self.ui_vars["doubles"]["sun_strength"],
                                                 min_value=0.0, max_value=8.0,
                                                 callback=self.enhanced_keyframe_editor._sync_property_value,
                                                 user_data="sun_strength")
                            dpg.add_slider_float(label="Dir. X", tag="kf_sun_direction_x", width=110,
                                                 default_value=self.ui_vars["doubles"]["sun_direction_x"],
                                                 min_value=-360.0, max_value=360.0,
                                                 callback=self.enhanced_keyframe_editor._sync_property_value,
                                                 user_data="sun_direction_x")
                            dpg.add_slider_float(label="Dir.Y", tag="kf_sun_direction_y", width=110,
                                                 default_value=self.ui_vars["doubles"]["sun_direction_y"],
                                                 min_value=-360.0, max_value=360.0,
                                                 callback=self.enhanced_keyframe_editor._sync_property_value,
                                                 user_data="sun_direction_y")
                            dpg.add_color_edit(label="Sun Color", tag="kf_sun_color", no_alpha=True, width=190,
                                               default_value=[c / 2.0 for c in self.ui_vars["colors"]["sun_color"]],
                                               callback=self.enhanced_keyframe_editor._sync_color_value,
                                               user_data="sun_color")

                        with dpg.child_window(width=200, height=150, border=True):
                            dpg.add_text("General", color=(255, 255, 0))
                            dpg.add_slider_float(label="FOV", tag="kf_fov", width=110,
                                                 default_value=self.ui_vars["doubles"]["fov"],
                                                 min_value=5.0, max_value=165.0,
                                                 callback=self.enhanced_keyframe_editor._sync_property_value,
                                                 user_data="fov")
                            dpg.add_slider_float(label="Brightness", tag="kf_brightness", width=110,
                                                 default_value=self.ui_vars["doubles"]["brightness"],
                                                 min_value=-1.0, max_value=1.0,
                                                 callback=self.enhanced_keyframe_editor._sync_property_value,
                                                 user_data="brightness")
                            dpg.add_slider_float(label="Contrast", tag="kf_contrast", width=110,
                                                 default_value=self.ui_vars["doubles"]["contrast"],
                                                 min_value=0.0, max_value=4.0,
                                                 callback=self.enhanced_keyframe_editor._sync_property_value,
                                                 user_data="contrast")
                            dpg.add_slider_float(label="Desat.", tag="kf_desaturation", width=110,
                                                 default_value=self.ui_vars["doubles"]["desaturation"],
                                                 min_value=0.0, max_value=1.0,
                                                 callback=self.enhanced_keyframe_editor._sync_property_value,
                                                 user_data="desaturation")

                        with dpg.child_window(width=200, height=150, border=True):
                            dpg.add_text("Fog & Tints", color=(255, 255, 0))
                            dpg.add_slider_float(label="Fog Start", tag="kf_fog_start", width=110,
                                                 default_value=self.ui_vars["doubles"]["fog_start"],
                                                 min_value=1.0, max_value=9999.0,
                                                 callback=self.enhanced_keyframe_editor._sync_property_value,
                                                 user_data="fog_start")
                            dpg.add_color_edit(label="Fog Color", tag="kf_fog_color", no_alpha=True, width=110,
                                               default_value=[c / 2.0 for c in self.ui_vars["colors"]["fog_color"]],
                                               callback=self.enhanced_keyframe_editor._sync_color_value,
                                               user_data="fog_color")
                            dpg.add_color_edit(label="Light Tint", tag="kf_light_color", no_alpha=True, width=110,
                                               default_value=[c / 2.0 for c in self.ui_vars["colors"]["light_color"]],
                                               callback=self.enhanced_keyframe_editor._sync_color_value,
                                               user_data="light_color")
                            dpg.add_color_edit(label="Dark Tint", tag="kf_dark_color", no_alpha=True, width=110,
                                               default_value=[c / 2.0 for c in self.ui_vars["colors"]["dark_color"]],
                                               callback=self.enhanced_keyframe_editor._sync_color_value,
                                               user_data="dark_color")



                    dpg.add_separator()

                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Undo", tag="kf_undo_button", callback=self.history_manager.undo,
                                       enabled=False)
                        dpg.add_button(label="Redo", tag="kf_redo_button", callback=self.history_manager.redo,
                                       enabled=False)
                        dpg.add_separator()
                        dpg.add_text("Animation Duration:")
                        dpg.add_input_float(
                            tag="keyframe_total_duration",
                            default_value=10.0,
                            min_value=0.1,
                            width=100,
                            callback=self.enhanced_keyframe_editor._on_duration_change
                        )
                        dpg.add_text("seconds")


                    dpg.add_text("Timeline", color=(255, 255, 0))
                    self.enhanced_keyframe_editor.timeline_widget.create_timeline("keyframing_tab")

                    dpg.add_text("Keyframe Options", color=(255, 255, 0))
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Add Keyframe",
                                       callback=self.enhanced_keyframe_editor._add_selective_keyframe, width=110)
                        dpg.add_button(label="Update Selected",
                                       callback=self.enhanced_keyframe_editor._update_selected_keyframes, width=110)
                        dpg.add_button(label="Delete Selected",
                                       callback=self.enhanced_keyframe_editor._delete_selected_keyframes, width=120)
                        dpg.add_button(label="Copy", callback=self.enhanced_keyframe_editor._copy_selected_keyframes,
                                       width=60)
                        dpg.add_button(label="Paste", callback=self.enhanced_keyframe_editor._paste_keyframes, width=60)

                    with dpg.group(horizontal=True):
                        dpg.add_combo(label="Easing", tag="bulk_easing_combo",
                                      items=["Linear", "Smooth", "Ease-In", "Ease-Out"],
                                      callback=self.enhanced_keyframe_editor._apply_bulk_easing, width=120)
                        dpg.add_button(label="Reverse Selected",
                                       callback=self.enhanced_keyframe_editor._reverse_selected_keyframes, width=115)
                        dpg.add_button(label="Distribute Evenly",
                                       callback=self.enhanced_keyframe_editor._distribute_keyframes_evenly, width=115)

                    with dpg.group(horizontal=True):
                        dpg.add_combo(label="Template", tag="keyframe_template_combo",
                                      items=list(self.enhanced_keyframe_editor.keyframe_templates.keys()), width=150)
                        dpg.add_button(label="Load", callback=self.enhanced_keyframe_editor._load_keyframe_template,
                                       width=60)
                        dpg.add_input_text(label="Save As", tag="template_name_input", width=120)
                        dpg.add_button(label="Save", callback=self.enhanced_keyframe_editor._save_keyframe_template,
                                       width=60)

                    dpg.add_separator()


                    dpg.add_text("Animation Control", color=(255, 255, 0))
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Start Keyframe Animation", callback=self.start_animation,
                                       width=200, height=30)
                        dpg.add_button(label="Stop All Effects", callback=self.stop_animation,
                                       width=150, height=30)

                    dpg.add_separator()

                    dpg.add_text("Keyframe List", color=(255, 255, 0))
                    with dpg.child_window(height=150, tag="enhanced_keyframe_container"):
                        with dpg.table(header_row=True, tag="enhanced_keyframe_table",
                                       resizable=True, policy=dpg.mvTable_SizingStretchProp, scrollY=True):
                            dpg.add_table_column(label="Sel", width_fixed=True, init_width_or_weight=30)
                            dpg.add_table_column(label="Time", width_fixed=True, init_width_or_weight=80)
                            dpg.add_table_column(label="Easing", width_fixed=True, init_width_or_weight=100)
                            dpg.add_table_column(label="Properties", width_stretch=True, init_width_or_weight=0.5)
                            dpg.add_table_column(label="Actions", width_fixed=True, init_width_or_weight=120)

                    with dpg.collapsing_header(label="Property Selection", default_open=False):
                        dpg.add_text("Choose which properties to keyframe:")
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="All",
                                           callback=lambda: self.enhanced_keyframe_editor._select_all_properties(True),
                                           width=50)
                            dpg.add_button(label="None",
                                           callback=lambda: self.enhanced_keyframe_editor._select_all_properties(False),
                                           width=50)
                            dpg.add_button(label="Sun Only",
                                           callback=self.enhanced_keyframe_editor._select_sun_properties, width=80)
                            dpg.add_button(label="Visual Only",
                                           callback=self.enhanced_keyframe_editor._select_visual_properties, width=80)

                        with dpg.group(horizontal=True):
                            with dpg.child_window(width=250, height=100):
                                dpg.add_text("Float Properties:")
                                for prop, info in self.enhanced_keyframe_editor.keyframeable_properties.items():
                                    dpg.add_checkbox(label=info["label"], tag=f"kf_prop_{prop}",
                                                     default_value=True,
                                                     callback=lambda s, d,
                                                                     u=prop: self.enhanced_keyframe_editor._toggle_property_selection(
                                                         u, d))

                            with dpg.child_window(width=200, height=100):
                                dpg.add_text("Color Properties:")
                                for prop, info in self.enhanced_keyframe_editor.color_properties.items():
                                    dpg.add_checkbox(label=info["label"], tag=f"kf_prop_{prop}",
                                                     default_value=True,
                                                     callback=lambda s, d,
                                                                     u=prop: self.enhanced_keyframe_editor._toggle_property_selection(
                                                         u, d))

                    with dpg.collapsing_header(label="Validation & Preview", default_open=False):
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="Validate Keyframes",
                                           callback=self.enhanced_keyframe_editor._validate_keyframes, width=130)
                            dpg.add_button(label="Show Interpolation",
                                           callback=self.enhanced_keyframe_editor._show_interpolation_preview,
                                           width=130)
                            dpg.add_checkbox(label="Auto-validate", tag="auto_validate", default_value=True)

                        dpg.add_text("", tag="validation_status", color=(100, 255, 100))

                dpg.add_tab(label="|")

                with dpg.tab(label="Binds"):
                    dpg.add_text("Custom Actions", color=(255, 255, 0))
                    dpg.add_text("Format: cmd: <command> OR wait: <ms>")

                    def update_actions_list():
                        if dpg.does_item_exist("custom_actions_list"): dpg.delete_item("custom_actions_list",
                                                                                       children_only=True)
                        actions = self.preset_manager.get_presets("actions")
                        for name in actions:
                            with dpg.group(horizontal=True, parent="custom_actions_list"):
                                dpg.add_text(name);
                                dpg.add_button(label="Edit", user_data=name, callback=edit_action_callback);
                                dpg.add_button(label="Delete", user_data=name, callback=delete_action_callback)

                    def delete_action_callback(s, a, u):
                        self.preset_manager.delete_preset("actions", u);
                        self._add_debug_message(f"Action '{u}' deleted.");
                        update_actions_list();
                        self.update_hotkey_tab_ui()

                    def edit_action_callback(s, a, u):
                        steps = self.preset_manager.get_presets("actions").get(u, []);
                        text_block = "\n".join([f"{step['type']}: {step['value']}" for step in steps])
                        dpg.set_value("action_name_input", u);
                        dpg.set_value("action_editor_input", text_block);
                        dpg.configure_item("action_editor_window", show=True)

                    dpg.add_child_window(tag="custom_actions_list", height=150);
                    update_actions_list()
                    dpg.add_button(label="Create New Action", callback=lambda: (dpg.set_value("action_name_input", ""),
                                                                                dpg.set_value("action_editor_input",
                                                                                              ""), dpg.configure_item(
                            "action_editor_window", show=True)))
                    dpg.add_separator();
                    dpg.add_text("Hotkey Assignments", color=(255, 255, 0));
                    dpg.add_text("Requires admin privileges (Run as Admin)!", color=(255, 0, 0))
                    with dpg.table(header_row=True, tag="hotkey_table"):
                        pass
                    self.update_hotkey_tab_ui()

                    def save_hotkeys_callback():
                        new_config = {}
                        for action in self.hotkey_manager.bindable_actions: new_config[action] = dpg.get_value(
                            f"hotkey_input_{action}").lower()
                        for preset_type in ["animation", "flicker"]:
                            for name in self.preset_manager.get_presets(preset_type): new_config[
                                f"{preset_type}_preset:{name}"] = dpg.get_value(
                                f"hotkey_input_{preset_type}_preset:{name}").lower()
                        for name in self.preset_manager.get_presets("actions"): new_config[
                            f"custom:{name}"] = dpg.get_value(f"hotkey_input_custom:{name}").lower()
                        self.hotkeys = new_config;
                        self.hotkey_manager.reregister_all_hotkeys(self.hotkeys);
                        self._add_debug_message("Hotkeys have been updated.")

                    dpg.add_button(label="Save and Apply Hotkeys", callback=save_hotkeys_callback, width=-1)

                dpg.add_tab(label="|")

                with dpg.tab(label="Config"):
                    def refresh_list():
                        if dpg.does_item_exist("config_list_group"):
                            dpg.delete_item("config_list_group", children_only=True)
                        else:
                            dpg.add_group(tag="config_list_group", parent="config_loader_window")
                        for f in list_config_files(): dpg.add_button(label=f, width=-1, callback=load, user_data=f,
                                                                     parent="config_list_group")

                    def load(s, d, u):
                        config_data = load_config(u);
                        self._apply_config_to_ui(config_data)

                    def save():
                        name = dpg.get_value("save_name_input")
                        if name:
                            save_config(self.ui_vars, self.hotkeys, name);
                            self._add_debug_message(f"Saved config: {name}.ini");
                            refresh_list()
                        else:
                            self._add_debug_message("Please choose a file name.", is_error=True)

                    with dpg.group(horizontal=True):
                        with dpg.child_window(width=250, border=False):
                            dpg.add_text("Save Config");
                            dpg.add_input_text(label="", tag="save_name_input", width=-1)
                            dpg.add_button(label="Save", callback=save, width=-1)
                        with dpg.child_window(width=250, border=False, tag="config_loader_window"):
                            dpg.add_text("Load Config");
                            dpg.add_group(tag="config_list_group")
                    refresh_list()

                with dpg.tab(label="Debug"):
                    with dpg.group(horizontal=True): dpg.add_text("Debug Console"); dpg.add_button(label="Clear",
                                                                                                   callback=self._clear_debug_console)
                    with dpg.child_window(tag="debug_window", width=-1, height=-1,
                                          horizontal_scrollbar=True): dpg.add_text("Debug console loaded",
                                                                                   tag="debug_text", wrap=0)
                dpg.add_tab(label="|")

                with dpg.tab(label="UI Theme"):
                    self.theme_manager.create_theme_ui("UI Theme")

                dpg.add_tab(label="|")

                with dpg.tab(label="About"):
                    dpg.add_text("Made by Celine\nDiscord: ce.line", color=(255, 255, 0))
                    dpg.add_separator()
                    dpg.add_text("Special thanks to @Kruumy and @luckyy!", color=(255, 255, 0))
                    if dpg.does_item_exist("about_texture"): dpg.add_image("about_texture")


            with dpg.window(label="Edit Keyframe Values", modal=True, show=False,
                            tag="keyframe_edit_modal", width=500, height=600):
                dpg.add_text("Editing Keyframe", tag="kf_modal_title")
                dpg.add_separator()

                with dpg.collapsing_header(label="Basic Properties", default_open=True):
                    dpg.add_input_float(label="FOV", tag="kf_modal_fov", width=200)
                    dpg.add_input_float(label="Brightness", tag="kf_modal_brightness", width=200)
                    dpg.add_input_float(label="Contrast", tag="kf_modal_contrast", width=200)
                    dpg.add_input_float(label="Desaturation", tag="kf_modal_desaturation", width=200)
                    dpg.add_input_float(label="Fog Density", tag="kf_modal_fog_start", width=200)

                with dpg.collapsing_header(label="Color Properties", default_open=True):
                    dpg.add_color_edit(label="Fog Color", tag="kf_modal_fog_color", no_alpha=True, width=300)
                    dpg.add_color_edit(label="Light Tint", tag="kf_modal_light_color", no_alpha=True, width=300)
                    dpg.add_color_edit(label="Dark Tint", tag="kf_modal_dark_color", no_alpha=True, width=300)

                with dpg.collapsing_header(label="Sun Properties", default_open=True):
                    dpg.add_input_float(label="Sun Strength", tag="kf_modal_sun_strength", width=200)
                    dpg.add_input_float(label="Sun Dir X", tag="kf_modal_sun_direction_x", width=200)
                    dpg.add_input_float(label="Sun Dir Y", tag="kf_modal_sun_direction_y", width=200)
                    dpg.add_color_edit(label="Sun Color", tag="kf_modal_sun_color", no_alpha=True, width=300)

                dpg.add_separator()
                dpg.add_input_int(tag="kf_modal_index", show=False)

                with dpg.group(horizontal=True):
                    dpg.add_button(label="Save Changes", callback=self._save_keyframe_modal_changes)
                    dpg.add_button(label="Cancel",
                                   callback=lambda: dpg.configure_item("keyframe_edit_modal", show=False))

            with dpg.window(label="Action Editor", modal=True, show=False, tag="action_editor_window", width=400,
                            height=300):
                dpg.add_input_text(label="Action Name", tag="action_name_input")
                dpg.add_input_text(label="Commands", multiline=True, tag="action_editor_input", height=150, width=-1)

                def save_action():
                    name, text = dpg.get_value("action_name_input"), dpg.get_value("action_editor_input")
                    if not name: self._add_debug_message("Action name cannot be empty.", is_error=True); return
                    steps = []
                    for line in text.splitlines():
                        if not line.strip(): continue
                        match = re.match(r"^(cmd|wait):\s*(.*)", line.strip(), re.IGNORECASE)
                        if match:
                            steps.append({"type": match.group(1).lower(), "value": match.group(2).strip()})
                        else:
                            self._add_debug_message(f"Invalid syntax: '{line}'", is_error=True);
                            return
                    self.preset_manager.add_preset("actions", name, steps);
                    self._add_debug_message(f"Action '{name}' saved.")
                    dpg.configure_item("action_editor_window", show=False);
                    update_actions_list();
                    self.update_hotkey_tab_ui()

                with dpg.group(horizontal=True):
                    dpg.add_button(label="Save", callback=save_action)
                    dpg.add_button(label="Cancel",
                                   callback=lambda: dpg.configure_item("action_editor_window", show=False))

            self._add_debug_message(f"WAW Console started")
            if not self.memory_manager.is_connected():
                self._add_debug_message(self.memory_manager.status_message, is_error=True)
            else:
                self._add_debug_message(self.memory_manager.status_message)




if __name__ == "__main__":
    dpg.create_context()
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Text, (5, 5, 5));
            dpg.add_theme_color(dpg.mvThemeCol_Button, (25, 25, 25));
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (40, 40, 40));
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (55, 55, 55))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (49, 49, 49));
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (40, 40, 40));
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (55, 55, 55));
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (255, 105, 180));
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (255, 140, 200));
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (255, 105, 180))
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (40, 40, 40));
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (55, 55, 55));
            dpg.add_theme_color(dpg.mvThemeCol_Header, (255, 105, 180));
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (255, 140, 200));
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (255, 170, 220));
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (25, 25, 25));
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (40, 40, 40));
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10);
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 10);
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 10)
        with dpg.theme_component(dpg.mvWindowAppItem):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (0, 0, 0))
    dpg.bind_theme(global_theme)
    with dpg.texture_registry(show=False):
        try:
            width, height, channels, data = dpg.load_image(resource_path("about_logo.png"))
            dpg.add_static_texture(width=width, height=height, default_value=data, tag="about_texture")
        except Exception as e:
            print(f"Error loading about_logo.png: {e}")
    app = WAW_App_DPG()
    app.create_ui()
    dpg.create_viewport(title="WAW Console V1", width=660, height=900)
    dpg.set_primary_window("Primary Window", True)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()