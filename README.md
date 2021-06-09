# plover-xtest-input
Capture input from the xtest keyboard.

Only on systems that uses X.
Would be useful to use Plover from other machines from a remote control program
(TeamViewer, for example) if it uses xtest keyboard to send key presses.

Note: must not be used together with the default output method
(which uses xtest to simulate key presses. That will create an infinite loop).

Alternative output methods include [plover-uinput-output](https://github.com/user202729/plover-uinput-output)
(works better, but does not support full Unicode), and [plover-unused-xtest-output](https://github.com/user202729/plover-unused-xtest-output)
(doesn't work as well, especially with keyboard shortcuts)

For testing, `xdotool` can be used.

### Machines

When the plugin is installed, two additional machines are listed,
`XTEST keyboard` and `XTEST serial keyboard`.

* `XTEST keyboard` captures the key up/key down events like from a normal keyboard.
* `XTEST serial keyboard` captures the key presses events from the XTEST keyboard, then
   decode it to a chord using some algorithm (see the source code for details).

   This was implemented to use Plover over TeamViewer/Dotterel. To use it, you should
   download Dotterel (some version that includes [this commit](https://github.com/user202729/dotterel/commit/ba36bd4ffe59626999b98fa1aeaa9e403c80e2ba).
   You may need to build it from source), disable all the dictionaries and only keep the
   `SerialEncoding` dictionary, then use it normally.
