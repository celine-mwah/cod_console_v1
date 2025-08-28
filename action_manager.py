import threading
import time


class ActionManager:
    def __init__(self, memory_manager, debug_callback):
        self.memory_manager = memory_manager
        self._debug = debug_callback
        self.action_thread = None
        self.stop_action = False

    def execute_action(self, action_name, action_steps):

        if self.action_thread and self.action_thread.is_alive():
            self._debug(f"An action is already running. Please wait.", is_error=True)
            return

        self.stop_action = False
        self.action_thread = threading.Thread(target=self._worker, args=(action_name, action_steps))
        self.action_thread.daemon = True
        self.action_thread.start()

    def _worker(self, action_name, action_steps):
        ## step processing
        self._debug(f"Executing action: '{action_name}'...")
        for step in action_steps:
            if self.stop_action:
                self._debug(f"Action '{action_name}' stopped by user.")
                break

            step_type = step.get("type")
            value = step.get("value")

            if step_type == "command":
                self.memory_manager.execute_command(value)
            elif step_type == "wait":
                try:
                    ## convert ms to seconds
                    time.sleep(float(value) / 1000.0)
                except (ValueError, TypeError):
                    self._debug(f"Invalid wait time in action '{action_name}': {value}", is_error=True)

        self._debug(f"Action '{action_name}' finished.")