#from plover.machine.base import StenotypeBase
from plover.machine.keyboard import Keyboard
from plover.oslayer.xkeyboardcontrol import KeyboardCapture
from Xlib.ext import xinput


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
            self._keyboard_capture = XTESTKeyboardCapture()
            self._keyboard_capture.key_down = self._key_down
            self._keyboard_capture.key_up = self._key_up
            self._suppress()
            self._keyboard_capture.start()
        except:
            self._error()
            raise
        self._ready()
