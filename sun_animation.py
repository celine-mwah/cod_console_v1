import threading
import time
import random
import math


class SunAnimationSystem:
    def __init__(self, memory_manager, ui_callback):
        self.memory_manager = memory_manager
        self.ui_callback = ui_callback
        self.animation_thread = None
        self.stop_animation = False
        self.is_animating = False
        self._debug = memory_manager._debug
        self.current_interpolated_values = {}  # store currently values
        self._debug = memory_manager._debug if hasattr(memory_manager, '_debug') else print

    @staticmethod
    def lerp(start, end, t):
        return start + (end - start) * t

    @staticmethod
    def ease_in_out_cubic(t):
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def ease_in_quad(t):
        return t * t

    @staticmethod
    def ease_out_quad(t):
        return 1 - (1 - t) * (1 - t)

    def _start_thread(self, worker_func, on_complete, *args):
        if self.is_animating:
            self.stop()
            time.sleep(0.2)
        self.stop_animation = False
        self.is_animating = True
        self.animation_thread = threading.Thread(target=worker_func, args=(on_complete, *args))
        self.animation_thread.daemon = True
        self.animation_thread.start()

    def animate_sun_direction(self, start_x, end_x, start_y, end_y, duration, fps, easing, reset_on_finish,
                              on_complete=None):
        self._start_thread(self._linear_worker, on_complete, start_x, end_x, start_y, end_y, duration, fps, easing,
                           reset_on_finish)

    def animate_sun_orbital(self, center_x, center_y, radius_x, radius_y, rev_duration, direction, on_complete=None):
        self._start_thread(self._orbital_worker, on_complete, center_x, center_y, radius_x, radius_y, rev_duration,
                           direction)

    def animate_from_keyframes(self, keyframes, total_duration, easing_functions, on_complete=None):
        ## valdiate before starting
        if not self._validate_keyframes_for_animation(keyframes):
            if on_complete:
                on_complete()
            return

        self._start_thread(self._keyframe_worker, on_complete, keyframes, total_duration, easing_functions)

    def _validate_keyframes_for_animation(self, keyframes):
        if len(keyframes) < 2:
            self._debug("Need at least 2 keyframes for animation", is_error=True)
            return False

        for i, kf in enumerate(keyframes):
            if not kf.get('values'):
                self._debug(f"Keyframe {i + 1} has no properties set", is_error=True)
                return False

        times = [kf['time'] for kf in keyframes]
        if times != sorted(times):
            self._debug("Keyframes are not in chronological order", is_error=True)
            return False

        if len(times) != len(set(times)):
            self._debug("Multiple keyframes have the same time - this will break interpolation", is_error=True)
            return False

        return True

    def _keyframe_worker(self, on_complete, keyframes, total_duration, easing_functions):
        start_time = time.time()
        frame_delay = 1.0 / 60.0

        while not self.stop_animation:
            elapsed = time.time() - start_time

            if elapsed >= total_duration:
                # set final values from last keyframe
                final_values = self.interpolate_values_at_time(total_duration, keyframes, easing_functions)
                if final_values:
                    self.update_all_properties(final_values)
                break

            interpolated_values = self.interpolate_values_at_time(elapsed, keyframes, easing_functions)
            if interpolated_values:
                self.update_all_properties(interpolated_values)

            time.sleep(frame_delay)

        self.is_animating = False
        if on_complete:
            on_complete()

    def interpolate_values_at_time(self, elapsed_time, keyframes, easing_functions):
        if not keyframes:
            return {}

        # if before first keyframes, return fisrt keyframe values
        if elapsed_time <= keyframes[0]['time']:
            return keyframes[0]['values'].copy()

        # if after last keyframe, return last keyframe values
        if elapsed_time >= keyframes[-1]['time']:
            return keyframes[-1]['values'].copy()

        ## find surrounding keyframes
        prev_kf = keyframes[0]
        next_kf = keyframes[-1]

        for i in range(len(keyframes) - 1):
            if keyframes[i]['time'] <= elapsed_time < keyframes[i + 1]['time']:
                prev_kf = keyframes[i]
                next_kf = keyframes[i + 1]
                break

        ## calc interp factors
        segment_duration = next_kf['time'] - prev_kf['time']
        if segment_duration <= 0:
            return prev_kf['values'].copy()

        t = (elapsed_time - prev_kf['time']) / segment_duration
        #apply easing
        easing_func = easing_functions.get(prev_kf.get('easing', 'Linear'), lambda t: t)
        eased_t = easing_func(t)

        p_vals = prev_kf['values']
        n_vals = next_kf['values']
        interpolated = {}

        all_properties = set(p_vals.keys()) | set(n_vals.keys())

        for key in all_properties:

            prev_val = p_vals.get(key)
            next_val = n_vals.get(key)


            if prev_val is None:
                interpolated[key] = next_val
            elif next_val is None:
                interpolated[key] = prev_val
            else:

                if isinstance(prev_val, (int, float)):
                    interpolated[key] = self.lerp(prev_val, next_val, eased_t)
                elif isinstance(prev_val, list) and isinstance(next_val, list):

                    if len(prev_val) == len(next_val):
                        interpolated[key] = [self.lerp(prev_val[i], next_val[i], eased_t)
                                             for i in range(len(prev_val))]
                    else:

                        interpolated[key] = next_val if eased_t > 0.5 else prev_val
                else:

                    interpolated[key] = next_val if eased_t > 0.5 else prev_val

        self.current_interpolated_values = interpolated.copy()
        return interpolated

    def get_current_animation_values(self):
        return self.current_interpolated_values.copy()

    def _linear_worker(self, on_complete, start_x, end_x, start_y, end_y, duration, fps, easing, reset_on_finish):
        start_time = time.time()
        frame_delay = 1.0 / fps

        while not self.stop_animation:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                self.update_all_properties({"sun_direction_x": end_x, "sun_direction_y": end_y})
                break

            progress = elapsed / duration
            if easing == "smooth":
                progress = self.ease_in_out_cubic(progress)
            elif easing == "ease-in":
                progress = self.ease_in_quad(progress)
            elif easing == "ease-out":
                progress = self.ease_out_quad(progress)

            current_x = self.lerp(start_x, end_x, progress)
            current_y = self.lerp(start_y, end_y, progress)

            values = {"sun_direction_x": current_x, "sun_direction_y": current_y}
            self.current_interpolated_values = values.copy()
            self.update_all_properties(values)

            time.sleep(frame_delay)

        if not self.stop_animation and reset_on_finish:
            time.sleep(0.1)
            reset_values = {"sun_direction_x": 0, "sun_direction_y": 0}
            self.current_interpolated_values = reset_values.copy()
            self.update_all_properties(reset_values)

        self.is_animating = False
        if on_complete:
            on_complete()

    def _orbital_worker(self, on_complete, center_x, center_y, radius_x, radius_y, rev_duration, direction):
        start_time = time.time()
        dir_multiplier = -1 if direction == "Clockwise" else 1

        while not self.stop_animation:
            elapsed = time.time() - start_time
            angle = (elapsed / rev_duration) * 2 * math.pi * dir_multiplier
            current_x = center_x + radius_x * math.cos(angle)
            current_y = center_y + radius_y * math.sin(angle)

            values = {"sun_direction_x": current_x, "sun_direction_y": current_y}
            self.current_interpolated_values = values.copy()
            self.update_all_properties(values)

            time.sleep(1 / 60)

        self.is_animating = False
        if on_complete:
            on_complete()

    def update_all_properties(self, values):
        try:
            if 'sun_strength' in values and values['sun_strength'] is not None:
                self.memory_manager.execute_command(f"r_lighttweaksunlight {values['sun_strength']:.2f}")

            if 'sun_direction_x' in values and 'sun_direction_y' in values:
                if values['sun_direction_x'] is not None and values['sun_direction_y'] is not None:
                    self.memory_manager.execute_command(
                        f"r_lighttweaksundirection {values['sun_direction_x']:.2f} {values['sun_direction_y']:.2f}")
            elif 'sun_direction_x' in values and values['sun_direction_x'] is not None:
                ## if only x is selected get the current y value
                current_y = values.get('sun_direction_y', 0.0)
                self.memory_manager.execute_command(
                    f"r_lighttweaksundirection {values['sun_direction_x']:.2f} {current_y:.2f}")

            if 'sun_color' in values and values['sun_color'] is not None:
                c = values['sun_color']
                if isinstance(c, list) and len(c) >= 3:
                    self.memory_manager.execute_command(f"r_lighttweaksuncolor {c[0]:.2f} {c[1]:.2f} {c[2]:.2f}")

            if 'brightness' in values and values['brightness'] is not None:
                self.memory_manager.execute_command(f"r_filmtweakbrightness {values['brightness']:.2f}")

            if 'contrast' in values and values['contrast'] is not None:
                self.memory_manager.execute_command(f"r_filmtweakcontrast {values['contrast']:.2f}")

            if 'desaturation' in values and values['desaturation'] is not None:
                self.memory_manager.execute_command(f"r_filmtweakdesaturation {values['desaturation']:.2f}")

            if 'light_color' in values and values['light_color'] is not None:
                c = values['light_color']
                if isinstance(c, list) and len(c) >= 3:
                    self.memory_manager.execute_command(f"r_filmtweaklighttint {c[0]:.2f} {c[1]:.2f} {c[2]:.2f}")

            if 'dark_color' in values and values['dark_color'] is not None:
                c = values['dark_color']
                if isinstance(c, list) and len(c) >= 3:
                    self.memory_manager.execute_command(f"r_filmtweakdarktint {c[0]:.2f} {c[1]:.2f} {c[2]:.2f}")

            if 'fog_start' in values and values['fog_start'] is not None:
                self.memory_manager.execute_command(f"mvm_fog_start {values['fog_start']:.2f}")

            if 'fog_color' in values and values['fog_color'] is not None:
                c = values['fog_color']
                if isinstance(c, list) and len(c) >= 3:
                    self.memory_manager.execute_command(f"mvm_fog_color {c[0]:.2f} {c[1]:.2f} {c[2]:.2f}")
                    if hasattr(self, '_debug'):
                        self._debug(f"Setting fog color: {c[0]:.2f} {c[1]:.2f} {c[2]:.2f}")

            ## fov is handled different because of glichting
            if 'fov' in values and values['fov'] is not None:
                self.memory_manager.execute_command(f"cg_fov {int(values['fov'])}")

            ## update ui callback
            if self.ui_callback:
                ## filter "none" values before starting
                filtered_values = {k: v for k, v in values.items() if v is not None}
                if filtered_values:
                    self.ui_callback(filtered_values)

        except Exception as e:
            print(f"Error updating properties: {e}")

    def stop(self):
        self.stop_animation = True
        self.current_interpolated_values = {}


