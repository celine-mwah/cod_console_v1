import pymem
import pymem.process
import ctypes
import psutil
from constants import GAME_PROFILES


## memory manager
class MemoryManager:
    def __init__(self):
        self.pm = None
        self.module_base = None
        self.debug_callback = None
        self.connected_game_profile = None  # stores detected game profile
        self.status_message = "No supported game found."
        self.auto_connect()

    def find_running_game(self):

        running_processes = {p.name() for p in psutil.process_iter(['name'])}
        for process_name, profile in GAME_PROFILES.items():
            if process_name in running_processes:
                return process_name, profile  # # return the first match
        return None, None

    def auto_connect(self):
        ## attempts to connect to game
        process_name, profile = self.find_running_game()

        if not process_name:
            self._debug("No supported game found.", is_error=True)
            self.status_message = "No supported game found."
            return

        try:
            self.pm = pymem.Pymem(process_name)
            self.module_base = pymem.process.module_from_name(self.pm.process_handle, process_name).lpBaseOfDll
            self.connected_game_profile = profile
            self.status_message = f"Connected to {profile['friendly_name']}"
            self._debug(f"Successfully connected to {process_name} - Base: {hex(self.module_base)}")
        except (pymem.exception.ProcessNotFound, AttributeError) as e:
            self._debug(f"Failed to connect to {process_name}: {e}", is_error=True)
            self.status_message = f"Error connecting to {process_name}."
            self.pm = None
            self.module_base = None
            self.connected_game_profile = None

    def set_debug_callback(self, callback):
        self.debug_callback = callback

    def _debug(self, message, is_error=False):
        if self.debug_callback:
            self.debug_callback(message, is_error)
        print(f"{'[ERROR]' if is_error else '[INFO]'} {message}")

    def is_connected(self):
        return self.pm is not None and self.connected_game_profile is not None

    def execute_command(self, command: str, value: int = 0):
        if not self.is_connected():
            return

        # use the cbuf_addtext addresse from the detected game profile
        cbuf_addtext_offset = self.connected_game_profile['cbuf_addtext']

        command_bytes = (command + "\n").encode('ascii') + b'\x00'
        command_addr = self.pm.allocate(len(command_bytes))
        self.pm.write_bytes(command_addr, command_bytes, len(command_bytes))

        shellcode = (
                b"\xB8" + command_addr.to_bytes(4, 'little') +
                b"\xB9" + value.to_bytes(4, 'little') +
                b"\xBA" + cbuf_addtext_offset.to_bytes(4, 'little') +  # dynamic address
                b"\xFF\xD2" +
                b"\xC3"
        )

        shellcode_addr = self.pm.allocate(len(shellcode))
        self.pm.write_bytes(shellcode_addr, shellcode, len(shellcode))

        thread_handle = ctypes.windll.kernel32.CreateRemoteThread(
            self.pm.process_handle, None, 0, shellcode_addr, None, 0, None
        )

        if thread_handle:
            ctypes.windll.kernel32.WaitForSingleObject(thread_handle, 0xFFFFFFFF)
            ctypes.windll.kernel32.CloseHandle(thread_handle)
        else:
            self._debug("Failed to create remote thread.", is_error=True)

        self.pm.free(command_addr)
        self.pm.free(shellcode_addr)