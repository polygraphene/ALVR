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
	return [ v[i]/vmag	for i in range(len(v)) ]

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
	yaw_pitch_roll[2] = math.atan2(sinr, cosr)

	# pitch (y-axis rotation)
	sinp = +2.0 * (q[3] * q[1] - q[2] * q[0])
	if (math.fabs(sinp) >= 1):
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

def cross(one, other):
	"""
	cross product of self and other vector
	the result is a new perpendicular vector to self and other
	the length of the new vector is defined as
	|cross product| = |self| * |other| * cos(theta)
	so the angle theta between self and other is calculated as follows
	theta = asin(|cross product| / (|self| * | other|))
	if self and other are unit vectors
	|self| = |other| = 1
	this simplifies to
	|cross product| = sin(theta)
	so you can use the cross product of two vectors two
	find the angle between these two vector, possible useful for shading/lightning
	"""
	return [one[1] * other[2] - one[2] * other[1], one[2] * other[0] - one[0] * other[2], one[0] * other[1] - one[1] * other[0] ]

def QuaternionLookRotation(forward, up):
	vector	= normalize(forward)
	vector2 = normalize(cross(up, vector))
	vector3 = normalize(cross(vector, vector2))
	m00 = vector2[0]
	m01 = vector2[1]
	m02 = vector2[2]
	m10 = vector3[0]
	m11 = vector3[1]
	m12 = vector3[2]
	m20 = vector[0]
	m21 = vector[1]
	m22 = vector[2]
	
	quaternion = [0,0,0,1]
	num8 = (m00 + m11) + m22
	if (num8 > 0.0):
		 num = math.sqrt(num8 + 1.0)
		 quaternion[3] = num * 0.5;
		 num = 0.5 / num;
		 quaternion[0] = (m12 - m21) * num;
		 quaternion[1] = (m20 - m02) * num;
		 quaternion[2] = (m01 - m10) * num;
		 return quaternion
	if ((m00 >= m11) and (m00 >= m22)):
		num7 = math.sqrt(((1.0 + m00) - m11) - m22)
		num4 = 0.5 / num7
		quaternion[0] = 0.5 * num7
		quaternion[1] = (m01 + m10) * num4
		quaternion[2] = (m02 + m20) * num4
		quaternion[3] = (m12 - m21) * num4
		return quaternion;
	if (m11 > m22):
		num6 = math.sqrt(((1.0 + m11) - m00) - m22)
		num3 = 0.5 / num6
		quaternion[0] = (m10+ m01) * num3
		quaternion[1] = 0.5 * num6
		quaternion[2] = (m21 + m12) * num3
		quaternion[3] = (m20 - m02) * num3
		return quaternion 
	num5 = math.sqrt(((1.0 + m22) - m00) - m11)
	num2 = 0.5 / num5
	quaternion[0] = (m20 + m02) * num2
	quaternion[1] = (m21 + m12) * num2
	quaternion[2] = 0.5 * num5
	quaternion[3] = (m01 - m10) * num2
	return quaternion

#----------------------------------------------------------------------------
# SETTINGS
#----------------------------------------------------------------------------

# Arm pivot relative to your head
#armLocalPosition = [0.2, -0.2, -0.1]
armLocalPosition = [0.2, -0.15, -0.1]

# Hand is placed at the arm position + arm offset that you can control with trackpad. This is default arm offset
defaultArmX = -0.1
defaultArmY = 0.0
defaultArmZ = 0.4

