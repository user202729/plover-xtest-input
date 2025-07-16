from typing import Optional

from collections import OrderedDict
from pathlib import Path
from threading import Thread, Lock
from queue import Queue
import json
import asyncio

from plover.machine.base import StenotypeBase
from plover.misc import boolean
from plover.oslayer.keyboardcontrol import KeyboardCapture
from plover.steno import Stroke
from plover.oslayer.config import CONFIG_DIR

from Xlib import X, XK
from Xlib.display import Display
from Xlib.ext import xinput, xtest
from Xlib.ext.ge import GenericEventCode

XINPUT_EVENT_MASK = xinput.KeyPressMask | xinput.KeyReleaseMask

from plover.machine.base import StenotypeBase
from plover.machine.keyboard import Keyboard
try:
    from plover.oslayer.linux.keyboardcontrol_x11 import KeyboardCapture, KEY_TO_KEYCODE
except ImportError:
    from plover.oslayer.xkeyboardcontrol import KeyboardCapture, KEY_TO_KEYCODE
from plover import system


class XTESTKeyboardCapture(KeyboardCapture):
    def _update_devices(self, display)->bool:
        self._devices = [
                devinfo.deviceid
                for devinfo in display.xinput_query_device(xinput.AllDevices).devices
                if 'Virtual core XTEST keyboard' == devinfo.name
                ]
        self._window = display.screen().root
        print(self._devices)
        return True
 
    def _grab_key(self, keycode):
        for deviceid in self._devices:
            self._window.xinput_grab_keycode(deviceid,
                                             X.CurrentTime,
                                             keycode,
                                             xinput.GrabModeAsync,
                                             xinput.GrabModeAsync,
                                             True,
                                             XINPUT_EVENT_MASK,
                                             (0, X.Mod2Mask))

    def _ungrab_key(self, keycode):
        for deviceid in self._devices:
            self._window.xinput_ungrab_keycode(deviceid,
                                               keycode,
                                               (0, X.Mod2Mask))

    def _suppress_keys(self, suppressed_keys):
        suppressed_keys = set(suppressed_keys)
        if self._suppressed_keys == suppressed_keys:
            return
        for key in self._suppressed_keys - suppressed_keys:
            self._ungrab_key(KEY_TO_KEYCODE[key])
            self._suppressed_keys.remove(key)
        for key in suppressed_keys - self._suppressed_keys:
            self._grab_key(KEY_TO_KEYCODE[key])
            self._suppressed_keys.add(key)
        assert self._suppressed_keys == suppressed_keys


class XTESTKeyboard(Keyboard):
    def start_capture(self)->None:
        """Begin listening for output from the stenotype machine."""
        self._initializing()
        self._current_state_index = 0
        """
        The variable above is used to detect if a combination is held for long enough, it works as follows.

        Whenever the set _down_keys changes, a timer is set to be fired in some time duration (e.g. 0.1 seconds).
        If the set _down_keys has not changed the whole time, and it is a special action,
        then the action is fired.

        In order to detect if the set changed within the given time duration, the state index is increased
        for every change of _down_keys.
        """
        self._current_state = None
        self._current_task = None
        self._loop = asyncio.new_event_loop()
        self._stroke_on_release = None
        self._events = Queue()
        self._lock = Lock()
        self._thread_object = Thread(target=self._thread_fn)
        self._thread_object.start()

        # idea: hold TPWHR for holding shift etc.
        self._special_actions = {}
        import itertools
        for i in itertools.product(
                (Stroke(0), Stroke("T")),
                (Stroke(0), Stroke("K")),
                (Stroke(0), Stroke("A")),
                (Stroke(0), Stroke("O")),
                ):
            s=sum(i, Stroke("PWR*"))
            self._special_actions[s] = (s|Stroke("-FBLSD"), s|Stroke("-RPGTZ"))
            self._special_actions[s-Stroke("*")+Stroke("#")] = (s|Stroke("-FBLSD"), s|Stroke("-RPGTZ"))  # starboard stuff…

        try:
            self._keyboard_capture = XTESTKeyboardCapture()
            self._keyboard_capture.on_ready = self._ready
            self._keyboard_capture.on_error = self._error
            self._keyboard_capture.key_down = self._key_down
            #self._keyboard_capture.key_up = self._delayed_key_up
            self._keyboard_capture.key_up = self._key_up
            if self._keyboard_capture.start():
                self._ready()
            else:
                self._error()
            self._update_suppression()
        except:
            self._error()
            raise


class XTestSerialKeyboard(StenotypeBase):
    USED_KEYS = [chr(x) for x in range(ord('a'), ord('a')+16)] + ['z']

	# this "machine" doesn't really have a key layout;
	# rather, it reads directly from system.KEYS
	# this is just to suppress the warning

    KEYS_LAYOUT = '''
        #  #  #  #  #  #  #  #  #  #
        S- T- P- H- * -F -P -L -T -D
        S- K- W- R- * -R -B -G -S -Z
               A- O- -E -U
    '''
    KEYMAP_MACHINE_TYPE = 'TX Bolt'

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
