from __future__ import print_function		# helps make the code python 3 compatible

_DIMENSION = 800  							# 1000 is better for some projectors
"""set the height and width of the window and turn off multitouch simulation, which is the default right-click behavior"""
from kivy.config import Config
#Config.set('kivy', 'log_level', 'critical')					# can uncomment it for more uncluttered execution
#Config.set('kivy', 'log_enable', 0)							# but when programming, comment them out
Config.set('graphics', 'width', str(_DIMENSION))
Config.set('graphics', 'height', str(_DIMENSION))
Config.set('graphics','resizable',0)							# prevents resizing
Config.set('graphics', 'kivy_clock', 'interrupt')				# better timing
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window

import time
import functools
import random
import copy
import pickle
import colorsys

import rtmidi

_SIZERANGE = [0, 5]
_MOVEOPACITY = .2
_BURSTRADIUS = 300
_NUMCHANNELS = 14
_OFFOPACITY = .15

"""

A geometrical loop instrument based on the simplest possible configuration space.

It creates blinking circles ("beacons") that alternate between the notes corresponding to their x and y positions.

To create circles, hold left shift and click your rhythm on screen, moving the mouse as desired; releasing the left shift starts 
repeating the pattern.  Once created, circles can be moved (click and drag) or copied (option-click drag).  With option-click drag,
the clock will start when you release the mouse button; command-option drag will start the clock immediately, to synchronize the copies
with their originals.

Holding control moves or copies the entire synchronized group.  You can also make a selection rectangle then click-drag or option-click-drag to move or copy. 
Command-A selects all active circles. Many keyboard commands and mouse moves will affect the selection rectangle.

To delete, hold x and click for immediate deletion; z for a more gradual fade out.  backspace or x will also delete the selection group

< and > increase and decrease the volume of the selected/clicked on circles.

Hold down q or shift-q to enable only the x- or y- notes, respectively, alt-q will randomly choose either x-, y- or both notes for each selected circle; 
'w' restores default behavior; 'shift-w' randomly selects x or y notes.  'y' plays both notes at once, shift-y (or QW) plays only one

't' disables repetition and creates single-use circles; shift-t or qwer will restore default behavior.  [CUT THIS?]

Hold 'a' and throw circles!  '=' selects and stops or restarts all moving circles; 'command-=' silently selects them; 
	shift-'=' eliminates the moveVector, making the object stationary

command-'i' inverts the current selection

holding 'm' while pressing 12345 + creates specialized modulations controlling common tones (1 = 1 changing note, 2 = 2 changing notes, etc.).  'm' + '`' is a random modulation
	6 is a single semitone change, 7 is semitonal down, 8 is semitonal up; 9 transposes the current scale randomly 
	a fast m modulates

hold s + number keys return to the nth scale (1 is the first, 2 the second, etc. qwerty = 11, 12, etc.  TODO: clear scales)

hold 'p' + any key = recall the preset attached to that key; shift-p-key: store a preset there.  shift p (with no selection), followed by some notes, followed by shift-p-key 
stores a preset at k; preset x is a default preset that contains the most recently deleted items, z is the same for the most recent fade out items; algorithmic items are automatically saved in the corresponding preset (be careful here)

'f' preserves the last rhythmic frequency for greater rhythmic synchronization; shift-f restores the default of independent frequencies;
clicking a circle while pressing 'f' grabs its periodicity for the  future

f11 and f12 slow down and speed up the selected circle's frequency (shift-f11 and shift-f12 do it faster); alt-f11 or alt-f12 randomly change the selected items frequencies

g will cause the selected circles to change their frequency to a selected frequency; alt-g stores a frequency for this purpose, but if none is stored the last frequency is used; g plus a number controls the flock speed

numbers select output channel.  command-number selects all circles on that channel

'b' makes a burst of random circles; option b repeats the last burst at the new mouse position; holding t while pressing b creates single-shot circles (burst in periodicity mode? should work)

'o' turns off sound

'l' turns on lines, shift-l turns off lines

'd' delays a circle from firing, to adjust timing: click on a group and press 'd'

spacebar makes the selection go away

'\' dumps all information; shift-'\' sends all notes off to the current channel

g: set flocking
h: keyboard controlled notes
j: scramble notes
v: sends things moving, shift v returns to original position
e: echoes
r: return circles to their original state (should be able to reset this, maybe shift-r)


There is a max patch that can be used to drive an iPad telling performers what notes are being played

TODO:

	frequency is a weird parameter -- 
		it is playing two separate roles right now, depending on whether an object has rhythmIntervals or not.  
		We should get rid of the case where the object doesn't have have rhythmIntervals: here frequency is the time between on and off; 
		in the other case it is the length of the whole pattern.

	RHYTHMINTERVALS could be floats expressed in units of frequency; then we never have to recompute them, though we have to compute on clock start.

	problem with partnerwidgets -- some things I do assume it has self in it, but it will be blank; default should be [self], but maybe more things

	sometimes a circle loses its opacity and keeps going, I think because of phase relationships between the circle and the FPS drawing; adding jitter to the frame rate could help?

	can we use control to set the rhythm? that would make control an all-purpose grouping button
	deal correctly with a resized window
	UNDO?

"""

"""routines copied from DTmidi"""

def note_on(p = 60, v = 112, c = 1):
	return [143 + c, p, v]

def note_off(p = 60, v = 0, c = 1):
	return [127 + c, p, v]

def control_change(number = 0, value = 0, channel = 1):
	return [175 + channel, number, value]

def program_change(program = 0, channel = 1):
	return [191+ channel, program]

def releaseIO(midiin, midiout):
	if midiin: 
		midiin.close_port()
		del midiin
	if midiout: 
		midiout.close_port()
		del midiout

def select_port(portList, inputPorts = True):
	
	lineSpace = .1
	
	if not portList:
		return None
	
	if len(portList) > 7:
		lineSpace = .7/len(portList)

	inputPorts = int(inputPorts)
	portType = ['output', 'input'][inputPorts]
	
	if inputPorts:
		mainGame.screen_print("The (optional) available input ports are:", yPos = 1 - lineSpace, refnumber = -1)
	else:
		mainGame.screen_print("An output port is required.  The available MIDI ports are:", yPos = 1 - lineSpace, refnumber = -1)
		
	for i, name in enumerate(portList):
		mainGame.screen_print("  " + str(i + 1) + " " + name, yPos = 1 - ((2. + i)*lineSpace), refnumber = i)
		
	if inputPorts:
		mainGame.screen_print("Click on a port to select it; to select no port click here.", yPos = 1 - ((3+i) * lineSpace), refnumber = -1)
	else:
		mainGame.screen_print("Click on a port to select it.", yPos = 1 - ((3+i) * lineSpace), refnumber = -1)
	
	return None
	
def get_midi_output():
	mainGame.selectedPort = None
	mainGame.targetPort = 0
	mainGame.midiout = rtmidi.MidiOut()
	mainGame.availablePorts = mainGame.midiout.get_ports()
	p = select_port(mainGame.availablePorts, inputPorts = False)
	Clock.schedule_once(check_for_user_input, .1)
	
def check_for_user_input(dt = 0):
	
	if mainGame.selectedPort is not None:
		if mainGame.targetPort == 0:
			mainGame.midiout.open_port(mainGame.selectedPort)
			mainGame.outputPortName = mainGame.availablePorts[mainGame.selectedPort]
			mainGame.selectedPort = None
			mainGame.midiin = rtmidi.MidiIn()
			mainGame.targetPort = 1
			for w in mainGame.textWidgets:
				mainGame.remove_widget(w)
			mainGame.textWidgets = []
			mainGame.availablePorts = mainGame.midiout.get_ports()
			p = select_port(mainGame.availablePorts, inputPorts = True)
			Clock.schedule_once(check_for_user_input, .1)
		else:
			if mainGame.selectedPort >= 0 and (mainGame.availablePorts[mainGame.selectedPort] != mainGame.outputPortName):
				mainGame.midiin.open_port(mainGame.selectedPort)
			else:
				mainGame.midiin = False
			for w in mainGame.textWidgets:
				mainGame.remove_widget(w)
			mainGame.textWidgets = []
			Clock.unschedule(check_for_user_input)
			mainGame.initialize_midi()
	else:
		Clock.schedule_once(check_for_user_input, .1)

"""useful for finding temporary print statements"""
def debug(*args):
	print(*args)

"""utility routine to map a value in firstRange into secondRange; this is probably built into python somewhere"""
def linear_map(value, firstRange, secondRange):
	pct = 1.0 * (value - firstRange[0])/(firstRange[1] - firstRange[0])
	output = secondRange[0] + pct*(secondRange[1] - secondRange[0])
	return output
	
"""get a random point on the screen"""
def random_point():
	return [linear_map(random.randrange(0, 1000), [0, 1000], mainGame.xyBoundaries[i]) for i in [0, 1]]

"""get pixel size from percentage of screen width"""
def window_based_size(x, dimension = 0):					
	return (x * mainGame.xyBoundaries[dimension][1]/100.) + mainGame.xyBoundaries[dimension][0]

"""supply note offs automatically"""
def make_note(note, velocity, channel = 1, duration = .8):
	velocity = abs(min(velocity, 127))
	midiMessage = note_on(note, velocity, channel)
	mainGame.master_MIDI_out(midiMessage)
	if duration:
		newMessage = [[midiMessage[0], midiMessage[1], 0]] 				# or [[midiMessage[0], midiMessage[1], 0]]
		schedule_event(duration, mainGame.master_MIDI_out, newMessage)   		#FIX THIS FIX THIS

"""utility routine to use the Kivy event handler to call a function with the specified arguments"""
def schedule_event(deltaTime, functionToCall, regularArgs = [], kwArgs = {}):
	theFunc = lambda dt: functools.partial(functionToCall, *regularArgs, **kwArgs)()	# functools.partial wraps functions and arguments into a function
	e = Clock.schedule_once(theFunc, deltaTime)											# the lambda wrapper removes the delta time
	return e																			# need this for canceling scheduled events

"""get the pair of notes corresponding to x and y position"""
def get_MIDI_from_graphics(a):
	return [max(mainGame.lowNote, int(linear_map(a[0], mainGame.xyBoundaries[0], [mainGame.lowNote, mainGame.highNote]) + .5)), min(mainGame.highNote, int(linear_map(a[1], mainGame.xyBoundaries[1], [mainGame.lowNote, mainGame.highNote]) + .5))]

def get_coord_from_scaledegree(n):
	tempResult = int(linear_map(n, [mainGame.lowNote, mainGame.highNote], mainGame.xyBoundaries[0]) + .5)
	if tempResult < mainGame.xyBoundaries[0][0]:
		return mainGame.xyBoundaries[0][0]
	if tempResult > mainGame.xyBoundaries[0][1]:
		return mainGame.xyBoundaries[0][1]
	return tempResult

def random_coordinate(x, r = 3, i = 1):			# for midi keyboard input
	y = x + random.randrange(-r, r + 1)
	y = min(76, max(50, y))
	return get_coord_from_scaledegree(y)
	
