import dearpygui.dearpygui as dpg
import math


class TimelineWidget:
    def __init__(self, app_instance):
        self.app = app_instance
        self.timeline_width = 600
        self.timeline_height = 80
        self.timeline_y_start = 20
        self.timeline_y_end = 100
        self.dragging_keyframe = None
        self.drag_offset = 0
        self.keyframe_size = 8
        self.snap_threshold = 0.2  # seconds

    def create_timeline(self, parent_tag):

        with dpg.group(parent=parent_tag):
            dpg.add_drawlist(width=self.timeline_width, height=120, tag="keyframe_timeline")

            dpg.add_invisible_button(label="timeline_interaction", width=self.timeline_width, height=120,
                                     callback=self._on_timeline_interaction)
        self.draw_timeline()

    def draw_timeline(self):
        if not dpg.does_item_exist("keyframe_timeline"):
            return

        dpg.delete_item("keyframe_timeline", children_only=True)

        total_duration = dpg.get_value("keyframe_total_duration") if dpg.does_item_exist(
            "keyframe_total_duration") else 10.0


        dpg.draw_rectangle((10, self.timeline_y_start), (self.timeline_width - 10, self.timeline_y_end),
                           color=(100, 100, 100), fill=(40, 40, 40), parent="keyframe_timeline")


        marker_interval = max(1, total_duration / 20)
        for i in range(int(total_duration / marker_interval) + 1):
            time_val = i * marker_interval
            x = self._time_to_x(time_val, total_duration)


            if i % 5 == 0:
                dpg.draw_line((x, self.timeline_y_start), (x, self.timeline_y_end),
                              color=(150, 150, 150), thickness=2, parent="keyframe_timeline")
                dpg.draw_text((x - 10, self.timeline_y_end + 5), f"{time_val:.1f}s",
                              size=10, color=(200, 200, 200), parent="keyframe_timeline")
            else:
                dpg.draw_line((x, self.timeline_y_start + 10), (x, self.timeline_y_end - 10),
                              color=(80, 80, 80), thickness=1, parent="keyframe_timeline")

        playhead_time = dpg.get_value("keyframe_playhead") if dpg.does_item_exist("keyframe_playhead") else 0.0
        playhead_x = self._time_to_x(playhead_time, total_duration)
        dpg.draw_line((playhead_x, self.timeline_y_start - 10), (playhead_x, self.timeline_y_end + 10),
                      color=(255, 255, 0), thickness=3, parent="keyframe_timeline")

        for i, kf in enumerate(self.app.current_keyframes):
            self._draw_keyframe(kf, i, total_duration)

    def _draw_keyframe(self, keyframe, index, total_duration):
        x = self._time_to_x(keyframe['time'], total_duration)
        y = (self.timeline_y_start + self.timeline_y_end) / 2

        if keyframe.get('selected', False):
            color = (255, 105, 180)
            fill_color = (255, 105, 180, 100)
        else:
            easing = keyframe.get('easing', 'Linear')
            color_map = {
                'Linear': (150, 150, 150),
                'Smooth': (100, 200, 100),
                'Ease-In': (200, 100, 100),
                'Ease-Out': (100, 100, 200)
            }
            color = color_map.get(easing, (150, 150, 150))
            fill_color = (*color, 80)

        points = [
            (x, y - self.keyframe_size),  # Top
            (x + self.keyframe_size, y),  # Right
            (x, y + self.keyframe_size),  # Bottom
            (x - self.keyframe_size, y)  # Left
        ]

        dpg.draw_polygon(points, color=color, fill=fill_color, parent="keyframe_timeline")

        dpg.draw_text((x - 15, y + self.keyframe_size + 5), f"{keyframe['time']:.1f}",
                      size=8, color=color, parent="keyframe_timeline")

    def _time_to_x(self, time, total_duration):
        if total_duration <= 0:
            return 20
        return 20 + (time / total_duration) * (self.timeline_width - 40)

    def _x_to_time(self, x, total_duration):
        if self.timeline_width <= 40:
            return 0
        return max(0, ((x - 20) / (self.timeline_width - 40)) * total_duration)

    def _find_keyframe_at_position(self, x, y):
        total_duration = dpg.get_value("keyframe_total_duration") if dpg.does_item_exist(
            "keyframe_total_duration") else 10.0
        timeline_center_y = (self.timeline_y_start + self.timeline_y_end) / 2

        if not (self.timeline_y_start - 10 <= y <= self.timeline_y_end + 10):
            return None

        for i, kf in enumerate(self.app.current_keyframes):
            kf_x = self._time_to_x(kf['time'], total_duration)

            if (abs(x - kf_x) <= self.keyframe_size + 5 and
                    abs(y - timeline_center_y) <= self.keyframe_size + 5):
                return i

        return None

    def _on_timeline_interaction(self, sender, app_data):
        if not dpg.does_item_exist("keyframe_timeline"):
            return

        mouse_pos = dpg.get_mouse_pos(local=False)

        button_pos = dpg.get_item_pos(sender)
        local_x = mouse_pos[0] - button_pos[0]
        local_y = mouse_pos[1] - button_pos[1]


        if dpg.is_mouse_button_down(dpg.mvMouseButton_Left):
            self._handle_mouse_down(local_x, local_y)
        else:
            self._handle_mouse_release()

    def _handle_mouse_down(self, local_x, local_y):

        keyframe_index = self._find_keyframe_at_position(local_x, local_y)

        if keyframe_index is not None:

            keyframes_copy = copy.deepcopy(self.app.current_keyframes)

            if dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift):
                keyframes_copy[keyframe_index]['selected'] = not keyframes_copy[keyframe_index].get('selected', False)
            else:

                for kf in keyframes_copy:
                    kf['selected'] = False
                keyframes_copy[keyframe_index]['selected'] = True

            self.app._execute_keyframe_action(keyframes_copy, "Select Keyframe")
            self.dragging_keyframe = keyframe_index


            total_duration = dpg.get_value("keyframe_total_duration") if dpg.does_item_exist(
                "keyframe_total_duration") else 10.0
            kf_x = self._time_to_x(keyframes_copy[keyframe_index]['time'], total_duration)
            self.drag_offset = local_x - kf_x
        else:

            total_duration = dpg.get_value("keyframe_total_duration") if dpg.does_item_exist(
                "keyframe_total_duration") else 10.0
            new_time = self._x_to_time(local_x, total_duration)
            new_time = max(0, min(total_duration, new_time))

            if dpg.does_item_exist("keyframe_playhead"):
                dpg.set_value("keyframe_playhead", new_time)

                if hasattr(self.app, '_scrub_to_time'):
                    self.app._scrub_to_time(None, new_time)

    def _handle_mouse_release(self):

        if self.dragging_keyframe is not None:

            self.app._execute_keyframe_action(self.app.current_keyframes, "Move Keyframe")
            self.dragging_keyframe = None
            self.drag_offset = 0

    def _on_timeline_click(self, sender, app_data):
        pass

    def _on_timeline_drag(self, sender, app_data):
        pass

    def _on_timeline_release(self, sender, app_data):
        pass

    def update_timeline(self):
        self.draw_timeline()