import threading
import time
import json


class SequenceBuilder:
## chains all visuals together to create transitions between presets

    def __init__(self, app_instance, debug_callback):
        self.app = app_instance
        self._debug = debug_callback
        self.sequence_thread = None
        self.stop_sequence = False
        self.is_running = False
        self.duration_multiplier = 1.0

    def execute_sequence(self, sequence_name, sequence_steps, duration_multiplier=1.0):

        if self.sequence_thread and self.sequence_thread.is_alive():
            self._debug(f"A sequence is already running. Please wait.", is_error=True)
            return

        self.stop_sequence = False
        self.is_running = True
        self.duration_multiplier = duration_multiplier if duration_multiplier > 0 else 1.0
        self.sequence_thread = threading.Thread(
            target=self._sequence_worker,
            args=(sequence_name, sequence_steps)
        )
        self.sequence_thread.daemon = True
        self.sequence_thread.start()

    def _sequence_worker(self, sequence_name, sequence_steps):
        self._debug(f"Starting sequence: '{sequence_name}' (Speed: {self.duration_multiplier}x)")

        for i, step in enumerate(sequence_steps):
            if self.stop_sequence:
                self._debug(f"Sequence '{sequence_name}' stopped by user.")
                break

            step_type = step.get("type")

            if i == 0 and step_type == "environment":
                self._debug("First step is environment, converting to smooth transition.")
                step_type = "transition"
                step["to"] = step.get("name")
                step["duration"] = 4000  #default 4 sec transition

            if step_type == "animation":
                preset_name = step.get("preset")
                self.app.apply_anim_preset(None, preset_name)

                preset_data = self.app.builtin_anim_presets.get(preset_name)
                if preset_data is None:
                    preset_data = self.app.preset_manager.get_presets("animation").get(preset_name)

                if preset_data:
                    base_duration = preset_data.get("duration") or preset_data.get("rev_duration")
                    final_duration = (base_duration / self.duration_multiplier) if base_duration else None
                    self.app.start_animation(duration_override=final_duration)
                else:
                    # if preset isnt found fall back to default values
                    self.app.start_animation()

                if step.get("wait_for_completion"):
                    while self.app.sun_animator.is_animating and not self.stop_sequence:
                        time.sleep(0.1)

            elif step_type == "flicker":
                self.app.apply_flicker_preset(None, step.get("preset"))
                self.app.start_flicker()

            elif step_type == "environment":
                self.app.apply_environment_preset(step.get("name"))

            elif step_type == "transition":
                to_preset = step.get("to")
                duration_ms = float(step.get("duration", 3000)) / self.duration_multiplier
                self.app.transition_to_environment(to_preset, duration_ms)
                ## wait for the tranny to finish herself off
                while self.app.is_transitioning and not self.stop_sequence:
                    time.sleep(0.1)

            elif step_type == "command":
                self.app.memory_manager.execute_command(step.get("value"))

            elif step_type == "wait":
                try:
                    wait_ms = float(step.get("value")) / self.duration_multiplier
                    time.sleep(wait_ms / 1000.0)
                except (ValueError, TypeError):
                    self._debug(f"Invalid wait time: {step.get('value')}", is_error=True)

            elif step_type == "stop_effects":
                self.app.stop_animation()

        self._debug(f"Sequence '{sequence_name}' completed.")
        self.is_running = False

    def stop(self):
        self.stop_sequence = True
        if self.app.is_transitioning:
            self.app.stop_transition = True