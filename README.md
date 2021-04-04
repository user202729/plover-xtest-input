# plover-xtest-input
Capture input from the xtest keyboard.

Only on systems that uses X.
Would be useful to use Plover from other machines from a remote control program
(TeamViewer, for example) if it uses xtest keyboard to send key presses.

Note: must not be used together with the default output method
(which uses xtest to simulate key presses. That will create an infinite loop).

For testing, `xdotool` can be used.
