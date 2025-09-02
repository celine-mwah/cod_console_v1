import dearpygui.dearpygui as dpg
import math


class SliderTimelineWidget:
    def __init__(self, app_instance):
        self.app = app_instance
        self.selection_tolerance = 0.2
        self.last_click_time = 0
        self.double_click_threshold = 0.5

    def create_timeline(self, parent_tag):
        with dpg.group(parent=parent_tag):
            dpg.add_text("Interactive Timeline", color=(255, 255, 0))

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
                dpg.add_button(label="Back", width=40, callback=lambda: self._jump_to_keyframe(-1))
                dpg.add_button(label="Forward", width=40, callback=lambda: self._jump_to_keyframe(1))
                dpg.add_separator()
                dpg.add_button(label="Select Nearest", width=100, callback=self._select_nearest_keyframe)
                dpg.add_button(label="Add KF Here", width=100, callback=self._add_keyframe_at_playhead)
                dpg.add_button(label="Delete Selected", width=100, callback=self._delete_selected_from_timeline)

        self.update_timeline()

    def _timeline_slider_callback(self, sender, app_data):
        current_time = app_data

        if dpg.does_item_exist("timeline_current_time_display"):
            dpg.set_value("timeline_current_time_display", f"{current_time:.2f}s")

        if dpg.does_item_exist("keyframe_playhead"):
            dpg.set_value("keyframe_playhead", current_time)

        import time
        current_click_time = time.time()

        if hasattr(self, '_last_slider_value'):
            value_change = abs(current_time - self._last_slider_value)
            if value_change > 0.1:  # Significant jump suggests a click
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
        timeline_length = 100  # Character length of text timeline

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

        marker_positions = []
        for i in range(0, int(total_duration) + 1, max(1, int(total_duration / 10))):
            pos = int((i / total_duration) * (timeline_length - 1)) if total_duration > 0 else 0
            marker_positions.append(f"{i}s@{pos}")

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
        """Get current timeline position"""
        return dpg.get_value("interactive_timeline_slider") if dpg.does_item_exist(
            "interactive_timeline_slider") else 0.0