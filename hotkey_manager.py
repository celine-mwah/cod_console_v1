import keyboard
import dearpygui.dearpygui as dpg


class HotkeyManager:
    def __init__(self, app_instance):
        """
        :param app_instance: A reference to the main app instance.
        """
        self.app = app_instance
        self.bindable_actions = {
            'start_animation': 'Start Sun Animation',
            'stop_animation': 'Stop All Effects',
            'start_flicker': 'Start Sun Flicker',
            'stop_flicker': 'Stop Sun Flicker',
        }

    def _adjust_fov(self, step):
        # helper to adjust fov
        current_fov = self.app.ui_vars["doubles"].get("fov", 65.0)
        min_fov, max_fov = 5.0, 165.0


        new_fov = current_fov + step
        new_fov = max(min_fov, min(max_fov, new_fov))  # clamp value

        self.app.ui_vars["doubles"]["fov"] = new_fov
        if dpg.does_item_exist("fov"):
            dpg.set_value("fov", new_fov)
        self.app.memory_manager.execute_command(f"cg_fov {int(new_fov)}")

    def _increase_fov(self):

        self._adjust_fov(1)  #increase fov by 1

    def _decrease_fov(self): #decrease fov by 1
        self._adjust_fov(-1)

    def reregister_all_hotkeys(self, hotkey_config):

        try:
            keyboard.unhook_all()
        except Exception:
            try:
                keyboard.unhook_all_hotkeys()
            except Exception as e:
                self.app._add_debug_message(f"Could not unhook hotkeys: {e}", is_error=True)

        # reg standard hotkeys from the config file
        for action_name, hotkey in hotkey_config.items():
            if not hotkey:
                continue

            try:
                action_func = None
                if action_name.startswith("custom:"):
                    preset_name = action_name.split(":", 1)[1]
                    action_func = lambda name=preset_name: self.app.execute_custom_action(name)
                elif action_name.startswith("animation_preset:"):
                    preset_name = action_name.split(":", 1)[1]
                    action_func = lambda name=preset_name: self.app.execute_animation_preset(name)
                elif action_name.startswith("flicker_preset:"):
                    preset_name = action_name.split(":", 1)[1]
                    action_func = lambda name=preset_name: self.app.execute_flicker_preset(name)
                else:
                    action_func = getattr(self.app, action_name)

                if action_func:
                    keyboard.add_hotkey(hotkey, action_func)
                    self.app._add_debug_message(f"Hotkey '{hotkey}' registered for '{action_name}'.")

            except AttributeError:
                self.app._add_debug_message(f"Action '{action_name}' not found for hotkey.", is_error=True)
            except Exception as e:
                self.app._add_debug_message(f"Failed to register hotkey '{hotkey}': {e}", is_error=True)

        # Register the persistent hotkeys for FOV adjustment
        try:
            keyboard.add_hotkey('e', self._increase_fov)
            keyboard.add_hotkey('q', self._decrease_fov)
            self.app._add_debug_message("Registered Q/E hotkeys for FOV adjusting.")
        except Exception as e:
            self.app._add_debug_message(f"Failed to register Q/E keys: {e}", is_error=True)