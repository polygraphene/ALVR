import math, time

#----------------------------------------------------------------------------
#	Math Utility
#----------------------------------------------------------------------------

def magnitude(v):
	return math.sqrt(sum(v[i]*v[i] for i in range(len(v))))

def mul(u, v):
	return [ u[i]*v for i in range(len(u)) ]

def add(u, v):
	return [ u[i]+v[i] for i in range(len(u)) ]

def sub(u, v):
	return [ u[i]-v[i] for i in range(len(u)) ]

def dot(u, v):
	return sum(u[i]*v[i] for i in range(len(u)))

def normalize(v):
	vmag = magnitude(v)
	return [ v[i]/vmag  for i in range(len(v)) ]

def clampMagnitude(v, max):
	if ( (v[0]*v[0]+v[1]*v[1]+v[2]*v[2]) > max*max):
		return mul(normalize(v), max)
	return v

def max(a, b):
	if (a > b):
		return a
	else:
		return b
		
def min(a, b):
	if (a < b):
		return a
	else:
		return b

def moveTowards(a, b, maxStep):
	if (b > a):
		return a + min(b-a, maxStep)
	else:
		return a + max(b-a, -maxStep)

def lerp(a, b, t):
	return a * (1 - t) + b * t

def sign(x): return 1 if x >= 0 else -1

def clamp(v, min, max):
	if (v < min):
		v = min
	elif (v > max):
		v = max
	return v

# conjugate quaternion
def conj(q):
  return [-q[0], -q[1], -q[2], q[3]]

# multiplication of quaternion
def multiply(a, b):
  x0, y0, z0, w0 = a
  x1, y1, z1, w1 = b
  return [x1 * w0 - y1 * z0 + z1 * y0 + w1 * x0,
	  x1 * z0 + y1 * w0 - z1 * x0 + w1 * y0,
	  -x1 * y0 + y1 * x0 + z1 * w0 + w1 * z0,
	  -x1 * x0 - y1 * y0 - z1 * z0 + w1 * w0]

# convert quaternion to euler
def quaternion2euler(q):
  yaw_pitch_roll = [0.0, 0.0, 0.0]
  # roll (x-axis rotation)
  sinr = +2.0 * (q[3] * q[0] + q[1] * q[2])
  cosr = +1.0 - 2.0 * (q[0] * q[0] + q[1] * q[1])
  yaw_pitch_roll[2] = atan2(sinr, cosr)

  # pitch (y-axis rotation)
  sinp = +2.0 * (q[3] * q[1] - q[2] * q[0])
  if (fabs(sinp) >= 1):
	yaw_pitch_roll[1] = math.copysign(M_PI / 2, sinp)
  else:
	yaw_pitch_roll[1] = math.asin(sinp)

  # yaw (z-axis rotation)
  siny = +2.0 * (q[3] * q[2] + q[0] * q[1]);
  cosy = +1.0 - 2.0 * (q[1] * q[1] + q[2] * q[2]);
  yaw_pitch_roll[0] = math.atan2(siny, cosy);

  return yaw_pitch_roll

# convert euler to quaternion
def euler2quaternion(yaw_pitch_roll):
  cy = math.cos(yaw_pitch_roll[0] * 0.5);
  sy = math.sin(yaw_pitch_roll[0] * 0.5);
  cr = math.cos(yaw_pitch_roll[2] * 0.5);
  sr = math.sin(yaw_pitch_roll[2] * 0.5);
  cp = math.cos(yaw_pitch_roll[1] * 0.5);
  sp = math.sin(yaw_pitch_roll[1] * 0.5);

  return [cy * sr * cp - sy * cr * sp,
  cy * cr * sp + sy * sr * cp,
  sy * cr * cp - cy * sr * sp,
  cy * cr * cp + sy * sr * sp]

# rotate specified vector using yaw_pitch_roll
def rotatevec(yaw_pitch_roll, vec):
  q = euler2quaternion(yaw_pitch_roll)
  return multiply(multiply(q, vec), conj(q))

#----------------------------------------------------------------------------
#	Main Program
#----------------------------------------------------------------------------

global timestamp, rightControllerId, keyboardAndMouseInput, buttonsUpdateTime, lastTouchTime, isTouch, oldTouchX, oldTouchY, controllerOffsetX, controllerOffsetY, controllerOffsetZ, downClick, triggerPulled, downClickTime, backClickTime, backClick, gripTriggerToggle, isCrouch, controllerLocalOffset