def capture_graphics(obj, **kwargs):
	mainGame.graphicsCapture.append([time.time(), id(obj), kwargs])

"""weighted choice utility"""	
def weighted_choice(weights, values):
	rnd = random.random() * sum(weights)
	for i, w in enumerate(weights):
		rnd -= w
		if rnd < 0:
			return values[i]
	return values[i]

"""circle widgets"""
class EllipseWidget(Widget):	
	
	nonCopyableKeys = [	'scheduledEvents', 'ellipse', 'makeLine', 'partnerwidgets', 'copiedWidget', 'isACopy', 
						'colorObject', 'makeLineColor', 'needNoteOffs', 'scheduledEvents', 'rhythmSourceWidget', 'initialDisplacementVector', 'movingCallback']	
						# took out clockIsStarted (just recently), kRhythmInProgress!
	weakRefKeys = ['size', 'pos']
	
	def __init__(self, **kwargs):
		"""creates an EllipseWidget that will be automatically activated; copied EllipseWidgets need to have their clock started manually"""
		global mainGame
		super(EllipseWidget, self).__init__(**kwargs)						# calls the widgets __init__ method, maybe not needed
		
		"""here I initialize all the attributes of the EllipseDict; having this list makes it easy to copy the Ellipse"""
		self.attributeDict = {	"loudestVelocity": random.randrange(mainGame.highVelocity - 16, mainGame.highVelocity), 
								"quietestVelocity": random.randrange(mainGame.lowVelocity, mainGame.lowVelocity + 10), 
								"originalVelocityRange": [],
								"velocity": 0,
								"velocityDelta": random.choice([-1, 1]) * random.randrange(3, 8),
								"baseSize": random.randrange(2, 5),
								"size": [0, 0],
								"color": (1, 1, 1),
								"pos": [0, 0],
								"opacity": 0.,
								"initialOpacity": random.randrange(40, 80)/100.,
								"storedOpacity": None,
								"patternLocation": -1, 
								"frequency": 0,
								"lastFiringTime": time.time(),
								"turnOffRandomly": 0,
								"refireDelay": 0,
								"playBothNotesAtOnce": False,
								"moveVector": False,
								"movingCallback": False,
								"randomMode": False,
								"colorObject": False,
								"playOnce": False,
								"startPos": False,
								"lastPosition": [0, 0],
								"makeLineColor": False,
								"makeLine": False,
								"ellipse": False,
								"drawLine": False,
								"channel": None,
								"copiedWidget": [],
								"isACopy": False,
								"playNote": True,	
								"partnerwidgets": [],
								"rhythmIntervals": [],							# rhythmic pattern of the widget
								"counter": -1,
								"index": 0,
								"indexList": [0, 1],
								"notes": [],
								"originalLines": [],
								"scheduledEvents": [],	
								"nextFiringTime": 0, 
								"needNoteOffs": [],
								"kRhythmInProgress": False,
								"clockIsStarted": False,	
								"lastPatternStart": 0,	
								"flockRestart": False,
								"targetFrequency": False, 
								"flockSteps": 1,
								"stepsTaken": 0,
								"originalFrequency": 0,	
								"flockingInterval": 0, 
								"originalPosition": [],
								"rhythmSourceWidget": False,
								"originalRefireDelay": 0, 
								"originalChannel": 0,
								"initialDisplacementVector": False,
								"movingWhenDeleted": False														
		 				   		}										
																	
		for key, value in self.attributeDict.items():
			if key in kwargs:
				setattr(self, key, kwargs[key])
			else:
				setattr(self, key, value)
		
		if not self.originalVelocityRange:
			self.originalVelocityRange = [self.quietestVelocity, self.loudestVelocity]
		
		if not self.velocity:
			if (self.quietestVelocity >= self.loudestVelocity):
				self.quietestVelocity = mainGame.lowVelocity
				self.loudestVelocity = mainGame.highVelocity 
			self.velocity = random.randrange(self.quietestVelocity, self.loudestVelocity)
			
		if "size" not in kwargs:
			self.size = [window_based_size(linear_map(self.velocity, [24, 74],  [x + self.baseSize for x in _SIZERANGE]))] * 2
			
		if not self.frequency:
			self.frequency = random.randrange(20, 200) / 100.
		
		if not self.originalFrequency:
			self.originalFrequency = self.frequency
			
		"""if 'frequency' not in kwargs and not (self.rhythmIntervals):
			mainGame.lastFrequency = self.frequency"""
			
		if kwargs.get('startPos', 0):															# pos is the keyword to initialize a specific position
			self.pos = [x - self.size[0]/2 for x in kwargs['startPos']]   #[kwargs['pos'][0] - self.size[0]/2, kwargs['pos'][1] - self.size[0]/2]
			kwargs['startPos'] = False
			self.startPos = False
		
		if self.pos == [0, 0]:
			if self.notes:
				for i, n in enumerate(self.notes):
					if n:
						self.pos[i] = get_coord_from_scaledegree(n) - self.size[i]/2.
					else:
						self.pos[i] = random_point()[i]
		
		self.set_channel_and_color()
		
		if not self.originalChannel:
			self.originalChannel = self.channel
		
		self.storedOpacity = self.initialOpacity	# shouldn't have to do this
		
		self.rhythmSourceWidget = self
		
		if self.initialDisplacementVector:
			self.pos = [self.pos[i] + self.initialDisplacementVector[i] for i in [0, 1]]
		
		with self.canvas:
			self.colorObject = Color(*self.color, mode='rgb')
			self.ellipse = Ellipse(pos=self.pos, size = self.size)					
		
		self.originalLines = [[self.center_x, 0, self.center_x, mainGame.xyBoundaries[1][1]], [0, self.center_y, mainGame.xyBoundaries[0][1], self.center_y]]
		
		if mainGame.globalIndexList:
			self.indexList = mainGame.globalIndexList[:]
		if mainGame.drawLines:
			self.make_line()
		if mainGame.buildingPreset:
			mainGame.presetWidgets.append([self, time.time()])
		
		self.update_position()		
		
		self.originalPosition = [self.center_x, self.center_y]										
			
		if (not self.isACopy) and (not self.kRhythmInProgress):	
			self.start_clock()
	
	def register(self, dt=0, remove = False):
		if not remove:
			if self not in mainGame.liveCircles:
				mainGame.liveCircles.append(self)											# list of currently active circles							
				mainGame.add_widget(self)													# include the widget in the main screen widget
		else:
			mainGame.remove_widget(self)
			if self in mainGame.liveCircles:
				mainGame.liveCircles.remove(self)	

	def start_clock(self, dt = 0, startOffset = 0, modStartOffsets = True):					# dt is always delta time, passed to the routine by Kivy
		"""starts the clock with a specified delay (startOffset)"""
		self.clockIsStarted = True
		self.kRhythmInProgress = False
		if self.playOnce:
			if not startOffset:
				self.single_play()	
			else:
				self.scheduledEvents.append(Clock.schedule_once(self.single_play, startOffset))
		elif not self.rhythmIntervals:
			if modStartOffsets:
				startOffset = startOffset % self.frequency
			self.scheduledEvents.append(schedule_event(startOffset, Clock.schedule_interval, [self.update, self.frequency]))
			self.scheduledEvents.append(schedule_event(startOffset, self.update))
			self.scheduledEvents.append(schedule_event(startOffset, self.register))
		else:
			for t in self.rhythmIntervals:
				newT = (t + startOffset) % self.frequency
				self.scheduledEvents.append(schedule_event(newT, Clock.schedule_interval, [self.update, self.frequency]))
				self.scheduledEvents.append(schedule_event(newT, self.update))
				self.scheduledEvents.append(schedule_event(newT, self.register))
		if self.movingWhenDeleted:
			self.start_moving()		
	
	def single_play(self, dt = 0):
		"""single-play circles are used for preset and algorithmic processes;
		the trick is that they can be converted into repeating objects if the player holds shift during replay"""
		self.register()
		self.update()
		t = self.lastFiringTime
		if mainGame.kRhythmInProgress:
			"""here we convert to repeating objects if necessary"""
			self.playOnce = False
			self.kRhythmInProgress = True
			self.clockIsStarted = False
			self.refireDelay = 0
			mainGame.kRhythmWidgets.append(self)
			if len(mainGame.kRhythmWidgets) == 1:
				mainGame.kRhythm.append(t)
			self.rhythmIntervals = [t]
			self.scheduledEvents.append(Clock.schedule_once(self.finish_single_play, self.frequency))
		else:
			self.scheduledEvents.append(Clock.schedule_once(self.kill, self.frequency))
	
	def finish_single_play(self, dt = 0):
		"""if the clock has started there is no need for a note off, as it was added when shift was released"""
		if self.clockIsStarted: 
			return
		self.kRhythm_touch()
	
	def start_flocking(self, target, targetSteps = 1):
		if self.frequency == target:
			return
		self.stepsTaken = 0
		self.targetFrequency = float(target)
		self.flockSteps = targetSteps
		self.flockRestart = True
		self.flockingInterval = ((self.targetFrequency - self.frequency)/self.flockSteps)
	
	def original_frequency(self):
		self.unschedule()
		newF = self.originalFrequency
		freqRatio = newF/self.frequency
		self.frequency = newF
		if self.rhythmIntervals:
			self.rhythmIntervals = [freqRatio * x for x in self.rhythmIntervals]
		self.start_clock(startOffset = self.originalRefireDelay)
		
	def flocking_control(self):
		self.unschedule()
		self.stepsTaken += 1
		if self.stepsTaken == self.flockSteps:
			self.flockRestart = False
			self.frequency = self.targetFrequency
			freqRatio = 1.
		else:
			newF = self.frequency + self.flockingInterval
			freqRatio = newF/self.frequency
			self.frequency = newF
		if self.rhythmIntervals:
			self.rhythmIntervals = [freqRatio * x for x in self.rhythmIntervals]
			self.calculate_refire_delay()
			self.start_clock(startOffset = self.refireDelay)
		else:
			self.calculate_refire_delay()
			self.start_clock(startOffset = self.refireDelay, modStartOffsets = False)
	
	def update(self, deltatime = 0, playNote = True):
		"""blink on and off"""
		curTime = time.time()
		self.counter += 1
		if self.rhythmIntervals:
			self.patternLocation = (self.patternLocation + 1) % len(self.rhythmIntervals)
		else:
			self.patternLocation = 0
		timeDelta = curTime - self.lastFiringTime
		self.lastFiringTime = curTime
		self.index = (self.counter / 2) % 2
		if self.turnOffRandomly and random.randrange(0, 100) < self.turnOffRandomly:
			self.kill()
			return
		if self.counter % 2 == 0:
			if self.patternLocation == 0: self.lastPatternStart = curTime			# time of first played note in the big pattern
			self.opacity = self.initialOpacity
			if self.randomMode:
				random.shuffle(self.indexList)
			if playNote:
				self.play()
			if self.drawLine:
				self.make_line()
		else:
			self.opacity = _OFFOPACITY
			capture_graphics(self, opacity = _OFFOPACITY)
			if self.kRhythmInProgress:
				for n in self.needNoteOffs:
					mainGame.master_MIDI_out([143 + self.channel, n, 0])
				self.needNoteOffs = []
		if self.flockRestart:
			self.flocking_control()
	
	def play(self):	
		"""plays the notes and handles the velocity shifting, updates the circle to match the new velocity"""
		if self.playNote:
			self.velocity += self.velocityDelta
			if self.velocity < self.quietestVelocity:
				self.velocityDelta = random.randrange(1, 4)
				self.velocity = self.quietestVelocity
			elif self.velocity > self.loudestVelocity:
				self.velocityDelta = -1 * random.randrange(1, 4)
				self.velocity = self.loudestVelocity
		if self.velocity <= 1:
			self.kill()
			return
		self.index = (self.counter / 2) % 2
		d = window_based_size(linear_map(self.velocity, [24, 74],  [x + self.baseSize for x in _SIZERANGE]))
		oldCenters = [self.center_x, self.center_y]
		self.size = [d, d]
		self.center_x, self.center_y = oldCenters
		self.ellipse.size = self.size
		self.ellipse.pos = self.pos
		capture_graphics(self, size=[d, d], opacity = float(self.opacity), centerx = float(self.center_x), centery = float(self.center_y))
		if self.rhythmIntervals:
			theDuration = self.rhythmIntervals[(self.patternLocation + 1) % len(self.rhythmIntervals)] - self.rhythmIntervals[self.patternLocation]
		else:
			theDuration = self.frequency
		if self.playBothNotesAtOnce:
			nList = self.notes
		else:
			nList = [self.notes[self.indexList[self.index]]]
		for n in nList:
			if self.playNote and n >= mainGame.lowNote and n <= mainGame.highNote:
				if self.kRhythmInProgress:
					newN = mainGame.pitchScale[n]
					self.needNoteOffs.append(newN)
					make_note(newN, max(self.velocity, 0), self.channel, None)	# zero duration means no note off!
				else:
					make_note(mainGame.pitchScale[n], max(self.velocity, 0), self.channel, theDuration)		
	
	def update_position(self, notes = False):
		"""if the circle moves, its notes and lines have to change"""
		if notes:
			self.notes = notes[:]
			self.center_x = get_coord_from_scaledegree(notes[0])
			self.center_y = get_coord_from_scaledegree(notes[1])
		else:	
			self.notes = get_MIDI_from_graphics([self.center_x, self.center_y])
		capture_graphics(self, opacity = float(self.opacity), centerx = float(self.center_x), centery = float(self.center_y))
		self.originalLines = [[self.center_x, 0, self.center_x, mainGame.xyBoundaries[1][1]], [0, self.center_y, mainGame.xyBoundaries[0][1], self.center_y]]
		if self.makeLine:
			self.makeLine.points = self.originalLines[self.indexList[self.index]]

	def on_touch_down(self, touch):
		
		"""mouse handling: click on a circle; 
		in general, the click can affect a synchronized group (if control is pressed), or the selected circles"""
		
		if touch.grab_current is self: 
			return												# this means the event is handled already
		
		if self.collide_point(*touch.pos):
			if 'shift' in mainGame.keysPressed:
				if self.kRhythmInProgress:
					self.kRhythm_touch()
				elif 'lctrl' in mainGame.keysPressed and self.partnerwidgets:						# control affects a whole group
					mainGame.selectedCircles += self.partnerwidgets[:]
				else:
					mainGame.selectedCircles.append(self)
			elif self not in mainGame.selectedCircles:	
				if 'lctrl' in mainGame.keysPressed and self.partnerwidgets:						# control affects a whole group
					mainGame.selectedCircles = self.partnerwidgets[:]				
				else:				
					mainGame.selectedCircles = [self]	
			if 'd' in mainGame.keysPressed:
				for w in mainGame.selectedCircles:
					w.unschedule()
					w.calculate_refire_delay()
				touch.grab(self)
			elif 'f' in mainGame.keysPressed:
				mainGame.lastFrequency = self.frequency
			elif 'lctrl' in mainGame.keysPressed and 'alt' not in mainGame.keysPressed:		# start of a move event; store proper opacity
				touch.grab(self)
				self.storedOpacity = self.opacity		# is self in partnerwidgets?
				for w in self.partnerwidgets:
					w.storedOpacity = w.opacity
			else:
				mainGame.handle_keypress(mainGame.keysPressed, mainGame.selectedCircles)
				touch.grab(self)
				for w in mainGame.selectedCircles:
					w.storedOpacity = w.opacity
			return True
		else:
			return False
	
	def kRhythm_touch(self, dt = 0):
		self.rhythmIntervals.append(time.time())
		self.update()
	
	def on_touch_up(self, touch, directCall = False):
		
		if directCall or ('shift' in mainGame.keysPressed and self.kRhythmInProgress and touch.grab_current is self):
			self.rhythmIntervals.append(time.time())
			self.update()
			touch.ungrab(self)
			return True
			
		elif touch.grab_current is self:
			if 'd' in mainGame.keysPressed:
				for w in mainGame.selectedCircles:
					w.start_clock(startOffset = w.refireDelay - self.refireDelay)
				touch.ungrab(self)
				return True
			elif 'a' in mainGame.keysPressed:	
				self.moveVector = [2*(touch.pos[0] - self.lastPosition[0]), 2*(touch.pos[1] - self.lastPosition[1])]
				self.start_moving()
				for w in mainGame.selectedCircles:
					if w is self: continue
					w.moveVector = [2*(touch.pos[0] - self.lastPosition[0]), 2*(touch.pos[1] - self.lastPosition[1])]
					w.start_moving()		
				touch.ungrab(self)
				return True
				
			elif self.copiedWidget:
				
				for w in self.copiedWidget:
					if w.clockIsStarted: continue
					w.isACopy = False
					w.playNote = True
					w.counter = -1
					#w.rhythmIntervals = [x - w.rhythmIntervals[0] for x in w.rhythmIntervals]	# shouldn't need this any more 
					w.update_position()
					w.start_clock(startOffset = w.refireDelay)
				
				mainGame.selectedCircles = self.copiedWidget[:]
				self.copiedWidget = []
				touch.ungrab(self)
				return True
			else:
				if 'lctrl' in mainGame.keysPressed:
					for w in self.partnerwidgets:
						w.opacity = w.storedOpacity
				for w in mainGame.selectedCircles:
						w.opacity = w.storedOpacity
						w.update_position()
				touch.ungrab(self)
				return True
		else:
			return False
	
	def on_touch_move(self, touch):
		if self.isACopy or 'shift' in mainGame.keysPressed or (touch.grab_current is not self): 
			return False
		self.lastPosition = [self.center_x, self.center_y]
		if 'alt' in mainGame.keysPressed:
			if not self.copiedWidget:
				self.copiedWidget = EllipseWidget.copy_widgets(mainGame.selectedCircles, targetWidget = self)
				if 'super' in mainGame.keysPressed:
					for w in self.copiedWidget:
						w.calculate_refire_delay()
						w.register()
						w.isACopy = False
						w.playNote = True
						w.start_clock(startOffset = w.refireDelay)
				else:
					self.calculate_pattern_start()
					for w in self.copiedWidget:
						w.calculate_pattern_start()
						w.refireDelay = round(w.refireDelay - self.refireDelay, 3)
						w.register()
						w.clockIsStarted = False
			touchDelta = [touch.pos[0] - self.copiedWidget[0].center_x, touch.pos[1] - self.copiedWidget[0].center_y]	
			for w in self.copiedWidget:
				w.opacity = _MOVEOPACITY
				w.center_x += touchDelta[0]
				w.center_y += touchDelta[1]
				w.update_position()
				w.ellipse.pos = w.pos			
			return True
		else:
			touchDelta = [touch.pos[0] - self.center_x, touch.pos[1] - self.center_y]
			for w in mainGame.selectedCircles:
				w.opacity = _MOVEOPACITY
				w.center_x += touchDelta[0]
				w.center_y += touchDelta[1]
				w.update_position()
				w.ellipse.pos = w.pos
			return True
	
	def start_moving(self):
		if not self.moveVector: return
		capture_graphics(self, moveVector = self.moveVector[:])
		self.movingWhenDeleted = True
		if not self.movingCallback:
			self.move_step()
			self.movingCallback = Clock.schedule_interval(self.move_step, .033)
		
	def stop_moving(self):
		if self.movingCallback:
			self.movingWhenDeleted = False
			self.movingCallback.cancel()
			self.movingCallback = False
	
	def move_to_target(self, dt = 0, notes = [0, 0], position = [], steps = 10, delay = .033):
		if position:
			self.tempVector = [(position[0] - self.center_x)/float(steps), (position[1] - self.center_y)/float(steps)]
			self.notes = get_MIDI_from_graphics(position)
		else:
			self.notes = notes[:]
			target = [get_coord_from_scaledegree(notes[0]), get_coord_from_scaledegree(notes[1])]
			self.tempVector = [(target[0] - self.center_x)/float(steps), (target[1] - self.center_y)/float(steps)]
		for i in range(1, steps + 1):
			Clock.schedule_once(self.raw_move, delay * i)

	def raw_move(self, dt = 0):
		for i in [0, 1]:
			self.pos[i] += self.tempVector[i]
		"""code copied from update_position"""
		self.ellipse.pos = self.pos
		capture_graphics(self, opacity = float(self.opacity), centerx = float(self.center_x), centery = float(self.center_y))
		self.originalLines = [[self.center_x, 0, self.center_x, mainGame.xyBoundaries[1][1]], [0, self.center_y, mainGame.xyBoundaries[0][1], self.center_y]]
		if self.makeLine:
			self.makeLine.points = self.originalLines[self.indexList[self.index]]
			
	def move_step(self, dt = 0):
		for i in [0, 1]:
			self.pos[i] += self.moveVector[i]
			if self.pos[i] < 0:
				self.pos[i] = -self.pos[i]
				self.moveVector[i] = -self.moveVector[i]
			elif self.pos[i] + self.size[i] > mainGame.xyBoundaries[i][1]:
				self.moveVector[i] = -self.moveVector[i]
				delta = (self.pos[i] + self.size[i]) - mainGame.xyBoundaries[i][1]
				self.pos[i] = mainGame.xyBoundaries[i][1] - delta - self.size[i]
		self.update_position()
		self.ellipse.pos = self.pos
	
	def set_channel_and_color(self):
		if self.channel is None:
			self.channel = mainGame.defaultChannel
		if self.channel >= 1 and self.channel <= _NUMCHANNELS:
			h = (((1./(_NUMCHANNELS + 1)) * (self.channel - 1)) + .47) % 1. + random.randrange(0, 5) / 100.
			s =  random.randrange(80, 100) / 100.
			l = random.randrange(40, 70) / 100.
			if self.channel == 8: l += .2
			self.color = colorsys.hls_to_rgb(h, l, s)
		else:
			r = random.random()
			self.color = (r, r, 1)
		capture_graphics(self, color = self.color)
		if self.colorObject:
			self.colorObject.rgb = self.color
		if self.makeLineColor:
			self.makeLineColor.rgb = self.color	
		
	def copy(self, returnDict = False):
		newKwargs = {}
		for k in self.attributeDict:
			if k in EllipseWidget.nonCopyableKeys:
				continue
			a = getattr(self, k)
			if type(a) is list:
				a = a[:]
			elif k in EllipseWidget.weakRefKeys:
				a = list(a)
			newKwargs[k] = a
		newKwargs['isACopy'] = True
		newKwargs['playNote'] = False
		if returnDict:
			return newKwargs
		else:
			return EllipseWidget(**newKwargs)
	
	def finish_rhythmic_pattern(self, extraDelay = 0):
		"""should make rhythmIntervals always start with 0 I think, then we won't have to do this when copying circles"""
		if mainGame.playOnce or len(mainGame.kRhythm) <= 1: 
			return
		if mainGame.useLastFrequency and mainGame.lastFrequency:
			self.frequency = mainGame.quantize_to_tempo(mainGame.kRhythm[1] - mainGame.kRhythm[0])
			#self.frequency = max(1, int(0.5 + (mainGame.kRhythm[1] - mainGame.kRhythm[0])/mainGame.lastFrequency)) * mainGame.lastFrequency
		else:
			self.frequency = mainGame.kRhythm[1] - mainGame.kRhythm[0]
		self.originalFrequency = self.frequency
		self.partnerwidgets = mainGame.kRhythmWidgets
		if len(self.rhythmIntervals) % 2 == 1:
			self.rhythmIntervals.append((mainGame.kRhythm[1] + self.rhythmIntervals[-1])/2.)
		startOffset = self.rhythmIntervals[0] -  mainGame.kRhythm[0]									# delay of first attack point
		self.rhythmIntervals = [x - mainGame.kRhythm[0] - startOffset for x in self.rhythmIntervals]	# start pattern at zero
		self.originalRefireDelay = self.refireDelay + extraDelay + startOffset
		self.start_clock(startOffset = self.originalRefireDelay)						# add startOffset
	
	def unmake_line(self):
		self.drawLine = False
		if self.makeLineColor:
			self.makeLineColor.rgba = list(self.makeLineColor.rgba[:-1] + [0])
		capture_graphics(self, lines = False)
			
	def make_line(self):
		"""draws perpendicular lines corresponding to the notes being played"""
		self.drawLine = True
		if self.makeLine:
			self.makeLine.points = self.originalLines[self.indexList[self.index]]
			if self.makeLineColor.rgba[-1] == 0:
				a = self.makeLineColor.rgba[:-1] + [.6]
				self.makeLineColor.rgba = a
		else:
			with self.canvas:
				self.makeLineColor = Color(*tuple(list(self.color) + [.6]), mode='rgba')
				self.makeLine = Line(points=self.originalLines[self.indexList[self.index]], width=2)
		capture_graphics(self, lines = self.originalLines[self.indexList[self.index]])
	
	def calculate_refire_delay(self):
		
		"""The logic of this calculation is not immediately clear, since it depends in a subtle way on how self.start_clock works"""
		
		if not self.rhythmIntervals:
			self.refireDelay = self.frequency - (time.time() - self.lastFiringTime)
		else:
			i = (self.counter) % len(self.rhythmIntervals)
			if i == len(self.rhythmIntervals) - 1:
				nextTarget = self.frequency + self.rhythmIntervals[0]	# self.rhythmIntervals[0] should now be 0, we can eliminate this
			else:
				nextTarget = self.rhythmIntervals[i + 1]
			nextFiringTime = (nextTarget - self.rhythmIntervals[i]) - (time.time() - self.lastFiringTime)
			self.refireDelay = nextFiringTime - nextTarget			
			
			"""
			why subtract nextTarget?  
				because startclock will automatically add that delay, since it starts from the beginning of the pattern.
				To start in the middle we need to subtract off the built-in delay from all those delays.
			"""
	
	def calculate_pattern_start(self):
		if not self.rhythmIntervals:
			self.refireDelay = 2*self.frequency - (time.time() - self.lastPatternStart)
		else:
			self.refireDelay = self.frequency - (time.time() - self.lastPatternStart)
	
	def unschedule(self):
		Clock.unschedule(self.update, all=True)
		self.clockIsStarted = False
		for e in self.scheduledEvents:
			Clock.unschedule(e)
		self.scheduledEvents = []
		if self.movingCallback:
			self.movingCallback.cancel()
		
	def kill(self, dt = 0):
		"""self explanatory"""
		#print(self.scheduledEvents)
		self.unschedule()
		self.register(remove = True)
		capture_graphics(self, kill=True)
		for n in self.needNoteOffs:
			mainGame.master_MIDI_out([143 + self.channel, n, 0])
		self.rhythmIntervals.append(time.time())
		self.needNotesOffs = []
	
	def print_everything(self):
		print('\n\n\n', self)
		for i, k in enumerate(sorted(self.attributeDict)):
			print(i,k,getattr(self, k))
		
	@staticmethod
	def copy_widgets(myList, targetWidget = False):
		"""copy a bunch of widgets and update the partnerwidgets list manually, which we can't copy automatically"""
		copiedWidget = []
		if targetWidget:
			newPW = targetWidget.copy()
			copiedWidget.append([targetWidget, newPW])
		for pw in myList:
			if pw == targetWidget:
				continue
			newPW = pw.copy()
			copiedWidget.append([pw, newPW])
		for pw, newPW in copiedWidget:						
			if newPW.partnerwidgets: continue
			if pw.partnerwidgets:
				newPartners = [x[1] for x in copiedWidget if x[0] in pw.partnerwidgets]
				for np in newPartners:
					np.partnerwidgets = newPartners
		return [x[1] for x in copiedWidget]
	

