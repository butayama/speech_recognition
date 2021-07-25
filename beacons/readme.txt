	Beacons is a geometrical loop instrument based on the simplest possible configuration space.  It creates blinking circles ("beacons") that alternate between the notes corresponding to their x and y positions.

	Beacons was written for my own amusement, and as a result is very poorly documented.  I am at the beginning of a long process of making it public.

	This program is distributed in the hope that it will be useful, but without any warranty; without even the implied warranty of merchantability or fitness for a particular purpose.  

	The current version is for MAC ONLY.  If I can get it working I will try to produce a PC version next.

BEFORE YOU START:

	1. To run this program you need a MIDI output source.  If you have a MIDI keyboard you should be able to use it.  If not, a good, free option is the Independence sampler, which you can download here:

	https://www.magix.com/us/music/independence/

	2. If you are using a software instrument, like Independence, you may also need to turn on the "IAC Bus," if you haven't done so already. Search for "Audio MIDI setup," choose "Show MIDI Studio" (from the Window menu), click on "IAC Driver," and then check "Device is online."  Quit the program.

AFTER YOU RUN BEACONS:

	1. Choose midi output and input devices.  Your output device cannot be your input device as that will create a loop. 

	2. To make beacons hold down the left shift key and click on the screen; releasing the shift key starts the loop.

	3. There are many other commands documented below.

BASIC DOCUMENTATION:

	To create circles, hold left shift and click your rhythm on screen, moving the mouse as desired; releasing the left shift starts repeating the pattern.  Once created, circles can be moved (click and drag) or copied (option-click drag).  With option-click drag, the clock will start when you release the mouse button; command-option drag will start the clock immediately, synchronizing the copies with their originals.

	Holding control moves or copies an entire synchronized group.  You can also make a selection rectangle then click-drag or option-click-drag to move or copy.   Command-A selects all active circles. Many keyboard commands and mouse moves will affect the selection rectangle.  Command-'i' inverts the current selection

	To delete, hold x and click for immediate deletion; z for a more gradual fade out.  backspace or x will also delete the selection group.

	Numbers select output channel.  Command-number selects all circles on that channel.

	< and > increase and decrease the volume of the selected/clicked on circles.

	Hold down q or shift-q to enable only the x- or y- notes, respectively, alt-q will randomly choose either x-, y- or both notes for each selected circle; 'w' restores default behavior; 'shift-w' randomly selects x or y notes.  'y' plays both notes at once, shift-y (or 'q' or 'w') plays only one.

	Hold 'a' and throw circles!  '=' selects and stops or restarts all moving circles; 'command-=' silently selects them; shift-'=' eliminates the moveVector, making the object stationary.

	Holding 'm' while pressing 12345 + creates specialized modulations controlling common tones (1 = 1 changing note, 2 = 2 changing notes, etc.).  'm' + '`' is a random modulation 6 is a single semitone change, 7 is semitonal down, 8 is semitonal up; 9 transposes the current scale randomly.

	A fast m repeats the last modulation. 

	Hold s + number keys return to the nth scale (1 is the first, 2 the second, etc. qwerty = 11, 12, etc.).

	Hold 'p' + any key = recall the preset attached to that key; shift-p-key: store a preset there.  Shift-p (with no selection), followed by some notes, followed by shift-p-key stores a preset at k; preset x is a default preset that contains the most recently deleted items, z is the same for the most recent fade out items; algorithmic items are automatically saved in the corresponding preset (be careful here).

	'f' preserves the last rhythmic frequency for greater rhythmic synchronization; shift-f restores the default of independent frequencies; clicking a circle while pressing 'f' grabs its periodicity for the  future.

	f11 and f12 slow down and speed up the selected circle's frequency (shift-f11 and shift-f12 do it faster); alt-f11 or alt-f12 randomly change the selected items frequencies.

	g will cause the selected circles to change their frequency to a selected frequency; alt-g stores a frequency for this purpose, but if none is stored the last frequency is used; g plus a number controls the flock speed.


	'b' makes a burst of random circles; option b repeats the last burst at the new mouse position.

	'o' turns off sound.

	'l' turns on lines, shift-l turns off lines.

	'd' delays a circle from firing, to adjust timing: click on a group and press 'd'.

	spacebar makes the selection go away

	Still not documented:
	
	g: set flocking
	h: keyboard controlled notes
	j: scramble notes
	v: sends things moving, shift v returns to original position
	e: echoes
	r: return circles to their original state (should be able to reset this, maybe shift-r)

There is a max patch that can be used to drive an iPad telling performers what notes are being played
