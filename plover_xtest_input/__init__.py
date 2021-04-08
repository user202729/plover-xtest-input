from typing import Optional

from Xlib.ext import xinput

from plover.machine.base import StenotypeBase
from plover.machine.keyboard import Keyboard
from plover.oslayer.xkeyboardcontrol import KeyboardCapture
from plover import system


class XTESTKeyboardCapture(KeyboardCapture):
    def _update_devices(self)->None:
        self._devices = [
                devinfo.deviceid
                for devinfo in self._display.xinput_query_device(xinput.AllDevices).devices
                if 'Virtual core XTEST keyboard' == devinfo.name
                ]


class XTESTKeyboard(Keyboard):
    def start_capture(self)->None:
        self._initializing()
        try:
            self._keyboard_capture: Optional[KeyboardCapture] = XTESTKeyboardCapture()
            self._keyboard_capture.key_down = self._key_down
            self._keyboard_capture.key_up = self._key_up
            self._suppress()
            self._keyboard_capture.start()
        except:
            self._error()
            raise
        self._ready()


class XTestSerialKeyboard(StenotypeBase):
    USED_KEYS = [chr(x) for x in range(ord('a'), ord('a')+16)] + ['z']

    def __init__(self, params: dict)->None:
        assert not params
        super().__init__()
        self._sequence: str = ""

    def start_capture(self)->None:
        self._initializing()
        try:
            self._keyboard_capture : Optional[KeyboardCapture] = XTESTKeyboardCapture()
            self._keyboard_capture.key_down = self._key_down
            self._keyboard_capture.key_up = self._key_up
            self._keyboard_capture.suppress_keyboard(self.USED_KEYS)
            self._keyboard_capture.start()
        except:
            self._error()
            raise
        self._ready()

    def stop_capture(self)->None:
        """Stop listening for output from the stenotype machine."""
        if self._keyboard_capture is not None:
            self._is_suppressed = False
            self._keyboard_capture.suppress_keyboard()
            self._keyboard_capture.cancel()
            self._keyboard_capture = None
        self._stopped()

    def _key_down(self, key: str)->None:
        pass

    def _key_up(self, key: str)->None:
        # 'a' for example

        #print(self.keymap.get_keys())
        # empty, but it doesn't matter...

        #print(self.keymap.get_actions())
        # extraneous no-op

        #keys = ['#', 'S-', 'T-', 'K-', 'P-', 'W-', 'H-', 'R-', 'A-', 'O-', '*', '-E', '-U', '-F', '-R', '-P', '-B', '-L', '-G', '-T', '-S', '-D', '-Z']
        #assert len(keys)==23
        # should be system.KEYS

        keys = system.KEYS
        if key not in self.USED_KEYS:
            return

        if key=='z':
            if len(self._sequence)==6:
                stroke = []
                for i in range(6):
                    value = ord(self._sequence[i])-ord('a')
                    for bit in range(4):
                        if value >> bit & 1:
                            stroke.append(keys[i*4+bit])
                self._notify(stroke)
            self._sequence = ""
        else:
            self._sequence += key

        # it would be bad if the order is not the same as in Dotterel's side...