class BeaconsWindow(Widget):
	"""the main window, handles keyboard input"""
	def __init__(self, **kwargs):
		
		super(BeaconsWindow, self).__init__(**kwargs)
		self.mousePos = None
		self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
		Window.bind(mouse_pos=lambda w, p: setattr(self, 'mousePos', [Window._density*x for x in p]))		# correct for a known Kivy bug
		Window.bind(on_resize=self.on_resize)
		self._keyboard.bind(on_key_down=self._on_keyboard_down)
		self._keyboard.bind(on_key_up=self._on_keyboard_up)
		self.keysPressed = set([])
		self.defaultChannel = 1
		self.randomMode = False
		self.playBothNotesAtOnce = False
		self.waitingForScale = False
		self.buildScale = set([])
		self.lastKeyboardInput = 0
		self.keyboardKRhythmDict = {}
		self.presetDict = {}
		self.buildingPreset = False
		self.presetStartTime = 0
		self.presetWidgets = []
		self.highVelocity = 70
		self.lowVelocity = 14
		self.currentScale = [0, 2, 3, 5, 7]
		self.midiCapture = []
		self.scaleCapture = []
		self.graphicsCapture = []
		self.flockFrequency = 0
		self.lastFade = []
		self.lastCommonTones = 4
		self.lastPresetStored = False
		self.kRhythmInProgress = False
		self.showCursor = True
		self.midiIsChosen = False
		self.selectedPort = None
		self.midiout = False
		self.midiin = False
		self.textWidgets = []
		
		self.movablePresets = False
		self.toMaxOutput = False
		
		self.algorithmicPresets = {	'q': [[[5, 5, 3, 3, 1, 1], [1, -1, 2, -2, 3, -3]], [[5, 3, 2, 1], [1, 2, 3, 8]], {}], 
									'w': [[[10, 1, 1], [0, 1, -1]], [[10, 1], [1, 2]], {'lengthRange': [15, 30]}],
									'e': [[[9, 1], [1, -1]], [[10, 1], [1, 2]], {'lengthRange': [15, 50], 'baseDuration': .1}],
									'r': [[[9, 1], [-1, 1]], [[10, 1], [1, 2]], {'lengthRange': [15, 50], 'baseDuration': .1}],
									't': [[[10, 1, 1], [0, 1, -1]], [[1, 1], [1, 2]], {'lengthRange': [15, 30]}],
									'y': [[[1], [0]], [[1, 3], [1, 2]], {'yVariation': 0, 'velocityRange': [84, 96], 'baseDuration': .25, 'lengthRange': [15, 30]}],
									'u': [[[10, 1, 1], [0, 1, -1]], [[10, 1], [1, 2]], {'lengthRange': [2, 3]}],
									}
		self.mTimer = 0
		self.subdivisions = 1
		
		self.overridePedal = False
		self.randomEchoes = False
		
		self.changePitchesWithKeyboard = False
		self.keyboardControlledCircles = []
		self.keyboardChord = [set([]), []]
		
		self.keyboardPattern = []
		
		self.chromaticMode = False
		self.shiftPressed = False

		self.flockSpeeds = {'1': [1, 2], '2': [5, 10], '3': [10, 20]}
		self.flockSpeed = self.flockSpeeds['1']
			
		self.scaleHistory = []
		
		self.inversePitchScale = {([1, 3, 6, 8, 10][i] + 36 + 12 * j):(range(5)[i]+50+5*j) for i in range(5) for j in range(5)}
		self.lowMidi = min(self.inversePitchScale.keys())
		self.highMidi = max(self.inversePitchScale.keys())
		
		self.capslock = False
		self.autofadeEchoes = True
		
		self.selectionBox = [[], []]
		self.selectedCircles = []
		self.drawLines = False
		
		self.pedalDown = 0
		self.textWidgets = []
		
		self.shuffleFrequencies = []

		self.liveCircles = []
		self.globalIndexList = []
		self.kRhythm = []
		self.kRhythmWidgets = []
		
		self.lastScaleNumber = 0
		self.currentScaleNumber = 0
		
		self.lastBurst = []
		self.lastBurstTime = time.time()
		self.burstInProgress = []
		
		self.xyBoundaries = [[], []]
		
		self.keyboardNoteOffs = {}
		self.parsimoniousScale = []
		
		self.lastFrequency = random.randrange(20, 200) / 100.
		self.useLastFrequency = False
		
		self.selectionLines = False
		self.playOnce = False
		
		with self.canvas:
			self.selectionLineColor = Color(*(1., 1., 1., 0.), mode='rgba', width = 1.)
			self.selectionLines = Rectangle(pos=[0, 0], size=[1, 1])
	
	def initialize_midi(self):
		
		self.midiin2, self.midiout2 = False, False
		
		if self.midiin:
			self.midiin.set_callback(self.MIDIkeyboard_input)
			
		if self.midiin2:
			self.midiin2.set_callback(self.MIDIkeyboard_input)
		
		self.volumeChannelMappings = {82: 1, 83: 2, 28: 3, 29: 4, 16:5, 80:6, 18:7, 19:8, 74:9, 71:10, 81: 11, 2: 12, 10: 13, 5: 14, 21:15}
		
		self.toMaxOutput = rtmidi.MidiOut()
		thePorts = self.toMaxOutput.get_ports()
		
		if 'to Max 1' in thePorts:
			self.toMaxOutput.open_port(thePorts.index('to Max 1'))
			self.toMaxOutput.send_message([147, 12, 0])
		else:
			self.toMaxOutput = False
		
		self.fromMaxInput = rtmidi.MidiIn()
		thePorts = self.fromMaxInput.get_ports()
		
		if 'from Max 1' in thePorts:
			self.fromMaxInput.open_port(thePorts.index('from Max 1'))
			self.fromMaxInput.set_callback(self.maxpatch_input)
		else:
			self.fromMaxInput = False
		self.midiIsChosen = True
		self.master_MIDI_out([176, 64, 127])
		if self.midiout2:
			self.midiout2.send_message([176, 64, 127])
		#Clock.schedule_interval(mainGame.debug_update, 3)			# should I distribute with this???
	
	
	def screen_print(self, theText = 'Testing!', lineOffset = 0, refnumber = 0, xPos = .45, yPos = .9, color = 'ffffff', **kwargs):
		l = Label(text=('[color=' + color + '][ref=' + str(refnumber)+ ']' + theText + '[/ref][/color]'), font_size=str(24) + 'sp', markup=True)
		self.add_widget(l)
		self.textWidgets.append(l)
		l.pos = [self.width * xPos, self.height * yPos]
		l.bind(on_ref_press=self.print_it)
	
	def print_it(self, instance, value):
		i = int(value)
		if (i >= 0) or self.targetPort == 1:
			self.selectedPort = i
			
	"""send MIDI out and record messages"""
	def master_MIDI_out(self, midiMessage):
		self.midiout.send_message(midiMessage)
		#self.midiCapture.append([time.time(), midiMessage])	
		if self.midiout2 and midiMessage[0] == 144:
			self.midiout2.send_message(midiMessage)
	
	def maxpatch_input(self, *args):
		msg = args[0][0]
		if type(msg) is list and len(msg) > 2:
			if msg[0] == 144 and msg[2] == 1:
				if len(self.scaleHistory) >= msg[1]:
					self.initialize_scale(recallPreset = msg[1])
			elif msg[0] == 145 and msg[2] == 2:
				if msg[1] == 10:
					self.initialize_scale(recallPreset = self.lastScaleNumber)  
				elif msg[1] == 9:
					self.initialize_scale()
				elif msg[1] == 8:
					self.initialize_scale(randomTransposition = 0)
				elif 0 <= msg[1] <= 4:
					self.initialize_scale(commonTones = msg[1])
			elif msg[0] == 146 and msg[2] == 2:
				scaleNumber = len(self.scaleHistory) - 1 - msg[1]
				self.initialize_scale(recallPreset = scaleNumber)
				
	def make_echoes(self):
		t = time.time()
		self.keyboardPattern, startT = self.clean_keyboard_pattern(self.keyboardPattern)
		l = len(self.keyboardPattern)
		m = int(.5 + l/2.)
		for w in self.kRhythmWidgets:
			w.kill()
		if self.useLastFrequency:
			freq = self.lastFrequency
		else:
			freq = t - startT
		minV = max(min(min([x[2] for x in self.keyboardPattern]), 54), 24)
		self.selectedCircles = []
		print(self.keyboardPattern)
		#random.shuffle(self.keyboardPattern)
		for i in range(m):
			n1 = self.keyboardPattern[2*i]
			n2 = self.keyboardPattern[(2*i + 1) % l]
			#v = min(n1[2], n2[2]) 
			start1 = n1[0]
			start2 = (n2[0] - start1) % freq
			end1 = (n1[3]) % freq
			if end1 > start2: end1 = start2 - .01
			end2 = (start2 + n2[3]) % freq
			if end2 < 0 or n2[3] == 0 or end2 < start2: 
				end2 = freq - .01
			ri = [0, end1, start2, end2]
			#print('  notes', n1[1], n2[1], 'rhythms', ri, 'freq', freq, 'refire', start1)
			nw = EllipseWidget(notes = [n1[1], n2[1]], velocity = minV, rhythmIntervals = ri, frequency = freq, randomMode = self.randomMode, playBothNotesAtOnce = self.playBothNotesAtOnce, isACopy = True, refireDelay = start1)
			nw.isACopy = False
			if self.autofadeEchoes:
				nw.quietestVelocity = -10
				nw.velocityDelta = -1 * random.randrange(3, 6)
			nw.start_clock(startOffset = nw.refireDelay)
			self.selectedCircles.append(nw)
		
	def clean_keyboard_pattern(self, keyboardPattern):
		usedNoteOffs = []
		finalList = []
		startT = keyboardPattern[0][0]
		l = len(keyboardPattern)
		for i, note1 in enumerate(keyboardPattern):
			if note1[2] != 0:
				finalDur = 0
				for j, note2 in enumerate(keyboardPattern[i+1:]):
					if note2[1] == note1[1] and note2[2] == 0 and i+j+1 not in usedNoteOffs:
						usedNoteOffs.append(i+j+1)
						finalDur = note2[0] - note1[0]
						break
				note1.append(finalDur)
				note1[0] = note1[0] - startT
				finalList.append(note1)
		return finalList, startT
		
	def MIDIkeyboard_input(self, *args):
		msg = args[0][0]
		#print(msg)
		"""Radium controllers 82, 83, 28, 29, 16, 80, 18, 19, 74, 71, 81"""
		
		if type(msg) is list and len(msg) >= 2:
			
			if msg[0] == 176:
				if msg[1] == 64:
					if msg[2] == 127:
						self.pedalDown = time.time()
						self.kRhythmInProgress = True
					else:
						if (self.overridePedal or (not self.keyboardPattern)):
							if (time.time() - self.pedalDown < .5):
								self.initialize_scale(commonTones = self.lastCommonTones)
						elif 'shift' not in self.keysPressed:
							if self.randomEchoes:
								self.make_echoes()
							else:
								self.complete_rhythmic_patterns() # finish krhythm
						self.pedalDown = 0
						self.keyboardPattern = []
						self.keyboardKRhythmDict = {}
						"""would like to make pedal and shift equivalent, this may take some tracing"""
						if ('shift' not in self.keysPressed) and not self.randomEchoes:
							self.kRhythmInProgress = False	# not sure if this should be here; should 'shift' and the pedal be on a par?
							self.complete_rhythmic_patterns()
					return	
				c = self.volumeChannelMappings.get(msg[1], 0)
				if c:
					newMessage = [175 + c, 7] + msg[2:]
					self.master_MIDI_out(newMessage)
				elif msg[1] == 64:
					self.waitingForScale = True
			else:
				if msg[0] >> 4 == 8:
					msg[0] += 16
					if len(msg) == 2:
						msg.append(0)
					else:
						msg[2] = 0
						
				"""keyboard note on"""
				if msg[0] >> 4 == 9:
					thePitch = msg[1]
					
					"""this is the code for modulating via keyboard"""
					if self.waitingForScale:
						self.buildScale.add(msg[1] % 12)
						if len(self.buildScale) >= 5:
							newScale = sorted(list(self.buildScale)[:5])
							self.initialize_scale(newScale)
							self.waitingForScale = False
							self.buildScale = set([])
					
					else:
						t = time.time()					
						c = self.get_scaledegree_from_midi(msg[1])
						if not c: 
							return
						x = get_coord_from_scaledegree(c)
						
						"""this is the code for controlling chords via the keyboard"""
						if self.changePitchesWithKeyboard:
							if msg[2] == 0:
								if msg[1] in self.keyboardChord[0]:
									self.keyboardChord[0].remove(msg[1])
								if self.keyboardChord[1] and not self.keyboardChord[0]:
									mList = self.keyboardChord[1][:]
									for i in range(3):
										l = self.keyboardChord[1][:]
										random.shuffle(l)
										mList = mList + l
									chordLen = len(mList)
									for i, w in enumerate(self.keyboardControlledCircles):
										w.stop_moving()
										w.moveVector = False
										w.move_to_target(notes = [self.get_scaledegree_from_midi(mList[i % chordLen]), self.get_scaledegree_from_midi(mList[(i+1) % chordLen])])
							else:
								if not self.keyboardChord[0]:
									self.keyboardChord[1] = []
								self.keyboardChord[0].add(msg[1])
								self.keyboardChord[1].append(msg[1])
								
							"""simple playing notes"""	
						elif (('shift' not in self.keysPressed) and not self.pedalDown) or (msg[2] == 0 and not self.keyboardPattern):
							if msg[2] == 0: 
								for w in self.keyboardNoteOffs.setdefault(c, []):
									w.kill()
								del(self.keyboardNoteOffs[c])
								return
							if (t - self.lastKeyboardInput > 2):
								self.make_random_Y_coordinates()
							nw = EllipseWidget(startPos = [x, self.randomYCoords[c]], velocity = msg[2], rhythmIntervals = [t], randomMode = self.randomMode, playBothNotesAtOnce = self.playBothNotesAtOnce, kRhythmInProgress = True, indexList = [0, 0])
							nw.register()
							nw.update()
							self.keyboardNoteOffs.setdefault(c, []).append(nw)		# this used to be x
							
							"""keyboard controlled loops"""
						else:
							self.keyboardPattern.append([t, c, msg[2]])
							thePos = [x, self.randomYCoords[c]]
							tuplePos = tuple(thePos)
							if tuplePos not in self.keyboardKRhythmDict:
								nw = EllipseWidget(startPos = thePos, rhythmIntervals = [t], velocity = msg[2], frequency = self.lastFrequency, randomMode = self.randomMode, playBothNotesAtOnce = self.playBothNotesAtOnce, kRhythmInProgress = True)
								nw.register()
								nw.update()
								self.keyboardKRhythmDict[tuplePos] = nw
								self.kRhythmWidgets.append(nw)
								if len(self.kRhythmWidgets) == 1:
									self.kRhythm = [t]
							else:
								nw = self.keyboardKRhythmDict[tuplePos]
								nw.rhythmIntervals.append(time.time())
								nw.update()		
						self.lastKeyboardInput = t
	
	def make_random_Y_coordinates(self):
		self.randomYCoords = {y:random_coordinate(y, 3) for y in range(50, 76)}
				
	def get_scaledegree_from_midi(self, n):
		
		while n >= self.lowMidi:
			if n in self.inversePitchScale:
				return self.inversePitchScale[n]
			else:
				n -= 1
	
	def change_one_note(self, direction = [-1, 1]):
		possibleChanges = []
		if not self.parsimoniousScale:
			self.parsimoniousScale = self.currentScale
		temp = [x % 12 for x in self.parsimoniousScale]
		for i in temp:
			for j in direction:
				if (i + j) % 12 not in temp:
					possibleChanges.append([i, j])
		alteration = random.choice(possibleChanges)
		i = temp.index(alteration[0])
		self.parsimoniousScale[i] += alteration[1]
		self.display_scale(sorted([x % 12 for x in self.parsimoniousScale]))
	
	def initialize_scale(self, theScale = False, commonTones = None, recallPreset = None, lastScale = False, randomTransposition = None):				# choose a random 5-note scale
		if commonTones is not None and commonTones < 0: 	# more fine grained modulations
			if commonTones == -1:
				self.change_one_note()
			elif commonTones == -2:
				self.change_one_note([-1])
			else:
				self.change_one_note([1])
			return
		self.parsimoniousScale = []
		if lastScale:
			recallPreset = self.lastScale
		if recallPreset is not None:
			if len(self.scaleHistory) >= recallPreset + 1:
				theScale = self.scaleHistory[recallPreset]
				self.display_scale(theScale, preset = recallPreset)
			return
		if randomTransposition is not None:
			if randomTransposition == 0:
				randomTransposition = random.randrange(0, 12)
				theScale = sorted([(x + randomTransposition) % 12 for x in self.currentScale])
		if not theScale:
			if self.scaleHistory and (commonTones is not None):
				oldScale = self.currentScale[:]
				random.shuffle(oldScale)
			else:
				commonTones = 0
				oldScale = []
			l = set(range(12))
			l = list(l - set(oldScale))
			random.shuffle(l)
			l = list(oldScale[:commonTones]) + l
			theScale = sorted(l[:5])
		self.display_scale(theScale)
	
	def display_scale(self, theScale = [], preset = None):
		
		"""
		Max/MSP interaction: channels give different messages
			- incoming notes on channel 1 to set secale
			- store preset numbers on 2
			- recall preset on channel 3
			- additional messages on channel 4 (12 = scale complete, )
			- set scale menu on channel 5 (used to display the last scale)
			- preset numbers go out on channel 6
		"""
		
		self.currentScale = theScale[:]
		self.scaleCapture.append([time.time(), self.currentScale])
		self.pitchScale = {i:(theScale[i % 5]) + ((i/5) - 10) * 12 + 36 for i in range(50, 76)}
		self.lowNote = min(self.pitchScale.keys())
		self.highNote = max(self.pitchScale.keys())
		self.lastScaleNumber = self.currentScaleNumber
		if self.toMaxOutput:
			self.toMaxOutput.send_message([148, self.lastScaleNumber, 60])									# recall presets on channel 3
		if preset is not None:
			if self.toMaxOutput:
				self.toMaxOutput.send_message([146, preset, 60])									# recall presets on channel 3
			self.currentScaleNumber = preset
			print("Recalled Scale", preset + 1, theScale)
			return
		else:
			print("Current Scale", len(self.scaleHistory) + 1, theScale)
			self.currentScaleNumber = len(self.scaleHistory)
			if self.toMaxOutput:
				for i in theScale:
					self.toMaxOutput.send_message([144, 60 + i, 60])							# notes on channel 1
				self.toMaxOutput.send_message([145, self.currentScaleNumber  % 128, 60])		# preset numbers on channel 2
			self.scaleHistory.append(theScale)
	
	def _keyboard_closed(self):
		self._keyboard.unbind(on_key_down=self._on_keyboard_down)
		self._keyboard = None

	def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
		
		if keycode[1] in self.keysPressed:
			return
		
		if keycode[1] == 'capslock':
			self.capslock = not(self.capslock)
			
		self.keysPressed.add(keycode[1])
		tempCircles = []
		#debug(self.keysPressed, keycode, text, modifiers)
		self.shiftPressed = 'shift' in self.keysPressed
		self.altPressed = 'alt' in self.keysPressed
		
		if 'p' in self.keysPressed:					# pressing 'p' for preset overrides everything else
			#print(self.presetWidgets)
			if 'super' in self.keysPressed and 'alt' in self.keysPressed:
				self.save_presets()
				
			elif self.shiftPressed:
				
				if keycode[1] not in ['shift', 'p']:
					if keycode[1] in self.presetDict:
						self.play_preset(keycode[1])
					else:
						"""if shift is pressed, you either store a new preset or recall a preset for looping"""
						if self.selectedCircles:
							self.store_preset(keycode[1])
						elif self.lastPresetStored:
							print("Stored last deleted circles as preset", keycode[1])
							self.presetDict[keycode[1]] = copy.deepcopy(self.presetDict[self.lastPresetStored])
							if self.toMaxOutput:
								i = ord(keycode[1].lower())
								if 0 <= i <= 127:
									self.toMaxOutput.send_message([149, i, 60])
								self.toMaxOutput.send_message([147, 42, 60])
				
				elif keycode[1] == 'p' and 'alt' in self.keysPressed:
					self.movablePresets = False
					
			elif keycode[1] not in ['shift', 'p']:
				self.play_preset(keycode[1])
			
			elif 'alt' in self.keysPressed:
				self.movablePresets = True			# shift-alt captured a few lines above
		
		elif 's' in self.keysPressed:
			if keycode[1] in '1234567890qwertyuiop':	# recall previous scales					
				myScale = '1234567890qwertyuiop'.index(keycode[1])
				if self.shiftPressed:
					myScale += 20
				self.initialize_scale(recallPreset = myScale)
			
		elif self.capslock and keycode[1] in self.algorithmicPresets:
			intHisto, durHisto, kwargs = self.algorithmicPresets[keycode[1]]	# intHisto and durHisto are [[weights], [values]]
			self.algorithmic_pattern(intHisto, durHisto, presetCode = keycode[1], **kwargs)
			return
		
		elif keycode[1] == 'a' and 'super' in self.keysPressed:
			self.selectedCircles = self.liveCircles[:]
		
		elif keycode[1] == 'spacebar':
			self.selectedCircles = []
			self.changePitchesWithKeyboard = False
			
		elif keycode[1] == 'i' and 'super' in self.keysPressed:
			self.selectedCircles = [w for w in self.liveCircles if w not in self.selectedCircles ]
		# scale stuff
		
		elif keycode[1] == 'm':
			self.mTimer = time.time()
			self.waitingForScale = True
		
		elif keycode[1] == ':':
			self.showCursor = not self.showCursor
			Window.show_cursor = self.showCursor
			#Config.set('graphics','show_cursor',str(int(self.showCursor)))
		
		elif keycode[1] == 'n':
			self.initialize_scale(recallPreset = self.lastScaleNumber) 
		
		elif keycode[1] in '`123456789' and 'm' in self.keysPressed:  # change scale will specifying common tones
			i = '`123456789'.index(keycode[1])
			if i == 9:
				self.initialize_scale(randomTransposition = 0)
			else:
				self.lastCommonTones = [None, 4, 3, 2, 1, 0, -1, -2, -3][i]
				self.initialize_scale(commonTones = self.lastCommonTones)
				
		elif keycode[1] in '`123456789' and 'f' in self.keysPressed: 
			self.subdivisions = float(max(1, '`123456789'.index(keycode[1])))
			#print(self.subdivisions)
		
		# turn off moving circles		
		
		elif keycode[1] == '=':
			
			if self.shiftPressed:
				for w in self.selectedCircles:
					if w.moveVector:
						w.stop_moving()
						w.moveVector =  []
			else:
				self.selectedCircles = []
				for w in self.liveCircles:
					if w.moveVector:
						self.selectedCircles.append(w)
				if 'super' not in self.keysPressed:
					if all([w.movingCallback == False for w in self.selectedCircles]):
						for w in self.selectedCircles:
							w.start_moving()
					else:
						for w in self.selectedCircles:
							w.stop_moving()
		
		elif keycode[1] == 'shift' and len(self.keysPressed) == 1:
			self.kRhythmWidgets = []
			self.kRhythmInProgress = True
			#self.selectedCircles = []
		
		elif keycode[1] == 'e':
			if self.shiftPressed:
				self.randomEchoes = False
			else:
				self.randomEchoes = True
		
		elif keycode[1] == 't':
			if self.shiftPressed:
				self.playOnce = False
			else:
				self.playOnce = not(self.playOnce)
		
		elif keycode[1] == 'b':
			if 'alt' not in self.keysPressed:
				t = time.time()
				if ('shift' in self.keysPressed) and self.kRhythmWidgets:
					for w in self.kRhythmWidgets:
						w.rhythmIntervals.append(t)
						w.update()
					return
				self.lastBurst = []
				self.burstInProgress = []
				self.lastBurstXY = self.mousePos[:]
				for i in range(random.randrange(3, 6)):
					xRange = [max(self.mousePos[0] - _BURSTRADIUS, self.xyBoundaries[0][0]), min(self.mousePos[0] + _BURSTRADIUS, self.xyBoundaries[0][1])]
					yRange = [max(self.mousePos[1] - _BURSTRADIUS, self.xyBoundaries[1][0]), min(self.mousePos[1] + _BURSTRADIUS, self.xyBoundaries[1][1])]
					thePos = [random.randrange(*xRange), random.randrange(*yRange)]
					if 'shift' in self.keysPressed:
						if not self.kRhythm:
							self.kRhythm = [t]
						nw = EllipseWidget(startPos = thePos, rhythmIntervals = [t], frequency = self.lastFrequency, randomMode = self.randomMode, playBothNotesAtOnce = self.playBothNotesAtOnce, kRhythmInProgress = True)
						self.kRhythmWidgets.append(nw)
						nw.register()
						nw.update()
					else:
						nw = EllipseWidget(startPos = thePos, rhythmIntervals = [t], frequency = self.lastFrequency, randomMode = self.randomMode, playBothNotesAtOnce = self.playBothNotesAtOnce, kRhythmInProgress = True)
						nw.register()
						nw.update()
						self.burstInProgress.append(nw)
					self.lastBurst.append(thePos)
					self.lastBurstTime = time.time()
				self.selectedCircles = self.burstInProgress[:]
			else:
				self.burstInProgress = []
				t = time.time()
				for thePos in self.lastBurst:
					nw = EllipseWidget(startPos = thePos, rhythmIntervals = [t], frequency = self.lastFrequency, randomMode = self.randomMode, playBothNotesAtOnce = self.playBothNotesAtOnce, kRhythmInProgress = True)
					nw.register()
					nw.update()
					self.burstInProgress.append(nw)
					
		elif keycode[1] == '\\':
			if self.shiftPressed:
				self.master_MIDI_out([175 + self.defaultChannel, 123, 0])			# all notes off
			elif 'super' in self.keysPressed:
				for i in range(1, _NUMCHANNELS + 1):
					self.master_MIDI_out([175 + i, 123, 0])			# all notes off
				for w in self.liveCircles[:]:
					w.kill()
			else:
				for w in self.liveCircles:
					w.print_everything()
		
		elif keycode[1] == 'h':
			
			if self.shiftPressed:
				self.changePitchesWithKeyboard = False
				if 'alt' in self.keysPressed:
					for w in self.keyboardControlledCircles:
						w.pos = [w.originalPosition[0] - w.size/2., w.originalPosition[1] - w.size/2.]
						w.update_position()
			else:
				self.keyboardControlledCircles = self.selectedCircles[:]
				self.changePitchesWithKeyboard = True
				self.keyboardChord = [set([]), []]
				
		elif keycode[1] == 'j':
			if self.shiftPressed:
				for nd in self.shuffleFrequencies:
					w = nd[-1]
					w.unschedule()
					w.frequency = nd[0]
					w.rhythmIntervals = nd[1][:]
					w.refireDelay = nd[2]
					w.counter = nd[3]
					w.patternLocation = nd[4]
					w.rhythmSourceWidget = w
					w.moveVector = False
					w.start_clock(startOffset = w.refireDelay)			
			else:
				self.shuffleFrequencies = []
				for w in self.selectedCircles:
					ints = w.rhythmIntervals[:]
					w.calculate_refire_delay()
					w.originalRhythmIntervals = ints
					self.shuffleFrequencies.append([w.frequency, ints, w.refireDelay, w.counter, w.patternLocation, w.rhythmSourceWidget])
				random.shuffle(self.shuffleFrequencies)
				for i, w in enumerate(self.selectedCircles):
					w.unschedule()
					nd = self.shuffleFrequencies[i]
					w.frequency = nd[0]
					w.rhythmIntervals = nd[1][:]
					w.refireDelay = nd[2]
					w.counter = nd[3]
					w.patternLocation = nd[4]
					w.rhythmSourceWidget = nd[-1]
					w.start_clock(startOffset = w.refireDelay)
		
		elif keycode[1] == 'enter' and 'super' in self.keysPressed and 'alt' in self.keysPressed:
			print('reset')
			if self.toMaxOutput:
				self.toMaxOutput.send_message([147, 12, 0])				# reset timer
			self.capslock = False									# reset capslock state
			return
			
		else:
			self.handle_keypress([keycode[1]], self.selectedCircles)
					
			
	"""unified method to handle keypresses, since commands can be triggered either by clicking on circles or selecting them and pressing the keyboard"""
	def handle_keypress(self, theKeys, widgetList):
		for theKey in theKeys:
			if theKey == ',':
				if 'super' in self.keysPressed:
					self.highVelocity = 70
					self.lowVelocity = 14
					for w in widgetList:
						w.quietestVelocity = random.randrange(self.lowVelocity, self.lowVelocity + 10)
						w.loudestVelocity = random.randrange(self.highVelocity - 16, self.highVelocity)
				elif not widgetList:
					self.lowVelocity = max(4, self.lowVelocity - 4)
					self.highVelocity = max(self.lowVelocity + 14, self.highVelocity - 4)
				else:
					for w in widgetList:
						w.quietestVelocity = max(5, w.quietestVelocity - 5)
						w.loudestVelocity = max(w.quietestVelocity + 5, w.loudestVelocity - 4)
						w.velocityDelta = -max(4, abs(w.velocityDelta))
						w.velocity += w.velocityDelta
			
			elif theKey == 'g':
				if 'alt' in self.keysPressed and widgetList:
					self.flockFrequency = widgetList[0].frequency
				elif self.shiftPressed:
					for w in widgetList:
						w.original_frequency()
				else:
					if self.flockFrequency:
						for w in widgetList:
							w.start_flocking(self.quantize_to_tempo(w.frequency, refFreq = self.flockFrequency), random.randrange(*self.flockSpeed))
					elif self.lastFrequency:
						for w in widgetList:
							w.start_flocking(self.quantize_to_tempo(w.frequency, refFreq = self.lastFrequency), random.randrange(*self.flockSpeed))
				return
			
			elif theKey == '.':
				if 'super' in self.keysPressed:
					self.highVelocity = 70
					self.lowVelocity = 14
					for w in widgetList:
						w.quietestVelocity = random.randrange(self.lowVelocity, self.lowVelocity + 10)
						w.loudestVelocity = random.randrange(self.highVelocity - 16, self.highVelocity)
				elif not widgetList:
					self.lowVelocity = min(self.highVelocity - 4, self.lowVelocity + 4)
					self.highVelocity = min(100, self.highVelocity + 4)
				else:
					for w in widgetList:
						w.loudestVelocity = min(100, w.loudestVelocity + 5)
						w.quiestestVelocity = min(w.quietestVelocity + 5, w.loudestVelocity - 4)
						w.velocityDelta = max(4, abs(w.velocityDelta))
						w.velocity += w.velocityDelta
				return
			
			elif theKey in '1234567890':
				if 'g' in self.keysPressed:
					self.flockSpeed = self.flockSpeeds[theKey]
				else:
					targetChannel = 'x12345678900'.index(theKey)
					if 'super' in self.keysPressed:
						self.selectedCircles = []
						for w in self.liveCircles:
							if w.channel == targetChannel:
								self.selectedCircles.append(w)
					else:
						self.defaultChannel = targetChannel
						for w in widgetList:
							w.channel = targetChannel
							w.set_channel_and_color()
				return
			
			elif theKey in ['f1', 'f2','f3', 'f4', 'f5', 'f6']:
				targetChannel = 10 + 'x12345678900'.index(theKey[1])
				if 'super' in self.keysPressed:
					self.selectedCircles = []
					for w in self.liveCircles:
						if w.channel == targetChannel:
							self.selectedCircles.append(w)
				else:
					self.defaultChannel = targetChannel
					for w in widgetList:
						w.channel = targetChannel
						w.set_channel_and_color()
				return

			elif theKey == 'q':
				if 'alt' in self.keysPressed:
					self.randomMode = False
					self.playBothNotesAtOnce = False
					for w in widgetList + self.kRhythmWidgets:
						w.indexList = random.choice([[0, 0], [1, 1], [0, 1]])[:]
						w.randomMode = False
						w.playBothNotesAtOnce = False
					return
				elif self.shiftPressed and not self.kRhythm:
					l = [1, 1]
				else:
					l = [0, 0]
				self.randomMode = False
				self.playBothNotesAtOnce = False
				self.globalIndexList = l
				for w in widgetList + self.kRhythmWidgets:
					w.indexList = l
					w.randomMode = False
					w.playBothNotesAtOnce = False
			
			elif theKey == 'w':
				if self.shiftPressed and not self.kRhythm:
					self.randomMode = True
					self.playBothNotesAtOnce = False
					self.globalIndexList = [0, 1]
					for w in widgetList + self.kRhythmWidgets:
						w.indexList = [0, 1]
						w.randomMode = True
						w.playBothNotesAtOnce = False
				else:
					self.globalIndexList = [0, 1]
					self.playBothNotesAtOnce = False
					self.playOnce = False
					self.randomMode = False
					for w in widgetList + self.kRhythmWidgets:
						w.playBothNotesAtOnce = False
						w.indexList = [0, 1]
						w.randomMode = False
	
			elif theKey == 'f10':
				if self.shiftPressed:
					self.lastFrequency = self.lastFrequency*2.
				else:
					self.lastFrequency = self.lastFrequency/2.
				return
				
			
			elif theKey == 'f11' or theKey == 'f12':
				for w in widgetList:
					w.unschedule()
					w.calculate_refire_delay()
					w.refireDelay = w.refireDelay % w.frequency
					if 'alt' in self.keysPressed:
						freqRatio = random.randrange(80, 133)/100.
					elif theKey == 'f11':			
						if self.shiftPressed:
							freqRatio = 1.414
						else:
							freqRatio = 1.0905
					else:
						if self.shiftPressed:
							freqRatio = .707
						else:
							freqRatio = .917
					w.frequency = freqRatio * w.frequency
					w.refireDelay *= freqRatio
					if w.rhythmIntervals:
						w.rhythmIntervals = [freqRatio * x for x in w.rhythmIntervals]
						w.start_clock(startOffset = w.refireDelay)
					else:
						w.start_clock(startOffset = w.refireDelay, modStartOffsets = False)
								
			elif theKey == 'z':
				if self.shiftPressed:
					for w in widgetList:
						if w.quietestVelocity < 0:
							w.quietestVelocity = max(10, w.velocity)
						w.velocityDelta = abs(w.velocityDelta)
				else:
					if widgetList != self.lastFade:
						self.store_preset('z', overwrite = True)
						self.lastPresetStored = 'z'
						self.lastFade = widgetList
					for w in widgetList:
						w.quietestVelocity = -10
						if w.velocityDelta > -1:
							w.velocityDelta = -1
						elif w.velocityDelta >= -6:
							w.velocityDelta += -2
						else:
							w.velocityDelta += -5
						
			elif theKey == 'x' or theKey == 'backspace':
				self.changePitchesWithKeyboard = False
				self.selectedCircles = widgetList[:]
				self.lastPresetStored = 'x'
				self.store_preset('x', overwrite = True)
				for w in widgetList:
					w.kill()
				self.selectedCircles = []
					
			elif theKey == 'v':								# random velocity
				if self.shiftPressed:
					for w in widgetList:
						w.stop_moving()
						w.moveVector = False
						w.move_to_target(position = w.originalPosition[:])
				else:
					for w in widgetList:
						if w.moveVector:
							w.moveVector = [x * 2. for x in w.moveVector]
						else:
							w.moveVector = [random.randrange(-15, 16), random.randrange(-15, 16)]
						w.start_moving()
			
			elif theKey == 'o':
				if self.shiftPressed:
					for w in widgetList:
						w.playNote = True
				else:
					for w in widgetList:
						w.playNote = not w.playNote
					
			elif theKey == 'f':
				if self.shiftPressed:
					self.useLastFrequency = False
					self.lastFrequency = 0
				else:
					self.useLastFrequency = True
					if widgetList:
						self.lastFrequency = widgetList[0].frequency
					elif self.liveCircles:
						self.lastFrequency = self.liveCircles[-1].frequency
			
			elif theKey == 'r':		#reset, still need to deal with frequencies 
				for w in widgetList:
					w.stop_moving()
					w.moveVector = False
					w.move_to_target(position = w.originalPosition[:])
					w.channel = w.originalChannel
					w.set_channel_and_color()
					w.original_frequency()
					
			elif theKey == 'y':
				if self.shiftPressed:
					self.playBothNotesAtOnce = False
					for w in widgetList:
						w.playBothNotesAtOnce = False
				else:
					self.playBothNotesAtOnce = True
					for w in widgetList:
						w.playBothNotesAtOnce = True
			
			elif theKey == 'l':
				if self.shiftPressed:
					self.drawLines = False
					for w in widgetList:
						w.unmake_line()
				else:
					self.drawLines = True
					for w in widgetList:
						w.make_line()
						
	def complete_rhythmic_patterns(self):
		self.kRhythmInProgress = False
		if self.kRhythm:
			self.kRhythm.append(time.time())
			if (not self.useLastFrequency) or (not self.lastFrequency):
				self.lastFrequency = self.kRhythm[1] - self.kRhythm[0]
				self.finish_rhythmic_patterns(self.kRhythmWidgets)
			else:
				kRhythmFreq = self.kRhythm[1] - self.kRhythm[0]
				deltaTime = (int(kRhythmFreq/self.lastFrequency) + 1) * self.lastFrequency
				self.finish_rhythmic_patterns(self.kRhythmWidgets, extraDelay = deltaTime - kRhythmFreq)
			self.keyboardKRhythmDict = {}
			self.kRhythm = []	# NEW, does it cause bugs?
			self.kRhythmWidgets = []
			#self.keyboardKRhythmDict = []
	
	def _on_keyboard_up(self, keyboard, keycode):					# keep track of which keys are pressed
	
		if keycode[1] == 'shift':
			self.complete_rhythmic_patterns()
		elif keycode[1] == 'm':
			self.waitingForScale = False
			self.buildScale = set([])
			if time.time() - self.mTimer < .3:
				self.initialize_scale(commonTones = self.lastCommonTones)
		elif keycode[1] == 'b':
			
			if 'shift' in self.keysPressed:
				t = time.time()
				for w in self.kRhythmWidgets:
					w.rhythmIntervals.append(t)
					w.update()
			elif self.burstInProgress:
			
				attributeList = []
				t = time.time()
				for w in self.burstInProgress:
					w.kill()
				self.burstInProgress = []
			
		self.keysPressed.remove(keycode[1])
		self.selectionLineColor.rgba = (.35, .35, .35, 0)
	
	"""quantize to tempogrid"""
	def quantize_to_tempo(self, f, refFreq = None):
		if not refFreq:
			refFreq = self.lastFrequency/self.subdivisions
		else:
			refFreq = refFreq/self.subdivisions
		return refFreq * max(1, int((f/float(refFreq)) + .5))
	
	def finish_rhythmic_patterns(self, widgetList, extraDelay = 0):
		self.selectedCircles = widgetList
		for w in widgetList:
			w.finish_rhythmic_pattern(extraDelay = extraDelay)
	
	def on_touch_down(self, touch):					# handle mouse touches
		eventHandled = super(BeaconsWindow, self).on_touch_down(touch)	# passes the event on to child widgets
		self.selectionLineColor.rgba = (.35, .35, .35, 0)
		if touch.button == 'left' and not eventHandled and len(self.keysPressed) == 0 and (not self.playOnce):
			self.selectedCircles = []
			self.selectionBox = [touch.pos, False]
			return True
		elif touch.button == 'left' and not eventHandled:
			if ('shift' in self.keysPressed) or self.playOnce:
				t = time.time()
				nw = EllipseWidget(startPos = [touch.x, touch.y], rhythmIntervals = [t], frequency = self.lastFrequency, randomMode = self.randomMode, playBothNotesAtOnce = self.playBothNotesAtOnce, kRhythmInProgress = True)
				nw.register()
				nw.update()
				"""I would like to do this, but it doesn't work!
				touch.grab(nw)
				debug('grabbed the touch', nw, touch.grab_current)"""
				self.kRhythmWidgets.append(nw)
				if len(self.kRhythmWidgets) == 1:
					self.kRhythm = [t]
			#elif not 'v' in self.keysPressed and not 'z' in self.keysPressed:					# if not handled by them, make a circle
			#	nw = EllipseWidget(startPos = [touch.x, touch.y], frequency = self.lastFrequency, playBothNotesAtOnce = self.playBothNotesAtOnce)
			return True
	
	def on_touch_move(self, touch):										# handle mouse touches
		eventHandled = super(BeaconsWindow, self).on_touch_move(touch)	# passes the event on to child widgets
		if not eventHandled and self.selectionBox[0]:
			self.selectionLineColor.rgba = (.35, .35, .35, .3)
			self.selectionBox[1] = touch.pos
			self.xRange = sorted([x[0] for x in self.selectionBox])
			self.yRange = sorted([x[1] for x in self.selectionBox])
			self.selectionLines.pos = [self.xRange[0], self.yRange[0]]
			self.selectionLines.size = [self.xRange[1] - self.xRange[0], self.yRange[1] - self.yRange[0]]
				
	def on_touch_up(self, touch):					# handle mouse touches
		
		eventHandled = super(BeaconsWindow, self).on_touch_up(touch)	# passes the event on to child widgets
		
		if eventHandled: return True
		
		if touch.button == 'left' and len(self.keysPressed) == 0 and not eventHandled and self.selectionBox[0]:
			self.selectionBox[1] = touch.pos
			self.xRange = sorted([x[0] for x in self.selectionBox])
			self.yRange = sorted([x[1] for x in self.selectionBox])
			self.selectionLineColor.rgba = (.35, .35, .35, .3)
			self.selectionBox = [False, False]
			self.selectionLines.pos = [self.xRange[0], self.yRange[0]]
			self.selectionLines.size = [self.xRange[1] - self.xRange[0], self.yRange[1] - self.yRange[0]]
			self.selectedCircles = []
			for c in self.liveCircles:			# probably a Kivy command for this
				if c.center_x > self.xRange[0] and c.center_x < self.xRange[1] and c.center_y > self.yRange[0] and c.center_y < self.yRange[1]:
					self.selectedCircles.append(c)
			return True
		elif touch.button == 'left' and not eventHandled:
			if 'shift' in self.keysPressed and len(self.kRhythmWidgets) > 0:
				self.kRhythmWidgets[-1].on_touch_up(touch, directCall = True)		# shouldn't need this?
				return True
			elif self.playOnce and len(self.kRhythmWidgets) > 0:
				for w in self.kRhythmWidgets:
					w.kill()
				self.kRhythmWidgets = []
				self.kRhythm = []
				self.selectedCircles = []
	
	def load_presets(self, presetFile = 'beaconspresets.pkl'):
		try:
			with open(presetFile, 'rb') as f:
				self.presetDict = pickle.load(f)
			if 'x' in self.presetDict:
				del self.presetDict['x']
		except:
			print("No presets found")
			
	def save_presets(self, presetFile = 'beaconspresets.pkl'):
		if self.presetDict:
			with open(presetFile, 'w+') as f:
				pickle.dump(self.presetDict, f)
	
	def algorithmic_pattern(self, intervalHisto, rhythmHisto, presetCode = 'f1', startNote = False, baseDuration = .05, yVariation = 3, lengthRange = [5, 20], velocityRange = [54, 84], **kwargs):
		outList = []
		if not startNote:
			startNote, yPos = get_MIDI_from_graphics(self.mousePos)
		lastNote = startNote
		baseDict = {'isACopy': True, "playNote": False, 'indexList': [0, 0], 'playOnce': True}
		totalDuration = 0
		if self.useLastFrequency:
			baseDuration = self.quantize_to_tempo(baseDuration/2.)
		for i in range(random.randrange(*lengthRange)):
			d = {}
			lastNote = lastNote + weighted_choice(*intervalHisto)
			if lastNote > 75 or lastNote <= 50: 
				break
			d['notes'] = [lastNote, yPos + random.randrange(-yVariation, yVariation + 1)]
			dur = weighted_choice(*rhythmHisto) * baseDuration
			d['refireDelay'] = totalDuration
			d['frequency'] = 1.9*baseDuration
			totalDuration += dur + .1 * baseDuration
			d.update(kwargs)
			d.update(baseDict)
			outList.append(d)
		self.presetDict[presetCode] = outList
		self.play_preset(presetCode)
	
	def play_preset(self, k):
		widgetList = self.presetDict.get(k, [])
		if not widgetList: return
		mainGame.selectedCircles = []
		moveVec = False
		if self.movablePresets:
			firstCircle = widgetList[0]
			if 'notes' in firstCircle:
				screenPos = [get_coord_from_scaledegree(n) for n in firstCircle['notes']]
				moveVec = [self.mousePos[i] - screenPos[i] for i in [0, 1]]
			else:
				moveVec = [self.mousePos[i] - firstCircle.pos[i] for i in [0, 1]]
		for e in widgetList:
			d = copy.deepcopy(e)			# think this is not needed, because d is unpacked as arguments
			if self.movablePresets: 
				d['initialDisplacementVector'] = moveVec
			if 'channel' not in d:
				w = EllipseWidget(channel = self.defaultChannel, **d)
			else:
				w = EllipseWidget(**d)
			w.playNote = True
			w.isACopy = False
			w.start_clock(startOffset = w.refireDelay, modStartOffsets = False)
			mainGame.selectedCircles.append(w)
	
	def store_preset(self, k, overwrite = False):
		if not overwrite and k in self.presetDict: return				# prohibit overwriting of presets
		print('Stored preset', k)
		if self.toMaxOutput:
			i = ord(k[0].lower())
			if 0 <= i <= 127:
				self.toMaxOutput.send_message([149, i, 60])
			self.toMaxOutput.send_message([147, 42, 60])
		attributeList = []
		if self.buildingPreset:
			if not self.presetWidgets: return
			t = self.presetWidgets[0][1]
			for w, tStart in self.presetWidgets:
				temp = w.copy(returnDict = True)
				d = copy.deepcopy(temp)				# good to fix this
				d['counter'] = -1
				if d['rhythmIntervals']:
					l = d['rhythmIntervals']
					if len(l) <= 2 and not d['clockIsStarted']:
						d['rhythmIntervals'] = []
						d['playOnce'] = True
						d['kRhythmInProgress'] = False
						if len(l) == 2:
							d['frequency'] = l[1] - l[0]
					else:
						d['rhythmIntervals'] = [x - l[0] for x in l]
				d['isACopy'] = True
				d['playNote'] = False
				d['refireDelay'] = tStart - t
				attributeList.append(d)
		else:
			for w in self.selectedCircles:
				w.calculate_refire_delay()
				temp = w.copy(returnDict = True)
				d = copy.deepcopy(temp)
				d['isACopy'] = True
				d['playNote'] = False
				attributeList.append(d)
		self.presetDict[k] = attributeList
		self.buildingPreset = False
		self.presetStartTime = time.time()
		self.presetWidgets = []
		
	def on_resize(self, *args):					# doesn't work yet
		#print(time.time(), args[1:])
		pass
		
	def debug_update(self, args):
		# debugging
		
		for i, w in enumerate(self.children):
			t = time.time()
			if t - w.lastFiringTime > 20:
				print (i, type(w).__name__, format(id(w), 'x'), w.channel)
				print( "\n\n\n", t, )
				print ("  DEFUNCT BUT STILL HANGING AROUND?")
				w.print_everything()
				print("\n\n\n")
				w.kill()
			if w not in self.liveCircles:
				print ("  NOT IN LIVECIRCLES!")
		for w in self.liveCircles:
			if w not in self.children:
				print( w, type(w).__name__, format(id(w), 'x'))
				print ("  NOT IN SELF.CHILDREN!")

