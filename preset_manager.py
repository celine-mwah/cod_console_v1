import json
import os

class PresetManager:
    def __init__(self, filename='custom_presets.json'):
        self.filename = filename
        self.presets = {
            "animation": {},
            "flicker": {},
            "actions": {},
            "keyframe": {}
        }
        self.load_presets()

    def load_presets(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    loaded_data = json.load(f)
                    self.presets["animation"] = loaded_data.get("animation", {})
                    self.presets["flicker"] = loaded_data.get("flicker", {})
                    self.presets["actions"] = loaded_data.get("actions", {})
                    self.presets["keyframe"] = loaded_data.get("keyframe", {})
            except (json.JSONDecodeError, IOError):
                print(f"[ERROR] Could not load or parse {self.filename}. Starting fresh.")
        else:
            print(f"[INFO] No presets file found. A new '{self.filename}' will be created.")

    def save_presets(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.presets, f, indent=4)
        except IOError:
            print(f"[ERROR] Could not save presets to {self.filename}.")

    def get_presets(self, preset_type):

        return self.presets.get(preset_type, {})

    def add_preset(self, preset_type, name, data):
        if preset_type in self.presets and name:
            self.presets[preset_type][name] = data
            self.save_presets()
            return True
        return False

    def delete_preset(self, preset_type, name):
        if preset_type in self.presets and name in self.presets[preset_type]:
            del self.presets[preset_type][name]
            self.save_presets()
            return True
        return False