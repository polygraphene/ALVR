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

global timestamp, buttonsUpdateTime, forwardOrientation, controllerOffsetX, controllerOffsetY, controllerOffsetZ, leftClick, rightClick, isCrouch, touchX, touchY

#ControllerPivotVector - placed at the right eye for better aiming
defaultPivotX = 0.033
defaultPivotY = 0
defaultPivotZ = -0.5

if starting:
	timestamp = time.time()
	leftClick = False
	rightClick = False
	isCrouch = False
	touchX = 0
	touchY = 0
	controllerOffsetX = 0
	controllerOffsetY = 0
	controllerOffsetZ = 0
	#controllerPivotVector = [defaultPivotX,defaultPivotY,defaultPivotZ]
	buttonsUpdateTime = 0
	forwardOrientation = [0,0,0]

deltaTime = time.time() - timestamp

buttonsUpdateTime += deltaTime

if (deltaTime > 0.0):
	timestamp = time.time()
	diagnostics.watch(deltaTime)
	
	# Touch and drag tracking
	
	mouseBtnBack = mouse.getButton(3)
	mouseBtnFwd = mouse.getButton(4)
	
	touchX = 0
	touchY = 0
	if (mouseBtnFwd):
		touchY = 1
	elif (mouseBtnBack):
		touchY = -1
	else:
		touchY = 0

	alvr.trackpad[0][0] = touchX
	alvr.trackpad[0][1] = touchY
	
	diagnostics.watch(touchX)
	diagnostics.watch(touchY)
		
	keyboardX = (keyboard.getKeyDown(Key.D) * 1.0 - keyboard.getKeyDown(Key.A) * 1.0)
	keyboardY = (keyboard.getKeyDown(Key.W) * 1.0 - keyboard.getKeyDown(Key.S) * 1.0)

	diagnostics.watch(keyboardX), diagnostics.watch(keyboardY)
	
	targetOrientation = [alvr.head_orientation[0], alvr.head_orientation[1], alvr.head_orientation[2]]
	if (mouse.rightButton):
		controllerOffsetX = lerp(controllerOffsetX, 0.2, 2 * deltaTime)
		controllerOffsetY = lerp(controllerOffsetY, 0.2, 2 * deltaTime)
		controllerOffsetZ = lerp(controllerOffsetZ, 0.2, 2 * deltaTime)
		targetOrientation[2] += math.radians(160)
		rightClick = True
	else:
		if (rightClick):
			rightClick = False
	
	leftClick = mouse.leftButton

	forwardOrientation[0] = moveTowards(forwardOrientation[0], targetOrientation[0], 50 * deltaTime)
	forwardOrientation[1] = moveTowards(forwardOrientation[1], targetOrientation[1], 50 * deltaTime)
	forwardOrientation[2] = moveTowards(forwardOrientation[2], targetOrientation[2], 5 * deltaTime)
	
	mouseX = mouse.deltaX * 0.001
	mouseY = mouse.deltaY * 0.001
	
	controllerOffsetZ -= mouse.wheel * 0.001
	diagnostics.watch(mouseX), diagnostics.watch(mouseY)

	if (not leftClick and not rightClick and not mouse.wheel):
		controllerOffsetX = clamp(controllerOffsetX, -0.4, 0.4)
		controllerOffsetY = clamp(controllerOffsetY, -0.4, 0.4)
		#controllerOffsetZ = clamp(controllerOffsetZ, -0.4, 0.6)
	
	
	# Reset hand position
	if ( not rightClick):
		controllerOffsetX = lerp(controllerOffsetX, 0, 2 * deltaTime)
		controllerOffsetY = lerp(controllerOffsetX, 0, 2 * deltaTime)
		controllerOffsetZ = lerp(controllerOffsetZ, 0, 2 * deltaTime)
	
	# Head offset and crouching
	
	alvr.override_head_position = True
	
	if (keyboard.getPressed(Key.LeftControl)):
		isCrouch = not isCrouch
	
	headOffset = [0, 0, 0]
	if (isCrouch):
		headOffset[1] = -0.5
	else:
		headOffset[1] = 0.0
	
	alvr.head_position[0] = 0
	alvr.head_position[1] = lerp(alvr.head_position[1], headOffset[1], 20 * deltaTime)
	alvr.head_position[2] = 0

	alvr.override_head_orientation = True
	
	alvr.head_orientation[1] += -mouseX
	alvr.head_orientation[2] += -mouseY
	
	alvr.override_controller_orientation = True

	rot = alvr.controller_orientation[0]
	rot[0] = lerp(rot[0], forwardOrientation[0], 0.2)
	rot[1] = lerp(rot[1], forwardOrientation[1] + math.radians(-8), 0.2)
	rot[2] = lerp(rot[2], forwardOrientation[2] + math.radians(58), 0.2)
	
	# Controller position
	
	alvr.override_controller_position = True
	
	# Local vector from controller pivot
	controllerOffsetVector = rotatevec(forwardOrientation, [controllerOffsetX, controllerOffsetY, controllerOffsetZ,0])
	
	diagnostics.watch(controllerOffsetVector[0]), diagnostics.watch(controllerOffsetVector[1]), diagnostics.watch(controllerOffsetVector[2]);
	
	controllerPivotVector = rotatevec( [forwardOrientation[0], forwardOrientation[1], forwardOrientation[2]], [defaultPivotX, defaultPivotY, defaultPivotZ,0] )
	
	desiredControllerPosition = add(controllerPivotVector, controllerOffsetVector)
	
	alvr.controller_position[0][0] = lerp(alvr.controller_position[0][0], desiredControllerPosition[0], 0.9)
	alvr.controller_position[0][1] = lerp(alvr.controller_position[0][1], desiredControllerPosition[1] + headOffset[1], 0.9)
	alvr.controller_position[0][2] = lerp(alvr.controller_position[0][2], desiredControllerPosition[2], 0.9)
	
if (buttonsUpdateTime >= 0.02):

	deltaTime = buttonsUpdateTime
	
	buttonsUpdateTime = 0.0

	alvr.buttons[0][alvr.Id("system")] = keyboard.getKeyDown(Key.Q)
	
	alvr.buttons[0][alvr.Id("application_menu")] = mouse.middleButton
	
	# Controller buttons
	
	trackpadClickNow = (not rightClick and (mouseBtnFwd or mouseBtnBack))
	
	alvr.buttons[0][alvr.Id("trackpad_click")] = trackpadClickNow
	
	alvr.buttons[0][alvr.Id("trackpad_touch")] = True
	
	alvr.trackpad[0]
	
	# Hold touchpad down and pull the trigger to activate 'Grip' button
	
	triggerPulledNow = leftClick
	
	alvr.buttons[0][alvr.Id("grip")] = keyboard.getKeyDown(Key.R)
	#if (rightClick):
		#alvr.buttons[0][alvr.Id("grip")] = mouseBtnBack
	#else:	
		#alvr.buttons[0][alvr.Id("grip")] = keyboard.getKeyDown(Key.Space)
		
	alvr.trigger[0] = triggerPulledNow