class SunFlickerSystem:
    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.flicker_thread = None
        self.stop_flicker = False
        self.is_flickering = False
        self.original_strength = 1.0

    def _fade_strength(self, start, end, duration):
        steps = 20
        step_delay = duration / steps if steps > 0 else 0
        for i in range(steps + 1):
            if self.stop_flicker:
                break
            progress = i / steps
            current_strength = SunAnimationSystem.lerp(start, end, progress)
            self.memory_manager.execute_command(f"r_lighttweaksunlight {current_strength:.2f}")
            if step_delay > 0:
                time.sleep(step_delay)

    def start(self, strength, speed_ms, preset="Pulse", use_easing=False):
        if self.is_flickering:
            self.stop()
            time.sleep(0.2)
        self.stop_flicker = False
        self.is_flickering = True
        self.original_strength = strength if strength > 0 else 1.0
        delay = max(0.01, speed_ms / 1000.0)

        def flicker_worker():
            initial_strength = self.original_strength
            while not self.stop_flicker:
                on_action = lambda: self._fade_strength(0, self.original_strength,
                                                        delay) if use_easing else self.memory_manager.execute_command(
                    f"r_lighttweaksunlight {self.original_strength:.2f}")
                off_action = lambda: self._fade_strength(self.original_strength, 0,
                                                         delay) if use_easing else self.memory_manager.execute_command(
                    f"r_lighttweaksunlight 0")

                if preset == "Pulse":
                    off_action()
                    time.sleep(delay if not use_easing else 0)
                    if self.stop_flicker:
                        break
                    on_action()
                    time.sleep(delay if not use_easing else 0)
                elif preset == "Faulty":
                    on_action()
                    time.sleep(random.uniform(0.02, 0.2))
                    if self.stop_flicker:
                        break
                    off_action()
                    time.sleep(random.uniform(delay * 0.5, delay * 1.5))
                elif preset == "Strobe":
                    on_action()
                    time.sleep(0.02 if not use_easing else 0)
                    if self.stop_flicker:
                        break
                    off_action()
                    time.sleep(delay)
                elif preset == "Storm":
                    for _ in range(random.randint(2, 4)):
                        if self.stop_flicker:
                            break
                        on_action()
                        time.sleep(random.uniform(0.02, 0.05))
                        off_action()
                        time.sleep(random.uniform(0.02, 0.08))
                    if self.stop_flicker:
                        break
                    time.sleep(random.uniform(3.0, 8.0))
                elif preset == "Heartbeat":
                    on_action()
                    time.sleep(0.1 if not use_easing else 0)
                    off_action()
                    time.sleep(0.1 if not use_easing else 0)
                    if self.stop_flicker:
                        break
                    on_action()
                    time.sleep(0.1 if not use_easing else 0)
                    off_action()
                    time.sleep(delay)
                elif preset == "Candle":
                    current_strength = self.original_strength * random.uniform(0.7, 0.95)
                    fade_duration = random.uniform(delay * 0.8, delay * 1.2)
                    self._fade_strength(self.original_strength, current_strength, fade_duration)
                    if self.stop_flicker:
                        break
                    self.original_strength = current_strength

            ## restore original strength
            self.memory_manager.execute_command(f"r_lighttweaksunlight {initial_strength}")
            self.is_flickering = False

        self.flicker_thread = threading.Thread(target=flicker_worker)
        self.flicker_thread.daemon = True
        self.flicker_thread.start()

    def stop(self):
        self.stop_flicker = True