defaultArmX = -0.1
defaultArmY = -0.2
defaultArmZ = 0.05

if starting:
	timestamp = time.time()
	rightControllerId = 0
	keyboardAndMouseInput = False
	oldTouchY = 0
	oldTouchX = 0
	controllerOffsetX = 0
	controllerOffsetY = 0
	controllerOffsetZ = 0
	controllerLocalOffset = [defaultArmX,defaultArmY,defaultArmZ]
	isTouch = False
	lastTouchTime = time.time()
	downClickTime = 0
	backClickTime = 0
	downClick = False
	triggerPulled = False
	isCrouch = False
	buttonsUpdateTime = 0
	gripTriggerToggle = False
	backClick = False

deltaTime = time.time() - timestamp

buttonsUpdateTime += deltaTime

if (deltaTime > 0.0):
	timestamp = time.time()
	diagnostics.watch(deltaTime)
	
	if (keyboard.getPressed(Key.Tab)):
		keyboardAndMouseInput = not keyboardAndMouseInput
	
	diagnostics.watch(keyboardAndMouseInput)
	
	# Double click tracking
	
	downClickDouble = False
	
	if (alvr.input_buttons[alvr.InputId("trackpad_click")] and alvr.input_trackpad[1] < -0.75):
		if (not downClick and time.time() - downClickTime < 0.15):
			downClickDouble = True
		downClickTime = time.time()
		downClick = True
	else:
		downClick = False
	
	# Touch and drag tracking
	
	touchX = alvr.input_trackpad[0]
	touchY = alvr.input_trackpad[1]
	alvr.trackpad[rightControllerId][0] = touchX
	alvr.trackpad[rightControllerId][1] = touchY
	isTouch = alvr.input_buttons[alvr.InputId("trackpad_touch")]
	
	if (isTouch and not wasTouched):
		oldTouchX = touchX
		oldTouchY = touchY
	
	wasTouched = isTouch
	diagnostics.watch(isTouch)
	
	keyboardX = 0
	keyboardY = 0
	
	controllerPivotPosition = alvr.input_controller_position
	
	if (keyboardAndMouseInput):
		alvr.two_controllers = True
		#rightControllerId = 1 
		keyboardX = (keyboard.getKeyDown(Key.NumberPad6) * 1.0 - keyboard.getKeyDown(Key.NumberPad4) * 1.0) * deltaTime * 0.5
		keyboardY = (keyboard.getKeyDown(Key.NumberPad8) * 1.0 - keyboard.getKeyDown(Key.NumberPad2) * 1.0) * deltaTime * 0.5
		diagnostics.watch(keyboardX), diagnostics.watch(keyboardY)
	else:
		alvr.two_controllers = False
		rightControllerId = 0
	
	if (isTouch or keyboardX != 0 or keyboardY != 0 or mouse.deltaX != 0 or mouse.deltaY != 0 ):
		lastTouchTime = time.time()
		deltaTouchX = touchX - oldTouchX
		deltaTouchY = touchY - oldTouchY
		diagnostics.watch(touchX), diagnostics.watch(deltaTouchX)
		diagnostics.watch(touchY), diagnostics.watch(deltaTouchY)
		controllerOffsetX += deltaTouchX * 0.25
		controllerOffsetZ += deltaTouchY * 0.5
		if (keyboardAndMouseInput):
			mouseX = mouse.deltaX * 0.001
			mouseY = mouse.deltaY * 0.001
			controllerOffsetX += keyboardX + mouseX
			controllerOffsetZ += keyboardY - mouseY
			diagnostics.watch(mouseX), diagnostics.watch(mouseY)
			controllerPivotPosition[0] += mouseX
			controllerPivotPosition[0] -= mouseY
		
	controllerOffsetY += mouse.wheel *0.0001
		
	oldTouchX = touchX
	oldTouchY = touchY
	controllerOffsetX = clamp(controllerOffsetX, -0.4, 0.4)
	controllerOffsetZ = clamp(controllerOffsetZ, -0.2, 0.6)
	controllerLocalOffset = [controllerOffsetX, -0.15, -controllerOffsetZ]
	
	# Reset hand position after some time of inactivity
	if (not isTouch and (time.time() - lastTouchTime) > 0.4):
		controllerOffsetX = lerp(controllerOffsetX, -0.05, 0.5 * deltaTime)
		controllerOffsetZ = lerp(controllerOffsetZ, defaultArmZ, 0.5 * deltaTime)
	
	# Head offset and crouching
	
	alvr.override_head_position = True;
	
	headOffset = [0, 0, 0]
	if (keyboard.getPressed(Key.LeftControl) or downClickDouble):
		isCrouch = not isCrouch
	
	if (isCrouch):
		headOffset[1] = -0.5
	
	alvr.head_position[1] = lerp(alvr.head_position[1], headOffset[1], 20 * deltaTime)
	
	# Controller rotation
	
	alvr.override_controller_orientation = True

	alvr.controller_orientation[rightControllerId][0] = alvr.input_controller_orientation[0]
	alvr.controller_orientation[rightControllerId][1] = alvr.input_controller_orientation[1]
	alvr.controller_orientation[rightControllerId][2] = alvr.input_controller_orientation[2]
	#alvr.controller_orientation[rightControllerId][0] = lerp(alvr.controller_orientation[rightControllerId][0], alvr.input_controller_orientation[0], deltaTime * 2)
	#alvr.controller_orientation[rightControllerId][1] = lerp(alvr.controller_orientation[rightControllerId][1], alvr.input_controller_orientation[1], deltaTime * 2)
	#alvr.controller_orientation[rightControllerId][2] = lerp(alvr.controller_orientation[rightControllerId][2], alvr.input_controller_orientation[2], deltaTime * 2)
	
	
	# Controller position
	
	alvr.override_controller_position = True
	
	
	
	rotatedVector = rotatevec(alvr.controller_orientation[0], controllerLocalOffset+[0] )
	
	oldX = alvr.controller_position[rightControllerId][0]
	oldY = alvr.controller_position[rightControllerId][1]
	oldZ = alvr.controller_position[rightControllerId][2]
	
	desiredControllerPosition = add(controllerPivotPosition, rotatedVector)

	alvr.controller_position[rightControllerId][0] = lerp(alvr.controller_position[rightControllerId][0], desiredControllerPosition[0], 0.05)
	alvr.controller_position[rightControllerId][1] = lerp(alvr.controller_position[rightControllerId][1], desiredControllerPosition[1] + headOffset[1], 0.05)
	alvr.controller_position[rightControllerId][2] = lerp(alvr.controller_position[rightControllerId][2], desiredControllerPosition[2], 0.05)
	
	speedX = (alvr.controller_position[0][0] - oldX)/deltaTime
	speedY = (alvr.controller_position[0][1] - oldY)/deltaTime
	speedZ = (alvr.controller_position[0][2] - oldZ)/deltaTime
		
	speed = math.sqrt( speedX*speedX + speedY*speedY + speedZ*speedZ )
	#diagnostics.watch(speed)
	