# How low player can duck
crouchOffset = -0.7

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
	backClickDouble = False
	
	inputControllerRotation = alvr.input_controller_orientation
	
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
		inputHeadPosition[1] = crouchOffset
	inputHeadRotation = [alvr.input_head_orientation[0], alvr.input_head_orientation[1], alvr.input_head_orientation[2]]
	inputControllerPosition = [alvr.input_controller_position[0],alvr.input_controller_position[1],alvr.input_controller_position[2]]
	inputControllerRotation = [alvr.input_controller_orientation[0],alvr.input_controller_orientation[1],alvr.input_controller_orientation[2]]
	#rotationLerp = 0.1
	#inputControllerRotation = [lerp(inputControllerRotation[0], alvr.input_controller_orientation[0], rotationLerp),lerp(inputControllerRotation[1], alvr.input_controller_orientation[1], rotationLerp), lerp(inputControllerRotation[2],alvr.input_controller_orientation[2], rotationLerp)]
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
	if (isTouch):
		alvr.trackpad[rightControllerId][0] = touchX
		alvr.trackpad[rightControllerId][1] = touchY
	else:
		alvr.trackpad[rightControllerId][0] = 0
		alvr.trackpad[rightControllerId][1] = 0
	
	# Set Trackpad touch and click
	alvr.buttons[rightControllerId][touchId] = isTouch
	

	# Move virtual controller position by deltaTouch
	if ( isTouch ):
		controllerOffsetX += deltaTouchX * 0.25
		controllerOffsetZ += deltaTouchY * 0.5
		controllerOffsetX = clamp(controllerOffsetX, -0.3, 0.3)
		controllerOffsetY = clamp(controllerOffsetY, -0.3, 0.3)
		controllerOffsetZ = clamp(controllerOffsetZ,  0.25, 1.0) # arm length ~0.75cm
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
	
	if ( isTouch ):
		handPivotPosition = add( inputHeadPosition, rotatevec(inputHeadRotation, armLocalPosition+[0]) )
		#inputControllerRotation = inputHeadRotation
		#inputControllerRotation[2] += math.radians(30)
	else:
		armLocalPositionSteady = [0.2, -0.25, -0.1]
		#armLocalPositionSteady = [0.0, 0.0, 0.0]
		handPivotPosition = add( inputHeadPosition, rotatevec(inputHeadRotation, armLocalPositionSteady+[0]) )
	handPosition = add( handPivotPosition, rotatevec(inputControllerRotation, controllerLocalOffset+[0]) )
	
	rightEyePosition = add(inputHeadPosition, rotatevec( inputHeadRotation, [0.023, 0, 0, 0] ) )
	
	lookDirection = normalize( sub(rightEyePosition, handPosition))
	#diagnostics.watch(controllerLocalX), diagnostics.watch(controllerLocalY),diagnostics.watch(controllerLocalZ)
	

	localUp = rotatevec(inputControllerRotation, [0,1,0,0])
	dotUp = math.degrees( dot(localUp, [0,1,0,0]) )
	diagnostics.watch(dotUp)
	if ( isTouch ):
		controllerRotation = quaternion2euler( QuaternionLookRotation ( lookDirection, localUp ) ) #inputControllerRotation
		controllerRotation[2] += math.radians(60)
	else:
		controllerRotation = inputControllerRotation
		controllerRotation[2] += math.radians(45)
	
	alvr.controller_orientation[rightControllerId][0] = controllerRotation[0]#lerp(alvr.controller_orientation[rightControllerId][0], controllerRotation[0], deltaTime * 30)
	alvr.controller_orientation[rightControllerId][1] = controllerRotation[1]#lerp(alvr.controller_orientation[rightControllerId][1], controllerRotation[1], deltaTime * 30)
	alvr.controller_orientation[rightControllerId][2] = controllerRotation[2]#lerp(alvr.controller_orientation[rightControllerId][2], controllerRotation[2], deltaTime * 30) #	+ math.radians(45)
	
	t = deltaTime * 30
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
	
	if (backClickNow):
		if (not backClick):
			if (backClickDeltaTime < 0.5):
				backClickDouble = True
			
		backClickTime = time.time()
		backClick = True
	else:
		if (backClick and backClickHoldTime < 0.15):
			gripTriggerToggle = not gripTriggerToggle;
		else:
			backClickDouble = False
		backClick = False
	
	centerClick = False
	if (isClick and touchX > -0.7 and touchX < 0.7 and touchY > -0.7 and touchY < 0.7):
		#if (clickHoldTime > 0.2):
		centerClick = True
		isClick = False
		
	alvr.buttons[rightControllerId][clickId] = isClick
	
	alvr.buttons[rightControllerId][gripId] = backClick or keyboard.getKeyDown(Key.R)
	
	#if (backClickDouble):
	#	diagnostics.debug("backClickDouble")
	
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