class Action:

    def __init__(self, app):
        self.app = app

    def do(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError


class ModifyKeyframesAction(Action):

    def __init__(self, app, old_keyframes, new_keyframes, description="Modify Keyframes"):
        super().__init__(app)
        self.old_keyframes = [kf.copy() for kf in old_keyframes]
        self.new_keyframes = [kf.copy() for kf in new_keyframes]
        self.description = description

    def do(self):
        self.app.current_keyframes = self.new_keyframes
        self.app._update_keyframe_list_ui()
        self.app._add_debug_message(self.description)

    def undo(self):
        self.app.current_keyframes = self.old_keyframes
        self.app._update_keyframe_list_ui()
        self.app._add_debug_message(f"Undo: {self.description}")


class HistoryManager:
    def __init__(self, app):
        self.app = app
        self.undo_stack = []
        self.redo_stack = []

    def execute_action(self, action):
        action.do()
        self.undo_stack.append(action)
        self.redo_stack.clear()
        self._update_buttons()

    def undo(self):
        if not self.undo_stack:
            self.app._add_debug_message("Nothing to undo.")
            return
        action = self.undo_stack.pop()
        action.undo()
        self.redo_stack.append(action)
        self._update_buttons()

    def redo(self):
        if not self.redo_stack:
            self.app._add_debug_message("Nothing to redo.")
            return
        action = self.redo_stack.pop()
        action.do()
        self.undo_stack.append(action)
        self._update_buttons()

    def _update_buttons(self):
        import dearpygui.dearpygui as dpg
        if dpg.does_item_exist("undo_button"):
            dpg.configure_item("undo_button", enabled=bool(self.undo_stack))
        if dpg.does_item_exist("redo_button"):
            dpg.configure_item("redo_button", enabled=bool(self.redo_stack))