class BeaconsApp(App):
	def build(self):
		global mainGame
		Window.borderless = True
		mainGame = BeaconsWindow()
		return mainGame
	
	def open_settings(*args):			# needed if you want to use F1 for other purpoes
		pass
		
	def on_start(self):
		global mainGame
		mainGame.xyBoundaries = [[0, mainGame.width], [0, mainGame.height]]
		mainGame.load_presets()
		mainGame.initialize_scale([0, 4, 5, 8, 11])
		mainGame.make_random_Y_coordinates()
		get_midi_output()
		#mainGame.screen_print()
		#mainGame.initialize_midi()
			
	def on_stop(self):
		for i in range(16):
			mainGame.master_MIDI_out([176 + i, 64, 0])				# lift pedal
			mainGame.master_MIDI_out([176 + i, 123, 0])				# all notes off
			if mainGame.midiout2:
				mainGame.midiout2.send_message([176 + i, 64, 0])				# lift pedal
				mainGame.midiout2.send_message([176 + i, 123, 0])				# all notes off
		fName = time.asctime().split()
		fName = '-'.join(fName[1:3] + [fName[4]] + [fName[3].replace(':', '-')]) + '.pkl'
		if mainGame.toMaxOutput:
			mainGame.toMaxOutput.close_port()
		releaseIO(False, mainGame.midiout)
		if mainGame.midiout2:
			releaseIO(mainGame.midiin2, mainGame.midiout2)
		
if __name__ == '__main__':
	BeaconsApp().run()	