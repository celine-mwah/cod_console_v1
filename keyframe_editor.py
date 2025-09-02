import dearpygui.dearpygui as dpg
import copy
import math
import time


class SliderTimelineWidget:
    def __init__(self, app_instance):
        self.app = app_instance
        self.selection_tolerance = 0.2
        self.last_click_time = 0
        self.double_click_threshold = 0.5

    def create_timeline(self, parent_tag):
        with dpg.group(parent=parent_tag):
            with dpg.group(horizontal=True):
                dpg.add_text("Time:", tag="timeline_current_time_label")
                dpg.add_text("0.00s", tag="timeline_current_time_display", color=(255, 255, 0))
                dpg.add_text("| Selected:", color=(150, 150, 150))
                dpg.add_text("None", tag="timeline_selected_display", color=(255, 105, 180))

            dpg.add_slider_float(
                label="",
                tag="interactive_timeline_slider",
                min_value=0.0,
                max_value=10.0,
                default_value=0.0,
                width=580,
                callback=self._timeline_slider_callback,
                format="%.2fs"
            )

            dpg.add_text("Keyframes: None", tag="timeline_keyframe_positions",
                         color=(150, 150, 150), wrap=580)

            with dpg.group(horizontal=True):
                dpg.add_button(label="<<", width=40, callback=lambda: self._jump_to_keyframe(-1))
                dpg.add_button(label=">>", width=40, callback=lambda: self._jump_to_keyframe(1))
                dpg.add_separator()
                dpg.add_button(label="Select Nearest", width=105, callback=self._select_nearest_keyframe)
                dpg.add_button(label="Add KF", width=100, callback=self._add_keyframe_at_playhead)
                dpg.add_button(label="Delete Selected", width=115, callback=self._delete_selected_from_timeline)
                dpg.add_button(label="Play Range", width=90, callback=self._play_preview_range)

        self.update_timeline()

    def _timeline_slider_callback(self, sender, app_data):
        current_time = app_data

        if dpg.does_item_exist("timeline_current_time_display"):
            dpg.set_value("timeline_current_time_display", f"{current_time:.2f}s")

        if dpg.does_item_exist("keyframe_playhead"):
            dpg.set_value("keyframe_playhead", current_time)

        current_click_time = time.time()

        if hasattr(self, '_last_slider_value'):
            value_change = abs(current_time - self._last_slider_value)
            if value_change > 0.1:
                self._handle_timeline_click(current_time)

        self._last_slider_value = current_time

        if hasattr(self.app, '_scrub_to_time') and not self.app.sun_animator.is_animating:
            self.app._scrub_to_time(None, current_time)

    def _handle_timeline_click(self, click_time):

        nearest_kf_index = self._find_nearest_keyframe_index(click_time)

        if nearest_kf_index is not None:
            kf = self.app.current_keyframes[nearest_kf_index]
            distance = abs(kf['time'] - click_time)

            if distance <= self.selection_tolerance:
                self._toggle_keyframe_selection(nearest_kf_index)
                self._update_selection_display()
                return True

        return False

    def _find_nearest_keyframe_index(self, time_position):
        if not self.app.current_keyframes:
            return None

        closest_index = 0
        min_distance = abs(self.app.current_keyframes[0]['time'] - time_position)

        for i, kf in enumerate(self.app.current_keyframes):
            distance = abs(kf['time'] - time_position)
            if distance < min_distance:
                min_distance = distance
                closest_index = i

        return closest_index

    def _toggle_keyframe_selection(self, keyframe_index):
        if 0 <= keyframe_index < len(self.app.current_keyframes):
            keyframes_copy = [kf.copy() for kf in self.app.current_keyframes]
            current_state = keyframes_copy[keyframe_index].get('selected', False)
            keyframes_copy[keyframe_index]['selected'] = not current_state

            self.app._execute_keyframe_action(keyframes_copy, f"Toggle KF {keyframe_index} Selection")

    def _jump_to_keyframe(self, direction):

        if not self.app.current_keyframes:
            return

        current_time = dpg.get_value("interactive_timeline_slider") if dpg.does_item_exist(
            "interactive_timeline_slider") else 0.0

        if direction > 0:
            next_kf = None
            for kf in self.app.current_keyframes:
                if kf['time'] > current_time + 0.01:
                    next_kf = kf
                    break
            if next_kf:
                self._set_timeline_position(next_kf['time'])
        else:
            prev_kf = None
            for kf in reversed(self.app.current_keyframes):
                if kf['time'] < current_time - 0.01:
                    prev_kf = kf
                    break
            if prev_kf:
                self._set_timeline_position(prev_kf['time'])

    def _set_timeline_position(self, time_position):

        if dpg.does_item_exist("interactive_timeline_slider"):
            dpg.set_value("interactive_timeline_slider", time_position)
        if dpg.does_item_exist("keyframe_playhead"):
            dpg.set_value("keyframe_playhead", time_position)

        if hasattr(self.app, '_scrub_to_time'):
            self.app._scrub_to_time(None, time_position)

    def _select_nearest_keyframe(self):
        current_time = dpg.get_value("interactive_timeline_slider") if dpg.does_item_exist(
            "interactive_timeline_slider") else 0.0
        nearest_index = self._find_nearest_keyframe_index(current_time)

        if nearest_index is not None:
            self._toggle_keyframe_selection(nearest_index)
            self._update_selection_display()

    def _add_keyframe_at_playhead(self):
        if hasattr(self.app, 'enhanced_keyframe_editor'):
            self.app.enhanced_keyframe_editor._add_selective_keyframe()

    def _delete_selected_from_timeline(self):
        if hasattr(self.app, 'enhanced_keyframe_editor'):
            self.app.enhanced_keyframe_editor._delete_selected_keyframes()

    def _play_preview_range(self):
        if hasattr(self.app, 'enhanced_keyframe_editor'):
            self.app.enhanced_keyframe_editor._play_preview_range()

    def update_timeline(self):
        total_duration = dpg.get_value("keyframe_total_duration") if dpg.does_item_exist(
            "keyframe_total_duration") else 10.0

        if dpg.does_item_exist("interactive_timeline_slider"):
            dpg.configure_item("interactive_timeline_slider", max_value=total_duration)

        self._update_keyframe_display()
        self._update_selection_display()

    def _update_keyframe_display(self):
        if not dpg.does_item_exist("timeline_keyframe_positions"):
            return

        if not self.app.current_keyframes:
            dpg.set_value("timeline_keyframe_positions", "Keyframes: None")
            return

        total_duration = dpg.get_value("keyframe_total_duration") if dpg.does_item_exist(
            "keyframe_total_duration") else 10.0
        timeline_length = 50

        timeline_chars = ['-'] * timeline_length

        for i, kf in enumerate(self.app.current_keyframes):
            if total_duration > 0:
                pos = int((kf['time'] / total_duration) * (timeline_length - 1))
                pos = max(0, min(timeline_length - 1, pos))

                if kf.get('selected', False):
                    timeline_chars[pos] = '●'
                else:
                    timeline_chars[pos] = '○'

        timeline_str = ''.join(timeline_chars)

        display_text = f"Timeline: [{timeline_str}]\nKeyframes: {len(self.app.current_keyframes)} total"
        if self.app.current_keyframes:
            times = [f"{kf['time']:.1f}s" for kf in self.app.current_keyframes]
            display_text += f"\nAt: {', '.join(times)}"

        dpg.set_value("timeline_keyframe_positions", display_text)

    def _update_selection_display(self):

        if not dpg.does_item_exist("timeline_selected_display"):
            return

        selected_keyframes = [i for i, kf in enumerate(self.app.current_keyframes) if kf.get('selected', False)]

        if not selected_keyframes:
            dpg.set_value("timeline_selected_display", "None")
        elif len(selected_keyframes) == 1:
            kf = self.app.current_keyframes[selected_keyframes[0]]
            dpg.set_value("timeline_selected_display", f"KF at {kf['time']:.2f}s")
        else:
            dpg.set_value("timeline_selected_display", f"{len(selected_keyframes)} keyframes")

    def get_timeline_position(self):

        return dpg.get_value("interactive_timeline_slider") if dpg.does_item_exist(
            "interactive_timeline_slider") else 0.0


