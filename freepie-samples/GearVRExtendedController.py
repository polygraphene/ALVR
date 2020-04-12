import math, time

# GearVR Extended Controller v0.9
#----------------------------------------------------------------------------
# INFO
#----------------------------------------------------------------------------
# This is controller script optimized for GearVR controller in HL:Alyx game. Use FreePIE to execute this script.
#
# *** Note: enable one-handed mode in SteamVR controller settings! Also disable application menu on trackpad center action
#
# * Rotate GearVR controller to move and rotate your hand
# * Swipe GearVR controller trackpad to extend your arm
# * Double-click trackpad 'Down' button to crouch
# * 'Back' button is mapped to controller 'Grip' for reloading weapon in HL:Alyx. Do not hold it too long - it will trigger system back action! 
# * Double-click 'Back' button to call System menu
# * Center trackpad button is 'Application Menu'. You shoud disable redundant action mapping in SteamVR controller settings
# 
# Look for SETTINGS below

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
# SETTINGS
#----------------------------------------------------------------------------

# Arm pivot relative to your head
armLocalPosition = [0.2, -0.2, -0.1]

# Hand is placed at the arm position + arm offset that you can control with trackpad. This is default arm offset
defaultArmX = 0.0
defaultArmY = 0.0
defaultArmZ = 0.4

# How low player can duck
crouchOffset = -0.8

# Enable this for head position displacement for correcting ARCore data
ARCoreCorrection = False

#----------------------------------------------------------------------------
#	Main Program
#----------------------------------------------------------------------------

global timestamp, rightControllerId, buttonsUpdateTime, lastTouchTime, isClick, downClick, backClick, isTouch, oldTouchX, oldTouchY, controllerOffsetX, controllerOffsetY, controllerOffsetZ, triggerPulled, clickHoldTime, downClickTime, backClickHoldTime, backClickTime, gripTriggerToggle, isCrouch, isSnappedAim

if starting:
	isClick = False
	timestamp = time.time()
	lastTouchTime = time.time()
	downClickTime = 0
	backClickTime = 0
	clickHoldTime = 0
	rightControllerId = 0
	oldTouchY = 0
	oldTouchX = 0
	controllerOffsetX = 0
	controllerOffsetY = 0
	controllerOffsetZ = 0
	isTouch = False
	downClick = False
	triggerPulled = False
	isCrouch = False
	gripTriggerToggle = False
	backClick = False
	isSnappedAim = False
	
	inputTouchId = alvr.InputId("trackpad_touch")
	inputTrackpadClickId = alvr.InputId("trackpad_click")
	inputTriggerId = alvr.InputId("trigger")
	inputBackId = alvr.InputId("back")
	touchId = alvr.Id("trackpad_touch")
	clickId = alvr.Id("trackpad_click")
	systemId = alvr.Id("system")
	menuId = alvr.Id("application_menu")
	gripId = alvr.Id("grip")

deltaTime = time.time() - timestamp