if (buttonsUpdateTime >= 0.02):

	deltaTime = buttonsUpdateTime;
	buttonsUpdateTime = 0.0

	# Controller buttons
	
	alvr.buttons[rightControllerId][alvr.Id("trackpad_click")] = alvr.input_buttons[alvr.InputId("trackpad_click")]
	alvr.buttons[rightControllerId][alvr.Id("trackpad_touch")] = alvr.input_buttons[alvr.InputId("trackpad_touch")]
	
	# Hold touchpad down and pull the trigger to activate 'Grip' button
	
	triggerPulledNow = alvr.input_buttons[alvr.InputId("trigger")]
	
	if (not gripTriggerToggle):
		triggerPulled = triggerPulledNow
	else:
		alvr.buttons[rightControllerId][alvr.Id("grip")] = triggerPulledNow
	
	alvr.trigger[rightControllerId] = triggerPulled
	
	backClickNow = alvr.input_buttons[alvr.InputId("back")]
	
	if (backClick != backClickNow):
		if (backClickNow):
			gripTriggerToggle = not gripTriggerToggle;
	
	backClick = backClickNow
	
	if (backClickNow):
		backClickTime += deltaTime
	else:
		backClickTime = 0
	
	if (backClickTime > 0.3):
		alvr.buttons[rightControllerId][alvr.Id("application_menu")] = True
	else:
		alvr.buttons[rightControllerId][alvr.Id("application_menu")] = False
		
	diagnostics.watch(triggerPulled)
		
	
	