class EnhancedKeyframeEditor:
    def __init__(self, app_instance):
        self.app = app_instance
        self.timeline_widget = SliderTimelineWidget(app_instance)
        self.keyframeable_properties = {
            "sun_strength": {"min": 0.0, "max": 8.0, "default": 1.4, "label": "Sun Strength"},
            "sun_direction_x": {"min": -360.0, "max": 360.0, "default": 0.0, "label": "Sun Dir X"},
            "sun_direction_y": {"min": -360.0, "max": 360.0, "default": 0.0, "label": "Sun Dir Y"},
            "brightness": {"min": -1.0, "max": 1.0, "default": 0.0, "label": "Brightness"},
            "contrast": {"min": 0.0, "max": 4.0, "default": 1.4, "label": "Contrast"},
            "desaturation": {"min": 0.0, "max": 1.0, "default": 0.2, "label": "Desaturation"},
            "fov": {"min": 5.0, "max": 165.0, "default": 65.0, "label": "FOV"},
            "fog_start": {"min": 1.0, "max": 9999.0, "default": 250.0, "label": "Fog Density"}
        }

        self.color_properties = {
            "sun_color": {"default": [1.0, 1.0, 1.0], "label": "Sun Color"},
            "light_color": {"default": [1.0, 1.0, 1.0], "label": "Light Tint"},
            "dark_color": {"default": [1.0, 1.0, 1.0], "label": "Dark Tint"},
            "fog_color": {"default": [1.0, 1.0, 1.0], "label": "Fog Color"}
        }

        self.selected_properties = set(self.keyframeable_properties.keys()) | set(self.color_properties.keys())
        self.keyframe_templates = self._load_keyframe_templates()

    def _load_keyframe_templates(self):
        return {
            "Sunrise": [
                {"time": 0.0, "easing": "Linear", "selected": False, "values": {
                    "sun_direction_y": -10, "brightness": -0.5, "sun_color": [0.8, 0.6, 0.4]}},
                {"time": 3.0, "easing": "Smooth", "selected": False, "values": {
                    "sun_direction_y": 20, "brightness": -0.2, "sun_color": [1.0, 0.8, 0.6]}},
                {"time": 5.0, "easing": "Ease-Out", "selected": False, "values": {
                    "sun_direction_y": 45, "brightness": 0.1, "sun_color": [1.2, 1.0, 0.8]}}
            ],
            "Sunset": [
                {"time": 0.0, "easing": "Linear", "selected": False, "values": {
                    "sun_direction_y": 45, "brightness": 0.1, "sun_color": [1.2, 1.0, 0.8]}},
                {"time": 3.0, "easing": "Smooth", "selected": False, "values": {
                    "sun_direction_y": 10, "brightness": -0.2, "sun_color": [1.5, 0.7, 0.4]}},
                {"time": 5.0, "easing": "Ease-In", "selected": False, "values": {
                    "sun_direction_y": -10, "brightness": -0.6, "sun_color": [0.8, 0.4, 0.2]}}
            ],
            "Fade to Black": [
                {"time": 0.0, "easing": "Linear", "selected": False, "values": {"brightness": 0.0}},
                {"time": 2.0, "easing": "Ease-In", "selected": False, "values": {"brightness": -1.0}}
            ],
            "FOV Zoom": [
                {"time": 0.0, "easing": "Linear", "selected": False, "values": {"fov": 65.0}},
                {"time": 1.0, "easing": "Smooth", "selected": False, "values": {"fov": 30.0}},
                {"time": 3.0, "easing": "Ease-Out", "selected": False, "values": {"fov": 65.0}}
            ],
            "Color Shift": [
                {"time": 0.0, "easing": "Linear", "selected": False, "values": {
                    "sun_color": [1.0, 1.0, 1.0], "light_color": [1.0, 1.0, 1.0]}},
                {"time": 2.0, "easing": "Smooth", "selected": False, "values": {
                    "sun_color": [2.0, 0.5, 0.5], "light_color": [1.5, 0.7, 0.7]}},
                {"time": 4.0, "easing": "Smooth", "selected": False, "values": {
                    "sun_color": [0.5, 0.5, 2.0], "light_color": [0.7, 0.7, 1.5]}}
            ]
        }

    def _sync_property_value(self, sender, app_data, user_data):
        prop_name = user_data

        if prop_name == "fov":
            self.app._safe_update_fov_ui(app_data, source="keyframe_editor")
            return

        self.app.ui_vars["doubles"][prop_name] = app_data


        if dpg.does_item_exist(prop_name):
            dpg.set_value(prop_name, app_data)

        command_map = {
            "sun_strength": "r_lighttweaksunlight",
            "sun_direction_x": "r_lighttweaksundirection",
            "sun_direction_y": "r_lighttweaksundirection",
            "brightness": "r_filmtweakbrightness",
            "contrast": "r_filmtweakcontrast",
            "desaturation": "r_filmtweakdesaturation",
            "fog_start": "mvm_fog_start"
        }

        if prop_name in ["sun_direction_x", "sun_direction_y"]:
            x = dpg.get_value("kf_sun_direction_x")
            y = dpg.get_value("kf_sun_direction_y")
            self.app.memory_manager.execute_command(f"r_lighttweaksundirection {x:.2f} {y:.2f}")
        elif prop_name in command_map:
            command = command_map[prop_name]
            self.app.memory_manager.execute_command(f"{command} {app_data:.2f}")

    def _sync_color_value(self, sender, app_data, user_data):
        prop_name = user_data

        rgb_internal = [c * 2.0 for c in app_data[:3]]
        self.app.ui_vars["colors"][prop_name] = rgb_internal


        main_tag = f"main_{prop_name}"
        if dpg.does_item_exist(main_tag):
            dpg.set_value(main_tag, app_data)
        elif dpg.does_item_exist(prop_name):
            dpg.set_value(prop_name, app_data)

        command_map = {
            "sun_color": "r_lighttweaksuncolor",
            "light_color": "r_filmtweaklighttint",
            "dark_color": "r_filmtweakdarktint",
            "fog_color": "mvm_fog_color"
        }

        if prop_name in command_map:
            command = command_map[prop_name]
            self.app.memory_manager.execute_command(
                f"{command} {rgb_internal[0]:.2f} {rgb_internal[1]:.2f} {rgb_internal[2]:.2f}")

    def _set_property_selection(self, selected_props):
        all_props = set(self.keyframeable_properties.keys()) | set(self.color_properties.keys())
        self.selected_properties.clear()

        for prop in all_props:
            tag = f"kf_prop_{prop}"
            should_select = prop in selected_props
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, should_select)
            if should_select:
                self.selected_properties.add(prop)

    def _select_sun_properties(self):
        sun_props = {"sun_strength", "sun_direction_x", "sun_direction_y", "sun_color"}
        self._set_property_selection(sun_props)

    def _select_visual_properties(self):
        visual_props = {"brightness", "contrast", "desaturation", "fov", "light_color", "dark_color"}
        self._set_property_selection(visual_props)

    def _select_fog_properties(self):
        fog_props = {"fog_start", "fog_color"}
        self._set_property_selection(fog_props)

    def _select_tint_properties(self):
        tint_props = {"light_color", "dark_color", "sun_color", "fog_color"}
        self._set_property_selection(tint_props)

    def _on_duration_change(self, sender, app_data):
        if dpg.does_item_exist("keyframe_playhead"):
            dpg.configure_item("keyframe_playhead", max_value=app_data)

        if dpg.does_item_exist("interactive_timeline_slider"):
            dpg.configure_item("interactive_timeline_slider", max_value=app_data)

        current_playhead = dpg.get_value("keyframe_playhead") if dpg.does_item_exist("keyframe_playhead") else 0.0
        if current_playhead > app_data:
            dpg.set_value("keyframe_playhead", app_data)
            if dpg.does_item_exist("interactive_timeline_slider"):
                dpg.set_value("interactive_timeline_slider", app_data)

        self.timeline_widget.update_timeline()

    def _toggle_property_selection(self, property_name, enabled):
        if enabled:
            self.selected_properties.add(property_name)
        else:
            self.selected_properties.discard(property_name)

    def _select_all_properties(self, select_all):
        all_props = set(self.keyframeable_properties.keys()) | set(self.color_properties.keys())

        for prop in all_props:
            tag = f"kf_prop_{prop}"
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, select_all)

        if select_all:
            self.selected_properties = all_props.copy()
        else:
            self.selected_properties.clear()

    def _add_selective_keyframe(self):
        time = self.timeline_widget.get_timeline_position()

        keyframes_copy = [kf for kf in self.app.current_keyframes if abs(kf['time'] - time) > 0.01]

        values = {}
        for prop in self.selected_properties:
            if prop in self.keyframeable_properties:
                current_value = self.app.ui_vars["doubles"].get(prop)
                if current_value is not None:
                    values[prop] = current_value

            elif prop in self.color_properties:
                current_color_list = self.app.ui_vars["colors"].get(prop)
                if current_color_list:
                    values[prop] = list(current_color_list)

        if not values:
            self.app._add_debug_message("No properties selected to keyframe.", is_error=True)
            return

        new_kf = {
            "time": time,
            "easing": "Linear",
            "selected": False,  ## new keyframe is not selected by default
            "values": values
        }

        keyframes_copy.append(new_kf)
        keyframes_copy.sort(key=lambda kf: kf['time'])

        self.app._execute_keyframe_action(keyframes_copy, f"Add KF at {time:.2f}s")
        self.app._add_debug_message(f"Added keyframe with {len(values)} properties at {time:.2f}s.")

        if dpg.does_item_exist("auto_validate") and dpg.get_value("auto_validate"):
            self._validate_keyframes()

    def _update_selected_keyframes(self):
        keyframes_copy = copy.deepcopy(self.app.current_keyframes)
        updated_count = 0

        for kf in keyframes_copy:
            if kf.get('selected', False):
                for prop in self.selected_properties:
                    if prop in self.keyframeable_properties:
                        kf['values'][prop] = self.app.ui_vars["doubles"].get(prop, self.keyframeable_properties[prop][
                            "default"])
                    elif prop in self.color_properties:
                        kf['values'][prop] = list(
                            self.app.ui_vars["colors"].get(prop, self.color_properties[prop]["default"]))
                updated_count += 1

        if updated_count > 0:
            self.app._execute_keyframe_action(keyframes_copy, f"Update {updated_count} keyframes")

    def _delete_selected_keyframes(self):
        keyframes_copy = [kf for kf in self.app.current_keyframes if not kf.get('selected', False)]
        deleted_count = len(self.app.current_keyframes) - len(keyframes_copy)

        if deleted_count > 0:
            self.app._execute_keyframe_action(keyframes_copy, f"Delete {deleted_count} keyframes")

    def _copy_selected_keyframes(self):
        self.app.keyframe_clipboard = [copy.deepcopy(kf) for kf in self.app.current_keyframes
                                       if kf.get('selected', False)]
        self.app.keyframe_clipboard.sort(key=lambda k: k['time'])

        if self.app.keyframe_clipboard:
            self.app._add_debug_message(f"Copied {len(self.app.keyframe_clipboard)} keyframe(s).")

    def _paste_keyframes(self):
        if not self.app.keyframe_clipboard:
            self.app._add_debug_message("Clipboard is empty.", is_error=True)
            return

        paste_time = self.timeline_widget.get_timeline_position()
        keyframes_copy = copy.deepcopy(self.app.current_keyframes)

        if self.app.keyframe_clipboard:
            time_offset = paste_time - self.app.keyframe_clipboard[0]['time']

            for kf in self.app.keyframe_clipboard:
                new_kf = copy.deepcopy(kf)
                new_kf['time'] += time_offset
                new_kf['selected'] = True
                keyframes_copy.append(new_kf)

        keyframes_copy.sort(key=lambda k: k['time'])
        self.app._execute_keyframe_action(keyframes_copy, "Paste Keyframes")

    def _distribute_keyframes_evenly(self):
        selected_kfs = [(i, kf) for i, kf in enumerate(self.app.current_keyframes) if kf.get('selected', False)]

        if len(selected_kfs) < 3:
            self.app._add_debug_message("Need at least 3 selected keyframes to distribute evenly.", is_error=True)
            return

        selected_times = [kf['time'] for _, kf in selected_kfs]
        min_time = min(selected_times)
        max_time = max(selected_times)
        time_span = max_time - min_time

        keyframes_copy = copy.deepcopy(self.app.current_keyframes)

        for i, (orig_idx, _) in enumerate(selected_kfs):
            if i == 0 or i == len(selected_kfs) - 1:
                continue
            new_time = min_time + (time_span * i / (len(selected_kfs) - 1))
            for j, kf in enumerate(keyframes_copy):
                if j == orig_idx:
                    kf['time'] = new_time
                    break

        keyframes_copy.sort(key=lambda k: k['time'])
        self.app._execute_keyframe_action(keyframes_copy, "Distribute Keyframes Evenly")

    def _apply_bulk_easing(self, sender, app_data):
        if not app_data:
            return

        keyframes_copy = copy.deepcopy(self.app.current_keyframes)
        updated_count = 0

        for kf in keyframes_copy:
            if kf.get('selected', False):
                kf['easing'] = app_data
                updated_count += 1

        if updated_count > 0:
            self.app._execute_keyframe_action(keyframes_copy, f"Set {updated_count} keyframes to {app_data}")

    def _load_keyframe_template(self):
        template_name = dpg.get_value("keyframe_template_combo")
        if not template_name or template_name not in self.keyframe_templates:
            return

        template_kfs = copy.deepcopy(self.keyframe_templates[template_name])

        if template_kfs:
            max_time = max(kf['time'] for kf in template_kfs)
            dpg.set_value("keyframe_total_duration", max_time)

            if dpg.does_item_exist("keyframe_playhead"):
                dpg.set_value("keyframe_playhead", 0.0)
                dpg.configure_item("keyframe_playhead", max_value=max_time)
            if dpg.does_item_exist("interactive_timeline_slider"):
                dpg.set_value("interactive_timeline_slider", 0.0)
                dpg.configure_item("interactive_timeline_slider", max_value=max_time)

        self.app._execute_keyframe_action(template_kfs, f"Load Template: {template_name}")

    def _save_keyframe_template(self):
        name = dpg.get_value("template_name_input")
        if not name:
            self.app._add_debug_message("Please enter a template name.", is_error=True)
            return

        self.keyframe_templates[name] = copy.deepcopy(self.app.current_keyframes)

        items = list(self.keyframe_templates.keys())
        dpg.configure_item("keyframe_template_combo", items=items)
        dpg.set_value("keyframe_template_combo", name)

        self.app._add_debug_message(f"Template '{name}' saved.")

    def _validate_keyframes(self):
        issues = []

        if len(self.app.current_keyframes) < 2:
            issues.append("At least 2 keyframes required for animation")

        times = [kf['time'] for kf in self.app.current_keyframes]
        if len(times) != len(set(times)):
            issues.append("Keyframes cannot have identical times")

        if times != sorted(times):
            issues.append("Keyframes are not in chronological order")

        for i, kf in enumerate(self.app.current_keyframes):
            if not kf.get('values'):
                issues.append(f"Keyframe {i + 1} has no properties")

        total_duration = None
        if dpg.does_item_exist("keyframe_total_duration"):
            total_duration = dpg.get_value("keyframe_total_duration")

        if total_duration is not None:
            for i, kf in enumerate(self.app.current_keyframes):
                if kf['time'] > total_duration:
                    issues.append(f"Keyframe {i + 1} time exceeds total duration")
        else:
            issues.append("Animation duration control not found in UI")

        if issues:
            status_text = "Issues found: " + "; ".join(issues)
            color = (255, 100, 100)
        else:
            status_text = "Keyframes are valid"
            color = (100, 255, 100)

        if dpg.does_item_exist("validation_status"):
            dpg.set_value("validation_status", status_text)
            dpg.configure_item("validation_status", color=color)

        return len(issues) == 0

    def _show_interpolation_preview(self):
        if not self.app.current_keyframes:
            return

        current_time = self.timeline_widget.get_timeline_position()
        interpolated = self.app.sun_animator.interpolate_values_at_time(
            current_time, self.app.current_keyframes, self.app.easing_functions)

        if not dpg.does_item_exist("interpolation_preview_window"):
            with dpg.window(label="Interpolation Preview", tag="interpolation_preview_window",
                            width=400, height=300, show=True):
                dpg.add_text("Interpolated values at current playhead time:", color=(255, 255, 0))
                dpg.add_separator()
                with dpg.child_window(tag="interpolation_values_container"):
                    pass
        else:
            dpg.configure_item("interpolation_preview_window", show=True)

        dpg.delete_item("interpolation_values_container", children_only=True)

        for key, value in interpolated.items():
            if isinstance(value, list):
                value_str = f"[{', '.join(f'{v:.2f}' for v in value)}]"
            else:
                value_str = f"{value:.2f}"

            dpg.add_text(f"{key}: {value_str}", parent="interpolation_values_container")

    def update_keyframe_list(self):
        if not dpg.does_item_exist("enhanced_keyframe_table"):
            return

        dpg.delete_item("enhanced_keyframe_table", children_only=True)

        dpg.add_table_column(label="Sel", width_fixed=True, init_width_or_weight=30, parent="enhanced_keyframe_table")
        dpg.add_table_column(label="Time", width_fixed=True, init_width_or_weight=80, parent="enhanced_keyframe_table")
        dpg.add_table_column(label="Easing", width_fixed=True, init_width_or_weight=100,
                             parent="enhanced_keyframe_table")
        dpg.add_table_column(label="Properties", width_stretch=True, init_width_or_weight=0.5,
                             parent="enhanced_keyframe_table")
        dpg.add_table_column(label="Actions", width_fixed=True, init_width_or_weight=120,
                             parent="enhanced_keyframe_table")

        for i, kf in enumerate(self.app.current_keyframes):
            with dpg.table_row(parent="enhanced_keyframe_table"):
                def toggle_select(s, d, u):
                    keyframes_copy = copy.deepcopy(self.app.current_keyframes)
                    keyframes_copy[u]['selected'] = d
                    self.app._execute_keyframe_action(keyframes_copy, "Select Keyframe")

                dpg.add_checkbox(default_value=kf.get('selected', False), user_data=i, callback=toggle_select)

                def time_changed(s, d, u):
                    keyframes_copy = copy.deepcopy(self.app.current_keyframes)
                    keyframes_copy[u]['time'] = d
                    keyframes_copy.sort(key=lambda k: k['time'])
                    self.app._execute_keyframe_action(keyframes_copy, "Edit Keyframe Time")

                dpg.add_input_float(default_value=kf['time'], user_data=i, callback=time_changed,
                                    width=80, step=0.1, format="%.2f")

                def easing_changed(s, d, u):
                    keyframes_copy = copy.deepcopy(self.app.current_keyframes)
                    keyframes_copy[u]['easing'] = d
                    self.app._execute_keyframe_action(keyframes_copy, "Edit Keyframe Easing")

                dpg.add_combo(items=self.app.easing_options, default_value=kf.get('easing', 'Linear'),
                              user_data=i, callback=easing_changed, width=100)

                prop_count = len(kf.get('values', {}))
                prop_names = ', '.join(list(kf.get('values', {}).keys())[:3])
                if prop_count > 3:
                    prop_names += f" (+{prop_count - 3} more)"
                dpg.add_text(f"{prop_count} props: {prop_names}")

                with dpg.group(horizontal=True):
                    dpg.add_button(label="Edit", user_data=i, callback=self.app._open_keyframe_editor_modal, width=50)

                    def delete_keyframe(s, a, u):
                        keyframes_copy = copy.deepcopy(self.app.current_keyframes)
                        keyframes_copy.pop(u)
                        self.app._execute_keyframe_action(keyframes_copy, "Delete Keyframe")

                    dpg.add_button(label="Del", user_data=i, callback=delete_keyframe, width=50)

    def sync_from_main_ui(self):
        for prop in self.keyframeable_properties:
            kf_tag = f"kf_{prop}"
            if dpg.does_item_exist(kf_tag):
                main_value = self.app.ui_vars["doubles"].get(prop)
                if main_value is not None:
                    dpg.set_value(kf_tag, main_value)

        for prop in self.color_properties:
            kf_tag = f"kf_{prop}"
            if dpg.does_item_exist(kf_tag):
                main_color = self.app.ui_vars["colors"].get(prop)
                if main_color is not None:
                    dpg.set_value(kf_tag, [c / 2.0 for c in main_color])

    def on_keyframes_changed(self):
        self.timeline_widget.update_timeline()
        self.update_keyframe_list()

        if dpg.does_item_exist("auto_validate") and dpg.get_value("auto_validate"):
            self._validate_keyframes()

    def _reverse_selected_keyframes(self):
        selected_kfs = [kf for kf in self.app.current_keyframes if kf.get('selected', False)]

        if len(selected_kfs) < 2:
            self.app._add_debug_message("Need at least 2 selected keyframes to reverse.", is_error=True)
            return

        min_time = min(kf['time'] for kf in selected_kfs)
        max_time = max(kf['time'] for kf in selected_kfs)

        keyframes_copy = copy.deepcopy(self.app.current_keyframes)

        for kf in keyframes_copy:
            if kf.get('selected', False):
                kf['time'] = max_time - (kf['time'] - min_time)

        keyframes_copy.sort(key=lambda k: k['time'])
        self.app._execute_keyframe_action(keyframes_copy, "Reverse Selected Keyframes")