if (deltaTime > 0.0):
	timestamp = time.time()
	diagnostics.watch(deltaTime)
	
	# Get GearVR Input
	inputHeadPosition = [alvr.input_head_position[0],alvr.input_head_position[1],alvr.input_head_position[2]]
	if (isCrouch):
		inputHeadPosition.y = crouchOffset
	inputHeadRotation = [alvr.input_head_orientation[0], alvr.input_head_orientation[1], alvr.input_head_orientation[2]]
	inputControllerPosition = [alvr.input_controller_position[0],alvr.input_controller_position[1],alvr.input_controller_position[2]]
	inputControllerRotation = [alvr.input_controller_orientation[0],alvr.input_controller_orientation[1],alvr.input_controller_orientation[2]]
	controllerLocalPosition = sub(inputControllerPosition, inputHeadPosition)
	#diagnostics.watch(controllerLocalPosition.x), diagnostics.watch(controllerLocalPosition.y),diagnostics.watch(controllerLocalPosition.z)
	
	# Get Controller Input
	wasTouched = isTouch
	isTouch = alvr.input_buttons[inputTouchId]
	isClickNow = alvr.input_buttons[inputTrackpadClickId]
	touchX = alvr.input_trackpad[0]
	touchY = alvr.input_trackpad[1]
	deltaTouchX = 0
	deltaTouchY = 0
	if (isTouch):
		lastTouchTime = time.time()
		if (wasTouched):
			deltaTouchX = (touchX - oldTouchX)
			deltaTouchY = (touchY - oldTouchY)
		oldTouchX = touchX
		oldTouchY = touchY
	diagnostics.watch(isTouch), diagnostics.watch(touchX), diagnostics.watch(touchY)
	
	# Get Trackpad Down Click
	downClickDouble = False
	if (isClickNow):
		# prevents click from happening until double click time gap ended
		if (not isClick and clickHoldTime > 0.15 or alvr.input_trackpad[1] > -0.75): 
			isClick = True
		clickHoldTime += deltaTime
		if (not downClick and alvr.input_trackpad[1] < -0.75):
			if (time.time() - downClickTime < 0.3 ):
				downClickDouble = True
				isCrouch = not isCrouch
			downClickTime = time.time()
			downClick = True
	else:
		clickHoldTime = 0
		isClick = False
		downClick = False
	
	# Get Keyboard WASD
	keyboardX = (keyboard.getKeyDown(Key.D) * 1.0 - keyboard.getKeyDown(Key.A) * 1.0)
	keyboardY = (keyboard.getKeyDown(Key.W) * 1.0 - keyboard.getKeyDown(Key.S) * 1.0)
	#diagnostics.watch(keyboardX), diagnostics.watch(keyboardY)
	
	# Set Trackpad XY touch
	alvr.trackpad[rightControllerId][0] = touchX
	alvr.trackpad[rightControllerId][1] = touchY
	
	# Set Trackpad touch and click
	alvr.buttons[rightControllerId][touchId] = isTouch
	alvr.buttons[rightControllerId][clickId] = isClick

	# Move virtual controller position by deltaTouch
	if ( isTouch ):
		controllerOffsetX += deltaTouchX * 0.25
		controllerOffsetZ += deltaTouchY * 0.50
	controllerOffsetX = clamp(controllerOffsetX, -0.3, 0.3)
	controllerOffsetY = clamp(controllerOffsetY, -0.3, 0.3)
	controllerOffsetZ = clamp(controllerOffsetZ,  0.0, 0.8)
	controllerLocalOffset = [controllerOffsetX, controllerOffsetY, -controllerOffsetZ]
	
	# Clear controller position offset after some time of inactivity
	if (not isTouch and (time.time() - lastTouchTime) > 0.2):
		t = 2.0 * deltaTime
		controllerOffsetX = lerp(controllerOffsetX, defaultArmX, t)
		controllerOffsetY = lerp(controllerOffsetY, defaultArmY, t)
		controllerOffsetZ = lerp(controllerOffsetZ, defaultArmZ, t)
	
	# Controller position and rotation override
	alvr.override_controller_orientation = True
	alvr.override_controller_position = True
	
	handPivotPosition = add( inputHeadPosition, rotatevec(inputHeadRotation, armLocalPosition+[0]) )
	handPosition = add( handPivotPosition, rotatevec(inputControllerRotation, controllerLocalOffset+[0]) )
	handLocalPosition = sub(handPosition, inputHeadPosition)
	#diagnostics.watch(controllerLocalX), diagnostics.watch(controllerLocalY),diagnostics.watch(controllerLocalZ)
	controllerRotation = inputControllerRotation

	alvr.controller_orientation[rightControllerId][0] = controllerRotation[0] #lerp(alvr.controller_orientation[rightControllerId][0], controllerRotationX, deltaTime * 30)
	alvr.controller_orientation[rightControllerId][1] = controllerRotation[1] #lerp(alvr.controller_orientation[rightControllerId][1], controllerRotationY, deltaTime * 30)
	alvr.controller_orientation[rightControllerId][2] = controllerRotation[2] + math.radians(45) #lerp(alvr.controller_orientation[rightControllerId][2], controllerRotationZ, deltaTime * 30) #  + math.radians(45)
	
	t = deltaTime * 50
	alvr.controller_position[rightControllerId][0] = lerp(alvr.controller_position[rightControllerId][0], handPosition[0], t )
	alvr.controller_position[rightControllerId][1] = lerp(alvr.controller_position[rightControllerId][1], handPosition[1], t )
	alvr.controller_position[rightControllerId][2] = lerp(alvr.controller_position[rightControllerId][2], handPosition[2], t )
	
	alvr.override_head_position = True
	
	if (ARCoreCorrection):
		headToDisplayDistance = -0.25
	else:
		headToDisplayDistance = 0.0
	
	headPosition = sub(inputHeadPosition, rotatevec(inputHeadRotation, [0,0,headToDisplayDistance,0]))
	#diagnostics.watch(v[0]), diagnostics.watch(v[1]),diagnostics.watch(v[2])
	alvr.head_position[0] = headPosition[0]
	alvr.head_position[1] = headPosition[1]
	alvr.head_position[2] = headPosition[2]
	
	# Hold touchpad down and pull the trigger to activate 'Grip' button
	triggerPulledNow = alvr.input_buttons[inputTriggerId]
	
	triggerPulled = triggerPulledNow

	alvr.trigger[rightControllerId] = triggerPulled
	backClickNow = alvr.input_buttons[inputBackId]
	if (backClickNow):
		backClickHoldTime += deltaTime
	else:
		backClickHoldTime = 0
		
	backClickDeltaTime = (time.time() - backClickTime) 
	backClickDouble = False
	if (backClickNow):
		if (not backClick):
			if (backClickDeltaTime < 0.5):
				backClickDouble = True
			
		backClickTime = time.time()
		backClick = True
	else:
		if (backClick and backClickHoldTime < 0.15):
			gripTriggerToggle = not gripTriggerToggle;
		backClick = False
	
	centerClick = False
	if (isClick and touchX > -0.3 and touchX < 0.3 and touchY > -0.3 and touchY < 0.3):
		#if (clickHoldTime > 0.2):
		centerClick = True
		isClick = False
		
	alvr.buttons[rightControllerId][gripId] = backClick or keyboard.getKeyDown(Key.R)
	
	alvr.buttons[0][systemId] = backClickDouble
	#diagnostics.watch(systemButton)
	backClick = backClickNow
	if (centerClick):
		alvr.buttons[rightControllerId][menuId] = True
	else:
		alvr.buttons[rightControllerId][menuId] = False
	diagnostics.watch(gripTriggerToggle), diagnostics.watch(backClickDeltaTime), diagnostics.watch(backClick), diagnostics.watch(backClickHoldTime)
	diagnostics.watch(triggerPulled)
	executeTime = time.time() - timestamp
	diagnostics.watch(executeTime)